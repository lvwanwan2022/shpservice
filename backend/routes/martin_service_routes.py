#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一Martin服务路由
提供GeoJSON和SHP Martin服务的统一API接口
"""

from flask import Blueprint, jsonify, request, current_app
from models.db import execute_query
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
martin_service_bp = Blueprint('martin_service', __name__, url_prefix='/api/martin-services')


@martin_service_bp.route('/list', methods=['GET'])
def get_all_martin_services():
    """获取所有Martin服务列表（包括GeoJSON和SHP）"""
    try:
        # 获取查询参数
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        user_id = request.args.get('user_id')
        vector_type = request.args.get('vector_type')  # 'geojson' 或 'shp'
        
        # 构建查询条件
        where_conditions = ["status = 'active'"]
        params = []
        
        if user_id:
            where_conditions.append("user_id = %s")
            params.append(user_id)
        
        if vector_type and vector_type in ['geojson', 'shp']:
            where_conditions.append("vector_type = %s")
            params.append(vector_type)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 查询统一的Vector Martin服务表
        sql = f"""
        SELECT 
            vector_type as service_type,
            id,
            file_id,
            original_filename,
            table_name,
            mvt_url,
            tilejson_url,
            style,
            status,
            user_id,
            created_at,
            updated_at
        FROM vector_martin_services
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        # 添加分页参数
        query_params = params + [limit, offset]
        
        services = execute_query(sql, tuple(query_params))
        
        # 获取总数
        count_sql = f"""
        SELECT COUNT(*) as total FROM vector_martin_services
        {where_clause}
        """
        
        total_result = execute_query(count_sql, tuple(params))
        total = total_result[0]['total'] if total_result else 0
        
        # 处理结果，添加完整的服务信息
        result_services = []
        for service in services:
            service_info = {
                "service_type": service['service_type'],
                "id": service['id'],
                "file_id": service['file_id'],
                "original_filename": service['original_filename'],
                "table_name": service['table_name'],
                "mvt_url": service['mvt_url'],
                "tilejson_url": service['tilejson_url'],
                "style": service['style'],
                "status": service['status'],
                "user_id": service['user_id'],
                "created_at": service['created_at'].isoformat() if service['created_at'] else None,
                "updated_at": service['updated_at'].isoformat() if service['updated_at'] else None,
                "database_record_id": service['id']  # 为兼容性添加
            }
            result_services.append(service_info)
        
        return jsonify({
            'success': True,
            'services': result_services,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"获取Martin服务列表失败: {str(e)}")
        return jsonify({'error': f'获取Martin服务列表失败: {str(e)}'}), 500


@martin_service_bp.route('/search', methods=['GET'])
def search_martin_services():
    """搜索Martin服务"""
    try:
        # 获取搜索参数
        file_id = request.args.get('file_id')
        original_filename = request.args.get('original_filename')
        vector_type = request.args.get('vector_type')  # 'geojson' 或 'shp'
        
        if not file_id and not original_filename:
            return jsonify({'error': '必须提供file_id或original_filename参数'}), 400
        
        # 构建查询条件
        where_conditions = ["status = 'active'"]
        params = []
        
        if file_id:
            where_conditions.append("file_id = %s")
            params.append(file_id)
        elif original_filename:
            where_conditions.append("original_filename = %s")
            params.append(original_filename)
        
        if vector_type and vector_type in ['geojson', 'shp']:
            where_conditions.append("vector_type = %s")
            params.append(vector_type)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 搜索统一的Vector Martin服务表
        sql = f"""
        SELECT 
            vector_type as service_type,
            id,
            file_id,
            original_filename,
            table_name,
            mvt_url,
            tilejson_url,
            style,
            status,
            user_id,
            created_at,
            updated_at
        FROM vector_martin_services
        {where_clause}
        ORDER BY created_at DESC
        """
        
        services = execute_query(sql, tuple(params))
        
        # 处理结果
        result_services = []
        for service in services:
            service_info = {
                "service_type": service['service_type'],
                "id": service['id'],
                "file_id": service['file_id'],
                "original_filename": service['original_filename'],
                "table_name": service['table_name'],
                "mvt_url": service['mvt_url'],
                "tilejson_url": service['tilejson_url'],
                "style": service['style'],
                "status": service['status'],
                "user_id": service['user_id'],
                "created_at": service['created_at'].isoformat() if service['created_at'] else None,
                "updated_at": service['updated_at'].isoformat() if service['updated_at'] else None,
                "database_record_id": service['id']
            }
            result_services.append(service_info)
        
        return jsonify({
            'success': True,
            'services': result_services,
            'total': len(result_services)
        }), 200
        
    except Exception as e:
        logger.error(f"搜索Martin服务失败: {str(e)}")
        return jsonify({'error': f'搜索Martin服务失败: {str(e)}'}), 500


@martin_service_bp.route('/<int:service_id>', methods=['GET'])
def get_martin_service_by_id(service_id):
    """根据ID获取Martin服务详细信息"""
    try:
        sql = """
        SELECT 
            vector_type as service_type,
            id,
            file_id,
            original_filename,
            table_name,
            service_url,
            mvt_url,
            tilejson_url,
            style,
            vector_info,
            postgis_info,
            status,
            user_id,
            created_at,
            updated_at
        FROM vector_martin_services
        WHERE id = %s AND status = 'active'
        """
        
        result = execute_query(sql, (service_id,))
        
        if not result:
            return jsonify({'error': 'Martin服务不存在'}), 404
        
        service = result[0]
        
        service_info = {
            "service_type": service['service_type'],
            "id": service['id'],
            "file_id": service['file_id'],
            "original_filename": service['original_filename'],
            "table_name": service['table_name'],
            "service_url": service['service_url'],
            "mvt_url": service['mvt_url'],
            "tilejson_url": service['tilejson_url'],
            "style": service['style'],
            "vector_info": service['vector_info'],
            "postgis_info": service['postgis_info'],
            "status": service['status'],
            "user_id": service['user_id'],
            "created_at": service['created_at'].isoformat() if service['created_at'] else None,
            "updated_at": service['updated_at'].isoformat() if service['updated_at'] else None
        }
        
        return jsonify({
            'success': True,
            'service': service_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取Martin服务详情失败: {str(e)}")
        return jsonify({'error': f'获取Martin服务详情失败: {str(e)}'}), 500 