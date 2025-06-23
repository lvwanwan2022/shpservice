#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
登录认证服务模块
Author: 自动生成
Description: 提供登录验证、token生成和验证功能，方便移植到其他项目
"""

import jwt
import datetime
import hashlib
from functools import wraps
from flask import request, jsonify, current_app

class AuthService:
    def __init__(self, secret_key='your-secret-key', token_expiry_hours=24):
        """
        初始化认证服务
        :param secret_key: JWT签名密钥
        :param token_expiry_hours: token过期时间（小时）
        """
        self.secret_key = secret_key
        self.token_expiry_hours = token_expiry_hours
        
        # 模拟用户数据库 - 实际使用时可替换为真实数据库
        self.users = {
            'admin': {
                'password': self._hash_password('admin123'),
                'name': '管理员',
                'role': 'admin',
                'email': 'admin@example.com'
            },
            'user': {
                'password': self._hash_password('user123'),
                'name': '普通用户',
                'role': 'user',
                'email': 'user@example.com'
            }
        }
    
    def _hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """
        验证用户凭据
        :param username: 用户名
        :param password: 密码
        :return: 验证结果和用户信息
        """
        # 优先从数据库查询用户
        try:
            from models.db import execute_query
            sql = "SELECT id, username, password, email FROM users WHERE username = %s"
            result = execute_query(sql, (username,))
            
            if result:
                user = result[0]
                if user['password'] == self._hash_password(password):
                    # 🔥 返回用户信息（ID作为字符串，防止JavaScript精度丢失）
                    user_info = {
                        'id': str(user['id']),  # 🔥 强制转换为字符串
                        'username': user['username'],
                        'email': user['email'],
                        'name': user['username'],  # 使用用户名作为显示名称
                        'role': 'admin' if username == 'admin' else 'user'
                    }
                    return True, user_info, "登录成功"
                else:
                    return False, None, "密码错误"
            else:
                # 如果数据库中没有用户，回退到内存用户
                if username not in self.users:
                    return False, None, "用户名不存在"
                
                user = self.users[username]
                if user['password'] != self._hash_password(password):
                    return False, None, "密码错误"
                
                # 返回用户信息（去掉密码）
                user_info = {k: v for k, v in user.items() if k != 'password'}
                user_info['username'] = username
                user_info['id'] = username  # 临时使用用户名作为ID
                
                return True, user_info, "登录成功"
                
        except Exception as e:
            print(f"数据库查询用户失败: {e}")
            # 回退到内存用户验证
            if username not in self.users:
                return False, None, "用户名不存在"
            
            user = self.users[username]
            if user['password'] != self._hash_password(password):
                return False, None, "密码错误"
            
            # 返回用户信息（去掉密码）
            user_info = {k: v for k, v in user.items() if k != 'password'}
            user_info['username'] = username
            user_info['id'] = username  # 临时使用用户名作为ID
            
            return True, user_info, "登录成功"
    
    def register(self, username, password, email):
        """
        注册新用户
        :param username: 用户名
        :param password: 密码
        :param email: 邮箱
        :return: 注册结果和用户信息
        """
        try:
            # 先检查用户是否已存在
            from models.db import execute_query, insert_with_snowflake_id
            
            # 检查用户名是否已存在
            sql = "SELECT id FROM users WHERE username = %s"
            result = execute_query(sql, (username,))
            if result:
                return False, None, "用户名已存在"
            
            # 检查邮箱是否已存在
            sql = "SELECT id FROM users WHERE email = %s"
            result = execute_query(sql, (email,))
            if result:
                return False, None, "邮箱已被注册"
            
            # 使用雪花算法插入新用户
            user_data = {
                'username': username,
                'password': self._hash_password(password),
                'email': email,
                'created_at': 'NOW()'
            }
            
            # 使用雪花算法生成ID并插入
            user_id = insert_with_snowflake_id('users', user_data)
            
            # 获取新插入的用户信息
            sql = "SELECT id, username, email FROM users WHERE id = %s"
            result = execute_query(sql, (user_id,))
            
            if result:
                user = result[0]
                user_info = {
                    'id': str(user['id']),  # 🔥 强制转换为字符串
                    'username': user['username'],
                    'email': user['email'],
                    'name': user['username'],
                    'role': 'user'
                }
                return True, user_info, "注册成功"
            else:
                return False, None, "注册失败，请稍后重试"
                
        except Exception as e:
            print(f"数据库注册用户失败: {e}")
            
            # 检查是否是整数范围错误
            if "integer out of range" in str(e).lower():
                return False, None, "系统错误：数据库ID字段类型需要升级，请联系管理员"
            
            # 检查是否是约束违反错误
            if "violates not-null constraint" in str(e).lower():
                return False, None, "系统错误：数据库字段约束错误，请联系管理员"
            
            # 回退到内存存储
            try:
                if username in self.users:
                    return False, None, "用户名已存在"
                
                # 检查邮箱是否重复
                for user in self.users.values():
                    if user.get('email') == email:
                        return False, None, "邮箱已被注册"
                
                # 添加到内存存储
                self.users[username] = {
                    'password': self._hash_password(password),
                    'name': username,
                    'role': 'user',
                    'email': email
                }
                
                user_info = {
                    'id': username,
                    'username': username,
                    'email': email,
                    'name': username,
                    'role': 'user'
                }
                
                return True, user_info, "注册成功"
            except Exception as fallback_error:
                print(f"内存存储注册也失败: {fallback_error}")
                return False, None, "注册失败，请稍后重试"
    
    def generate_token(self, user_info):
        """
        生成JWT token
        :param user_info: 用户信息
        :return: token字符串
        """
        payload = {
            'user_info': user_info,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=self.token_expiry_hours),
            'iat': datetime.datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token):
        """
        验证JWT token
        :param token: token字符串
        :return: 验证结果和用户信息
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True, payload['user_info'], None
        except jwt.ExpiredSignatureError:
            return False, None, "Token已过期"
        except jwt.InvalidTokenError:
            return False, None, "Token无效"
    
    def get_token_from_request(self):
        """
        从请求中获取token
        支持Header: Authorization: Bearer <token>
        支持Header: X-Auth-Token: <token>
        """
        # 从Authorization header获取
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # 去掉'Bearer '
        
        # 从X-Auth-Token header获取
        token = request.headers.get('X-Auth-Token')
        if token:
            return token
        
        return None

# 创建全局认证服务实例
auth_service = AuthService()

def require_auth(f):
    """
    登录认证装饰器 - 一行代码实现接口权限验证
    使用方法: @require_auth
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = auth_service.get_token_from_request()
        
        if not token:
            return jsonify({'code': 401, 'message': '未提供认证token'}), 401
        
        success, user_info, error = auth_service.verify_token(token)
        if not success:
            return jsonify({'code': 401, 'message': error}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = user_info
        return f(*args, **kwargs)
    
    return decorated

def get_current_user():
    """
    获取当前登录用户信息
    :return: 用户信息字典
    """
    return getattr(request, 'current_user', None) 