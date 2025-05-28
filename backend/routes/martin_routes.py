"""
Martin 瓦片服务相关 API 路由
"""

from flask import Blueprint, jsonify, request
from flask_restx import Api, Resource, fields
import logging
from services.martin_service import MartinService

logger = logging.getLogger(__name__)

# 创建蓝图
martin_bp = Blueprint('martin', __name__, url_prefix='/api/martin')
api = Api(martin_bp, doc='/martin-docs/', title='Martin 瓦片服务 API', 
          description='Martin MVT 瓦片服务管理接口')

# 创建 Martin 服务实例
martin_service = MartinService()

# API 模型定义
service_status_model = api.model('ServiceStatus', {
    'enabled': fields.Boolean(description='服务是否启用'),
    'installed': fields.Boolean(description='Martin 是否已安装'),
    'running': fields.Boolean(description='服务是否运行中'),
    'base_url': fields.String(description='服务基础URL'),
    'config_file': fields.String(description='配置文件路径'),
    'tables_count': fields.Integer(description='可用表数量')
})

table_info_model = api.model('TableInfo', {
    'schema': fields.String(description='数据库模式'),
    'table': fields.String(description='表名'),
    'geometry_column': fields.String(description='几何列名'),
    'srid': fields.Integer(description='空间参考系统ID'),
    'geometry_type': fields.String(description='几何类型'),
    'source_id': fields.String(description='数据源ID')
})

mvt_info_model = api.model('MVTInfo', {
    'table_id': fields.String(description='表ID'),
    'mvt_url': fields.String(description='MVT瓦片URL模板'),
    'tilejson_url': fields.String(description='TileJSON URL')
})

@api.route('/status')
class ServiceStatus(Resource):
    @api.doc('get_martin_status')
    @api.marshal_with(service_status_model)
    def get(self):
        """获取 Martin 服务状态"""
        try:
            status = martin_service.get_status()
            return status, 200
        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return {'error': str(e)}, 500

@api.route('/start')
class StartService(Resource):
    @api.doc('start_martin_service')
    def post(self):
        """启动 Martin 服务"""
        try:
            if martin_service.is_running():
                return {'message': 'Martin 服务已在运行中', 'status': 'running'}, 200
            
            success = martin_service.start_service()
            if success:
                return {'message': 'Martin 服务启动成功', 'status': 'started'}, 200
            else:
                return {'message': 'Martin 服务启动失败', 'status': 'failed'}, 500
                
        except Exception as e:
            logger.error(f"启动服务失败: {e}")
            return {'error': str(e)}, 500

@api.route('/stop')
class StopService(Resource):
    @api.doc('stop_martin_service')
    def post(self):
        """停止 Martin 服务"""
        try:
            success = martin_service.stop_service()
            if success:
                return {'message': 'Martin 服务已停止', 'status': 'stopped'}, 200
            else:
                return {'message': 'Martin 服务停止失败', 'status': 'failed'}, 500
                
        except Exception as e:
            logger.error(f"停止服务失败: {e}")
            return {'error': str(e)}, 500

@api.route('/restart')
class RestartService(Resource):
    @api.doc('restart_martin_service')
    def post(self):
        """重启 Martin 服务"""
        try:
            martin_service.stop_service()
            success = martin_service.start_service()
            
            if success:
                return {'message': 'Martin 服务重启成功', 'status': 'restarted'}, 200
            else:
                return {'message': 'Martin 服务重启失败', 'status': 'failed'}, 500
                
        except Exception as e:
            logger.error(f"重启服务失败: {e}")
            return {'error': str(e)}, 500

@api.route('/tables')
class PostGISTables(Resource):
    @api.doc('get_postgis_tables')
    @api.marshal_list_with(table_info_model)
    def get(self):
        """获取 PostGIS 中的空间表列表"""
        try:
            tables = martin_service.get_postgis_tables()
            return tables, 200
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return {'error': str(e)}, 500

@api.route('/catalog')
class ServiceCatalog(Resource):
    @api.doc('get_martin_catalog')
    def get(self):
        """获取 Martin 服务目录"""
        try:
            if not martin_service.is_running():
                return {'error': 'Martin 服务未运行'}, 503
                
            catalog = martin_service.get_catalog()
            if catalog:
                return catalog, 200
            else:
                return {'error': '无法获取服务目录'}, 500
                
        except Exception as e:
            logger.error(f"获取服务目录失败: {e}")
            return {'error': str(e)}, 500

