#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户反馈系统API路由
独立可移植的反馈收集系统
"""

import os
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from .feedback_service import FeedbackService

# 创建蓝图
feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

# 创建服务实例
feedback_service = FeedbackService(upload_folder='feedback_uploads')

def get_current_user():
    """获取当前用户信息（适配现有认证系统）"""
    try:
        # 这里需要根据实际的认证系统调整
        from auth.auth_service import get_current_user as get_auth_user
        return get_auth_user()
    except ImportError:
        # 如果没有认证系统，返回默认用户（开发环境）
        return {
            'id': 'anonymous',
            'username': '匿名用户',
            'email': 'anonymous@example.com'
        }

@feedback_bp.route('/items', methods=['GET'])
def get_feedback_list():
    """
    获取反馈列表
    ---
    tags:
      - 反馈系统
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码
      - name: page_size
        in: query
        type: integer
        default: 20
        description: 每页数量
      - name: category
        in: query
        type: string
        description: 分类 (feature/bug)
      - name: module
        in: query
        type: string
        description: 模块 (frontend/backend)
      - name: type
        in: query
        type: string
        description: 类型 (ui/code)
      - name: status
        in: query
        type: string
        description: 状态 (open/in_progress/resolved/closed)
      - name: priority
        in: query
        type: string
        description: 优先级 (low/medium/high/urgent)
      - name: my_feedback
        in: query
        type: boolean
        description: 只显示我的反馈
      - name: keyword
        in: query
        type: string
        description: 关键词搜索
      - name: sort_by
        in: query
        type: string
        default: created_at
        description: 排序字段
      - name: sort_order
        in: query
        type: string
        default: desc
        description: 排序方向 (asc/desc)
    responses:
      200:
        description: 反馈列表
    """
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)  # 限制最大页面大小
        
        # 构建筛选条件
        filters = {}
        for field in ['category', 'module', 'type', 'status', 'priority', 'keyword']:
            value = request.args.get(field)
            if value:
                filters[field] = value
        
        # 我的反馈筛选
        if request.args.get('my_feedback') == 'true':
            filters['my_feedback'] = True
        
        # 排序参数
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 获取当前用户
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        # 调用服务
        result = feedback_service.get_feedback_list(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id
        )
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'code': 400, 'message': f'参数错误: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f"获取反馈列表失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items', methods=['POST'])
def create_feedback():
    """
    创建反馈
    ---
    tags:
      - 反馈系统
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - category
            - module
            - type
          properties:
            title:
              type: string
              description: 反馈标题
            description:
              type: string
              description: 详细描述
            category:
              type: string
              enum: [feature, bug]
              description: 分类
            module:
              type: string
              enum: [frontend, backend]
              description: 模块
            type:
              type: string
              enum: [ui, code]
              description: 类型
            priority:
              type: string
              enum: [low, medium, high, urgent]
              description: 优先级
    responses:
      201:
        description: 反馈创建成功
      400:
        description: 参数错误
      401:
        description: 未登录
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        # 创建反馈
        success, result, error = feedback_service.create_feedback(data, current_user)
        
        if success:
            return jsonify({
                'code': 201,
                'message': '反馈创建成功',
                'data': {'feedback_id': result}
            }), 201
        else:
            return jsonify({'code': 400, 'message': result}), 400
            
    except Exception as e:
        current_app.logger.error(f"创建反馈失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items/<feedback_id>', methods=['GET'])
def get_feedback_detail(feedback_id):
    """
    获取反馈详情
    ---
    tags:
      - 反馈系统
    parameters:
      - name: feedback_id
        in: path
        type: string
        required: true
        description: 反馈ID
    responses:
      200:
        description: 反馈详情
      404:
        description: 反馈不存在
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        user_id = str(current_user.get('id')) if current_user else None
        
        # 获取反馈详情
        feedback = feedback_service.get_feedback_detail(feedback_id, user_id)
        
        if not feedback:
            return jsonify({'code': 404, 'message': '反馈不存在'}), 404
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': feedback
        })
        
    except Exception as e:
        current_app.logger.error(f"获取反馈详情失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items/<feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    """
    删除反馈
    ---
    tags:
      - 反馈系统
    parameters:
      - name: feedback_id
        in: path
        type: string
        required: true
        description: 反馈ID
    responses:
      200:
        description: 删除成功
      401:
        description: 未登录
      403:
        description: 权限不足
      404:
        description: 反馈不存在
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        user_id = str(current_user.get('id'))
        
        # 删除反馈
        success, message = feedback_service.delete_feedback(feedback_id, user_id)
        
        if success:
            return jsonify({
                'code': 200,
                'message': message
            })
        else:
            if '权限' in message:
                return jsonify({'code': 403, 'message': message}), 403
            elif '不存在' in message:
                return jsonify({'code': 404, 'message': message}), 404
            else:
                return jsonify({'code': 400, 'message': message}), 400
                
    except Exception as e:
        current_app.logger.error(f"删除反馈失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items/<feedback_id>/attachments', methods=['POST'])
def upload_attachment(feedback_id):
    """
    上传附件
    ---
    tags:
      - 反馈系统
    parameters:
      - name: feedback_id
        in: path
        type: string
        required: true
        description: 反馈ID
      - name: file
        in: formData
        type: file
        required: true
        description: 文件
      - name: is_screenshot
        in: formData
        type: boolean
        description: 是否是截图
    responses:
      201:
        description: 上传成功
      400:
        description: 上传失败
      401:
        description: 未登录
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'code': 400, 'message': '没有选择文件'}), 400
        
        file = request.files['file']
        is_screenshot = request.form.get('is_screenshot', 'false').lower() == 'true'
        
        # 上传文件
        success, message, attachment_info = feedback_service.upload_attachment(
            file, feedback_id, is_screenshot
        )
        
        if success:
            return jsonify({
                'code': 201,
                'message': message,
                'data': attachment_info
            }), 201
        else:
            return jsonify({'code': 400, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"上传附件失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items/<feedback_id>/comments', methods=['POST'])
def add_comment(feedback_id):
    """
    添加评论
    ---
    tags:
      - 反馈系统
    parameters:
      - name: feedback_id
        in: path
        type: string
        required: true
        description: 反馈ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - content
          properties:
            content:
              type: string
              description: 评论内容
            parent_id:
              type: string
              description: 父评论ID（回复时使用）
    responses:
      201:
        description: 评论成功
      400:
        description: 参数错误
      401:
        description: 未登录
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        content = data.get('content')
        parent_id = data.get('parent_id')
        
        # 添加评论
        success, result = feedback_service.add_comment(
            feedback_id, content, current_user, parent_id
        )
        
        if success:
            return jsonify({
                'code': 201,
                'message': '评论成功',
                'data': {'comment_id': result}
            }), 201
        else:
            return jsonify({'code': 400, 'message': result}), 400
            
    except Exception as e:
        current_app.logger.error(f"添加评论失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items/<feedback_id>/vote', methods=['POST'])
def vote_feedback(feedback_id):
    """
    投票支持或反对
    ---
    tags:
      - 反馈系统
    parameters:
      - name: feedback_id
        in: path
        type: string
        required: true
        description: 反馈ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - vote_type
          properties:
            vote_type:
              type: string
              enum: [support, oppose]
              description: 投票类型
    responses:
      200:
        description: 投票成功
      400:
        description: 参数错误
      401:
        description: 未登录
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        vote_type = data.get('vote_type')
        
        # 投票
        success, message = feedback_service.vote_feedback(
            feedback_id, 
            str(current_user.get('id')), 
            current_user.get('username', ''),
            vote_type
        )
        
        if success:
            return jsonify({
                'code': 200,
                'message': message
            })
        else:
            return jsonify({'code': 400, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"投票失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/items/<feedback_id>/status', methods=['PUT'])
def update_feedback_status(feedback_id):
    """
    更新反馈状态（管理员功能）
    ---
    tags:
      - 反馈系统
    parameters:
      - name: feedback_id
        in: path
        type: string
        required: true
        description: 反馈ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [open, in_progress, resolved, closed]
              description: 新状态
    responses:
      200:
        description: 状态更新成功
      400:
        description: 参数错误
      401:
        description: 未登录
      403:
        description: 权限不足
    """
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'code': 401, 'message': '请先登录'}), 401
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        status = data.get('status')
        
        # 更新状态
        success, message = feedback_service.update_feedback_status(
            feedback_id, status, str(current_user.get('id'))
        )
        
        if success:
            return jsonify({
                'code': 200,
                'message': message
            })
        else:
            if '权限' in message:
                return jsonify({'code': 403, 'message': message}), 403
            else:
                return jsonify({'code': 400, 'message': message}), 400
                
    except Exception as e:
        current_app.logger.error(f"更新状态失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/attachments/<filename>')
def download_attachment(filename):
    """
    下载附件
    ---
    tags:
      - 反馈系统
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: 文件名
    responses:
      200:
        description: 文件内容
      404:
        description: 文件不存在
    """
    try:
        file_path = os.path.join(feedback_service.upload_folder, secure_filename(filename))
        
        if not os.path.exists(file_path):
            return jsonify({'code': 404, 'message': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f"下载附件失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

@feedback_bp.route('/stats', methods=['GET'])
def get_feedback_stats():
    """
    获取反馈统计信息
    ---
    tags:
      - 反馈系统
    responses:
      200:
        description: 统计信息
    """
    try:
        from models.db import execute_query
        
        # 基本统计
        stats = {}
        
        # 总数统计
        total_sql = "SELECT COUNT(*) as total FROM feedback_items"
        total_result = execute_query(total_sql)
        stats['total'] = total_result[0]['total'] if total_result else 0
        
        # 按分类统计
        category_sql = """
        SELECT category, COUNT(*) as count 
        FROM feedback_items 
        GROUP BY category
        """
        category_result = execute_query(category_sql)
        stats['by_category'] = {item['category']: item['count'] for item in category_result}
        
        # 按状态统计
        status_sql = """
        SELECT status, COUNT(*) as count 
        FROM feedback_items 
        GROUP BY status
        """
        status_result = execute_query(status_sql)
        stats['by_status'] = {item['status']: item['count'] for item in status_result}
        
        # 按模块统计
        module_sql = """
        SELECT module, COUNT(*) as count 
        FROM feedback_items 
        GROUP BY module
        """
        module_result = execute_query(module_sql)
        stats['by_module'] = {item['module']: item['count'] for item in module_result}
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500 