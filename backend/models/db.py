#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接和操作模块
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG
import time
import json
import os

def get_connection():
    """获取数据库连接"""
    try:
        # 使用明确的参数连接，避免编码问题
        # 设置环境变量强制使用英文错误信息
        os.environ['LC_ALL'] = 'C'
        os.environ['LANG'] = 'C'
        
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            client_encoding='utf8'
        )
        # 设置会话编码
        conn.set_client_encoding('UTF8')
        return conn
    except psycopg2.OperationalError as e:
        # 处理编码问题 - 尝试解析GB2312编码的错误信息
        error_msg = str(e)
        try:
            # 如果原始错误包含字节信息，尝试解码
            if hasattr(e, 'args') and len(e.args) > 1:
                error_bytes = e.args[1]
                if isinstance(error_bytes, bytes):
                    try:
                        decoded_msg = error_bytes.decode('gb2312', errors='ignore')
                        error_msg = f"数据库连接失败 - 连接错误: {decoded_msg}"
                    except:
                        error_msg = f"数据库连接失败 - 连接错误: {error_msg}"
        except:
            pass
        
        print(error_msg)
        raise Exception(error_msg)
    except psycopg2.DatabaseError as e:
        error_msg = f"数据库连接失败 - 数据库错误: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    except UnicodeDecodeError as e:
        error_msg = f"数据库连接失败 - 编码错误: PostgreSQL服务器返回了非UTF-8编码的错误信息，可能是中文Windows系统的编码问题"
        print(error_msg)
        print("💡 建议:")
        print("   - 检查PostgreSQL配置文件中的语言设置")
        print("   - 确保PostgreSQL使用UTF-8编码")
        print("   - 检查用户名和密码是否正确")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"数据库连接失败 - 未知错误: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def execute_query(query, params=None, fetch=True):
    """执行SQL查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否获取结果
        
    Returns:
        查询结果列表（如果fetch=True）
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            # 检查是否是修改操作（INSERT/UPDATE/DELETE）
            query_type = query.strip().upper().split()[0]
            is_modify_operation = query_type in ('INSERT', 'UPDATE', 'DELETE')
            
            # 检查是否有RETURNING子句
            has_returning = 'RETURNING' in query.upper()
            
            if fetch and (not is_modify_operation or has_returning):
                # 只有在非修改操作或有RETURNING子句时才获取结果
                result = cursor.fetchall()
                # 如果是修改操作，提交事务
                if is_modify_operation:
                    conn.commit()
                
                # 转换结果为字典列表
                dict_result = []
                for row in result:
                    # 将 RealDictRow 转换为普通字典
                    row_dict = dict(row)
                    # 特殊处理JSON字段
                    for key, value in row_dict.items():
                        if isinstance(value, (dict, list)):
                            row_dict[key] = value
                    dict_result.append(row_dict)
                return dict_result
            else:
                # 对于修改操作（不带RETURNING）或不需要获取结果的操作，直接提交
                if is_modify_operation:
                    conn.commit()
                    # 返回受影响的行数
                    return cursor.rowcount
                else:
                    conn.commit()
                return None
                
    except psycopg2.OperationalError as e:
        if conn:
            conn.rollback()
        error_msg = f"执行查询失败 - 连接错误: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        error_msg = f"执行查询失败 - 数据库错误: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        if conn:
            conn.rollback()
        error_msg = f"执行查询失败 - 未知错误: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
    finally:
        if conn:
            conn.close()

def execute_transaction(queries):
    """执行多个SQL查询作为单个事务
    
    Args:
        queries: (query, params)元组列表
        
    Returns:
        最后一个查询的结果（如果有）
    """
    conn = None
    result = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            for query, params in queries:
                cursor.execute(query, params)
                
                # 如果是SELECT查询，获取结果
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
            
            conn.commit()
            
            # 转换结果为字典列表
            if result:
                dict_result = []
                for row in result:
                    dict_result.append(dict(row))
                return dict_result
            return None
                
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"执行事务失败: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def execute_batch(query, params_list):
    """批量执行SQL查询
    
    Args:
        query: SQL查询语句
        params_list: 参数列表
        
    Returns:
        None
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            for params in params_list:
                cursor.execute(query, params)
            conn.commit()
                
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"批量执行查询失败: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def check_table_exists(table_name):
    """检查表是否存在
    
    Args:
        table_name: 表名
        
    Returns:
        布尔值，表示表是否存在
    """
    query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name = %s
    )
    """
    
    result = execute_query(query, (table_name,))
    return result[0]['exists'] if result else False

def init_database():
    """初始化数据库表"""
    try:
        # 创建用户表
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建文件表 - 更新以匹配新的数据库结构
        create_files_table = """
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(100) NOT NULL,
            file_path VARCHAR(200) NOT NULL,
            original_name VARCHAR(100) NOT NULL,
            file_size BIGINT NOT NULL,
            is_public BOOLEAN DEFAULT TRUE,
            discipline VARCHAR(50) NOT NULL,
            dimension VARCHAR(10) NOT NULL,
            file_type VARCHAR(20) NOT NULL,
            coordinate_system VARCHAR(20),
            tags VARCHAR(200),
            description TEXT,
            user_id INTEGER REFERENCES users(id),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'uploaded',
            bbox JSONB,
            geometry_type VARCHAR(50),
            feature_count INTEGER,
            metadata JSONB
        )
        """
        
        # 创建GeoServer工作空间表
        create_geoserver_workspaces_table = """
        CREATE TABLE IF NOT EXISTS geoserver_workspaces (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            namespace_uri VARCHAR(255),
            namespace_prefix VARCHAR(100),
            description TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建GeoServer存储仓库表
        create_geoserver_stores_table = """
        CREATE TABLE IF NOT EXISTS geoserver_stores (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id INTEGER REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
            store_type VARCHAR(50) NOT NULL,
            data_type VARCHAR(50),
            connection_params JSONB,
            description TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            file_id INTEGER REFERENCES files(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, name)
        )
        """
        
        # 创建GeoServer要素类型表
        create_geoserver_featuretypes_table = """
        CREATE TABLE IF NOT EXISTS geoserver_featuretypes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            native_name VARCHAR(100),
            store_id INTEGER REFERENCES geoserver_stores(id) ON DELETE CASCADE,
            title VARCHAR(255),
            abstract TEXT,
            keywords TEXT[],
            srs VARCHAR(50),
            projection_policy VARCHAR(50) DEFAULT 'REPROJECT_TO_DECLARED',
            native_bbox JSONB,
            lat_lon_bbox JSONB,
            attributes JSONB,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_id, name)
        )
        """
        
        # 创建GeoServer覆盖范围表
        create_geoserver_coverages_table = """
        CREATE TABLE IF NOT EXISTS geoserver_coverages (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            native_name VARCHAR(100),
            store_id INTEGER REFERENCES geoserver_stores(id) ON DELETE CASCADE,
            title VARCHAR(255),
            abstract TEXT,
            keywords TEXT[],
            srs VARCHAR(50) DEFAULT 'EPSG:4326',
            native_srs VARCHAR(50),
            native_bbox JSONB,
            lat_lon_bbox JSONB,
            grid_info JSONB,
            bands_info JSONB,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_id, name)
        )
        """
        
        # 创建GeoServer图层表 - 更新以支持矢量和栅格数据
        create_geoserver_layers_table = """
        CREATE TABLE IF NOT EXISTS geoserver_layers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id INTEGER REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
            featuretype_id INTEGER REFERENCES geoserver_featuretypes(id) ON DELETE CASCADE,
            coverage_id INTEGER REFERENCES geoserver_coverages(id) ON DELETE CASCADE,
            title VARCHAR(255),
            abstract TEXT,
            default_style VARCHAR(100),
            additional_styles TEXT[],
            enabled BOOLEAN DEFAULT TRUE,
            queryable BOOLEAN DEFAULT TRUE,
            opaque BOOLEAN DEFAULT FALSE,
            attribution TEXT,
            wms_url TEXT,
            wfs_url TEXT,
            wcs_url TEXT,
            file_id INTEGER REFERENCES files(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, name),
            CONSTRAINT check_data_source CHECK (
                (featuretype_id IS NOT NULL AND coverage_id IS NULL) OR 
                (featuretype_id IS NULL AND coverage_id IS NOT NULL)
            )
        )
        """
        
        # 创建GeoServer样式表
        create_geoserver_styles_table = """
        CREATE TABLE IF NOT EXISTS geoserver_styles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id INTEGER REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
            filename VARCHAR(255),
            format VARCHAR(50) DEFAULT 'sld',
            language_version VARCHAR(20),
            content TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, name)
        )
        """
        
        # 创建GeoServer图层组表
        create_geoserver_layergroups_table = """
        CREATE TABLE IF NOT EXISTS geoserver_layergroups (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id INTEGER REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
            title VARCHAR(255),
            abstract TEXT,
            mode VARCHAR(50) DEFAULT 'SINGLE',
            layers JSONB,
            bounds JSONB,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, name)
        )
        """
        
        # 创建场景表 - 更新以匹配新的数据库结构
        create_scenes_table = """
        CREATE TABLE IF NOT EXISTS scenes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            is_public BOOLEAN DEFAULT TRUE,
            user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建场景图层表 - 更新以匹配新的数据库结构
        create_scene_layers_table = """
        CREATE TABLE IF NOT EXISTS scene_layers (
            id SERIAL PRIMARY KEY,
            scene_id INTEGER NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
            layer_id INTEGER NOT NULL,
            martin_service_id INTEGER,
            martin_service_type VARCHAR(20) DEFAULT NULL,
            layer_type VARCHAR(20) DEFAULT 'geoserver',
            layer_order INTEGER DEFAULT 1,
            visible BOOLEAN DEFAULT true,
            opacity REAL DEFAULT 1.0,
            style_name VARCHAR(100),
            custom_style JSONB,
            queryable BOOLEAN DEFAULT true,
            selectable BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建统一的矢量Martin服务表（合并geojson和shp服务）
        create_vector_martin_services_table = """
        CREATE TABLE IF NOT EXISTS vector_martin_services (
            id SERIAL PRIMARY KEY,
            file_id VARCHAR(36) NOT NULL UNIQUE,
            original_filename VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            vector_type VARCHAR(20) NOT NULL, -- 'geojson' 或 'shp'
            table_name VARCHAR(100) NOT NULL,
            service_url TEXT,
            mvt_url TEXT,
            tilejson_url TEXT,
            style JSONB,
            vector_info JSONB,  -- 存储原始矢量文件信息
            postgis_info JSONB,
            status VARCHAR(20) DEFAULT 'active',
            user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建矢量Martin服务表的索引
        create_vector_martin_services_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_file_id ON vector_martin_services(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_table_name ON vector_martin_services(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_vector_type ON vector_martin_services(vector_type)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_status ON vector_martin_services(status)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_user_id ON vector_martin_services(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_service_url ON vector_martin_services(service_url)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)"
        ]
        
        # 创建其他表的索引（为了保持一致性）
        create_users_indexes = []
        create_files_indexes = []
        create_geoserver_workspaces_indexes = []
        create_geoserver_stores_indexes = []
        create_geoserver_featuretypes_indexes = []
        create_geoserver_coverages_indexes = []
        create_geoserver_layers_indexes = []
        create_geoserver_styles_indexes = []
        create_geoserver_layergroups_indexes = []
        create_scenes_indexes = []
        
        # 执行所有创建表的SQL
        tables = [
            create_users_table,
            create_files_table,
            create_geoserver_workspaces_table,
            create_geoserver_stores_table,
            create_geoserver_featuretypes_table,
            create_geoserver_coverages_table,
            create_geoserver_layers_table,
            create_geoserver_styles_table,
            create_geoserver_layergroups_table,
            create_scenes_table,
            create_scene_layers_table,
            create_vector_martin_services_table
        ]
        
        for table_sql in tables:
            execute_query(table_sql, fetch=False)
        
        # 创建所有索引
        all_indexes = (
            create_users_indexes +
            create_files_indexes +
            create_geoserver_workspaces_indexes +
            create_geoserver_stores_indexes +
            create_geoserver_featuretypes_indexes +
            create_geoserver_coverages_indexes +
            create_geoserver_layers_indexes +
            create_geoserver_styles_indexes +
            create_geoserver_layergroups_indexes +
            create_scenes_indexes +
            create_vector_martin_services_indexes +
            create_scene_layers_indexes
        )
        
        for index_sql in all_indexes:
            execute_query(index_sql, fetch=False)
        
        print("数据库表创建成功")
        
        # 插入默认工作空间
        insert_default_workspace = """
        INSERT INTO geoserver_workspaces (name, namespace_uri, namespace_prefix, description, is_default)
        VALUES ('shpservice', 'http://shpservice', 'shpservice', 'Default workspace for SHP service', TRUE)
        ON CONFLICT (name) DO NOTHING
        """
        execute_query(insert_default_workspace, fetch=False)
        
        print("默认工作空间创建成功")
        
        # 执行数据库迁移
        _migrate_database()
        
    except Exception as e:
        print(f"初始化数据库失败: {str(e)}")
        raise

def _migrate_database():
    """执行数据库迁移"""
    try:
        print("检查数据库迁移...")
        
        # 检查 geoserver_featuretypes 表是否有 projection_policy 字段
        check_projection_policy_sql = """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'geoserver_featuretypes' 
            AND column_name = 'projection_policy'
            AND table_schema = 'public'
        )
        """
        
        result = execute_query(check_projection_policy_sql)
        has_projection_policy = result[0]['exists']
        
        if not has_projection_policy:
            print("添加 projection_policy 字段到 geoserver_featuretypes 表...")
            add_projection_policy_sql = """
            ALTER TABLE geoserver_featuretypes 
            ADD COLUMN projection_policy VARCHAR(50) DEFAULT 'REPROJECT_TO_DECLARED'
            """
            execute_query(add_projection_policy_sql, fetch=False)
            print("✅ projection_policy 字段添加成功")
        else:
            print("✅ projection_policy 字段已存在")
        
        # 检查 scene_layers 表是否有 martin_service_type 字段
        check_scene_layers_fields_sql = """
        SELECT 
            EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'scene_layers' 
                AND column_name = 'martin_service_type'
                AND table_schema = 'public'
            ) as has_martin_service_type,
            EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'scene_layers' 
                AND column_name = 'layer_type'
                AND table_schema = 'public'
            ) as has_layer_type
        """
        
        result = execute_query(check_scene_layers_fields_sql)
        scene_layers_fields = result[0]
        
        if not scene_layers_fields['has_martin_service_type']:
            print("添加 martin_service_type 字段到 scene_layers 表...")
            add_martin_service_type_sql = """
            ALTER TABLE scene_layers 
            ADD COLUMN martin_service_type VARCHAR(20) DEFAULT NULL
            """
            execute_query(add_martin_service_type_sql, fetch=False)
            print("✅ martin_service_type 字段添加成功")
        else:
            print("✅ martin_service_type 字段已存在")
        
        if not scene_layers_fields['has_layer_type']:
            print("添加 layer_type 字段到 scene_layers 表...")
            add_layer_type_sql = """
            ALTER TABLE scene_layers 
            ADD COLUMN layer_type VARCHAR(20) DEFAULT 'geoserver'
            """
            execute_query(add_layer_type_sql, fetch=False)
            print("✅ layer_type 字段添加成功")
        else:
            print("✅ layer_type 字段已存在")
        
        # 检查并迁移Martin服务表到统一的vector_martin_services表
        check_vector_table_sql = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'vector_martin_services' 
            AND table_schema = 'public'
        )
        """
        
        result = execute_query(check_vector_table_sql)
        has_vector_table = result[0]['exists']
        
        if not has_vector_table:
            print("创建vector_martin_services表...")
            # 表会在init_database中创建，这里只是检查
        else:
            print("✅ vector_martin_services表已存在")
        
        # 数据迁移：从旧的geojson_martin_services和shp_martin_services迁移数据
        print("检查数据迁移...")
        
        # 检查旧表是否存在
        check_old_tables_sql = """
        SELECT 
            EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'geojson_martin_services' 
                AND table_schema = 'public'
            ) as has_geojson_table,
            EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'shp_martin_services' 
                AND table_schema = 'public'
            ) as has_shp_table
        """
        
        result = execute_query(check_old_tables_sql)
        old_tables = result[0]
        
        # 迁移GeoJSON Martin服务数据
        if old_tables['has_geojson_table']:
            # 检查是否已经迁移过
            check_geojson_migrated_sql = """
            SELECT COUNT(*) as count FROM vector_martin_services WHERE vector_type = 'geojson'
            """
            result = execute_query(check_geojson_migrated_sql)
            migrated_count = result[0]['count']
            
            # 检查原表数据数量
            check_geojson_count_sql = "SELECT COUNT(*) as count FROM geojson_martin_services"
            result = execute_query(check_geojson_count_sql)
            original_count = result[0]['count']
            
            if migrated_count < original_count:
                print(f"迁移GeoJSON Martin服务数据: {original_count} 条记录...")
                migrate_geojson_sql = """
                INSERT INTO vector_martin_services 
                (file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, style, vector_info, postgis_info, status, user_id, created_at, updated_at)
                SELECT 
                    file_id, original_filename, file_path, 'geojson' as vector_type, table_name, service_url, mvt_url, tilejson_url, style, geojson_info as vector_info, postgis_info, status, user_id, created_at, updated_at
                FROM geojson_martin_services 
                WHERE file_id NOT IN (SELECT file_id FROM vector_martin_services WHERE vector_type = 'geojson')
                """
                execute_query(migrate_geojson_sql, fetch=False)
                print("✅ GeoJSON Martin服务数据迁移完成")
            else:
                print("✅ GeoJSON Martin服务数据已迁移")
        
        # 迁移SHP Martin服务数据
        if old_tables['has_shp_table']:
            # 检查是否已经迁移过
            check_shp_migrated_sql = """
            SELECT COUNT(*) as count FROM vector_martin_services WHERE vector_type = 'shp'
            """
            result = execute_query(check_shp_migrated_sql)
            migrated_count = result[0]['count']
            
            # 检查原表数据数量
            check_shp_count_sql = "SELECT COUNT(*) as count FROM shp_martin_services"
            result = execute_query(check_shp_count_sql)
            original_count = result[0]['count']
            
            if migrated_count < original_count:
                print(f"迁移SHP Martin服务数据: {original_count} 条记录...")
                migrate_shp_sql = """
                INSERT INTO vector_martin_services 
                (file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, style, vector_info, postgis_info, status, user_id, created_at, updated_at)
                SELECT 
                    file_id, original_filename, file_path, 'shp' as vector_type, table_name, service_url, mvt_url, tilejson_url, style, shp_info as vector_info, postgis_info, status, user_id, created_at, updated_at
                FROM shp_martin_services 
                WHERE file_id NOT IN (SELECT file_id FROM vector_martin_services WHERE vector_type = 'shp')
                """
                execute_query(migrate_shp_sql, fetch=False)
                print("✅ SHP Martin服务数据迁移完成")
            else:
                print("✅ SHP Martin服务数据已迁移")
        
        # 更新scene_layers表中的martin_service_type字段
        print("更新scene_layers表中的martin_service_type字段...")
        update_scene_layers_sql = """
        UPDATE scene_layers 
        SET martin_service_type = (
            SELECT vector_type 
            FROM vector_martin_services 
            WHERE vector_martin_services.id = scene_layers.martin_service_id
        )
        WHERE martin_service_id IS NOT NULL 
        AND martin_service_type IS NULL
        """
        execute_query(update_scene_layers_sql, fetch=False)
        print("✅ scene_layers表martin_service_type字段更新完成")
        
        print("数据库迁移完成")
        
    except Exception as e:
        print(f"数据库迁移失败: {str(e)}")
        # 不抛出异常，允许应用继续运行
        pass

if __name__ == "__main__":
    init_database() 