#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import tempfile
import time
import contextlib
from typing import Optional, Callable


@contextlib.contextmanager
def safe_temp_file(suffix: str = '', prefix: str = 'tmp', delete: bool = True, 
                   cleanup_delay: float = 0.1) -> str:
    """
    安全的临时文件上下文管理器
    
    Args:
        suffix: 文件后缀
        prefix: 文件前缀
        delete: 是否自动删除
        cleanup_delay: 清理失败时的重试延迟
        
    Yields:
        临时文件路径
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix)
    temp_file_path = temp_file.name
    temp_file.close()  # 立即关闭文件句柄
    
    try:
        yield temp_file_path
    finally:
        if delete:
            # 安全清理临时文件
            _safe_remove_file(temp_file_path, cleanup_delay)


def _safe_remove_file(file_path: str, delay: float = 0.1, max_retries: int = 3):
    """
    安全删除文件，支持重试机制
    
    Args:
        file_path: 文件路径
        delay: 重试延迟
        max_retries: 最大重试次数
    """
    for attempt in range(max_retries):
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                break
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️ 删除文件失败，尝试重试 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
            else:
                print(f"⚠️ 无法删除临时文件（不影响功能）: {file_path} - {e}")


def cleanup_temp_files(pattern: str = "tmp*", directory: Optional[str] = None):
    """
    清理临时文件
    
    Args:
        pattern: 文件模式匹配
        directory: 目录路径，默认为系统临时目录
    """
    import glob
    
    if directory is None:
        directory = tempfile.gettempdir()
    
    try:
        for file_path in glob.glob(os.path.join(directory, pattern)):
            _safe_remove_file(file_path)
    except Exception as e:
        print(f"⚠️ 清理临时文件时出错: {e}") 