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
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("user_id = %s")
            params.append(user_id)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 查询GeoJSON Martin服务
        geojson_sql = f"""
        SELECT 
            'geojson' as service_type,
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
        FROM geojson_martin_services
        {where_clause} AND status = 'active'
        """
        
        # 查询SHP Martin服务
        shp_sql = f"""
        SELECT 
            'shp' as service_type,
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
        FROM shp_martin_services
        {where_clause} AND status = 'active'
        """
        
        # 合并查询
        union_sql = f"""
        ({geojson_sql})
        UNION ALL
        ({shp_sql})
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        # 添加分页参数
        query_params = params + params + [limit, offset]
        
        services = execute_query(union_sql, tuple(query_params))
        
        # 获取总数
        count_sql = f"""
        SELECT COUNT(*) as total FROM (
            ({geojson_sql})
            UNION ALL
            ({shp_sql})
        ) as all_services
        """
        
        count_params = params + params
        total_result = execute_query(count_sql, tuple(count_params))
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
        service_type = request.args.get('service_type')  # 'geojson' 或 'shp'
        
        if not file_id and not original_filename:
            return jsonify({'error': '必须提供file_id或original_filename参数'}), 400
        
        services = []
        
        # 根据service_type决定查询哪些表
        search_geojson = service_type in [None, 'geojson']
        search_shp = service_type in [None, 'shp']
        
        if search_geojson:
            # 搜索GeoJSON Martin服务
            if file_id:
                geojson_sql = """
                SELECT 'geojson' as service_type, * FROM geojson_martin_services
                WHERE file_id = %s AND status = 'active'
                """
                geojson_result = execute_query(geojson_sql, (file_id,))
            else:
                geojson_sql = """
                SELECT 'geojson' as service_type, * FROM geojson_martin_services
                WHERE original_filename = %s AND status = 'active'
                """
                geojson_result = execute_query(geojson_sql, (original_filename,))
            
            services.extend(geojson_result)
        
        if search_shp:
            # 搜索SHP Martin服务
            if file_id:
                shp_sql = """
                SELECT 'shp' as service_type, * FROM shp_martin_services
                WHERE file_id = %s AND status = 'active'
                """
                shp_result = execute_query(shp_sql, (file_id,))
            else:
                shp_sql = """
                SELECT 'shp' as service_type, * FROM shp_martin_services
                WHERE original_filename = %s AND status = 'active'
                """
                shp_result = execute_query(shp_sql, (original_filename,))
            
            services.extend(shp_result)
        
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
                "database_record_id": service['id']  # 为兼容性添加
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