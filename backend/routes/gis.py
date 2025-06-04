#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from models.db import get_connection as get_db_connection
import json
import logging

# 创建logger
logger = logging.getLogger(__name__)

gis_bp = Blueprint('gis', __name__)

@gis_bp.route('/layer/<int:layer_id>/crs-info', methods=['GET'])
def get_layer_crs_info(layer_id):
    """获取图层的坐标系信息
    
    直接从geoserver_layers表中查询layer_id对应的图层，再通过featuretype_id获取坐标系信息
    
    Args:
        layer_id: geoserver_layers表中的图层ID
        
    Returns:
        坐标系信息，包括SRS、边界框、推荐的WMS版本等
    """
    try:
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 直接查询geoserver_layers表
        cursor.execute("""
            SELECT 
                gl.id as layer_id,
                gl.name as layer_name,
                gl.featuretype_id,
                gl.wms_url,
                gl.wfs_url,
                gl.file_id,
                gw.name as workspace_name
            FROM geoserver_layers gl
            JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
            WHERE gl.id = %s
            AND gl.enabled = true
            AND gl.featuretype_id IS NOT NULL
        """, (layer_id,))
        
        layer_record = cursor.fetchone()
        
        if not layer_record:
            return jsonify({
                "success": False,
                "message": f"未找到ID为{layer_id}的GeoServer图层，或该图层未启用/不是矢量图层"
            }), 404
        
        # 查询FeatureType的坐标系信息
        cursor.execute("""
            SELECT 
                gft.name as featuretype_name,
                gft.srs,
                gft.native_bbox,
                gft.lat_lon_bbox,
                gft.projection_policy,
                gs.name as store_name
            FROM geoserver_featuretypes gft
            JOIN geoserver_stores gs ON gft.store_id = gs.id
            WHERE gft.id = %s
        """, (layer_record[2],))  # featuretype_id
        
        featuretype_record = cursor.fetchone()
        
        if not featuretype_record:
            return jsonify({
                "success": False,
                "message": f"找到图层但无法获取FeatureType信息（featuretype_id: {layer_record[2]}）"
            }), 500
        
        # 解析坐标系信息
        srs = featuretype_record[1] or "EPSG:4326"
        native_bbox = featuretype_record[2]
        lat_lon_bbox = featuretype_record[3]
        projection_policy = featuretype_record[4] or "REPROJECT_TO_DECLARED"
        
        # 根据坐标系选择合适的WMS版本
        wms_version = "1.1.0" if srs == "EPSG:404000" else "1.1.1"
        
        # 计算推荐的地图中心点和缩放级别
        center_coords = None
        zoom_level = 10
        
        if lat_lon_bbox:
            # 从经纬度bbox计算中心点
            try:
                if isinstance(lat_lon_bbox, str):
                    bbox_data = json.loads(lat_lon_bbox)
                else:
                    bbox_data = lat_lon_bbox
                    
                if bbox_data and 'coordinates' in bbox_data:
                    coords = bbox_data['coordinates'][0]  # 假设是矩形
                    if len(coords) >= 4:
                        min_lng = min(coord[0] for coord in coords)
                        max_lng = max(coord[0] for coord in coords)
                        min_lat = min(coord[1] for coord in coords)
                        max_lat = max(coord[1] for coord in coords)
                        
                        center_lng = (min_lng + max_lng) / 2
                        center_lat = (min_lat + max_lat) / 2
                        center_coords = [center_lat, center_lng]
                        
                        # 根据bbox大小估算合适的缩放级别
                        width = max_lng - min_lng
                        height = max_lat - min_lat
                        max_extent = max(width, height)
                        
                        if max_extent > 5:
                            zoom_level = 8
                        elif max_extent > 2:
                            zoom_level = 9
                        elif max_extent > 1:
                            zoom_level = 10
                        elif max_extent > 0.5:
                            zoom_level = 11
                        else:
                            zoom_level = 12
                            
            except Exception as e:
                logger.warning(f"解析lat_lon_bbox失败: {e}")
        
        # 关闭数据库连接
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "geoserver_layer_id": layer_record[0],  # geoserver_layers.id
                "layer_name": layer_record[1],  # geoserver_layers.name
                "featuretype_name": featuretype_record[0],  # geoserver_featuretypes.name
                "workspace_name": layer_record[6],  # workspace_name
                "store_name": featuretype_record[5],  # store_name
                "srs": srs,
                "native_bbox": native_bbox,
                "lat_lon_bbox": lat_lon_bbox,
                "projection_policy": projection_policy,
                "wms_version": wms_version,
                "wms_url": layer_record[3],  # wms_url
                "wfs_url": layer_record[4],  # wfs_url
                "file_id": layer_record[5],  # file_id
                "center_coords": center_coords,
                "zoom_level": zoom_level,
                "found_in_db": True,
                "is_geoserver_layer": True,
                "message": f"成功获取图层ID {layer_id} 的坐标系信息: {srs}"
            }
        })
        
    except Exception as e:
        logger.error(f"获取图层坐标系信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取坐标系信息失败: {str(e)}"
        }), 500 