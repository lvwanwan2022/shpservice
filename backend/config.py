'''
Author: WangNing
Date: 2025-05-16 21:36:41
LastEditors: WangNing
LastEditTime: 2025-06-06 17:01:17
FilePath: \shpservice\backend\config.py
Description: 
Copyright (c) 2025 by VGE, All Rights Reserved. 
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: WangNing
Date: 2025-05-16 21:36:41
LastEditors: WangNing
LastEditTime: 2025-05-27 16:09:03
FilePath: \\shpservice\\backend\\config.py
Description: 配置文件
Copyright (c) 2025 by VGE, All Rights Reserved. 
"""

import os

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'Geometry',
    'user': 'postgres',
    'password': '123456',
    'schema': 'public'
}

# PostGIS专用配置
POSTGIS_CONFIG = {
    **DB_CONFIG,  # 继承基础数据库配置
    'geometry_column': 'geom',  # 默认几何列名
    'srid': 4326,  # 默认空间参考系统
    'enable_mixed_geometry_split': True,  # 是否启用混合几何类型自动分离
    'table_prefix': 'geojson_',  # GeoJSON表前缀
    'use_geopandas': True,  # 优先使用GeoPandas
    'create_spatial_index': True,  # 自动创建空间索引
    'optimize_for_geoserver': True,  # 针对GeoServer优化
}

# Martin 瓦片服务配置
MARTIN_CONFIG = {
    'enabled': True,
    'port': 3000,
    'host': '0.0.0.0',
    'base_url': 'http://localhost:3000',  # Martin服务基础URL
    'worker_processes': 'auto',
    'postgres_connection': f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
    'auto_publish_tables': True,  # 自动发现并发布 PostGIS 表
    'table_sources': [],  # 将在运行时动态填充
    'cors_enabled': True,
    'cache_size': 512,  # MB
    'pool_size': 20,
    # Martin 可执行文件路径配置 - 修正路径中的特殊字符
    'martin_executable': r'G:\code\martin\martin-x86_64-pc-windows-msvc\martin.exe',
}

# GeoServer配置
GEOSERVER_CONFIG = {
    'url': 'http://localhost:8083/geoserver',
    'workspace': 'shpservice',
    'datastore': 'test_geojson',
    'user': 'admin',
    'password': 'geoserver',
    # GeoServer数据目录 - 请根据您的实际安装路径修改
    'data_dir': {
        'windows': 'D:\\ProgramData\\GeoServer\\data\\',
        'linux': '/opt/geoserver/data_dir/',
        'default': './geoserver_data/'
    },
    # 重试和超时配置
    'timeout': 60,
    'max_retries': 3,
    'retry_delay': 2,
    # 缓存重置延迟（秒）
    'cache_reset_delay': 5,
    # PostGIS数据源配置
    'postgis_datastore': {
        'host': DB_CONFIG['host'],
        'port': DB_CONFIG['port'],
        'database': DB_CONFIG['database'],
        'schema': DB_CONFIG['schema'],
        'user': DB_CONFIG['user'],
        'password': DB_CONFIG['password'],
        'dbtype': 'postgis',
        'Expose primary keys': 'true',
        'Support on the fly geometry simplification': 'true',
        'encode functions': 'true'
    }
}

# 文件存储配置
FILE_STORAGE = {
    'upload_folder': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FilesData'),
    'temp_folder': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp'),  # 临时文件目录
    'allowed_extensions': ['zip', 'shp', 'geojson', 'json', 'kml', 'gpkg', 'tif', 'tiff', 'dxf'],
    'max_content_length': 10 * 1024 * 1024 * 1024,  # 10GB
    'chunk_size': 10 * 1024 * 1024,  # 分片大小: 10MB
    'chunk_cleanup_hours': 24,  # 分片文件清理时间: 24小时
}

# 应用配置
APP_CONFIG = {
    'secret_key': 'shpservice-secret-key',
    'debug': True
}

# 日志配置
LOG_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'app.log',
}

# 调试模式
DEBUG = True 