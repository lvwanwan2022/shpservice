#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SLD样式文件管理路由
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from services.sld_style_service import SLDStyleService
import logging
import os

# 创建logger
logger = logging.getLogger(__name__)

sld_style_bp = Blueprint('sld_style', __name__, url_prefix='/api/sld-styles')
sld_style_service = SLDStyleService()

@sld_style_bp.route('/initialize', methods=['POST'])
def initialize_database():
    """初始化SLD样式数据库表
    ---
    tags:
      - SLD样式管理
    responses:
      200:
        description: 初始化成功
      500:
        description: 服务器内部错误
    """
    try:
        success = sld_style_service.initialize_database()
        if success:
            return jsonify({'message': 'SLD样式数据库初始化成功'}), 200
        else:
            return jsonify({'error': 'SLD样式数据库初始化失败'}), 500
    except Exception as e:
        current_app.logger.error(f"初始化SLD样式数据库失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/upload', methods=['POST'])
def upload_sld_file():
    """上传SLD样式文件
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: SLD文件
      - name: name
        in: formData
        type: string
        required: true
        description: 样式名称
      - name: description
        in: formData
        type: string
        required: false
        description: 样式描述
      - name: geometry_type
        in: formData
        type: string
        required: true
        enum: [point, line, polygon]
        description: 几何类型
    responses:
      200:
        description: 上传成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    try:
        # 添加调试日志
        current_app.logger.info("=== 开始处理SLD文件上传请求 ===")
        current_app.logger.info(f"请求文件: {list(request.files.keys())}")
        current_app.logger.info(f"请求表单: {dict(request.form)}")
        
        # 检查文件是否存在
        if 'file' not in request.files:
            current_app.logger.error("错误: 未找到上传文件")
            return jsonify({'error': '未找到上传文件'}), 400
        
        file = request.files['file']
        current_app.logger.info(f"文件名: {file.filename}")
        
        if file.filename == '':
            current_app.logger.error("错误: 未选择文件")
            return jsonify({'error': '未选择文件'}), 400
        
        # 获取表单参数
        name = request.form.get('name')
        description = request.form.get('description', '')
        geometry_type = request.form.get('geometry_type')
        
        current_app.logger.info(f"样式名称: {name}")
        current_app.logger.info(f"样式描述: {description}")
        current_app.logger.info(f"几何类型: {geometry_type}")
        
        if not name or not geometry_type:
            missing = []
            if not name:
                missing.append('name')
            if not geometry_type:
                missing.append('geometry_type')
            error_msg = f'缺少必要参数: {", ".join(missing)}'
            current_app.logger.error(f"错误: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # 验证几何类型
        valid_geometry_types = ['point', 'line', 'polygon']
        if geometry_type not in valid_geometry_types:
            error_msg = f'不支持的几何类型: {geometry_type}'
            current_app.logger.error(f"错误: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # 上传文件
        current_app.logger.info("开始调用 upload_sld_file 服务...")
        result = sld_style_service.upload_sld_file(
            file=file,
            name=name,
            description=description,
            geometry_type=geometry_type
        )
        
        current_app.logger.info(f"SLD文件上传成功: {result}")
        return jsonify({
            'message': 'SLD文件上传成功',
            'data': result
        }), 200
        
    except ValueError as e:
        current_app.logger.error(f"值错误: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"上传SLD文件失败: {str(e)}", exc_info=True)
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500

@sld_style_bp.route('', methods=['GET'])
def get_sld_styles():
    """获取SLD样式文件列表
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: geometry_type
        in: query
        type: string
        enum: [point, line, polygon]
        description: 几何类型过滤
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
        description: 获取成功
      500:
        description: 服务器内部错误
    """
    try:
        # 获取查询参数
        geometry_type = request.args.get('geometry_type')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 获取样式列表
        styles, total = sld_style_service.get_sld_styles(
            geometry_type=geometry_type,
            page=page,
            page_size=page_size
        )
        
        return jsonify({
            'styles': styles,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取SLD样式列表失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/<int:style_id>', methods=['GET'])
def get_sld_style(style_id):
    """获取SLD样式文件详情
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: style_id
        in: path
        type: integer
        required: true
        description: 样式ID
    responses:
      200:
        description: 获取成功
      404:
        description: 样式不存在
      500:
        description: 服务器内部错误
    """
    try:
        style = sld_style_service.get_sld_style_by_id(style_id)
        if not style:
            return jsonify({'error': 'SLD样式文件不存在'}), 404
        
        return jsonify({'data': style}), 200
        
    except Exception as e:
        current_app.logger.error(f"获取SLD样式详情失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/<int:style_id>/content', methods=['GET'])
def get_sld_style_content(style_id):
    """获取SLD样式文件的文本内容
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: style_id
        in: path
        type: integer
        required: true
        description: 样式ID
    responses:
      200:
        description: 获取成功
      404:
        description: 样式不存在
      500:
        description: 服务器内部错误
    """
    try:
        style = sld_style_service.get_sld_style_by_id(style_id)
        if not style:
            return jsonify({'error': 'SLD样式文件不存在'}), 404
        
        return jsonify({
            'id': style['id'],
            'name': style['name'],
            'description': style['description'],
            'geometry_type': style['geometry_type'],
            'content': style['content']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取SLD样式内容失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/<int:style_id>/content', methods=['PUT'])
def update_sld_style_content(style_id):
    """直接更新SLD样式文件的文本内容
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: style_id
        in: path
        type: integer
        required: true
        description: 样式ID
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
                description: 样式名称
              description:
                type: string
                description: 样式描述
              geometry_type:
                type: string
                enum: [point, line, polygon]
                description: 几何类型
              content:
                type: string
                description: SLD文件内容
    responses:
      200:
        description: 更新成功
      400:
        description: 请求参数错误
      404:
        description: 样式不存在
      500:
        description: 服务器内部错误
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        result = sld_style_service.update_sld_style_content(style_id, data)
        if not result:
            return jsonify({'error': 'SLD样式文件不存在'}), 404
        
        return jsonify({
            'message': 'SLD样式文件更新成功',
            'data': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"更新SLD样式内容失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/<int:style_id>/download', methods=['GET'])
def download_sld_file(style_id):
    """下载SLD样式文件
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: style_id
        in: path
        type: integer
        required: true
        description: 样式ID
    responses:
      200:
        description: 下载成功
      404:
        description: 样式不存在
      500:
        description: 服务器内部错误
    """
    try:
        file_info = sld_style_service.download_sld_file(style_id)
        
        return send_file(
            file_info['file_path'],
            as_attachment=True,
            download_name=file_info['filename'],
            mimetype='application/xml'
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"下载SLD文件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/<int:style_id>', methods=['DELETE'])
def delete_sld_style(style_id):
    """删除SLD样式文件
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: style_id
        in: path
        type: integer
        required: true
        description: 样式ID
    responses:
      200:
        description: 删除成功
      404:
        description: 样式不存在
      500:
        description: 服务器内部错误
    """
    try:
        result = sld_style_service.delete_sld_style(style_id)
        if not result:
            return jsonify({'error': 'SLD样式文件不存在'}), 404
        
        return jsonify({'message': 'SLD样式文件删除成功'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"删除SLD样式文件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/<int:style_id>', methods=['PUT'])
def update_sld_style(style_id):
    """更新SLD样式文件
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: style_id
        in: path
        type: integer
        required: true
        description: 样式ID
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
                description: 样式名称
              description:
                type: string
                description: 样式描述
              geometry_type:
                type: string
                enum: [point, line, polygon]
                description: 几何类型
              point:
                type: object
                properties:
                  color:
                    type: string
                  size:
                    type: number
              line:
                type: object
                properties:
                  color:
                    type: string
                  width:
                    type: number
              polygon:
                type: object
                properties:
                  fillColor:
                    type: string
                  strokeColor:
                    type: string
                  strokeWidth:
                    type: number
                  fillOpacity:
                    type: number
    responses:
      200:
        description: 更新成功
      400:
        description: 请求参数错误
      404:
        description: 样式不存在
      500:
        description: 服务器内部错误
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        result = sld_style_service.update_sld_style(style_id, data)
        if not result:
            return jsonify({'error': 'SLD样式文件不存在'}), 404
        
        return jsonify({
            'message': 'SLD样式文件更新成功',
            'data': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"更新SLD样式文件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/apply', methods=['POST'])
def apply_sld_style_to_layer():
    """将SLD样式应用到图层
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: layer_id
        in: body
        type: integer
        required: true
        description: 图层ID
      - name: sld_style_id
        in: body
        type: integer
        required: true
        description: SLD样式ID
    responses:
      200:
        description: 应用成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    try:
        data = request.get_json()
        layer_id = data.get('layer_id')
        sld_style_id = data.get('sld_style_id')
        
        if not layer_id or not sld_style_id:
            return jsonify({'error': '缺少必要参数'}), 400
        
        result = sld_style_service.apply_sld_style_to_layer(
            layer_id=layer_id,
            sld_style_id=sld_style_id
        )
        
        return jsonify({
            'message': 'SLD样式应用成功',
            'data': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"应用SLD样式失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/layer/<int:layer_id>', methods=['GET'])
def get_layer_sld_style(layer_id):
    """获取图层的当前SLD样式
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
    responses:
      200:
        description: 获取成功
      404:
        description: 图层没有应用SLD样式
      500:
        description: 服务器内部错误
    """
    try:
        style = sld_style_service.get_layer_sld_style(layer_id)
        if not style:
            return jsonify({'data': None, 'message': '图层没有应用SLD样式'}), 200
        
        return jsonify({'data': style}), 200
        
    except Exception as e:
        current_app.logger.error(f"获取图层SLD样式失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@sld_style_bp.route('/layer/<int:layer_id>/remove', methods=['POST'])
def remove_layer_sld_style(layer_id):
    """移除图层的SLD样式
    ---
    tags:
      - SLD样式管理
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
    responses:
      200:
        description: 移除成功
      404:
        description: 图层没有应用SLD样式
      500:
        description: 服务器内部错误
    """
    try:
        result = sld_style_service.remove_layer_sld_style(layer_id)
        if not result:
            return jsonify({'error': '图层没有应用SLD样式'}), 404
        
        return jsonify({'message': '图层SLD样式移除成功'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"移除图层SLD样式失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
