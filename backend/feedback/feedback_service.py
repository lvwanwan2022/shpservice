#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户反馈系统服务模块
独立可移植的反馈收集系统
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from models.db import execute_query, insert_with_snowflake_id


class FeedbackService:
    """反馈系统服务类"""
    
    def __init__(self, upload_folder: str = 'feedback_uploads'):
        self.upload_folder = upload_folder
        self.allowed_extensions = {
            'image': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
            'document': {'pdf', 'doc', 'docx', 'txt', 'md'},
            'archive': {'zip', 'rar', '7z', 'tar', 'gz'}
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # 确保上传目录存在
        os.makedirs(upload_folder, exist_ok=True)
    
    def get_file_type(self, filename: str) -> str:
        """根据文件扩展名判断文件类型"""
        if not filename:
            return 'unknown'
        
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        for file_type, extensions in self.allowed_extensions.items():
            if ext in extensions:
                return file_type
        
        return 'unknown'
    
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件是否允许上传"""
        file_type = self.get_file_type(filename)
        return file_type != 'unknown'
    
    def create_feedback(self, data: Dict, user_info: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        创建反馈
        
        Args:
            data: 反馈数据
            user_info: 用户信息
            
        Returns:
            (成功标志, 反馈ID或错误信息, 错误详情)
        """
        try:
            # 验证必填字段
            required_fields = ['title', 'category', 'module', 'type']
            for field in required_fields:
                if not data.get(field):
                    return False, f'缺少必填字段: {field}', None
            
            # 验证字段值
            valid_categories = ['feature', 'bug']
            valid_modules = ['frontend', 'backend']
            valid_types = ['ui', 'code']
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            
            if data['category'] not in valid_categories:
                return False, '无效的分类', None
            if data['module'] not in valid_modules:
                return False, '无效的模块', None
            if data['type'] not in valid_types:
                return False, '无效的类型', None
            if data.get('priority', 'medium') not in valid_priorities:
                return False, '无效的优先级', None
            
            # 准备插入数据
            feedback_data = {
                'title': data['title'][:200],  # 限制长度
                'description': data.get('description', ''),
                'category': data['category'],
                'module': data['module'],
                'type': data['type'],
                'priority': data.get('priority', 'medium'),
                'status': 'open',
                'user_id': str(user_info.get('id', '')),
                'username': user_info.get('username', ''),
                'user_email': user_info.get('email', ''),
                'created_at': 'NOW()',
                'updated_at': 'NOW()'
            }
            
            # 插入反馈
            feedback_id = insert_with_snowflake_id('feedback_items', feedback_data)
            
            return True, str(feedback_id), None
            
        except Exception as e:
            return False, '创建反馈失败', str(e)
    
    def upload_attachment(self, file, feedback_id: str, is_screenshot: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        上传附件
        
        Args:
            file: 文件对象
            feedback_id: 反馈ID
            is_screenshot: 是否是截图
            
        Returns:
            (成功标志, 消息, 附件信息)
        """
        try:
            if not file or not file.filename:
                return False, '没有选择文件', None
            
            if not self.is_allowed_file(file.filename):
                return False, '不支持的文件类型', None
            
            # 检查文件大小
            file.seek(0, 2)  # 移动到文件末尾
            file_size = file.tell()
            file.seek(0)     # 重置到文件开头
            
            if file_size > self.max_file_size:
                return False, f'文件大小超过限制 ({self.max_file_size // (1024*1024)}MB)', None
            
            # 生成安全的文件名
            original_name = file.filename
            timestamp = str(int(time.time() * 1000))
            secure_name = secure_filename(original_name)
            filename = f"{timestamp}_{secure_name}"
            
            # 保存文件
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            
            # 获取文件信息
            file_type = self.get_file_type(original_name)
            mime_type = file.content_type or 'application/octet-stream'
            
            # 如果是图片，获取尺寸
            image_width, image_height = None, None
            if file_type == 'image':
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        image_width, image_height = img.size
                except ImportError:
                    pass  # PIL不可用时跳过
                except Exception:
                    pass  # 读取图片失败时跳过
            
            # 保存附件信息到数据库
            attachment_data = {
                'feedback_id': feedback_id,
                'filename': filename,
                'original_name': original_name,
                'file_type': file_type,
                'file_size': file_size,
                'file_path': file_path,
                'mime_type': mime_type,
                'is_screenshot': is_screenshot,
                'image_width': image_width,
                'image_height': image_height,
                'uploaded_at': 'NOW()'
            }
            
            attachment_id = insert_with_snowflake_id('feedback_attachments', attachment_data)
            
            return True, '文件上传成功', {
                'id': str(attachment_id),
                'filename': filename,
                'original_name': original_name,
                'file_type': file_type,
                'file_size': file_size,
                'is_screenshot': is_screenshot
            }
            
        except Exception as e:
            return False, '文件上传失败', str(e)
    
    def get_feedback_list(self, 
                         page: int = 1, 
                         page_size: int = 20,
                         filters: Optional[Dict] = None,
                         sort_by: str = 'created_at',
                         sort_order: str = 'desc',
                         user_id: Optional[str] = None) -> Dict:
        """
        获取反馈列表
        
        Args:
            page: 页码
            page_size: 每页数量
            filters: 筛选条件
            sort_by: 排序字段
            sort_order: 排序方向
            user_id: 当前用户ID（用于判断权限）
            
        Returns:
            分页的反馈列表
        """
        try:
            filters = filters or {}
            offset = (page - 1) * page_size
            
            # 构建WHERE条件
            where_conditions = []
            params = {}
            
            # 基本筛选
            if filters.get('category'):
                where_conditions.append("category = %(category)s")
                params['category'] = filters['category']
            
            if filters.get('module'):
                where_conditions.append("module = %(module)s")
                params['module'] = filters['module']
            
            if filters.get('type'):
                where_conditions.append("type = %(type)s")
                params['type'] = filters['type']
            
            if filters.get('status'):
                where_conditions.append("status = %(status)s")
                params['status'] = filters['status']
            
            if filters.get('priority'):
                where_conditions.append("priority = %(priority)s")
                params['priority'] = filters['priority']
            
            # 用户筛选
            if filters.get('my_feedback') and user_id:
                where_conditions.append("user_id = %(user_id)s")
                params['user_id'] = user_id
            
            # 关键词搜索
            if filters.get('keyword'):
                where_conditions.append("(title LIKE %(keyword)s OR description LIKE %(keyword)s)")
                params['keyword'] = f"%{filters['keyword']}%"
            
            # 构建排序
            valid_sort_fields = [
                'created_at', 'updated_at', 'support_count', 
                'oppose_count', 'comment_count', 'view_count'
            ]
            if sort_by not in valid_sort_fields:
                sort_by = 'created_at'
            
            if sort_order.lower() not in ['asc', 'desc']:
                sort_order = 'desc'
            
            # 构建SQL
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询总数
            count_sql = f"""
            SELECT COUNT(*) as total
            FROM feedback_items
            {where_clause}
            """
            
            count_result = execute_query(count_sql, params)
            total = count_result[0]['total'] if count_result else 0
            
            # 查询数据
            data_sql = f"""
            SELECT 
                id, title, description, category, module, type, priority, status,
                user_id, username, support_count, oppose_count, comment_count, 
                view_count, has_attachments, created_at, updated_at
            FROM feedback_items
            {where_clause}
            ORDER BY {sort_by} {sort_order.upper()}
            LIMIT %(limit)s OFFSET %(offset)s
            """
            
            params.update({
                'limit': page_size,
                'offset': offset
            })
            
            feedback_items = execute_query(data_sql, params)
            
            # 转换ID为字符串
            for item in feedback_items:
                item['id'] = str(item['id'])
                if item.get('user_id'):
                    item['user_id'] = str(item['user_id'])
            
            return {
                'items': feedback_items,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'pages': (total + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            return {
                'items': [],
                'pagination': {'page': 1, 'page_size': page_size, 'total': 0, 'pages': 0},
                'error': str(e)
            }
    
    def get_feedback_detail(self, feedback_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        获取反馈详情
        
        Args:
            feedback_id: 反馈ID
            user_id: 当前用户ID
            
        Returns:
            反馈详情
        """
        try:
            # 增加浏览量
            execute_query(
                "UPDATE feedback_items SET view_count = view_count + 1 WHERE id = %s",
                (feedback_id,)
            )
            
            # 获取反馈基本信息
            feedback_sql = """
            SELECT 
                id, title, description, category, module, type, priority, status,
                user_id, username, user_email, support_count, oppose_count, 
                comment_count, view_count, has_attachments, created_at, updated_at
            FROM feedback_items
            WHERE id = %s
            """
            
            feedback_result = execute_query(feedback_sql, (feedback_id,))
            if not feedback_result:
                return None
            
            feedback = feedback_result[0]
            feedback['id'] = str(feedback['id'])
            if feedback.get('user_id'):
                feedback['user_id'] = str(feedback['user_id'])
            
            # 获取附件
            attachments_sql = """
            SELECT id, filename, original_name, file_type, file_size, 
                   is_screenshot, image_width, image_height, uploaded_at
            FROM feedback_attachments
            WHERE feedback_id = %s
            ORDER BY uploaded_at ASC
            """
            
            attachments = execute_query(attachments_sql, (feedback_id,))
            for attachment in attachments:
                attachment['id'] = str(attachment['id'])
            
            # 获取用户投票状态
            user_vote = None
            if user_id:
                vote_sql = """
                SELECT vote_type FROM feedback_votes
                WHERE feedback_id = %s AND user_id = %s
                """
                vote_result = execute_query(vote_sql, (feedback_id, user_id))
                if vote_result:
                    user_vote = vote_result[0]['vote_type']
            
            # 获取评论
            comments = self.get_feedback_comments(feedback_id)
            
            feedback['attachments'] = attachments
            feedback['user_vote'] = user_vote
            feedback['comments'] = comments
            
            return feedback
            
        except Exception as e:
            return None
    
    def get_feedback_comments(self, feedback_id: str) -> List[Dict]:
        """获取反馈评论"""
        try:
            comments_sql = """
            SELECT id, feedback_id, parent_id, content, user_id, username,
                   is_deleted, created_at, updated_at
            FROM feedback_comments
            WHERE feedback_id = %s AND is_deleted = FALSE
            ORDER BY created_at ASC
            """
            
            comments = execute_query(comments_sql, (feedback_id,))
            for comment in comments:
                comment['id'] = str(comment['id'])
                if comment.get('parent_id'):
                    comment['parent_id'] = str(comment['parent_id'])
                if comment.get('user_id'):
                    comment['user_id'] = str(comment['user_id'])
            
            return comments
            
        except Exception as e:
            return []
    
    def add_comment(self, feedback_id: str, content: str, user_info: Dict, parent_id: Optional[str] = None) -> Tuple[bool, str]:
        """添加评论"""
        try:
            if not content or not content.strip():
                return False, '评论内容不能为空'
            
            comment_data = {
                'feedback_id': feedback_id,
                'parent_id': parent_id if parent_id else None,
                'content': content.strip(),
                'user_id': str(user_info.get('id', '')),
                'username': user_info.get('username', ''),
                'user_email': user_info.get('email', ''),
                'created_at': 'NOW()',
                'updated_at': 'NOW()'
            }
            
            comment_id = insert_with_snowflake_id('feedback_comments', comment_data)
            return True, str(comment_id)
            
        except Exception as e:
            return False, str(e)
    
    def vote_feedback(self, feedback_id: str, user_id: str, username: str, vote_type: str) -> Tuple[bool, str]:
        """投票支持或反对"""
        try:
            if vote_type not in ['support', 'oppose']:
                return False, '无效的投票类型'
            
            # 检查是否已经投票
            existing_vote = execute_query(
                "SELECT vote_type FROM feedback_votes WHERE feedback_id = %s AND user_id = %s",
                (feedback_id, user_id)
            )
            
            if existing_vote:
                current_vote = existing_vote[0]['vote_type']
                if current_vote == vote_type:
                    # 取消投票
                    execute_query(
                        "DELETE FROM feedback_votes WHERE feedback_id = %s AND user_id = %s",
                        (feedback_id, user_id)
                    )
                    return True, '投票已取消'
                else:
                    # 修改投票
                    execute_query(
                        "UPDATE feedback_votes SET vote_type = %s WHERE feedback_id = %s AND user_id = %s",
                        (vote_type, feedback_id, user_id)
                    )
                    return True, '投票已修改'
            else:
                # 新增投票
                vote_data = {
                    'feedback_id': feedback_id,
                    'user_id': user_id,
                    'username': username,
                    'vote_type': vote_type,
                    'created_at': 'NOW()'
                }
                insert_with_snowflake_id('feedback_votes', vote_data)
                return True, '投票成功'
                
        except Exception as e:
            return False, str(e)
    
    def delete_feedback(self, feedback_id: str, user_id: str) -> Tuple[bool, str]:
        """删除反馈（仅创建者可删除）"""
        try:
            # 检查权限
            feedback = execute_query(
                "SELECT user_id FROM feedback_items WHERE id = %s",
                (feedback_id,)
            )
            
            if not feedback:
                return False, '反馈不存在'
            
            if str(feedback[0]['user_id']) != str(user_id):
                return False, '只能删除自己创建的反馈'
            
            # 删除反馈（级联删除相关数据）
            execute_query("DELETE FROM feedback_items WHERE id = %s", (feedback_id,))
            
            return True, '删除成功'
            
        except Exception as e:
            return False, str(e)
    
    def update_feedback_status(self, feedback_id: str, status: str, user_id: str) -> Tuple[bool, str]:
        """更新反馈状态（管理员功能）"""
        try:
            valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
            if status not in valid_statuses:
                return False, '无效的状态'
            
            # 这里可以添加管理员权限检查
            # if not is_admin(user_id):
            #     return False, '权限不足'
            
            execute_query(
                "UPDATE feedback_items SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (status, feedback_id)
            )
            
            return True, '状态更新成功'
            
        except Exception as e:
            return False, str(e) 