#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models.db import execute_query

class SceneService:
    """场景服务类，用于管理场景和图层"""
    
    def create_scene(self, scene_data):
        """创建场景
        
        Args:
            scene_data: 场景数据
            
        Returns:
            场景ID
        """
        sql = """
        INSERT INTO scenes 
        (name, description, is_public, user_id)
        VALUES 
        (%(name)s, %(description)s, %(is_public)s, %(user_id)s)
        RETURNING id
        """
        
        result = execute_query(sql, scene_data)
        return result[0]['id']
    
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
        layer_sql = "DELETE FROM layers WHERE scene_id = %(scene_id)s"
        execute_query(layer_sql, {'scene_id': scene_id})
        
        # 删除场景
        sql = "DELETE FROM scenes WHERE id = %(scene_id)s"
        execute_query(sql, {'scene_id': scene_id})
        
        return True
    
    def get_scenes(self, user_id=None, public_only=False):
        """获取场景列表
        
        Args:
            user_id: 用户ID（可选，仅查询特定用户的场景）
            public_only: 是否只查询公共场景
            
        Returns:
            场景列表
        """
        sql = """
        SELECT s.*, u.username as creator,
               (SELECT COUNT(*) FROM layers l WHERE l.scene_id = s.id) as layer_count
        FROM scenes s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE 1=1
        """
        
        params = {}
        
        if user_id:
            sql += " AND (s.user_id = %(user_id)s"
            if public_only:
                sql += " OR s.is_public = true"
            sql += ")"
            params['user_id'] = user_id
        elif public_only:
            sql += " AND s.is_public = true"
        
        sql += " ORDER BY s.updated_at DESC"
        
        return execute_query(sql, params)
    
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
        
        return result[0]
    
    # 图层管理
    def add_layer(self, layer_data):
        """添加图层到场景
        
        Args:
            layer_data: 图层数据
            
        Returns:
            图层ID
        """
        # 获取当前最大的layer_order
        order_sql = """
        SELECT COALESCE(MAX(layer_order), 0) as max_order
        FROM layers
        WHERE scene_id = %(scene_id)s
        """
        
        order_result = execute_query(order_sql, {'scene_id': layer_data.get('scene_id')})
        layer_order = order_result[0]['max_order'] + 1 if order_result else 1
        
        # 插入新图层
        sql = """
        INSERT INTO layers
        (scene_id, file_id, layer_name, layer_order, visibility, style_config)
        VALUES
        (%(scene_id)s, %(file_id)s, %(layer_name)s, %(layer_order)s, %(visibility)s, %(style_config)s)
        RETURNING id
        """
        
        params = {
            'scene_id': layer_data.get('scene_id'),
            'file_id': layer_data.get('file_id'),
            'layer_name': layer_data.get('layer_name'),
            'layer_order': layer_order,
            'visibility': layer_data.get('visibility', True),
            'style_config': layer_data.get('style_config', '{}')
        }
        
        result = execute_query(sql, params)
        return result[0]['id']
    
    def update_layer(self, layer_id, layer_data):
        """更新图层
        
        Args:
            layer_id: 图层ID
            layer_data: 图层数据
            
        Returns:
            True 如果更新成功
        """
        sql = """
        UPDATE layers
        SET layer_name = %(layer_name)s,
            visibility = %(visibility)s,
            style_config = %(style_config)s
        WHERE id = %(layer_id)s
        """
        
        params = {
            'layer_id': layer_id,
            'layer_name': layer_data.get('layer_name'),
            'visibility': layer_data.get('visibility'),
            'style_config': layer_data.get('style_config')
        }
        
        execute_query(sql, params)
        return True
    
    def delete_layer(self, layer_id):
        """删除图层
        
        Args:
            layer_id: 图层ID
            
        Returns:
            True 如果删除成功
        """
        sql = "DELETE FROM layers WHERE id = %(layer_id)s"
        execute_query(sql, {'layer_id': layer_id})
        
        return True
    
    def get_layers_by_scene(self, scene_id):
        """获取场景的图层列表
        
        Args:
            scene_id: 场景ID
            
        Returns:
            图层列表
        """
        sql = """
        SELECT l.*, f.file_name, f.file_type, f.dimension, f.discipline, 
               f.geoserver_layer, f.wms_url, f.wfs_url
        FROM layers l
        LEFT JOIN files f ON l.file_id = f.id
        WHERE l.scene_id = %(scene_id)s
        ORDER BY l.layer_order
        """
        
        return execute_query(sql, {'scene_id': scene_id})
    
    def reorder_layers(self, scene_id, layer_order_map):
        """重新排序图层
        
        Args:
            scene_id: 场景ID
            layer_order_map: 图层ID到顺序的映射
            
        Returns:
            True 如果更新成功
        """
        for layer_id, order in layer_order_map.items():
            sql = """
            UPDATE layers
            SET layer_order = %(order)s
            WHERE id = %(layer_id)s AND scene_id = %(scene_id)s
            """
            
            params = {
                'layer_id': layer_id,
                'order': order,
                'scene_id': scene_id
            }
            
            execute_query(sql, params)
        
        return True