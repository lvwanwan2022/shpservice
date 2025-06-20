#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一Martin服务路由
提供GeoJSON和SHP Martin服务的统一API接口
"""

from flask import Blueprint, jsonify, request, current_app
from models.db import execute_query
import json
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
martin_service_bp = Blueprint('martin_service', __name__)


@martin_service_bp.route('/martin-services/list', methods=['GET'])
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


@martin_service_bp.route('/martin-services/search', methods=['GET'])
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
                "id": str(service['id']),
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
                "database_record_id": str(service['id'])
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


@martin_service_bp.route('/martin-services/<int:service_id>', methods=['GET'])
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


@martin_service_bp.route('/martin-services/<int:service_id>/style', methods=['POST'])
def update_martin_service_style(service_id):
    """更新Martin服务的样式配置"""
    try:
        data = request.json
        if not data or 'style_config' not in data:
            return jsonify({
                'success': False,
                'error': '缺少样式配置参数',
                'error_type': 'missing_parameter'
            }), 400
        
        style_config = data['style_config']
        
        # 检查Martin服务是否存在
        check_sql = """
        SELECT id, vector_type, original_filename, style FROM vector_martin_services
        WHERE id = %s AND status = 'active'
        """
        result = execute_query(check_sql, (service_id,))
        
        if not result:
            return jsonify({
                'success': False,
                'error': f'Martin服务ID {service_id} 不存在',
                'error_type': 'not_found'
            }), 404
        
        service = result[0]
        current_app.logger.info(f"开始更新Martin服务 {service_id} 的样式，类型: {service['vector_type']}")
        
        # 将样式配置保存到style字段（所有类型统一使用）
        update_sql = """
        UPDATE vector_martin_services 
        SET style = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        # 转换为JSON字符串格式保存
        style_json = json.dumps(style_config, ensure_ascii=False)
        execute_query(update_sql, (style_json, service_id), fetch=False)
        
        current_app.logger.info(f"✅ Martin服务样式更新成功: {service_id}")
        
        return jsonify({
            'success': True,
            'message': '样式更新成功',
            'data': {
                'service_id': service_id,
                'service_type': service['vector_type'],
                'original_filename': service['original_filename'],
                'style_config': style_config
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"更新Martin服务样式时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'样式更新失败: {str(e)}',
            'error_type': 'internal_error'
        }), 500


@martin_service_bp.route('/martin-services/<int:service_id>/style', methods=['GET'])
def get_martin_service_style(service_id):
    """获取Martin服务的样式配置"""
    try:
        # 检查Martin服务是否存在并获取样式配置
        sql = """
        SELECT id, vector_type, original_filename, style, vector_info FROM vector_martin_services
        WHERE id = %s AND status = 'active'
        """
        
        result = execute_query(sql, (service_id,))
        if not result:
            return jsonify({
                'success': False,
                'error': f'Martin服务ID {service_id} 不存在',
                'error_type': 'not_found'
            }), 404
        
        service = result[0]
        current_app.logger.info(f"获取Martin服务 {service_id} 的样式，类型: {service['vector_type']}")
        
        # 解析样式配置，优先从style字段读取
        style_config = {}
        
        # 首先从style字段读取（统一的样式存储字段）
        if service['style']:
            try:
                if isinstance(service['style'], str):
                    style_config = json.loads(service['style'])
                else:
                    style_config = service['style']
                current_app.logger.info(f"从style字段读取到样式配置: {style_config}")
            except (json.JSONDecodeError, TypeError) as e:
                current_app.logger.warning(f"样式配置解析失败: {str(e)}")
                style_config = {}
        
        # 如果style字段为空，但是是DXF类型，尝试从vector_info中读取（向后兼容）
        if not style_config and service['vector_type'] == 'dxf' and service['vector_info']:
            try:
                vector_info = service['vector_info'] if isinstance(service['vector_info'], dict) else json.loads(service['vector_info'])
                style_config = vector_info.get('style_config', {})
                current_app.logger.info(f"从vector_info中读取到DXF样式配置: {style_config}")
            except (json.JSONDecodeError, TypeError) as e:
                current_app.logger.warning(f"DXF vector_info解析失败: {str(e)}")
        
        # 如果没有样式配置，提供默认配置
        if not style_config:
            style_config = {}
            current_app.logger.info(f"使用默认样式配置")
        
        return jsonify({
            'success': True,
            'data': {
                'service_id': service_id,
                'service_type': service['vector_type'],
                'original_filename': service['original_filename'],
                'style_config': style_config,
                'file_type': service['vector_type']  # 兼容前端期望的file_type字段
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取Martin服务样式时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取样式失败: {str(e)}',
            'error_type': 'internal_error'
        }), 500


@martin_service_bp.route('/martin-services/<int:service_id>/apply-style', methods=['POST'])
def apply_martin_service_style(service_id):
    """应用Martin服务的样式配置（保存样式并重新发布服务）"""
    try:
        data = request.json
        if not data or 'style_config' not in data:
            return jsonify({
                'success': False,
                'error': '缺少样式配置参数',
                'error_type': 'missing_parameter'
            }), 400
        
        style_config = data['style_config']
        
        # 检查Martin服务是否存在
        check_sql = """
        SELECT id, vector_type, original_filename, style, table_name FROM vector_martin_services
        WHERE id = %s AND status = 'active'
        """
        result = execute_query(check_sql, (service_id,))
        
        if not result:
            return jsonify({
                'success': False,
                'error': f'Martin服务ID {service_id} 不存在',
                'error_type': 'not_found'
            }), 404
        
        service = result[0]
        current_app.logger.info(f"开始应用Martin服务 {service_id} 的样式，类型: {service['vector_type']}")
        
        # 1. 保存样式配置到数据库
        update_sql = """
        UPDATE vector_martin_services 
        SET style = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        # 转换为JSON字符串格式保存
        style_json = json.dumps(style_config, ensure_ascii=False)
        execute_query(update_sql, (style_json, service_id), fetch=False)
        
        current_app.logger.info(f"✅ Martin服务样式配置已保存: {service_id}")
        
        # 2. 触发Martin服务重新发布（如果需要）
        # 对于DXF图层，样式是在前端VectorGrid中应用的，不需要重新发布Martin服务
        # 但我们可以在这里做一些额外的处理，比如更新缓存等
        
        # 3. 返回成功响应
        return jsonify({
            'success': True,
            'message': '样式已应用成功',
            'data': {
                'service_id': service_id,
                'service_type': service['vector_type'],
                'original_filename': service['original_filename'],
                'table_name': service['table_name'],
                'style_config': style_config,
                'applied_at': 'now'
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"应用Martin服务样式时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'样式应用失败: {str(e)}',
            'error_type': 'internal_error'
        }), 500


@martin_service_bp.route('/martin-services/style-templates', methods=['GET'])
def get_style_templates():
    """获取Martin服务样式模板"""
    try:
        templates = {
            '默认': {
                'description': '默认样式配置',
                'point': {
                    'color': '#FF0000',
                    'size': 6,
                    'shape': 'circle',
                    'opacity': 1.0
                },
                'line': {
                    'color': '#0000FF',
                    'width': 2,
                    'style': 'solid',
                    'opacity': 1.0
                },
                'polygon': {
                    'fillColor': '#00FF00',
                    'fillOpacity': 0.3,
                    'outlineColor': '#000000',
                    'outlineWidth': 1,
                    'opacity': 1.0
                }
            },
            '建筑规划': {
                'description': '适用于建筑和规划图纸',
                'point': {
                    'color': '#8B4513',
                    'size': 8,
                    'shape': 'circle',
                    'opacity': 1.0
                },
                'line': {
                    'color': '#8B4513',
                    'width': 2,
                    'style': 'solid',
                    'opacity': 1.0
                },
                'polygon': {
                    'fillColor': '#DEB887',
                    'fillOpacity': 0.7,
                    'outlineColor': '#8B4513',
                    'outlineWidth': 1,
                    'opacity': 1.0
                }
            },
            '道路交通': {
                'description': '适用于道路和交通设施图',
                'point': {
                    'color': '#696969',
                    'size': 6,
                    'shape': 'circle',
                    'opacity': 1.0
                },
                'line': {
                    'color': '#696969',
                    'width': 3,
                    'style': 'solid',
                    'opacity': 1.0
                },
                'polygon': {
                    'fillColor': '#D3D3D3',
                    'fillOpacity': 0.8,
                    'outlineColor': '#696969',
                    'outlineWidth': 1,
                    'opacity': 1.0
                }
            },
            '地形地物': {
                'description': '适用于地形图和地物标注',
                'point': {
                    'color': '#228B22',
                    'size': 6,
                    'shape': 'circle',
                    'opacity': 1.0
                },
                'line': {
                    'color': '#228B22',
                    'width': 2,
                    'style': 'solid',
                    'opacity': 1.0
                },
                'polygon': {
                    'fillColor': '#90EE90',
                    'fillOpacity': 0.5,
                    'outlineColor': '#228B22',
                    'outlineWidth': 1,
                    'opacity': 1.0
                }
            },
            '水系': {
                'description': '适用于水系和水利设施',
                'point': {
                    'color': '#0000FF',
                    'size': 6,
                    'shape': 'circle',
                    'opacity': 1.0
                },
                'line': {
                    'color': '#0000FF',
                    'width': 2,
                    'style': 'solid',
                    'opacity': 1.0
                },
                'polygon': {
                    'fillColor': '#87CEEB',
                    'fillOpacity': 0.6,
                    'outlineColor': '#0000FF',
                    'outlineWidth': 1,
                    'opacity': 1.0
                }
            },
            '边界线': {
                'description': '适用于行政边界和地块边界',
                'point': {
                    'color': '#FF0000',
                    'size': 6,
                    'shape': 'circle',
                    'opacity': 1.0
                },
                'line': {
                    'color': '#FF0000',
                    'width': 2,
                    'style': 'dashed',
                    'opacity': 1.0
                },
                'polygon': {
                    'fillColor': '#FFE4E1',
                    'fillOpacity': 0.3,
                    'outlineColor': '#FF0000',
                    'outlineWidth': 2,
                    'opacity': 1.0
                }
            }
        }
        
        return jsonify({
            'success': True,
            'templates': templates
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取样式模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取样式模板失败: {str(e)}',
            'error_type': 'internal_error'
        }), 500


@martin_service_bp.route('/martin-services/test', methods=['GET'])
def test_martin_services():
    """测试Martin服务查询"""
    try:
        # 查询所有Martin服务
        all_sql = "SELECT id, vector_type, original_filename, status FROM vector_martin_services ORDER BY id"
        all_result = execute_query(all_sql)
        
        # 查询active服务
        active_sql = "SELECT id, vector_type, original_filename FROM vector_martin_services WHERE status = 'active' ORDER BY id"
        active_result = execute_query(active_sql)
        
        return jsonify({
            'success': True,
            'all_services': all_result,
            'active_services': active_result,
            'total_count': len(all_result),
            'active_count': len(active_result)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'测试查询失败: {str(e)}',
            'error_type': 'database_error'
        }), 500 