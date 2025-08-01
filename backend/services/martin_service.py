"""
Martin 瓦片服务管理
提供 MVT (Mapbox Vector Tiles) 服务，作为 GeoServer 的现代化替代方案
"""

import os
import json
import subprocess
import requests
import logging
import time
import socket
from typing import Dict, List, Optional, Tuple
import psycopg2
from config import MARTIN_CONFIG, DB_CONFIG

logger = logging.getLogger(__name__)

class MartinService:
    """Martin 瓦片服务管理器"""
    
    def __init__(self):
        self.config = MARTIN_CONFIG
        self.db_config = DB_CONFIG
        self.process = None
        self.config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'martin_config.yaml')
        
        # 修复Windows上的连接问题：服务器监听0.0.0.0，但客户端连接使用localhost
        host = self.config['host']
        if host == '0.0.0.0':
            client_host = 'localhost'
        else:
            client_host = host
            
        self.base_url = f"http://{client_host}:{self.config['port']}"
        
        # 获取 Martin 可执行文件路径
        self.martin_executable = self.config.get('martin_executable', 'martin')
        
        # 检查可执行文件是否存在
        if self.martin_executable and not os.path.isfile(self.martin_executable):
            logger.warning(f"⚠️ 配置的Martin可执行文件不存在: {self.martin_executable}")
            logger.warning("将尝试使用系统PATH中的martin命令")
            self.martin_executable = 'martin'
        else:
            logger.info(f"✅ 使用Martin可执行文件: {self.martin_executable}")
        
    def is_enabled(self) -> bool:
        """检查 Martin 服务是否启用"""
        return self.config.get('enabled', False)
        
    def check_martin_installed(self) -> bool:
        """检查 Martin 是否已安装"""
        try:
            result = subprocess.run([self.martin_executable, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def install_martin(self) -> bool:
        """安装 Martin (通过 cargo)"""
        try:
            logger.info("正在安装 Martin...")
            result = subprocess.run(['cargo', 'install', 'martin'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info("Martin 安装成功")
                return True
            else:
                logger.error(f"Martin 安装失败: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"无法安装 Martin: {e}")
            return False
    
    def get_postgis_tables(self) -> List[Dict]:
        """获取 PostGIS 数据库中的空间表"""
        tables = []
        try:
            # 创建数据库连接，排除 schema 参数
            db_params = {k: v for k, v in self.db_config.items() if k != 'schema'}
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # 查询包含几何列的表
            query = """
            SELECT 
                f_table_schema,
                f_table_name,
                f_geometry_column,
                srid,
                type
            FROM geometry_columns
            WHERE f_table_schema = %s
            """
            
            cursor.execute(query, (self.db_config['schema'],))
            results = cursor.fetchall()
            
            for row in results:
                schema, table, geom_col, srid, geom_type = row
                tables.append({
                    'schema': schema,
                    'table': table,
                    'geometry_column': geom_col,
                    'srid': srid,
                    'geometry_type': geom_type,
                    'source_id': f"{schema}.{table}"
                })
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"查询 PostGIS 表失败: {e}")
            
        return tables
    
    def generate_config(self) -> Dict:
        """生成 Martin 配置文件内容"""
        # 处理 worker_processes 配置
        worker_processes = self.config['worker_processes']
        if worker_processes == 'auto':
            import os
            worker_processes = os.cpu_count() or 4  # 默认 4 个进程
        
        config = {
            'listen_addresses': f"{self.config['host']}:{self.config['port']}",
            'worker_processes': worker_processes,
            'cache_size_mb': self.config['cache_size'],
            'postgres': {
                'connection_string': self.config['postgres_connection'],
                'pool_size': self.config['pool_size'],
                # 启用自动发现 - Martin会自动发现数据库中的所有空间表
                'auto_publish': {
                    'tables': {
                        'source_id_format': '{schema}.{table}',  # 这个会被YAML处理器正确引用
                        'from_schemas': [self.db_config['schema']],  # 只发现指定schema
                        # 可选：过滤条件
                        'id_regex': '^geojson_.*',  # 只发布以geojson_开头的表
                    },
                    'functions': False  # 不自动发布函数
                }
            }
        }
        
        return config
    
    def write_config_file(self) -> bool:
        """写入 Martin 配置文件"""
        try:
            config = self.generate_config()
            
            # 转换为 YAML 格式
            yaml_content = self._dict_to_yaml(config)
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
                
            logger.info(f"Martin 配置文件已生成: {self.config_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成配置文件失败: {e}")
            return False
    
    def _dict_to_yaml(self, data: Dict, indent: int = 0) -> str:
        """简单的字典转 YAML 格式"""
        lines = []
        for key, value in data.items():
            prefix = "  " * indent
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                # 递归处理嵌套字典，并将结果按行分割后逐行添加
                nested_yaml = self._dict_to_yaml(value, indent + 1)
                for line in nested_yaml.split('\n'):
                    if line.strip():  # 只添加非空行
                        lines.append(line)
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        # 如果列表项是字典，需要特殊处理
                        lines.append(f"{prefix}  -")
                        nested_yaml = self._dict_to_yaml(item, indent + 2)
                        for line in nested_yaml.split('\n'):
                            if line.strip():
                                lines.append(f"  {line}")  # 额外缩进
                    else:
                        lines.append(f"{prefix}  - {item}")
            elif isinstance(value, bool):
                # 布尔值需要转换为小写
                lines.append(f"{prefix}{key}: {str(value).lower()}")
            elif isinstance(value, str):
                # 字符串值，如果包含特殊字符需要加引号
                if any(char in value for char in [':', '{', '}', '^']):
                    lines.append(f'{prefix}{key}: "{value}"')
                else:
                    lines.append(f"{prefix}{key}: {value}")
            else:
                lines.append(f"{prefix}{key}: {value}")
        return "\n".join(lines)
    
    def start_service(self) -> bool:
        """启动 Martin 服务"""
        if not self.is_enabled():
            logger.info("Martin 服务未启用")
            return False
            
        if not os.path.exists(self.martin_executable):
            logger.error(f"Martin 可执行文件不存在: {self.martin_executable}")
            return False
        
        if not os.path.exists(self.config_file_path):
            logger.info(f"配置文件不存在: {self.config_file_path}")
            logger.info("尝试生成配置文件...")
            if not self.write_config_file():
                logger.error("无法生成配置文件")
                return False
            logger.info(f"配置文件已生成: {self.config_file_path}")
            
        try:
            cmd = [self.martin_executable, '--config', self.config_file_path]
            logger.info(f"启动Martin: {' '.join(cmd)}")
            
            # 在Windows上使用特定的启动方式
            if os.name == 'nt':
                try:
                    # 使用startupinfo隐藏控制台窗口
                    import subprocess
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=False,
                        startupinfo=startupinfo
                    )
                    logger.info(f"Windows方式启动Martin进程，PID: {self.process.pid if self.process else 'unknown'}")
                except Exception as win_error:
                    logger.error(f"Windows特定启动方式失败: {win_error}")
                    # 回退到标准方式
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=False
                    )
            else:
                # 非Windows系统的标准启动方式
                self.process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=False
                )
            
            # 等待服务启动
            logger.info("等待Martin服务启动...")
            max_retries = 10  # 增加重试次数
            retry_interval = 2
            martin_port = self.config.get('port', 3000)
            
            for i in range(max_retries):
                # 检查进程是否已退出
                if self.process.poll() is not None:
                    exit_code = self.process.poll()
                    stderr_output = self._safe_decode(self.process.stderr.read() if self.process.stderr else b'')
                    logger.error(f"Martin进程启动后立即退出，退出码: {exit_code}")
                    logger.error(f"错误输出: {stderr_output}")
                    return False
                
                # 首先检查端口是否被占用（这是启动成功的主要指标）
                if self.check_port_in_use(martin_port):
                    logger.info(f"✅ 端口{martin_port}已被占用，Martin服务启动成功 (尝试 {i+1}/{max_retries})")
                    
                    # 进一步验证Martin服务的可访问性
                    if self.is_running():
                        logger.info(f"✅ Martin服务完全就绪并可访问")
                        return True
                    else:
                        logger.info(f"⚠️ 端口已占用但服务尚未完全就绪，继续等待...")
                        # 端口占用了，说明Martin在启动过程中，继续等待
                        time.sleep(retry_interval)
                        continue
                
                logger.info(f"端口{martin_port}尚未被占用，Martin服务正在启动... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            
            # 最后一次检查端口占用情况
            if self.check_port_in_use(martin_port):
                logger.info("✅ Martin服务启动成功（端口已被占用）")
                
                # 尝试最后一次验证服务可访问性
                if self.is_running():
                    logger.info("✅ Martin服务完全就绪")
                else:
                    logger.warning("⚠️ Martin服务端口已占用但HTTP访问可能需要更多时间")
                return True
            else:
                logger.error(f"❌ 端口{martin_port}未被占用，Martin服务启动失败")
                # 尝试获取错误输出
                if self.process and self.process.stderr:
                    stderr_output = self._safe_decode(self.process.stderr.read())
                    if stderr_output:
                        logger.error(f"错误输出: {stderr_output}")
                return False
                
        except Exception as e:
            logger.error(f"启动Martin失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _safe_decode(self, data: bytes) -> str:
        """安全地解码字节数据"""
        if not data:
            return ""
        
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，使用错误替换
        return data.decode('utf-8', errors='replace')
    
    def stop_service(self) -> bool:
        """停止Martin服务，同时杀掉martin.exe进程和占用端口的进程"""
        try:
            logger.info("正在停止Martin服务...")
            
            # 停止当前Python管理的进程
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except:
                    pass
                finally:
                    self.process = None
            
            # 获取Martin端口配置
            martin_port = self.config.get('port', 3000)
            logger.info(f"Martin服务端口: {martin_port}")
            
            # 根据操作系统选择不同的命令
            import platform
            system = platform.system().lower()
            
            if system == 'windows' or os.name == 'nt':
                # Windows系统的处理
                self._stop_service_windows(martin_port)
            else:
                # Linux/Unix系统的处理
                self._stop_service_linux(martin_port)
            
            logger.info("Martin服务已停止，进程和端口已清理")
            return True
            
        except Exception as e:
            logger.error(f"停止Martin服务失败: {e}")
            return False
    
    def _stop_service_windows(self, port: int) -> None:
        """Windows系统停止Martin服务"""
        # 1. 强制kill所有Martin进程
        try:
            result = subprocess.run(['taskkill', '/f', '/im', 'martin.exe'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("已kill所有martin.exe进程")
            else:
                logger.info("没有找到运行中的martin.exe进程")
        except Exception as e:
            logger.debug(f"kill martin.exe进程命令执行失败: {e}")
        
        # 2. 查找并杀掉占用端口的进程
        try:
            # 使用netstat查找占用端口的进程
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f':{port} ' in line and 'LISTENING' in line:
                        # 提取PID
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                # 杀掉占用端口的进程
                                kill_result = subprocess.run(['taskkill', '/f', '/pid', pid], 
                                                           capture_output=True, text=True)
                                if kill_result.returncode == 0:
                                    logger.info(f"已kill占用端口{port}的进程PID: {pid}")
                                else:
                                    logger.warning(f"无法kill占用端口{port}的进程PID: {pid}")
                            except Exception as e:
                                logger.debug(f"kill进程PID {pid}失败: {e}")
        except Exception as e:
            logger.debug(f"查找占用端口的进程失败: {e}")
    
    def _stop_service_linux(self, port: int) -> None:
        """Linux系统停止Martin服务"""
        # 1. 强制kill所有martin进程
        try:
            result = subprocess.run(['pkill', '-f', 'martin'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("已kill所有martin进程")
            else:
                logger.info("没有找到运行中的martin进程")
        except Exception as e:
            logger.debug(f"kill martin进程命令执行失败: {e}")
        
        # 2. 查找并杀掉占用端口的进程
        try:
            # 使用lsof查找占用端口的进程
            result = subprocess.run(['lsof', '-t', '-i', f':{port}'], 
                                 capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            # 杀掉占用端口的进程
                            kill_result = subprocess.run(['kill', '-9', pid.strip()], 
                                                       capture_output=True, text=True)
                            if kill_result.returncode == 0:
                                logger.info(f"已kill占用端口{port}的进程PID: {pid.strip()}")
                            else:
                                logger.warning(f"无法kill占用端口{port}的进程PID: {pid.strip()}")
                        except Exception as e:
                            logger.debug(f"kill进程PID {pid.strip()}失败: {e}")
            else:
                logger.info(f"没有找到占用端口{port}的进程")
                
        except FileNotFoundError:
            # 如果lsof不可用，尝试使用ss和netstat
            try:
                # 尝试使用ss命令
                result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if f':{port} ' in line:
                            # 提取PID信息 (格式通常是users:(("process",pid,fd)))
                            import re
                            pid_match = re.search(r'pid=(\d+)', line)
                            if not pid_match:
                                pid_match = re.search(r'"[^"]*",(\d+),', line)
                            
                            if pid_match:
                                pid = pid_match.group(1)
                                try:
                                    kill_result = subprocess.run(['kill', '-9', pid], 
                                                               capture_output=True, text=True)
                                    if kill_result.returncode == 0:
                                        logger.info(f"已kill占用端口{port}的进程PID: {pid}")
                                except Exception as e:
                                    logger.debug(f"kill进程PID {pid}失败: {e}")
            except Exception as e:
                logger.debug(f"使用ss查找占用端口的进程失败: {e}")
                
        except Exception as e:
            logger.debug(f"查找占用端口的进程失败: {e}")

    def start_service_with_bat(self, background=False) -> bool:
        """使用现成的bat文件启动Martin服务"""
        try:
            # 获取项目根目录的Martin启动bat文件
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            if background:
                # 后台启动（不显示窗口）
                martin_bat_file = os.path.join(project_root, 'start_martin_background.bat')
                start_type = "后台"
            else:
                # 前台启动（显示窗口）
                martin_bat_file = os.path.join(project_root, 'start_martin_service.bat')
                start_type = "前台"
            
            if not os.path.exists(martin_bat_file):
                logger.error(f"Martin启动bat文件不存在: {martin_bat_file}")
                return False
            
            logger.info(f"使用bat文件{start_type}启动Martin服务: {martin_bat_file}")
            
            if background:
                # 后台启动
                subprocess.run([martin_bat_file], shell=True, cwd=project_root)
            else:
                # 前台启动（新窗口）
                cmd = ['start', 'Martin地图服务', 'cmd', '/k', f'"{martin_bat_file}"']
                subprocess.run(cmd, shell=True, cwd=project_root)
            
            logger.info(f"✅ Martin{start_type}启动命令已执行")
            return True
            
        except Exception as e:
            logger.error(f"❌ 使用bat启动Martin失败: {e}")
            return False
    
    def check_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            # 检查TCP端口
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0  # 0表示连接成功，端口被占用
        except Exception as e:
            logger.debug(f"检查端口{port}占用状态失败: {e}")
            return False

    def is_running(self) -> bool:
        """检查 Martin 服务是否运行中"""
        # 首先检查端口是否被占用
        martin_port = self.config.get('port', 3000)
        if not self.check_port_in_use(martin_port):
            logger.debug(f"端口{martin_port}未被占用，Martin服务未运行")
            return False
        
        try:
            # 端口被占用，进一步检查是否是Martin服务
            # 尝试访问health端点
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return True
            
            # 如果health端点不可用，尝试访问根路径
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
            
        except requests.exceptions.ConnectionError:
            # 端口被占用但连接被拒绝，可能是其他服务
            logger.debug(f"端口{martin_port}被占用但不是Martin服务")
            return False
        except requests.exceptions.Timeout:
            # 超时，可能服务有问题
            logger.debug(f"端口{martin_port}被占用但Martin服务响应超时")
            return False
        except Exception as e:
            logger.error(f"检查Martin服务状态失败: {e}")
            return False
    
    def get_catalog(self) -> Optional[Dict]:
        """获取 Martin 服务目录"""
        try:
            response = requests.get(f"{self.base_url}/catalog", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"获取目录失败: {e}")
        return None
    
    def get_table_info(self, table_id: str) -> Optional[Dict]:
        """获取特定表的信息"""
        try:
            response = requests.get(f"{self.base_url}/{table_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
        return None
    
    def get_mvt_url(self, table_id: str) -> str:
        """获取 MVT 瓦片 URL 模板"""
        return f"{self.base_url}/{table_id}/{{z}}/{{x}}/{{y}}.pbf"
    
    def get_process_logs(self, lines: int = 50) -> Dict[str, str]:
        """获取Martin进程的日志输出"""
        logs = {'stdout': '', 'stderr': '', 'status': 'not_running'}
        
        if self.process is None:
            logs['status'] = 'no_process'
            return logs
            
        # 检查进程状态
        if self.process.poll() is None:
            logs['status'] = 'running'
        else:
            logs['status'] = 'terminated'
            
        try:
            # 由于我们使用bytes模式，这里需要处理编码
            # 对于实时日志，我们可以尝试读取少量数据
            if self.process.stdout:
                try:
                    # 非阻塞读取
                    import select
                    import sys
                    
                    if sys.platform != 'win32':
                        # Unix系统使用select
                        ready, _, _ = select.select([self.process.stdout], [], [], 0)
                        if ready:
                            data = self.process.stdout.read(1024)
                            if data:
                                logs['stdout'] = self._safe_decode(data)
                    else:
                        # Windows系统，只在进程结束时获取输出
                        if self.process.poll() is not None:
                            try:
                                stdout_bytes, stderr_bytes = self.process.communicate(timeout=1)
                                logs['stdout'] = self._safe_decode(stdout_bytes)
                                logs['stderr'] = self._safe_decode(stderr_bytes)
                            except subprocess.TimeoutExpired:
                                pass
                except Exception as e:
                    logger.debug(f"读取stdout失败: {e}")
                    
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            logs['error'] = str(e)
            
        return logs
    
    def get_status(self) -> Dict:
        """获取服务状态信息"""
        return {
            'enabled': self.is_enabled(),
            'installed': self.check_martin_installed(),
            'running': self.is_running(),
            'base_url': self.base_url,
            'config_file': self.config_file_path,
            'config_exists': os.path.exists(self.config_file_path)
        }
    
    def get_martin_version(self) -> str:
        """获取Martin版本信息"""
        try:
            result = subprocess.run([self.martin_executable, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"获取Martin版本失败: {e}")
        return "未知版本"
    
    def refresh_tables(self) -> bool:
        """重启Martin服务 - 更智能地处理重启过程"""
        try:
            logger.info("=== 重启Martin服务 ===")
            
            # 1. 停止当前服务
            logger.info("正在停止当前Martin服务...")
            self.stop_service()
            
            # 2. 等待一下让系统清理资源
            time.sleep(2)
            
            # 3. 检查Martin可执行文件
            if not os.path.exists(self.martin_executable):
                logger.error(f"❌ Martin可执行文件不存在: {self.martin_executable}")
                return False
                
            # 4. 确保配置文件存在
            if not os.path.exists(self.config_file_path):
                logger.info("配置文件不存在，尝试生成...")
                if not self.write_config_file():
                    logger.error("❌ 无法生成配置文件")
                    return False
            
            # 5. 尝试直接启动服务
            logger.info("尝试直接启动Martin服务...")
            if self.start_service():
                logger.info("✅ Martin服务直接启动成功")
                return True
                
            # 6. 如果直接启动失败，尝试使用bat文件启动
            logger.info("直接启动失败，尝试使用bat文件启动...")
            if self.start_service_with_bat(background=True):
                # 等待服务启动并验证（增加验证时间和次数）
                logger.info("等待bat启动的Martin服务...")
                martin_port = self.config.get('port', 3000)
                max_wait_time = 15  # 最多等待15秒
                check_interval = 1  # 每秒检查一次
                
                for i in range(max_wait_time):
                    # 检查端口是否被占用
                    if self.check_port_in_use(martin_port):
                        logger.info(f"✅ 端口{martin_port}已被占用，Martin服务通过bat启动成功")
                        
                        # 进一步验证HTTP访问
                        if self.is_running():
                            logger.info("✅ Martin服务完全就绪并可访问")
                        else:
                            logger.info("⚠️ Martin服务端口已占用，HTTP服务正在启动中")
                        return True
                    
                    logger.info(f"等待端口{martin_port}被占用... ({i+1}/{max_wait_time})")
                    time.sleep(check_interval)
                
                # 最后检查一次
                if self.check_port_in_use(martin_port):
                    logger.info("✅ Martin服务通过bat启动成功（端口已被占用）")
                    return True
                else:
                    logger.warning("⚠️ bat命令执行成功但Martin服务可能需要更多时间启动")
                    return True  # bat命令执行成功就算成功
            
            logger.error("❌ 所有启动方法均失败")
            return False
                
        except Exception as e:
            logger.error(f"❌ Martin服务重启失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def update_service_style(self, service_id: int, style_config: dict) -> dict:
        """更新Martin服务样式配置"""
        try:
            # 导入数据库工具
            from models.db import execute_query
            
            # 检查Martin服务是否存在
            check_sql = """
            SELECT id, vector_type, original_filename, style FROM vector_martin_services
            WHERE id = %s AND status = 'active'
            """
            result = execute_query(check_sql, (service_id,))
            
            if not result:
                return {
                    'success': False,
                    'error': f'Martin服务ID {service_id} 不存在'
                }
            
            service = result[0]
            logger.info(f"开始更新Martin服务 {service_id} 的样式，类型: {service['vector_type']}")
            
            # 将样式配置保存到style字段
            update_sql = """
            UPDATE vector_martin_services 
            SET style = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            # 转换为JSON字符串格式保存
            style_json = json.dumps(style_config, ensure_ascii=False)
            execute_query(update_sql, (style_json, service_id), fetch=False)
            
            logger.info(f"✅ Martin服务样式更新成功: {service_id}")
            
            return {
                'success': True,
                'data': {
                    'service_id': str(service_id),
                    'service_type': service['vector_type'],
                    'original_filename': service['original_filename'],
                    'style_config': style_config
                }
            }
            
        except Exception as e:
            logger.error(f"更新Martin服务样式失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新样式失败: {str(e)}'
            }

    def get_service_style(self, service_id: int) -> dict:
        """获取Martin服务样式配置"""
        try:
            # 导入数据库工具
            from models.db import execute_query
            
            # 检查Martin服务是否存在并获取样式配置
            sql = """
            SELECT id, vector_type, original_filename, style, vector_info FROM vector_martin_services
            WHERE id = %s AND status = 'active'
            """
            
            result = execute_query(sql, (service_id,))
            if not result:
                return {
                    'success': False,
                    'error': f'Martin服务ID {service_id} 不存在'
                }
            
            service = result[0]
            logger.info(f"获取Martin服务 {service_id} 的样式，类型: {service['vector_type']}")
            
            # 解析样式配置，优先从style字段读取
            style_config = {}
            
            # 首先从style字段读取（统一的样式存储字段）
            if service['style']:
                try:
                    if isinstance(service['style'], str):
                        style_config = json.loads(service['style'])
                    else:
                        style_config = service['style']
                    logger.info(f"从style字段读取到样式配置: {style_config}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"样式配置解析失败: {str(e)}")
                    style_config = {}
            
            # 如果style字段为空，但是是DXF类型，尝试从vector_info中读取（向后兼容）
            if not style_config and service['vector_type'] == 'dxf' and service['vector_info']:
                try:
                    vector_info = service['vector_info'] if isinstance(service['vector_info'], dict) else json.loads(service['vector_info'])
                    style_config = vector_info.get('style_config', {})
                    logger.info(f"从vector_info中读取到DXF样式配置: {style_config}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"DXF vector_info解析失败: {str(e)}")
            
            # 如果没有样式配置，提供默认配置
            if not style_config:
                style_config = {}
                logger.info(f"使用默认样式配置")
            
            return {
                'success': True,
                'data': {
                    'service_id': str(service_id),
                    'service_type': service['vector_type'],
                    'original_filename': service['original_filename'],
                    'style_config': style_config,
                    'vector_info': service['vector_info']
                }
            }
            
        except Exception as e:
            logger.error(f"获取Martin服务样式失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取样式失败: {str(e)}'
            }

    def apply_service_style(self, service_id: int, style_config: dict) -> dict:
        """应用Martin服务样式（保存并应用）"""
        try:
            # 导入数据库工具
            from models.db import execute_query
            
            # 检查Martin服务是否存在
            check_sql = """
            SELECT id, vector_type, original_filename, style, table_name FROM vector_martin_services
            WHERE id = %s AND status = 'active'
            """
            result = execute_query(check_sql, (service_id,))
            
            if not result:
                return {
                    'success': False,
                    'error': f'Martin服务ID {service_id} 不存在'
                }
            
            service = result[0]
            logger.info(f"开始应用Martin服务 {service_id} 的样式，类型: {service['vector_type']}")
            
            # 1. 保存样式配置到数据库
            update_sql = """
            UPDATE vector_martin_services 
            SET style = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            # 转换为JSON字符串格式保存
            style_json = json.dumps(style_config, ensure_ascii=False)
            execute_query(update_sql, (style_json, service_id), fetch=False)
            
            logger.info(f"✅ Martin服务样式配置已保存: {service_id}")
            
            # 2. 对于DXF图层，样式是在前端VectorGrid中应用的，不需要重新发布Martin服务
            # 但我们可以在这里做一些额外的处理，比如更新缓存等
            
            # 3. 返回成功响应
            return {
                'success': True,
                'data': {
                    'service_id': str(service_id),
                    'service_type': service['vector_type'],
                    'original_filename': service['original_filename'],
                    'table_name': service['table_name'],
                    'style_config': style_config,
                    'applied_at': 'now'
                }
            }
            
        except Exception as e:
            logger.error(f"应用Martin服务样式失败: {str(e)}")
            return {
                'success': False,
                'error': f'应用样式失败: {str(e)}'
            }


# 创建全局实例
martin_service = MartinService() 