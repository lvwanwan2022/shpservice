#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.scene_service import SceneService
from auth.auth_service import require_auth, get_current_user  # 🔥 添加认证导入

scene_bp = Blueprint('scene', __name__, url_prefix='/api/scenes')
scene_service = SceneService()

def verify_scene_permission(scene_id, operation="操作"):
    """
    验证用户对场景的操作权限
    
    Args:
        scene_id: 场景ID
        operation: 操作类型（用于日志记录）
        
    Returns:
        tuple: (success, scene, error_response)
        - success: 是否有权限
        - scene: 场景信息（如果存在）
        - error_response: 错误响应（如果有错误）
    """
    try:
        # 检查场景是否存在
        scene = scene_service.get_scene_by_id(scene_id)
        if not scene:
            return False, None, (jsonify({'error': '场景不存在'}), 404)
        
        # 获取当前用户
        current_user = get_current_user()
        from models.db import execute_query
        user_query = execute_query("SELECT id FROM users WHERE username = %s", (current_user.get('username'),))
        if not user_query:
            return False, None, (jsonify({'error': '用户不存在'}), 400)
        
        current_user_id = user_query[0]['id']
        scene_user_id = int(scene['user_id']) if isinstance(scene['user_id'], str) else scene['user_id']
        
        #current_app.logger.info(f"{operation}权限检查: 当前用户ID={current_user_id}, 场景创建者ID={scene_user_id}")
        
        if current_user_id != scene_user_id:
            current_app.logger.warning(f"用户 {current_user.get('username')} 尝试{operation}不属于自己的场景 {scene_id}")
            return False, scene, (jsonify({'error': f'权限不足：只有场景创建者可以{operation}场景'}), 403)
        
        return True, scene, None
        
    except Exception as e:
        current_app.logger.error(f"权限验证错误: {str(e)}")
        return False, None, (jsonify({'error': '服务器内部错误'}), 500)

