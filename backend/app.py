#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: WangNing
Date: 2025-05-16 21:36:54
LastEditors: WangNing
LastEditTime: 2025-05-23 09:19:19
FilePath: /shpservice/backend/app.py
Description: 
Copyright (c) 2025 by VGE, All Rights Reserved. 
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_restx import Api
import logging
import os
import requests
import atexit

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入Martin服务
try:
    from services.martin_service import MartinService
    martin_service = MartinService()
    logger.info("✅ Martin服务模块加载成功")
except Exception as e:
    martin_service = None
    logger.warning(f"⚠️ Martin服务模块加载失败: {str(e)}")

app = Flask(__name__)

# 从配置模块加载配置
try:
    from config import APP_CONFIG, FILE_STORAGE
    app.config.update(APP_CONFIG)
    # 设置文件上传大小限制
    app.config['MAX_CONTENT_LENGTH'] = FILE_STORAGE['max_content_length']
except ImportError:
    # 如果配置文件不存在，使用默认配置
    app.config.update({
        'SECRET_KEY': 'shpservice-secret-key',
        'DEBUG': True,
        'MAX_CONTENT_LENGTH': 10 * 1024 * 1024 * 1024  # 10GB
    })

# 启用CORS
CORS(app)

# 配置API文档
api = Api(
    app,
    version='1.0',
    title='SHP Service API',
    description='GIS文件管理和地图服务API',
    doc='/swagger/',
    prefix='/api'
)

# 尝试数据库连接和初始化
try:
    from models.db import get_connection, init_database
    logger.info("尝试连接数据库...")
    
    try:
        conn = get_connection()
        conn.close()
        logger.info("✅ 数据库连接成功")
        
        # 初始化数据库表
        #try:
            #init_database()
            #logger.info("✅ 数据库初始化成功")
        #except Exception as init_error:
            #logger.warning(f"⚠️ 数据库初始化失败: {str(init_error)}")
            
    except Exception as conn_error:
        logger.warning(f"⚠️ 数据库连接失败: {str(conn_error)}")
        logger.warning("应用将在无数据库模式下运行，部分功能可能受限")
        
except Exception as import_error:
    logger.warning(f"⚠️ 数据库模块导入失败: {str(import_error)}")

# 注册蓝图
try:
    from routes.file_routes import file_bp
    app.register_blueprint(file_bp, url_prefix='/api/files')
    logger.info("✅ 文件路由注册成功")
except Exception as e:
    logger.warning(f"⚠️ 文件路由注册失败: {str(e)}")

try:
    from routes.geoservice_routes import geoservice_bp
    app.register_blueprint(geoservice_bp, url_prefix='/api')
    logger.info("✅ GeoService路由注册成功")
except Exception as e:
    logger.warning(f"⚠️ GeoService路由注册失败: {str(e)}")

# 可选的蓝图（如果存在的话）
try:
    from routes.layer_routes import layer_bp
    app.register_blueprint(layer_bp, url_prefix='/api/layers')
    logger.info("✅ 图层路由注册成功")
except ImportError:
    logger.info("图层路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 图层路由注册失败: {str(e)}")

try:
    from routes.scene_routes import scene_bp
    app.register_blueprint(scene_bp, url_prefix='/api/scenes')
    logger.info("✅ 场景路由注册成功")
except ImportError:
    logger.info("场景路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 场景路由注册失败: {str(e)}")

# Martin 瓦片服务路由
try:
    from routes.martin_routes import martin_bp
    app.register_blueprint(martin_bp)
    logger.info("✅ Martin 瓦片服务路由注册成功")
except ImportError:
    logger.info("Martin 路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ Martin 路由注册失败: {str(e)}")

# GeoJSON Martin 服务路由
try:
    from routes.geojson_martin_routes import geojson_martin_bp
    app.register_blueprint(geojson_martin_bp)
    logger.info("✅ GeoJSON Martin 服务路由注册成功")
except ImportError:
    logger.info("GeoJSON Martin 路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ GeoJSON Martin 路由注册失败: {str(e)}")

