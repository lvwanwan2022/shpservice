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
        # 检查并创建PostGIS扩展
        check_postgis_sql = """
        SELECT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = 'postgis'
        )
        """
        result = execute_query(check_postgis_sql)
        has_postgis = result[0]['exists']
        
        if not has_postgis:
            print("PostGIS扩展不存在，尝试创建...")
            try:
                create_postgis_sql = "CREATE EXTENSION postgis"
                execute_query(create_postgis_sql, fetch=False)
                print("✅ PostGIS扩展创建成功")
                
                # 创建PostGIS拓扑扩展（可选）
                create_postgis_topology_sql = "CREATE EXTENSION postgis_topology"
                execute_query(create_postgis_topology_sql, fetch=False)
                print("✅ PostGIS拓扑扩展创建成功")
                
                # 创建其他有用的PostGIS相关扩展
                try:
                    # 用于栅格数据处理
                    execute_query("CREATE EXTENSION postgis_raster", fetch=False)
                    print("✅ PostGIS栅格扩展创建成功")
                except Exception as e:
                    print(f"⚠️ 创建PostGIS栅格扩展失败: {str(e)}")
                
                try:
                    # 用于地址解析和地理编码
                    execute_query("CREATE EXTENSION fuzzystrmatch", fetch=False)
                    execute_query("CREATE EXTENSION address_standardizer", fetch=False)
                    execute_query("CREATE EXTENSION address_standardizer_data_us", fetch=False)
                    execute_query("CREATE EXTENSION postgis_tiger_geocoder", fetch=False)
                    print("✅ PostGIS地理编码扩展创建成功")
                except Exception as e:
                    print(f"⚠️ 创建地理编码扩展失败: {str(e)}")
                    print("部分地理编码功能可能不可用")
                
                # 创建空间索引扩展
                try:
                    execute_query("CREATE EXTENSION btree_gist", fetch=False)
                    print("✅ GiST索引扩展创建成功")
                except Exception as e:
                    print(f"⚠️ 创建GiST索引扩展失败: {str(e)}")
            except Exception as e:
                print(f"⚠️ 创建PostGIS扩展失败: {str(e)}")
                print("请确保PostgreSQL已安装PostGIS，并且当前用户有创建扩展的权限")
        else:
            print("✅ PostGIS扩展已存在")
            
            # 检查PostGIS版本
            postgis_version_sql = "SELECT PostGIS_Version()"
            try:
                version_result = execute_query(postgis_version_sql)
                print(f"✅ 当前PostGIS版本: {version_result[0]['postgis_version']}")
            except:
                print("⚠️ 无法获取PostGIS版本信息")
            
            # 检查其他扩展
            check_extensions_sql = """
            SELECT extname FROM pg_extension 
            WHERE extname IN ('postgis_topology', 'postgis_raster', 'fuzzystrmatch', 
                             'address_standardizer', 'postgis_tiger_geocoder', 'btree_gist')
            """
            try:
                extensions_result = execute_query(check_extensions_sql)
                installed_extensions = [ext['extname'] for ext in extensions_result]
                print(f"✅ 已安装的扩展: {', '.join(installed_extensions)}")
                
                # 检查缺失的扩展
                all_extensions = ['postgis_topology', 'postgis_raster', 'fuzzystrmatch', 
                                 'address_standardizer', 'postgis_tiger_geocoder', 'btree_gist']
                missing_extensions = [ext for ext in all_extensions if ext not in installed_extensions]
                
                if missing_extensions:
                    print(f"⚠️ 缺少的扩展: {', '.join(missing_extensions)}")
                    print("部分空间数据功能可能受限")
            except:
                print("⚠️ 无法检查已安装扩展")
        
        # 创建用户表
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        execute_query(create_users_table, fetch=False)
        
        # 检查是否需要创建默认管理员用户
        check_admin_user = "SELECT COUNT(*) FROM users WHERE username = 'admin'"
        admin_count = execute_query(check_admin_user)[0]['count']
        
        if admin_count == 0:
            # 创建默认管理员用户，使用雪花算法生成ID
            import hashlib
            from utils.snowflake import get_snowflake_id
            
            # 生成密码哈希
            default_password = "admin123"
            password_hash = hashlib.sha256(default_password.encode()).hexdigest()
            
            # 使用雪花算法生成ID
            admin_id = get_snowflake_id()
            
            # 插入管理员用户
            insert_admin_sql = """
            INSERT INTO users (id, username, password, email    ) 
            VALUES (%s, %s, %s, %s)
            """
            execute_query(insert_admin_sql, (admin_id, "admin", password_hash, "admin@example.com"), fetch=False)
            print("✅ 已创建默认管理员用户 (用户名: admin, 密码: admin123)")
        # 检查是否需要创建默认普通用户
        check_user_user = "SELECT COUNT(*) FROM users WHERE username = 'user'"
        user_count = execute_query(check_user_user)[0]['count']
        
        if user_count == 0:
            # 创建默认普通用户，使用雪花算法生成ID
            import hashlib
            from utils.snowflake import get_snowflake_id
            
            # 生成密码哈希
            default_password = "user123"
            password_hash = hashlib.sha256(default_password.encode()).hexdigest()
            
            # 使用雪花算法生成ID
            user_id = get_snowflake_id()
            
            # 插入管理员用户
            insert_user_sql = """
            INSERT INTO users (id, username, password, email    ) 
            VALUES (%s, %s, %s, %s)
            """
            execute_query(insert_user_sql, (user_id, "user", password_hash, "user@example.com"), fetch=False)
            print("✅ 已创建默认普通用户 (用户名: user, 密码: user123)")
        # 创建文件表 - 更新以匹配新的数据库结构
        create_files_table = """
        CREATE TABLE IF NOT EXISTS files (
            id BIGINT PRIMARY KEY,
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
            user_id BIGINT REFERENCES users(id),
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
            id BIGINT PRIMARY KEY,
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
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id BIGINT REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
            store_type VARCHAR(50) NOT NULL,
            data_type VARCHAR(50),
            connection_params JSONB,
            description TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            file_id BIGINT REFERENCES files(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, name)
        )
        """
        
        # 创建GeoServer要素类型表
        create_geoserver_featuretypes_table = """
        CREATE TABLE IF NOT EXISTS geoserver_featuretypes (
            id BIGINT PRIMARY KEY,
            name VARCHAR(100),
            native_name VARCHAR(100),
            store_id BIGINT REFERENCES geoserver_stores(id) ON DELETE CASCADE,
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
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            native_name VARCHAR(100),
            store_id BIGINT REFERENCES geoserver_stores(id) ON DELETE CASCADE,
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
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id BIGINT REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
            featuretype_id BIGINT REFERENCES geoserver_featuretypes(id) ON DELETE CASCADE,
            coverage_id BIGINT REFERENCES geoserver_coverages(id) ON DELETE CASCADE,
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
            file_id BIGINT REFERENCES files(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            style_config JSONB,
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
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id BIGINT REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
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
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            workspace_id BIGINT REFERENCES geoserver_workspaces(id) ON DELETE CASCADE,
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
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            is_public BOOLEAN DEFAULT TRUE,
            user_id BIGINT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建场景图层表 - 更新以匹配新的数据库结构
        create_scene_layers_table = """
        CREATE TABLE IF NOT EXISTS scene_layers (
            id BIGINT PRIMARY KEY,
            scene_id BIGINT NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
            layer_id BIGINT NOT NULL,
            martin_service_id BIGINT,
            martin_service_type VARCHAR(20) DEFAULT NULL,
            layer_type VARCHAR(20) DEFAULT 'geoserver',
            layer_order INTEGER DEFAULT 0,
            visible BOOLEAN DEFAULT true,
            opacity NUMERIC(3,2) DEFAULT 1.0,
            style_name VARCHAR(100),
            custom_style JSONB,
            queryable BOOLEAN DEFAULT true,
            selectable BOOLEAN DEFAULT true,
            service_reference VARCHAR(100),
            service_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            boundingbox JSONB,
            CONSTRAINT chk_layer_type CHECK (layer_type IN ('geoserver', 'martin'))
        )
        """
        
        # 创建统一的矢量Martin服务表（合并geojson和shp服务）
        create_vector_martin_services_table = """
        CREATE TABLE IF NOT EXISTS vector_martin_services (
            id BIGINT PRIMARY KEY,
            file_id VARCHAR(36) NOT NULL UNIQUE,
            original_filename VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            vector_type VARCHAR(40) NOT NULL, -- 'geojson' 或 'shp'
            table_name VARCHAR(100) NOT NULL,
            service_url TEXT,
            mvt_url TEXT,
            tilejson_url TEXT,
            style JSONB,
            vector_info JSONB,  -- 存储原始矢量文件信息
            postgis_info JSONB,
            status VARCHAR(20) DEFAULT 'active',
            user_id BIGINT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建GeoJSON文件表（用于GeoJSON直接服务）
        create_geojson_files_table = """
        CREATE TABLE IF NOT EXISTS geojson_files (
            id BIGINT PRIMARY KEY,
            file_id VARCHAR(36) NOT NULL UNIQUE,
            original_filename VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            stored_path TEXT,
            file_size BIGINT NOT NULL,
            feature_count INTEGER DEFAULT 0,
            geometry_types JSONB,
            property_fields JSONB,
            bbox JSONB,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            user_id BIGINT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
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
        
        # 创建GeoJSON文件表的索引
        create_geojson_files_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_file_id ON geojson_files(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_status ON geojson_files(status)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_user_id ON geojson_files(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_geojson_files_upload_date ON geojson_files(upload_date)"
        ]
        
        # 创建反馈系统的索引
        create_feedback_items_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count)"
        ]
        
        create_feedback_attachments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type)"
        ]
        
        create_feedback_votes_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type)"
        ]
        
        create_feedback_comments_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at)"
        ]
        
        # 创建场景图层表的索引
        create_scene_layers_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_scene_id ON scene_layers(scene_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_id ON scene_layers(layer_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_martin_service_id ON scene_layers(martin_service_id)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_layer_order ON scene_layers(layer_order)",
            "CREATE INDEX IF NOT EXISTS idx_scene_layers_order ON scene_layers(scene_id, layer_order)"
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
        
        # 用户服务管理系统索引
        create_user_service_connections_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_type_status ON user_service_connections(service_type, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_port ON user_service_connections(port_number)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_created_at ON user_service_connections(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, is_default) WHERE is_default = TRUE"
        ]
        
        # 创建服务端口分配表
        create_service_port_allocations_table = """
        CREATE TABLE IF NOT EXISTS service_port_allocations (
            id BIGINT PRIMARY KEY,
            port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            service_config_id BIGINT REFERENCES user_service_connections(id) ON DELETE SET NULL,
            allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            released_at TIMESTAMP,
            notes TEXT
        )
        """
        
        # ===== 用户反馈系统表 =====
        # 创建反馈表
        create_feedback_items_table = """
        CREATE TABLE IF NOT EXISTS feedback_items (
            id BIGINT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
            module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
            type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
            priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
            status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
            
            -- 用户信息（可以根据实际系统调整）
            user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 统计信息
            support_count INTEGER DEFAULT 0,
            oppose_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            
            -- 附件信息
            has_attachments BOOLEAN DEFAULT FALSE,
            
            -- 时间戳
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建反馈附件表
        create_feedback_attachments_table = """
        CREATE TABLE IF NOT EXISTS feedback_attachments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),          -- 'image', 'document', 'archive'
            file_size BIGINT,
            file_path VARCHAR(500),
            mime_type VARCHAR(100),
            
            -- 图片特殊信息
            is_screenshot BOOLEAN DEFAULT FALSE,
            image_width INTEGER,
            image_height INTEGER,
            
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
        )
        """
        
        # 创建用户投票表
        create_feedback_votes_table = """
        CREATE TABLE IF NOT EXISTS feedback_votes (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            UNIQUE (feedback_id, user_id)
        )
        """
        
        # 创建评论表
        create_feedback_comments_table = """
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id BIGINT PRIMARY KEY,
            feedback_id BIGINT NOT NULL,
            parent_id BIGINT,               -- 支持回复评论
            
            content TEXT NOT NULL,
            
            -- 用户信息
            user_id VARCHAR(100) NOT NULL,
            username VARCHAR(100),
            user_email VARCHAR(200),
            
            -- 状态
            is_deleted BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
        )
        """
        
        # 创建矢量Martin服务表的索引
        create_vector_martin_services_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_file_id ON vector_martin_services(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_table_name ON vector_martin_services(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_vector_type ON vector_martin_services(vector_type)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_status ON vector_martin_services(status)",
            "CREATE INDEX IF NOT EXISTS idx_vector_martin_services_user_id ON