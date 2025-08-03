#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户服务连接管理路由 - 简化版
只提供外部服务连接的CRUD操作和连接测试功能
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import json
import requests
from requests.auth import HTTPBasicAuth

from models.user_service_db import (
    get_user_connections, create_service_connection, 
    update_connection_test_result, get_default_connection
)
from models.db import execute_query
from utils.snowflake import get_snowflake_id
from auth.auth_service import AuthService

# 创建蓝图
service_connection_bp = Blueprint('service_connection', __name__, url_prefix='/api/service-connections')

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

# ===============================
# 服务连接CRUD接口
# ===============================

@service_connection_bp.route('', methods=['GET'])
@require_auth
def get_connections():
    """获取用户的服务连接列表"""
    try:
        user_id = request.current_user['user_id']
        service_type = request.args.get('service_type')
        is_active = request.args.get('is_active')
        
        # 转换is_active参数
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        
        connections = get_user_connections(user_id, service_type, is_active)
        
        # 隐藏敏感信息
        for conn in connections:
            if 'connection_config' in conn and conn['connection_config']:
                config = json.loads(conn['connection_config']) if isinstance(conn['connection_config'], str) else conn['connection_config']
                # 隐藏密码和API密钥
                if 'password' in config:
                    config['password'] = '***'
                if 'api_key' in config:
                    config['api_key'] = '***'
                conn['connection_config'] = config
        
        return jsonify({
            'success': True,
            'data': connections
        })
        
    except Exception as e:
        return jsonify({'error': f'获取连接列表失败: {str(e)}'}), 500

@service_connection_bp.route('', methods=['POST'])
@require_auth
def create_connection():
    """创建新的服务连接"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['service_name', 'service_type', 'server_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证服务类型
        if data['service_type'] not in ['geoserver', 'martin']:
            return jsonify({'error': '无效的服务类型'}), 400
        
        # 构建连接配置
        connection_config = {
            'server_url': data['server_url']
        }
        
        if data['service_type'] == 'geoserver':
            if not data.get('username') or not data.get('password'):
                return jsonify({'error': 'GeoServer连接需要用户名和密码'}), 400
            connection_config.update({
                'username': data['username'],
                'password': data['password'],
                'workspace': data.get('workspace', 'default')
            })
        elif data['service_type'] == 'martin':
            if data.get('api_key'):
                connection_config['api_key'] = data['api_key']
            if data.get('database_url'):
                connection_config['database_url'] = data['database_url']
        
        # 创建连接
        connection = create_service_connection(
            user_id=user_id,
            service_name=data['service_name'],
            service_type=data['service_type'],
            server_url=data['server_url'],
            connection_config=connection_config,
            description=data.get('description'),
            is_default=data.get('is_default', False)
        )
        
        if connection:
            return jsonify({
                'success': True,
                'data': connection,
                'message': '服务连接创建成功'
            }), 201
        else:
            return jsonify({'error': '创建连接失败'}), 500
        
    except Exception as e:
        return jsonify({'error': f'创建连接失败: {str(e)}'}), 500

@service_connection_bp.route('/<int:connection_id>', methods=['PUT'])
@require_auth
def update_connection(connection_id):
    """更新服务连接"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        # 验证连接所有权
        check_sql = "SELECT * FROM user_service_connections WHERE id = %s AND user_id = %s"
        existing = execute_query(check_sql, [connection_id, user_id])
        
        if not existing:
            return jsonify({'error': '连接不存在或无权限访问'}), 404
        
        # 构建更新字段
        update_fields = []
        params = []
        
        if 'service_name' in data:
            update_fields.append('service_name = %s')
            params.append(data['service_name'])
        
        if 'server_url' in data:
            update_fields.append('server_url = %s')
            params.append(data['server_url'])
        
        if 'description' in data:
            update_fields.append('description = %s')
            params.append(data['description'])
        
        if 'is_default' in data:
            update_fields.append('is_default = %s')
            params.append(data['is_default'])
        
        if 'is_active' in data:
            update_fields.append('is_active = %s')
            params.append(data['is_active'])
        
        # 更新连接配置
        if any(key in data for key in ['username', 'password', 'workspace', 'api_key', 'database_url']):
            current_config = json.loads(existing[0]['connection_config'])
            
            if 'username' in data:
                current_config['username'] = data['username']
            if 'password' in data:
                current_config['password'] = data['password']
            if 'workspace' in data:
                current_config['workspace'] = data['workspace']
            if 'api_key' in data:
                current_config['api_key'] = data['api_key']
            if 'database_url' in data:
                current_config['database_url'] = data['database_url']
            
            update_fields.append('connection_config = %s')
            params.append(json.dumps(current_config))
        
        if not update_fields:
            return jsonify({'error': '没有需要更新的字段'}), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.extend([connection_id, user_id])
        
        update_sql = f"""
        UPDATE user_service_connections 
        SET {', '.join(update_fields)}
        WHERE id = %s AND user_id = %s
        RETURNING *
        """
        
        result = execute_query(update_sql, params)
        
        if result:
            return jsonify({
                'success': True,
                'data': result[0],
                'message': '连接更新成功'
            })
        else:
            return jsonify({'error': '更新失败'}), 500
        
    except Exception as e:
        return jsonify({'error': f'更新连接失败: {str(e)}'}), 500

