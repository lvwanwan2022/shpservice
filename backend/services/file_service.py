#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from config import FILE_STORAGE
from models.db import execute_query

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
        file_path = os.path.join(self.upload_folder, unique_filename)
        
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
        
        # 插入数据库
        sql = """
        INSERT INTO files 
        (file_name, file_path, original_name, file_size, is_public, 
        discipline, dimension, file_type, coordinate_system, tags, description, user_id)
        VALUES 
        (%(file_name)s, %(file_path)s, %(original_name)s, %(file_size)s, %(is_public)s,
        %(discipline)s, %(dimension)s, %(file_type)s, %(coordinate_system)s, %(tags)s, %(description)s, %(user_id)s)
        RETURNING id
        """
        result = execute_query(sql, file_data)
        file_id = result[0]['id']
        
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