#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.layer_service import LayerService
from services.geoserver_service import GeoServerService
from models.db import get_connection as get_db_connection
import json
import logging

# 创建logger
logger = logging.getLogger(__name__)

layer_bp = Blueprint('layer', __name__)
layer_service = LayerService()
geoserver_service = GeoServerService()

@layer_bp.route('', methods=['GET'])
def list_layers():
    """获取图层列表
    ---
    tags:
      - 图层管理
    parameters:
      - name: workspace_id
        in: query
        type: integer
        description: 工作空间ID
      - name: enabled
        in: query
        type: boolean
        description: 是否启用
      - name: queryable
        in: query
        type: boolean
        description: 是否可查询
      - name: file_id
        in: query
        type: integer
        description: 关联文件ID
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码
      - name: page_size
        in: query
        type: integer
        default: 20
        description: 每页数量
    responses:
      200:
        description: 图层列表
    """
    try:
        # 获取查询参数
        filters = {}
        
        if request.args.get('workspace_id'):
            filters['workspace_id'] = int(request.args.get('workspace_id'))
        
        if request.args.get('enabled') is not None:
            filters['enabled'] = request.args.get('enabled').lower() == 'true'
        
        if request.args.get('queryable') is not None:
            filters['queryable'] = request.args.get('queryable').lower() == 'true'
        
        if request.args.get('file_id'):
            filters['file_id'] = int(request.args.get('file_id'))
        
        if request.args.get('name'):
            filters['name'] = request.args.get('name')
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 获取排序参数
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 获取图层列表
        layers, total = layer_service.get_layers(filters, page, page_size, sort_by, sort_order)
        
        return jsonify({
            'layers': layers,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
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
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({'error': '图层不存在'}), 404
        
        return jsonify(layer), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层详情错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/publish/<int:file_id>', methods=['POST'])
def publish_layer(file_id):
    """发布图层服务
    ---
    tags:
      - 图层管理
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: 文件ID
      - name: body
        in: body
        schema:
          type: object
          properties:
            workspace_name:
              type: string
              description: 工作空间名称
            layer_name:
              type: string
              description: 图层名称
            title:
              type: string
              description: 图层标题
            abstract:
              type: string
              description: 图层摘要
            style_name:
              type: string
              description: 样式名称
            srs:
              type: string
              description: 坐标参考系统
            enabled:
              type: boolean
              description: 是否启用
            queryable:
              type: boolean
              description: 是否可查询
    responses:
      200:
        description: 图层发布成功
      400:
        description: 参数错误
      404:
        description: 文件不存在
    """
    try:
        data = request.json or {}
        
        # 发布图层
        layer_id = layer_service.publish_layer(file_id, data)
        
        return jsonify({
            'id': layer_id,
            'message': '图层发布成功'
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        current_app.logger.error(f"发布图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/<int:layer_id>', methods=['PUT'])
def update_layer(layer_id):
    """更新图层
    ---
    tags:
      - 图层管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
      - name: body
        in: body
        schema:
          type: object
          properties:
            title:
              type: string
              description: 图层标题
            abstract:
              type: string
              description: 图层摘要
            default_style:
              type: string
              description: 默认样式
            enabled:
              type: boolean
              description: 是否启用
            queryable:
              type: boolean
              description: 是否可查询
            opaque:
              type: boolean
              description: 是否不透明
            attribution:
              type: string
              description: 归属信息
    responses:
      200:
        description: 图层更新成功
      404:
        description: 图层不存在
    """
    try:
        data = request.json
        
        # 检查图层是否存在
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({'error': '图层不存在'}), 404
        
        # 更新图层
        layer_service.update_layer(layer_id, data)
        
        return jsonify({'message': '图层更新成功'}), 200
    
    except Exception as e:
        current_app.logger.error(f"更新图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/<int:layer_id>', methods=['DELETE'])
def delete_layer(layer_id):
    """删除图层
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
        description: 图层删除成功
      404:
        description: 图层不存在
    """
    try:
        # 检查图层是否存在
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({'error': '图层不存在'}), 404
        
        # 删除图层
        layer_service.delete_layer(layer_id)
        
        return jsonify({'message': '图层删除成功'}), 200
    
    except Exception as e:
        current_app.logger.error(f"删除图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/<int:layer_id>/capabilities', methods=['GET'])
def get_layer_capabilities(layer_id):
    """获取图层能力信息
    ---
    tags:
      - 图层管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
      - name: service_type
        in: query
        type: string
        enum: [WMS, WFS, WCS]
        description: 服务类型
    responses:
      200:
        description: 图层能力信息
      404:
        description: 图层不存在
    """
    try:
        service_type = request.args.get('service_type', 'WMS').upper()
        
        # 检查图层是否存在
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({'error': '图层不存在'}), 404
        
        # 获取能力信息
        capabilities = layer_service.get_layer_capabilities(layer_id, service_type)
        
        return jsonify(capabilities), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层能力信息错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/<int:layer_id>/preview', methods=['GET'])
def preview_layer(layer_id):
    """预览图层
    ---
    tags:
      - 图层管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
      - name: bbox
        in: query
        type: string
        description: 边界框 (minx,miny,maxx,maxy)
      - name: width
        in: query
        type: integer
        default: 512
        description: 图片宽度
      - name: height
        in: query
        type: integer
        default: 512
        description: 图片高度
      - name: srs
        in: query
        type: string
        default: EPSG:4326
        description: 坐标参考系统
    responses:
      200:
        description: 图层预览图片URL
      404:
        description: 图层不存在
    """
    try:
        # 检查图层是否存在
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({'error': '图层不存在'}), 404
        
        # 获取预览参数
        bbox = request.args.get('bbox')
        width = int(request.args.get('width', 512))
        height = int(request.args.get('height', 512))
        srs = request.args.get('srs', 'EPSG:4326')
        
        # 生成预览URL
        preview_url = layer_service.get_layer_preview_url(
            layer_id, bbox, width, height, srs
        )
        
        return jsonify({
            'preview_url': preview_url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"预览图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/statistics', methods=['GET'])
def get_layer_statistics():
    """获取图层统计信息
    ---
    tags:
      - 图层管理
    responses:
      200:
        description: 图层统计信息
    """
    try:
        stats = layer_service.get_layer_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层统计错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@layer_bp.route('/<int:layer_id>/style', methods=['PUT'])
def update_layer_style(layer_id):
    """更新图层样式
    ---
    tags:
      - 图层管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
      - name: body
        in: body
        schema:
          type: object
          properties:
            style_config:
              type: object
              description: 样式配置
              properties:
                point:
                  type: object
                  properties:
                    color:
                      type: string
                      description: 点颜色 (如 #FF0000)
                    size:
                      type: number
                      description: 点大小
                    shape:
                      type: string
                      description: 点形状 (circle, square, triangle, star, cross, x)
                    opacity:
                      type: number
                      description: 透明度 (0-1)
                line:
                  type: object
                  properties:
                    color:
                      type: string
                      description: 线颜色 (如 #0000FF)
                    width:
                      type: number
                      description: 线宽
                    style:
                      type: string
                      description: 线型 (solid, dashed, dotted, dashdot)
                    opacity:
                      type: number
                      description: 透明度 (0-1)
                    linecap:
                      type: string
                      description: 线端点样式 (round, butt, square)
                    linejoin:
                      type: string
                      description: 线连接样式 (round, bevel, miter)
                polygon:
                  type: object
                  properties:
                    fillColor:
                      type: string
                      description: 填充颜色 (如 #00FF00)
                    fillOpacity:
                      type: number
                      description: 填充透明度 (0-1)
                    strokeColor:
                      type: string
                      description: 边框颜色 (如 #000000)
                    strokeWidth:
                      type: number
                      description: 边框宽度
                    strokeOpacity:
                      type: number
                      description: 边框透明度 (0-1)
    responses:
      200:
        description: 样式更新成功
      400:
        description: 样式配置错误
      404:
        description: 图层不存在
      500:
        description: 服务器内部错误
    """
    try:
        data = request.json
        if not data or 'style_config' not in data:
            return jsonify({
                'success': False,
                'error': '缺少样式配置参数',
                'error_type': 'missing_parameter'
            }), 400
        
        style_config = data['style_config']
        
        # 检查图层是否存在
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({
                'success': False,
                'error': f'图层ID {layer_id} 不存在',
                'error_type': 'not_found'
            }), 404
        
        current_app.logger.info(f"开始更新图层 {layer_id} 的样式")
        current_app.logger.info(f"接收到的样式配置: {style_config}")
        
        # 更新图层样式
        style_result = layer_service.update_layer_style(layer_id, style_config)
        
        if style_result.get('success'):
            # 样式更新成功
            return jsonify({
                'success': True,
                'message': style_result.get('message', '样式更新成功'),
                'data': {
                    'layer_id': layer_id,
                    'style_id': style_result.get('style_id'),
                    'style_name': style_result.get('style_name'),
                    'geoserver_updated': style_result.get('geoserver_updated', False)
                }
            }), 200
        else:
            # 样式更新失败
            error_type = style_result.get('error_type', 'unknown_error')
            error_message = style_result.get('error', '未知错误')
            
            if error_type == 'validation_error':
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'error_type': error_type
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'error_type': error_type
                }), 500
    
    except Exception as e:
        current_app.logger.error(f"更新图层样式时发生未处理的错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'error_type': 'internal_error'
        }), 500

@layer_bp.route('/<int:layer_id>/style', methods=['GET'])
def get_layer_style(layer_id):
    """获取图层样式信息
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
        description: 图层样式信息
      404:
        description: 图层不存在
      500:
        description: 服务器内部错误
    """
    try:
        # 检查图层是否存在
        layer = layer_service.get_layer_by_id(layer_id)
        if not layer:
            return jsonify({
                'success': False,
                'error': f'图层ID {layer_id} 不存在',
                'error_type': 'not_found'
            }), 404
        
        current_app.logger.info(f"获取图层 {layer_id} 的样式信息")
        
        # 获取图层的样式配置
        style_result = layer_service.get_layer_style_config(layer_id)
        
        if style_result.get('success'):
            return jsonify({
                'success': True,
                'data': {
                    'layer_id': layer_id,
                    'layer_name': layer['name'],
                    'workspace_name': layer['workspace_name'],
                    'file_type': layer.get('file_type'),
                    'style_config': style_result.get('style_config'),
                    'style_name': style_result.get('style_name'),
                    'geoserver_styles': style_result.get('geoserver_styles')
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': style_result.get('error', '获取样式信息失败'),
                'error_type': style_result.get('error_type', 'unknown_error')
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"获取图层样式时发生未处理的错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'error_type': 'internal_error'
        }), 500

@layer_bp.route('/style/template/<geometry_type>', methods=['GET'])
def get_style_template(geometry_type):
    """获取样式模板
    ---
    tags:
      - 图层管理
    parameters:
      - name: geometry_type
        in: path
        type: string
        required: true
        description: 几何类型 (point, line, polygon)
    responses:
      200:
        description: 样式模板
      400:
        description: 几何类型不支持
    """
    try:
        from services.sld_template_service import SLDTemplateService
        
        sld_service = SLDTemplateService()
        
        # 验证几何类型
        valid_types = ['point', 'line', 'polygon']
        if geometry_type.lower() not in valid_types:
            return jsonify({
                'success': False,
                'error': f'不支持的几何类型: {geometry_type}，支持的类型: {valid_types}',
                'error_type': 'invalid_geometry_type'
            }), 400
        
        # 生成默认样式配置
        default_config = {
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
                'opacity': 1.0,
                'linecap': 'round',
                'linejoin': 'round'
            },
            'polygon': {
                'fillColor': '#00FF00',
                'fillOpacity': 0.7,
                'strokeColor': '#000000',
                'strokeWidth': 1,
                'strokeOpacity': 1.0
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'geometry_type': geometry_type,
                'default_style_config': {geometry_type: default_config[geometry_type]},
                'supported_options': {
                    'point': {
                        'color': 'string (十六进制颜色，如 #FF0000)',
                        'size': 'number (点大小)',
                        'shape': 'string (circle, square, triangle, star, cross, x)',
                        'opacity': 'number (0-1)'
                    },
                    'line': {
                        'color': 'string (十六进制颜色，如 #0000FF)',
                        'width': 'number (线宽)',
                        'style': 'string (solid, dashed, dotted, dashdot, longdash, shortdash)',
                        'opacity': 'number (0-1)',
                        'linecap': 'string (round, butt, square)',
                        'linejoin': 'string (round, bevel, miter)'
                    },
                    'polygon': {
                        'fillColor': 'string (十六进制颜色，如 #00FF00)',
                        'fillOpacity': 'number (0-1)',
                        'strokeColor': 'string (十六进制颜色，如 #000000)',
                        'strokeWidth': 'number (边框宽度)',
                        'strokeOpacity': 'number (0-1)'
                    }
                }
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取样式模板错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'error_type': 'internal_error'
        }), 500

@layer_bp.route('/<int:layer_id>/bounds', methods=['GET'])
def get_layer_bounds(layer_id):
    """获取图层边界信息
    
    Args:
        layer_id: scene_layers表中的layer_id（对应geoserver_layers.id或files.id）
    """
    try:
        # 获取图层信息 - 根据用户描述的逻辑链条处理
        with get_db_connection() as conn:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 首先尝试从scene_layers中查找，确定服务类型
            cursor.execute("""
            SELECT sl.*, sl.layer_type as service_type
            FROM scene_layers sl
            WHERE sl.layer_id = %s
            LIMIT 1
            """, (layer_id,))
            
            scene_layer = cursor.fetchone()
            
            if scene_layer:
                # 如果在scene_layers中找到，根据service_type处理
                if scene_layer['service_type'] == 'martin' and scene_layer.get('martin_service_id'):
                    # Martin服务：从PostGIS表中计算边界
                    bbox = get_martin_service_bounds(scene_layer['martin_service_id'])
                    layer_info = {
                        'scene_layer_id': scene_layer['id'],
                        'service_type': 'martin',
                        'martin_service_id': scene_layer['martin_service_id']
                    }
                    
                    # 获取图层名称
                    cursor.execute("""
                    SELECT original_filename 
                    FROM vector_martin_services 
                    WHERE id = %s AND status = 'active'
                    """, (scene_layer['martin_service_id'],))
                    martin_result = cursor.fetchone()
                    layer_name = martin_result['original_filename'] if martin_result else f'Martin图层{layer_id}'
                    
                elif scene_layer['service_type'] == 'geoserver':
                    # GeoServer服务：从geoserver_layers表获取信息并调用GetCapabilities
                    cursor.execute("""
                    SELECT gl.id, gl.name as layer_name, gl.title, gl.wms_url,
                           gw.name as workspace_name, f.file_name, f.bbox
                    FROM geoserver_layers gl
                    LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
                    LEFT JOIN files f ON gl.file_id = f.id
                    WHERE gl.id = %s
                    """, (layer_id,))
                    
                    geoserver_layer = cursor.fetchone()
                    if not geoserver_layer:
                        return jsonify({
                            'success': False,
                            'error': f'GeoServer图层不存在 (ID: {layer_id})'
                        }), 404
                    
                    # 构建完整图层名称用于GetCapabilities查询
                    full_layer_name = f"{geoserver_layer['workspace_name']}:{geoserver_layer['layer_name']}"
                    wms_url = geoserver_layer['wms_url']
                    
                    # 尝试从GeoServer GetCapabilities获取边界
                    bbox = get_geoserver_layer_bounds(full_layer_name, wms_url)
                    
                    # 如果GetCapabilities失败，尝试从文件bbox获取
                    if not bbox and geoserver_layer.get('bbox'):
                        if isinstance(geoserver_layer['bbox'], str):
                            try:
                                bbox = json.loads(geoserver_layer['bbox'])
                            except:
                                pass
                        else:
                            bbox = geoserver_layer['bbox']
                    
                    layer_info = {
                        'scene_layer_id': scene_layer['id'],
                        'service_type': 'geoserver',
                        'geoserver_layer_id': geoserver_layer['id'],
                        'full_layer_name': full_layer_name
                    }
                    layer_name = geoserver_layer.get('file_name') or geoserver_layer.get('title') or geoserver_layer['layer_name']
                    
                else:
                    return jsonify({
                        'success': False,
                        'error': f'未知的服务类型: {scene_layer["service_type"]}'
                    }), 400
                    
            else:
                # 如果在scene_layers中没找到，尝试直接作为geoserver_layers.id查询
                cursor.execute("""
                SELECT gl.id, gl.name as layer_name, gl.title, gl.wms_url,
                       gw.name as workspace_name, f.file_name, f.bbox
                FROM geoserver_layers gl
                LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
                LEFT JOIN files f ON gl.file_id = f.id
                WHERE gl.id = %s
                """, (layer_id,))
                
                geoserver_layer = cursor.fetchone()
                if geoserver_layer:
                    # 直接作为GeoServer图层处理
                    full_layer_name = f"{geoserver_layer['workspace_name']}:{geoserver_layer['layer_name']}"
                    wms_url = geoserver_layer['wms_url']
                    
                    # 尝试从GeoServer GetCapabilities获取边界
                    bbox = get_geoserver_layer_bounds(full_layer_name, wms_url)
                    
                    # 如果GetCapabilities失败，尝试从文件bbox获取
                    if not bbox and geoserver_layer.get('bbox'):
                        if isinstance(geoserver_layer['bbox'], str):
                            try:
                                bbox = json.loads(geoserver_layer['bbox'])
                            except:
                                pass
                        else:
                            bbox = geoserver_layer['bbox']
                    
                    layer_info = {
                        'scene_layer_id': None,
                        'service_type': 'geoserver',
                        'geoserver_layer_id': geoserver_layer['id'],
                        'full_layer_name': full_layer_name
                    }
                    layer_name = geoserver_layer.get('file_name') or geoserver_layer.get('title') or geoserver_layer['layer_name']
                else:
                    # 最后尝试作为files.id查询（Martin服务）
                    cursor.execute("""
                    SELECT f.*, vms.id as martin_service_id
                    FROM files f
                    LEFT JOIN vector_martin_services vms ON vms.file_id = f.id::text
                    WHERE f.id = %s AND vms.status = 'active'
                    LIMIT 1
                    """, (layer_id,))
                    
                    file_record = cursor.fetchone()
                    if file_record and file_record['martin_service_id']:
                        # 作为Martin服务处理
                        bbox = get_martin_service_bounds(file_record['martin_service_id'])
                        layer_info = {
                            'scene_layer_id': None,
                            'service_type': 'martin',
                            'martin_service_id': file_record['martin_service_id']
                        }
                        layer_name = file_record.get('file_name') or f'Martin图层{layer_id}'
                    else:
                        return jsonify({
                            'success': False,
                            'error': '图层不存在'
                        }), 404
            
            if not bbox:
                return jsonify({
                    'success': False,
                    'error': '无法获取图层边界信息'
                }), 500
                
            return jsonify({
                'success': True,
                'data': {
                    'bbox': bbox,
                    'layer_id': layer_id,
                    'scene_layer_id': layer_info.get('scene_layer_id'),
                    'layer_name': layer_name,
                    'service_type': layer_info['service_type'],
                    'coordinate_system': 'EPSG:4326'  # 返回的坐标系统一为WGS84
                }
            })
            
    except Exception as e:
        logger.error(f"获取图层边界失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取图层边界失败: {str(e)}'
        }), 500


def get_martin_service_bounds(martin_service_id):
    """从Martin服务获取PostGIS表的边界"""
    try:
        with get_db_connection() as conn:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 获取Martin服务信息
            cursor.execute("""
            SELECT table_name, original_filename
            FROM vector_martin_services 
            WHERE id = %s AND status = 'active'
            """, (martin_service_id,))
            
            service = cursor.fetchone()
            if not service:
                return None
                
            table_name = service['table_name']
            
            # 动态获取几何字段名称
            cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND data_type = 'USER-DEFINED' 
            AND udt_name = 'geometry'
            ORDER BY ordinal_position
            LIMIT 1
            """, (table_name,))
            
            geom_column_result = cursor.fetchone()
            if not geom_column_result:
                logger.error(f"表 {table_name} 中未找到几何字段")
                return None
                
            geom_column = geom_column_result['column_name']
            logger.info(f"表 {table_name} 中找到几何字段: {geom_column}")
            
            # 获取几何字段的SRID和边界
            cursor.execute(f"""
            SELECT 
                ST_SRID((SELECT "{geom_column}" FROM "{table_name}" WHERE "{geom_column}" IS NOT NULL LIMIT 1)) as srid,
                ST_XMin(extent) as minx, 
                ST_YMin(extent) as miny,
                ST_XMax(extent) as maxx, 
                ST_YMax(extent) as maxy
            FROM (
                SELECT ST_Extent("{geom_column}") as extent
                FROM "{table_name}"
                WHERE "{geom_column}" IS NOT NULL
            ) t
            """)
            
            result = cursor.fetchone()
            if not result or not all(v is not None for v in [result['minx'], result['miny'], result['maxx'], result['maxy']]):
                logger.error(f"表 {table_name} 中无法计算有效的边界框")
                return None
            
            # 获取原始坐标系SRID
            source_srid = result['srid']
            minx, miny = float(result['minx']), float(result['miny'])
            maxx, maxy = float(result['maxx']), float(result['maxy'])
            
            logger.info(f"表 {table_name}, 原始坐标系: EPSG:{source_srid}, 边界框: [{minx}, {miny}, {maxx}, {maxy}]")
            
            # 如果不是地理坐标系（4326），则进行坐标转换
            if source_srid != 4326:
                try:
                    # 使用PostGIS进行坐标转换
                    cursor.execute("""
                    SELECT 
                        ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), %s), 4326)) as min_lon,
                        ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), %s), 4326)) as min_lat,
                        ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), %s), 4326)) as max_lon,
                        ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), %s), 4326)) as max_lat
                    """, (minx, miny, source_srid, minx, miny, source_srid, 
                          maxx, maxy, source_srid, maxx, maxy, source_srid))
                    
                    transform_result = cursor.fetchone()
                    if transform_result:
                        converted_bbox = {
                            'minx': float(transform_result['min_lon']),
                            'miny': float(transform_result['min_lat']),
                            'maxx': float(transform_result['max_lon']),
                            'maxy': float(transform_result['max_lat'])
                        }
                        logger.info(f"转换后地理坐标: {converted_bbox}")
                        return converted_bbox
                except Exception as transform_error:
                    logger.error(f"坐标转换失败: {transform_error}")
                    # 转换失败时返回原始坐标
                    pass
            
            # 如果已经是地理坐标系或转换失败，返回原始坐标
            return {
                'minx': minx,
                'miny': miny,
                'maxx': maxx,
                'maxy': maxy
            }
                
    except Exception as e:
        logger.error(f"获取Martin服务边界失败: {str(e)}")
        
    return None


def get_geoserver_layer_bounds(layer_name, wms_url):
    """从GeoServer WMS GetCapabilities获取图层边界"""
    try:
        import requests
        from xml.etree import ElementTree as ET
        
        if not wms_url:
            return None
            
        # 构造GetCapabilities请求
        base_url = wms_url.split('?')[0]
        capabilities_url = f"{base_url}?service=WMS&version=1.3.0&request=GetCapabilities"
        
        response = requests.get(capabilities_url, timeout=30)
        response.raise_for_status()
        
        # 解析XML响应
        root = ET.fromstring(response.content)
        
        # 查找指定图层
        namespaces = {
            'wms': 'http://www.opengis.net/wms',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        
        # 查找图层
        for layer in root.findall('.//wms:Layer', namespaces):
            name_elem = layer.find('wms:Name', namespaces)
            if name_elem is not None and name_elem.text == layer_name:
                # 查找边界框
                bbox_elem = layer.find('wms:BoundingBox[@CRS="EPSG:4326"]', namespaces)
                if bbox_elem is not None:
                    return {
                        'minx': float(bbox_elem.get('minx')),
                        'miny': float(bbox_elem.get('miny')),
                        'maxx': float(bbox_elem.get('maxx')),
                        'maxy': float(bbox_elem.get('maxy'))
                    }
                    
                # 如果没有找到EPSG:4326的边界框，尝试其他CRS
                bbox_elem = layer.find('wms:BoundingBox', namespaces)
                if bbox_elem is not None:
                    return {
                        'minx': float(bbox_elem.get('minx')),
                        'miny': float(bbox_elem.get('miny')),
                        'maxx': float(bbox_elem.get('maxx')),
                        'maxy': float(bbox_elem.get('maxy'))
                    }
                    
    except Exception as e:
        logger.error(f"获取GeoServer图层边界失败: {str(e)}")
        
    return None 