@scene_bp.route('', methods=['POST'])
@require_auth  # 🔥 添加认证装饰器
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
        
        # 🔥 获取当前登录用户ID
        current_user = get_current_user()
        from models.db import execute_query
        user_query = execute_query("SELECT id FROM users WHERE username = %s", (current_user.get('username'),))
        if not user_query:
            return jsonify({'error': '用户不存在'}), 400
        user_id = user_query[0]['id']
        
        # 准备场景数据
        scene_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'is_public': data.get('is_public', True),
            'user_id': user_id  # 🔥 使用当前登录用户的真实ID
        }
        
        # 创建场景
        scene_id = scene_service.create_scene(scene_data)
        
        return jsonify({
            'id': str(scene_id),  # 🔥 转换为字符串避免JavaScript精度丢失
            'message': '场景创建成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"创建场景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>', methods=['PUT'])
@require_auth  # 🔥 添加认证装饰器
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
      403:
        description: 权限不足
      404:
        description: 场景不存在
    """
    try:
        data = request.json
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "编辑")
        if not has_permission:
            return error_response
        
        # 准备场景数据
        scene_data = {
            'name': data.get('name', scene['name']),
            'description': data.get('description', scene['description']),
            'is_public': data.get('is_public', scene['is_public'])
        }
        
        # 如果提供了bbox，也更新bbox
        if 'bbox' in data:
            scene_data['bbox'] = data.get('bbox')
        
        # 更新场景
        scene_service.update_scene(scene_id, scene_data)
        
        return jsonify({
            'message': '场景更新成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"更新场景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>', methods=['DELETE'])
@require_auth  # 🔥 添加认证装饰器
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
      403:
        description: 权限不足
      404:
        description: 场景不存在
    """
    try:
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "删除")
        if not has_permission:
            return error_response
        
        # 删除场景
        scene_service.delete_scene(scene_id)
        
        return jsonify({
            'message': '场景删除成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"删除场景错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/list', methods=['GET'])
@require_auth  # 🔥 添加认证装饰器
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
        description: 用户ID(指定时优先显示该用户场景，同时包含其他公开场景)
      - name: public_only
        in: query
        type: boolean
        required: false
        default: false
        description: 是否只获取公开场景
      - name: include_public
        in: query
        type: boolean
        required: false
        default: true
        description: 是否包含其他用户的公开场景
    responses:
      200:
        description: 场景列表
    """
    try:
        # 🔥 获取当前登录用户信息
        current_user = get_current_user()
        current_app.logger.info(f"当前用户: {current_user}")
        
        # 获取查询参数
        user_id = request.args.get('user_id')
        public_only = request.args.get('public_only', 'false').lower() == 'true'
        include_public = request.args.get('include_public', 'true').lower() == 'true'
        
        # 🔥 获取当前登录用户的ID（用于优先排序）
        current_user_id = None
        if current_user:
            from models.db import execute_query
            user_query = execute_query("SELECT id FROM users WHERE username = %s", (current_user.get('username'),))
            if user_query:
                current_user_id = user_query[0]['id']
                current_app.logger.info(f"当前登录用户ID: {current_user_id}")
        
        # 如果没有指定user_id，且不是只获取公开场景，则使用当前用户ID
        if not user_id and not public_only and current_user_id:
            user_id = current_user_id
            current_app.logger.info(f"使用当前用户ID: {user_id}")
        
        if user_id:
            user_id = int(user_id)
        
        # 获取场景列表
        scenes = scene_service.get_scenes(user_id, public_only)
        current_app.logger.info(f"查询到场景数量: {len(scenes)}")
        
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
@require_auth  # 🔥 添加认证装饰器
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
      403:
        description: 权限不足
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
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "添加图层")
        if not has_permission:
            return error_response
        
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
            # Martin服务验证 - 使用统一的vector_martin_services表
            current_app.logger.info(f"验证Martin服务图层: layer_id={layer_id}")
            
            # 检查必要的Martin服务字段
            martin_file_id = data.get('martin_file_id')
            martin_service_id = data.get('martin_service_id')
            
            # 优先使用martin_service_id，如果没有则通过martin_file_id查找
            if martin_service_id:
                # 查询统一的vector_martin_services表
                martin_check = execute_query(
                    "SELECT * FROM vector_martin_services WHERE id = %s AND status = 'active'", 
                    (martin_service_id,)
                )
                
                if not martin_check:
                    current_app.logger.error(f"Martin服务不存在: martin_service_id={martin_service_id}")
                    return jsonify({'error': f'Martin服务不存在'}), 400
                
                current_app.logger.info(f"Martin服务存在: {martin_check[0]['table_name']}, vector_type={martin_check[0]['vector_type']}")
                
            elif martin_file_id:
                # 通过file_id查询统一的vector_martin_services表
                martin_check = execute_query(
                    "SELECT * FROM vector_martin_services WHERE file_id = %s AND status = 'active'", 
                    (martin_file_id,)
                )
                
                if not martin_check:
                    current_app.logger.error(f"Martin服务不存在: file_id={martin_file_id}")
                    return jsonify({'error': f'Martin服务不存在'}), 400
                
                # 获取martin_service_id
                martin_service_id = martin_check[0]['id']
                current_app.logger.info(f"Martin服务存在: {martin_check[0]['table_name']}, vector_type={martin_check[0]['vector_type']}")
                
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
            # 从martin_check结果中获取vector_type
            layer_service_type = 'geojson'  # 默认值
            if martin_service_id and 'martin_check' in locals() and martin_check:
                layer_service_type = martin_check[0]['vector_type']
            else:
                # 如果没有martin_check，从传入数据中获取
                layer_service_type = data.get('layer_service_type', 'geojson')
                
            layer_data.update({
                'service_type': 'martin',
                'martin_file_id': data.get('martin_file_id'),
                'martin_service_id': martin_service_id,
                'layer_service_type': layer_service_type,
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
            'id': str(scene_layer_id),  # 🔥 转换为字符串避免JavaScript精度丢失
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
@require_auth  # 🔥 添加认证装饰器
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
        description: 图层ID
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
      403:
        description: 权限不足
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
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "更新图层")
        if not has_permission:
            return error_response
        
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
@require_auth  # 🔥 添加认证装饰器
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
      403:
        description: 权限不足
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
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "删除图层")
        if not has_permission:
            return error_response
        
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
@require_auth  # 🔥 添加认证装饰器
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
        #current_app.logger.info(f"重新排序图层请求: scene_id={scene_id}, data={data}")
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "重新排序图层")
        if not has_permission:
            return error_response
        
        # 验证必填字段
        if not data.get('layer_order'):
            current_app.logger.error(f"缺少必填字段: layer_order, 接收到的数据: {data}")
            return jsonify({'error': '缺少必填字段: layer_order'}), 400
        
        # 验证layer_order格式
        layer_order = data.get('layer_order')
        if not isinstance(layer_order, dict):
            return jsonify({'error': 'layer_order必须是对象'}), 400
        
        # 🔥 保持layer_id为字符串，避免大整数精度丢失
        layer_order_map = {}
        for layer_id, order in layer_order.items():
            # 保持layer_id为字符串，但确保order为整数
            layer_order_map[str(layer_id)] = int(order)
        
        # 重新排序图层
        scene_service.reorder_layers(scene_id, layer_order_map)
        
        return jsonify({
            'message': '图层重新排序成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"重新排序图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/layers/<int:layer_id>/order', methods=['PUT'])
@require_auth
def update_layer_order(scene_id, layer_id):
    """更新单个图层的顺序
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
            layer_order:
              type: integer
              description: 新的图层顺序
    responses:
      200:
        description: 图层顺序更新成功
      400:
        description: 参数错误
      403:
        description: 权限不足
      404:
        description: 场景或图层不存在
    """
    try:
        data = request.json
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "更新图层顺序")
        if not has_permission:
            return error_response
        
        # 验证必填字段
        if 'layer_order' not in data:
            return jsonify({'error': '缺少必填字段: layer_order'}), 400
        
        new_order = data['layer_order']
        if not isinstance(new_order, int):
            return jsonify({'error': 'layer_order必须是整数'}), 400
        
        # 检查场景图层是否存在
        from models.db import execute_query
        scene_layer_check = execute_query(
            "SELECT * FROM scene_layers WHERE scene_id = %s AND layer_id = %s", 
            (scene_id, layer_id)
        )
        if not scene_layer_check:
            return jsonify({'error': '场景中不存在该图层'}), 404
        
        # 更新图层顺序
        scene_service.update_scene_layer(scene_id, layer_id, {'layer_order': new_order})
        
        return jsonify({
            'message': '图层顺序更新成功',
            'layer_id': layer_id,
            'new_order': new_order
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"更新图层顺序错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@scene_bp.route('/<int:scene_id>/bbox', methods=['PUT'])
@require_auth  # 🔥 添加认证装饰器
def update_scene_bbox(scene_id):
    """设置场景范围
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
            - bbox
          properties:
            bbox:
              type: array
              items:
                type: number
              minItems: 4
              maxItems: 4
              description: 边界框，格式为 [minx, miny, maxx, maxy] 或 {minx, miny, maxx, maxy}
    responses:
      200:
        description: 场景范围设置成功
      400:
        description: 参数错误
      403:
        description: 权限不足
      404:
        description: 场景不存在
    """
    try:
        data = request.json
        
        # 验证必填字段
        if 'bbox' not in data:
            return jsonify({'error': '缺少必填字段: bbox'}), 400
        
        bbox = data.get('bbox')
        
        # 🔥 使用统一权限验证函数
        has_permission, scene, error_response = verify_scene_permission(scene_id, "设置场景范围")
        if not has_permission:
            return error_response
        
        # 更新场景范围
        scene_service.update_scene_bbox(scene_id, bbox)
        
        return jsonify({
            'message': '场景范围设置成功'
        }), 200
    
    except ValueError as e:
        current_app.logger.error(f"设置场景范围错误: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"设置场景范围错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500 