#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多实例启动器 - 用于负载均衡部署
在不同端口启动多个Waitress实例
"""

import os
import sys
import subprocess
import multiprocessing
import time
import signal
import threading
import psutil
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class MultiInstanceLauncher:
    """多实例启动器"""
    
    def __init__(self):
        # 基础配置
        self.base_port = 5030
        self.instance_count = min(multiprocessing.cpu_count(), 4)  # 最多4个实例
        self.instances = []
        self.is_running = True
        
        # 配置日志
        self.setup_logging()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """设置日志"""
        log_dir = Path(project_root) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "multi_instance.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("MultiInstanceLauncher")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在关闭所有实例...")
        self.is_running = False
        self.stop_all_instances()
    
    def create_instance_script(self, port):
        """创建单个实例的启动脚本"""
        script_content = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实例 {port} 启动脚本
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = r"{project_root}"
sys.path.insert(0, project_root)
os.chdir(project_root)

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONUNBUFFERED', '1')

try:
    from waitress import serve
    from wsgi import app
    import logging
    
    # 配置实例特定的日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - Instance{port} - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/instance_{port}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(f"Instance{port}")
    
    logger.info(f"启动实例 {port}...")
    
    # 启动Waitress服务器
    serve(
        app,
        host="127.0.0.1",  # 只监听本地，通过nginx负载均衡
        port={port},
        threads=8,  # 每个实例8个线程
        connection_limit=250,  # 每个实例250连接
        channel_timeout=120,
        cleanup_interval=30,
        send_bytes=18000,
        expose_tracebacks=False
    )
    
except Exception as e:
    print(f"实例 {port} 启动失败: {{e}}")
    sys.exit(1)
'''
        
        script_file = Path(project_root) / f"instance_{port}.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_file
    
    def start_instance(self, port):
        """启动单个实例"""
        try:
            # 检查端口是否已被占用
            if self.is_port_in_use(port):
                self.logger.warning(f"端口 {port} 已被占用，跳过启动")
                return None
            
            # 创建实例脚本
            script_file = self.create_instance_script(port)
            
            # 启动进程
            process = subprocess.Popen(
                [sys.executable, str(script_file)],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.logger.info(f"实例 {port} 启动中... PID: {process.pid}")
            
            # 等待启动
            time.sleep(2)
            
            # 检查进程是否正常运行
            if process.poll() is None:
                self.logger.info(f"✅ 实例 {port} 启动成功")
                return {
                    'port': port,
                    'process': process,
                    'script_file': script_file,
                    'pid': process.pid
                }
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ 实例 {port} 启动失败")
                self.logger.error(f"stdout: {stdout.decode()}")
                self.logger.error(f"stderr: {stderr.decode()}")
                return None
                
        except Exception as e:
            self.logger.error(f"启动实例 {port} 时发生异常: {e}")
            return None
    
    def is_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except:
            return False
    
    def stop_instance(self, instance):
        """停止单个实例"""
        try:
            port = instance['port']
            process = instance['process']
            script_file = instance['script_file']
            
            self.logger.info(f"正在停止实例 {port}...")
            
            # 优雅关闭
            process.terminate()
            
            # 等待进程结束
            try:
                process.wait(timeout=10)
                self.logger.info(f"✅ 实例 {port} 已停止")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"实例 {port} 未在超时时间内停止，强制终止")
                process.kill()
                process.wait()
                self.logger.info(f"✅ 实例 {port} 已强制停止")
            
            # 清理脚本文件
            try:
                script_file.unlink()
                self.logger.debug(f"清理脚本文件: {script_file}")
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"停止实例时发生异常: {e}")
    
    def start_all_instances(self):
        """启动所有实例"""
        self.logger.info("=" * 60)
        self.logger.info("🚀 启动 SHP Service 多实例负载均衡集群")
        self.logger.info("=" * 60)
        self.logger.info(f"实例数量: {self.instance_count}")
        self.logger.info(f"端口范围: {self.base_port} - {self.base_port + self.instance_count - 1}")
        self.logger.info(f"负载均衡: 请配置 Nginx 或其他反向代理")
        self.logger.info("=" * 60)
        
        success_count = 0
        
        for i in range(self.instance_count):
            port = self.base_port + i
            instance = self.start_instance(port)
            
            if instance:
                self.instances.append(instance)
                success_count += 1
            else:
                self.logger.error(f"实例 {port} 启动失败")
        
        self.logger.info(f"启动完成: {success_count}/{self.instance_count} 个实例成功启动")
        
        if success_count == 0:
            self.logger.error("没有实例成功启动，退出")
            return False
        
        # 显示集群状态
        self.show_cluster_status()
        return True
    
    def stop_all_instances(self):
        """停止所有实例"""
        self.logger.info("正在停止所有实例...")
        
        for instance in self.instances:
            self.stop_instance(instance)
        
        self.instances.clear()
        self.logger.info("✅ 所有实例已停止")
    
    def show_cluster_status(self):
        """显示集群状态"""
        self.logger.info("集群状态:")
        
        for instance in self.instances:
            port = instance['port']
            pid = instance['pid']
            
            # 检查进程是否存在
            try:
                process = psutil.Process(pid)
                status = "运行中" if process.is_running() else "已停止"
                cpu_percent = process.cpu_percent()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                self.logger.info(f"  实例 {port}: {status} (PID: {pid}, CPU: {cpu_percent:.1f}%, 内存: {memory_mb:.1f}MB)")
                
            except psutil.NoSuchProcess:
                self.logger.warning(f"  实例 {port}: 进程不存在 (PID: {pid})")
    
    def monitor_instances(self):
        """监控实例状态"""
        self.logger.info("启动实例监控线程...")
        
        while self.is_running:
            try:
                # 检查实例状态
                for instance in self.instances[:]:  # 创建副本避免修改时迭代
                    port = instance['port']
                    process = instance['process']
                    
                    if process.poll() is not None:
                        self.logger.warning(f"检测到实例 {port} 已停止，尝试重启...")
                        
                        # 从列表中移除
                        self.instances.remove(instance)
                        
                        # 清理
                        try:
                            instance['script_file'].unlink()
                        except:
                            pass
                        
                        # 重启实例
                        new_instance = self.start_instance(port)
                        if new_instance:
                            self.instances.append(new_instance)
                            self.logger.info(f"✅ 实例 {port} 重启成功")
                        else:
                            self.logger.error(f"❌ 实例 {port} 重启失败")
                
                # 等待下次检查
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"监控过程中发生异常: {e}")
                time.sleep(5)
    
    def run(self):
        """运行多实例集群"""
        try:
            # 启动所有实例
            if not self.start_all_instances():
                return False
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=self.monitor_instances, daemon=True)
            monitor_thread.start()
            
            self.logger.info("多实例集群启动完成，按 Ctrl+C 停止")
            
            # 等待中断信号
            while self.is_running:
                time.sleep(1)
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号...")
        except Exception as e:
            self.logger.error(f"运行过程中发生异常: {e}")
        finally:
            self.stop_all_instances()

def main():
    """主函数"""
    print("SHP Service 多实例负载均衡启动器")
    print("=" * 50)
    
    # 创建必要目录
    for directory in ['logs', 'temp']:
        os.makedirs(directory, exist_ok=True)
    
    # 启动多实例集群
    launcher = MultiInstanceLauncher()
    
    try:
        launcher.run()
    except Exception as e:
        print(f"启动失败: {e}")
        return 1
    
    print("多实例集群已关闭")
    return 0

if __name__ == '__main__':
    sys.exit(main())
