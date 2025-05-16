#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app, send_file
from services.geoserver_service import GeoServerService
from models.db import execute_query
import os
import tempfile

geoservice_bp = Blueprint('geoservice', __name__)
geoserver_service = GeoServerService()

@geoservice_bp.route('/layer_info/<layer_name>', methods=['GET'])
def get_layer_info(layer_name):
    """获取图层信息
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: layer_name
        in: path
        type: string
        required: true
        description: 图层名称
    responses:
      200:
        description: 图层信息
      404:
        description: 图层不存在
    """
    try:
        # 从GeoServer获取图层信息
        layer_info = geoserver_service.get_layer_info(layer_name)
        
        return jsonify(layer_info), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层信息错误: {str(e)}")
        return jsonify({'error': '图层不存在或无法访问'}), 404

@geoservice_bp.route('/wms_capabilities', methods=['GET'])
def get_wms_capabilities():
    """获取WMS服务能力
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: WMS服务能力
    """
    try:
        url = f"{geoserver_service.url}/wms?service=WMS&version=1.3.0&request=GetCapabilities"
        
        return jsonify({
            'wms_capabilities_url': url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取WMS服务能力错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/wfs_capabilities', methods=['GET'])
def get_wfs_capabilities():
    """获取WFS服务能力
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: WFS服务能力
    """
    try:
        url = f"{geoserver_service.url}/wfs?service=WFS&version=2.0.0&request=GetCapabilities"
        
        return jsonify({
            'wfs_capabilities_url': url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取WFS服务能力错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/layers', methods=['GET'])
def list_layers():
    """获取所有图层
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: 图层列表
    """
    try:
        # 从数据库获取图层列表
        sql = """
        SELECT DISTINCT f.id, f.file_name, f.file_type, f.discipline,
               f.geoserver_layer, f.wms_url, f.wfs_url
        FROM files f
        WHERE f.geoserver_layer IS NOT NULL
        ORDER BY f.upload_date DESC
        """
        
        layers = execute_query(sql)
        
        return jsonify({
            'layers': layers
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/layer_preview/<layer_name>', methods=['GET'])
def layer_preview(layer_name):
    """获取图层预览
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: layer_name
        in: path
        type: string
        required: true
        description: 图层名称
      - name: width
        in: query
        type: integer
        required: false
        default: 800
        description: 预览宽度
      - name: height
        in: query
        type: integer
        required: false
        default: 600
        description: 预览高度
    responses:
      200:
        description: 图层预览图片
      404:
        description: 图层不存在
    """
    try:
        # 获取查询参数
        width = request.args.get('width', 800)
        height = request.args.get('height', 600)
        
        # 构建WMS请求URL
        bbox = request.args.get('bbox')
        bbox_param = f"&bbox={bbox}" if bbox else ""
        
        preview_url = f"{geoserver_service.url}/wms?service=WMS&version=1.3.0&request=GetMap&layers={layer_name}&styles=&width={width}&height={height}&format=image/png{bbox_param}&transparent=true&CRS=EPSG:4326"
        
        return jsonify({
            'preview_url': preview_url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层预览错误: {str(e)}")
        return jsonify({'error': '图层不存在或无法访问'}), 404 