@service_connection_bp.route('/<int:connection_id>', methods=['DELETE'])
@require_auth
def delete_connection(connection_id):
    """删除服务连接"""
    try:
        user_id = request.current_user['user_id']
        
        # 验证连接所有权
        check_sql = "SELECT service_name FROM user_service_connections WHERE id = %s AND user_id = %s"
        existing = execute_query(check_sql, [connection_id, user_id])
        
        if not existing:
            return jsonify({'error': '连接不存在或无权限访问'}), 404
        
        service_name = existing[0]['service_name']
        
        # 删除连接
        delete_sql = "DELETE FROM user_service_connections WHERE id = %s AND user_id = %s"
        execute_query(delete_sql, [connection_id, user_id], fetch=False)
        
        return jsonify({
            'success': True,
            'message': f'连接 "{service_name}" 删除成功'
        })
        
    except Exception as e:
        return jsonify({'error': f'删除连接失败: {str(e)}'}), 500

# ===============================
# 连接测试接口
# ===============================

@service_connection_bp.route('/test', methods=['POST'])
@require_auth
def test_connection():
    """测试服务连接"""
    try:
        data = request.get_json()
        service_type = data.get('service_type')
        server_url = data.get('server_url')
        
        if not service_type or not server_url:
            return jsonify({'error': '缺少必要参数'}), 400
        
        if service_type == 'geoserver':
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'GeoServer需要用户名和密码'}), 400
            
            result = test_geoserver_connection(server_url, username, password)
        elif service_type == 'martin':
            api_key = data.get('api_key')
            result = test_martin_connection(server_url, api_key)
        else:
            return jsonify({'error': '不支持的服务类型'}), 400
        
        # 如果是更新已有连接的测试，保存测试结果
        connection_id = data.get('connection_id')
        if connection_id:
            update_connection_test_result(
                connection_id, 
                'success' if result['success'] else 'failed',
                result['message']
            )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result.get('data', {})
            })
        else:
            return jsonify({'error': result['message']}), 400
        
    except Exception as e:
        return jsonify({'error': f'连接测试失败: {str(e)}'}), 500

