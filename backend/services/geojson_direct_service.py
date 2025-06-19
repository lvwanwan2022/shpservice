#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GeoJSON直接服务类，用于管理GeoJSON文件的上传、获取和处理
"""

import os
import json
import uuid
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from config import FILE_STORAGE
from models.db import execute_query, insert_with_snowflake_id

class GeoJsonDirectService:
    """GeoJSON直接服务类，用于处理GeoJSON文件的上传和检索"""
    
    def __init__(self):
        """初始化服务"""
        self.upload_folder = os.path.join(FILE_STORAGE['upload_folder'], 'geojson')
        self.public_url_base = '/api/geojson/files'
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def upload_geojson(self, file_obj, file_info):
        """上传GeoJSON文件
        
        Args:
            file_obj: 文件对象
            file_info: 文件信息字典
            
        Returns:
            文件信息和访问URL
        """
        try:
            print(f"\n=== 上传GeoJSON文件 ===")
            
            # 检查文件扩展名
            original_filename = file_info.get('original_filename')
            if not original_filename.lower().endswith(('.geojson', '.json')):
                raise ValueError("只支持.geojson或.json文件")
                
            # 读取文件内容并验证
            file_content = file_obj.read()
            geojson_data = json.loads(file_content)
            
            # 分析GeoJSON内容
            analysis = self._analyze_geojson(geojson_data)
            
            # 生成唯一文件ID
            file_id = str(uuid.uuid4())
            
            # 保存文件
            file_path = os.path.join(self.upload_folder, f"{file_id}.geojson")
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 记录到数据库
            params = {
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': file_path,
                'file_size': len(file_content),
                'feature_count': analysis['feature_count'],
                'geometry_types': json.dumps(list(analysis['geometry_types'])),
                'property_fields': json.dumps(analysis['properties']),
                'bbox': json.dumps(analysis.get('bbox')),
                'status': 'active',
                'user_id': file_info.get('user_id')
            }
            
            insert_with_snowflake_id('geojson_files', params)
            
            # 构建结果
            result = {
                "success": True,
                "file_id": file_id,
                "original_filename": original_filename,
                "file_size": len(file_content),
                "feature_count": analysis['feature_count'],
                "geometry_types": list(analysis['geometry_types']),
                "access_url": f"{self.public_url_base}/{file_id}",
                "upload_date": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 上传GeoJSON文件失败: {str(e)}")
            raise
    
    def list_geojson_files(self, limit=100, offset=0, user_id=None):
        """列出GeoJSON文件
        
        Args:
            limit: 限制返回的记录数
            offset: 结果集的偏移量
            user_id: 用户ID过滤
            
        Returns:
            文件列表
        """
        try:
            # 构建SQL查询
            sql = """
            SELECT file_id, original_filename, file_size, feature_count, geometry_types, 
                   upload_date, status, user_id
            FROM geojson_files
            WHERE status = 'active'
            """
            
            params = []
            
            # 添加用户ID过滤
            if user_id is not None:
                sql += " AND user_id = %s"
                params.append(user_id)
            
            # 添加排序和分页
            sql += " ORDER BY upload_date DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 执行查询
            files = execute_query(sql, tuple(params))
            
            # 处理结果
            result = []
            for file in files:
                # 解析JSON字段
                if file.get('geometry_types') and isinstance(file['geometry_types'], str):
                    file['geometry_types'] = json.loads(file['geometry_types'])
                
                # 格式化日期
                if file.get('upload_date'):
                    file['upload_date'] = file['upload_date'].isoformat()
                
                result.append(file)
            
            return {
                "success": True,
                "files": result,
                "total": len(result)
            }
            
        except Exception as e:
            print(f"❌ 列出GeoJSON文件失败: {str(e)}")
            raise
    
    def get_geojson_file(self, file_id):
        """获取GeoJSON文件内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            GeoJSON数据和文件信息
        """
        try:
            # 获取文件信息
            sql = "SELECT * FROM geojson_files WHERE file_id = %s AND status = 'active'"
            result = execute_query(sql, (file_id,))
            
            if not result:
                raise ValueError(f"文件不存在或已被删除: {file_id}")
            
            file_info = result[0]
            
            # 读取文件内容
            file_path = file_info['file_path']
            
            if not os.path.exists(file_path):
                # 尝试在不同位置查找文件
                alt_path = os.path.join(self.upload_folder, f"{file_id}.geojson")
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    raise ValueError(f"文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            # 处理文件信息
            if file_info.get('geometry_types') and isinstance(file_info['geometry_types'], str):
                file_info['geometry_types'] = json.loads(file_info['geometry_types'])
            
            if file_info.get('property_fields') and isinstance(file_info['property_fields'], str):
                file_info['property_fields'] = json.loads(file_info['property_fields'])
            
            if file_info.get('bbox') and isinstance(file_info['bbox'], str):
                file_info['bbox'] = json.loads(file_info['bbox'])
            
            if file_info.get('upload_date'):
                file_info['upload_date'] = file_info['upload_date'].isoformat()
            
            return {
                "success": True,
                "file_info": file_info,
                "data": geojson_data
            }
            
        except Exception as e:
            print(f"❌ 获取GeoJSON文件失败: {str(e)}")
            raise
    
    def delete_geojson_file(self, file_id, user_id=None):
        """删除GeoJSON文件
        
        Args:
            file_id: 文件ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            删除结果
        """
        try:
            # 获取文件信息
            sql = "SELECT * FROM geojson_files WHERE file_id = %s AND status = 'active'"
            result = execute_query(sql, (file_id,))
            
            if not result:
                raise ValueError(f"文件不存在或已被删除: {file_id}")
            
            file_info = result[0]
            
            # 检查用户权限
            if user_id is not None and file_info.get('user_id') != user_id:
                raise ValueError("无权删除此文件")
            
            # 更新文件状态为已删除
            update_sql = "UPDATE geojson_files SET status = 'deleted' WHERE file_id = %s"
            execute_query(update_sql, (file_id,))
            
            # 尝试删除文件
            file_path = file_info['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                "success": True,
                "message": "文件已删除"
            }
            
        except Exception as e:
            print(f"❌ 删除GeoJSON文件失败: {str(e)}")
            raise
    
    def _analyze_geojson(self, geojson_data):
        """分析GeoJSON数据
        
        Args:
            geojson_data: GeoJSON数据对象
            
        Returns:
            分析结果
        """
        analysis = {
            'feature_count': 0,
            'geometry_types': set(),
            'properties': []
        }
        
        # 提取要素
        features = []
        if geojson_data.get('type') == 'FeatureCollection':
            features = geojson_data.get('features', [])
        elif geojson_data.get('type') == 'Feature':
            features = [geojson_data]
        
        # 设置要素数量
        analysis['feature_count'] = len(features)
        
        # 分析第一个要素的属性
        if features:
            first_feature = features[0]
            if 'properties' in first_feature and isinstance(first_feature['properties'], dict):
                analysis['properties'] = list(first_feature['properties'].keys())
        
        # 分析几何类型
        for feature in features:
            if 'geometry' in feature and feature['geometry'] and 'type' in feature['geometry']:
                analysis['geometry_types'].add(feature['geometry']['type'])
        
        # 计算边界框
        if features:
            try:
                min_x, min_y = float('inf'), float('inf')
                max_x, max_y = float('-inf'), float('-inf')
                
                has_valid_coords = False
                
                for feature in features:
                    if 'geometry' not in feature or not feature['geometry']:
                        continue
                    
                    geometry = feature['geometry']
                    coords = self._extract_coordinates(geometry)
                    
                    for x, y in coords:
                        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                            min_x = min(min_x, x)
                            min_y = min(min_y, y)
                            max_x = max(max_x, x)
                            max_y = max(max_y, y)
                            has_valid_coords = True
                
                if has_valid_coords:
                    analysis['bbox'] = [min_x, min_y, max_x, max_y]
            except Exception as e:
                print(f"计算边界框失败: {str(e)}")
        
        return analysis
    
    def _extract_coordinates(self, geometry):
        """从几何对象中提取所有坐标
        
        Args:
            geometry: GeoJSON几何对象
            
        Returns:
            坐标列表 [(x, y), ...]
        """
        coords = []
        
        if not geometry or 'type' not in geometry:
            return coords
        
        geom_type = geometry['type']
        
        if geom_type == 'Point':
            coords.append(tuple(geometry['coordinates'][:2]))
        
        elif geom_type == 'LineString':
            coords.extend([tuple(p[:2]) for p in geometry['coordinates']])
        
        elif geom_type == 'Polygon':
            for ring in geometry['coordinates']:
                coords.extend([tuple(p[:2]) for p in ring])
        
        elif geom_type == 'MultiPoint':
            coords.extend([tuple(p[:2]) for p in geometry['coordinates']])
        
        elif geom_type == 'MultiLineString':
            for line in geometry['coordinates']:
                coords.extend([tuple(p[:2]) for p in line])
        
        elif geom_type == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for ring in polygon:
                    coords.extend([tuple(p[:2]) for p in ring])
        
        elif geom_type == 'GeometryCollection':
            for geom in geometry.get('geometries', []):
                coords.extend(self._extract_coordinates(geom))
        
        return coords
    
    def _generate_leaflet_config(self, geojson_url, analysis):
        """生成Leaflet地图配置
        
        Args:
            geojson_url: GeoJSON数据URL
            analysis: 分析结果
            
        Returns:
            Leaflet配置
        """
        # 确定中心点和缩放级别
        center = [0, 0]
        zoom = 2
        
        if 'bbox' in analysis:
            bbox = analysis['bbox']
            center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
            
            # 粗略估计适合的缩放级别
            lon_diff = abs(bbox[2] - bbox[0])
            lat_diff = abs(bbox[3] - bbox[1])
            
            if lon_diff > 0 and lat_diff > 0:
                # 基于边界框大小估计缩放级别
                if max(lon_diff, lat_diff) < 0.01:
                    zoom = 15
                elif max(lon_diff, lat_diff) < 0.1:
                    zoom = 12
                elif max(lon_diff, lat_diff) < 1:
                    zoom = 10
                elif max(lon_diff, lat_diff) < 5:
                    zoom = 8
                elif max(lon_diff, lat_diff) < 20:
                    zoom = 6
                else:
                    zoom = 4
        
        # 为不同几何类型选择合适的样式
        style = {}
        if 'geometry_types' in analysis:
            if 'Point' in analysis['geometry_types'] or 'MultiPoint' in analysis['geometry_types']:
                style = {
                    'radius': 6,
                    'fillColor': "#ff7800",
                    'color': "#000",
                    'weight': 1,
                    'opacity': 1,
                    'fillOpacity': 0.8
                }
            else:
                style = {
                    'color': "#ff7800",
                    'weight': 2,
                    'opacity': 0.65
                }
        
        config = {
            'url': geojson_url,
            'center': center,
            'zoom': zoom,
            'style': style,
            'properties': analysis.get('properties', [])
        }
        
        return config 