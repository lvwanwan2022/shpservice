#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from config import FILE_STORAGE
from models.db import execute_query, insert_with_snowflake_id
from utils.snowflake import get_snowflake_id

class FileService:
    """文件服务类，用于处理文件上传、存储和元数据管理"""
    
    def __init__(self):
        self.upload_folder = FILE_STORAGE['upload_folder']
        self.allowed_extensions = FILE_STORAGE['allowed_extensions']
        self.max_file_size = FILE_STORAGE['max_content_length']
        
        # 延迟初始化GeoServer服务，避免启动时的连接问题
        self.geoserver = None
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def _get_geoserver(self):
        """延迟获取GeoServer服务实例"""
        if self.geoserver is None:
            try:
                from services.geoserver_service import GeoServerService
                self.geoserver = GeoServerService()
            except Exception as e:
                print(f"GeoServer服务初始化失败: {e}")
                self.geoserver = None
        return self.geoserver
    
    def allowed_file(self, filename):
        """检查文件是否允许上传"""
        print(f"检查文件: {filename}")
        print(f"允许的扩展名: {self.allowed_extensions}")
        
        if '.' not in filename:
            print("文件名中没有扩展名")
            return False
            
        extension = filename.rsplit('.', 1)[1].lower()
        print(f"文件扩展名: {extension}")
        
        is_allowed = extension in self.allowed_extensions
        print(f"是否允许: {is_allowed}")
        
        return is_allowed
    
    def save_file(self, file, metadata):
        """保存上传文件并记录元数据"""
        # 验证文件
        if not file:
            raise ValueError("未找到上传文件")
        
        # 先从原始文件名提取扩展名进行验证
        original_filename = file.filename
        if not self.allowed_file(original_filename):
            raise ValueError(f"不支持的文件类型，允许的类型: {', '.join(self.allowed_extensions)}")
        
        # 提取扩展名
        extension = original_filename.rsplit('.', 1)[1].lower()
        
        # 生成安全的文件名（使用UUID避免中文问题）
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        # 构建文件路径
        if original_filename.lower().endswith('.mbtiles'):
            # 确保mbtiles子目录存在
            mbtiles_folder = os.path.join(self.upload_folder, 'mbtiles')
            if not os.path.exists(mbtiles_folder):
                os.makedirs(mbtiles_folder)
            file_path = os.path.join(mbtiles_folder, unique_filename)
        else:
            file_path = os.path.join(self.upload_folder, unique_filename)
        # 构建文件路径
        #file_path = os.path.join(self.upload_folder, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 检查文件大小
        if file_size > self.max_file_size:
            os.remove(file_path)
            raise ValueError(f"文件太大，最大允许: {self.max_file_size / 1024 / 1024}MB")
        
        # 准备元数据（使用原始文件名作为original_name）
        file_data = {
            'file_name': metadata.get('file_name'),
            'file_path': file_path,
            'original_name': original_filename,  # 保存原始文件名
            'file_size': file_size,
            'is_public': metadata.get('is_public', True),
            'discipline': metadata.get('discipline'),
            'dimension': metadata.get('dimension'),
            'file_type': metadata.get('file_type'),
            'coordinate_system': metadata.get('coordinate_system'),
            'tags': metadata.get('tags', ''),
            'description': metadata.get('description', ''),
            'user_id': metadata.get('user_id')
        }
        
        # 使用雪花算法生成ID并插入数据库
        file_id = insert_with_snowflake_id('files', file_data)
        
        # 注释掉自动发布逻辑，改为手动发布
        # self._publish_to_geoserver(file_path, file_id, metadata)
        
        return file_id, file_data
    
    def _publish_to_geoserver(self, file_path, file_id, metadata):
        """根据文件类型发布到GeoServer"""
        geoserver = self._get_geoserver()
        if not geoserver:
            print("GeoServer服务不可用，跳过发布")
            return
        
        file_type = metadata.get('file_type', '').lower()
        store_name = f"file_{file_id}"
        
        result = None
        
        try:
            if file_type == 'shp':
                # 发布shapefile
                if file_path.endswith('.zip'):
                    result = geoserver.publish_shapefile(file_path, store_name)
                else:
                    print(f"警告: Shapefile不是zip格式: {file_path}")
            elif file_type in ['dem', 'dom']:
                # 发布geotiff
                if file_path.endswith('.tif'):
                    # 对DOM文件自动启用透明度
                    enable_transparency = 'dom' in file_type.lower()
                    result = geoserver.publish_geotiff(file_path, store_name, file_id, None, enable_transparency)
                else:
                    print(f"警告: 栅格文件不是tif格式: {file_path}")
            elif file_type in ['dwg', 'dxf']:
                # 发布DWG/DXF
                coord_system = metadata.get('coordinate_system', 'EPSG:4326')
                result = geoserver.publish_dwg_dxf(file_path, store_name, coord_system)
            elif file_type == 'geojson':
                # 发布GeoJSON
                result = geoserver.publish_geojson(file_path, store_name, file_id)
            else:
                print(f"不支持的文件类型: {file_type}")
                
        except Exception as e:
            # 记录错误，但不阻止文件上传
            print(f"发布到GeoServer失败: {str(e)}")
            # 可以选择记录到日志文件
        
        # 如果发布成功，更新数据库
        if result:
            try:
                sql = """
                UPDATE files
                SET geoserver_layer = %(layer_name)s,
                    wms_url = %(wms_url)s,
                    wfs_url = %(wfs_url)s
                WHERE id = %(file_id)s
                """
                params = {
                    'layer_name': result.get('layer_name', ''),
                    'wms_url': result.get('wms_url', ''),
                    'wfs_url': result.get('wfs_url', ''),
                    'file_id': file_id
                }
                execute_query(sql, params)
                print(f"文件 {file_id} 成功发布到GeoServer")
            except Exception as e:
                print(f"更新数据库GeoServer信息失败: {str(e)}")
    
    def get_files(self, filters=None, page=1, page_size=12, sort_by='upload_date', sort_order='desc'):
        """获取文件列表"""
        # 构建基础查询
        base_sql = """
        SELECT f.*, u.username as uploader 
        FROM files f 
        LEFT JOIN users u ON f.user_id = u.id
        WHERE 1=1
        """
        count_sql = "SELECT COUNT(*) FROM files f WHERE 1=1"
        
        params = {}
        
        # 添加过滤条件
        if filters:
            if 'user_id' in filters and filters['user_id']:
                base_sql += " AND f.user_id = %(user_id)s"
                count_sql += " AND f.user_id = %(user_id)s"
                params['user_id'] = filters['user_id']
            
            if 'discipline' in filters and filters['discipline']:
                base_sql += " AND f.discipline = %(discipline)s"
                count_sql += " AND f.discipline = %(discipline)s"
                params['discipline'] = filters['discipline']
            
            if 'file_type' in filters and filters['file_type']:
                base_sql += " AND f.file_type = %(file_type)s"
                count_sql += " AND f.file_type = %(file_type)s"
                params['file_type'] = filters['file_type']
            
            if 'dimension' in filters and filters['dimension']:
                base_sql += " AND f.dimension = %(dimension)s"
                count_sql += " AND f.dimension = %(dimension)s"
                params['dimension'] = filters['dimension']
            
            if 'status' in filters and filters['status']:
                base_sql += " AND f.status = %(status)s"
                count_sql += " AND f.status = %(status)s"
                params['status'] = filters['status']
            
            if 'geometry_type' in filters and filters['geometry_type']:
                base_sql += " AND f.geometry_type = %(geometry_type)s"
                count_sql += " AND f.geometry_type = %(geometry_type)s"
                params['geometry_type'] = filters['geometry_type']
            
            if 'tags' in filters and filters['tags']:
                base_sql += " AND f.tags LIKE %(tags)s"
                count_sql += " AND f.tags LIKE %(tags)s"
                params['tags'] = f"%{filters['tags']}%"
            
            if 'file_name' in filters and filters['file_name']:
                base_sql += " AND f.file_name LIKE %(file_name)s"
                count_sql += " AND f.file_name LIKE %(file_name)s"
                params['file_name'] = f"%{filters['file_name']}%"
            
            if 'is_public' in filters and filters['is_public'] is not None:
                base_sql += " AND f.is_public = %(is_public)s"
                count_sql += " AND f.is_public = %(is_public)s"
                params['is_public'] = filters['is_public']
        
        # 获取总数
        count_result = execute_query(count_sql, params)
        total = count_result[0]['count'] if count_result else 0
        
        # 添加排序
        valid_sort_fields = ['id', 'file_name', 'file_size', 'upload_date', 'discipline', 'file_type']
        if sort_by not in valid_sort_fields:
            sort_by = 'upload_date'
        
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        base_sql += f" ORDER BY f.{sort_by} {sort_order.upper()}"
        
        # 添加分页
        base_sql += " LIMIT %(limit)s OFFSET %(offset)s"
        params['limit'] = page_size
        params['offset'] = (page - 1) * page_size
        
        # 执行查询
        files = execute_query(base_sql, params)
        
        return files, total
    
    def get_file_by_id(self, file_id):
        """根据ID获取文件"""
        sql = """
        SELECT f.*, u.username as uploader 
        FROM files f 
        LEFT JOIN users u ON f.user_id = u.id
        WHERE f.id = %(file_id)s
        """
        params = {'file_id': file_id}
        
        result = execute_query(sql, params)
        if not result:
            return None
        
        return result[0]
    
    def delete_file(self, file_id):
        """删除文件"""
        # 先获取文件信息
        file_info = self.get_file_by_id(file_id)
        if not file_info:
            raise ValueError(f"文件不存在: {file_id}")
        
        errors = []
        
        # 检查并清理GeoServer相关记录
        try:
            # 1. 检查是否有关联的GeoServer图层
            layer_check_sql = "SELECT id, name FROM geoserver_layers WHERE file_id = %s"
            layer_result = execute_query(layer_check_sql, (file_id,))
            
            if layer_result:
                # 如果有图层，先删除图层记录（这会级联删除相关的要素类型等）
                for layer in layer_result:
                    try:
                        # 删除图层记录
                        delete_layer_sql = "DELETE FROM geoserver_layers WHERE id = %s"
                        execute_query(delete_layer_sql, (layer['id'],), fetch=False)
                        print(f"删除图层记录: {layer['name']}")
                    except Exception as e:
                        errors.append(f"删除GeoServer图层记录失败: {str(e)}")
            
            # 2. 检查并删除存储仓库记录
            stores_sql = """
            SELECT s.* FROM geoserver_stores s
            WHERE s.file_id = %s
            """
            stores = execute_query(stores_sql, (file_id,))
            
            if stores:
                for store in stores:
                    try:
                        # 删除要素类型记录
                        delete_featuretypes_sql = "DELETE FROM geoserver_featuretypes WHERE store_id = %s"
                        execute_query(delete_featuretypes_sql, (store['id'],), fetch=False)
                        
                        # 删除存储记录
                        delete_store_sql = "DELETE FROM geoserver_stores WHERE id = %s"
                        execute_query(delete_store_sql, (store['id'],), fetch=False)
                        print(f"已删除GeoServer存储仓库记录: {store['name']}")
                    except Exception as e:
                        errors.append(f"删除GeoServer存储仓库记录失败: {str(e)}")
            
        except Exception as e:
            print(f"清理GeoServer记录时出错: {str(e)}")
            errors.append(f"清理GeoServer记录失败: {str(e)}")
        
        # 尝试从GeoServer删除服务（如果存在）
        try:
            geoserver = self._get_geoserver()
            if geoserver:
                store_name = f"file_{file_id}"
                geoserver.delete_layer(store_name)
        except Exception as e:
            # 记录错误但继续
            print(f"从GeoServer删除服务失败: {str(e)}")
            errors.append(f"从GeoServer删除服务失败: {str(e)}")
        
        # 从文件系统删除
        try:
            if os.path.exists(file_info['file_path']):
                os.remove(file_info['file_path'])
                print(f"已删除物理文件: {file_info['file_path']}")
            else:
                errors.append(f"物理文件不存在: {file_info['file_path']}")
        except Exception as e:
            # 记录错误但继续
            print(f"删除物理文件失败: {str(e)}")
            errors.append(f"删除物理文件失败: {str(e)}")
        
        # 从数据库删除文件记录
        try:
            sql = "DELETE FROM files WHERE id = %(file_id)s"
            params = {'file_id': file_id}
            execute_query(sql, params)
            print(f"已删除文件数据库记录: {file_id}")
        except Exception as e:
            print(f"从数据库删除文件记录失败: {str(e)}")
            errors.append(f"从数据库删除文件记录失败: {str(e)}")
            raise ValueError(f"删除文件失败: {str(e)}")
        
        # 如果有非致命错误，记录但不抛出异常
        if errors:
            print(f"删除文件时遇到一些问题: {'; '.join(errors)}")
            # 可以选择返回警告信息而不是抛出异常
        
        return True

    def update_file(self, file_id, data):
        """更新文件信息"""
        try:
            # 检查文件是否存在
            file_info = self.get_file_by_id(file_id)
            if not file_info:
                raise ValueError(f"文件不存在: {file_id}")
            
            # 构建更新字段
            update_fields = []
            params = {'file_id': file_id}
            
            allowed_fields = [
                'file_name', 'discipline', 'dimension', 'file_type', 
                'coordinate_system', 'tags', 'description', 'is_public',
                'status', 'geometry_type', 'feature_count', 'bbox', 'metadata'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %({field})s")
                    params[field] = data[field]
            
            if not update_fields:
                return
            
            # 执行更新
            sql = f"""
            UPDATE files 
            SET {', '.join(update_fields)}
            WHERE id = %(file_id)s
            """
            
            execute_query(sql, params)
            
        except Exception as e:
            print(f"更新文件失败: {str(e)}")
            raise

    def get_file_statistics(self):
        """获取文件统计信息"""
        try:
            stats = {}
            
            # 总文件数
            total_query = "SELECT COUNT(*) as total FROM files"
            total_result = execute_query(total_query)
            stats['total_files'] = total_result[0]['total'] if total_result else 0
            
            # 总文件大小
            size_query = "SELECT SUM(file_size) as total_size FROM files"
            size_result = execute_query(size_query)
            stats['total_size'] = size_result[0]['total_size'] if size_result and size_result[0]['total_size'] else 0
            
            # 按类型统计
            type_query = """
            SELECT file_type, COUNT(*) as count
            FROM files
            WHERE file_type IS NOT NULL
            GROUP BY file_type
            ORDER BY count DESC
            """
            type_result = execute_query(type_query)
            stats['by_type'] = {row['file_type']: row['count'] for row in type_result}
            
            # 按学科统计
            discipline_query = """
            SELECT discipline, COUNT(*) as count
            FROM files
            WHERE discipline IS NOT NULL
            GROUP BY discipline
            ORDER BY count DESC
            """
            discipline_result = execute_query(discipline_query)
            stats['by_discipline'] = {row['discipline']: row['count'] for row in discipline_result}
            
            # 按状态统计
            status_query = """
            SELECT status, COUNT(*) as count
            FROM files
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
            """
            status_result = execute_query(status_query)
            stats['by_status'] = {row['status']: row['count'] for row in status_result}
            
            return stats
            
        except Exception as e:
            print(f"获取文件统计信息失败: {str(e)}")
            raise 
    
    def get_file_coordinate_info_with_gdal(self, file_path, file_type):
        """使用GDAL获取文件的坐标系信息"""
        import subprocess
        import json
        import zipfile
        import tempfile
        import shutil
        
        try:
            coordinate_info = {
                'source': 'gdal',
                'file_type': file_type,
                'wkt': None,
                'epsg_code': None,
                'proj4': None,
                'authority': None,
                'geotransform': None,
                'extent': None,
                'error': None
            }
            
            actual_file_path = file_path
            temp_dir = None
            
            # 处理shapefile（zip文件）
            if file_type == 'shp' and file_path.endswith('.zip'):
                try:
                    temp_dir = tempfile.mkdtemp()
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # 获取zip文件中的所有文件列表
                    zip_files = []
                    shp_file_path = None
                    prj_file_path = None
                    
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, temp_dir)
                            zip_files.append(relative_path)
                            
                            # 查找.shp文件
                            if file.endswith('.shp'):
                                shp_file_path = full_path
                                actual_file_path = full_path
                            
                            # 查找.prj文件
                            elif file.endswith('.prj'):
                                prj_file_path = full_path
                    
                    coordinate_info['zip_contents'] = zip_files
                    
                    # 如果找到.prj文件，直接读取其内容
                    if prj_file_path and os.path.exists(prj_file_path):
                        try:
                            with open(prj_file_path, 'r', encoding='utf-8') as prj_file:
                                prj_content = prj_file.read().strip()
                                coordinate_info['prj_file_content'] = prj_content
                                coordinate_info['wkt'] = prj_content
                                
                                # 尝试从WKT中提取EPSG代码
                                import re
                                epsg_match = re.search(r'ID\[\"EPSG\",(\d+)\]', prj_content)
                                if epsg_match:
                                    epsg_code = epsg_match.group(1)
                                    coordinate_info['epsg_code'] = f"EPSG:{epsg_code}"
                                    coordinate_info['authority'] = 'EPSG'
                                    
                        except Exception as e:
                            coordinate_info['prj_read_error'] = f'读取.prj文件失败: {str(e)}'
                    
                    if not shp_file_path:
                        coordinate_info['error'] = 'ZIP文件中未找到.shp文件'
                        return coordinate_info
                        
                except Exception as e:
                    coordinate_info['error'] = f'解压ZIP文件失败: {str(e)}'
                    return coordinate_info
            
            # 优先尝试使用Python GDAL绑定获取坐标系信息
            try:
                from osgeo import gdal, ogr, osr
                gdal.UseExceptions()
                
                print(f"✅ 使用Python GDAL处理文件: {actual_file_path}")
                
                if file_type == 'shp':
                    # 使用OGR读取矢量数据
                    coordinate_info['gdal_command'] = 'python-ogr'
                    coordinate_info['source'] = 'python-gdal'
                    
                    driver = ogr.GetDriverByName("ESRI Shapefile")
                    datasource = driver.Open(actual_file_path, 0)
                    
                    if datasource:
                        layer = datasource.GetLayer()
                        spatial_ref = layer.GetSpatialRef()
                        
                        if spatial_ref:
                            # 获取WKT
                            wkt = spatial_ref.ExportToWkt()
                            if not coordinate_info.get('wkt'):
                                coordinate_info['wkt'] = wkt
                            
                            # 获取EPSG代码
                            epsg_code = spatial_ref.GetAuthorityCode(None)
                            if epsg_code and not coordinate_info.get('epsg_code'):
                                coordinate_info['epsg_code'] = f"EPSG:{epsg_code}"
                                coordinate_info['authority'] = 'EPSG'
                            
                            # 获取PROJ4字符串
                            try:
                                proj4 = spatial_ref.ExportToProj4()
                                coordinate_info['proj4'] = proj4
                            except:
                                pass
                        
                        # 获取范围
                        extent = layer.GetExtent()
                        coordinate_info['extent'] = {
                            'minX': extent[0],
                            'maxX': extent[1],
                            'minY': extent[2],
                            'maxY': extent[3]
                        }
                        
                        datasource = None
                        print(f"✅ 成功使用Python OGR获取坐标系信息")
                        return coordinate_info
                    else:
                        print(f"⚠️ 无法打开shapefile: {actual_file_path}")
                        
                else:
                    # 使用GDAL读取栅格数据
                    coordinate_info['gdal_command'] = 'python-gdal'
                    coordinate_info['source'] = 'python-gdal'
                    
                    dataset = gdal.Open(actual_file_path, gdal.GA_ReadOnly)
                    
                    if dataset:
                        print(f"✅ 成功打开栅格文件: {actual_file_path}")
                        
                        # 获取投影信息
                        projection = dataset.GetProjection()
                        if projection:
                            coordinate_info['wkt'] = projection
                            
                            # 创建空间参考对象
                            srs = osr.SpatialReference()
                            srs.ImportFromWkt(projection)
                            
                            # 获取EPSG代码
                            epsg_code = srs.GetAuthorityCode(None)
                            if epsg_code:
                                coordinate_info['epsg_code'] = f"EPSG:{epsg_code}"
                                coordinate_info['authority'] = 'EPSG'
                            
                            # 获取PROJ4字符串
                            try:
                                proj4 = srs.ExportToProj4()
                                coordinate_info['proj4'] = proj4
                            except:
                                pass
                        else:
                            print("⚠️ 文件没有投影信息")
                        
                        # 获取地理变换参数
                        geotransform = dataset.GetGeoTransform()
                        if geotransform and geotransform != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                            coordinate_info['geotransform'] = geotransform
                            
                            # 计算范围
                            width = dataset.RasterXSize
                            height = dataset.RasterYSize
                            
                            minX = geotransform[0]
                            maxX = geotransform[0] + width * geotransform[1]
                            maxY = geotransform[3]
                            minY = geotransform[3] + height * geotransform[5]
                            
                            coordinate_info['extent'] = {
                                'minX': minX,
                                'maxX': maxX,
                                'minY': minY,
                                'maxY': maxY
                            }
                        else:
                            print("⚠️ 文件没有地理变换信息")
                        
                        dataset = None
                        print(f"✅ 成功使用Python GDAL获取坐标系信息")
                        return coordinate_info
                    else:
                        print(f"⚠️ 无法打开栅格文件: {actual_file_path}")
                        
            except ImportError:
                print("⚠️ Python GDAL绑定不可用")
                coordinate_info['gdal_python_available'] = False
                coordinate_info['error'] = "Python GDAL绑定不可用，请安装GDAL: pip install gdal 或 conda install gdal"
                return coordinate_info
            except Exception as e:
                print(f"⚠️ Python GDAL处理失败: {str(e)}")
                coordinate_info['gdal_python_error'] = str(e)
                coordinate_info['error'] = f"Python GDAL处理失败: {str(e)}"
                return coordinate_info
            
            # 如果Python GDAL失败，尝试使用命令行工具
            try:
                if file_type == 'shp':
                    # 使用ogrinfo读取矢量数据信息
                    cmd = ['ogrinfo', '-json', '-so', actual_file_path]
                    coordinate_info['gdal_command'] = 'ogrinfo'
                else:
                    # 使用gdalinfo读取栅格数据信息
                    cmd = ['gdalinfo', '-json', actual_file_path]
                    coordinate_info['gdal_command'] = 'gdalinfo'
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    # 如果命令行工具也失败，提供详细错误信息
                    error_msg = f"GDAL命令行工具执行失败: {result.stderr}"
                    if "系统找不到指定的文件" in result.stderr or "not found" in result.stderr.lower():
                        error_msg += "\n\n可能的解决方案:\n1. 安装GDAL: conda install gdal 或 pip install gdal\n2. 确保GDAL工具已添加到系统PATH中\n3. 检查GDAL安装是否正确"
                    
                    coordinate_info['error'] = error_msg
                    
                    # 如果是shapefile且有.prj文件，至少返回.prj文件的信息
                    if file_type == 'shp' and coordinate_info.get('prj_file_content'):
                        coordinate_info['source'] = 'prj_file_only'
                        return coordinate_info
                    
                    # 提供一些基本建议
                    if file_type == 'shp':
                        coordinate_info['suggestions'] = self._get_coordinate_system_suggestions()
                    
                    return coordinate_info
                
                gdal_info = json.loads(result.stdout)
                
            except FileNotFoundError:
                error_msg = "GDAL工具未找到。请安装GDAL并确保已添加到系统PATH中。\n\n安装方法:\n1. conda install gdal\n2. pip install gdal\n3. 或下载OSGeo4W安装包"
                coordinate_info['error'] = error_msg
                
                # 如果是shapefile且有.prj文件，至少返回.prj文件的信息
                if file_type == 'shp' and coordinate_info.get('prj_file_content'):
                    coordinate_info['source'] = 'prj_file_only'
                    return coordinate_info
                
                return coordinate_info
                
            except subprocess.TimeoutExpired:
                coordinate_info['error'] = 'GDAL命令执行超时'
                return coordinate_info
                
            except json.JSONDecodeError as e:
                coordinate_info['error'] = f'解析GDAL输出失败: {str(e)}'
                return coordinate_info
                
            except Exception as e:
                coordinate_info['error'] = f'获取坐标系信息失败: {str(e)}'
                return coordinate_info
            
            # 存储GDAL信息用于对比
            gdal_coordinate_info = {}
            
            # 提取坐标系信息
            if 'coordinateSystem' in gdal_info:
                coord_sys = gdal_info['coordinateSystem']
                
                # WKT格式坐标系（如果没有从.prj文件获取到，则使用GDAL的）
                if 'wkt' in coord_sys:
                    gdal_coordinate_info['gdal_wkt'] = coord_sys['wkt']
                    
                    # 如果之前没有从.prj文件获取到WKT，则使用GDAL的
                    if not coordinate_info.get('wkt'):
                        coordinate_info['wkt'] = coord_sys['wkt']
                    
                    # 尝试从GDAL的WKT中提取EPSG代码（如果之前没有获取到）
                    if not coordinate_info.get('epsg_code'):
                        import re
                        epsg_match = re.search(r'ID\["EPSG",(\d+)\]', coord_sys['wkt'])
                        if epsg_match:
                            epsg_code = epsg_match.group(1)
                            coordinate_info['epsg_code'] = f"EPSG:{epsg_code}"
                            coordinate_info['authority'] = 'EPSG'
                
                # PROJ4格式
                if 'proj4' in coord_sys:
                    coordinate_info['proj4'] = coord_sys['proj4']
            
            # 对于shp文件，比较.prj文件和GDAL信息
            if file_type == 'shp' and coordinate_info.get('prj_file_content'):
                comparison = {
                    'prj_wkt': coordinate_info.get('prj_file_content'),
                    'gdal_wkt': gdal_coordinate_info.get('gdal_wkt'),
                    'match': False
                }
                
                # 简单的字符串比较（去除空白字符）
                if (coordinate_info.get('prj_file_content') and 
                    gdal_coordinate_info.get('gdal_wkt')):
                    prj_normalized = ''.join(coordinate_info['prj_file_content'].split())
                    gdal_normalized = ''.join(gdal_coordinate_info['gdal_wkt'].split())
                    comparison['match'] = prj_normalized == gdal_normalized
                
                coordinate_info['prj_gdal_comparison'] = comparison
            
            # 地理转换参数
            if 'geoTransform' in gdal_info:
                coordinate_info['geotransform'] = gdal_info['geoTransform']
            
            # 空间范围
            if 'wgs84Extent' in gdal_info:
                extent = gdal_info['wgs84Extent']
                coordinate_info['extent'] = {
                    'type': 'wgs84',
                    'coordinates': extent.get('coordinates', [])
                }
            elif 'cornerCoordinates' in gdal_info:
                corner_coords = gdal_info['cornerCoordinates']
                coordinate_info['extent'] = {
                    'type': 'corner',
                    'coordinates': corner_coords
                }
            
            # 文件大小和像素信息（针对栅格文件）
            if 'size' in gdal_info:
                coordinate_info['raster_size'] = gdal_info['size']
            
            if 'bands' in gdal_info:
                coordinate_info['band_count'] = len(gdal_info['bands'])
                if gdal_info['bands']:
                    coordinate_info['data_type'] = gdal_info['bands'][0].get('type')
            
            return coordinate_info
            
        except Exception as e:
            coordinate_info['error'] = f'获取坐标系信息失败: {str(e)}'
            return coordinate_info
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    def get_mbtiles_coordinate_info(self, file_path):
        """从MBTiles文件的metadata表中获取坐标系信息"""
        import sqlite3
        
        try:
            coordinate_info = {
                'source': 'mbtiles_metadata',
                'file_type': 'mbtiles',
                'wkt': None,
                'epsg_code': None,
                'proj4': None,
                'authority': None,
                'metadata': {},
                'error': None
            }
            
            # 连接SQLite数据库
            conn = sqlite3.connect(file_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询metadata表
            cursor.execute("SELECT name, value FROM metadata")
            metadata_rows = cursor.fetchall()
            
            metadata = {}
            for row in metadata_rows:
                metadata[row['name']] = row['value']
            
            coordinate_info['metadata'] = metadata
            
            # 从metadata中提取坐标系信息
            # MBTiles通常使用Web Mercator (EPSG:3857)
            if 'projection' in metadata:
                projection = metadata['projection']
                if projection == 'mercator' or projection == '900913':
                    coordinate_info['epsg_code'] = 'EPSG:3857'
                    coordinate_info['authority'] = 'EPSG'
                elif projection.startswith('EPSG:'):
                    coordinate_info['epsg_code'] = projection
                    coordinate_info['authority'] = 'EPSG'
            else:
                # 默认情况下，MBTiles使用Web Mercator
                coordinate_info['epsg_code'] = 'EPSG:3857 or EPSG:4326'
                coordinate_info['authority'] = 'EPSG'
                coordinate_info['note'] = 'MBTiles默认使用WGS84投影(EPSG:3857 or EPSG:4326)'
            
            # 提取其他有用信息
            useful_keys = ['bounds', 'center', 'minzoom', 'maxzoom', 'format', 'type', 'version', 'description', 'attribution']
            extracted_info = {}
            for key in useful_keys:
                if key in metadata:
                    extracted_info[key] = metadata[key]
            
            coordinate_info['tile_info'] = extracted_info
            
            # 解析bounds信息
            if 'bounds' in metadata:
                try:
                    bounds_str = metadata['bounds']
                    bounds = [float(x) for x in bounds_str.split(',')]
                    if len(bounds) == 4:
                        coordinate_info['extent'] = {
                            'type': 'bounds',
                            'coordinates': {
                                'west': bounds[0],
                                'south': bounds[1],
                                'east': bounds[2],
                                'north': bounds[3]
                            }
                        }
                except:
                    pass
            
            conn.close()
            return coordinate_info
            
        except Exception as e:
            coordinate_info['error'] = f'读取MBTiles元数据失败: {str(e)}'
            return coordinate_info
    
    def _analyze_shapefile_extent(self, ogrinfo_output):
        """分析shapefile的边界范围来推测坐标系"""
        analysis = {
            'extent_analysis': {},
            'suggested_crs': [],
            'analysis_notes': []
        }
        
        try:
            import re
            
            # 解析Extent信息
            extent_match = re.search(r'Extent:\s*\(([-\d.]+),\s*([-\d.]+)\)\s*-\s*\(([-\d.]+),\s*([-\d.]+)\)', ogrinfo_output)
            
            if extent_match:
                min_x = float(extent_match.group(1))
                min_y = float(extent_match.group(2))
                max_x = float(extent_match.group(3))
                max_y = float(extent_match.group(4))
                
                analysis['extent_analysis'] = {
                    'min_x': min_x,
                    'min_y': min_y,
                    'max_x': max_x,
                    'max_y': max_y,
                    'width': max_x - min_x,
                    'height': max_y - min_y
                }
                
                # 推测坐标系类型
                # 1. 检查是否为地理坐标系（经纬度）
                if (-180 <= min_x <= 180) and (-180 <= max_x <= 180) and (-90 <= min_y <= 90) and (-90 <= max_y <= 90):
                    analysis['analysis_notes'].append('坐标范围在经纬度范围内（-180~180, -90~90），可能是地理坐标系')
                    
                    # 进一步推测具体的地理坐标系
                    if (-180 <= min_x <= -66) and (18 <= min_y <= 72):  # 北美洲范围
                        analysis['suggested_crs'].extend([
                            {'epsg': 'EPSG:4326', 'name': 'WGS 84', 'reason': 'GPS数据或全球数据常用坐标系'},
                            {'epsg': 'EPSG:4269', 'name': 'NAD83', 'reason': '北美地区常用坐标系'},
                            {'epsg': 'EPSG:4267', 'name': 'NAD27', 'reason': '北美地区传统坐标系'}
                        ])
                    elif (70 <= min_x <= 140) and (10 <= min_y <= 55):  # 中国范围
                        analysis['suggested_crs'].extend([
                            {'epsg': 'EPSG:4326', 'name': 'WGS 84', 'reason': 'GPS数据或全球数据常用坐标系'},
                            {'epsg': 'EPSG:4490', 'name': 'CGCS2000', 'reason': '中国大陆常用坐标系'},
                            {'epsg': 'EPSG:4214', 'name': 'Beijing 1954', 'reason': '中国传统坐标系'}
                        ])
                    else:
                        analysis['suggested_crs'].append({
                            'epsg': 'EPSG:4326', 
                            'name': 'WGS 84', 
                            'reason': 'GPS数据的标准坐标系'
                        })
                
                # 2. 检查是否为投影坐标系
                elif abs(min_x) > 1000000 or abs(max_x) > 1000000:  # 大坐标值，可能是投影坐标系
                    coord_magnitude = max(abs(min_x), abs(max_x), abs(min_y), abs(max_y))
                    
                    if coord_magnitude > 10000000:
                        analysis['analysis_notes'].append(f'坐标值很大（{coord_magnitude:.0f}），可能是以米为单位的投影坐标系')
                    else:
                        analysis['analysis_notes'].append(f'坐标值较大（{coord_magnitude:.0f}），可能是投影坐标系')
                    
                    # 根据坐标范围推测可能的投影坐标系
                    if 200000 <= abs(min_x) <= 800000:  # UTM坐标系特征
                        analysis['suggested_crs'].extend([
                            {'epsg': 'EPSG:3857', 'name': 'Web Mercator', 'reason': '网络地图常用投影'},
                            {'epsg': 'EPSG:32649', 'name': 'WGS 84 / UTM zone 49N', 'reason': 'UTM投影系统'},
                            {'epsg': 'EPSG:32650', 'name': 'WGS 84 / UTM zone 50N', 'reason': 'UTM投影系统'}
                        ])
                    else:
                        analysis['suggested_crs'].append({
                            'epsg': 'EPSG:3857', 
                            'name': 'Web Mercator', 
                            'reason': '网络地图和Web应用常用投影'
                        })
                
                # 3. 中等范围坐标值
                else:
                    analysis['analysis_notes'].append('坐标值在中等范围内，需要更多信息来确定坐标系')
                    analysis['suggested_crs'].extend([
                        {'epsg': 'EPSG:4326', 'name': 'WGS 84', 'reason': '通用地理坐标系'},
                        {'epsg': 'EPSG:3857', 'name': 'Web Mercator', 'reason': '网络地图投影'}
                    ])
            
            # 解析几何类型
            geom_match = re.search(r'Geometry:\s*(\w+)', ogrinfo_output)
            if geom_match:
                analysis['geometry_type'] = geom_match.group(1)
                analysis['analysis_notes'].append(f'几何类型: {geom_match.group(1)}')
            
            # 解析要素数量
            feature_match = re.search(r'Feature Count:\s*(\d+)', ogrinfo_output)
            if feature_match:
                analysis['feature_count'] = int(feature_match.group(1))
                analysis['analysis_notes'].append(f'要素数量: {feature_match.group(1)}')
            
        except Exception as e:
            analysis['analysis_notes'].append(f'边界分析失败: {str(e)}')
        
        return analysis
    
    def _get_coordinate_system_suggestions(self):
        """提供常用坐标系建议"""
        return {
            'common_geographic': [
                {
                    'epsg': 'EPSG:4326',
                    'name': 'WGS 84',
                    'description': 'GPS和全球定位系统的标准坐标系',
                    'use_cases': ['GPS数据', '全球数据', 'Web地图服务']
                },
                {
                    'epsg': 'EPSG:4490',
                    'name': 'CGCS2000',
                    'description': '中国大陆地区的官方坐标系',
                    'use_cases': ['中国测绘数据', '政府数据', '基础地理信息']
                },
                {
                    'epsg': 'EPSG:4269',
                    'name': 'NAD83',
                    'description': '北美地区的标准坐标系',
                    'use_cases': ['美国和加拿大数据', '北美测绘数据']
                }
            ],
            'common_projected': [
                {
                    'epsg': 'EPSG:3857',
                    'name': 'Web Mercator',
                    'description': '网络地图服务的标准投影',
                    'use_cases': ['Google Maps', 'OpenStreetMap', 'Web地图应用']
                },
                {
                    'epsg': 'EPSG:32649',
                    'name': 'WGS 84 / UTM zone 49N',
                    'description': 'UTM第49带北区投影（中国东部）',
                    'use_cases': ['中国东部地区', '精确测量', '工程项目']
                },
                {
                    'epsg': 'EPSG:32650',
                    'name': 'WGS 84 / UTM zone 50N',
                    'description': 'UTM第50带北区投影（中国中东部）',
                    'use_cases': ['中国中东部地区', '精确测量', '工程项目']
                }
            ],
            'detection_tips': [
                '如果数据来源于GPS设备，通常使用WGS84 (EPSG:4326)',
                '如果数据在中国境内，建议尝试CGCS2000 (EPSG:4490)',
                '如果是网络地图数据，通常使用Web Mercator (EPSG:3857)',
                '联系数据提供者是获取准确坐标系信息的最佳方式',
                '可以通过与已知坐标系的数据进行对比来验证坐标系'
            ]
        } 