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
        self.config_file_path = os.path.join(os.path.dirname(__file__), 'martin_config.yaml')
        
        # 修复Windows上的连接问题：服务器监听0.0.0.0，但客户端连接使用localhost
        host = self.config['host']
        if host == '0.0.0.0':
            client_host = 'localhost'
        else:
            client_host = host
            
        self.base_url = f"http://{client_host}:{self.config['port']}"
        # 获取 Martin 可执行文件路径
        self.martin_executable = self.config.get('martin_executable', 'martin')
        
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
        """备用启动方法 - 直接subprocess启动"""
        if not self.is_enabled():
            logger.info("Martin 服务未启用")
            return False
            
        if not self.check_martin_installed():
            logger.error("Martin 未安装")
            return False
        
        if not os.path.exists(self.config_file_path):
            logger.error(f"配置文件不存在: {self.config_file_path}")
            return False
            
        try:
            cmd = [self.martin_executable, '--config', self.config_file_path]
            logger.info(f"直接启动Martin: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(cmd, 
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=False)
            
            import time
            time.sleep(3)
            
            if self.process.poll() is not None:
                logger.error("Martin进程启动后立即退出")
                return False
            
            if self.is_running():
                logger.info("Martin服务启动成功")
                return True
            else:
                logger.error("Martin服务无法访问")
                return False
                
        except Exception as e:
            logger.error(f"启动Martin失败: {e}")
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
        """简单kill Martin进程"""
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
            
            # 强制kill所有Martin进程
            try:
                result = subprocess.run(['taskkill', '/f', '/im', 'martin.exe'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("已kill所有martin.exe进程")
                else:
                    logger.info("没有找到运行中的martin.exe进程")
            except Exception as e:
                logger.debug(f"kill进程命令执行失败: {e}")
            
            logger.info("Martin进程已清理")
            return True
            
        except Exception as e:
            logger.error(f"停止Martin服务失败: {e}")
            return False

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
    
    def is_running(self) -> bool:
        """检查 Martin 服务是否运行中"""
        try:
            # 尝试访问health端点
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return True
            
            # 如果health端点不可用，尝试访问根路径
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
            
        except requests.exceptions.ConnectionError:
            # 连接被拒绝，服务未运行
            return False
        except requests.exceptions.Timeout:
            # 超时，可能服务有问题
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
        """重启Martin服务 - 使用kill+bat方式"""
        try:
            logger.info("=== 重启Martin服务 ===")
            
            # 1. Kill所有Martin进程
            logger.info("正在清理Martin进程...")
            self.stop_service()
            
            # 2. 等待一下让系统清理资源
            import time
            time.sleep(2)
            
            # 3. 使用bat后台启动Martin服务
            logger.info("正在使用bat后台启动Martin服务...")
            if self.start_service_with_bat(background=True):
                # 4. 等待服务启动并验证
                time.sleep(4)  # 给bat启动一些时间
                
                if self.is_running():
                    logger.info("✅ Martin服务重启成功")
                    return True
                else:
                    logger.warning("⚠️ Martin启动命令已执行，服务可能正在启动中...")
                    return True  # bat命令执行成功就算成功
            else:
                logger.error("❌ bat启动命令执行失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Martin服务重启失败: {e}")
            return False 