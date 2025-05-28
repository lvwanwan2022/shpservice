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
                        'source_id_format': '{schema}.{table}',
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
                lines.append(self._dict_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")
        return "\n".join(lines)
    
    def start_service(self) -> bool:
        """启动 Martin 服务"""
        if not self.is_enabled():
            logger.info("Martin 服务未启用")
            return False
            
        if not self.check_martin_installed():
            logger.warning("Martin 未安装，尝试安装...")
            if not self.install_martin():
                logger.error("Martin 安装失败，无法启动服务")
                return False
        
        if not self.write_config_file():
            logger.error("配置文件生成失败")
            return False
            
        try:
            # 启动 Martin 进程
            cmd = [self.martin_executable, '--config', self.config_file_path]
            logger.info(f"正在启动 Martin 服务: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(cmd, 
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=True,
                                          bufsize=1,
                                          universal_newlines=True)
            
            # 等待服务启动并收集初始日志
            logger.info("等待 Martin 服务启动...")
            time.sleep(3)
            
            # 检查进程是否仍在运行
            if self.process.poll() is not None:
                # 进程已退出，获取错误信息
                stdout, stderr = self.process.communicate()
                logger.error("Martin 服务启动失败")
                if stdout:
                    logger.error(f"标准输出: {stdout}")
                if stderr:
                    logger.error(f"错误输出: {stderr}")
                return False
            
            if self.is_running():
                logger.info(f"Martin 服务已成功启动: {self.base_url}")
                # 显示一些启动信息
                catalog = self.get_catalog()
                if catalog and 'tiles' in catalog:
                    tables_count = len(catalog['tiles'])
                    logger.info(f"发现并发布了 {tables_count} 个数据表")
                    for table_name in catalog['tiles'].keys():
                        logger.info(f"  - {table_name}")
                return True
            else:
                logger.error("Martin 服务启动失败 - 健康检查未通过")
                return False
                
        except Exception as e:
            logger.error(f"启动 Martin 服务失败: {e}")
            return False
    
    def stop_service(self) -> bool:
        """停止 Martin 服务"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("Martin 服务已停止")
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("强制终止 Martin 服务")
                return True
            except Exception as e:
                logger.error(f"停止 Martin 服务失败: {e}")
                return False
        return True
    
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
            # 尝试读取已缓存的输出
            if hasattr(self, '_stdout_lines'):
                logs['stdout'] = '\n'.join(self._stdout_lines[-lines:])
            if hasattr(self, '_stderr_lines'):
                logs['stderr'] = '\n'.join(self._stderr_lines[-lines:])
                
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
            'tables_count': len(self.get_postgis_tables())
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
        """刷新表配置 - 重新生成配置文件并重启Martin服务"""
        try:
            logger.info("开始刷新Martin表配置...")
            
            # 1. 停止当前服务
            if self.is_running():
                logger.info("停止当前Martin服务...")
                self.stop_service()
                
                # 等待服务完全停止
                import time
                time.sleep(2)
            
            # 2. 重新生成配置文件
            logger.info("重新生成配置文件...")
            if not self.write_config_file():
                logger.error("配置文件生成失败")
                return False
            
            # 3. 重新启动服务
            logger.info("重新启动Martin服务...")
            if not self.start_service():
                logger.error("Martin服务启动失败")
                return False
            
            # 4. 等待服务启动并验证
            import time
            time.sleep(3)  # 给服务一些启动时间
            
            if self.is_running():
                tables_count = len(self.get_postgis_tables())
                logger.info(f"Martin表配置刷新成功，发现 {tables_count} 个表")
                return True
            else:
                logger.error("Martin服务启动后验证失败")
                return False
                
        except Exception as e:
            logger.error(f"刷新表配置失败: {e}")
            return False 