#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'Geometry',
    'user': 'postgres',
    'password': '123456'
}

# GeoServer配置
GEOSERVER_CONFIG = {
    'url': 'http://localhost:8083/geoserver',
    'user': 'admin',
    'password': 'geoserver',
    'workspace': 'shpservice'
}

# 文件存储配置
FILE_STORAGE = {
    'upload_folder': '../FilesData',
    'allowed_extensions': ['tif', 'mbtiles', 'dwg', 'dxf', 'geojson', 'zip'],
    'max_file_size': 500 * 1024 * 1024  # 500MB
}

# 应用配置
APP_CONFIG = {
    'secret_key': 'shpservice-secret-key',
    'debug': True
} 