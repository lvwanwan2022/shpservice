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
            - layer_id
          properties:
            layer_id:
              type: integer
              description: 图层ID（Martin服务使用负数虚拟ID）
            layer_name:
              type: string
              description: 图层名称
            service_type:
              type: string
              description: 服务类型（martin或geoserver）
            martin_file_id:
              type: string
              description: Martin服务文件ID（UUID）
            martin_service_id:
              type: integer
              description: Martin服务ID
            mvt_url:
              type: string
              description: MVT瓦片URL
            tilejson_url:
              type: string
              description: TileJSON URL
            file_id:
              type: integer
              description: 原始文件ID
            file_type:
              type: string
              description: 文件类型
            discipline:
              type: string
              description: 专业
            layer_order:
              type: integer
              description: 图层顺序
            visible:
              type: boolean
              description: 是否可见
            opacity:
              type: number
              description: 透明度 (0.0-1.0)
            style_name:
              type: string
              description: 样式名称
            custom_style:
              type: object
              description: 自定义样式配置
            queryable:
              type: boolean
              description: 是否可查询
            selectable:
              type: boolean
              description: 是否可选择
    responses:
      200:
        description: 图层添加成功
      400:
        description: 参数错误
      404:
        description: 场景不存在
    """
    try:
        # 记录请求信息
        current_app.logger.info(f"收到添加图层请求: scene_id={scene_id}")
        
        data = request.json
        current_app.logger.info(f"请求数据: {data}")
        
        # 检查请求数据是否为空
        if not data:
            current_app.logger.error("请求数据为空")
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 检查场景是否存在
        current_app.logger.info(f"检查场景是否存在: scene_id={scene_id}")
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            current_app.logger.error(f"场景不存在: scene_id={scene_id}")
            return jsonify({'error': '场景不存在'}), 404
        
        current_app.logger.info(f"场景存在: {scene['name']}")
        
        # 验证必填字段
        if not data.get('layer_id'):
            current_app.logger.error("缺少必填字段: layer_id")
            return jsonify({'error': '缺少必填字段: layer_id'}), 400
        
        layer_id = data.get('layer_id')
        service_type = data.get('service_type', 'geoserver')
        
        # 根据服务类型检查图层是否存在
        from models.db import execute_query
        
        if service_type == 'martin':
            # Martin服务验证
            current_app.logger.info(f"验证Martin服务图层: layer_id={layer_id}")
            
            # 检查必要的Martin服务字段
            martin_file_id = data.get('martin_file_id')
            martin_service_id = data.get('martin_service_id')
            
            # 优先使用martin_service_id，如果没有则通过martin_file_id查找
            if martin_service_id:
                # 根据layer_service_type确定查询哪个表
                layer_service_type = data.get('layer_service_type', 'geojson')
                
                if layer_service_type == 'shp':
                    martin_check = execute_query(
                        "SELECT * FROM shp_martin_services WHERE id = %s AND status = 'active'", 
                        (martin_service_id,)
                    )
                else:
                    martin_check = execute_query(
                        "SELECT * FROM geojson_martin_services WHERE id = %s AND status = 'active'", 
                        (martin_service_id,)
                    )
                
                if not martin_check:
                    current_app.logger.error(f"Martin服务不存在: martin_service_id={martin_service_id}, service_type={layer_service_type}")
                    return jsonify({'error': f'Martin服务不存在'}), 400
                
                current_app.logger.info(f"Martin服务存在: {martin_check[0]['table_name']}")
                
                # 获取martin_service_id
                martin_service_id = martin_check[0]['id']
                current_app.logger.info(f"Martin服务存在: {martin_check[0]['table_name']}, service_type={layer_service_type}")
                
            elif martin_file_id:
                # 优先查询指定类型的表，如果没有则查询另一个表
                layer_service_type = data.get('layer_service_type', 'geojson')
                martin_check = None
                
                if layer_service_type == 'shp':
                    martin_check = execute_query(
                        "SELECT * FROM shp_martin_services WHERE file_id = %s AND status = 'active'", 
                        (martin_file_id,)
                    )
                    if not martin_check:
                        # 如果SHP表中没有，尝试查询GeoJSON表
                        martin_check = execute_query(
                            "SELECT * FROM geojson_martin_services WHERE file_id = %s AND status = 'active'", 
                            (martin_file_id,)
                        )
                        if martin_check:
                            layer_service_type = 'geojson'
                else:
                    martin_check = execute_query(
                        "SELECT * FROM geojson_martin_services WHERE file_id = %s AND status = 'active'", 
                        (martin_file_id,)
                    )
                    if not martin_check:
                        # 如果GeoJSON表中没有，尝试查询SHP表
                        martin_check = execute_query(
                            "SELECT * FROM shp_martin_services WHERE file_id = %s AND status = 'active'", 
                            (martin_file_id,)
                        )
                        if martin_check:
                            layer_service_type = 'shp'
                
                if not martin_check:
                    current_app.logger.error(f"Martin服务不存在: file_id={martin_file_id}")
                    return jsonify({'error': f'Martin服务不存在'}), 400
                
                # 获取martin_service_id
                martin_service_id = martin_check[0]['id']
                current_app.logger.info(f"Martin服务存在: {martin_check[0]['table_name']}, service_type={layer_service_type}")
                
            else:
                current_app.logger.error("Martin服务缺少必要字段: martin_service_id或martin_file_id")
                return jsonify({'error': 'Martin服务缺少必要字段'}), 400
            
        else:
            # GeoServer服务验证（原有逻辑）
            current_app.logger.info(f"验证GeoServer图层: layer_id={layer_id}")
            
            layer_check = execute_query("SELECT * FROM geoserver_layers WHERE id = %s", (layer_id,))
            if not layer_check:
                current_app.logger.error(f"GeoServer图层不存在: layer_id={layer_id}")
                return jsonify({'error': f'图层ID {layer_id} 不存在'}), 400
            
            current_app.logger.info(f"GeoServer图层存在: {layer_check[0]['name']}")
        
        # 检查图层是否已经在场景中
        if service_type == 'martin':
            # 对于Martin服务，检查martin_service_id是否已存在
            existing_check = execute_query(
                "SELECT * FROM scene_layers WHERE scene_id = %s AND martin_service_id = %s", 
                (scene_id, martin_service_id)
            )
        else:
            # 对于GeoServer服务，检查layer_id是否已存在
            existing_check = execute_query(
                "SELECT * FROM scene_layers WHERE scene_id = %s AND layer_id = %s AND martin_service_id IS NULL", 
                (scene_id, layer_id)
            )
            
        if existing_check:
            current_app.logger.error(f"图层已存在于场景中: service_type={service_type}")
            return jsonify({'error': '图层已存在于该场景中'}), 400
        
        # 准备图层数据
        layer_data = {
            'scene_id': scene_id,
            'layer_id': layer_id,
            'layer_name': data.get('layer_name', f'图层_{layer_id}'),
            'layer_order': data.get('layer_order', 0),
            'visible': data.get('visible', True),
            'opacity': data.get('opacity', 1.0),
            'style_name': data.get('style_name'),
            'custom_style': data.get('custom_style'),
            'queryable': data.get('queryable', True),
            'selectable': data.get('selectable', True)
        }
        
        # 添加服务类型特定的字段
        if service_type == 'martin':
            layer_data.update({
                'service_type': 'martin',
                'martin_file_id': data.get('martin_file_id'),
                'martin_service_id': data.get('martin_service_id'),
                'layer_service_type': data.get('layer_service_type', 'geojson'),
                'mvt_url': data.get('mvt_url'),
                'tilejson_url': data.get('tilejson_url'),
                'file_id': data.get('file_id'),
                'file_type': data.get('file_type'),
                'discipline': data.get('discipline')
            })
        else:
            layer_data.update({
                'service_type': 'geoserver',
                'geoserver_layer_name': data.get('geoserver_layer_name'),
                'wms_url': data.get('wms_url'),
                'wfs_url': data.get('wfs_url'),
                'file_id': data.get('file_id'),
                'file_type': data.get('file_type'),
                'discipline': data.get('discipline')
            })
        
        current_app.logger.info(f"准备添加图层: {layer_data}")
        
        # 添加图层到场景
        scene_layer_id = scene_service.add_layer_to_scene(layer_data)
        
        current_app.logger.info(f"图层添加成功: scene_layer_id={scene_layer_id}")
        
        return jsonify({
            'id': scene_layer_id,
            'message': '图层添加成功'
        }), 200
    
    except Exception as e:
        import traceback
        error_msg = f"添加图层错误: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 返回更详细的错误信息（仅在调试模式下）
        if current_app.debug:
            return jsonify({
                'error': '服务器内部错误',
                'details': str(e),
                'traceback': traceback.format_exc()
            }), 500
        else:
            return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers/<layer_id>', methods=['PUT'])
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
        type: string
        required: true
        description: 图层ID（可以是正数或负数）
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            layer_order:
              type: integer
              description: 图层顺序
            visible:
              type: boolean
              description: 是否可见
            opacity:
              type: number
              description: 透明度 (0.0-1.0)
            style_name:
              type: string
              description: 样式名称
            custom_style:
              type: object
              description: 自定义样式配置
            queryable:
              type: boolean
              description: 是否可查询
            selectable:
              type: boolean
              description: 是否可选择
    responses:
      200:
        description: 图层更新成功
      404:
        description: 场景或图层不存在
    """
    try:
        # 转换layer_id为整数
        try:
            layer_id = int(layer_id)
        except ValueError:
            return jsonify({'error': '无效的图层ID'}), 400
        
        data = request.json
        
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return jsonify({'error': '场景不存在'}), 404
        
        # 检查场景图层是否存在
        from models.db import execute_query
        scene_layer_check = execute_query(
            "SELECT * FROM scene_layers WHERE scene_id = %s AND layer_id = %s", 
            (scene_id, layer_id)
        )
        if not scene_layer_check:
            return jsonify({'error': '场景中不存在该图层'}), 404
        
        # 准备更新数据
        update_data = {}
        allowed_fields = [
            'layer_order', 'visible', 'opacity', 'style_name', 
            'custom_style', 'queryable', 'selectable'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # 更新场景图层
        scene_service.update_scene_layer(scene_id, layer_id, update_data)
        
        return jsonify({
            'message': '图层更新成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"更新图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers/<layer_id>', methods=['DELETE'])
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
        type: string
        required: true
        description: 图层ID（可以是正数或负数）
    responses:
      200:
        description: 图层删除成功
      404:
        description: 场景或图层不存在
    """
    try:
        # 转换layer_id为整数
        try:
            layer_id = int(layer_id)
        except ValueError:
            return jsonify({'error': '无效的图层ID'}), 400
        
        current_app.logger.info(f"删除图层请求: scene_id={scene_id}, layer_id={layer_id}")
        
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            current_app.logger.error(f"场景不存在: scene_id={scene_id}")
            return jsonify({'error': '场景不存在'}), 404
        
        # 直接检查scene_layers表中是否存在该图层
        from models.db import execute_query
        scene_layer_check = execute_query(
            "SELECT * FROM scene_layers WHERE scene_id = %s AND layer_id = %s", 
            (scene_id, layer_id)
        )
        
        if not scene_layer_check:
            current_app.logger.error(f"场景中不存在该图层: scene_id={scene_id}, layer_id={layer_id}")
            return jsonify({'error': '场景中不存在该图层'}), 404
        
        current_app.logger.info(f"找到图层记录: {scene_layer_check[0]}")
        
        # 删除图层记录（直接从scene_layers表删除，不是从geoserver_layers删除）
        delete_sql = "DELETE FROM scene_layers WHERE scene_id = %s AND layer_id = %s"
        execute_query(delete_sql, (scene_id, layer_id))
        
        current_app.logger.info(f"图层删除成功: scene_id={scene_id}, layer_id={layer_id}")
        
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