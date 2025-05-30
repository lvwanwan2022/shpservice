#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DXF服务发布类
提供DXF文件的Martin和GeoServer服务发布功能
"""

import os
import uuid
import tempfile
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from werkzeug.utils import secure_filename

from config import FILE_STORAGE, DB_CONFIG
from models.db import execute_query
from services.dxf_processor import DXFProcessor
from services.martin_service import MartinService
from services.geoserver_service import GeoServerService

logger = logging.getLogger(__name__)

class DXFService:
    """DXF服务发布类，统一处理Martin和GeoServer服务发布"""
    
    def __init__(self):
        """初始化DXF服务"""
        self.upload_folder = os.path.join(FILE_STORAGE['upload_folder'], 'dxf')
        self.dxf_processor = DXFProcessor()
        self.martin_service = MartinService()
        self.geoserver_service = GeoServerService()
        
        # 数据库连接
        db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(db_url)
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        
        logger.info("✅ DXF服务初始化完成")

    def publish_dxf_martin_service(self, file_id, file_path, original_filename, coordinate_system='EPSG:4326', user_id=None):
        """
        发布DXF文件为Martin MVT服务
        
        Args:
            file_id: 文件ID
            file_path: DXF文件路径
            original_filename: 原始文件名
            coordinate_system: 坐标系
            user_id: 用户ID
            
        Returns:
            dict: 发布结果
        """
        try:
            logger.info(f"开始发布DXF Martin服务: {file_id}")
            
            # 1. 生成表名
            table_name = f"dxf_{uuid.uuid4().hex[:8]}"
            
            # 2. 将DXF导入PostGIS
            logger.info("步骤1: 导入DXF到PostGIS...")
            import_result = self.dxf_processor.process_dxf_file(
                file_path, 
                table_name, 
                coordinate_system
            )
            
            if not import_result.get('success'):
                raise Exception(f"DXF导入PostGIS失败: {import_result.get('error')}")
            
            logger.info(f"✅ DXF导入PostGIS成功: {table_name}")
            
            # 3. 配置Martin服务
            logger.info("步骤2: 配置Martin服务...")
            martin_result = self._setup_martin_service(table_name)
            
            if not martin_result.get('enabled') or not martin_result.get('running'):
                raise Exception("Martin服务配置失败")
            
            # 4. 记录到vector_martin_services表
            logger.info("步骤3: 记录Martin服务信息...")
            service_record = self._record_martin_service(
                file_id, 
                original_filename,
                file_path,
                table_name,
                coordinate_system,
                martin_result,
                import_result,
                user_id
            )
            
            logger.info("✅ DXF Martin服务发布成功")
            
            return {
                'success': True,
                'service_type': 'martin',
                'table_name': table_name,
                'service_record': service_record,
                'martin_info': martin_result,
                'import_info': import_result
            }
            
        except Exception as e:
            logger.error(f"DXF Martin服务发布失败: {str(e)}")
            # 清理可能创建的表
            try:
                if 'table_name' in locals():
                    with self.engine.connect() as conn:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        conn.commit()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }

    def publish_dxf_geoserver_service(self, file_id, table_name=None, coordinate_system='EPSG:4326'):
        """
        发布DXF文件为GeoServer WMS/WFS服务
        如果table_name为None，会先导入PostGIS；如果已存在则直接发布
        
        Args:
            file_id: 文件ID
            table_name: PostGIS表名（可选，如果已导入可复用）
            coordinate_system: 坐标系
            
        Returns:
            dict: 发布结果
        """
        try:
            logger.info(f"开始发布DXF GeoServer服务: {file_id}")
            
            # 1. 获取文件信息
            file_info = self._get_file_info(file_id)
            if not file_info:
                raise Exception(f"文件不存在: {file_id}")
            
            # 2. 如果没有提供table_name，需要先导入PostGIS
            if not table_name:
                logger.info("未提供表名，开始导入PostGIS...")
                table_name = f"dxf_{uuid.uuid4().hex[:8]}"
                
                import_result = self.dxf_processor.process_dxf_file(
                    file_info['file_path'], 
                    table_name, 
                    coordinate_system
                )
                
                if not import_result.get('success'):
                    raise Exception(f"DXF导入PostGIS失败: {import_result.get('error')}")
                    
                logger.info(f"✅ DXF导入PostGIS成功: {table_name}")
            else:
                logger.info(f"复用已存在的PostGIS表: {table_name}")
            
            # 3. 发布到GeoServer
            logger.info("发布到GeoServer...")
            layer_name = f"dxf_{file_id}_{uuid.uuid4().hex[:6]}"
            
            geoserver_result = self.geoserver_service.publish_postgis_layer(
                table_name=table_name,
                layer_name=layer_name,
                workspace='dxf_data',
                title=f"DXF: {file_info['file_name']}",
                abstract=f"DXF file imported from {file_info['file_name']}"
            )
            
            if not geoserver_result.get('success'):
                raise Exception(f"GeoServer发布失败: {geoserver_result.get('error')}")
            
            # 4. 记录GeoServer服务信息
            logger.info("记录GeoServer服务信息...")
            service_record = self._record_geoserver_service(
                file_id,
                table_name,
                layer_name,
                geoserver_result
            )
            
            logger.info("✅ DXF GeoServer服务发布成功")
            
            return {
                'success': True,
                'service_type': 'geoserver',
                'table_name': table_name,
                'layer_name': layer_name,
                'service_record': service_record,
                'geoserver_info': geoserver_result
            }
            
        except Exception as e:
            logger.error(f"DXF GeoServer服务发布失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def publish_dxf_both_services(self, file_id, file_path, original_filename, coordinate_system='EPSG:4326', user_id=None):
        """
        同时发布Martin和GeoServer服务（共用PostGIS表）
        
        Returns:
            dict: 发布结果
        """
        try:
            logger.info(f"开始发布DXF双服务: {file_id}")
            
            # 1. 先发布Martin服务（包含PostGIS导入）
            martin_result = self.publish_dxf_martin_service(
                file_id, file_path, original_filename, coordinate_system, user_id
            )
            
            if not martin_result['success']:
                return {
                    'success': False,
                    'error': f"Martin服务发布失败: {martin_result['error']}"
                }
            
            table_name = martin_result['table_name']
            
            # 2. 基于已导入的表发布GeoServer服务
            geoserver_result = self.publish_dxf_geoserver_service(
                file_id, table_name, coordinate_system
            )
            
            return {
                'success': True,
                'table_name': table_name,
                'martin_result': martin_result,
                'geoserver_result': geoserver_result,
                'message': '双服务发布完成'
            }
            
        except Exception as e:
            logger.error(f"DXF双服务发布失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _setup_martin_service(self, table_name):
        """配置Martin服务"""
        try:
            # 检查Martin是否启用
            if not self.martin_service.is_enabled():
                return {
                    "enabled": False,
                    "running": False,
                    "message": "Martin服务未启用"
                }
            
            # 刷新Martin配置
            success = self.martin_service.refresh_tables()
            
            if success:
                # 生成MVT服务URL
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
            logger.error(f"配置Martin服务失败: {str(e)}")
            return {
                "enabled": True,
                "running": False,
                "error": str(e),
                "message": "Martin服务配置失败"
            }

    def _record_martin_service(self, file_id, original_filename, file_path, table_name, 
                              coordinate_system, martin_result, import_result, user_id):
        """记录Martin服务到vector_martin_services表"""
        try:
            insert_sql = """
            INSERT INTO vector_martin_services (
                file_id, original_filename, file_path, table_name, 
                coordinate_system, mvt_url, tilejson_url, source_id,
                vector_type, status, created_at, updated_at, user_id
            ) VALUES (
                %(file_id)s, %(original_filename)s, %(file_path)s, %(table_name)s,
                %(coordinate_system)s, %(mvt_url)s, %(tilejson_url)s, %(source_id)s,
                %(vector_type)s, %(status)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %(user_id)s
            ) RETURNING id;
            """
            
            params = {
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': file_path,
                'table_name': table_name,
                'coordinate_system': coordinate_system,
                'mvt_url': martin_result.get('mvt_url'),
                'tilejson_url': martin_result.get('tilejson_url'),
                'source_id': martin_result.get('source_id'),
                'vector_type': 'dxf',
                'status': 'active',
                'user_id': user_id
            }
            
            result = execute_query(insert_sql, params)
            service_id = result[0]['id'] if result else None
            
            logger.info(f"✅ Martin服务记录成功，ID: {service_id}")
            
            return {
                'service_id': service_id,
                **params
            }
            
        except Exception as e:
            logger.error(f"记录Martin服务失败: {str(e)}")
            raise

    def _record_geoserver_service(self, file_id, table_name, layer_name, geoserver_result):
        """记录GeoServer服务信息"""
        try:
            # 这里可以创建一个专门的DXF GeoServer服务表，或者扩展现有表
            # 暂时返回基本信息
            return {
                'file_id': file_id,
                'table_name': table_name,
                'layer_name': layer_name,
                'wms_url': geoserver_result.get('wms_url'),
                'wfs_url': geoserver_result.get('wfs_url'),
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"记录GeoServer服务失败: {str(e)}")
            raise

    def _get_file_info(self, file_id):
        """获取文件信息"""
        try:
            sql = "SELECT * FROM files WHERE id = %(file_id)s"
            result = execute_query(sql, {'file_id': file_id})
            return result[0] if result else None
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None

    def get_dxf_martin_services(self, file_id=None, status='active'):
        """获取DXF Martin服务列表"""
        try:
            sql = """
            SELECT * FROM vector_martin_services
            WHERE vector_type = 'dxf' AND status = %(status)s
            """
            params = {'status': status}
            
            if file_id:
                sql += " AND file_id = %(file_id)s"
                params['file_id'] = file_id
            
            sql += " ORDER BY created_at DESC"
            
            return execute_query(sql, params)
            
        except Exception as e:
            logger.error(f"获取DXF Martin服务失败: {str(e)}")
            return []

    def delete_dxf_martin_service(self, service_id):
        """删除DXF Martin服务"""
        try:
            # 获取服务信息
            sql = "SELECT * FROM vector_martin_services WHERE id = %(service_id)s AND vector_type = 'dxf'"
            service = execute_query(sql, {'service_id': service_id})
            
            if not service:
                return {'success': False, 'error': '服务不存在'}
            
            service = service[0]
            table_name = service['table_name']
            
            # 删除PostGIS表
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
                logger.info(f"✅ PostGIS表已删除: {table_name}")
            
            # 更新服务状态
            update_sql = """
            UPDATE vector_martin_services 
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP 
            WHERE id = %(service_id)s
            """
            execute_query(update_sql, {'service_id': service_id}, fetch=False)
            
            # 刷新Martin服务
            try:
                self.martin_service.refresh_tables()
            except Exception as e:
                logger.warning(f"刷新Martin服务失败: {e}")
            
            logger.info(f"✅ DXF Martin服务删除成功: {service_id}")
            
            return {
                'success': True,
                'service_id': service_id,
                'table_name': table_name
            }
            
        except Exception as e:
            logger.error(f"删除DXF Martin服务失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# 便捷函数
def publish_dxf_martin(file_id, file_path, original_filename, coordinate_system='EPSG:4326', user_id=None):
    """发布DXF Martin服务的便捷函数"""
    service = DXFService()
    return service.publish_dxf_martin_service(file_id, file_path, original_filename, coordinate_system, user_id)

def publish_dxf_geoserver(file_id, table_name=None, coordinate_system='EPSG:4326'):
    """发布DXF GeoServer服务的便捷函数"""
    service = DXFService()
    return service.publish_dxf_geoserver_service(file_id, table_name, coordinate_system)

def publish_dxf_both(file_id, file_path, original_filename, coordinate_system='EPSG:4326', user_id=None):
    """发布DXF双服务的便捷函数"""
    service = DXFService()
    return service.publish_dxf_both_services(file_id, file_path, original_filename, coordinate_system, user_id) 