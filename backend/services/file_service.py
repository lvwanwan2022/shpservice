#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from config import FILE_STORAGE
from models.db import execute_query
from services.geoserver_service import GeoServerService

class FileService:
    """文件服务类，用于处理文件上传、存储和元数据管理"""
    
    def __init__(self):
        self.upload_folder = FILE_STORAGE['upload_folder']
        self.allowed_extensions = FILE_STORAGE['allowed_extensions']
        self.max_file_size = FILE_STORAGE['max_file_size']
        self.geoserver = GeoServerService()
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        """检查文件是否允许上传"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_file(self, file, metadata):
        """保存上传文件并记录元数据"""
        # 验证文件
        if not file:
            raise ValueError("未找到上传文件")
        
        filename = secure_filename(file.filename)
        if not self.allowed_file(filename):
            raise ValueError(f"不支持的文件类型，允许的类型: {', '.join(self.allowed_extensions)}")
        
        # 生成唯一文件名
        extension = filename.rsplit('.', 1)[1].lower()
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
        
        # 准备元数据
        file_data = {
            'file_name': metadata.get('file_name'),
            'file_path': file_path,
            'original_name': filename,
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
        
        # 根据文件类型发布到GeoServer
        self._publish_to_geoserver(file_path, file_id, metadata)
        
        return file_id, file_data
    
    def _publish_to_geoserver(self, file_path, file_id, metadata):
        """根据文件类型发布到GeoServer"""
        file_type = metadata.get('file_type').lower()
        store_name = f"file_{file_id}"
        
        result = None
        
        try:
            if file_type == 'shp':
                # 发布shapefile
                result = self.geoserver.publish_shapefile(file_path, store_name)
            elif file_type in ['dem', 'dom']:
                # 发布geotiff
                result = self.geoserver.publish_geotiff(file_path, store_name)
            elif file_type in ['dwg', 'dxf']:
                # 发布DWG/DXF
                coord_system = metadata.get('coordinate_system', 'EPSG:4326')
                result = self.geoserver.publish_dwg_dxf(file_path, store_name, coord_system)
            elif file_type == 'geojson':
                # 发布GeoJSON
                result = self.geoserver.publish_geojson(file_path, store_name)
        except Exception as e:
            # 记录错误，但不阻止文件上传
            print(f"发布到GeoServer失败: {str(e)}")
        
        # 如果发布成功，更新数据库
        if result:
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
    
    def get_files(self, filters=None, page=1, page_size=12):
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
            
            if 'tags' in filters and filters['tags']:
                base_sql += " AND f.tags LIKE %(tags)s"
                count_sql += " AND f.tags LIKE %(tags)s"
                params['tags'] = f"%{filters['tags']}%"
            
            if 'file_name' in filters and filters['file_name']:
                base_sql += " AND f.file_name LIKE %(file_name)s"
                count_sql += " AND f.file_name LIKE %(file_name)s"
                params['file_name'] = f"%{filters['file_name']}%"
        
        # 添加分页
        base_sql += " ORDER BY f.upload_date DESC LIMIT %(limit)s OFFSET %(offset)s"
        params['limit'] = page_size
        params['offset'] = (page - 1) * page_size
        
        # 执行查询
        files = execute_query(base_sql, params)
        count_result = execute_query(count_sql, params)
        total = count_result[0]['count'] if count_result else 0
        
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
        
        # 尝试从GeoServer删除
        try:
            store_name = f"file_{file_id}"
            self.geoserver.delete_layer(store_name)
        except Exception as e:
            # 记录错误但继续
            print(f"从GeoServer删除图层失败: {str(e)}")
        
        # 从文件系统删除
        try:
            if os.path.exists(file_info['file_path']):
                os.remove(file_info['file_path'])
        except Exception as e:
            # 记录错误但继续
            print(f"删除文件失败: {str(e)}")
        
        # 从数据库删除
        sql = "DELETE FROM files WHERE id = %(file_id)s"
        params = {'file_id': file_id}
        execute_query(sql, params)
        
        return True 