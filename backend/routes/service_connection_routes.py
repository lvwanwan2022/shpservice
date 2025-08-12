#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户服务连接管理路由 - 简化版 + 加密功能
只提供外部服务连接的CRUD操作和连接测试功能
集成数据加密保护敏感信息
"""

from flask import Blueprint, request, jsonify
import json
import requests
from requests.auth import HTTPBasicAuth

from models.user_service_db import (
    get_user_connections, create_service_connection, 
    update_connection_test_result, get_default_connection
)
from models.db import execute_query
from utils.snowflake import get_snowflake_id
from auth.auth_service import AuthService, require_auth, get_current_user
# 🔒 引入加密服务
from utils.encryption import service_connection_encryption, encryption_service

# 创建蓝图
service_connection_bp = Blueprint('service_connection', __name__, url_prefix='/api/service-connections')

# 使用统一的认证装饰器，移除自定义版本

# ===============================
# 🔒 加密工具函数
# ===============================

def encrypt_request_data(data):
    """加密请求中的敏感数据"""
    try:
        # 处理RSA加密的敏感字段
        encrypted_fields = {}
        sensitive_fields = ['password', 'api_key', 'file_service_password']
        
        for field in sensitive_fields:
            if field in data and data[field]:
                # 检查是否已经被RSA加密（来自前端）
                if data.get(f'{field}_rsa_encrypted'):
                    # RSA解密
                    decrypted_value = encryption_service.rsa_decrypt(data[field])
                    if decrypted_value:
                        encrypted_fields[field] = decrypted_value
                        # 清除RSA加密标记
                        data.pop(f'{field}_rsa_encrypted', None)
                else:
                    encrypted_fields[field] = data[field]
        
        # 更新原始数据
        data.update(encrypted_fields)
        return data
    except Exception as e:
        print(f"❌ 请求数据解密失败: {e}")
        return data

def prepare_response_data(connections):
    """准备响应数据，遮蔽敏感信息"""
    try:
        for conn in connections:
            # 🔥 确保ID字段转换为字符串，避免JavaScript精度丢失
            if conn.get('id'):
                conn['id'] = str(conn['id'])
            if conn.get('user_id'):
                conn['user_id'] = str(conn['user_id'])
                
            if 'connection_config' in conn and conn['connection_config']:
                config = json.loads(conn['connection_config']) if isinstance(conn['connection_config'], str) else conn['connection_config']
                
                # 🔒 解密配置以便处理
                decrypted_config = service_connection_encryption.decrypt_connection_config(config)
                
                # 🔒 遮蔽敏感字段返回给前端
                masked_config = service_connection_encryption.mask_sensitive_fields(decrypted_config)
                
                conn['connection_config'] = masked_config
        
        return connections
    except Exception as e:
        print(f"❌ 响应数据处理失败: {e}")
        return connections

# ===============================
# 🔒 公钥获取接口
# ===============================

@service_connection_bp.route('/encryption/public-key', methods=['GET'])
def get_public_key():
    """获取RSA公钥用于前端加密"""
    try:
        public_key = encryption_service.get_public_key_pem()
        return jsonify({
            'success': True,
            'data': {
                'public_key': public_key,
                'algorithm': 'RSA-OAEP-SHA256'
            }
        })
    except Exception as e:
        return jsonify({'error': f'获取公钥失败: {str(e)}'}), 500

# ===============================
# 服务连接CRUD接口
# ===============================

@service_connection_bp.route('', methods=['GET'])
@require_auth
def get_connections():
    """获取用户的服务连接列表"""
    try:
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        if not user_id:
            return jsonify({'error': '无法获取用户信息'}), 401
        service_type = request.args.get('service_type')
        is_active = request.args.get('is_active')
        
        # 转换is_active参数
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        
        connections = get_user_connections(user_id, service_type, is_active)
        
        # 🔒 处理响应数据，遮蔽敏感信息
        processed_connections = prepare_response_data(connections)
        
        return jsonify({
            'success': True,
            'data': processed_connections
        })
        
    except Exception as e:
        return jsonify({'error': f'获取连接列表失败: {str(e)}'}), 500

@service_connection_bp.route('', methods=['POST'])
@require_auth
def create_connection():
    """创建新的服务连接"""
    try:
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        if not user_id:
            return jsonify({'error': '无法获取用户信息'}), 401
        data = request.get_json()
        
        # 🔒 解密请求中的敏感数据
        data = encrypt_request_data(data)
        
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
            # 文件服务配置
            if data.get('file_service_url'):
                connection_config['file_service_url'] = data['file_service_url']
            if data.get('file_folder_url'):
                connection_config['file_folder_url'] = data['file_folder_url']
            if data.get('file_service_username'):
                connection_config['file_service_username'] = data['file_service_username']
            if data.get('file_service_password'):
                connection_config['file_service_password'] = data['file_service_password']
        
        # 🔒 加密敏感配置字段
        encrypted_config = service_connection_encryption.encrypt_connection_config(connection_config)
        
        # 创建连接
        connection = create_service_connection(
            user_id=user_id,
            service_name=data['service_name'],
            service_type=data['service_type'],
            server_url=data['server_url'],
            connection_config=encrypted_config,
            description=data.get('description'),
            is_default=data.get('is_default', False)
        )
        
        if connection:
            # 🔥 处理创建返回数据中的大整数ID
            if connection.get('id'):
                connection['id'] = str(connection['id'])
            if connection.get('user_id'):
                connection['user_id'] = str(connection['user_id'])
            
            # 🔒 处理返回的配置信息，遮蔽敏感字段
            if connection.get('connection_config'):
                config = connection['connection_config']
                if isinstance(config, str):
                    config = json.loads(config)
                
                # 解密后遮蔽
                decrypted_config = service_connection_encryption.decrypt_connection_config(config)
                masked_config = service_connection_encryption.mask_sensitive_fields(decrypted_config)
                connection['connection_config'] = masked_config
            
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
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        # 🔥 添加调试日志
        print(f"🔍 更新服务连接调试信息:")
        print(f"   - connection_id: {connection_id} (类型: {type(connection_id)})")
        print(f"   - user_id: {user_id}")
        
        if not user_id:
            return jsonify({'error': '无法获取用户信息'}), 401
        data = request.get_json()
        
        # 🔒 解密请求中的敏感数据
        data = encrypt_request_data(data)
        
        # 验证连接所有权
        check_sql = "SELECT * FROM user_service_connections WHERE id = %s AND user_id = %s"
        print(f"🔍 查询SQL: {check_sql}")
        print(f"🔍 查询参数: [{connection_id}, {user_id}]")
        
        existing = execute_query(check_sql, [connection_id, user_id])
        
        print(f"🔍 查询结果: {len(existing) if existing else 0} 条记录")
        if existing:
            print(f"🔍 找到的连接ID: {existing[0].get('id')}")
        else:
            print(f"❌ 未找到连接 - 可能原因：")
            print(f"   1. 连接ID不存在: {connection_id}")
            print(f"   2. 用户无权限: {user_id}")
            
            # 尝试单独查询连接是否存在
            check_connection_sql = "SELECT id, user_id FROM user_service_connections WHERE id = %s"
            connection_check = execute_query(check_connection_sql, [connection_id])
            if connection_check:
                print(f"   连接存在，但属于用户: {connection_check[0].get('user_id')}")
            else:
                print(f"   连接完全不存在")
                
                # 🔥 查找该用户的相近连接ID（可能是前端精度问题）
                similar_connections_sql = """
                SELECT id, service_name, service_type 
                FROM user_service_connections 
                WHERE user_id = %s 
                ORDER BY ABS(id - %s) 
                LIMIT 3
                """
                similar_connections = execute_query(similar_connections_sql, [user_id, connection_id])
                if similar_connections:
                    print(f"   该用户的相近连接ID:")
                    for similar in similar_connections:
                        print(f"     ID: {similar['id']} | 名称: {similar['service_name']} | 类型: {similar['service_type']}")
                        id_diff = abs(int(similar['id']) - int(connection_id))
                        print(f"     ID差值: {id_diff}")
                        if id_diff <= 10:  # ID差值很小，可能是精度问题
                            print(f"     ⚠️ 可能的精度丢失问题！")
        
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
        config_update_needed = any(key in data for key in ['server_url', 'username', 'password', 'workspace', 'api_key', 'database_url', 'file_service_url', 'file_folder_url', 'file_service_username', 'file_service_password'])
        
        if config_update_needed:
            config_data = existing[0]['connection_config']
            
            # 安全地解析JSON配置
            if isinstance(config_data, str):
                current_config = json.loads(config_data)
            elif isinstance(config_data, dict):
                current_config = config_data
            else:
                current_config = {}
            
            # 🔒 先解密现有配置
            current_config = service_connection_encryption.decrypt_connection_config(current_config)
            
            # 🔥 确保同步更新server_url
            if 'server_url' in data:
                current_config['server_url'] = data['server_url']
                print(f"🔍 更新配置中的server_url: {data['server_url']}")
            
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
            # 文件服务配置更新
            if 'file_service_url' in data:
                current_config['file_service_url'] = data['file_service_url']
            if 'file_folder_url' in data:
                current_config['file_folder_url'] = data['file_folder_url']
            if 'file_service_username' in data:
                current_config['file_service_username'] = data['file_service_username']
            if 'file_service_password' in data:
                current_config['file_service_password'] = data['file_service_password']
            
            print(f"🔍 更新后的配置: {current_config}")
            
            # 🔒 重新加密配置
            encrypted_config = service_connection_encryption.encrypt_connection_config(current_config)
            
            update_fields.append('connection_config = %s')
            params.append(json.dumps(encrypted_config))
        
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
            # 🔥 处理返回数据中的大整数ID
            updated_connection = result[0]
            if updated_connection.get('id'):
                updated_connection['id'] = str(updated_connection['id'])
            if updated_connection.get('user_id'):
                updated_connection['user_id'] = str(updated_connection['user_id'])
            
            # 🔒 处理返回的配置信息，遮蔽敏感字段
            if updated_connection.get('connection_config'):
                config = updated_connection['connection_config']
                if isinstance(config, str):
                    config = json.loads(config)
                
                # 解密后遮蔽
                decrypted_config = service_connection_encryption.decrypt_connection_config(config)
                masked_config = service_connection_encryption.mask_sensitive_fields(decrypted_config)
                updated_connection['connection_config'] = masked_config
            
            return jsonify({
                'success': True,
                'data': updated_connection,
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
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        if not user_id:
            return jsonify({'error': '无法获取用户信息'}), 401
        
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
        
        # 🔒 解密请求中的敏感数据
        data = encrypt_request_data(data)
        
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
            # 构建文件服务配置
            file_service_config = {}
            if data.get('file_service_url'):
                file_service_config = {
                    'file_service_url': data.get('file_service_url'),
                    'file_service_username': data.get('file_service_username'),
                    'file_service_password': data.get('file_service_password')
                }
            result = test_martin_connection(server_url, api_key, file_service_config if file_service_config else None)
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
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        # 🔥 添加调试日志
        print(f"🔍 测试现有连接调试信息:")
        print(f"   - connection_id: {connection_id} (类型: {type(connection_id)})")
        print(f"   - user_id: {user_id}")
        
        if not user_id:
            return jsonify({'error': '无法获取用户信息'}), 401
        
        # 获取连接信息
        query = "SELECT * FROM user_service_connections WHERE id = %s AND user_id = %s"
        print(f"🔍 查询SQL: {query}")
        print(f"🔍 查询参数: [{connection_id}, {user_id}]")
        
        connections = execute_query(query, [connection_id, user_id])
        print(f"🔍 查询结果: {len(connections) if connections else 0} 条记录")
        
        if not connections:
            return jsonify({'error': '连接不存在或无权限访问'}), 404
        
        connection = connections[0]
        config_data = connection['connection_config']
        
        # 安全地解析JSON配置
        if isinstance(config_data, str):
            config = json.loads(config_data)
        elif isinstance(config_data, dict):
            config = config_data
        else:
            return jsonify({'error': '连接配置格式错误'}), 400
        
        # 🔒 解密配置数据
        config = service_connection_encryption.decrypt_connection_config(config)
        
        # 执行测试
        print(f"🔍 连接信息: 类型={connection['service_type']}, 名称={connection['service_name']}")
        print(f"🔍 配置信息: {config}")
        print(f"🔍 数据库server_url: {connection['server_url']}")
        print(f"🔍 配置server_url: {config.get('server_url')}")
        
        if connection['service_type'] == 'geoserver':
            print(f"🔍 开始测试GeoServer连接...")
            
            # 🔥 优先使用数据库中的server_url（通常是完整的）
            server_url = connection['server_url'] or config.get('server_url')
            
            # 🔥 如果URL仍然不完整，添加/geoserver路径
            if server_url and '/geoserver' not in server_url:
                if server_url.endswith('/'):
                    server_url += 'geoserver'
                else:
                    server_url += '/geoserver'
                print(f"🔍 修正后的server_url: {server_url}")
            
            print(f"🔍 最终使用的server_url: {server_url}")
            
            result = test_geoserver_connection(
                server_url,
                config['username'],
                config['password']
            )
            print(f"🔍 GeoServer测试结果: {result}")
        elif connection['service_type'] == 'martin':
            print(f"🔍 开始测试Martin连接...")
            # 构建文件服务配置
            file_service_config = None
            if config.get('file_service_url'):
                file_service_config = {
                    'file_service_url': config.get('file_service_url'),
                    'file_service_username': config.get('file_service_username'),
                    'file_service_password': config.get('file_service_password')
                }
            result = test_martin_connection(
                config['server_url'],
                config.get('api_key'),
                file_service_config
            )
            print(f"🔍 Martin测试结果: {result}")
        else:
            return jsonify({'error': '不支持的服务类型'}), 400
        
        # 更新测试结果
        print(f"🔍 准备更新测试结果: success={result['success']}, message={result['message']}")
        update_connection_test_result(
            connection_id,
            'success' if result['success'] else 'failed',
            result['message']
        )
        
        if result['success']:
            print(f"🔍 测试成功，返回200")
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result.get('data', {})
            })
        else:
            print(f"🔍 测试失败，返回400: {result['message']}")
            return jsonify({'error': result['message']}), 400
        
    except Exception as e:
        print(f"❌ 测试连接异常: {str(e)}")
        import traceback
        print(f"❌ 异常堆栈: {traceback.format_exc()}")
        return jsonify({'error': f'测试连接失败: {str(e)}'}), 500

# ===============================
# 连接测试函数
# ===============================

def test_geoserver_connection(server_url, username, password):
    """测试GeoServer连接"""
    try:
        print(f"🔍 GeoServer测试参数:")
        print(f"   - server_url: {server_url}")
        print(f"   - username: {username}")
        print(f"   - password: {'***' if password else 'None'}")
        
        # 构建REST API URL
        if not server_url.endswith('/'):
            server_url += '/'
        
        workspaces_url = f"{server_url}rest/workspaces.json"
        print(f"🔍 请求URL: {workspaces_url}")
        
        response = requests.get(
            workspaces_url,
            auth=HTTPBasicAuth(username, password),
            timeout=10
        )
        
        print(f"🔍 响应状态码: {response.status_code}")
        
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

def test_file_service_connection(file_service_url, username=None, password=None):
    """测试文件服务连接"""
    try:
        if not file_service_url.endswith('/'):
            file_service_url += '/'
        
        # 构建认证
        auth = None
        if username and password:
            auth = HTTPBasicAuth(username, password)
        
        # 测试健康检查接口
        try:
            health_url = f"{file_service_url}health"
            response = requests.get(health_url, auth=auth, timeout=10)
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': '文件服务连接成功',
                    'data': {'service_type': 'file_service'}
                }
        except:
            pass
        
        # 测试登录接口
        try:
            login_url = f"{file_service_url}login"
            response = requests.get(login_url, timeout=10)
            if response.status_code in [200, 401]:  # 登录页面存在
                return {
                    'success': True,
                    'message': '文件服务连接成功，服务正在运行',
                    'data': {'service_type': 'file_service', 'has_auth': True}
                }
        except:
            pass
        
        # 测试根路径
        root_response = requests.get(file_service_url, timeout=10)
        if root_response.status_code in [200, 401, 403]:
            return {
                'success': True,
                'message': '文件服务连接成功',
                'data': {'service_type': 'file_service'}
            }
        else:
            return {'success': False, 'message': f'文件服务连接失败，HTTP状态码: {root_response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '文件服务连接超时，请检查服务地址'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': '无法连接到文件服务，请检查地址和网络'}
    except Exception as e:
        return {'success': False, 'message': f'文件服务连接测试失败: {str(e)}'}

def test_martin_connection(server_url, api_key=None, file_service_config=None):
    """测试Martin连接，可选文件服务配置"""
    try:
        if not server_url.endswith('/'):
            server_url += '/'
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        martin_result = None
        file_service_result = None
        
        # 测试Martin服务
        try:
            # 尝试健康检查
            try:
                health_url = f"{server_url}health"
                health_response = requests.get(health_url, headers=headers, timeout=10)
                if health_response.status_code == 200:
                    martin_result = {
                        'success': True,
                        'message': 'Martin服务连接成功',
                        'data': health_response.json()
                    }
            except:
                pass
            
            if not martin_result:
                # 尝试目录接口
                catalog_url = f"{server_url}catalog"
                catalog_response = requests.get(catalog_url, headers=headers, timeout=10)
                
                if catalog_response.status_code == 200:
                    catalog_data = catalog_response.json()
                    table_count = len(catalog_data) if isinstance(catalog_data, list) else 0
                    
                    martin_result = {
                        'success': True,
                        'message': f'Martin服务连接成功，发现 {table_count} 个数据源',
                        'data': {'table_count': table_count}
                    }
                elif catalog_response.status_code == 401:
                    martin_result = {'success': False, 'message': 'Martin认证失败，请检查API密钥'}
                else:
                    martin_result = {'success': False, 'message': f'Martin连接失败，HTTP状态码: {catalog_response.status_code}'}
                    
        except requests.exceptions.Timeout:
            martin_result = {'success': False, 'message': 'Martin连接超时，请检查服务地址'}
        except requests.exceptions.ConnectionError:
            martin_result = {'success': False, 'message': '无法连接到Martin服务器，请检查地址和网络'}
        except Exception as e:
            martin_result = {'success': False, 'message': f'Martin连接测试失败: {str(e)}'}
        
        # 测试文件服务（如果配置了）
        if file_service_config and file_service_config.get('file_service_url'):
            file_service_result = test_file_service_connection(
                file_service_config['file_service_url'],
                file_service_config.get('file_service_username'),
                file_service_config.get('file_service_password')
            )
        
        # 综合返回结果
        if martin_result and martin_result['success']:
            if file_service_result:
                if file_service_result['success']:
                    return {
                        'success': True,
                        'message': f"{martin_result['message']}，文件服务也连接成功",
                        'data': {
                            'martin': martin_result.get('data', {}),
                            'file_service': file_service_result.get('data', {})
                        }
                    }
                else:
                    return {
                        'success': True,
                        'message': f"{martin_result['message']}，但文件服务连接失败: {file_service_result['message']}",
                        'data': {
                            'martin': martin_result.get('data', {}),
                            'file_service_error': file_service_result['message']
                        }
                    }
            else:
                return martin_result
        else:
            return martin_result or {'success': False, 'message': 'Martin连接测试失败'}
            
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
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        if not user_id:
            return jsonify({'error': '无法获取用户信息'}), 401
        
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

@service_connection_bp.route('/file-service/download', methods=['GET'])
def download_file_service():
    """下载文件服务程序"""
    try:
        import os
        from flask import send_file
        
        # 假设main.exe文件在项目的downloads目录中
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'downloads', 'selfFileService.zip')
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件服务程序未找到'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name='文件服务程序.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500 