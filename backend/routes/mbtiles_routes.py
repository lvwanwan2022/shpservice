#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request, current_app
from models.db import execute_query
from services.raster_martin_service import RasterMartinService
from services.file_service import FileService

# 创建蓝图
mbtiles_bp = Blueprint('mbtiles', __name__)
file_service = FileService()
raster_martin_service = RasterMartinService()

@mbtiles_bp.route('/services/list', methods=['GET'])
def get_mbtiles_services():
    """获取所有MBTiles服务列表"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 计算偏移量
        offset = (page - 1) * per_page
        
        # 构建查询
        sql = """
        SELECT vms.*, f.file_name, f.file_size, f.file_type, f.upload_date
        FROM vector_martin_services vms
        LEFT JOIN files f ON vms.file_id = f.id::text
        WHERE vms.vector_type IN ('mbtiles', 'vector_mbtiles', 'raster_mbtiles') AND vms.status = 'active'
        ORDER BY vms.created_at DESC
        LIMIT %s OFFSET %s
        """
        
        # 获取总数
        count_sql = """
        SELECT COUNT(*) as total
        FROM vector_martin_services
        WHERE vector_type IN ('mbtiles', 'vector_mbtiles', 'raster_mbtiles') AND status = 'active'
        """
        
        # 执行查询
        services = execute_query(sql, (per_page, offset))
        count_result = execute_query(count_sql)
        total = count_result[0]['total'] if count_result else 0
        
        return jsonify({
            'success': True,
            'services': services,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取MBTiles服务列表失败: {str(e)}")
        return jsonify({'error': f'获取MBTiles服务列表失败: {str(e)}'}), 500

@mbtiles_bp.route('/services/<int:service_id>', methods=['GET'])
def get_mbtiles_service(service_id):
    """获取指定的MBTiles服务信息"""
    try:
        service = raster_martin_service.get_martin_service_by_id(service_id)
        
        if not service or service['vector_type'] not in ['mbtiles', 'vector_mbtiles', 'raster_mbtiles']:
            return jsonify({'error': 'MBTiles服务不存在'}), 404
        
        return jsonify({
            'success': True,
            'service': service
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取MBTiles服务信息失败: {str(e)}")
        return jsonify({'error': f'获取MBTiles服务信息失败: {str(e)}'}), 500

@mbtiles_bp.route('/services/<int:service_id>', methods=['DELETE'])
def delete_mbtiles_service(service_id):
    """删除MBTiles服务"""
    try:
        service = raster_martin_service.get_martin_service_by_id(service_id)
        
        if not service or service['vector_type'] not in ['mbtiles', 'vector_mbtiles', 'raster_mbtiles']:
            return jsonify({'error': 'MBTiles服务不存在'}), 404
        
        success = raster_martin_service.delete_martin_service(service_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'MBTiles服务删除成功'
            }), 200
        else:
            return jsonify({'error': 'MBTiles服务删除失败'}), 500
    
    except Exception as e:
        current_app.logger.error(f"删除MBTiles服务失败: {str(e)}")
        return jsonify({'error': f'删除MBTiles服务失败: {str(e)}'}), 500

@mbtiles_bp.route('/publish/<int:file_id>', methods=['POST'])
def publish_mbtiles(file_id):
    """发布MBTiles文件为Martin服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型是否为MBTiles
        file_type = file_info.get('file_type', '').lower()
        if file_type not in ['mbtiles', 'vector.mbtiles', 'raster.mbtiles']:
            return jsonify({'error': '只能发布MBTiles文件'}), 400
        
        # 检查是否已发布
        check_sql = """
        SELECT id, file_id, vector_type FROM vector_martin_services 
        WHERE original_filename = %s AND status = 'active' AND vector_type IN ('mbtiles', 'vector_mbtiles', 'raster_mbtiles')
        """
        existing = execute_query(check_sql, (file_info['file_name'],))
        
        if existing:
            return jsonify({
                'error': '文件已发布为MBTiles服务',
                'martin_file_id': existing[0]['file_id'],
                'service_id': existing[0]['id']
            }), 400
        
        # 确定MBTiles类型
        mbtiles_type = None
        if file_type == 'vector.mbtiles':
            mbtiles_type = 'vector'
        elif file_type == 'raster.mbtiles':
            mbtiles_type = 'raster'
        
        # 发布MBTiles服务
        result = raster_martin_service.publish_mbtiles_martin(
            file_id=str(file_id),
            file_path=file_info['file_path'],
            original_filename=file_info['file_name'],
            user_id=file_info.get('user_id'),
            mbtiles_type=mbtiles_type
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'MBTiles服务发布成功',
                'service_info': result
            }), 200
        else:
            return jsonify({
                'error': f'MBTiles服务发布失败: {result.get("error", "未知错误")}'
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"发布MBTiles服务失败: {str(e)}")
        return jsonify({'error': f'发布MBTiles服务失败: {str(e)}'}), 500

@mbtiles_bp.route('/unpublish/<int:file_id>', methods=['DELETE'])
def unpublish_mbtiles(file_id):
    """取消发布MBTiles服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 查找Martin服务记录
        check_sql = """
        SELECT id, file_id FROM vector_martin_services 
        WHERE original_filename = %s AND status = 'active' AND vector_type IN ('mbtiles', 'vector_mbtiles', 'raster_mbtiles')
        """
        existing = execute_query(check_sql, (file_info['file_name'],))
        
        if not existing:
            return jsonify({'error': '文件未发布为MBTiles服务'}), 404
        
        service_id = existing[0]['id']
        
        # 删除服务
        success = raster_martin_service.delete_martin_service(service_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'MBTiles服务取消发布成功'
            }), 200
        else:
            return jsonify({'error': 'MBTiles服务取消发布失败'}), 500
    
    except Exception as e:
        current_app.logger.error(f"取消发布MBTiles服务失败: {str(e)}")
        return jsonify({'error': f'取消发布MBTiles服务失败: {str(e)}'}), 500 