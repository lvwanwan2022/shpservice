#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.scene_service import SceneService
from services.file_service import FileService

layer_bp = Blueprint('layer', __name__)
scene_service = SceneService()
file_service = FileService()

@layer_bp.route('', methods=['GET'])
def list_layers():
    """获取图层列表
    ---
    tags:
      - 图层管理
    parameters:
      - name: scene_id
        in: query
        type: integer
        required: false
        description: 场景ID
    responses:
      200:
        description: 图层列表
    """
    try:
        scene_id = request.args.get('scene_id')
        
        if scene_id:
            # 获取指定场景的图层
            layers = scene_service.get_layers_by_scene(int(scene_id))
        else:
            # 获取所有可用于添加到场景的文件/图层
            sql = """
            SELECT f.id, f.file_name, f.file_type, f.dimension, f.discipline,
                f.geoserver_layer, f.wms_url, f.wfs_url, f.is_public,
                u.username as uploader
            FROM files f
            LEFT JOIN users u ON f.user_id = u.id
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

@layer_bp.route('/<int:layer_id>', methods=['GET'])
def get_layer(layer_id):
    """获取图层详情
    ---
    tags:
      - 图层管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
    responses:
      200:
        description: 图层详情
      404:
        description: 图层不存在
    """
    try:
        # 查询图层和关联的文件信息
        sql = """
        SELECT l.*, f.file_name, f.file_type, f.dimension, f.discipline,
               f.geoserver_layer, f.wms_url, f.wfs_url, f.is_public,
               s.name as scene_name
        FROM layers l
        JOIN files f ON l.file_id = f.id
        JOIN scenes s ON l.scene_id = s.id
        WHERE l.id = %(layer_id)s
        """
        
        result = execute_query(sql, {'layer_id': layer_id})
        
        if not result:
            return jsonify({'error': '图层不存在'}), 404
        
        return jsonify(result[0]), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层详情错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/styles', methods=['GET'])
def get_layer_styles():
    """获取图层样式选项
    ---
    tags:
      - 图层管理
    parameters:
      - name: file_type
        in: query
        type: string
        required: true
        description: 文件类型(shp/dem/dom/dwg/dxf/geojson)
    responses:
      200:
        description: 图层样式选项
    """
    try:
        file_type = request.args.get('file_type', '').lower()
        
        # 根据文件类型返回不同的样式选项
        styles = {}
        
        if file_type in ['shp', 'dwg', 'dxf', 'geojson']:
            # 矢量数据样式
            styles = {
                'point': {
                    'size': [3, 5, 8, 10, 15],
                    'color': ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'],
                    'shape': ['circle', 'square', 'triangle', 'star']
                },
                'line': {
                    'width': [1, 2, 3, 5, 8],
                    'color': ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'],
                    'style': ['solid', 'dashed', 'dotted', 'dash-dot']
                },
                'polygon': {
                    'fill_color': ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'],
                    'outline_color': ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF'],
                    'outline_width': [0, 1, 2, 3, 5],
                    'opacity': [0.1, 0.3, 0.5, 0.7, 1.0]
                }
            }
        elif file_type in ['dem']:
            # DEM栅格数据样式
            styles = {
                'palette': ['elevation', 'rainbow', 'terrain', 'grayscale'],
                'opacity': [0.1, 0.3, 0.5, 0.7, 1.0],
                'contrast': [-10, -5, 0, 5, 10],
                'brightness': [-10, -5, 0, 5, 10]
            }
        elif file_type in ['dom']:
            # DOM栅格数据样式
            styles = {
                'opacity': [0.1, 0.3, 0.5, 0.7, 1.0],
                'contrast': [-10, -5, 0, 5, 10],
                'brightness': [-10, -5, 0, 5, 10],
                'saturation': [-10, -5, 0, 5, 10]
            }
        
        return jsonify({
            'styles': styles
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层样式选项错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

from models.db import execute_query 