# SHP Martin 服务路由
try:
    from routes.shp_martin_routes import shp_martin_bp
    app.register_blueprint(shp_martin_bp)
    logger.info("✅ SHP Martin 服务路由注册成功")
except ImportError:
    logger.info("SHP Martin 路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ SHP Martin 路由注册失败: {str(e)}")

# 统一Martin 服务路由
try:
    from routes.martin_service_routes import martin_service_bp
    app.register_blueprint(martin_service_bp, url_prefix='/api')
    logger.info("✅ 统一Martin 服务路由注册成功")
except ImportError:
    logger.info("统一Martin 路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 统一Martin 路由注册失败: {str(e)}")

# GeoJSON 直接服务路由
try:
    from routes.geojson_direct_routes import geojson_direct_bp
    app.register_blueprint(geojson_direct_bp)
    logger.info("✅ GeoJSON 直接服务路由注册成功")
except ImportError:
    logger.info("GeoJSON 直接服务路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ GeoJSON 直接服务路由注册失败: {str(e)}")

# DXF 服务路由
try:
    from routes.dxf_routes import dxf_bp
    app.register_blueprint(dxf_bp)
    logger.info("✅ DXF 服务路由注册成功")
except ImportError:
    logger.info("DXF 服务路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ DXF 服务路由注册失败: {str(e)}")

# MBTiles 服务路由
try:
    from routes.mbtiles_routes import mbtiles_bp
    app.register_blueprint(mbtiles_bp, url_prefix='/api/mbtiles')
    logger.info("✅ MBTiles 服务路由注册成功")
except ImportError:
    logger.info("MBTiles 服务路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ MBTiles 服务路由注册失败: {str(e)}")

# GIS 通用路由
try:
    from routes.gis import gis_bp
    app.register_blueprint(gis_bp, url_prefix='/api/gis')
    logger.info("✅ GIS 通用路由注册成功")
except ImportError:
    logger.info("GIS 通用路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ GIS 通用路由注册失败: {str(e)}")

# GeoServer代理路由（解决CORS问题）
@app.route('/geoserver/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def geoserver_proxy(path):
    """GeoServer代理，解决CORS跨域问题"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    geoserver_url = 'http://localhost:8083/geoserver'
    target_url = f"{geoserver_url}/{path}"
    
    # 转发查询参数
    if request.query_string:
        target_url += f"?{request.query_string.decode('utf-8')}"
    
    logger.info(f"代理请求: {request.method} {target_url}")
    
    try:
        # 转发请求到GeoServer
        if request.method == 'GET':
            resp = requests.get(target_url, timeout=30, allow_redirects=False)
        elif request.method == 'POST':
            resp = requests.post(target_url, data=request.get_data(), timeout=30, allow_redirects=False)
        else:
            resp = requests.request(request.method, target_url, timeout=30, allow_redirects=False)
        
        # 创建代理响应
        response = Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('content-type')
        )
        
        # 添加CORS头
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        logger.info(f"代理响应: {resp.status_code}")
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"GeoServer代理请求失败: {str(e)}")
        response = jsonify({'error': f'GeoServer服务不可用: {str(e)}'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 503

@app.route('/health')
def health_check():
    """健康检查端点"""
    return {'status': 'healthy', 'message': 'SHP Service is running'}, 200

@app.route('/api/health')
def api_health_check():
    """API健康检查端点"""
    return {'status': 'healthy', 'message': 'SHP Service API is running'}, 200

@app.route('/')
def index():
    """根路径"""
    return {'message': 'SHP Service API', 'version': '1.0.0'}, 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

def cleanup_martin():
    """清理Martin服务进程"""
    if martin_service and martin_service.process:
        try:
            martin_service.process.terminate()
            martin_service.process.wait(timeout=5)
            logger.info("✅ Martin服务已清理")
        except Exception as e:
            logger.warning(f"⚠️ 清理Martin服务时出错: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5030))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'    
    logger.info(f"🌐 启动Flask应用在端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 