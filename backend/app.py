#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Lvwan-793145268@qq.com
Date: 2025-05-16 21:36:54
LastEditors: Lvwan-793145268@qq.com
LastEditTime: 2025-05-23 09:19:19
FilePath: /shpservice/backend/app.py
Description: 
Copyright (c) 2025 by Lvwan, All Rights Reserved. 
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_restx import Api
import logging
import os
import requests
import atexit
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



app = Flask(__name__)

# 从配置模块加载配置
try:
    from config import APP_CONFIG, FILE_STORAGE, GEOSERVER_CONFIG
    app.config.update(APP_CONFIG)
    # 设置文件上传大小限制
    app.config['MAX_CONTENT_LENGTH'] = FILE_STORAGE['max_content_length']
except ImportError:
    # 如果配置文件不存在，使用默认配置
    app.config.update({
        'SECRET_KEY': 'shpservice-secret-key',
        'DEBUG': True,
        'MAX_CONTENT_LENGTH': 50 * 1024 * 1024 * 1024  # 50GB
    })

# 启用CORS
CORS(app)

# 🔥 添加全局中间件，处理大整数ID转换为字符串
class BigIntJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，将大整数转换为字符串"""
    def default(self, obj):
        if isinstance(obj, int):
            # 如果整数大于JavaScript安全整数范围，转换为字符串
            if obj > 9007199254740991 or obj < -9007199254740991:
                return str(obj)
        return super().default(obj)

# 🔥 重写Flask的jsonify函数，使用自定义JSON编码器
def custom_jsonify(*args, **kwargs):
    """自定义jsonify函数，使用BigIntJSONEncoder处理大整数"""
    return app.response_class(
        json.dumps(dict(*args, **kwargs), cls=BigIntJSONEncoder),
        mimetype='application/json'
    )

# 🔥 替换Flask的jsonify函数
app.json.encoder = BigIntJSONEncoder

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
        try:
            init_database()
            logger.info("✅ 数据库初始化成功")
        except Exception as init_error:
            logger.warning(f"⚠️ 数据库初始化失败: {str(init_error)}")
            
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

# SLD样式管理路由
try:
    from routes.sld_style_routes import sld_style_bp
    app.register_blueprint(sld_style_bp)
    logger.info("✅ SLD样式管理路由注册成功")
except ImportError:
    logger.info("SLD样式管理路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ SLD样式管理路由注册失败: {str(e)}")
    logger.info("✅ MBTiles 服务路由注册成功")
except ImportError:
    logger.info("MBTiles 服务路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ MBTiles 服务路由注册失败: {str(e)}")

# TIF Martin 服务路由
try:
    from routes.tif_martin_routes import tif_martin_bp
    app.register_blueprint(tif_martin_bp,url_prefix='/api/tif-martin')
    logger.info("✅ TIF Martin 服务路由注册成功")
except ImportError:
    logger.info("TIF Martin 服务路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ TIF Martin 服务路由注册失败: {str(e)}")

# GIS 通用路由
try:
    from routes.gis import gis_bp
    app.register_blueprint(gis_bp, url_prefix='/api/gis')
    logger.info("✅ GIS 通用路由注册成功")
except ImportError:
    logger.info("GIS 通用路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ GIS 通用路由注册失败: {str(e)}")

# 登录认证路由 - 独立模块，方便移植
try:
    from auth.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("✅ 登录认证路由注册成功")
except ImportError:
    logger.info("登录认证路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 登录认证路由注册失败: {str(e)}")

# 用户反馈路由 - 独立模块，方便移植
try:
    from feedback.feedback_routes import feedback_bp
    app.register_blueprint(feedback_bp)
    logger.info("✅ 用户反馈路由注册成功")
    
    # 确保反馈系统上传目录存在
    feedback_upload_dir = os.path.join(os.path.dirname(__file__), 'feedback_uploads')
    if not os.path.exists(feedback_upload_dir):
        os.makedirs(feedback_upload_dir)
        logger.info(f"✅ 反馈上传目录创建成功: {feedback_upload_dir}")
        
except ImportError:
    logger.info("用户反馈路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 用户反馈路由注册失败: {str(e)}")

# 用户服务管理路由
try:
    from routes.user_service_routes import user_service_bp
    app.register_blueprint(user_service_bp)
    logger.info("✅ 用户服务管理路由注册成功")
except ImportError:
    logger.info("用户服务管理路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 用户服务管理路由注册失败: {str(e)}")

# 用户服务连接管理路由
try:
    from routes.service_connection_routes import service_connection_bp
    app.register_blueprint(service_connection_bp)
    logger.info("✅ 用户服务连接管理路由注册成功")
except ImportError:
    logger.info("用户服务连接管理路由不存在，跳过")
except Exception as e:
    logger.warning(f"⚠️ 用户服务连接管理路由注册失败: {str(e)}")


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
    
    geoserver_url = GEOSERVER_CONFIG['url']
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
            resp = requests.post(target_url, json=request.json, timeout=30, allow_redirects=False)
        elif request.method == 'PUT':
            resp = requests.put(target_url, json=request.json, timeout=30, allow_redirects=False)
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, timeout=30, allow_redirects=False)
        else:
            return jsonify({'error': '不支持的请求方法'}), 405
        
        # 创建响应
        response = Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'text/plain')
        )
        
        # 复制头信息
        for key, value in resp.headers.items():
            if key.lower() not in ('content-length', 'connection', 'content-encoding'):
                response.headers[key] = value
        
        # 设置CORS头
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response
        
    except requests.RequestException as e:
        logger.error(f"代理请求失败: {str(e)}")
        return jsonify({'error': f'代理请求失败: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': 'shpservice'
    })

@app.route('/api/health')
def api_health_check():
    """API健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': 'shpservice-api'
    })

@app.route('/')
def index():
    """首页"""
    return """
    <h1>SHP Service API</h1>
    <p>GIS文件管理和地图服务API</p>
    <p><a href="/swagger/">API文档</a></p>
    """

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({'error': '资源不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5030))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'    
    logger.info(f"🌐 启动Flask应用在端口 {port} (IPv4 + IPv6)")
    #app.run(host='::', port=port, debug=debug) 
    app.run(host='0.0.0.0', port=port, debug=debug) 