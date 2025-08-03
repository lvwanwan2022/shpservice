#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户服务管理路由
提供用户服务配置的CRUD操作和服务控制功能
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import json
import time
import subprocess
import psutil
from datetime import datetime

from models.db import execute_query
from utils.snowflake import get_snowflake_id
from auth.auth_service import AuthService

# 创建蓝图
user_service_bp = Blueprint('user_service', __name__, url_prefix='/api/user-services')

# 认证装饰器
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '需要登录访问'}), 401
        
        token = auth_header.split(' ')[1]
        auth_service = AuthService()
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            return jsonify({'error': '无效的认证信息'}), 401
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

def log_service_operation(service_config_id, user_id, operation_type, status, message=None, error_details=None, execution_time=None):
    """记录服务操作日志"""
    try:
        log_id = get_snowflake_id()
        insert_sql = """
        INSERT INTO service_logs (
            id, service_config_id, user_id, operation_type, operation_status,
            log_message, error_details, execution_time_ms, ip_address, user_agent
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent', '')
        
        execute_query(insert_sql, (
            log_id, service_config_id, user_id, operation_type, status,
            message, json.dumps(error_details) if error_details else None,
            execution_time, ip_address, user_agent
        ), fetch=False)
    except Exception as e:
        print(f"记录日志失败: {e}")

# ===============================
# 服务配置管理接口
# ===============================

@user_service_bp.route('', methods=['GET'])
@require_auth
def get_user_services():
    """获取用户的服务列表"""
    try:
        user_id = request.current_user['user_id']
        service_type = request.args.get('service_type')
        status = request.args.get('status')
        
        # 构建查询条件
        where_conditions = ['user_id = %s']
        params = [user_id]
        
        if service_type:
            where_conditions.append('service_type = %s')
            params.append(service_type)
        
        if status:
            where_conditions.append('service_status = %s')
            params.append(status)
        
        where_clause = ' AND '.join(where_conditions)
        
        # 查询服务配置
        query = f"""
        SELECT 
            usc.*,
            spa.port_number as allocated_port,
            srq.max_geoserver_services,
            srq.max_martin_services,
            srq.quota_type
        FROM user_service_configs usc
        LEFT JOIN service_port_allocations spa ON usc.id = spa.service_config_id AND spa.allocation_status = 'allocated'
        LEFT JOIN system_resource_quotas srq ON usc.user_id = srq.user_id AND srq.is_active = TRUE
        WHERE {where_clause}
        ORDER BY usc.created_at DESC
        """
        
        services = execute_query(query, params)
        
        return jsonify({
            'success': True,
            'data': {
                'services': services
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取服务列表失败: {str(e)}'}), 500

@user_service_bp.route('', methods=['POST'])
@require_auth
def create_service():
    """创建新的服务配置"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['service_name', 'service_type', 'config_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证服务类型
        if data['service_type'] not in ['geoserver', 'martin']:
            return jsonify({'error': '无效的服务类型'}), 400
        
        start_time = time.time()
        service_id = get_snowflake_id()
        
        # 检查服务名称是否重复
        check_sql = """
        SELECT COUNT(*) as count FROM user_service_configs 
        WHERE user_id = %s AND service_name = %s AND service_type = %s
        """
        result = execute_query(check_sql, [user_id, data['service_name'], data['service_type']])
        if result[0]['count'] > 0:
            return jsonify({'error': '服务名称已存在'}), 400
        
        # 分配端口
        try:
            port_sql = "SELECT allocate_available_port(%s, %s) as port"
            port_result = execute_query(port_sql, [user_id, service_id])
            allocated_port = port_result[0]['port']
        except Exception as e:
            return jsonify({'error': f'端口分配失败: {str(e)}'}), 500
        
        # 创建服务配置
        insert_sql = """
        INSERT INTO user_service_configs (
            id, user_id, service_name, service_type, service_status,
            config_data, port_number, description, is_default, auto_start
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """
        
        config_data = data['config_data']
        # 将端口信息添加到配置中
        config_data['port'] = allocated_port
        
        service = execute_query(insert_sql, (
            service_id, user_id, data['service_name'], data['service_type'], 'stopped',
            json.dumps(config_data), allocated_port, 
            data.get('description', ''), data.get('is_default', False),
            data.get('auto_start', False)
        ))
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # 记录操作日志
        log_service_operation(
            service_id, user_id, 'create', 'success',
            f'创建{data["service_type"]}服务: {data["service_name"]}',
            None, execution_time
        )
        
        return jsonify({
            'success': True,
            'data': service[0],
            'message': '服务创建成功'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'创建服务失败: {str(e)}'}), 500

