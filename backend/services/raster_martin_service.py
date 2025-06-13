#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import uuid
import zipfile
import tempfile
import shutil
import geopandas as gpd
from pathlib import Path
from models.db import execute_query
from sqlalchemy import create_engine, text
from config import DB_CONFIG, MARTIN_CONFIG

class RasterMartinService:
    """统一的栅格Martin服务类，处理MBTiles文件的Martin服务发布"""
    
    def __init__(self):
        """初始化服务"""
        # 构建PostgreSQL连接字符串
        self.db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(self.db_url)
        
    def publish_mbtiles_martin(self, file_id, file_path, original_filename, user_id=None):
        """发布MBTiles文件为Martin服务
        
        Args:
            file_id: 文件ID
            file_path: MBTiles文件路径
            original_filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            发布结果字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'MBTiles文件不存在: {file_path}'
                }
            
            # 从文件名生成表名（不使用实际的PostGIS表，只是为了生成唯一标识符）
            table_name = f"mbtiles_{uuid.uuid4().hex[:8]}"
            
            # 构建Martin服务URL
            # 对于MBTiles文件，Martin会自动从mbtiles目录加载
            # 服务URL格式为: http://localhost:3000/mbtiles/{文件名不带扩展名}
            file_basename = os.path.basename(file_path)
            file_name_without_ext = os.path.splitext(file_basename)[0]
            
            service_url = f"{MARTIN_CONFIG['base_url']}/mbtiles/{file_name_without_ext}"
            mvt_url = f"{service_url}/{{z}}/{{x}}/{{y}}"
            tilejson_url = f"{service_url}"
            
            # 保存服务信息到数据库,共用vector_martin_services表，vector_type为raster
            insert_sql = """
            INSERT INTO vector_martin_services 
            (file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, user_id)
            VALUES (%(file_id)s, %(original_filename)s, %(file_path)s, %(vector_type)s, %(table_name)s, %(service_url)s, %(mvt_url)s, %(tilejson_url)s, %(user_id)s)
            RETURNING id
            """
            
            params = {
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': file_path,
                'vector_type': 'mbtiles',
                'table_name': table_name,  # 使用生成的唯一表名
                'service_url': service_url,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
                'user_id': user_id
            }
            
            result = execute_query(insert_sql, params)
            service_id = result[0]['id']
            
            print(f"✅ MBTiles Martin服务发布成功，服务ID: {service_id}")
            
            return {
                'success': True,
                'service_id': service_id,
                'service_url': service_url,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
            }
            
        except Exception as e:
            print(f"❌ MBTiles Martin服务发布失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_martin_services(self, vector_type='mbtiles', status='active'):
        """获取Martin服务列表
        
        Args:
            vector_type: 矢量类型过滤 ('mbtiles', None)
            status: 状态过滤
            
        Returns:
            服务列表
        """
        sql = """
        SELECT * FROM vector_martin_services
        WHERE status = %(status)s
        """
        
        params = {'status': status}
        
        if vector_type:
            sql += " AND vector_type = %(vector_type)s"
            params['vector_type'] = vector_type
        
        sql += " ORDER BY created_at DESC"
        
        return execute_query(sql, params)
    
    def get_martin_service_by_id(self, service_id):
        """根据ID获取Martin服务信息
        
        Args:
            service_id: 服务ID
            
        Returns:
            服务信息
        """
        sql = """
        SELECT * FROM vector_martin_services
        WHERE id = %(service_id)s AND status = 'active'
        """
        
        result = execute_query(sql, {'service_id': service_id})
        return result[0] if result else None
    
    def delete_martin_service(self, service_id):
        """删除Martin服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            删除是否成功
        """
        try:
            # 获取服务信息
            service = self.get_martin_service_by_id(service_id)
            if not service:
                return False
            
            # 对于MBTiles服务，不需要删除PostGIS表，只需更新服务状态
            # 更新服务状态为已删除
            sql = """
            UPDATE vector_martin_services
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE id = %(service_id)s
            """
            
            execute_query(sql, {'service_id': service_id}, fetch=False)
            print(f"✅ MBTiles Martin服务已删除: {service_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 删除Martin服务失败: {str(e)}")
            return False 