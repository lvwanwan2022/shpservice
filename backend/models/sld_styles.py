#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SLD样式文件管理数据库模型
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from models.db import get_connection, execute_query
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class SLDStyleModel:
    """SLD样式文件数据模型"""
    
    @staticmethod
    def create_sld_styles_table():
        """创建SLD样式文件表"""
        query = """
        CREATE TABLE IF NOT EXISTS sld_styles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            geometry_type VARCHAR(50) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            content TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE(name, geometry_type)
        );
        """
        try:
            execute_query(query, fetch=False)
            
            # 创建触发器函数
            trigger_function = """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            """
            execute_query(trigger_function, fetch=False)
            
            # 创建触发器
            trigger = """
            DROP TRIGGER IF EXISTS update_sld_styles_updated_at ON sld_styles;
            CREATE TRIGGER update_sld_styles_updated_at
                BEFORE UPDATE ON sld_styles
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """
            execute_query(trigger, fetch=False)
            
            logger.info("SLD样式文件表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建SLD样式文件表失败: {str(e)}")
            return False
    
    @staticmethod
    def create_layer_sld_mapping_table():
        """创建图层SLD样式映射表"""
        query = """
        CREATE TABLE IF NOT EXISTS layer_sld_mapping (
            id SERIAL PRIMARY KEY,
            layer_id BIGINT NOT NULL,
            sld_style_id INTEGER NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_by INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(layer_id),
            FOREIGN KEY (layer_id) REFERENCES geoserver_layers(id) ON DELETE CASCADE,
            FOREIGN KEY (sld_style_id) REFERENCES sld_styles(id) ON DELETE CASCADE
        );
        """
        try:
            execute_query(query, fetch=False)
            
            # 创建触发器
            trigger = """
            DROP TRIGGER IF EXISTS update_layer_sld_mapping_updated_at ON layer_sld_mapping;
            CREATE TRIGGER update_layer_sld_mapping_updated_at
                BEFORE UPDATE ON layer_sld_mapping
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """
            execute_query(trigger, fetch=False)
            
            logger.info("图层SLD样式映射表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建图层SLD样式映射表失败: {str(e)}")
            return False
    
    @staticmethod
    def insert_sld_style(name, description, geometry_type, file_path, file_size, content, created_by=None):
        """插入SLD样式文件记录"""
        query = """
        INSERT INTO sld_styles (name, description, geometry_type, file_path, file_size, content, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, name, description, geometry_type, file_path, file_size, created_at
        """
        try:
            result = execute_query(query, (name, description, geometry_type, file_path, file_size, content, created_by))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"插入SLD样式文件失败: {str(e)}")
            raise
    
    @staticmethod
    def get_sld_styles(geometry_type=None, is_active=True, page=1, page_size=20):
        """获取SLD样式文件列表"""
        where_conditions = ["is_active = %s"]
        params = [is_active]
        
        if geometry_type:
            where_conditions.append("geometry_type = %s")
            params.append(geometry_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) as total FROM sld_styles WHERE {where_clause}"
        count_result = execute_query(count_query, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 获取分页数据
        offset = (page - 1) * page_size
        query = f"""
        SELECT id, name, description, geometry_type, file_path, file_size, created_at, updated_at
        FROM sld_styles 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        try:
            result = execute_query(query, params)
            return result, total
        except Exception as e:
            logger.error(f"获取SLD样式文件列表失败: {str(e)}")
            raise
    
    @staticmethod
    def get_sld_style_by_id(style_id):
        """根据ID获取SLD样式文件"""
        query = """
        SELECT id, name, description, geometry_type, file_path, file_size, content, created_at, updated_at
        FROM sld_styles 
        WHERE id = %s AND is_active = TRUE
        """
        try:
            result = execute_query(query, (style_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"获取SLD样式文件失败: {str(e)}")
            raise
    
    @staticmethod
    def update_sld_style(style_id, update_data):
        """更新SLD样式文件"""
        update_fields = []
        params = []
        
        # 支持所有字段的更新
        field_mapping = {
            'name': 'name',
            'description': 'description',
            'geometry_type': 'geometry_type',
            'content': 'content',
            'updated_at': 'updated_at'
        }
        
        for key, value in update_data.items():
            if key in field_mapping and value is not None:
                update_fields.append(f"{field_mapping[key]} = %s")
                params.append(value)
        
        if not update_fields:
            return False
        
        params.append(style_id)
        
        query = f"""
        UPDATE sld_styles 
        SET {', '.join(update_fields)}
        WHERE id = %s AND is_active = TRUE
        RETURNING id, name, description, geometry_type, file_path, file_size, updated_at
        """
        
        try:
            result = execute_query(query, params)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"更新SLD样式文件失败: {str(e)}")
            raise
    
    @staticmethod
    def delete_sld_style(style_id):
        """删除SLD样式文件（软删除）"""
        query = """
        UPDATE sld_styles 
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id
        """
        try:
            result = execute_query(query, (style_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"删除SLD样式文件失败: {str(e)}")
            raise
    
    @staticmethod
    def apply_sld_style_to_layer(layer_id, sld_style_id, applied_by=None):
        """将SLD样式应用到图层"""
        # 先删除该图层的其他样式映射
        delete_query = """
        DELETE FROM layer_sld_mapping 
        WHERE layer_id = %s
        """
        
        # 插入新的映射关系
        insert_query = """
        INSERT INTO layer_sld_mapping (layer_id, sld_style_id, applied_by)
        VALUES (%s, %s, %s)
        RETURNING id, layer_id, sld_style_id, applied_at
        """
        
        try:
            # 删除旧样式映射
            execute_query(delete_query, (layer_id,), fetch=False)
            
            # 应用新样式
            result = execute_query(insert_query, (layer_id, sld_style_id, applied_by))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"应用SLD样式到图层失败: {str(e)}")
            raise
    
    @staticmethod
    def get_layer_sld_style(layer_id):
        """获取图层的当前SLD样式"""
        query = """
        SELECT lsm.id, lsm.layer_id, lsm.sld_style_id, lsm.applied_at, lsm.applied_by,
               ss.name, ss.description, ss.geometry_type, ss.file_path, ss.content
        FROM layer_sld_mapping lsm
        JOIN sld_styles ss ON lsm.sld_style_id = ss.id
        WHERE lsm.layer_id = %s AND lsm.is_active = TRUE AND ss.is_active = TRUE
        """
        try:
            result = execute_query(query, (layer_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"获取图层SLD样式失败: {str(e)}")
            raise
    
    @staticmethod
    def remove_layer_sld_style(layer_id):
        """移除图层的SLD样式"""
        query = """
        DELETE FROM layer_sld_mapping 
        WHERE layer_id = %s
        RETURNING id
        """
        try:
            result = execute_query(query, (layer_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"移除图层SLD样式失败: {str(e)}")
            raise
