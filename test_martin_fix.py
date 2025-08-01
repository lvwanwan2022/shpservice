#!/usr/bin/env python3
"""
测试Martin服务启动修复效果的脚本
"""

import os
import sys
import time
import logging

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_martin_service():
    """测试Martin服务启动"""
    try:
        from services.martin_service import martin_service
        
        logger.info("=== 开始测试Martin服务启动修复效果 ===")
        
        # 1. 检查服务状态
        status = martin_service.get_status()
        logger.info(f"当前状态: {status}")
        
        # 2. 如果服务正在运行，先停止
        if martin_service.is_running():
            logger.info("服务正在运行，先停止...")
            martin_service.stop_service()
            time.sleep(3)
        
        # 3. 测试启动服务
        logger.info("开始启动Martin服务...")
        start_time = time.time()
        
        success = martin_service.start_service()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"启动耗时: {duration:.2f} 秒")
        
        if success:
            logger.info("✅ Martin服务启动成功!")
            
            # 4. 验证端口占用
            martin_port = martin_service.config.get('port', 3000)
            port_in_use = martin_service.check_port_in_use(martin_port)
            logger.info(f"端口{martin_port}占用状态: {port_in_use}")
            
            # 5. 验证HTTP服务
            is_running = martin_service.is_running()
            logger.info(f"HTTP服务可访问: {is_running}")
            
            # 6. 获取服务日志
            logs = martin_service.get_process_logs(10)
            logger.info(f"进程状态: {logs['status']}")
            if logs['stdout']:
                logger.info(f"标准输出: {logs['stdout'][:200]}...")
            if logs['stderr']:
                logger.info(f"错误输出: {logs['stderr'][:200]}...")
            
        else:
            logger.error("❌ Martin服务启动失败!")
            
            # 获取错误日志
            logs = martin_service.get_process_logs(20)
            if logs['stderr']:
                logger.error(f"错误详情: {logs['stderr']}")
        
        logger.info("=== 测试完成 ===")
        return success
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_martin_service()