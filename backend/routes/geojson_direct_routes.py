#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoJSON直接服务路由
提供GeoJSON文件的上传、获取、管理等API接口
"""

from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
from werkzeug.utils import secure_filename
from services.geojson_direct_service import GeoJsonDirectService

# 创建蓝图
geojson_direct_bp = Blueprint('geojson_direct', __name__, url_prefix='/api/geojson')

# 服务实例
geojson_service = GeoJsonDirectService()

@geojson_direct_bp.route('/upload', methods=['POST'])
def upload_geojson():
    """
    上传GeoJSON文件
    
    Returns:
        JSON response with file info and access URLs
    """
    try:
        print("\n=== GeoJSON文件上传请求 ===")
        
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
        
        # 保存到临时文件
        original_filename = secure_filename(file.filename)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.geojson')
        
        try:
            file.save(temp_file.name)
            temp_file.close()
            
            print(f"接收到文件: {original_filename}")
            print(f"临时文件: {temp_file.name}")
            
            # 处理文件
            result = geojson_service.upload_geojson(
                file_path=temp_file.name,
                original_filename=original_filename,
                user_id=user_id
            )
            
            print(f"✅ 文件上传成功: {result['file_id']}")
            
            return jsonify(result), 200
            
        except Exception as e:
            # 清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
            raise e
            
    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_direct_bp.route('/files/<file_id>', methods=['GET'])
def get_geojson_file(file_id):
    """
    获取GeoJSON文件内容（前端用于Leaflet加载）
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with GeoJSON data
    """
    try:
        print(f"\n=== 获取GeoJSON文件: {file_id} ===")
        
        result = geojson_service.get_geojson_file(file_id)
        
        # 设置CORS头部（允许跨域访问）
        response = jsonify(result['data'])
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        
        print(f"✅ 返回GeoJSON数据，要素数量: {result['file_info']['feature_count']}")
        
        return response, 200
        
    except Exception as e:
        print(f"❌ 获取文件失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

@geojson_direct_bp.route('/files/<file_id>/info', methods=['GET'])
def get_file_info(file_id):
    """
    获取文件信息（不包含数据内容）
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with file metadata
    """
    try:
        result = geojson_service.get_geojson_file(file_id)
        
        return jsonify({
            "success": True,
            "file_info": result['file_info']
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

@geojson_direct_bp.route('/files/<file_id>/download', methods=['GET'])
def download_geojson_file(file_id):
    """
    下载GeoJSON原文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        File download response
    """
    try:
        print(f"\n=== 下载GeoJSON文件: {file_id} ===")
        
        result = geojson_service.get_geojson_file(file_id)
        file_info = result['file_info']
        
        # 获取文件路径
        from models.db import execute_query
        sql = "SELECT stored_path FROM geojson_files WHERE file_id = %s AND status = 'active'"
        file_result = execute_query(sql, (file_id,))
        
        if not file_result:
            raise Exception("文件不存在")
        
        stored_path = file_result[0]['stored_path']
        
        if not os.path.exists(stored_path):
            raise Exception("物理文件不存在")
        
        # 返回文件下载
        return send_file(
            stored_path,
            as_attachment=True,
            download_name=file_info['original_filename'],
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

@geojson_direct_bp.route('/files', methods=['GET'])
def list_geojson_files():
    """
    列出GeoJSON文件
    
    Query parameters:
        user_id: 用户ID（可选）
        limit: 每页数量（默认50）
        offset: 偏移量（默认0）
        
    Returns:
        JSON response with file list
    """
    try:
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        # 限制查询范围
        limit = min(limit, 100)  # 最大100条
        
        result = geojson_service.list_geojson_files(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_direct_bp.route('/files/<file_id>', methods=['DELETE'])
def delete_geojson_file(file_id):
    """
    删除GeoJSON文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with success status
    """
    try:
        user_id = request.args.get('user_id', type=int)
        
        result = geojson_service.delete_geojson_file(file_id, user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@geojson_direct_bp.route('/leaflet-config/<file_id>', methods=['GET'])
def get_leaflet_config(file_id):
    """
    获取Leaflet地图配置
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with Leaflet configuration
    """
    try:
        # 获取文件信息
        from models.db import execute_query
        sql = """
        SELECT file_id, original_filename, feature_count, geometry_types, 
               property_fields, bbox
        FROM geojson_files 
        WHERE file_id = %s AND status = 'active'
        """
        result = execute_query(sql, (file_id,))
        
        if not result:
            raise Exception("文件不存在")
        
        record = result[0]
        
        # 构建分析数据
        analysis = {
            'feature_count': record['feature_count'],
            'geometry_types': eval(record['geometry_types'] or '[]'),
            'property_fields': eval(record['property_fields'] or '[]'),
            'bbox': eval(record['bbox']) if record['bbox'] else None
        }
        
        # 生成配置
        access_url = f"{geojson_service.public_url_base}/{file_id}"
        config = geojson_service._generate_leaflet_config(access_url, analysis)
        
        return jsonify({
            "success": True,
            "config": config,
            "file_info": {
                "file_id": record['file_id'],
                "original_filename": record['original_filename'],
                "feature_count": record['feature_count']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404

@geojson_direct_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "success": True,
        "service": "GeoJSON Direct Service",
        "status": "healthy"
    }), 200

# 错误处理
@geojson_direct_bp.errorhandler(413)
def request_entity_too_large(error):
    """文件过大错误处理"""
    return jsonify({
        "success": False,
        "error": "文件过大，请上传小于指定大小的文件"
    }), 413

@geojson_direct_bp.errorhandler(400)
def bad_request(error):
    """请求错误处理"""
    return jsonify({
        "success": False,
        "error": "请求格式错误"
    }), 400

@geojson_direct_bp.errorhandler(404)
def not_found(error):
    """资源不存在错误处理"""
    return jsonify({
        "success": False,
        "error": "请求的资源不存在"
    }), 404

@geojson_direct_bp.errorhandler(500)
def internal_server_error(error):
    """服务器内部错误处理"""
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500 