@user_service_bp.route('/<int:service_id>/start', methods=['POST'])
@require_auth
def start_service(service_id):
    """启动服务"""
    try:
        user_id = request.current_user['user_id']
        
        # 获取服务信息
        service_sql = "SELECT * FROM user_service_configs WHERE id = %s AND user_id = %s"
        services = execute_query(service_sql, [service_id, user_id])
        
        if not services:
            return jsonify({'error': '服务不存在或无权限访问'}), 404
        
        service = services[0]
        
        if service['service_status'] == 'running':
            return jsonify({'error': '服务已在运行中'}), 400
        
        # 更新状态为启动中
        update_sql = "UPDATE user_service_configs SET service_status = 'starting' WHERE id = %s"
        execute_query(update_sql, [service_id], fetch=False)
        
        # 这里可以添加实际的服务启动逻辑
        # 模拟启动成功
        time.sleep(1)
        
        # 更新状态为运行中
        update_sql = "UPDATE user_service_configs SET service_status = 'running' WHERE id = %s"
        execute_query(update_sql, [service_id], fetch=False)
        
        log_service_operation(
            service_id, user_id, 'start', 'success',
            f'启动服务成功: {service["service_name"]}'
        )
        
        return jsonify({
            'success': True,
            'message': '服务启动成功',
            'data': {
                'service_id': service_id,
                'status': 'running',
                'port': service['port_number']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'启动服务失败: {str(e)}'}), 500

@user_service_bp.route('/<int:service_id>/stop', methods=['POST'])
@require_auth
def stop_service(service_id):
    """停止服务"""
    try:
        user_id = request.current_user['user_id']
        
        # 获取服务信息
        service_sql = "SELECT * FROM user_service_configs WHERE id = %s AND user_id = %s"
        services = execute_query(service_sql, [service_id, user_id])
        
        if not services:
            return jsonify({'error': '服务不存在或无权限访问'}), 404
        
        service = services[0]
        
        if service['service_status'] == 'stopped':
            return jsonify({'error': '服务已停止'}), 400
        
        # 更新状态为停止中
        update_sql = "UPDATE user_service_configs SET service_status = 'stopping' WHERE id = %s"
        execute_query(update_sql, [service_id], fetch=False)
        
        # 这里可以添加实际的服务停止逻辑
        # 模拟停止成功
        time.sleep(1)
        
        # 更新状态为已停止
        update_sql = "UPDATE user_service_configs SET service_status = 'stopped' WHERE id = %s"
        execute_query(update_sql, [service_id], fetch=False)
        
        log_service_operation(
            service_id, user_id, 'stop', 'success',
            f'停止服务成功: {service["service_name"]}'
        )
        
        return jsonify({
            'success': True,
            'message': '服务停止成功',
            'data': {
                'service_id': service_id,
                'status': 'stopped'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'停止服务失败: {str(e)}'}), 500

@user_service_bp.route('/<int:service_id>/status', methods=['GET'])
@require_auth
def get_service_status(service_id):
    """获取服务状态"""
    try:
        user_id = request.current_user['user_id']
        
        # 获取服务信息
        service_sql = """
        SELECT usc.*, spa.port_number as allocated_port
        FROM user_service_configs usc
        LEFT JOIN service_port_allocations spa ON usc.id = spa.service_config_id 
        WHERE usc.id = %s AND usc.user_id = %s
        """
        services = execute_query(service_sql, [service_id, user_id])
        
        if not services:
            return jsonify({'error': '服务不存在或无权限访问'}), 404
        
        service = services[0]
        
        return jsonify({
            'success': True,
            'data': {
                'service_id': service_id,
                'service_name': service['service_name'],
                'service_type': service['service_type'],
                'status': service['service_status'],
                'port': service['port_number'],
                'last_started_at': service['last_started_at'],
                'last_stopped_at': service['last_stopped_at']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取服务状态失败: {str(e)}'}), 500

@user_service_bp.route('/resource-usage', methods=['GET'])
@require_auth
def get_resource_usage():
    """获取用户资源使用情况"""
    try:
        user_id = request.current_user['user_id']
        
        # 获取用户配额和使用情况
        usage_sql = """
        SELECT 
            u.username,
            srq.max_geoserver_services,
            srq.max_martin_services,
            srq.max_memory_mb,
            srq.max_storage_mb,
            srq.quota_type,
            COUNT(CASE WHEN usc.service_type = 'geoserver' THEN 1 END) as used_geoserver,
            COUNT(CASE WHEN usc.service_type = 'martin' THEN 1 END) as used_martin,
            COUNT(CASE WHEN usc.service_status = 'running' THEN 1 END) as running_services,
            COUNT(usc.id) as total_services
        FROM users u
        LEFT JOIN system_resource_quotas srq ON u.id = srq.user_id AND srq.is_active = TRUE
        LEFT JOIN user_service_configs usc ON u.id = usc.user_id
        WHERE u.id = %s
        GROUP BY u.id, u.username, srq.max_geoserver_services, srq.max_martin_services, 
                 srq.max_memory_mb, srq.max_storage_mb, srq.quota_type
        """
        
        usage_data = execute_query(usage_sql, [user_id])
        
        if not usage_data:
            return jsonify({'error': '用户资源配额未配置'}), 404
        
        data = usage_data[0]
        
        return jsonify({
            'success': True,
            'data': {
                'quota': {
                    'max_geoserver_services': data['max_geoserver_services'],
                    'max_martin_services': data['max_martin_services'],
                    'max_memory_mb': data['max_memory_mb'],
                    'max_storage_mb': data['max_storage_mb'],
                    'quota_type': data['quota_type']
                },
                'usage': {
                    'used_geoserver': data['used_geoserver'],
                    'used_martin': data['used_martin'],
                    'running_services': data['running_services'],
                    'total_services': data['total_services']
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取资源使用情况失败: {str(e)}'}), 500 