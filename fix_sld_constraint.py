#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复SLD数据库表约束问题
"""

import sys
import os
sys.path.append('backend')

from models.db import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_sld_constraint():
    """修复SLD数据库表约束"""
    try:
        logger.info("开始修复SLD数据库表约束...")
        
        # 1. 删除现有的layer_sld_mapping表
        logger.info("删除现有的layer_sld_mapping表...")
        execute_query("DROP TABLE IF EXISTS layer_sld_mapping CASCADE", fetch=False)
        
        # 2. 重新创建layer_sld_mapping表，修改唯一约束
        logger.info("重新创建layer_sld_mapping表...")
        create_mapping_table_query = """
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
        execute_query(create_mapping_table_query, fetch=False)
        
        # 3. 重新创建触发器
        logger.info("创建updated_at触发器...")
        
        # 创建触发器函数（如果不存在）
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
        
        # 为layer_sld_mapping表创建触发器
        trigger = """
        DROP TRIGGER IF EXISTS update_layer_sld_mapping_updated_at ON layer_sld_mapping;
        CREATE TRIGGER update_layer_sld_mapping_updated_at
            BEFORE UPDATE ON layer_sld_mapping
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        execute_query(trigger, fetch=False)
        
        logger.info("✅ SLD数据库表约束修复成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 修复SLD数据库表约束失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("SLD数据库表约束修复工具")
    print("=" * 50)
    
    success = fix_sld_constraint()
    
    if success:
        print("\n✅ 修复完成！")
        print("现在每个图层只能有一个SLD样式映射（通过DELETE/INSERT模式）")
    else:
        print("\n❌ 修复失败！")
        sys.exit(1)
