#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GeoJSON Martin服务类
使用geopandas将GeoJSON数据存入PostGIS，然后通过Martin发布MVT瓦片服务
"""

import os
import json
import uuid
import tempfile
import warnings
from datetime import datetime
from werkzeug.utils import secure_filename

from config import FILE_STORAGE, DB_CONFIG
from models.db import execute_query
from services.postgis_service import PostGISService
from services.martin_service import MartinService


class GeoJsonMartinService:
    """GeoJSON Martin服务类，提供完整的GeoJSON到MVT瓦片服务的发布流程"""
    
    def __init__(self):
        """初始化服务"""
        self.upload_folder = os.path.join(FILE_STORAGE['upload_folder'], 'geojson')
        self.postgis_service = PostGISService()
        self.martin_service = MartinService()
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        
        print("✅ GeoJSON Martin服务初始化完成")
        print(f"   - PostGIS模式: {'geopandas' if self.postgis_service.use_geopandas else '手动实现'}")
        print(f"   - Martin服务: {'启用' if self.martin_service.is_enabled() else '禁用'}")
    
    def publish_geojson_service(self, file_obj, file_info):
        """发布GeoJSON为MVT瓦片服务
        
        完整流程：
        1. 验证和保存GeoJSON文件
        2. 使用geopandas将数据存入PostGIS
        3. 刷新Martin配置并重启服务
        4. 返回MVT瓦片服务信息
        
        Args:
            file_obj: 文件对象
            file_info: 文件信息字典，包含original_filename, user_id等
            
        Returns:
            包含服务信息的字典
        """
        try:
            print(f"\n=== 开始发布GeoJSON为MVT瓦片服务 ===")
            
            # 1. 验证文件格式
            original_filename = file_info.get('original_filename')
            if not original_filename.lower().endswith(('.geojson', '.json')):
                raise ValueError("只支持.geojson或.json文件")
            
            # 2. 读取和验证GeoJSON内容
            file_content = file_obj.read()
            geojson_data = json.loads(file_content)
            
            # 验证GeoJSON格式
            self._validate_geojson(geojson_data)
            
            # 3. 生成唯一文件ID和表名
            file_id = str(uuid.uuid4())
            table_name = f"geojson_{file_id.replace('-', '_')}"
            
            print(f"文件ID: {file_id}")
            print(f"表名: {table_name}")
            
            # 4. 保存GeoJSON文件到本地
            file_path = self._save_geojson_file(file_content, file_id, original_filename)
            
            # 5. 分析GeoJSON特性
            analysis = self._analyze_geojson(geojson_data)
            print(f"GeoJSON分析结果: {analysis}")
            
            # 6. 使用PostGIS服务将数据存入数据库
            print("\n--- 将GeoJSON存入PostGIS ---")
            postgis_result = self.postgis_service.store_geojson(file_path, file_id)
            
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
                
                # GeoJSON文件信息
                "geojson_info": {
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
            
            print(f"✅ GeoJSON MVT瓦片服务发布成功")
            print(f"   - 文件ID: {file_id}")
            print(f"   - 表名: {postgis_result['table_name']}")
            print(f"   - MVT URL: {martin_result.get('mvt_url', 'N/A')}")
            
            return result
            
        except Exception as e:
            print(f"❌ 发布GeoJSON服务失败: {str(e)}")
            # 清理可能创建的资源
            self._cleanup_failed_publish(locals())
            raise
    
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
            SELECT * FROM geojson_martin_services 
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
                
                # 解析JSON字段 - 修复：检查是否已经是字典类型
                "geojson_info": self._safe_json_parse(service_record['geojson_info']),
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
                   geojson_info, postgis_info, service_url
            FROM geojson_martin_services
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
                # 解析JSON字段 - 修复：检查是否已经是字典类型
                geojson_info = self._safe_json_parse(service['geojson_info'])
                postgis_info = self._safe_json_parse(service['postgis_info'])
                
                # 获取MVT信息 - 添加验证逻辑
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
                    
                    # 从geojson_info中提取的字段
                    "feature_count": geojson_info.get('feature_count', 0),
                    "geometry_types": geojson_info.get('geometry_types', []),
                    "bbox": geojson_info.get('bbox'),
                    
                    # 完整的geojson_info和postgis_info
                    "geojson_info": geojson_info,
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
    
    def delete_service(self, file_id, user_id=None):
        """删除已发布的服务
        
        Args:
            file_id: 文件ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            删除结果
        """
        try:
            print(f"\n=== 删除GeoJSON服务: {file_id} ===")
            
            # 获取服务记录
            sql = "SELECT * FROM geojson_martin_services WHERE file_id = %s AND status = 'active'"
            result = execute_query(sql, (file_id,))
            
            if not result:
                raise ValueError(f"服务不存在: {file_id}")
            
            service_record = result[0]
            
            # 权限检查
            if user_id is not None and service_record['user_id'] != user_id:
                raise ValueError("没有权限删除此服务")
            
            table_name = service_record['table_name']
            file_path = service_record['file_path']
            
            # 1. 删除PostGIS表
            try:
                print(f"准备删除PostGIS表: {table_name}")
                self._drop_postgis_table(table_name)
                print(f"✅ 已删除PostGIS表: {table_name}")
                
                # 验证表是否真的被删除
                conn_verify = self.postgis_service.get_connection()
                try:
                    cursor_verify = conn_verify.cursor()
                    cursor_verify.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public'
                            AND table_name = %s
                        )
                    """, (table_name,))
                    table_exists = cursor_verify.fetchone()[0]
                    
                    if table_exists:
                        print(f"⚠️ 警告: 表 {table_name} 在删除操作后仍然存在")
                    else:
                        print(f"✅ 确认: 表 {table_name} 已成功删除")
                        
                finally:
                    conn_verify.close()
                    
            except Exception as e:
                print(f"⚠️ 删除PostGIS表失败: {e}")
                # 打印详细的错误信息
                import traceback
                print(f"详细错误信息: {traceback.format_exc()}")
            
            # 2. 保留源文件 - 取消服务发布不应该删除原始文件
            # 注意：这里不删除 file_path 指向的源文件，因为:
            # - 源文件可能被其他服务或用户使用
            # - 取消发布服务只是停止Martin服务，不是删除数据
            # - 用户可能之后还想重新发布服务
            print(f"✅ 保留源文件: {file_path} (取消发布不删除源文件)")
            
            # 3. 更新数据库记录状态
            update_sql = """
            UPDATE geojson_martin_services 
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP 
            WHERE file_id = %s
            """
            execute_query(update_sql, (file_id,))
            print(f"✅ 数据库记录状态已更新为'deleted'")
            
            # 4. 刷新Martin服务
            try:
                self.martin_service.refresh_tables()
                print("✅ Martin服务已刷新")
            except Exception as e:
                print(f"⚠️ 刷新Martin服务失败: {e}")
            
            print(f"✅ Martin服务取消发布成功: {file_id}")
            print("注意: 源文件已保留，如需删除请使用文件管理功能")
            
            return {
                "success": True,
                "file_id": file_id,
                "message": "Martin服务取消发布成功，源文件已保留"
            }
            
        except Exception as e:
            print(f"❌ 删除服务失败: {str(e)}")
            raise
    
    def get_martin_status(self):
        """获取Martin服务状态"""
        return self.martin_service.get_status()
    
    def restart_martin_service(self):
        """重启Martin服务"""
        try:
            self.martin_service.stop_service()
            success = self.martin_service.start_service()
            return {
                "success": success,
                "message": "Martin服务重启成功" if success else "Martin服务重启失败"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"重启失败: {str(e)}"
            }
    
    def publish_existing_file(self, file_id, user_id=None):
        """发布已上传的GeoJSON文件到Martin服务
        
        Args:
            file_id: 文件ID (数据库中的files表ID)
            user_id: 用户ID (可选，用于权限检查)
            
        Returns:
            包含服务信息的字典
        """
        try:
            print(f"\n=== 发布已存在文件到Martin服务: {file_id} ===")
            
            # 1. 从数据库获取文件信息
            file_sql = """
            SELECT id, file_name, file_path, file_type, user_id, upload_date
            FROM files 
            WHERE id = %s AND file_type = 'geojson'
            """
            file_result = execute_query(file_sql, (file_id,))
            
            if not file_result:
                raise ValueError(f"文件不存在或不是GeoJSON类型: {file_id}")
            
            file_info = file_result[0]
            
            # 权限检查（如果提供了user_id）
            if user_id and file_info['user_id'] != user_id:
                raise ValueError("没有权限发布此文件")
            
            print(f"文件信息: {file_info['file_name']}")
            
            # 2. 检查是否已经发布到Martin
            existing_sql = """
            SELECT file_id FROM geojson_martin_services 
            WHERE original_filename = %s AND status = 'active'
            """
            existing_result = execute_query(existing_sql, (file_info['file_name'],))
            
            if existing_result:
                raise ValueError(f"文件已发布到Martin服务: {existing_result[0]['file_id']}")
            
            # 3. 读取GeoJSON文件
            file_path = file_info['file_path']
            if not os.path.exists(file_path):
                raise ValueError(f"文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                geojson_data = json.loads(file_content)
            
            # 验证GeoJSON格式
            self._validate_geojson(geojson_data)
            
            # 4. 生成新的服务ID和表名
            service_file_id = str(uuid.uuid4())
            table_name = f"geojson_{service_file_id.replace('-', '_')}"
            
            print(f"服务文件ID: {service_file_id}")
            print(f"表名: {table_name}")
            
            # 5. 分析GeoJSON特性
            analysis = self._analyze_geojson(geojson_data)
            print(f"GeoJSON分析结果: {analysis}")
            
            # 6. 使用PostGIS服务将数据存入数据库
            print("\n--- 将GeoJSON存入PostGIS ---")
            postgis_result = self.postgis_service.store_geojson(file_path, service_file_id)
            
            if not postgis_result.get('success'):
                raise Exception("PostGIS数据存储失败")
            
            print(f"✅ 数据已存入PostGIS表: {postgis_result['table_name']}")
            
            # 7. 记录到Martin服务数据库
            db_record_id = self._record_to_database(
                service_file_id, file_info['file_name'], file_path, analysis, 
                postgis_result, file_info['user_id']
            )
            
            # 8. 启动/刷新Martin服务
            print("\n--- 配置Martin服务 ---")
            martin_result = self._setup_martin_service(postgis_result['table_name'])
            
            # 9. 构建返回结果
            result = {
                "success": True,
                "file_id": service_file_id,
                "original_file_id": file_id,  # 原始文件ID
                "original_filename": file_info['file_name'],
                "table_name": postgis_result['table_name'],
                "database_record_id": db_record_id,
                
                # GeoJSON文件信息
                "geojson_info": {
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
    
    # === 私有方法 ===
    
    def _validate_geojson(self, geojson_data):
        """验证GeoJSON格式"""
        if not isinstance(geojson_data, dict):
            raise ValueError("无效的GeoJSON格式：必须是JSON对象")
        
        geojson_type = geojson_data.get('type')
        if geojson_type not in ['FeatureCollection', 'Feature', 'Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']:
            raise ValueError(f"无效的GeoJSON类型: {geojson_type}")
        
        # 检查是否有要素
        if geojson_type == 'FeatureCollection':
            features = geojson_data.get('features', [])
            if not features:
                raise ValueError("FeatureCollection中没有要素")
        
        print("✅ GeoJSON格式验证通过")
    
    def _save_geojson_file(self, file_content, file_id, original_filename):
        """保存GeoJSON文件到本地"""
        file_path = os.path.join(self.upload_folder, f"{file_id}.geojson")
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        print(f"✅ 文件已保存: {file_path}")
        return file_path
    
    def _analyze_geojson(self, geojson_data):
        """分析GeoJSON数据"""
        analysis = {
            "feature_count": 0,
            "geometry_types": set(),
            "properties": {},
            "bbox": None
        }
        
        # 处理FeatureCollection
        if geojson_data.get('type') == 'FeatureCollection':
            features = geojson_data.get('features', [])
            analysis['feature_count'] = len(features)
            
            # 分析几何类型和属性
            for feature in features:
                if 'geometry' in feature and feature['geometry']:
                    geom_type = feature['geometry'].get('type')
                    if geom_type:
                        analysis['geometry_types'].add(geom_type)
                
                # 分析属性（使用第一个有属性的要素）
                if 'properties' in feature and feature['properties'] and not analysis['properties']:
                    for key, value in feature['properties'].items():
                        if value is not None:
                            if isinstance(value, int):
                                analysis['properties'][key] = 'integer'
                            elif isinstance(value, float):
                                analysis['properties'][key] = 'double precision'
                            elif isinstance(value, bool):
                                analysis['properties'][key] = 'boolean'
                            else:
                                analysis['properties'][key] = 'text'
        
        # 处理单个Feature
        elif geojson_data.get('type') == 'Feature':
            analysis['feature_count'] = 1
            if 'geometry' in geojson_data and geojson_data['geometry']:
                geom_type = geojson_data['geometry'].get('type')
                if geom_type:
                    analysis['geometry_types'].add(geom_type)
        
        # 转换set为list
        analysis['geometry_types'] = sorted(list(analysis['geometry_types']))
        
        return analysis
    
    def _record_to_database(self, file_id, original_filename, file_path, analysis, postgis_result, user_id):
        """记录服务信息到数据库
        
        Args:
            file_id: 文件ID
            original_filename: 原始文件名
            file_path: 文件路径
            analysis: GeoJSON分析结果
            postgis_result: PostGIS存储结果
            user_id: 用户ID
            
        Returns:
            数据库记录ID
        """
        try:
            table_name = postgis_result['table_name']
            
            # 构建MVT和TileJSON URL
            mvt_url = f"http://localhost:3000/{table_name}/{{z}}/{{x}}/{{y}}.pbf"
            tilejson_url = f"http://localhost:3000/{table_name}"
            
            # 默认样式配置
            default_style = {
                "version": 8,
                "name": f"Style for {original_filename}",
                "sources": {
                    table_name: {
                        "type": "vector",
                        "tiles": [mvt_url],
                        "maxzoom": 14
                    }
                },
                "layers": [
                    {
                        "id": f"{table_name}-layer",
                        "source": table_name,
                        "source-layer": table_name,
                        "type": "fill",
                        "paint": {
                            "fill-color": "#3388ff",
                            "fill-opacity": 0.6,
                            "fill-outline-color": "#ffffff"
                        }
                    }
                ]
            }
            
            sql = """
            INSERT INTO geojson_martin_services 
            (file_id, original_filename, file_path, table_name, service_url, mvt_url, tilejson_url, style, geojson_info, postgis_info, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                file_id,
                original_filename,
                file_path,
                table_name,
                f"http://localhost:3000/{table_name}",  # service_url
                mvt_url,
                tilejson_url,
                json.dumps(default_style),
                json.dumps(analysis),
                json.dumps(postgis_result),
                user_id
            )
            
            result = execute_query(sql, params)
            record_id = result[0]['id']
            
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
    
    def _drop_postgis_table(self, table_name):
        """删除PostGIS表"""
        conn = None
        try:
            conn = self.postgis_service.get_connection()
            cursor = conn.cursor()
            
            # 使用安全的SQL构建方式
            from psycopg2 import sql
            drop_table_sql = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                sql.Identifier(table_name)
            )
            
            print(f"正在删除PostGIS表: {table_name}")
            cursor.execute(drop_table_sql)
            conn.commit()
            print(f"✅ PostGIS表 {table_name} 删除成功")
            
        except Exception as e:
            print(f"❌ 删除PostGIS表失败: {str(e)}")
            if conn:
                conn.rollback()
            # 不抛出异常，允许删除流程继续
            print(f"⚠️ 继续执行删除流程，但表 {table_name} 可能仍然存在")
        finally:
            if conn:
                conn.close()
    
    def _cleanup_failed_publish(self, local_vars):
        """清理发布失败时可能创建的资源"""
        try:
            # 清理文件
            if 'file_path' in local_vars and local_vars['file_path']:
                try:
                    os.unlink(local_vars['file_path'])
                except:
                    pass
            
            # 清理PostGIS表
            if 'postgis_result' in local_vars and local_vars['postgis_result']:
                table_name = local_vars['postgis_result'].get('table_name')
                if table_name:
                    try:
                        self._drop_postgis_table(table_name)
                    except:
                        pass
            
        except Exception as e:
            print(f"⚠️ 清理资源失败: {e}")
    
    def _safe_json_parse(self, value):
        """安全的JSON解析，处理已经是字典的情况"""
        if value is None:
            return {}
        elif isinstance(value, (dict, list)):
            # 如果已经是字典或列表，直接返回
            return value
        elif isinstance(value, str):
            # 如果是字符串，尝试JSON解析
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            return {} 