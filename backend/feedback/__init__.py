#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户反馈系统模块
独立可移植的反馈收集系统
"""

from .feedback_routes import feedback_bp
from .feedback_service import FeedbackService

__version__ = '1.0.0'
__author__ = 'Feedback System'

# 导出主要组件
__all__ = [
    'feedback_bp',
    'FeedbackService'
] 