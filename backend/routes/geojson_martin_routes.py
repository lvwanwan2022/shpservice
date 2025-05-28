#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoJSON Martin服务路由
提供GeoJSON文件到MVT瓦片服务的完整发布流程API接口
"""

from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename
from services.geojson_martin_service import GeoJsonMartinService

# 创建蓝图
geojson_martin_bp = Blueprint('geojson_martin', __name__, url_prefix='/api/geojson-martin')

# 服务实例
geojson_martin_service = GeoJsonMartinService()

@geojson_martin_bp.route('/publish', methods=['POST'])
def publish_geojson_service():
    """
    发布GeoJSON为MVT瓦片服务
    
    完整流程：
    1. 上传GeoJSON文件
    2. 使用geopandas存入PostGIS
    3. 通过Martin发布MVT瓦片服务
    
    Returns:
        JSON response with service info and MVT URLs
    """
    try:
        print("\n=== GeoJSON MVT瓦片服务发布请求 ===")
        
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "没有选择文件"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "没有选择文件"
            }), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith(('.geojson', '.json')):
            return jsonify({
                "success": False,
                "error": "只支持 .geojson 或 .json 文件"
            }), 400
        
        # 获取用户ID（如果有用户系统）
        user_id = request.form.get('user_id', type=int)
        
        # 构建文件信息
        file_info = {
            'original_filename': secure_filename(file.filename),
            'user_id': user_id
        }
        
        print(f"接收到文件: {file_info['original_filename']}")
        print(f"用户ID: {user_id}")
        
        # 发布服务
        result = geojson_martin_service.publish_geojson_service(file, file_info)
        
        print(f"✅ GeoJSON MVT瓦片服务发布成功: {result['file_id']}")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ 发布失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/services/<file_id>', methods=['GET'])
def get_service_info(file_id):
    """
    获取已发布服务的详细信息
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with service details and MVT URLs
    """
    try:
        print(f"\n=== 获取服务信息: {file_id} ===")
        
        result = geojson_martin_service.get_service_info(file_id)
        
        print(f"✅ 服务信息获取成功")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ 获取服务信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

@geojson_martin_bp.route('/services', methods=['GET'])
def list_services():
    """
    列出已发布的GeoJSON MVT瓦片服务
    
    Query Parameters:
        limit: 限制返回的记录数 (默认100)
        offset: 结果集的偏移量 (默认0)
        user_id: 用户ID过滤
        
    Returns:
        JSON response with services list
    """
    try:
        print("\n=== 列出GeoJSON MVT瓦片服务 ===")
        
        # 获取查询参数
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id', type=int)
        
        # 限制最大返回数量
        limit = min(limit, 1000)
        
        print(f"查询参数: limit={limit}, offset={offset}, user_id={user_id}")
        
        result = geojson_martin_service.list_services(limit, offset, user_id)
        
        print(f"✅ 返回 {len(result['services'])} 个服务")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ 列出服务失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/services/<file_id>', methods=['DELETE'])
def delete_service(file_id):
    """
    删除已发布的GeoJSON MVT瓦片服务
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with deletion result
    """
    try:
        print(f"\n=== 删除服务: {file_id} ===")
        
        # 获取用户ID（用于权限检查）
        user_id = request.args.get('user_id', type=int)
        
        result = geojson_martin_service.delete_service(file_id, user_id)
        
        print(f"✅ 服务删除成功")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ 删除服务失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/martin/status', methods=['GET'])
def get_martin_status():
    """
    获取Martin服务状态
    
    Returns:
        JSON response with Martin service status
    """
    try:
        status = geojson_martin_service.get_martin_status()
        
        return jsonify({
            "success": True,
            "martin_status": status
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/martin/restart', methods=['POST'])
def restart_martin_service():
    """
    重启Martin服务
    
    Returns:
        JSON response with restart result
    """
    try:
        print("\n=== 重启Martin服务 ===")
        
        result = geojson_martin_service.restart_martin_service()
        
        if result['success']:
            print("✅ Martin服务重启成功")
        else:
            print("❌ Martin服务重启失败")
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        print(f"❌ 重启Martin服务失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/mvt/<file_id>/{z}/{x}/{y}.pbf', methods=['GET'])
def get_mvt_tile(file_id, z, x, y):
    """
    代理MVT瓦片请求到Martin服务
    
    Args:
        file_id: 文件ID
        z: 缩放级别
        x: 瓦片X坐标
        y: 瓦片Y坐标
        
    Returns:
        MVT瓦片数据
    """
    try:
        # 获取服务信息
        service_info = geojson_martin_service.get_service_info(file_id)
        
        if not service_info.get('mvt_info'):
            return jsonify({
                "success": False,
                "error": "MVT服务不可用"
            }), 503
        
        # 构建Martin瓦片URL
        table_name = service_info['table_name']
        source_id = f"public.{table_name}"
        martin_base_url = geojson_martin_service.martin_service.base_url
        tile_url = f"{martin_base_url}/{source_id}/{z}/{x}/{y}.pbf"
        
        # 代理请求到Martin
        import requests
        response = requests.get(tile_url)
        
        if response.status_code == 200:
            return response.content, 200, {
                'Content-Type': 'application/x-protobuf',
                'Content-Encoding': 'gzip',
                'Access-Control-Allow-Origin': '*'
            }
        else:
            return jsonify({
                "success": False,
                "error": f"瓦片获取失败: {response.status_code}"
            }), response.status_code
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/tilejson/<file_id>', methods=['GET'])
def get_tilejson(file_id):
    """
    获取TileJSON配置
    
    Args:
        file_id: 文件ID
        
    Returns:
        TileJSON配置
    """
    try:
        # 获取服务信息
        service_info = geojson_martin_service.get_service_info(file_id)
        
        if not service_info.get('mvt_info'):
            return jsonify({
                "success": False,
                "error": "MVT服务不可用"
            }), 503
        
        # 构建TileJSON URL
        table_name = service_info['table_name']
        source_id = f"public.{table_name}"
        martin_base_url = geojson_martin_service.martin_service.base_url
        tilejson_url = f"{martin_base_url}/{source_id}"
        
        # 代理请求到Martin
        import requests
        response = requests.get(tilejson_url)
        
        if response.status_code == 200:
            tilejson = response.json()
            
            # 修改tiles URL为我们的代理URL
            base_url = request.url_root.rstrip('/')
            tilejson['tiles'] = [f"{base_url}/api/geojson-martin/mvt/{file_id}/{{z}}/{{x}}/{{y}}.pbf"]
            
            return jsonify(tilejson), 200
        else:
            return jsonify({
                "success": False,
                "error": f"TileJSON获取失败: {response.status_code}"
            }), response.status_code
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_martin_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    Returns:
        服务状态信息
    """
    try:
        martin_status = geojson_martin_service.get_martin_status()
        
        return jsonify({
            "success": True,
            "service": "GeoJSON Martin Service",
            "status": "healthy",
            "martin_status": martin_status,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "service": "GeoJSON Martin Service",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@geojson_martin_bp.route('/publish-file', methods=['POST'])
def publish_file_to_martin():
    """
    通过文件ID发布已上传的GeoJSON文件到Martin服务
    
    Request Body:
        {
            "file_id": int,  # 文件ID
            "user_id": int   # 用户ID (可选)
        }
        
    Returns:
        JSON response with service info and MVT URLs
    """
    try:
        print("\n=== 通过文件ID发布GeoJSON到Martin服务 ===")
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        file_id = data.get('file_id')
        if not file_id:
            return jsonify({
                "success": False,
                "error": "file_id参数是必需的"
            }), 400
        
        user_id = data.get('user_id')
        
        print(f"文件ID: {file_id}")
        print(f"用户ID: {user_id}")
        
        # 发布服务
        result = geojson_martin_service.publish_existing_file(file_id, user_id)
        
        print(f"✅ 文件 {file_id} 发布到Martin服务成功")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ 发布失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 错误处理器
@geojson_martin_bp.errorhandler(413)
def request_entity_too_large(error):
    """文件过大错误处理"""
    return jsonify({
        "success": False,
        "error": "文件过大，请选择较小的文件"
    }), 413

@geojson_martin_bp.errorhandler(400)
def bad_request(error):
    """请求错误处理"""
    return jsonify({
        "success": False,
        "error": "请求格式错误"
    }), 400

@geojson_martin_bp.errorhandler(404)
def not_found(error):
    """资源不存在错误处理"""
    return jsonify({
        "success": False,
        "error": "请求的资源不存在"
    }), 404

@geojson_martin_bp.errorhandler(500)
def internal_server_error(error):
    """服务器内部错误处理"""
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500 