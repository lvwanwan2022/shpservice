#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SHP Service 性能监控工具
实时监控服务器性能和健康状态
"""

import os
import sys
import time
import psutil
import requests
import threading
import logging
import json
import socket
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import deque
import argparse

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, monitor_ports=None, interval=5, history_size=100):
        self.monitor_ports = monitor_ports or [5030, 5031, 5032, 5033]
        self.interval = interval
        self.history_size = history_size
        self.is_running = True
        
        # 历史数据存储
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        self.response_time_history = deque(maxlen=history_size)
        self.timestamp_history = deque(maxlen=history_size)
        
        # 服务状态
        self.service_status = {}
        
        # 配置日志
        self.setup_logging()
        
        # 性能阈值
        self.thresholds = {
            'cpu_critical': 80.0,
            'cpu_warning': 60.0,
            'memory_critical': 85.0,
            'memory_warning': 70.0,
            'response_time_critical': 5.0,
            'response_time_warning': 2.0,
            'disk_critical': 90.0,
            'disk_warning': 80.0
        }
    
    def setup_logging(self):
        """设置日志"""
        log_dir = Path(project_root) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "performance_monitor.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("PerformanceMonitor")
    
    def get_system_info(self):
        """获取系统信息"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # 内存信息
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘信息
            disk = psutil.disk_usage('.')
            
            # 网络信息
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq.current if cpu_freq else 0
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.used / disk.total * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return None
    
    def get_process_info(self):
        """获取进程信息"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                if 'python' in proc.info['name'].lower():
                    # 检查是否是我们的服务进程
                    try:
                        connections = proc.connections()
                        for conn in connections:
                            if conn.laddr.port in self.monitor_ports:
                                processes.append({
                                    'pid': proc.info['pid'],
                                    'name': proc.info['name'],
                                    'port': conn.laddr.port,
                                    'cpu_percent': proc.info['cpu_percent'],
                                    'memory_percent': proc.info['memory_percent'],
                                    'create_time': proc.info['create_time'],
                                    'status': proc.status()
                                })
                                break
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        continue
        except Exception as e:
            self.logger.error(f"获取进程信息失败: {e}")
        
        return processes
    
    def check_service_health(self, port):
        """检查服务健康状态"""
        try:
            start_time = time.time()
            
            # 检查端口是否监听
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:
                return {
                    'port': port,
                    'status': 'down',
                    'response_time': None,
                    'error': 'Port not listening'
                }
            
            # 尝试HTTP健康检查
            try:
                response = requests.get(
                    f'http://127.0.0.1:{port}/health',
                    timeout=5
                )
                response_time = time.time() - start_time
                
                return {
                    'port': port,
                    'status': 'up' if response.status_code == 200 else 'unhealthy',
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': None
                }
            except requests.RequestException:
                # 如果没有健康检查端点，尝试根路径
                try:
                    response = requests.get(
                        f'http://127.0.0.1:{port}/',
                        timeout=5
                    )
                    response_time = time.time() - start_time
                    
                    return {
                        'port': port,
                        'status': 'up',
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'error': None
                    }
                except:
                    response_time = time.time() - start_time
                    return {
                        'port': port,
                        'status': 'unhealthy',
                        'response_time': response_time,
                        'error': 'HTTP request failed'
                    }
            
        except Exception as e:
            return {
                'port': port,
                'status': 'error',
                'response_time': None,
                'error': str(e)
            }
    
    def analyze_performance(self, system_info):
        """性能分析"""
        issues = []
        warnings = []
        
        if not system_info:
            return [], ['系统信息获取失败']
        
        # CPU分析
        cpu_percent = system_info['cpu']['percent']
        if cpu_percent > self.thresholds['cpu_critical']:
            issues.append(f"CPU使用率过高: {cpu_percent:.1f}%")
        elif cpu_percent > self.thresholds['cpu_warning']:
            warnings.append(f"CPU使用率偏高: {cpu_percent:.1f}%")
        
        # 内存分析
        memory_percent = system_info['memory']['percent']
        if memory_percent > self.thresholds['memory_critical']:
            issues.append(f"内存使用率过高: {memory_percent:.1f}%")
        elif memory_percent > self.thresholds['memory_warning']:
            warnings.append(f"内存使用率偏高: {memory_percent:.1f}%")
        
        # 磁盘分析
        disk_percent = system_info['disk']['percent']
        if disk_percent > self.thresholds['disk_critical']:
            issues.append(f"磁盘空间不足: {disk_percent:.1f}%")
        elif disk_percent > self.thresholds['disk_warning']:
            warnings.append(f"磁盘空间偏低: {disk_percent:.1f}%")
        
        # 交换空间分析
        if system_info['swap']['total'] > 0:
            swap_percent = system_info['swap']['percent']
            if swap_percent > 50:
                warnings.append(f"交换空间使用过多: {swap_percent:.1f}%")
        
        return issues, warnings
    
    def format_bytes(self, bytes_value):
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def display_status(self):
        """显示状态信息"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 80)
        print("🖥️  SHP Service 性能监控仪表板")
        print("=" * 80)
        print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 监控间隔: {self.interval}秒")
        print(f"📊 监控端口: {', '.join(map(str, self.monitor_ports))}")
        print("=" * 80)
        
        # 获取系统信息
        system_info = self.get_system_info()
        if system_info:
            # 系统资源状态
            print("\n📊 系统资源状态:")
            print("-" * 40)
            
            cpu_percent = system_info['cpu']['percent']
            memory_percent = system_info['memory']['percent']
            disk_percent = system_info['disk']['percent']
            
            # CPU状态
            cpu_status = "🔴" if cpu_percent > self.thresholds['cpu_critical'] else \
                        "🟡" if cpu_percent > self.thresholds['cpu_warning'] else "🟢"
            print(f"CPU: {cpu_status} {cpu_percent:5.1f}% ({system_info['cpu']['count']} 核心)")
            
            # 内存状态
            memory_status = "🔴" if memory_percent > self.thresholds['memory_critical'] else \
                           "🟡" if memory_percent > self.thresholds['memory_warning'] else "🟢"
            memory_used = self.format_bytes(system_info['memory']['used'])
            memory_total = self.format_bytes(system_info['memory']['total'])
            print(f"内存: {memory_status} {memory_percent:5.1f}% ({memory_used}/{memory_total})")
            
            # 磁盘状态
            disk_status = "🔴" if disk_percent > self.thresholds['disk_critical'] else \
                         "🟡" if disk_percent > self.thresholds['disk_warning'] else "🟢"
            disk_used = self.format_bytes(system_info['disk']['used'])
            disk_total = self.format_bytes(system_info['disk']['total'])
            print(f"磁盘: {disk_status} {disk_percent:5.1f}% ({disk_used}/{disk_total})")
            
            # 存储历史数据
            self.cpu_history.append(cpu_percent)
            self.memory_history.append(memory_percent)
            self.timestamp_history.append(system_info['timestamp'])
        
        # 服务状态
        print("\n🚀 服务状态:")
        print("-" * 40)
        
        total_response_time = 0
        active_services = 0
        
        for port in self.monitor_ports:
            health = self.check_service_health(port)
            self.service_status[port] = health
            
            status_icon = {
                'up': '🟢',
                'down': '🔴',
                'unhealthy': '🟡',
                'error': '❌'
            }.get(health['status'], '❓')
            
            response_time = health.get('response_time')
            if response_time is not None:
                total_response_time += response_time
                active_services += 1
                rt_str = f"{response_time*1000:.0f}ms"
            else:
                rt_str = "N/A"
            
            print(f"端口 {port}: {status_icon} {health['status'].upper():10} 响应时间: {rt_str:8}")
        
        # 平均响应时间
        if active_services > 0:
            avg_response_time = total_response_time / active_services
            self.response_time_history.append(avg_response_time)
            
            rt_status = "🔴" if avg_response_time > self.thresholds['response_time_critical'] else \
                       "🟡" if avg_response_time > self.thresholds['response_time_warning'] else "🟢"
            print(f"\n平均响应时间: {rt_status} {avg_response_time*1000:.0f}ms")
        
        # 进程信息
        processes = self.get_process_info()
        if processes:
            print(f"\n🔧 服务进程 ({len(processes)} 个):")
            print("-" * 40)
            for proc in processes:
                print(f"PID {proc['pid']:5} 端口 {proc['port']:4} "
                      f"CPU: {proc['cpu_percent']:5.1f}% "
                      f"内存: {proc['memory_percent']:5.1f}%")
        
        # 性能分析
        if system_info:
            issues, warnings = self.analyze_performance(system_info)
            
            if issues:
                print(f"\n🚨 性能问题 ({len(issues)} 个):")
                print("-" * 40)
                for issue in issues:
                    print(f"❌ {issue}")
            
            if warnings:
                print(f"\n⚠️  性能警告 ({len(warnings)} 个):")
                print("-" * 40)
                for warning in warnings:
                    print(f"🟡 {warning}")
            
            if not issues and not warnings:
                print(f"\n✅ 系统性能正常")
        
        print("\n" + "=" * 80)
        print("💡 提示: 按 Ctrl+C 退出监控")
        print("=" * 80)
    
    def save_report(self):
        """保存性能报告"""
        try:
            report_dir = Path(project_root) / "logs" / "performance_reports"
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = report_dir / f"performance_report_{timestamp}.json"
            
            # 准备报告数据
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'system_info': self.get_system_info(),
                'service_status': self.service_status,
                'processes': self.get_process_info(),
                'performance_history': {
                    'cpu': list(self.cpu_history),
                    'memory': list(self.memory_history),
                    'response_time': list(self.response_time_history),
                    'timestamps': [t.isoformat() for t in self.timestamp_history]
                }
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"性能报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存性能报告失败: {e}")
    
    def generate_chart(self):
        """生成性能图表"""
        try:
            if len(self.timestamp_history) < 2:
                return
            
            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('SHP Service 性能监控', fontsize=16)
            
            timestamps = list(self.timestamp_history)
            
            # CPU使用率
            ax1.plot(timestamps, list(self.cpu_history), 'b-', label='CPU使用率')
            ax1.axhline(y=self.thresholds['cpu_warning'], color='yellow', linestyle='--', alpha=0.7)
            ax1.axhline(y=self.thresholds['cpu_critical'], color='red', linestyle='--', alpha=0.7)
            ax1.set_title('CPU使用率 (%)')
            ax1.set_ylabel('百分比')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # 内存使用率
            ax2.plot(timestamps, list(self.memory_history), 'g-', label='内存使用率')
            ax2.axhline(y=self.thresholds['memory_warning'], color='yellow', linestyle='--', alpha=0.7)
            ax2.axhline(y=self.thresholds['memory_critical'], color='red', linestyle='--', alpha=0.7)
            ax2.set_title('内存使用率 (%)')
            ax2.set_ylabel('百分比')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 响应时间
            if self.response_time_history:
                response_times_ms = [rt * 1000 for rt in self.response_time_history]
                ax3.plot(timestamps[-len(response_times_ms):], response_times_ms, 'r-', label='响应时间')
                ax3.axhline(y=self.thresholds['response_time_warning']*1000, color='yellow', linestyle='--', alpha=0.7)
                ax3.axhline(y=self.thresholds['response_time_critical']*1000, color='red', linestyle='--', alpha=0.7)
                ax3.set_title('响应时间 (ms)')
                ax3.set_ylabel('毫秒')
                ax3.grid(True, alpha=0.3)
                ax3.legend()
            
            # 服务状态
            ports = list(self.service_status.keys())
            statuses = [1 if self.service_status[port]['status'] == 'up' else 0 for port in ports]
            ax4.bar(range(len(ports)), statuses, color=['green' if s else 'red' for s in statuses])
            ax4.set_title('服务状态')
            ax4.set_ylabel('在线状态')
            ax4.set_xticks(range(len(ports)))
            ax4.set_xticklabels([f':{port}' for port in ports])
            ax4.set_ylim(0, 1.2)
            
            # 格式化时间轴
            for ax in [ax1, ax2, ax3]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # 保存图表
            chart_dir = Path(project_root) / "logs" / "performance_charts"
            chart_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            chart_file = chart_dir / f"performance_chart_{timestamp}.png"
            
            plt.savefig(chart_file, dpi=150, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"性能图表已保存: {chart_file}")
            
        except Exception as e:
            self.logger.error(f"生成性能图表失败: {e}")
    
    def run_monitor(self):
        """运行监控"""
        self.logger.info("启动性能监控...")
        
        try:
            while self.is_running:
                self.display_status()
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止监控...")
        finally:
            self.is_running = False
            
            # 保存最终报告
            self.save_report()
            
            # 生成图表
            if len(self.timestamp_history) > 1:
                self.generate_chart()
            
            print("\n📊 性能监控已停止")
            print("📁 报告和图表已保存到 logs/ 目录")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SHP Service 性能监控工具')
    parser.add_argument('--ports', nargs='+', type=int, default=[5030, 5031, 5032, 5033],
                       help='监控的端口列表 (默认: 5030 5031 5032 5033)')
    parser.add_argument('--interval', type=int, default=5,
                       help='监控间隔（秒） (默认: 5)')
    parser.add_argument('--history', type=int, default=100,
                       help='历史数据数量 (默认: 100)')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = PerformanceMonitor(
        monitor_ports=args.ports,
        interval=args.interval,
        history_size=args.history
    )
    
    # 运行监控
    monitor.run_monitor()

if __name__ == '__main__':
    main()
