'''
Author: WangNing
Date: 2025-05-27 11:25:53
LastEditors: WangNing
LastEditTime: 2025-05-28 17:45:49
FilePath: \shpservice\backend\services\layer_service.py
Description: 
Copyright (c) 2025 by VGE, All Rights Reserved. 
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from models.db import execute_query
from services.file_service import FileService
from services.geoserver_service import GeoServerService
from services.style_service import StyleService
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from backend.config import GEOSERVER_CONFIG

class LayerService:
    def __init__(self):
        self.file_service = FileService()
        self.geoserver_service = GeoServerService()
        self.style_service = StyleService()

    def get_layers(self, filters=None, page=1, page_size=20, sort_by='created_at', sort_order='desc'):
        """获取图层列表"""
        try:
            # 构建基础查询
            base_query = """
            SELECT 
                gl.id, gl.name, gl.title, gl.abstract, gl.enabled, gl.queryable, gl.opaque,
                gl.default_style, gl.additional_styles, gl.attribution, gl.style_config,
                gl.wms_url, gl.wfs_url, gl.wcs_url, gl.file_id,
                gl.workspace_id, gl.featuretype_id, gl.coverage_id,
                gl.created_at, gl.updated_at,
                gw.name as workspace_name,
                f.file_name, f.file_type, f.discipline, f.dimension
            FROM geoserver_layers gl
            LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
            LEFT JOIN files f ON gl.file_id = f.id
            """
            
            # 构建WHERE条件
            where_conditions = []
            params = []
            
            if filters:
                if filters.get('workspace_id'):
                    where_conditions.append("gl.workspace_id = %s")
                    params.append(filters['workspace_id'])
                
                if filters.get('enabled') is not None:
                    where_conditions.append("gl.enabled = %s")
                    params.append(filters['enabled'])
                
                if filters.get('queryable') is not None:
                    where_conditions.append("gl.queryable = %s")
                    params.append(filters['queryable'])
                
                if filters.get('file_id'):
                    where_conditions.append("gl.file_id = %s")
                    params.append(filters['file_id'])
                
                if filters.get('name'):
                    where_conditions.append("gl.name ILIKE %s")
                    params.append(f"%{filters['name']}%")
            
            # 添加WHERE子句
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            # 获取总数
            count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
            count_result = execute_query(count_query, params)
            total = count_result[0]['total'] if count_result else 0
            
            # 添加排序和分页
            valid_sort_fields = ['id', 'name', 'title', 'created_at', 'updated_at']
            if sort_by not in valid_sort_fields:
                sort_by = 'created_at'
            
            if sort_order.lower() not in ['asc', 'desc']:
                sort_order = 'desc'
            
            base_query += f" ORDER BY gl.{sort_by} {sort_order.upper()}"
            
            # 分页
            offset = (page - 1) * page_size
            base_query += f" LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            
            # 执行查询
            layers = execute_query(base_query, params)
            
            # 处理结果
            for layer in layers:
                # 处理JSON字段
                json_fields = ['additional_styles', 'style_config']
                for field in json_fields:
                    if layer.get(field) and isinstance(layer[field], str):
                        try:
                            layer[field] = json.loads(layer[field])
                        except:
                            if field == 'additional_styles':
                                layer[field] = []
                            else:
                                layer[field] = None
                
                # 确定图层类型
                if layer.get('featuretype_id'):
                    layer['layer_type'] = 'vector'
                elif layer.get('coverage_id'):
                    layer['layer_type'] = 'raster'
                else:
                    layer['layer_type'] = 'unknown'
            
            return layers, total
            
        except Exception as e:
            print(f"获取图层列表失败: {str(e)}")
            raise

    def get_layer_by_id(self, layer_id):
        """根据ID获取图层详情"""
        try:
            query = """
            SELECT 
                gl.id, gl.name, gl.title, gl.abstract, gl.enabled, gl.queryable, gl.opaque,
                gl.default_style, gl.additional_styles, gl.attribution, gl.style_config,
                gl.wms_url, gl.wfs_url, gl.wcs_url, gl.file_id,
                gl.workspace_id, gl.featuretype_id, gl.coverage_id,
                gl.created_at, gl.updated_at,
                gw.name as workspace_name, gw.namespace_uri, gw.namespace_prefix,
                f.file_name, f.file_type, f.discipline, f.dimension, f.coordinate_system,
                gft.srs as featuretype_srs, gft.native_bbox as featuretype_bbox,
                gft.lat_lon_bbox as featuretype_lat_lon_bbox, gft.attributes,
                gc.srs as coverage_srs, gc.native_bbox as coverage_bbox,
                gc.lat_lon_bbox as coverage_lat_lon_bbox, gc.grid_info, gc.bands_info
            FROM geoserver_layers gl
            LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
            LEFT JOIN files f ON gl.file_id = f.id
            LEFT JOIN geoserver_featuretypes gft ON gl.featuretype_id = gft.id
            LEFT JOIN geoserver_coverages gc ON gl.coverage_id = gc.id
            WHERE gl.id = %s
            """
            
            result = execute_query(query, (layer_id,))
            
            if not result:
                return None
            
            layer = result[0]
            
            # 处理JSON字段
            json_fields = ['additional_styles', 'attributes', 'grid_info', 'bands_info', 
                          'featuretype_bbox', 'featuretype_lat_lon_bbox', 
                          'coverage_bbox', 'coverage_lat_lon_bbox', 'style_config']
            
            for field in json_fields:
                if layer.get(field) and isinstance(layer[field], str):
                    try:
                        layer[field] = json.loads(layer[field])
                    except:
                        layer[field] = None
            
            # 确定图层类型和相关信息
            if layer.get('featuretype_id'):
                layer['layer_type'] = 'vector'
                layer['srs'] = layer.get('featuretype_srs')
                layer['native_bbox'] = layer.get('featuretype_bbox')
                layer['lat_lon_bbox'] = layer.get('featuretype_lat_lon_bbox')
            elif layer.get('coverage_id'):
                layer['layer_type'] = 'raster'
                layer['srs'] = layer.get('coverage_srs')
                layer['native_bbox'] = layer.get('coverage_bbox')
                layer['lat_lon_bbox'] = layer.get('coverage_lat_lon_bbox')
            else:
                layer['layer_type'] = 'unknown'
            
            return layer
            
        except Exception as e:
            print(f"获取图层详情失败: {str(e)}")
            raise

    def publish_layer(self, file_id, params=None):
        """发布图层服务"""
        try:
            if params is None:
                params = {}
            
            # 获取文件信息
            file_info = self.file_service.get_file_by_id(file_id)
            if not file_info:
                raise FileNotFoundError(f"文件ID {file_id} 不存在")
            
            # 检查文件是否已经发布过图层
            existing_layer = execute_query(
                "SELECT id FROM geoserver_layers WHERE file_id = %s", 
                (file_id,)
            )
            if existing_layer:
                raise ValueError(f"文件已经发布过图层，图层ID: {existing_layer[0]['id']}")
            
            # 获取或创建默认工作空间
            workspace_name = params.get('workspace_name', 'shpservice')
            workspace = execute_query(
                "SELECT id FROM geoserver_workspaces WHERE name = %s", 
                (workspace_name,)
            )
            if not workspace:
                raise ValueError(f"工作空间 {workspace_name} 不存在")
            
            workspace_id = workspace[0]['id']
            
            # 生成图层名称
            layer_name = params.get('layer_name') or file_info['file_name'].split('.')[0]
            
            # 检查图层名称是否已存在
            existing_name = execute_query(
                "SELECT id FROM geoserver_layers WHERE workspace_id = %s AND name = %s",
                (workspace_id, layer_name)
            )
            if existing_name:
                # 添加后缀避免重名
                counter = 1
                while existing_name:
                    new_name = f"{layer_name}_{counter}"
                    existing_name = execute_query(
                        "SELECT id FROM geoserver_layers WHERE workspace_id = %s AND name = %s",
                        (workspace_id, new_name)
                    )
                    counter += 1
                layer_name = new_name
            
            # 根据文件类型创建存储仓库和图层
            file_type = file_info['file_type'].lower()
            
            if file_type in ['shp', 'geojson', 'dwg', 'dxf']:
                # 矢量数据
                layer_id = self._publish_vector_layer(
                    file_info, workspace_id, layer_name, params
                )
            elif file_type in ['tif', 'tiff']:
                # 栅格数据
                layer_id = self._publish_raster_layer(
                    file_info, workspace_id, layer_name, params
                )
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            # 更新文件状态
            self.file_service.update_file(file_id, {'status': 'published'})
            
            return layer_id
            
        except Exception as e:
            print(f"发布图层失败: {str(e)}")
            raise

    def _publish_vector_layer(self, file_info, workspace_id, layer_name, params):
        """发布矢量图层"""
        try:
            # 创建存储仓库
            store_name = f"{layer_name}_store"
            store_data = {
                'name': store_name,
                'workspace_id': workspace_id,
                'store_type': 'datastore',
                'data_type': 'Shapefile' if file_info['file_type'].lower() == 'shp' else 'Directory',
                'connection_params': {
                    'url': f"file://{file_info['file_path']}",
                    'charset': 'UTF-8'
                },
                'description': f"Store for {file_info['file_name']}",
                'enabled': True,
                'file_id': file_info['id']
            }
            
            store_id = self._create_store(store_data)
            
            # 创建要素类型
            featuretype_data = {
                'name': layer_name,
                'native_name': layer_name,
                'store_id': store_id,
                'title': params.get('title', file_info['file_name']),
                'abstract': params.get('abstract', file_info.get('description', '')),
                'keywords': [],
                'srs': params.get('srs', file_info.get('coordinate_system', 'EPSG:4326')),
                'enabled': True
            }
            
            featuretype_id = self._create_featuretype(featuretype_data)
            
            # 创建图层
            layer_data = {
                'name': layer_name,
                'workspace_id': workspace_id,
                'featuretype_id': featuretype_id,
                'title': params.get('title', file_info['file_name']),
                'abstract': params.get('abstract', file_info.get('description', '')),
                'default_style': params.get('style_name', 'polygon'),
                'enabled': params.get('enabled', True),
                'queryable': params.get('queryable', True),
                'file_id': file_info['id']
            }
            
            return self._create_layer(layer_data)
            
        except Exception as e:
            print(f"发布矢量图层失败: {str(e)}")
            raise

    def _publish_raster_layer(self, file_info, workspace_id, layer_name, params):
        """发布栅格图层"""
        try:
            # 创建存储仓库
            store_name = f"{layer_name}_store"
            store_data = {
                'name': store_name,
                'workspace_id': workspace_id,
                'store_type': 'coveragestore',
                'data_type': 'GeoTIFF',
                'connection_params': {
                    'url': f"file://{file_info['file_path']}",
                    'type': 'GeoTIFF'
                },
                'description': f"Coverage store for {file_info['file_name']}",
                'enabled': True,
                'file_id': file_info['id']
            }
            
            store_id = self._create_store(store_data)
            
            # 创建覆盖范围
            coverage_data = {
                'name': layer_name,
                'native_name': layer_name,
                'store_id': store_id,
                'title': params.get('title', file_info['file_name']),
                'abstract': params.get('abstract', file_info.get('description', '')),
                'keywords': [],
                'srs': params.get('srs', file_info.get('coordinate_system', 'EPSG:4326')),
                'enabled': True
            }
            
            coverage_id = self._create_coverage(coverage_data)
            
            # 创建图层
            layer_data = {
                'name': layer_name,
                'workspace_id': workspace_id,
                'coverage_id': coverage_id,
                'title': params.get('title', file_info['file_name']),
                'abstract': params.get('abstract', file_info.get('description', '')),
                'default_style': params.get('style_name', 'raster'),
                'enabled': params.get('enabled', True),
                'queryable': params.get('queryable', False),  # 栅格图层通常不可查询
                'file_id': file_info['id']
            }
            
            return self._create_layer(layer_data)
            
        except Exception as e:
            print(f"发布栅格图层失败: {str(e)}")
            raise

    def _create_store(self, store_data):
        """创建存储仓库"""
        try:
            query = """
            INSERT INTO geoserver_stores 
            (name, workspace_id, store_type, data_type, connection_params, description, enabled, file_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                store_data['name'],
                store_data['workspace_id'],
                store_data['store_type'],
                store_data['data_type'],
                json.dumps(store_data['connection_params']),
                store_data['description'],
                store_data['enabled'],
                store_data['file_id']
            )
            
            result = execute_query(query, params)
            return result[0]['id']
            
        except Exception as e:
            print(f"创建存储仓库失败: {str(e)}")
            raise

    def _create_featuretype(self, featuretype_data):
        """创建要素类型"""
        try:
            query = """
            INSERT INTO geoserver_featuretypes 
            (name, native_name, store_id, title, abstract, keywords, srs, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                featuretype_data['name'],
                featuretype_data['native_name'],
                featuretype_data['store_id'],
                featuretype_data['title'],
                featuretype_data['abstract'],
                featuretype_data['keywords'],
                featuretype_data['srs'],
                featuretype_data['enabled']
            )
            
            result = execute_query(query, params)
            return result[0]['id']
            
        except Exception as e:
            print(f"创建要素类型失败: {str(e)}")
            raise

    def _create_coverage(self, coverage_data):
        """创建覆盖范围"""
        try:
            query = """
            INSERT INTO geoserver_coverages 
            (name, native_name, store_id, title, abstract, keywords, srs, enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                coverage_data['name'],
                coverage_data['native_name'],
                coverage_data['store_id'],
                coverage_data['title'],
                coverage_data['abstract'],
                coverage_data['keywords'],
                coverage_data['srs'],
                coverage_data['enabled']
            )
            
            result = execute_query(query, params)
            return result[0]['id']
            
        except Exception as e:
            print(f"创建覆盖范围失败: {str(e)}")
            raise

    def _create_layer(self, layer_data):
        """创建图层"""
        try:
            query = """
            INSERT INTO geoserver_layers 
            (name, workspace_id, featuretype_id, coverage_id, title, abstract, 
             default_style, enabled, queryable, file_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                layer_data['name'],
                layer_data['workspace_id'],
                layer_data.get('featuretype_id'),
                layer_data.get('coverage_id'),
                layer_data['title'],
                layer_data['abstract'],
                layer_data['default_style'],
                layer_data['enabled'],
                layer_data['queryable'],
                layer_data['file_id']
            )
            
            result = execute_query(query, params)
            return result[0]['id']
            
        except Exception as e:
            print(f"创建图层失败: {str(e)}")
            raise

    def update_layer(self, layer_id, data):
        """更新图层"""
        try:
            # 构建更新字段
            update_fields = []
            params = []
            
            allowed_fields = [
                'title', 'abstract', 'default_style', 'enabled', 
                'queryable', 'opaque', 'attribution'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])
            
            if not update_fields:
                return
            
            # 添加更新时间
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(layer_id)
            
            query = f"""
            UPDATE geoserver_layers 
            SET {', '.join(update_fields)}
            WHERE id = %s
            """
            
            execute_query(query, params)
            
        except Exception as e:
            print(f"更新图层失败: {str(e)}")
            raise

    def delete_layer(self, layer_id):
        """删除图层"""
        try:
            # 获取图层信息
            layer = self.get_layer_by_id(layer_id)
            if not layer:
                raise ValueError(f"图层ID {layer_id} 不存在")
            
            # 删除图层（级联删除会处理相关的要素类型/覆盖范围和存储仓库）
            execute_query("DELETE FROM geoserver_layers WHERE id = %s", (layer_id,), fetch=False)
            
            # 如果有关联文件，更新文件状态
            if layer.get('file_id'):
                self.file_service.update_file(layer['file_id'], {'status': 'uploaded'})
            
        except Exception as e:
            print(f"删除图层失败: {str(e)}")
            raise

    def get_layer_capabilities(self, layer_id, service_type='WMS'):
        """获取图层能力信息"""
        try:
            layer = self.get_layer_by_id(layer_id)
            if not layer:
                raise ValueError(f"图层ID {layer_id} 不存在")
            
            capabilities = {
                'layer_id': layer_id,
                'layer_name': layer['name'],
                'service_type': service_type,
                'workspace': layer.get('workspace_name'),
                'title': layer.get('title'),
                'abstract': layer.get('abstract'),
                'srs': layer.get('srs'),
                'bbox': layer.get('lat_lon_bbox'),
                'queryable': layer.get('queryable', False),
                'opaque': layer.get('opaque', False)
            }
            
            # 根据服务类型添加特定信息
            if service_type.upper() == 'WMS':
                capabilities['formats'] = ['image/png', 'image/jpeg', 'image/gif']
                capabilities['styles'] = [layer.get('default_style')]
                if layer.get('additional_styles'):
                    capabilities['styles'].extend(layer['additional_styles'])
            
            elif service_type.upper() == 'WFS':
                if layer.get('layer_type') == 'vector':
                    capabilities['formats'] = ['application/json', 'application/gml+xml']
                    capabilities['operations'] = ['GetFeature', 'DescribeFeatureType']
                    if layer.get('attributes'):
                        capabilities['attributes'] = layer['attributes']
                else:
                    raise ValueError("WFS服务仅支持矢量图层")
            
            elif service_type.upper() == 'WCS':
                if layer.get('layer_type') == 'raster':
                    capabilities['formats'] = ['image/tiff', 'image/geotiff']
                    capabilities['operations'] = ['GetCoverage', 'DescribeCoverage']
                    if layer.get('grid_info'):
                        capabilities['grid_info'] = layer['grid_info']
                    if layer.get('bands_info'):
                        capabilities['bands_info'] = layer['bands_info']
                else:
                    raise ValueError("WCS服务仅支持栅格图层")
            
            return capabilities
            
        except Exception as e:
            print(f"获取图层能力信息失败: {str(e)}")
            raise

    def get_layer_preview_url(self, layer_id, bbox=None, width=512, height=512, srs='EPSG:4326'):
        """生成图层预览URL"""
        try:
            layer = self.get_layer_by_id(layer_id)
            if not layer:
                raise ValueError(f"图层ID {layer_id} 不存在")
            
            # 构建WMS GetMap请求URL
            workspace_name = layer.get('workspace_name', 'shpservice')
            layer_name = layer['name']
            
            # 如果没有提供bbox，使用图层的边界框
            if not bbox and layer.get('lat_lon_bbox'):
                bbox_data = layer['lat_lon_bbox']
                if isinstance(bbox_data, dict):
                    bbox = f"{bbox_data.get('minx', -180)},{bbox_data.get('miny', -90)},{bbox_data.get('maxx', 180)},{bbox_data.get('maxy', 90)}"
                else:
                    bbox = "-180,-90,180,90"  # 默认全球范围
            elif not bbox:
                bbox = "-180,-90,180,90"
            
            # 构建预览URL（这里假设有GeoServer实例）
            base_url = "http://localhost:8080/geoserver"  # 这应该从配置中获取
            preview_url = (
                f"{base_url}/{workspace_name}/wms?"
                f"service=WMS&version=1.1.0&request=GetMap&"
                f"layers={workspace_name}:{layer_name}&"
                f"styles={layer.get('default_style', '')}&"
                f"bbox={bbox}&width={width}&height={height}&"
                f"srs={srs}&format=image/png"
            )
            
            return preview_url
            
        except Exception as e:
            print(f"生成图层预览URL失败: {str(e)}")
            raise

    def get_layer_statistics(self):
        """获取图层统计信息"""
        try:
            stats = {}
            
            # 总图层数
            total_query = "SELECT COUNT(*) as total FROM geoserver_layers"
            total_result = execute_query(total_query)
            stats['total_layers'] = total_result[0]['total'] if total_result else 0
            
            # 启用的图层数
            enabled_query = "SELECT COUNT(*) as enabled FROM geoserver_layers WHERE enabled = true"
            enabled_result = execute_query(enabled_query)
            stats['enabled_layers'] = enabled_result[0]['enabled'] if enabled_result else 0
            
            # 按工作空间统计
            workspace_query = """
            SELECT gw.name as workspace, COUNT(gl.id) as count
            FROM geoserver_layers gl
            LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
            GROUP BY gw.name
            ORDER BY count DESC
            """
            workspace_result = execute_query(workspace_query)
            stats['by_workspace'] = {row['workspace']: row['count'] for row in workspace_result}
            
            # 按类型统计
            type_query = """
            SELECT 
                CASE 
                    WHEN featuretype_id IS NOT NULL THEN 'vector'
                    WHEN coverage_id IS NOT NULL THEN 'raster'
                    ELSE 'unknown'
                END as layer_type,
                COUNT(*) as count
            FROM geoserver_layers
            GROUP BY layer_type
            """
            type_result = execute_query(type_query)
            stats['by_type'] = {row['layer_type']: row['count'] for row in type_result}
            
            return stats
            
        except Exception as e:
            print(f"获取图层统计信息失败: {str(e)}")
            raise

    def get_layer_style_config(self, layer_id):
        """获取图层的样式配置信息"""
        try:
            # 获取图层信息
            layer = self.get_layer_by_id(layer_id)
            if not layer:
                return {
                    'success': False,
                    'error': f'图层ID {layer_id} 不存在',
                    'error_type': 'not_found'
                }
            
            print(f"获取图层 {layer['name']} 的样式配置...")
            
            # 从数据库获取图层的样式配置
            style_config = None
            if layer.get('style_config'):
                try:
                    if isinstance(layer['style_config'], str):
                        style_config = json.loads(layer['style_config'])
                    else:
                        style_config = layer['style_config']
                except json.JSONDecodeError as e:
                    print(f"解析图层样式配置失败: {str(e)}")
                    style_config = None
            
            # 如果没有样式配置，提供默认配置
            if not style_config:
                file_type = layer.get('file_type', '').lower()
                if file_type in ['shp', 'geojson', 'dwg', 'dxf']:
                    # 矢量图层默认样式
                    style_config = {
                        'point': {
                            'color': '#FF0000',
                            'size': 6,
                            'shape': 'circle',
                            'opacity': 1.0
                        },
                        'line': {
                            'color': '#0000FF',
                            'width': 2,
                            'style': 'solid',
                            'opacity': 1.0
                        },
                        'polygon': {
                            'fillColor': '#00FF00',
                            'fillOpacity': 0.3,
                            'outlineColor': '#000000',
                            'outlineWidth': 1,
                            'opacity': 1.0
                        }
                    }
                else:
                    # 栅格图层默认样式
                    style_config = {
                        'raster': {
                            'opacity': 1.0,
                            'palette': 'default'
                        }
                    }
            
            # 查找对应的样式名称
            style_name = f"{layer['name']}_custom_style"
            existing_style = execute_query(
                "SELECT name, description FROM geoserver_styles WHERE name = %s AND workspace_id = %s",
                (style_name, layer['workspace_id'])
            )
            
            style_info = {
                'style_name': style_name if existing_style else None,
                'style_exists': bool(existing_style),
                'style_description': existing_style[0]['description'] if existing_style else None
            }
            
            # 获取GeoServer中的样式信息
            geoserver_styles = None
            try:
                geoserver_styles = self.style_service.get_layer_styles(
                    layer['workspace_name'], 
                    layer['name'], 
                    GEOSERVER_CONFIG
                )
            except Exception as e:
                print(f"获取GeoServer样式信息失败: {str(e)}")
            
            return {
                'success': True,
                'style_config': style_config,
                'style_name': style_info['style_name'],
                'style_exists': style_info['style_exists'],
                'style_description': style_info['style_description'],
                'geoserver_styles': geoserver_styles,
                'file_type': layer.get('file_type'),
                'layer_type': layer.get('layer_type')
            }
            
        except Exception as e:
            print(f"获取图层样式配置失败: {str(e)}")
            return {
                'success': False,
                'error': f"获取样式配置时发生错误: {str(e)}",
                'error_type': 'system_error'
            }

    def update_layer_style(self, layer_id, style_config):
        """更新图层样式 - 支持增量更新"""
        try:
            # 验证样式配置
            is_valid, validation_message = self.style_service.validate_style_config(style_config)
            if not is_valid:
                raise ValueError(f"样式配置无效: {validation_message}")
            
            # 获取图层信息
            layer = self.get_layer_by_id(layer_id)
            if not layer:
                raise ValueError(f"图层ID {layer_id} 不存在")
            
            # 生成样式名称 - 使用图层名称作为样式名称，确保一一对应
            style_name = f"{layer['name']}_custom_style"
            
            print(f"开始更新图层 {layer['name']} 的样式...")
            print(f"样式配置: {json.dumps(style_config, indent=2)}")
            
            # 使用StyleService生成SLD内容
            sld_content = self.style_service.generate_sld_xml(style_config, style_name)
            
            # 1. 保存/更新样式到数据库
            style_id = self._save_or_update_style_to_database(
                style_name, 
                layer['workspace_id'], 
                sld_content, 
                style_config
            )
            
            print(f"样式已保存/更新到数据库，样式ID: {style_id}")
            
            # 2. 更新图层表中的样式配置
            self._update_layer_style_config(layer_id, style_config)
            
            # 3. 更新GeoServer中的样式
            geoserver_updated = False
            try:
                geoserver_updated = self.style_service.create_or_update_geoserver_style(
                    layer['workspace_name'], 
                    style_name, 
                    sld_content,
                    layer['name'],
                    GEOSERVER_CONFIG
                )
                if geoserver_updated:
                    print(f"✅ GeoServer样式更新成功: {style_name}")
                else:
                    print(f"❌ GeoServer样式更新失败")
            except Exception as e:
                print(f"❌ GeoServer样式更新失败: {str(e)}")
                # 不抛出异常，因为数据库中的样式已经保存
            
            return {
                'success': True,
                'style_id': style_id,
                'style_name': style_name,
                'geoserver_updated': geoserver_updated,
                'message': '样式更新成功' if geoserver_updated else '样式已保存到数据库，但GeoServer更新失败'
            }
            
        except ValueError as e:
            # 参数验证错误
            print(f"样式配置错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'validation_error'
            }
        except Exception as e:
            print(f"更新图层样式失败: {str(e)}")
            return {
                'success': False,
                'error': f"更新样式时发生错误: {str(e)}",
                'error_type': 'system_error'
            }

    def _save_or_update_style_to_database(self, style_name, workspace_id, sld_content, style_config):
        """保存或更新样式到geoserver_styles表"""
        try:
            # 检查样式是否已存在
            existing_style = execute_query(
                "SELECT id FROM geoserver_styles WHERE name = %s AND workspace_id = %s",
                (style_name, workspace_id)
            )
            
            if existing_style:
                # 更新现有样式
                print(f"样式 {style_name} 已存在，正在更新...")
                query = """
                UPDATE geoserver_styles 
                SET content = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                params = (
                    sld_content, 
                    f"Custom style updated at {datetime.now().isoformat()}: {json.dumps(style_config)}", 
                    existing_style[0]['id']
                )
                execute_query(query, params)
                print(f"✅ 样式 {style_name} 数据库记录已更新")
                return existing_style[0]['id']
            else:
                # 创建新样式
                print(f"样式 {style_name} 不存在，正在创建...")
                query = """
                INSERT INTO geoserver_styles 
                (name, workspace_id, content, format, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
                """
                params = (
                    style_name,
                    workspace_id,
                    sld_content,
                    'sld',
                    f"Custom style created at {datetime.now().isoformat()}: {json.dumps(style_config)}"
                )
                result = execute_query(query, params)
                print(f"✅ 样式 {style_name} 数据库记录已创建")
                return result[0]['id']
                
        except Exception as e:
            print(f"保存样式到数据库失败: {str(e)}")
            raise

    def _update_layer_style_config(self, layer_id, style_config):
        """更新图层表中的样式配置"""
        try:
            query = """
            UPDATE geoserver_layers 
            SET style_config = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            params = (json.dumps(style_config), layer_id)
            execute_query(query, params)
            print(f"✅ 图层 {layer_id} 的样式配置已更新到图层表")
        except Exception as e:
            print(f"更新图层样式配置失败: {str(e)}")
            # 不抛出异常，因为这不是关键错误

    def generate_sld_style(self, style_config, style_name):
        """生成正确的SLD样式XML"""
        try:
            # 默认样式配置
            defaults = {
                'point': {
                    'color': '#FFEE00',
                    'size': 4,
                    'shape': 'square'
                },
                'line': {
                    'color': '#0000FF', 
                    'width': 2,
                    'style': 'solid'
                },
                'polygon': {
                    'fillColor': '#00FF00',
                    'outlineColor': '#000000',
                    'outlineWidth': 1,
                    'opacity': 0.5
                }
            }

            # 合并用户设置和默认样式
            point_style = {**defaults['point'], **(style_config.get('point', {}))}
            line_style = {**defaults['line'], **(style_config.get('line', {}))}
            polygon_style = {**defaults['polygon'], **(style_config.get('polygon', {}))}

            # 转换线型样式
            def get_stroke_dash_array(style):
                style_map = {
                    'dashed': '5 5',
                    'dotted': '2 2'
                }
                return style_map.get(style, None)

            # 生成SLD XML
            sld_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
 xmlns="http://www.opengis.net/sld" 
 xmlns:ogc="http://www.opengis.net/ogc" 
 xmlns:xlink="http://www.w3.org/1999/xlink" 
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <!-- a Named Layer is the basic building block of an SLD document -->
  <NamedLayer>
    <Name>{style_name}</Name>
    <UserStyle>
    <!-- Styles can have names, titles and abstracts -->
      <Title>Custom Style</Title>
      <Abstract>A custom style generated from user configuration</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <FeatureTypeStyle>
        <!-- Point Style Rule -->
        <Rule>
          <Name>Point Rule</Name>
          <Title>Point Style</Title>
          <Abstract>Point symbolizer for point geometries</Abstract>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>Point</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>MultiPoint</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>{point_style.get('shape', 'square')}</WellKnownName>
                <Fill>
                  <CssParameter name="fill">{point_style['color']}</CssParameter>
                </Fill>
              </Mark>
              <Size>{point_style['size']}</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        
        <!-- Line Style Rule -->
        <Rule>
          <Name>Line Rule</Name>
          <Title>Line Style</Title>
          <Abstract>Line symbolizer for line geometries</Abstract>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>LineString</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>MultiLineString</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">{line_style['color']}</CssParameter>
              <CssParameter name="stroke-width">{line_style['width']}</CssParameter>'''
            
            # 添加线型样式
            dash_array = get_stroke_dash_array(line_style.get('style'))
            if dash_array:
                sld_content += f'''
              <CssParameter name="stroke-dasharray">{dash_array}</CssParameter>'''
            
            sld_content += f'''
            </Stroke>
          </LineSymbolizer>
        </Rule>
        
        <!-- Polygon Style Rule -->
        <Rule>
          <Name>Polygon Rule</Name>
          <Title>Polygon Style</Title>
          <Abstract>Polygon symbolizer for polygon geometries</Abstract>
          <ogc:Filter>
            <ogc:Or>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>Polygon</ogc:Literal>
              </ogc:PropertyIsEqualTo>
              <ogc:PropertyIsEqualTo>
                <ogc:Function name="geometryType">
                  <ogc:PropertyName>the_geom</ogc:PropertyName>
                </ogc:Function>
                <ogc:Literal>MultiPolygon</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:Or>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">{polygon_style['fillColor']}</CssParameter>
              <CssParameter name="fill-opacity">{polygon_style['opacity']}</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">{polygon_style['outlineColor']}</CssParameter>
              <CssParameter name="stroke-width">{polygon_style['outlineWidth']}</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''

            return sld_content

        except Exception as e:
            print(f"生成SLD样式失败: {str(e)}")
            raise 