@service_connection_bp.route('/<int:connection_id>/test', methods=['POST'])
@require_auth
def test_existing_connection(connection_id):
    """测试现有连接"""
    try:
        user_id = request.current_user['user_id']
        
        # 获取连接信息
        query = "SELECT * FROM user_service_connections WHERE id = %s AND user_id = %s"
        connections = execute_query(query, [connection_id, user_id])
        
        if not connections:
            return jsonify({'error': '连接不存在或无权限访问'}), 404
        
        connection = connections[0]
        config = json.loads(connection['connection_config'])
        
        # 执行测试
        if connection['service_type'] == 'geoserver':
            result = test_geoserver_connection(
                config['server_url'],
                config['username'],
                config['password']
            )
        elif connection['service_type'] == 'martin':
            result = test_martin_connection(
                config['server_url'],
                config.get('api_key')
            )
        else:
            return jsonify({'error': '不支持的服务类型'}), 400
        
        # 更新测试结果
        update_connection_test_result(
            connection_id,
            'success' if result['success'] else 'failed',
            result['message']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result.get('data', {})
            })
        else:
            return jsonify({'error': result['message']}), 400
        
    except Exception as e:
        return jsonify({'error': f'测试连接失败: {str(e)}'}), 500

# ===============================
# 连接测试函数
# ===============================

def test_geoserver_connection(server_url, username, password):
    """测试GeoServer连接"""
    try:
        # 构建REST API URL
        if not server_url.endswith('/'):
            server_url += '/'
        
        workspaces_url = f"{server_url}rest/workspaces.json"
        
        response = requests.get(
            workspaces_url,
            auth=HTTPBasicAuth(username, password),
            timeout=10
        )
        
        if response.status_code == 200:
            workspaces_data = response.json()
            workspace_count = len(workspaces_data.get('workspaces', {}).get('workspace', []))
            
            return {
                'success': True,
                'message': f'GeoServer连接成功，发现 {workspace_count} 个工作空间',
                'data': {
                    'workspace_count': workspace_count,
                    'server_info': response.headers.get('Server', 'Unknown')
                }
            }
        elif response.status_code == 401:
            return {'success': False, 'message': '认证失败，请检查用户名和密码'}
        else:
            return {'success': False, 'message': f'连接失败，HTTP状态码: {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '连接超时，请检查服务地址'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': '无法连接到服务器，请检查地址和网络'}
    except Exception as e:
        return {'success': False, 'message': f'连接测试失败: {str(e)}'}

def test_martin_connection(server_url, api_key=None):
    """测试Martin连接"""
    try:
        if not server_url.endswith('/'):
            server_url += '/'
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # 尝试健康检查
        try:
            health_url = f"{server_url}health"
            health_response = requests.get(health_url, headers=headers, timeout=10)
            if health_response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Martin服务连接成功',
                    'data': health_response.json()
                }
        except:
            pass
        
        # 尝试目录接口
        catalog_url = f"{server_url}catalog"
        catalog_response = requests.get(catalog_url, headers=headers, timeout=10)
        
        if catalog_response.status_code == 200:
            catalog_data = catalog_response.json()
            table_count = len(catalog_data) if isinstance(catalog_data, list) else 0
            
            return {
                'success': True,
                'message': f'Martin服务连接成功，发现 {table_count} 个数据源',
                'data': {'table_count': table_count}
            }
        elif catalog_response.status_code == 401:
            return {'success': False, 'message': '认证失败，请检查API密钥'}
        else:
            return {'success': False, 'message': f'连接失败，HTTP状态码: {catalog_response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '连接超时，请检查服务地址'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': '无法连接到服务器，请检查地址和网络'}
    except Exception as e:
        return {'success': False, 'message': f'连接测试失败: {str(e)}'}

# ===============================
# 工具接口
# ===============================

@service_connection_bp.route('/defaults', methods=['GET'])
@require_auth
def get_default_connections():
    """获取用户的默认连接"""
    try:
        user_id = request.current_user['user_id']
        
        geoserver_default = get_default_connection(user_id, 'geoserver')
        martin_default = get_default_connection(user_id, 'martin')
        
        return jsonify({
            'success': True,
            'data': {
                'geoserver': geoserver_default,
                'martin': martin_default
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取默认连接失败: {str(e)}'}), 500 