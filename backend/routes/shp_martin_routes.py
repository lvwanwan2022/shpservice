#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SHP Martin 瓦片服务相关 API 路由
"""

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
import logging
from services.shp_martin_service import ShpMartinService

logger = logging.getLogger(__name__)

# 创建蓝图
shp_martin_bp = Blueprint('shp_martin', __name__, url_prefix='/api/shp-martin')

# 创建 SHP Martin 服务实例
shp_martin_service = ShpMartinService()


@shp_martin_bp.route('/upload', methods=['POST'])
def upload_and_publish():
    """上传并发布SHP压缩包为Martin瓦片服务"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 验证文件类型
        if not file.filename.lower().endswith('.zip'):
            return jsonify({'error': '只支持.zip格式的SHP压缩包'}), 400
        
        # 获取用户ID（如果有）
        user_id = request.form.get('user_id')
        if user_id:
            user_id = int(user_id)
        
        # 构建文件信息
        file_info = {
            'original_filename': secure_filename(file.filename),
            'user_id': user_id
        }
        
        # 发布服务
        result = shp_martin_service.publish_shp_service(file, file_info)
        
        return jsonify({
            'success': True,
            'message': 'SHP Martin服务发布成功',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"上传并发布SHP服务失败: {str(e)}")
        return jsonify({'error': f'发布SHP服务失败: {str(e)}'}), 500


@shp_martin_bp.route('/services', methods=['GET'])
def list_services():
    """获取SHP Martin服务列表"""
    try:
        # 获取查询参数
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        user_id = request.args.get('user_id')
        
        if user_id:
            user_id = int(user_id)
        
        # 获取服务列表
        result = shp_martin_service.list_services(limit=limit, offset=offset, user_id=user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取SHP Martin服务列表失败: {str(e)}")
        return jsonify({'error': f'获取服务列表失败: {str(e)}'}), 500


@shp_martin_bp.route('/services/<file_id>', methods=['GET'])
def get_service_info(file_id):
    """获取指定SHP Martin服务的信息"""
    try:
        result = shp_martin_service.get_service_info(file_id)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"获取SHP Martin服务信息失败: {str(e)}")
        return jsonify({'error': f'获取服务信息失败: {str(e)}'}), 500


@shp_martin_bp.route('/publish/<string:file_id>', methods=['POST'])
def publish_existing_file(file_id):
    """发布已上传的SHP文件到Martin服务"""
    try:
        # 获取用户ID（如果有）
        user_id = request.json.get('user_id') if request.json else None
        
        # 发布服务
        result = shp_martin_service.publish_existing_file(file_id, user_id)
        
        return jsonify({
            'success': True,
            'message': 'SHP文件发布到Martin服务成功',
            'data': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"发布已存在SHP文件失败: {str(e)}")
        return jsonify({'error': f'发布SHP文件失败: {str(e)}'}), 500


@shp_martin_bp.route('/services/<file_id>', methods=['DELETE'])
def delete_service(file_id):
    """删除SHP Martin服务（软删除）"""
    try:
        # 更新服务状态为非活跃
        from models.db import execute_query
        
        sql = "UPDATE shp_martin_services SET status = 'deleted' WHERE file_id = %s"
        execute_query(sql, (file_id,), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'SHP Martin服务删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"删除SHP Martin服务失败: {str(e)}")
        return jsonify({'error': f'删除服务失败: {str(e)}'}), 500


@shp_martin_bp.errorhandler(413)
def too_large(e):
    """文件太大的错误处理"""
    return jsonify({'error': '文件太大，请选择小于200MB的文件'}), 413


@shp_martin_bp.errorhandler(415)
def unsupported_media_type(e):
    """不支持的媒体类型错误处理"""
    return jsonify({'error': '不支持的文件类型，请上传ZIP格式的SHP压缩包'}), 415 