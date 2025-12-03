#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows 服务管理脚本
将Flask应用注册为Windows系统服务，支持自动启动和重启
"""

import os
import sys
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil
import threading
import time
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONUNBUFFERED', '1')

class SHPServiceWindowsService(win32serviceutil.ServiceFramework):
    """Windows服务类"""
    
    # 服务配置
    _svc_name_ = "SHPService"
    _svc_display_name_ = "SHP Service Backend"
    _svc_description_ = "高性能GIS数据处理和地图服务后端API"
    
    # 服务依赖（如果需要）
    _svc_deps_ = ["EventLog"]
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        self.server_thread = None
        
        # 配置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置服务日志"""
        log_dir = Path(project_root) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "windows_service.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self._svc_name_)
        
    def SvcStop(self):
        """停止服务"""
        self.logger.info("正在停止 SHP Service...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        
        # 设置停止事件
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        
        # 等待服务器线程结束
        if self.server_thread and self.server_thread.is_alive():
            self.logger.info("等待服务器线程结束...")
            self.server_thread.join(timeout=30)
            
        self.logger.info("SHP Service 已停止")
        
    def SvcDoRun(self):
        """运行服务"""
        # 记录服务启动
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.logger.info("SHP Service 正在启动...")
        
        try:
            # 创建并启动服务器线程
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            self.logger.info("SHP Service 启动成功")
            
            # 等待停止信号
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
        except Exception as e:
            self.logger.error(f"服务运行失败: {e}")
            servicemanager.LogErrorMsg(f"SHP Service 运行失败: {e}")
            
        finally:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, '')
            )
    
    def run_server(self):
        """运行Flask服务器"""
        try:
            # 导入服务器模块
            from waitress_production import start_server
            
            self.logger.info("启动 Waitress 生产服务器...")
            start_server()
            
        except ImportError:
            # 降级到基本 Waitress 配置
            self.logger.warning("waitress_production 模块未找到，使用基本配置")
            self.run_basic_server()
            
        except Exception as e:
            self.logger.error(f"服务器启动失败: {e}")
            
    def run_basic_server(self):
        """运行基本服务器配置"""
        try:
            from waitress import serve
            from wsgi import app
            import multiprocessing
            
            # 基本配置
            host = "0.0.0.0"
            port = 5030
            threads = min(multiprocessing.cpu_count() * 2, 20)
            
            self.logger.info(f"启动基本服务器 - {host}:{port}, 线程数: {threads}")
            
            serve(
                app,
                host=host,
                port=port,
                threads=threads,
                connection_limit=500,
                channel_timeout=120
            )
            
        except Exception as e:
            self.logger.error(f"基本服务器启动失败: {e}")

def install_service():
    """安装Windows服务"""
    print("正在安装 SHP Service Windows 服务...")
    
    try:
        # 安装服务
        win32serviceutil.InstallService(
            SHPServiceWindowsService,
            SHPServiceWindowsService._svc_name_,
            SHPServiceWindowsService._svc_display_name_,
            description=SHPServiceWindowsService._svc_description_,
            startType=win32service.SERVICE_AUTO_START  # 自动启动
        )
        print("✅ SHP Service 服务安装成功")
        print(f"   服务名称: {SHPServiceWindowsService._svc_name_}")
        print(f"   显示名称: {SHPServiceWindowsService._svc_display_name_}")
        print("   启动类型: 自动")
        
        # 设置服务描述
        import win32api
        import win32con
        
        # 打开服务管理器
        sc_manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        service = win32service.OpenService(sc_manager, SHPServiceWindowsService._svc_name_, win32service.SERVICE_ALL_ACCESS)
        
        # 设置服务描述
        win32service.ChangeServiceConfig2(
            service, 
            win32service.SERVICE_CONFIG_DESCRIPTION, 
            SHPServiceWindowsService._svc_description_
        )
        
        # 设置失败恢复策略
        win32service.ChangeServiceConfig2(
            service,
            win32service.SERVICE_CONFIG_FAILURE_ACTIONS,
            {
                'ResetPeriod': 86400,  # 24小时重置计数
                'RebootMsg': '',
                'Command': '',
                'Actions': [
                    (win32service.SC_ACTION_RESTART, 60000),    # 1分钟后重启
                    (win32service.SC_ACTION_RESTART, 120000),   # 2分钟后重启
                    (win32service.SC_ACTION_RESTART, 300000),   # 5分钟后重启
                ]
            }
        )
        
        win32service.CloseServiceHandle(service)
        win32service.CloseServiceHandle(sc_manager)
        
        print("✅ 服务恢复策略设置成功")
        
    except Exception as e:
        print(f"❌ 服务安装失败: {e}")
        return False
    
    return True

