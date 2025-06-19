#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SHP Martin服务类
解压SHP压缩包，使用geopandas将SHP数据存入PostGIS，然后通过Martin发布MVT瓦片服务
"""

import os
import json
import uuid
import tempfile
import zipfile
import shutil
import warnings
from datetime import datetime
from werkzeug.utils import secure_filename
import geopandas as gpd
from pathlib import Path

from config import FILE_STORAGE, DB_CONFIG
from models.db import execute_query, insert_with_snowflake_id
from services.postgis_service import PostGISService
from services.martin_service import MartinService


class ShpMartinService:
    """SHP Martin服务类，提供完整的SHP到MVT瓦片服务的发布流程"""
    
    def __init__(self):
        """初始化服务"""
        self.upload_folder = os.path.join(FILE_STORAGE['upload_folder'], 'shp')
        self.postgis_service = PostGISService()
        self.martin_service = MartinService()
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        
        print("✅ SHP Martin服务初始化完成")
        print(f"   - PostGIS模式: {'geopandas' if self.postgis_service.use_geopandas else '手动实现'}")
        print(f"   - Martin服务: {'启用' if self.martin_service.is_enabled() else '禁用'}")
    
    def publish_shp_service(self, file_obj, file_info):
        """发布SHP压缩包为MVT瓦片服务
        
        完整流程：
        1. 验证和保存SHP压缩包文件
        2. 解压ZIP文件并验证SHP文件完整性
        3. 使用geopandas将数据存入PostGIS
        4. 刷新Martin配置并重启服务
        5. 返回MVT瓦片服务信息
        
        Args:
            file_obj: 文件对象
            file_info: 文件信息字典，包含original_filename, user_id等
            
        Returns:
            包含服务信息的字典
        """
        extracted_folder = None
        try:
            print(f"\n=== 开始发布SHP为MVT瓦片服务 ===")
            
            # 1. 验证文件格式
            original_filename = file_info.get('original_filename')
            if not original_filename.lower().endswith('.zip'):
                raise ValueError("只支持.zip文件")
            
            # 2. 生成唯一文件ID和表名
            file_id = str(uuid.uuid4())
            table_name = f"shp_{file_id.replace('-', '_')}"
            
            print(f"文件ID: {file_id}")
            print(f"表名: {table_name}")
            
            # 3. 保存ZIP文件到本地
            file_content = file_obj.read()
            file_path = self._save_shp_file(file_content, file_id, original_filename)
            
            # 4. 解压并验证SHP文件
            print("\n--- 解压和验证SHP文件 ---")
            extracted_folder = self._extract_and_validate_shp(file_path)
            shp_file_path = self._find_shp_file(extracted_folder)
            
            # 5. 分析SHP文件特性
            analysis = self._analyze_shp(shp_file_path)
            print(f"SHP分析结果: {analysis}")
            
            # 6. 使用PostGIS服务将数据存入数据库
            print("\n--- 将SHP存入PostGIS ---")
            postgis_result = self._store_shp_to_postgis(shp_file_path, file_id)
            
            if not postgis_result.get('success'):
                raise Exception("PostGIS数据存储失败")
            
            print(f"✅ 数据已存入PostGIS表: {postgis_result['table_name']}")
            
            # 7. 记录到数据库
            db_record_id = self._record_to_database(
                file_id, original_filename, file_path, analysis, 
                postgis_result, file_info.get('user_id')
            )
            
            # 8. 启动/刷新Martin服务
            print("\n--- 配置Martin服务 ---")
            martin_result = self._setup_martin_service(postgis_result['table_name'])
            
            # 9. 构建返回结果
            result = {
                "success": True,
                "file_id": file_id,
                "original_filename": original_filename,
                "table_name": postgis_result['table_name'],
                "database_record_id": db_record_id,
                
                # SHP文件信息
                "shp_info": {
                    "file_size": len(file_content),
                    "feature_count": analysis['feature_count'],
                    "geometry_types": analysis['geometry_types'],
                    "bbox": analysis.get('bbox'),
                    "file_path": file_path,
                    "extracted_folder": extracted_folder
                },
                
                # PostGIS信息
                "postgis_info": {
                    "table_name": postgis_result['table_name'],
                    "schema": postgis_result.get('schema', 'public'),
                    "full_table_name": postgis_result.get('full_table_name'),
                    "geometry_types": postgis_result.get('geometry_types'),
                    "is_mixed": postgis_result.get('is_mixed', False)
                },
                
                # Martin服务信息
                "martin_info": martin_result,
                
                "upload_date": datetime.now().isoformat()
            }
            
            print(f"✅ SHP MVT瓦片服务发布成功")
            print(f"   - 文件ID: {file_id}")
            print(f"   - 表名: {postgis_result['table_name']}")
            print(f"   - MVT URL: {martin_result.get('mvt_url', 'N/A')}")
            
            return result
            
        except Exception as e:
            print(f"❌ 发布SHP服务失败: {str(e)}")
            # 清理可能创建的资源
            self._cleanup_failed_publish(locals())
            raise
        
        finally:
            # 清理解压的临时文件夹
            if extracted_folder and os.path.exists(extracted_folder):
                try:
                    shutil.rmtree(extracted_folder)
                    print(f"✅ 清理临时文件夹: {extracted_folder}")
                except Exception as cleanup_error:
                    print(f"⚠️ 清理临时文件夹失败: {cleanup_error}")
    
    def get_service_info(self, file_id):
        """获取已发布服务的信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            服务信息字典
        """
        try:
            # 从数据库获取记录
            sql = """
            SELECT * FROM shp_martin_services 
            WHERE file_id = %s AND status = 'active'
            """
            result = execute_query(sql, (file_id,))
            
            if not result:
                raise ValueError(f"服务不存在: {file_id}")
            
            service_record = result[0]
            table_name = service_record['table_name']
            
            # 检查Martin服务状态
            martin_status = self.martin_service.get_status()
            
            # 获取MVT信息
            mvt_info = None
            if martin_status.get('running'):
                try:
                    source_id = f"public.{table_name}"
                    mvt_url = self.martin_service.get_mvt_url(source_id)
                    tilejson_url = f"{self.martin_service.base_url}/{source_id}"
                    
                    mvt_info = {
                        "mvt_url": mvt_url,
                        "tilejson_url": tilejson_url,
                        "source_id": source_id
                    }
                except Exception as e:
                    print(f"⚠️ 获取MVT信息失败: {e}")
            
            # 构建返回结果
            result = {
                "success": True,
                "file_id": file_id,
                "original_filename": service_record['original_filename'],
                "table_name": table_name,
                "upload_date": service_record['created_at'].isoformat(),
                "status": service_record['status'],
                
                # 解析JSON字段
                "shp_info": self._safe_json_parse(service_record['shp_info']),
                "postgis_info": self._safe_json_parse(service_record['postgis_info']),
                
                # Martin服务状态
                "martin_status": martin_status,
                "mvt_info": mvt_info
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 获取服务信息失败: {str(e)}")
            raise
    
    def list_services(self, limit=100, offset=0, user_id=None):
        """列出已发布的服务
        
        Args:
            limit: 限制返回的记录数
            offset: 结果集的偏移量
            user_id: 用户ID过滤
            
        Returns:
            服务列表
        """
        try:
            # 构建SQL查询
            sql = """
            SELECT id, file_id, original_filename, table_name, status, created_at, user_id,
                   shp_info, postgis_info, service_url
            FROM shp_martin_services
            WHERE status = 'active'
            """
            
            params = []
            
            # 添加用户ID过滤
            if user_id is not None:
                sql += " AND user_id = %s"
                params.append(user_id)
            
            # 添加排序和分页
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 执行查询
            services = execute_query(sql, tuple(params))
            
            # 获取Martin服务状态
            martin_status = self.martin_service.get_status()
            
            # 获取Martin catalog以验证表是否真实存在
            martin_catalog = None
            if martin_status.get('running'):
                try:
                    martin_catalog = self.martin_service.get_catalog()
                except Exception as e:
                    print(f"⚠️ 获取Martin catalog失败: {e}")
            
            # 处理结果
            result = []
            for service in services:
                # 解析JSON字段
                shp_info = self._safe_json_parse(service['shp_info'])
                postgis_info = self._safe_json_parse(service['postgis_info'])
                
                # 获取MVT信息
                mvt_info = None
                if martin_status.get('running') and martin_catalog:
                    try:
                        source_id = f"public.{service['table_name']}"
                        
                        # 验证表是否在Martin catalog中存在
                        if 'tiles' in martin_catalog and source_id in martin_catalog['tiles']:
                            mvt_url = self.martin_service.get_mvt_url(source_id)
                            tilejson_url = f"{self.martin_service.base_url}/{source_id}"
                            mvt_info = {
                                "mvt_url": mvt_url,
                                "tilejson_url": tilejson_url,
                                "source_id": source_id
                            }
                        else:
                            print(f"⚠️ 表{source_id}在Martin catalog中不存在，跳过MVT信息")
                    except Exception as e:
                        print(f"⚠️ 获取{service['table_name']}的MVT信息失败: {e}")
                
                service_info = {
                    "id": service['id'],
                    "file_id": service['file_id'],
                    "original_filename": service['original_filename'],
                    "table_name": service['table_name'],
                    "status": service['status'],
                    "upload_date": service['created_at'].isoformat(),
                    "user_id": service['user_id'],
                    "service_url": service.get('service_url'),
                    
                    # 从shp_info中提取的字段
                    "feature_count": shp_info.get('feature_count', 0),
                    "geometry_types": shp_info.get('geometry_types', []),
                    "bbox": shp_info.get('bbox'),
                    
                    # 完整的shp_info和postgis_info
                    "shp_info": shp_info,
                    "postgis_info": postgis_info,
                    
                    # MVT服务信息
                    "mvt_info": mvt_info
                }
                
                result.append(service_info)
            
            return {
                "success": True,
                "services": result,
                "total": len(result),
                "martin_status": martin_status
            }
            
        except Exception as e:
            print(f"❌ 列出服务失败: {str(e)}")
            raise
    
    def delete_service(self, file_id):
        """删除已发布的SHP Martin服务
        
        Args:
            file_id: 文件ID
            
        Returns:
            删除结果字典
        """
        try:
            print(f"\n=== 删除SHP Martin服务 ===")
            print(f"文件ID: {file_id}")
            
            # 1. 获取服务记录
            sql = """
            SELECT * FROM shp_martin_services 
            WHERE file_id = %s AND status = 'active'
            """
            result = execute_query(sql, (file_id,))
            
            if not result:
                raise ValueError(f"服务不存在: {file_id}")
            
            service_record = result[0]
            table_name = service_record['table_name']
            
            print(f"找到服务记录: {table_name}")
            
            # 2. 从PostGIS删除表
            try:
                from sqlalchemy import create_engine, text
                connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
                engine = create_engine(connection_string, echo=False)
                
                with engine.connect() as conn:
                    # 删除表
                    drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE"
                    conn.execute(text(drop_sql))
                    conn.commit()
                    print(f"✅ 已删除PostGIS表: {table_name}")
            except Exception as e:
                print(f"⚠️ 删除PostGIS表失败: {e}")
                # 继续执行，不中断删除流程
            
            # 3. 更新服务记录状态为已删除
            update_sql = """
            UPDATE shp_martin_services 
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE file_id = %s
            """
            execute_query(update_sql, (file_id,))
            
            print(f"✅ 服务记录状态已更新为deleted")
            
            # 4. 刷新Martin配置
            try:
                self.martin_service.refresh_tables()
                print(f"✅ Martin配置已刷新")
            except Exception as e:
                print(f"⚠️ 刷新Martin配置失败: {e}")
            
            result = {
                "success": True,
                "file_id": file_id,
                "table_name": table_name,
                "message": "SHP Martin服务删除成功"
            }
            
            print(f"✅ SHP Martin服务删除成功: {file_id}")
            return result
            
        except Exception as e:
            print(f"❌ 删除SHP Martin服务失败: {str(e)}")
            raise
    
    def publish_existing_file(self, file_id, user_id=None):
        """发布已上传的SHP文件到Martin服务
        
        Args:
            file_id: 文件ID
            user_id: 用户ID（可选）
            
        Returns:
            发布结果字典
        """
        extracted_folder = None
        try:
            print(f"\n=== 发布已存在SHP文件到Martin服务 ===")
            print(f"文件ID: {file_id}")
            
            # 1. 获取文件信息
            sql = "SELECT * FROM files WHERE id = %s"
            file_result = execute_query(sql, (file_id,))
            if not file_result:
                raise ValueError(f"文件不存在: {file_id}")
            
            file_info = file_result[0]
            
            # 2. 验证文件类型
            if file_info['file_type'].lower() != 'shp':
                raise ValueError(f"文件类型不支持: {file_info['file_type']}")
            
            file_path = file_info['file_path']
            
            # 3. 检查文件是否存在
            if not os.path.exists(file_path):
                raise ValueError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 4. 生成新的服务ID和表名
            service_file_id = str(uuid.uuid4())
            table_name = f"shp_{service_file_id.replace('-', '_')}"
            
            print(f"服务文件ID: {service_file_id}")
            print(f"表名: {table_name}")
            
            # 5. 解压并验证SHP文件
            extracted_folder = self._extract_and_validate_shp(file_path)
            shp_file_path = self._find_shp_file(extracted_folder)
            
            # 6. 分析SHP文件特性
            analysis = self._analyze_shp(shp_file_path)
            print(f"SHP分析结果: {analysis}")
            
            # 7. 使用PostGIS服务将数据存入数据库
            print("\n--- 将SHP存入PostGIS ---")
            postgis_result = self._store_shp_to_postgis(shp_file_path, service_file_id)
            
            if not postgis_result.get('success'):
                raise Exception("PostGIS数据存储失败")
            
            print(f"✅ 数据已存入PostGIS表: {postgis_result['table_name']}")
            
            # 8. 记录到Martin服务数据库
            db_record_id = self._record_to_database(
                service_file_id, file_info['file_name'], file_path, analysis, 
                postgis_result, file_info['user_id']
            )
            
            # 9. 启动/刷新Martin服务
            print("\n--- 配置Martin服务 ---")
            martin_result = self._setup_martin_service(postgis_result['table_name'])
            
            # 10. 构建返回结果
            result = {
                "success": True,
                "file_id": service_file_id,
                "original_file_id": file_id,  # 原始文件ID
                "original_filename": file_info['file_name'],
                "table_name": postgis_result['table_name'],
                "database_record_id": db_record_id,
                
                # SHP文件信息
                "shp_info": {
                    "file_size": len(file_content),
                    "feature_count": analysis['feature_count'],
                    "geometry_types": analysis['geometry_types'],
                    "bbox": analysis.get('bbox'),
                    "file_path": file_path
                },
                
                # PostGIS信息
                "postgis_info": {
                    "table_name": postgis_result['table_name'],
                    "schema": postgis_result.get('schema', 'public'),
                    "full_table_name": postgis_result.get('full_table_name'),
                    "geometry_types": postgis_result.get('geometry_types'),
                    "is_mixed": postgis_result.get('is_mixed', False)
                },
                
                # Martin服务信息
                "martin_info": martin_result,
                
                "upload_date": datetime.now().isoformat()
            }
            
            print(f"✅ 已存在文件发布到Martin服务成功")
            print(f"   - 原始文件ID: {file_id}")
            print(f"   - 服务文件ID: {service_file_id}")
            print(f"   - 表名: {postgis_result['table_name']}")
            print(f"   - MVT URL: {martin_result.get('mvt_url', 'N/A')}")
            
            return result
            
        except Exception as e:
            print(f"❌ 发布已存在文件到Martin服务失败: {str(e)}")
            # 清理可能创建的资源
            self._cleanup_failed_publish(locals())
            raise
        
        finally:
            # 清理解压的临时文件夹
            if extracted_folder and os.path.exists(extracted_folder):
                try:
                    shutil.rmtree(extracted_folder)
                    print(f"✅ 清理临时文件夹: {extracted_folder}")
                except Exception as cleanup_error:
                    print(f"⚠️ 清理临时文件夹失败: {cleanup_error}")
    
    # === 私有方法 ===
    
    def _save_shp_file(self, file_content, file_id, original_filename):
        """保存SHP文件到本地"""
        file_path = os.path.join(self.upload_folder, f"{file_id}.zip")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        print(f"✅ 文件已保存: {file_path}")
        return file_path
    
    def _extract_and_validate_shp(self, zip_path):
        """解压并验证SHP文件"""
        print(f"开始解压SHP文件: {zip_path}")
        
        # 创建临时解压目录
        temp_dir = tempfile.mkdtemp()
        filename = os.path.splitext(os.path.basename(zip_path))[0]
        extracted_folder = os.path.join(temp_dir, filename)
        os.makedirs(extracted_folder, exist_ok=True)
        
        try:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                zip_file.extractall(extracted_folder)
                print(f"ZIP文件解压完成: {extracted_folder}")
            
            # 获取解压后的文件列表
            extracted_files = []
            for root, dirs, files in os.walk(extracted_folder):
                for file in files:
                    extracted_files.append(file.lower())
            
            print(f"解压后的文件列表: {extracted_files}")
            
            # 验证必需文件是否存在
            has_shp = any(f.endswith('.shp') for f in extracted_files)
            has_dbf = any(f.endswith('.dbf') for f in extracted_files)
            has_shx = any(f.endswith('.shx') for f in extracted_files)
            
            if not has_shp:
                raise Exception("ZIP文件中未找到.shp文件")
            if not has_dbf:
                raise Exception("ZIP文件中未找到.dbf文件")
            if not has_shx:
                raise Exception("ZIP文件中未找到.shx文件")
            
            print(f"✅ SHP文件验证通过")
            return extracted_folder
            
        except Exception as e:
            # 如果验证失败，清理解压的文件
            if os.path.exists(extracted_folder):
                shutil.rmtree(extracted_folder)
            raise Exception(f"SHP文件解压或验证失败: {str(e)}")
    
    def _find_shp_file(self, folder_path):
        """在解压文件夹中查找SHP文件"""
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.shp'):
                    return os.path.join(root, file)
        
        raise Exception("在解压文件夹中未找到.shp文件")
    
    def _analyze_shp(self, shp_file_path):
        """分析SHP文件"""
        try:
            import geopandas as gpd
            import pandas as pd
            import warnings
            
            print(f"分析SHP文件: {shp_file_path}")
            
            # 禁用一些不必要的警告
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gdf = gpd.read_file(shp_file_path, encoding='utf-8')
            
            # 分析几何类型
            geometry_types = set()
            for geom in gdf.geometry:
                if geom is not None and not geom.is_empty:
                    geometry_types.add(geom.geom_type)
            
            geometry_types = sorted(list(geometry_types))
            
            # 计算边界框
            bbox = None
            try:
                bounds = gdf.total_bounds
                if not any(pd.isna(bounds)):
                    bbox = [bounds[0], bounds[1], bounds[2], bounds[3]]  # [minx, miny, maxx, maxy]
            except:
                pass
            
            analysis = {
                'feature_count': len(gdf),
                'geometry_types': geometry_types,
                'bbox': bbox,
                'crs': str(gdf.crs) if gdf.crs else None,
                'columns': list(gdf.columns)
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ 分析SHP文件失败: {str(e)}")
            raise Exception(f"分析SHP文件失败: {str(e)}")
    
    def _store_shp_to_postgis(self, shp_file_path, file_id):
        """使用geopandas将SHP数据存入PostGIS"""
        try:
            import geopandas as gpd
            import warnings
            from sqlalchemy import create_engine, text
            
            print(f"将SHP数据存入PostGIS: {shp_file_path}")
            
            # 读取SHP文件
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gdf = gpd.read_file(shp_file_path, encoding='utf-8')
            
            if len(gdf) == 0:
                raise Exception("SHP文件中没有要素")
            
            # 设置CRS（如果未设置）
            if gdf.crs is None:
                print("⚠️ SHP文件没有CRS信息，设置为EPSG:4326")
                gdf = gdf.set_crs('EPSG:4326')
            
            # 生成表名
            table_name = f"shp_{file_id.replace('-', '_')}"
            
            # 创建数据库连接
            connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            engine = create_engine(connection_string, echo=False)
            
            # 将几何列重命名为'geom'以符合PostGIS标准
            if gdf.geometry.name != 'geom':
                gdf = gdf.rename_geometry('geom')
            
            # 存入PostGIS
            gdf.to_postgis(
                name=table_name,
                con=engine,
                if_exists='replace',
                index=True,
                index_label='id'
            )
            
            # 创建空间索引
            with engine.connect() as conn:
                index_sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_geom ON {table_name} USING GIST (geom)"
                conn.execute(text(index_sql))
                conn.commit()
            
            # 分析几何类型
            geometry_types = set()
            for geom in gdf.geometry:
                if geom is not None and not geom.is_empty:
                    geometry_types.add(geom.geom_type)
            
            result = {
                "success": True,
                "table_name": table_name,
                "schema": "public",
                "full_table_name": f"public.{table_name}",
                "geometry_types": sorted(list(geometry_types)),
                "feature_count": len(gdf),
                "is_mixed": len(geometry_types) > 1
            }
            
            print(f"✅ SHP数据存入PostGIS成功: {table_name}")
            return result
            
        except Exception as e:
            print(f"❌ 存入PostGIS失败: {str(e)}")
            raise Exception(f"存入PostGIS失败: {str(e)}")
    
    def _record_to_database(self, file_id, original_filename, file_path, analysis, postgis_result, user_id):
        """记录服务信息到数据库"""
        try:
            table_name = postgis_result["table_name"]
            mvt_url = f"http://localhost:3000/{table_name}/{{z}}/{{x}}/{{y}}"
            tilejson_url = f"http://localhost:3000/{table_name}"
            
            # 创建默认样式
            default_style = {
                "version": 8,
                "name": f"style_{table_name}",
                "sources": {
                    table_name: {
                        "type": "vector",
                        "url": tilejson_url
                    }
                },
                "layers": [
                    {
                        "id": f"layer_{table_name}",
                        "source": table_name,
                        "source-layer": table_name,
                        "type": "line",
                        "paint": {
                            "line-color": "#000000",
                            "line-width": 1
                        }
                    }
                ]
            }
            
            params = {
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': file_path,
                'table_name': table_name,
                'service_url': f"http://localhost:3000/{table_name}",
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
                'style': json.dumps(default_style),
                'shp_info': json.dumps(analysis),
                'postgis_info': json.dumps(postgis_result),
                'user_id': user_id
            }
            
            record_id = insert_with_snowflake_id('shp_martin_services', params)
            
            print(f"✅ 服务记录已保存到数据库，ID: {record_id}")
            print(f"   - MVT URL: {mvt_url}")
            print(f"   - TileJSON URL: {tilejson_url}")
            
            return record_id
            
        except Exception as e:
            print(f"❌ 保存服务记录到数据库失败: {str(e)}")
            raise
    
    def _setup_martin_service(self, table_name):
        """设置Martin服务"""
        try:
            # 检查Martin是否启用
            if not self.martin_service.is_enabled():
                return {
                    "enabled": False,
                    "message": "Martin服务未启用"
                }
            
            # 刷新Martin配置和服务
            success = self.martin_service.refresh_tables()
            
            if success:
                # 获取MVT URL
                source_id = f"public.{table_name}"
                mvt_url = self.martin_service.get_mvt_url(source_id)
                tilejson_url = f"{self.martin_service.base_url}/{source_id}"
                
                return {
                    "enabled": True,
                    "running": True,
                    "mvt_url": mvt_url,
                    "tilejson_url": tilejson_url,
                    "source_id": source_id,
                    "message": "Martin服务配置成功"
                }
            else:
                return {
                    "enabled": True,
                    "running": False,
                    "message": "Martin服务启动失败"
                }
                
        except Exception as e:
            print(f"⚠️ 配置Martin服务失败: {e}")
            return {
                "enabled": True,
                "running": False,
                "error": str(e),
                "message": "Martin服务配置失败"
            }
    
    def _safe_json_parse(self, json_field):
        """安全解析JSON字段"""
        if json_field is None:
            return {}
        
        if isinstance(json_field, dict):
            return json_field
        
        try:
            if isinstance(json_field, str):
                return json.loads(json_field)
            return json_field
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def _cleanup_failed_publish(self, local_vars):
        """清理失败发布可能创建的资源"""
        try:
            # 这里可以添加清理逻辑，比如删除已创建的数据库表等
            # 目前暂时留空，因为PostGIS服务会处理自己的清理
            pass
        except Exception as e:
            print(f"⚠️ 清理失败发布资源时出错: {e}") 