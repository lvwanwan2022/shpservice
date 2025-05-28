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
        tables = self.get_postgis_tables()
        
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
                'tables': {}
            }
        }
        
        # 添加发现的表作为瓦片源
        for table in tables:
            table_id = table['source_id']
            config['postgres']['tables'][table_id] = {
                'schema': table['schema'],
                'table': table['table'],
                'geometry_column': table['geometry_column'],
                'srid': table['srid'],
                'geometry_type': table['geometry_type']
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
            self.process = subprocess.Popen(cmd, 
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
            
            # 等待服务启动
            time.sleep(3)
            
            if self.is_running():
                logger.info(f"Martin 服务已启动: {self.base_url}")
                return True
            else:
                logger.error("Martin 服务启动失败")
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
    
    def refresh_tables(self) -> bool:
        """刷新表配置（重新生成配置并重启服务）"""
        if self.is_running():
            self.stop_service()
            time.sleep(1)
        
        return self.start_service()
    
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