def uninstall_service():
    """卸载Windows服务"""
    print("正在卸载 SHP Service Windows 服务...")
    
    try:
        # 先停止服务
        stop_service()
        
        # 卸载服务
        win32serviceutil.RemoveService(SHPServiceWindowsService._svc_name_)
        print("✅ SHP Service 服务卸载成功")
        
    except Exception as e:
        print(f"❌ 服务卸载失败: {e}")
        return False
    
    return True

def start_service():
    """启动服务"""
    print("正在启动 SHP Service...")
    
    try:
        win32serviceutil.StartService(SHPServiceWindowsService._svc_name_)
        print("✅ SHP Service 启动成功")
        
        # 检查服务状态
        time.sleep(2)
        status = win32serviceutil.QueryServiceStatus(SHPServiceWindowsService._svc_name_)[1]
        if status == win32service.SERVICE_RUNNING:
            print("✅ 服务运行状态确认")
        else:
            print(f"⚠️  服务状态: {status}")
            
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        return False
    
    return True

def stop_service():
    """停止服务"""
    print("正在停止 SHP Service...")
    
    try:
        win32serviceutil.StopService(SHPServiceWindowsService._svc_name_)
        print("✅ SHP Service 停止成功")
        
    except Exception as e:
        print(f"❌ 服务停止失败: {e}")
        return False
    
    return True

def restart_service():
    """重启服务"""
    print("正在重启 SHP Service...")
    
    if stop_service():
        time.sleep(3)
        return start_service()
    
    return False

def service_status():
    """查看服务状态"""
    try:
        status = win32serviceutil.QueryServiceStatus(SHPServiceWindowsService._svc_name_)
        
        status_map = {
            win32service.SERVICE_STOPPED: "已停止",
            win32service.SERVICE_START_PENDING: "启动中",
            win32service.SERVICE_STOP_PENDING: "停止中",
            win32service.SERVICE_RUNNING: "运行中",
            win32service.SERVICE_CONTINUE_PENDING: "继续中",
            win32service.SERVICE_PAUSE_PENDING: "暂停中",
            win32service.SERVICE_PAUSED: "已暂停"
        }
        
        current_status = status_map.get(status[1], f"未知状态({status[1]})")
        
        print(f"SHP Service 状态: {current_status}")
        print(f"服务类型: {status[0]}")
        print(f"控制接受: {status[2]}")
        print(f"退出代码: {status[3]}")
        print(f"服务退出代码: {status[4]}")
        print(f"检查点: {status[5]}")
        print(f"等待提示: {status[6]}")
        
        return status[1] == win32service.SERVICE_RUNNING
        
    except Exception as e:
        print(f"❌ 无法查询服务状态: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) == 1:
        print("SHP Service Windows 服务管理工具")
        print("=" * 50)
        print("使用方法:")
        print("  python windows_service.py install    - 安装服务")
        print("  python windows_service.py uninstall  - 卸载服务")
        print("  python windows_service.py start      - 启动服务")
        print("  python windows_service.py stop       - 停止服务")
        print("  python windows_service.py restart    - 重启服务")
        print("  python windows_service.py status     - 查看状态")
        print("  python windows_service.py debug      - 调试模式运行")
        return
    
    command = sys.argv[1].lower()
    
    if command == "install":
        if install_service():
            print("\n🎉 安装完成！可以使用以下命令管理服务:")
            print("   python windows_service.py start")
            print("   python windows_service.py stop")
            print("   python windows_service.py status")
            
    elif command == "uninstall":
        uninstall_service()
        
    elif command == "start":
        start_service()
        
    elif command == "stop":
        stop_service()
        
    elif command == "restart":
        restart_service()
        
    elif command == "status":
        service_status()
        
    elif command == "debug":
        # 调试模式 - 直接运行服务代码
        print("调试模式运行...")
        service = SHPServiceWindowsService([])
        service.run_server()
        
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['install', 'remove', 'start', 'stop', 'restart']:
        # 使用 win32serviceutil 的标准命令行处理
        win32serviceutil.HandleCommandLine(SHPServiceWindowsService)
    else:
        main()
