#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户服务连接数据库模型 - 简化版
只管理用户的外部Geoserver和Martin服务连接信息
"""

from models.db import execute_query
from utils.snowflake import get_snowflake_id
import json

def init_user_service_tables():
    """初始化用户服务连接相关表"""
    try:
        print("开始创建用户服务连接管理表...")
        
        # 1. 创建用户服务连接配置表
        create_connections_table = """
        CREATE TABLE IF NOT EXISTS user_service_connections (
            id BIGINT PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            service_name VARCHAR(100) NOT NULL,
            service_type VARCHAR(20) NOT NULL CHECK (service_type IN ('geoserver', 'martin')),
            server_url VARCHAR(500) NOT NULL,
            connection_config JSONB NOT NULL,
            description TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            last_tested_at TIMESTAMP,
            test_status VARCHAR(20) DEFAULT 'unknown',
            test_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, service_name, service_type)
        )
        """
        
        execute_query(create_connections_table, fetch=False)
        print("✅ 用户服务连接表创建成功")
        
        # 2. 添加表注释
        add_comments = """
        COMMENT ON TABLE user_service_connections IS '用户服务连接配置表 - 存储用户外部Geoserver和Martin服务连接信息';
        COMMENT ON COLUMN user_service_connections.service_type IS '服务类型: geoserver 或 martin';
        COMMENT ON COLUMN user_service_connections.server_url IS '外部服务的完整访问地址';
        COMMENT ON COLUMN user_service_connections.connection_config IS '连接配置(JSON格式，包含认证信息等)';
        COMMENT ON COLUMN user_service_connections.is_default IS '是否为该类型服务的默认连接';
        COMMENT ON COLUMN user_service_connections.test_status IS '最后一次连接测试状态: success, failed, unknown';
        """
        
        execute_query(add_comments, fetch=False)
        print("✅ 表注释添加成功")
        
        # 3. 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type ON user_service_connections(service_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_active ON user_service_connections(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, service_type, is_default) WHERE is_default = TRUE"
        ]
        
        for index_sql in indexes:
            execute_query(index_sql, fetch=False)
        
        print("✅ 索引创建成功")
        
        # 4. 创建触发器函数
        # 更新时间戳触发器
        update_timestamp_trigger = """
        CREATE OR REPLACE FUNCTION update_connection_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_user_service_connections_updated_at ON user_service_connections;
        CREATE TRIGGER update_user_service_connections_updated_at 
            BEFORE UPDATE ON user_service_connections 
            FOR EACH ROW EXECUTE FUNCTION update_connection_updated_at();
        """
        
        execute_query(update_timestamp_trigger, fetch=False)
        print("✅ 更新时间戳触发器创建成功")
        
        # 确保默认连接唯一性的触发器
        default_unique_trigger = """
        CREATE OR REPLACE FUNCTION ensure_single_default_connection()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.is_default = TRUE THEN
                UPDATE user_service_connections 
                SET is_default = FALSE 
                WHERE user_id = NEW.user_id 
                AND service_type = NEW.service_type 
                AND id != NEW.id
                AND is_default = TRUE;
            END IF;
            
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS ensure_single_default_connection_trigger ON user_service_connections;
        CREATE TRIGGER ensure_single_default_connection_trigger
            BEFORE INSERT OR UPDATE ON user_service_connections
            FOR EACH ROW EXECUTE FUNCTION ensure_single_default_connection();
        """
        
        execute_query(default_unique_trigger, fetch=False)
        print("✅ 默认连接唯一性触发器创建成功")
        
        print("🎉 用户服务连接管理表初始化完成！")
        return True
        
    except Exception as e:
        print(f"❌ 用户服务连接表初始化失败: {e}")
        return False

def cleanup_old_service_tables():
    """清理旧的服务管理表"""
    try:
        print("开始清理旧的服务管理表...")
        
        # 删除不需要的表
        tables_to_drop = [
            'service_logs',
            'system_resource_quotas', 
            'service_port_allocations',
            'user_service_configs'
        ]
        
        for table in tables_to_drop:
            try:
                drop_sql = f"DROP TABLE IF EXISTS {table} CASCADE"
                execute_query(drop_sql, fetch=False)
                print(f"✅ 删除表 {table}")
            except Exception as e:
                print(f"⚠️ 删除表 {table} 失败: {e}")
        
        # 删除相关函数
        functions_to_drop = [
            'allocate_available_port(BIGINT, BIGINT)',
            'release_port(INTEGER)',
            'log_service_status_change()',
            'check_user_service_limit()',
            'update_updated_at_column()',
            'update_vote_counts()',
            'update_comment_count()',
            'update_attachments_flag()'
        ]
        
        for func in functions_to_drop:
            try:
                drop_func_sql = f"DROP FUNCTION IF EXISTS {func}"
                execute_query(drop_func_sql, fetch=False)
                print(f"✅ 删除函数 {func}")
            except Exception as e:
                print(f"⚠️ 删除函数 {func} 失败: {e}")
        
        print("✅ 旧表清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 清理旧表失败: {e}")
        return False

# 数据操作函数
def get_user_connections(user_id, service_type=None, is_active=True):
    """获取用户的服务连接列表"""
    try:
        where_conditions = ['user_id = %s']
        params = [user_id]
        
        if service_type:
            where_conditions.append('service_type = %s')
            params.append(service_type)
            
        if is_active is not None:
            where_conditions.append('is_active = %s')
            params.append(is_active)
        
        where_clause = ' AND '.join(where_conditions)
        
        query = f"""
        SELECT * FROM user_service_connections 
        WHERE {where_clause}
        ORDER BY created_at DESC
        """
        
        return execute_query(query, params)
        
    except Exception as e:
        print(f"获取用户连接失败: {e}")
        return []

def create_service_connection(user_id, service_name, service_type, server_url, connection_config, description=None, is_default=False):
    """创建服务连接"""
    try:
        connection_id = get_snowflake_id()
        
        insert_sql = """
        INSERT INTO user_service_connections (
            id, user_id, service_name, service_type, server_url,
            connection_config, description, is_default
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """
        
        result = execute_query(insert_sql, (
            connection_id, user_id, service_name, service_type, server_url,
            json.dumps(connection_config), description, is_default
        ))
        
        return result[0] if result else None
        
    except Exception as e:
        print(f"创建服务连接失败: {e}")
        return None

def update_connection_test_result(connection_id, test_status, test_message=None):
    """更新连接测试结果"""
    try:
        update_sql = """
        UPDATE user_service_connections 
        SET test_status = %s, test_message = %s, last_tested_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        execute_query(update_sql, (test_status, test_message, connection_id), fetch=False)
        return True
        
    except Exception as e:
        print(f"更新测试结果失败: {e}")
        return False

def get_default_connection(user_id, service_type):
    """获取用户指定类型的默认连接"""
    try:
        query = """
        SELECT * FROM user_service_connections 
        WHERE user_id = %s AND service_type = %s AND is_default = TRUE AND is_active = TRUE
        LIMIT 1
        """
        
        result = execute_query(query, [user_id, service_type])
        return result[0] if result else None
        
    except Exception as e:
        print(f"获取默认连接失败: {e}")
        return None

if __name__ == "__main__":
    print("🚀 开始初始化用户服务连接管理系统")
    
    # 清理旧表
    cleanup_old_service_tables()
    
    # 初始化新表
    if init_user_service_tables():
        print("🎉 用户服务连接管理系统初始化成功！")
    else:
        print("❌ 初始化失败") 