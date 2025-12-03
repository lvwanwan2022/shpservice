#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows Server 生产环境 Waitress 高性能配置
支持多进程、连接池、错误恢复
"""

import os
import sys
import multiprocessing
import logging
import signal
import threading
import time
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONUNBUFFERED', '1')  # 确保日志实时输出

try:
    from waitress import serve
    from wsgi import app
    import psutil
    
    # 服务器配置 - 高性能设置
    class ProductionConfig:
        # 基本配置
        HOST = "0.0.0.0"
        PORT = 5030
        
        # 性能配置 - 针对Windows Server优化
        THREADS = min(multiprocessing.cpu_count() * 4, 50)  # 线程数：CPU核心数*4，最大50
        CONNECTION_LIMIT = 1000  # 连接限制
        CHANNEL_TIMEOUT = 120    # 通道超时（秒）
        CLEANUP_INTERVAL = 30    # 清理间隔（秒）
        
        # 内存和连接管理 - 动态调整
        MAX_MEMORY_USAGE = None  # 自动检测系统内存，不设固定限制
        MEMORY_THRESHOLD_PERCENT = 85  # 内存使用率阈值（百分比）
        RESTART_THRESHOLD = 0.9  # 内存使用率重启阈值
        
        # 日志配置
        LOG_LEVEL = "INFO"
        LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 错误恢复
        MAX_RETRIES = 3
        RETRY_DELAY = 5

    config = ProductionConfig()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/waitress_production.log', encoding='utf-8')
        ]
    )
    logger = logging.getLogger(__name__)
    
    # 全局变量
    server_process = None
    should_restart = False
    
    def setup_directories():
        """创建必要的目录"""
        directories = [
            'logs',
            'temp', 
            'FilesData',
            'feedback_uploads'
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✅ 创建目录: {directory}")
    
    def check_system_resources():
        """检查系统资源"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / 1024 / 1024
            memory_percent = memory.percent
            
            # 磁盘使用情况
            disk = psutil.disk_usage('.')
            disk_percent = disk.used / disk.total * 100
            
            logger.info(f"系统资源状态:")
            logger.info(f"  CPU使用率: {cpu_percent:.1f}%")
            logger.info(f"  内存使用: {memory_used_mb:.1f}MB ({memory_percent:.1f}%)")
            logger.info(f"  磁盘使用: {disk_percent:.1f}%")
            
            # 检查是否需要重启 - 使用百分比检查
            if memory_percent > config.MEMORY_THRESHOLD_PERCENT:
                logger.warning(f"内存使用率过高: {memory_percent:.1f}% > {config.MEMORY_THRESHOLD_PERCENT}%")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"资源检查失败: {e}")
            return True
    
    def monitor_resources():
        """资源监控线程"""
        global should_restart
        
        while True:
            try:
                if not check_system_resources():
                    logger.warning("触发重启条件")
                    should_restart = True
                    break
                    
                time.sleep(config.CLEANUP_INTERVAL)
                
            except Exception as e:
                logger.error(f"监控线程错误: {e}")
                time.sleep(config.CLEANUP_INTERVAL)
    
    def signal_handler(signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，正在优雅关闭...")
        global should_restart
        should_restart = True
    
    def start_server():
        """启动服务器"""
        global server_process, should_restart
        
        logger.info("🚀 启动 SHP Service 高性能生产服务器")
        logger.info("=" * 60)
        logger.info(f"📱 本地访问: http://localhost:{config.PORT}")
        logger.info(f"🌐 网络访问: http://10.20.148.169:{config.PORT}")
        logger.info(f"📚 API文档: http://10.20.148.169:{config.PORT}/swagger/")
        logger.info("=" * 60)
        logger.info(f"⚙️  配置信息:")
        logger.info(f"   - 线程数: {config.THREADS}")
        logger.info(f"   - 连接限制: {config.CONNECTION_LIMIT}")
        logger.info(f"   - 通道超时: {config.CHANNEL_TIMEOUT}s")
        logger.info(f"   - 清理间隔: {config.CLEANUP_INTERVAL}s")
        logger.info(f"   - 内存阈值: {config.MEMORY_THRESHOLD_PERCENT}%")
        logger.info(f"📊 服务器: Waitress (Windows 高性能版)")
        logger.info("=" * 60)
        
        try:
            # 启动资源监控线程
            monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
            monitor_thread.start()
            logger.info("✅ 资源监控线程已启动")
            
            # 启动服务器
            serve(
                app,
                host=config.HOST,
                port=config.PORT,
                threads=config.THREADS,
                connection_limit=config.CONNECTION_LIMIT,
                channel_timeout=config.CHANNEL_TIMEOUT,
                cleanup_interval=config.CLEANUP_INTERVAL,
                # Windows 特定优化
                send_bytes=18000,  # 发送缓冲区大小
                # 启用连接复用
                asyncore_use_poll=True if hasattr(os, 'poll') else False,
                # 错误处理
                expose_tracebacks=False,  # 生产环境不暴露错误跟踪
            )
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭服务器...")
        except Exception as e:
            logger.error(f"服务器启动失败: {e}")
            raise
    
    def main():
        """主函数 - 带重启机制"""
        global should_restart
        
        # 设置信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 创建必要目录
        setup_directories()
        
        # 检查系统要求
        logger.info("检查系统要求...")
        if not check_system_resources():
            logger.error("系统资源不足，无法启动服务器")
            sys.exit(1)
        
        retry_count = 0
        
        while retry_count < config.MAX_RETRIES:
            try:
                should_restart = False
                start_server()
                
                # 如果到达这里，说明服务器正常退出
                if should_restart:
                    logger.info("准备重启服务器...")
                    time.sleep(config.RETRY_DELAY)
                    retry_count += 1
                    continue
                else:
                    logger.info("服务器正常关闭")
                    break
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"服务器异常 (尝试 {retry_count}/{config.MAX_RETRIES}): {e}")
                
                if retry_count < config.MAX_RETRIES:
                    logger.info(f"等待 {config.RETRY_DELAY} 秒后重启...")
                    time.sleep(config.RETRY_DELAY)
                else:
                    logger.error("达到最大重试次数，服务器退出")
                    sys.exit(1)
    
    if __name__ == '__main__':
        main()

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请安装必要的依赖:")
    print("  pip install waitress psutil")
    sys.exit(1)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    sys.exit(1)
