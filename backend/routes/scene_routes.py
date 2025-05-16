#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.scene_service import SceneService

scene_bp = Blueprint('scene', __name__)
scene_service = SceneService()

@scene_bp.route('', methods=['POST'])
def create_scene():
    """创建场景
    ---
    tags:
      - 场景管理
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: 场景名称
            description:
              type: string
              description: 场景描述
            is_public:
              type: boolean
              description: 是否公开
            user_id:
              type: integer
              description: 用户ID
    responses:
      200:
        description: 场景创建成功
      400:
        description: 参数错误
    """
    try:
        data = request.json
        
        # 验证必填字段
        if not data.get('name'):
            return jsonify({'error': '缺少必填字段: name'}), 400
        
        # 准备场景数据
        scene_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'is_public': data.get('is_public', True),
            'user_id': data.get('user_id', 1)  # 暂时使用固定用户ID
        }
        
        # 创建场景
        scene_id = scene_service.create_scene(scene_data)
        
        return jsonify({
            'id': scene_id,
            'message': '场景创建成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"创建场景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>', methods=['PUT'])
def update_scene(scene_id):
    """更新场景
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: 场景名称
            description:
              type: string
              description: 场景描述
            is_public:
              type: boolean
              description: 是否公开
    responses:
      200:
        description: 场景更新成功
      404:
        description: 场景不存在
    """
    try:
        data = request.json
        
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 准备场景数据
        scene_data = {
            'name': data.get('name', scene['name']),
            'description': data.get('description', scene['description']),
            'is_public': data.get('is_public', scene['is_public'])
        }
        
        # 更新场景
        scene_service.update_scene(scene_id, scene_data)
        
        return jsonify({
            'message': '场景更新成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"更新场景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>', methods=['DELETE'])
def delete_scene(scene_id):
    """删除场景
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
    responses:
      200:
        description: 场景删除成功
      404:
        description: 场景不存在
    """
    try:
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 删除场景
        scene_service.delete_scene(scene_id)
        
        return jsonify({
            'message': '场景删除成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"删除场景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('', methods=['GET'])
def list_scenes():
    """获取场景列表
    ---
    tags:
      - 场景管理
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: 用户ID(不传则获取所有公开场景)
      - name: public_only
        in: query
        type: boolean
        required: false
        default: false
        description: 是否只获取公开场景
    responses:
      200:
        description: 场景列表
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id')
        public_only = request.args.get('public_only', 'false').lower() == 'true'
        
        if user_id:
            user_id = int(user_id)
        
        # 获取场景列表
        scenes = scene_service.get_scenes(user_id, public_only)
        
        return jsonify({
            'scenes': scenes
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取场景列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>', methods=['GET'])
def get_scene(scene_id):
    """获取场景详情
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
    responses:
      200:
        description: 场景详情
      404:
        description: 场景不存在
    """
    try:
        # 获取场景信息
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 获取场景图层
        layers = scene_service.get_layers_by_scene(scene_id)
        
        return jsonify({
            'scene': scene,
            'layers': layers
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取场景详情错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers', methods=['POST'])
def add_layer(scene_id):
    """添加图层到场景
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - file_id
            - layer_name
          properties:
            file_id:
              type: integer
              description: 文件ID
            layer_name:
              type: string
              description: 图层名称
            visibility:
              type: boolean
              description: 是否可见
            style_config:
              type: object
              description: 样式配置
    responses:
      200:
        description: 图层添加成功
      400:
        description: 参数错误
      404:
        description: 场景不存在
    """
    try:
        data = request.json
        
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 验证必填字段
        if not data.get('file_id'):
            return jsonify({'error': '缺少必填字段: file_id'}), 400
        
        if not data.get('layer_name'):
            return jsonify({'error': '缺少必填字段: layer_name'}), 400
        
        # 准备图层数据
        layer_data = {
            'scene_id': scene_id,
            'file_id': data.get('file_id'),
            'layer_name': data.get('layer_name'),
            'visibility': data.get('visibility', True),
            'style_config': data.get('style_config', {})
        }
        
        # 添加图层
        layer_id = scene_service.add_layer(layer_data)
        
        return jsonify({
            'id': layer_id,
            'message': '图层添加成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"添加图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers/<int:layer_id>', methods=['PUT'])
def update_layer(scene_id, layer_id):
    """更新场景图层
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            layer_name:
              type: string
              description: 图层名称
            visibility:
              type: boolean
              description: 是否可见
            style_config:
              type: object
              description: 样式配置
    responses:
      200:
        description: 图层更新成功
      404:
        description: 场景或图层不存在
    """
    try:
        data = request.json
        
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 获取图层列表，检查图层是否存在
        layers = scene_service.get_layers_by_scene(scene_id)
        layer_exists = False
        for layer in layers:
            if layer['id'] == layer_id:
                layer_exists = True
                break
        
        if not layer_exists:
            return jsonify({'error': '图层不存在'}), 404
        
        # 准备图层数据
        layer_data = {
            'layer_name': data.get('layer_name'),
            'visibility': data.get('visibility'),
            'style_config': data.get('style_config')
        }
        
        # 更新图层
        scene_service.update_layer(layer_id, layer_data)
        
        return jsonify({
            'message': '图层更新成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"更新图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers/<int:layer_id>', methods=['DELETE'])
def delete_layer(scene_id, layer_id):
    """删除场景图层
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
    responses:
      200:
        description: 图层删除成功
      404:
        description: 场景或图层不存在
    """
    try:
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 获取图层列表，检查图层是否存在
        layers = scene_service.get_layers_by_scene(scene_id)
        layer_exists = False
        for layer in layers:
            if layer['id'] == layer_id:
                layer_exists = True
                break
        
        if not layer_exists:
            return jsonify({'error': '图层不存在'}), 404
        
        # 删除图层
        scene_service.delete_layer(layer_id)
        
        return jsonify({
            'message': '图层删除成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"删除图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers/reorder', methods=['POST'])
def reorder_layers(scene_id):
    """重新排序场景图层
    ---
    tags:
      - 场景管理
    parameters:
      - name: scene_id
        in: path
        type: integer
        required: true
        description: 场景ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            layer_order:
              type: object
              description: 图层ID到顺序的映射，例如：{"1": 2, "3": 1}
    responses:
      200:
        description: 图层重新排序成功
      400:
        description: 参数错误
      404:
        description: 场景不存在
    """
    try:
        data = request.json
        
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 验证必填字段
        if not data.get('layer_order'):
            return jsonify({'error': '缺少必填字段: layer_order'}), 400
        
        # 验证layer_order格式
        layer_order = data.get('layer_order')
        if not isinstance(layer_order, dict):
            return jsonify({'error': 'layer_order必须是对象'}), 400
        
        # 将字符串键转换为整数
        layer_order_map = {}
        for layer_id, order in layer_order.items():
            layer_order_map[int(layer_id)] = int(order)
        
        # 重新排序图层
        scene_service.reorder_layers(scene_id, layer_order_map)
        
        return jsonify({
            'message': '图层重新排序成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"重新排序图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500 