@api.route('/table/<string:table_id>')
class TableInfo(Resource):
    @api.doc('get_table_info')
    def get(self, table_id):
        """获取特定表的 TileJSON 信息"""
        try:
            if not martin_service.is_running():
                return {'error': 'Martin 服务未运行'}, 503
                
            table_info = martin_service.get_table_info(table_id)
            if table_info:
                return table_info, 200
            else:
                return {'error': f'表 {table_id} 不存在或无法访问'}, 404
                
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            return {'error': str(e)}, 500

@api.route('/mvt/<string:table_id>')
class MVTInfo(Resource):
    @api.doc('get_mvt_info')
    @api.marshal_with(mvt_info_model)
    def get(self, table_id):
        """获取 MVT 瓦片URL信息"""
        try:
            if not martin_service.is_running():
                return {'error': 'Martin 服务未运行'}, 503
            
            # 检查表是否存在
            tables = martin_service.get_postgis_tables()
            table_exists = any(t['source_id'] == table_id for t in tables)
            
            if not table_exists:
                return {'error': f'表 {table_id} 不存在'}, 404
            
            mvt_url = martin_service.get_mvt_url(table_id)
            tilejson_url = f"{martin_service.base_url}/{table_id}"
            
            return {
                'table_id': table_id,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url
            }, 200
            
        except Exception as e:
            logger.error(f"获取MVT信息失败: {e}")
            return {'error': str(e)}, 500

@api.route('/refresh')
class RefreshTables(Resource):
    @api.doc('refresh_tables')
    def post(self):
        """刷新表配置（重新扫描数据库并重启服务）"""
        try:
            success = martin_service.refresh_tables()
            if success:
                tables_count = len(martin_service.get_postgis_tables())
                return {
                    'message': '表配置刷新成功',
                    'status': 'refreshed',
                    'tables_count': tables_count
                }, 200
            else:
                return {'message': '表配置刷新失败', 'status': 'failed'}, 500
                
        except Exception as e:
            logger.error(f"刷新表配置失败: {e}")
            return {'error': str(e)}, 500

@api.route('/reload-config')
class ReloadConfig(Resource):
    @api.doc('reload_config')
    def post(self):
        """重新加载配置文件（热重载，无需重启进程）"""
        try:
            # 如果Martin支持SIGHUP信号重载配置
            if martin_service.process and martin_service.process.poll() is None:
                import signal
                import os
                
                # 先重新生成配置文件
                if not martin_service.write_config_file():
                    return {'message': '配置文件生成失败', 'status': 'failed'}, 500
                
                # 发送SIGHUP信号给Martin进程（如果支持的话）
                try:
                    # 在Windows上可能不支持SIGHUP
                    if hasattr(signal, 'SIGHUP'):
                        os.kill(martin_service.process.pid, signal.SIGHUP)
                        tables_count = len(martin_service.get_postgis_tables())
                        return {
                            'message': '配置重载成功',
                            'status': 'reloaded',
                            'tables_count': tables_count
                        }, 200
                    else:
                        # Windows系统回退到重启服务
                        return refresh_tables()
                except Exception as e:
                    logger.warning(f"信号发送失败，回退到重启服务: {e}")
                    # 回退到重启服务
                    success = martin_service.refresh_tables()
                    if success:
                        tables_count = len(martin_service.get_postgis_tables())
                        return {
                            'message': '配置重载成功（通过重启）',
                            'status': 'reloaded_via_restart',
                            'tables_count': tables_count
                        }, 200
                    else:
                        return {'message': '配置重载失败', 'status': 'failed'}, 500
            else:
                return {'message': 'Martin服务未运行', 'status': 'not_running'}, 503
                
        except Exception as e:
            logger.error(f"重载配置失败: {e}")
            return {'error': str(e)}, 500

@api.route('/config')
class MartinConfigAPI(Resource):
    @api.doc('get_martin_config')
    def get(self):
        """获取Martin配置"""
        try:
            config = martin_service.generate_config()
            return {
                'success': True,
                'config': config
            }
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return {
                'success': False,
                'message': f"获取配置失败: {str(e)}"
            }, 500

@api.route('/logs')
class MartinLogsAPI(Resource):
    @api.doc('get_martin_logs')
    def get(self):
        """获取Martin服务日志"""
        try:
            logs = martin_service.get_process_logs()
            version = martin_service.get_martin_version()
            status = martin_service.get_status()
            
            return {
                'success': True,
                'logs': logs,
                'version': version,
                'status': status
            }
        except Exception as e:
            logger.error(f"获取日志失败: {e}")
            return {
                'success': False,
                'message': f"获取日志失败: {str(e)}"
            }, 500

# 注册错误处理器
@martin_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@martin_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500 