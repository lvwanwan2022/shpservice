#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
登录认证路由模块
Author: 自动生成
Description: 提供登录、注销、用户信息等API接口
"""

from flask import Blueprint, request, jsonify
from .auth_service import auth_service, require_auth, get_current_user

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
        
        # 验证用户凭据
        success, user_info, message = auth_service.authenticate(username, password)
        
        if not success:
            return jsonify({'code': 401, 'message': message}), 401
        
        # 生成token
        token = auth_service.generate_token(user_info)
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user_info
            }
        })
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户注销接口 - 前端处理，后端只返回成功状态
    """
    return jsonify({
        'code': 200,
        'message': '注销成功'
    })

@auth_bp.route('/userinfo', methods=['GET'])
@require_auth
def get_user_info():
    """
    获取当前用户信息接口
    """
    user_info = get_current_user()
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': user_info
    })

@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """
    验证token接口
    """
    try:
        token = auth_service.get_token_from_request()
        
        if not token:
            return jsonify({'code': 401, 'message': '未提供token'}), 401
        
        success, user_info, error = auth_service.verify_token(token)
        
        if not success:
            return jsonify({'code': 401, 'message': error}), 401
        
        return jsonify({
            'code': 200,
            'message': 'Token有效',
            'data': user_info
        })
        
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500

# 示例：需要登录权限的接口
@auth_bp.route('/protected', methods=['GET'])
@require_auth
def protected_route():
    """
    示例保护接口 - 演示如何一行代码添加登录验证
    """
    user = get_current_user()
    return jsonify({
        'code': 200,
        'message': f'你好 {user["name"]}，这是一个需要登录的接口',
        'data': user
    }) 