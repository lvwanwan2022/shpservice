#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models.db import execute_query, insert_with_snowflake_id
import json

class SceneService:
    """场景服务类，用于管理场景和图层"""
    
    def create_scene(self, scene_data):
        """创建场景
        
        Args:
            scene_data: 场景数据
            
        Returns:
            场景ID
        """
        return insert_with_snowflake_id('scenes', scene_data)
    
    def update_scene(self, scene_id, scene_data):
        """更新场景
        
        Args:
            scene_id: 场景ID
            scene_data: 场景数据
            
        Returns:
            True 如果更新成功
        """
        sql = """
        UPDATE scenes
        SET name = %(name)s,
            description = %(description)s,
            is_public = %(is_public)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %(scene_id)s
        """
        
        params = {
            'scene_id': scene_id,
            'name': scene_data.get('name'),
            'description': scene_data.get('description'),
            'is_public': scene_data.get('is_public')
        }
        
        execute_query(sql, params)
        return True
    
    def delete_scene(self, scene_id):
        """删除场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            True 如果删除成功
        """
        # 先删除场景相关的图层（由于外键CASCADE，此步骤可选）
        layer_sql = "DELETE FROM scene_layers WHERE scene_id = %(scene_id)s"
        execute_query(layer_sql, {'scene_id': scene_id})
        
        # 删除场景
        sql = "DELETE FROM scenes WHERE id = %(scene_id)s"
        execute_query(sql, {'scene_id': scene_id})
        
        return True
    
    def get_scenes(self, user_id=None, public_only=False):
        """获取场景列表
        
        Args:
            user_id: 用户ID（可选，优先显示该用户的场景，同时包含其他公开场景）
            public_only: 是否只查询公共场景
            
        Returns:
            场景列表
        """
        print(f"[DEBUG] get_scenes called with user_id={user_id}, public_only={public_only}")
        
        sql = """
        SELECT s.*, u.username as creator,
               (SELECT COUNT(*) FROM scene_layers sl WHERE sl.scene_id = s.id) as layer_count
        FROM scenes s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE 1=1
        """
        
        params = {}
        
        if public_only:
            # 只获取公开场景
            sql += " AND s.is_public = true"
            print("[DEBUG] 查询条件: 只获取公开场景")
        elif user_id:
            # 获取指定用户的所有场景（包括私有的）+ 其他用户的公开场景
            sql += " AND (s.user_id = %(user_id)s OR s.is_public = true)"
            params['user_id'] = user_id
            print(f"[DEBUG] 查询条件: 用户{user_id}的场景 + 其他公开场景")
        # 如果既没有user_id也没有public_only，则返回所有公开场景
        else:
            sql += " AND s.is_public = true"
            print("[DEBUG] 查询条件: 所有公开场景")
        
        # 排序：如果指定了用户ID，则该用户的场景排在前面
        if user_id and not public_only:
            sql += """
            ORDER BY 
                CASE WHEN s.user_id = %(user_id)s THEN 0 ELSE 1 END,
                s.updated_at DESC
            """
            print(f"[DEBUG] 排序: 用户{user_id}的场景优先")
        else:
            sql += " ORDER BY s.updated_at DESC"
            print("[DEBUG] 排序: 按更新时间降序")
        
        print(f"[DEBUG] 执行SQL: {sql}")
        print(f"[DEBUG] 参数: {params}")
        
        scenes = execute_query(sql, params)
        
        print(f"[DEBUG] 查询结果数量: {len(scenes)}")
        for scene in scenes:
            print(f"[DEBUG] 场景: ID={scene.get('id')}, 名称={scene.get('name')}, 公开={scene.get('is_public')}, 创建者={scene.get('creator')}")
        
        # 🔥 关键修复：将所有ID字段转换为字符串，避免JavaScript大整数精度丢失
        for scene in scenes:
            if scene.get('id'):
                scene['id'] = str(scene['id'])
            if scene.get('user_id'):
                scene['user_id'] = str(scene['user_id'])
        
        return scenes
    
    def get_scene_by_id(self, scene_id):
        """根据ID获取场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            场景信息
        """
        sql = """
        SELECT s.*, u.username as creator
        FROM scenes s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.id = %(scene_id)s
        """
        
        result = execute_query(sql, {'scene_id': scene_id})
        if not result:
            return None
        
        scene = result[0]
        
        # 🔥 关键修复：将所有ID字段转换为字符串，避免JavaScript大整数精度丢失
        if scene.get('id'):
            scene['id'] = str(scene['id'])
        if scene.get('user_id'):
            scene['user_id'] = str(scene['user_id'])
        
        return scene
    
    # 图层管理
    def add_layer_to_scene(self, layer_data):
        """添加图层到场景
        
        Args:
            layer_data: 图层数据，包含scene_id, layer_id等
            
        Returns:
            场景图层ID
        """
        # 获取当前最大的layer_order
        order_sql = """
        SELECT COALESCE(MAX(layer_order), 0) as max_order
        FROM scene_layers
        WHERE scene_id = %(scene_id)s
        """
        
        order_result = execute_query(order_sql, {'scene_id': layer_data.get('scene_id')})
        layer_order = layer_data.get('layer_order', order_result[0]['max_order'] + 1 if order_result else 1)
        
        # 处理custom_style
        custom_style = layer_data.get('custom_style')
        if custom_style and isinstance(custom_style, dict):
            custom_style_json = json.dumps(custom_style)
        else:
            custom_style_json = custom_style
        
        # 确定是否为Martin服务
        martin_service_id = layer_data.get('martin_service_id')
        martin_service_type = None
        service_type = layer_data.get('service_type', 'geoserver')
        
        # 如果是Martin服务但没有提供martin_service_id，尝试通过martin_file_id查找
        if service_type == 'martin' and not martin_service_id:
            martin_file_id = layer_data.get('martin_file_id')
            if martin_file_id:
                # 查询统一的Vector Martin服务表
                vector_martin_sql = """
                SELECT id, vector_type FROM vector_martin_services 
                WHERE file_id = %s AND status = 'active'
                """
                vector_result = execute_query(vector_martin_sql, (martin_file_id,))
                
                if vector_result:
                    martin_service_id = vector_result[0]['id']
                    martin_service_type = vector_result[0]['vector_type']
        elif service_type == 'martin' and martin_service_id:
            # 如果有martin_service_id，从layer_data中获取service_type信息
            # 前端应该传递服务类型信息
            layer_service_type = layer_data.get('layer_service_type')
            if layer_service_type and layer_service_type in ['geojson', 'shp']:
                martin_service_type = layer_service_type
            else:
                # 如果没有明确的服务类型，需要查询确定
                vector_check_sql = """
                SELECT vector_type FROM vector_martin_services 
                WHERE id = %s AND status = 'active'
                """
                vector_check = execute_query(vector_check_sql, (martin_service_id,))
                if vector_check:
                    martin_service_type = vector_check[0]['vector_type']
        
        # 准备图层数据
        layer_insert_data = {
            'scene_id': layer_data.get('scene_id'),
            'layer_id': layer_data.get('layer_id'),
            'martin_service_id': martin_service_id,
            'martin_service_type': martin_service_type,
            'layer_type': service_type,
            'layer_order': layer_order,
            'visible': layer_data.get('visible', True),
            'opacity': layer_data.get('opacity', 1.0),
            'style_name': layer_data.get('style_name'),
            'custom_style': custom_style_json,
            'queryable': layer_data.get('queryable', True),
            'selectable': layer_data.get('selectable', True),
            'service_reference': layer_data.get('service_reference'),
            'service_url': layer_data.get('service_url')
        }
        
        # 使用雪花算法生成ID并插入
        return insert_with_snowflake_id('scene_layers', layer_insert_data)
    
    def update_scene_layer(self, scene_id, layer_id, layer_data):
        """更新场景图层
        
        Args:
            scene_id: 场景ID
            layer_id: 图层ID
            layer_data: 图层数据
            
        Returns:
            True 如果更新成功
        """
        # 构建更新字段
        update_fields = []
        params = {'scene_id': scene_id, 'layer_id': layer_id}
        
        allowed_fields = [
            'layer_order', 'visible', 'opacity', 'style_name', 
            'custom_style', 'queryable', 'selectable'
        ]
        
        # 处理字段映射
        if 'style_config' in layer_data:
            # 将前端的style_config映射到数据库的custom_style字段
            layer_data['custom_style'] = layer_data.pop('style_config')
        
        if 'visibility' in layer_data:
            # 将前端的visibility映射到数据库的visible字段
            layer_data['visible'] = layer_data.pop('visibility')
        
        for field in allowed_fields:
            if field in layer_data:
                if field == 'custom_style' and isinstance(layer_data[field], dict):
                    update_fields.append(f"{field} = %({field})s")
                    params[field] = json.dumps(layer_data[field])
                else:
                    update_fields.append(f"{field} = %({field})s")
                    params[field] = layer_data[field]
        
        if not update_fields:
            return True
        
        sql = f"""
        UPDATE scene_layers
        SET {', '.join(update_fields)}
        WHERE scene_id = %(scene_id)s AND layer_id = %(layer_id)s
        """
        
        execute_query(sql, params)
        return True
    
    def delete_layer(self, layer_id):
        """从场景删除图层
        
        Args:
            layer_id: 图层ID
            
        Returns:
            True 如果删除成功
        """
        sql = "DELETE FROM scene_layers WHERE layer_id = %(layer_id)s"
        execute_query(sql, {'layer_id': layer_id})
        return True
    
    def get_layers_by_scene(self, scene_id):
        """获取场景的图层列表
        
        Args:
            scene_id: 场景ID
            
        Returns:
            图层列表
        """
        # 首先获取场景图层基本信息
        base_sql = """
        SELECT 
            sl.id as scene_layer_id,
            sl.layer_id,
            sl.martin_service_id,
            sl.martin_service_type,
            sl.layer_order,
            sl.visible as visibility,
            sl.opacity,
            sl.style_name,
            sl.custom_style as style_config,
            sl.queryable,
            sl.selectable,
            sl.created_at
        FROM scene_layers sl
        WHERE sl.scene_id = %(scene_id)s
        ORDER BY sl.layer_order ASC
        """
        
        scene_layers = execute_query(base_sql, {'scene_id': scene_id})
        
        # 处理每个图层，根据martin_service_id判断是Martin服务还是GeoServer服务
        result = []
        
        for layer in scene_layers:
            layer_id = layer['layer_id']
            martin_service_id = layer['martin_service_id']
            
            # 处理基本字段
            if 'visibility' in layer:
                layer['visibility'] = bool(layer['visibility'])
            
            if layer.get('style_config'):
                try:
                    if isinstance(layer['style_config'], str):
                        layer['style_config'] = json.loads(layer['style_config'])
                except (json.JSONDecodeError, TypeError):
                    layer['style_config'] = {}
            else:
                layer['style_config'] = {}
            
            # 判断是否为Martin服务
            if martin_service_id:
                martin_service_type = layer.get('martin_service_type')
                martin_result = None
                
                # 根据服务类型查询对应的表
                if martin_service_type == 'geojson':
                    martin_sql = """
                    SELECT 
                        'geojson' as service_type,
                        ms.id,
                        ms.file_id as martin_file_id,
                        ms.original_filename,
                        ms.table_name,
                        ms.mvt_url,
                        ms.tilejson_url,
                        ms.service_url,
                        ms.style,
                        ms.vector_info,
                        ms.status,
                        f.id as file_id,
                        f.file_type,
                        f.discipline
                    FROM vector_martin_services ms
                    LEFT JOIN files f ON ms.original_filename = f.file_name
                    WHERE ms.id = %(martin_service_id)s AND ms.status = 'active' AND ms.vector_type = 'geojson'
                    """
                    martin_result = execute_query(martin_sql, {'martin_service_id': martin_service_id})
                elif martin_service_type == 'shp':
                    martin_sql = """
                    SELECT 
                        'shp' as service_type,
                        ms.id,
                        ms.file_id as martin_file_id,
                        ms.original_filename,
                        ms.table_name,
                        ms.mvt_url,
                        ms.tilejson_url,
                        ms.service_url,
                        ms.style,
                        ms.vector_info,
                        ms.status,
                        f.id as file_id,
                        f.file_type,
                        f.discipline
                    FROM vector_martin_services ms
                    LEFT JOIN files f ON ms.original_filename = f.file_name
                    WHERE ms.id = %(martin_service_id)s AND ms.status = 'active' AND ms.vector_type = 'shp'
                    """
                    martin_result = execute_query(martin_sql, {'martin_service_id': martin_service_id})
                elif martin_service_type == 'dxf':
                    martin_sql = """
                    SELECT 
                        'dxf' as service_type,
                        ms.id,
                        ms.file_id as martin_file_id,
                        ms.original_filename,
                        ms.table_name,
                        ms.mvt_url,
                        ms.tilejson_url,
                        ms.service_url,
                        ms.style,
                        ms.vector_info,
                        ms.status,
                        f.id as file_id,
                        f.file_type,
                        f.discipline
                    FROM vector_martin_services ms
                    LEFT JOIN files f ON ms.original_filename = f.file_name
                    WHERE ms.id = %(martin_service_id)s AND ms.status = 'active' AND ms.vector_type = 'dxf'
                    """
                    martin_result = execute_query(martin_sql, {'martin_service_id': martin_service_id})
                else:
                    # 如果没有服务类型信息，查询统一表，根据ID获取
                    martin_sql = """
                    SELECT 
                        ms.vector_type as service_type,
                        ms.id,
                        ms.file_id as martin_file_id,
                        ms.original_filename,
                        ms.table_name,
                        ms.mvt_url,
                        ms.tilejson_url,
                        ms.service_url,
                        ms.style,
                        ms.status,
                        f.id as file_id,
                        f.file_type,
                        f.discipline
                    FROM vector_martin_services ms
                    LEFT JOIN files f ON ms.original_filename = f.file_name
                    WHERE ms.id = %(martin_service_id)s AND ms.status = 'active'
                    """
                    martin_result = execute_query(martin_sql, {'martin_service_id': martin_service_id})
                
                if martin_result:
                    martin_info = martin_result[0]
                    
                    # 解析Martin服务的样式配置
                    martin_style_config = {}
                    if martin_info.get('style'):
                        try:
                            if isinstance(martin_info['style'], str):
                                martin_style_config = json.loads(martin_info['style'])
                            else:
                                martin_style_config = martin_info['style']
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"解析Martin服务样式配置失败: {str(e)}")
                            martin_style_config = {}
                    
                    # 对于DXF类型，尝试从vector_info中读取样式配置
                    if martin_info.get('service_type') == 'dxf' and martin_info.get('vector_info'):
                        try:
                            vector_info = json.loads(martin_info['vector_info']) if isinstance(martin_info['vector_info'], str) else martin_info['vector_info']
                            dxf_style_config = vector_info.get('style_config', {})
                            if dxf_style_config:
                                martin_style_config = dxf_style_config
                                print(f"从vector_info读取DXF样式配置: {martin_style_config}")
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"解析DXF Martin服务vector_info失败: {str(e)}")
                    
                    # 构建Martin图层信息
                    layer.update({
                        'id': layer_id,  # 保持原有ID
                        'layer_name': martin_info['original_filename'],
                        'layer_name_only': martin_info['original_filename'],
                        'title': martin_info['original_filename'],
                        'abstract': f"Martin MVT瓦片服务 - {martin_info['original_filename']}",
                        'enabled': True,
                        'file_type': martin_info['file_type'],
                        'discipline': martin_info['discipline'],
                        'workspace_name': 'martin',
                        'geoserver_layer': None,
                        'wms_url': None,
                        'wfs_url': None,
                        'wcs_url': None,
                        # Martin服务特有字段
                        'service_type': 'martin',  # 统一设置为martin，不使用具体的子类型
                        'martin_service_subtype': martin_info['service_type'],  # 子类型单独存储
                        'martin_service_id': martin_service_id,
                        'martin_file_id': martin_info['martin_file_id'],
                        'martin_table_name': martin_info['table_name'],
                        'service_url': martin_info['service_url'],
                        'mvt_url': martin_info['mvt_url'],
                        'tilejson_url': martin_info['tilejson_url'],
                        'file_id': martin_info['file_id'],
                        # 样式配置
                        'style_config': martin_style_config
                    })
                else:
                    # Martin服务不存在
                    layer.update({
                        'id': layer_id,
                        'layer_name': f'Martin服务不存在 (ID: {martin_service_id})',
                        'layer_name_only': 'Martin服务不存在',
                        'title': 'Martin服务不存在',
                        'abstract': 'Martin服务已被删除',
                        'enabled': False,
                        'file_type': 'unknown',
                        'discipline': 'unknown',
                        'workspace_name': 'martin',
                        'service_type': 'martin',
                        'martin_service_subtype': 'unknown',
                        'martin_service_id': martin_service_id,
                        'geoserver_layer': None,
                        'wms_url': None,
                        'wfs_url': None,
                        'wcs_url': None
                    })
            
            else:
                # GeoServer服务处理（原有逻辑）
                geoserver_sql = """
                SELECT 
                    gl.id,
                    CONCAT(gw.name, ':', gl.name) as geoserver_layer,
                    gl.name as layer_name_only,
                    gl.title,
                    gl.abstract,
                    gl.enabled,
                    gl.wms_url,
                    gl.wfs_url,
                    gl.wcs_url,
                    gw.name as workspace_name,
                    f.file_name as layer_name,
                    f.file_type,
                    f.discipline
                FROM geoserver_layers gl
                LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
                LEFT JOIN files f ON gl.file_id = f.id
                WHERE gl.id = %(layer_id)s
                """
                
                geoserver_result = execute_query(geoserver_sql, {'layer_id': layer_id})
                
                if geoserver_result:
                    geoserver_info = geoserver_result[0]
                    layer.update(geoserver_info)
                    layer['service_type'] = 'geoserver'
                else:
                    # GeoServer图层不存在
                    layer.update({
                        'id': layer_id,
                        'layer_name': f'GeoServer图层不存在 (ID: {layer_id})',
                        'layer_name_only': 'GeoServer图层不存在',
                        'title': 'GeoServer图层不存在',
                        'abstract': 'GeoServer图层已被删除',
                        'enabled': False,
                        'file_type': 'unknown',
                        'discipline': 'unknown',
                        'workspace_name': 'unknown',
                        'service_type': 'geoserver',
                        'geoserver_layer': None,
                        'wms_url': None,
                        'wfs_url': None,
                        'wcs_url': None
                    })
            
            # 🔥 关键修复：将所有ID字段转换为字符串，避免JavaScript大整数精度丢失
            if layer.get('scene_layer_id'):
                layer['scene_layer_id'] = str(layer['scene_layer_id'])
            if layer.get('layer_id'):
                layer['layer_id'] = str(layer['layer_id'])
            if layer.get('martin_service_id'):
                layer['martin_service_id'] = str(layer['martin_service_id'])
            if layer.get('file_id'):
                layer['file_id'] = str(layer['file_id'])
            if layer.get('id'):
                layer['id'] = str(layer['id'])
            
            result.append(layer)
        
        return result
    
    def reorder_layers(self, scene_id, layer_order_map):
        """重新排序场景图层
        
        Args:
            scene_id: 场景ID
            layer_order_map: 图层ID到顺序的映射，例如：{"326586450273505300": 2, "326656740819079200": 1}
            
        Returns:
            True 如果更新成功
        """
        for layer_id, order in layer_order_map.items():
            # 🔥 确保layer_id转换为整数类型（对于数据库查询）
            try:
                layer_id_int = int(layer_id)
            except ValueError:
                print(f"警告：无效的layer_id格式: {layer_id}")
                continue
                
            sql = """
            UPDATE scene_layers
            SET layer_order = %(order)s
            WHERE scene_id = %(scene_id)s AND layer_id = %(layer_id)s
            """
            
            params = {
                'scene_id': scene_id,
                'layer_id': layer_id_int,  # 数据库中layer_id是BIGINT类型
                'order': order
            }
            
            print(f"更新图层顺序: scene_id={scene_id}, layer_id={layer_id_int}, order={order}")
            execute_query(sql, params)
        
        return True