#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DXF文件专用路由
提供DXF文件的特殊功能和服务发布
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime

from services.dxf_service import DXFService
from services.dxf_style_analyzer import DXFStyleAnalyzer
from models.db import execute_query

dxf_bp = Blueprint('dxf', __name__, url_prefix='/api/dxf')

@dxf_bp.route('/analyze-styles/<string:file_id>', methods=['GET'])
def analyze_dxf_styles(file_id):
    """分析DXF文件的样式信息"""
    try:
        # 获取文件信息 - 将字符串file_id转换为整数
        try:
            file_id_int = int(file_id)
        except ValueError:
            return jsonify({'error': '无效的文件ID格式'}), 400
            
        sql = "SELECT * FROM files WHERE id = %s AND file_type = 'dxf'"
        file_info = execute_query(sql, (file_id_int,))
        
        if not file_info:
            return jsonify({'error': 'DXF文件不存在'}), 404
        
        file_info = file_info[0]
        file_path = file_info['file_path']
        
        # 分析样式
        analyzer = DXFStyleAnalyzer()
        analysis = analyzer.analyze_dxf_styles(file_path)
        
        if 'error' in analysis:
            return jsonify({'error': f'样式分析失败: {analysis["error"]}'}), 500
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'file_name': file_info['file_name'],
            'style_analysis': analysis
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"DXF样式分析错误: {str(e)}")
        return jsonify({'error': f'样式分析失败: {str(e)}'}), 500

@dxf_bp.route('/publish-martin/<string:file_id>', methods=['POST'])
def publish_dxf_martin_service(file_id):
    """发布DXF文件为Martin MVT服务"""
    try:
        from services.file_service import FileService
        from services.dxf_processor import DXFProcessor
        from models.db import execute_query
        import uuid
        import os
        
        # 获取文件信息 - 将字符串file_id转换为整数
        try:
            file_id_int = int(file_id)
        except ValueError:
            return jsonify({'error': '无效的文件ID格式'}), 400
            
        file_service = FileService()
        file_info = file_service.get_file_by_id(file_id_int)
        
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        if file_info['file_type'].lower() != 'dxf':
            return jsonify({'error': '只支持DXF文件'}), 400
        
        # 检查文件是否已经发布到Martin
        check_sql = """
        SELECT id, table_name, status FROM vector_martin_services 
        WHERE (file_id = %s OR original_filename = %s) AND vector_type = 'dxf'
        ORDER BY created_at DESC
        LIMIT 1
        """
        existing = execute_query(check_sql, (str(file_id_int), file_info['file_name']))
        if existing:
            existing_record = existing[0]
            if existing_record['status'] == 'active':
                return jsonify({
                    'error': 'DXF文件已发布到Martin服务',
                    'service_id': existing_record['id'],
                    'table_name': existing_record['table_name']
                }), 400
            else:
                # 如果存在非活跃状态的记录，先清理它
                current_app.logger.info(f"发现非活跃状态的Martin服务记录，准备清理: {existing_record}")
                cleanup_sql = """
                DELETE FROM vector_martin_services 
                WHERE id = %s
                """
                execute_query(cleanup_sql, (existing_record['id'],))
                
                # 同时清理可能存在的PostGIS表
                if existing_record['table_name']:
                    try:
                        drop_sql = f"DROP TABLE IF EXISTS {existing_record['table_name']}"
                        execute_query(drop_sql, [])
                        current_app.logger.info(f"清理了遗留的PostGIS表: {existing_record['table_name']}")
                    except Exception as cleanup_error:
                        current_app.logger.warning(f"清理PostGIS表失败: {cleanup_error}")
                
                current_app.logger.info(f"✅ 清理完成，继续发布Martin服务")
        
        # 获取请求参数
        data = request.get_json() or {}
        coordinate_system = data.get('coordinate_system') or file_info.get('coordinate_system') or 'EPSG:4326'
        
        # 验证坐标系格式
        if not coordinate_system.startswith('EPSG:'):
            return jsonify({'error': '坐标系格式错误，请使用EPSG:XXXX格式'}), 400
        
        current_app.logger.info(f"开始发布DXF文件到Martin服务: {file_info['file_name']}, 坐标系: {coordinate_system}")
        
        # 生成唯一的表名 - 使用vector前缀
        table_name = f"vector_{uuid.uuid4().hex[:8]}"
        
        # 使用DXF处理器导入PostGIS
        dxf_processor = DXFProcessor()
        
        # Martin通常在Web Mercator下性能最佳，但我们先保持用户指定的坐标系
        # 如果需要转换为3857，可以在这里设置target_srs
        target_srs = coordinate_system
        
        # 如果原始坐标系不是Web Mercator，建议转换为3857以获得更好的瓦片性能
        if coordinate_system != 'EPSG:3857':
            current_app.logger.info(f"坐标系 {coordinate_system} 将转换为 EPSG:3857 以优化瓦片性能")
            target_srs = 'EPSG:3857'
        
        import_result = dxf_processor.import_dxf_to_postgis(
            file_path=file_info['file_path'],
            table_name=table_name,
            source_srs=coordinate_system,
            target_srs=target_srs
        )
        
        if not import_result['success']:
            return jsonify({
                'error': f'DXF导入PostGIS失败: {import_result.get("error")}'
            }), 500
        
        # Martin会在重启时自动发现vector_开头的表，无需额外配置
        
        # 生成服务URL（参照geojson逻辑）
        from config import MARTIN_CONFIG
        base_url = MARTIN_CONFIG.get('base_url', 'http://localhost:3000')
        service_url = f"{base_url}/{table_name}"
        mvt_url = f"{service_url}/{{z}}/{{x}}/{{y}}.pbf"
        tilejson_url = service_url  # TileJSON URL就是service_url，不需要.json后缀
        
        # 构建DXF信息（参照geojson逻辑）
        dxf_info = {
            'total_features': import_result.get('original_feature_count', 0),
            'imported_features': import_result.get('feature_count', 0),
            'skipped_features': import_result.get('skipped_features', 0),
            'success_rate': import_result.get('success_rate', 0),
            'geometry_types': import_result.get('geometry_types', []),
            'bbox': import_result.get('bbox'),
            'layers': import_result.get('layers', []),
            'warnings': import_result.get('warnings', [])
        }
        
        # 收集PostGIS信息（参照geojson逻辑）
        postgis_info = {
            'table_name': table_name,
            'geometry_column': 'geom',
            'srid': int(target_srs.replace('EPSG:', '')) if target_srs.startswith('EPSG:') else 3857
        }
        
        # 记录到vector_martin_services表（参照geojson逻辑）
        from utils.snowflake import get_snowflake_id
        service_id = get_snowflake_id()  # 🔥 使用雪花算法生成ID
        
        insert_sql = """
        INSERT INTO vector_martin_services 
        (id, file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, vector_info, postgis_info, user_id)
        VALUES (%(id)s, %(file_id)s, %(original_filename)s, %(file_path)s, %(vector_type)s, %(table_name)s, %(service_url)s, %(mvt_url)s, %(tilejson_url)s, %(vector_info)s, %(postgis_info)s, %(user_id)s)
        """
        
        params = {
            'id': service_id,  # 🔥 使用雪花算法生成的ID
            'file_id': str(file_id_int),
            'original_filename': file_info['file_name'],
            'file_path': file_info['file_path'],
            'vector_type': 'dxf',
            'table_name': table_name,
            'service_url': service_url,
            'mvt_url': mvt_url,
            'tilejson_url': tilejson_url,
            'vector_info': json.dumps(dxf_info),
            'postgis_info': json.dumps(postgis_info),
            'user_id': file_info.get('user_id')
        }
        
        result = execute_query(insert_sql, params)
        # service_id 已经通过雪花算法生成，不需要从结果中获取
        
        if not service_id:
            cleanup_failed_table(table_name)
            return jsonify({'error': '服务记录保存失败'}), 500
        
        current_app.logger.info(f"✅ DXF Martin服务发布成功: {table_name}")
        
        # 生成响应消息
        import_stats = import_result
        success_message = f'DXF Martin服务发布成功'
        
        # 如果有要素被跳过，添加统计信息
        if import_stats.get('skipped_features', 0) > 0:
            success_rate = import_stats.get('success_rate', 0)
            success_message += f"（成功导入 {import_stats.get('feature_count', 0)} 个要素，跳过 {import_stats.get('skipped_features', 0)} 个，成功率 {success_rate:.1f}%）"
        
        return jsonify({
            'success': True,
            'message': success_message,
            'service_id': service_id,
            'table_name': table_name,
            'service_url': service_url,
            'mvt_url': mvt_url,
            'tilejson_url': tilejson_url,
            'coordinate_system': coordinate_system,
            'target_srs': target_srs,
            'dxf_info': dxf_info,
            'postgis_info': postgis_info
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"发布DXF Martin服务失败: {str(e)}")
        return jsonify({'error': f'发布DXF Martin服务失败: {str(e)}'}), 500

@dxf_bp.route('/publish-martin-ezdxf/<string:file_id>', methods=['POST'])
def publish_dxf_martin_service_ezdxf(file_id):
    """发布DXF文件为Martin MVT服务（使用ezdxf库直接导入）"""
    try:
        from services.file_service import FileService
        from services.enhanced_dxf_processor import dxf_to_postgis
        from models.db import execute_query
        import uuid
        import os
        
        # 获取文件信息 - 将字符串file_id转换为整数
        try:
            file_id_int = int(file_id)
        except ValueError:
            return jsonify({'error': '无效的文件ID格式'}), 400
            
        file_service = FileService()
        file_info = file_service.get_file_by_id(file_id_int)
        
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        if file_info['file_type'].lower() != 'dxf':
            return jsonify({'error': '只支持DXF文件'}), 400
        
        # 检查文件是否已经发布到Martin
        check_sql = """
        SELECT id, table_name, status FROM vector_martin_services 
        WHERE (file_id = %s OR original_filename = %s) AND vector_type = 'dxf'
        ORDER BY created_at DESC
        LIMIT 1
        """
        existing = execute_query(check_sql, (str(file_id_int), file_info['file_name']))
        if existing:
            existing_record = existing[0]
            if existing_record['status'] == 'active':
                return jsonify({
                    'error': 'DXF文件已发布到Martin服务',
                    'service_id': existing_record['id'],
                    'table_name': existing_record['table_name']
                }), 400
            else:
                # 如果存在非活跃状态的记录，先清理它
                current_app.logger.info(f"发现非活跃状态的Martin服务记录，准备清理: {existing_record}")
                cleanup_sql = """
                DELETE FROM vector_martin_services 
                WHERE id = %s
                """
                execute_query(cleanup_sql, (existing_record['id'],))
                
                # 同时清理可能存在的PostGIS表
                if existing_record['table_name']:
                    try:
                        drop_sql = f"DROP TABLE IF EXISTS {existing_record['table_name']}"
                        execute_query(drop_sql, [])
                        current_app.logger.info(f"清理了遗留的PostGIS表: {existing_record['table_name']}")
                    except Exception as cleanup_error:
                        current_app.logger.warning(f"清理PostGIS表失败: {cleanup_error}")
                
                current_app.logger.info(f"✅ 清理完成，继续发布Martin服务")
        
        # 获取请求参数
        data = request.get_json() or {}
        coordinate_system = data.get('coordinate_system') or file_info.get('coordinate_system') or 'EPSG:4326'
        
        # 验证坐标系格式
        if not coordinate_system.startswith('EPSG:'):
            return jsonify({'error': '坐标系格式错误，请使用EPSG:XXXX格式'}), 400
        
        current_app.logger.info(f"开始发布DXF文件到Martin服务(使用Enhanced EZDXF): {file_info['file_name']}, 坐标系: {coordinate_system}")
        
        # 生成唯一的表名 - 使用vector前缀
        table_name = f"vector_{uuid.uuid4().hex[:8]}"
        
        # Martin通常在Web Mercator下性能最佳，但我们先保持用户指定的坐标系
        # 如果需要转换为3857，可以在这里设置target_srs
        target_srs = coordinate_system
        
        # 如果原始坐标系不是Web Mercator，建议转换为3857以获得更好的瓦片性能
        if coordinate_system != 'EPSG:3857':
            current_app.logger.info(f"坐标系 {coordinate_system} 将转换为 EPSG:3857 以优化瓦片性能")
            target_srs = 'EPSG:3857'
        
        # 使用enhanced_dxf_processor中的ezdxf方法导入DXF到PostGIS
        import_result = dxf_to_postgis(
            file_path=file_info['file_path'],
            table_name=table_name,
            source_srs=coordinate_system,
            target_srs=target_srs
        )
        
        if not import_result['success']:
            return jsonify({
                'error': f'DXF导入PostGIS失败: {import_result.get("error")}'
            }), 500
        
        # Martin会在重启时自动发现vector_开头的表，无需额外配置
        
        # 生成服务URL（参照geojson逻辑）
        from config import MARTIN_CONFIG
        base_url = MARTIN_CONFIG.get('base_url', 'http://localhost:3000')
        service_url = f"{base_url}/{table_name}"
        mvt_url = f"{service_url}/{{z}}/{{x}}/{{y}}.pbf"
        tilejson_url = service_url  # TileJSON URL就是service_url，不需要.json后缀
        
        # 构建DXF信息（参照geojson逻辑）
        dxf_info = {
            'total_features': import_result.get('original_feature_count', 0),
            'imported_features': import_result.get('feature_count', 0),
            'skipped_features': import_result.get('skipped_features', 0),
            'success_rate': import_result.get('success_rate', 0),
            'geometry_types': import_result.get('geometry_types', []),
            'bbox': import_result.get('bbox'),
            'layers': import_result.get('layers', []),
            'warnings': import_result.get('warnings', [])
        }
        
        # 收集PostGIS信息（参照geojson逻辑）
        postgis_info = {
            'table_name': table_name,
            'geometry_column': 'geom',
            'srid': int(target_srs.replace('EPSG:', '')) if target_srs.startswith('EPSG:') else 3857
        }
        
        # 记录到vector_martin_services表（参照geojson逻辑）
        from utils.snowflake import get_snowflake_id
        service_id = get_snowflake_id()  # 🔥 使用雪花算法生成ID
        
        insert_sql = """
        INSERT INTO vector_martin_services 
        (id, file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, vector_info, postgis_info, user_id)
        VALUES (%(id)s, %(file_id)s, %(original_filename)s, %(file_path)s, %(vector_type)s, %(table_name)s, %(service_url)s, %(mvt_url)s, %(tilejson_url)s, %(vector_info)s, %(postgis_info)s, %(user_id)s)
        """
        
        params = {
            'id': service_id,  # 🔥 使用雪花算法生成的ID
            'file_id': str(file_id_int),
            'original_filename': file_info['file_name'],
            'file_path': file_info['file_path'],
            'vector_type': 'dxf',
            'table_name': table_name,
            'service_url': service_url,
            'mvt_url': mvt_url,
            'tilejson_url': tilejson_url,
            'vector_info': json.dumps(dxf_info),
            'postgis_info': json.dumps(postgis_info),
            'user_id': file_info.get('user_id')
        }
        
        result = execute_query(insert_sql, params)
        # service_id 已经通过雪花算法生成，不需要从结果中获取
        
        if not service_id:
            cleanup_failed_table(table_name)
            return jsonify({'error': '服务记录保存失败'}), 500
        
        current_app.logger.info(f"✅ DXF Martin服务发布成功(Enhanced EZDXF): {table_name}")
        
        # 生成响应消息
        import_stats = import_result
        success_message = f'DXF Martin服务发布成功(Enhanced EZDXF)'
        
        # 如果有要素被跳过，添加统计信息
        if import_stats.get('skipped_features', 0) > 0:
            success_rate = import_stats.get('success_rate', 0)
            success_message += f"（成功导入 {import_stats.get('feature_count', 0)} 个要素，跳过 {import_stats.get('skipped_features', 0)} 个，成功率 {success_rate:.1f}%）"
        
        return jsonify({
            'success': True,
            'message': success_message,
            'service_id': service_id,
            'table_name': table_name,
            'service_url': service_url,
            'mvt_url': mvt_url,
            'tilejson_url': tilejson_url,
            'coordinate_system': coordinate_system,
            'target_srs': target_srs,
            'dxf_info': dxf_info,
            'postgis_info': postgis_info
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"发布DXF Martin服务失败(Enhanced EZDXF): {str(e)}")
        return jsonify({'error': f'发布DXF Martin服务失败(Enhanced EZDXF): {str(e)}'}), 500

def cleanup_failed_table(table_name):
    """清理失败的表"""
    try:
        from models.db import execute_query
        
        # 检查表是否存在
        check_sql = """
        SELECT COUNT(*) as exists FROM information_schema.tables 
        WHERE table_name = %s AND table_schema = 'public'
        """
        exists_result = execute_query(check_sql, [table_name])
        
        if exists_result and exists_result[0]['exists'] > 0:
            # 表存在，执行删除
            cleanup_sql = f"DROP TABLE {table_name}"
            execute_query(cleanup_sql, [])
            current_app.logger.info(f"已清理失败的表: {table_name}")
        else:
            current_app.logger.info(f"表 {table_name} 不存在，无需清理")
            
    except Exception as e:
        current_app.logger.error(f"清理表失败: {str(e)}")
        # 即使清理失败也不抛出异常，因为这不应该影响主要流程

@dxf_bp.route('/martin-services', methods=['GET'])
def get_dxf_martin_services():
    """获取DXF Martin服务列表"""
    try:
        from models.db import execute_query
        
        # 获取查询参数
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status', 'active')
        
        sql = """
        SELECT 
            id, file_id, original_filename, table_name,
            service_url, mvt_url, tilejson_url, status, 
            vector_info, postgis_info, user_id, created_at, updated_at
        FROM vector_martin_services 
        WHERE vector_type = 'dxf' AND status = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        services = execute_query(sql, (status, limit, offset))
        
        # 获取总数
        count_sql = """
        SELECT COUNT(*) as total FROM vector_martin_services 
        WHERE vector_type = 'dxf' AND status = %s
        """
        total_result = execute_query(count_sql, (status,))
        total = total_result[0]['total'] if total_result else 0
        
        return jsonify({
            'success': True,
            'services': services,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取DXF Martin服务列表失败: {str(e)}")
        return jsonify({'error': f'获取服务列表失败: {str(e)}'}), 500

@dxf_bp.route('/martin-services/<int:service_id>', methods=['DELETE'])
def delete_dxf_martin_service(service_id):
    """删除DXF Martin服务"""
    try:
        from models.db import execute_query
        
        # 获取服务信息
        get_sql = """
        SELECT id, table_name, original_filename FROM vector_martin_services 
        WHERE id = %s AND vector_type = 'dxf'
        """
        service_info = execute_query(get_sql, (service_id,))
        
        if not service_info:
            return jsonify({'error': '服务不存在'}), 404
        
        table_name = service_info[0]['table_name']
        
        # 删除PostGIS表
        drop_sql = f"DROP TABLE IF EXISTS {table_name}"
        execute_query(drop_sql, [])
        
        # 更新服务状态为已删除
        update_sql = """
        UPDATE vector_martin_services 
        SET status = 'deleted', updated_at = NOW()
        WHERE id = %s
        """
        execute_query(update_sql, (service_id,))
        
        current_app.logger.info(f"✅ DXF Martin服务删除成功: {table_name}")
        
        return jsonify({
            'success': True,
            'message': f'DXF Martin服务删除成功: {table_name}'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"删除DXF Martin服务失败: {str(e)}")
        return jsonify({'error': f'删除服务失败: {str(e)}'}), 500

@dxf_bp.route('/publish-both/<string:file_id>', methods=['POST'])
def publish_both_services(file_id):
    """同时发布DXF文件到Martin和GeoServer服务"""
    try:
        # 获取文件信息
        sql = "SELECT * FROM files WHERE id = %s AND file_type = 'dxf'"
        file_info = execute_query(sql, (file_id,))
        
        if not file_info:
            return jsonify({'error': 'DXF文件不存在'}), 404
        
        file_info = file_info[0]
        
        # 检查是否已发布
        check_sql = """
        SELECT COUNT(*) as count FROM vector_martin_services 
        WHERE original_filename = %s AND vector_type = 'dxf' AND status = 'active'
        """
        existing = execute_query(check_sql, (file_info['file_name'],))
        if existing[0]['count'] > 0:
            return jsonify({'error': '文件已发布到Martin服务'}), 400
        
        # 获取参数
        data = request.get_json() or {}
        coordinate_system = data.get('coordinate_system', 'EPSG:4326')
        
        # 发布双服务
        dxf_service = DXFService()
        result = dxf_service.publish_dxf_both_services(
            file_id=str(file_id),
            file_path=file_info['file_path'],
            original_filename=file_info['file_name'],
            coordinate_system=coordinate_system,
            user_id=file_info.get('user_id')
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'DXF双服务发布成功',
                'table_name': result['table_name'],
                'martin_result': result['martin_result'],
                'geoserver_result': result['geoserver_result']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"发布DXF双服务错误: {str(e)}")
        return jsonify({'error': f'发布双服务失败: {str(e)}'}), 500

@dxf_bp.route('/upload-and-publish', methods=['POST'])
def upload_and_publish_dxf():
    """上传DXF文件并直接发布服务"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': '只支持DXF文件'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        upload_folder = '/temp/dxf_uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, f"{file_id}_{filename}")
        file.save(file_path)
        
        # 获取发布参数
        publish_type = request.form.get('publish_type', 'both')  # martin, geoserver, both
        coordinate_system = request.form.get('coordinate_system', 'EPSG:4326')
        
        # 执行发布
        dxf_service = DXFService()
        
        if publish_type == 'martin':
            result = dxf_service.publish_dxf_martin_service(
                file_id, file_path, filename, coordinate_system
            )
        elif publish_type == 'geoserver':
            result = dxf_service.publish_dxf_geoserver_service(
                file_id, None, coordinate_system
            )
        else:  # both
            result = dxf_service.publish_dxf_both_services(
                file_id, file_path, filename, coordinate_system
            )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'DXF文件上传并发布成功',
                'file_id': file_id,
                'filename': filename,
                'publish_type': publish_type,
                'result': result
            }), 200
        else:
            # 删除上传的文件
            try:
                os.remove(file_path)
            except:
                pass
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        current_app.logger.error(f"上传并发布DXF文件错误: {str(e)}")
        return jsonify({'error': f'上传并发布失败: {str(e)}'}), 500

@dxf_bp.route('/style-templates', methods=['GET'])
def get_dxf_style_templates():
    """获取DXF样式模板"""
    try:
        templates = {
            '建筑规划': {
                'description': '适用于建筑和规划图纸',
                'point': {'color': '#8B4513', 'size': 8},
                'line': {'color': '#8B4513', 'width': 2, 'style': 'solid'},
                'polygon': {'fillColor': '#DEB887', 'outlineColor': '#8B4513', 'outlineWidth': 1, 'opacity': 0.7}
            },
            '道路交通': {
                'description': '适用于道路和交通设施图',
                'point': {'color': '#696969', 'size': 6},
                'line': {'color': '#696969', 'width': 3, 'style': 'solid'},
                'polygon': {'fillColor': '#D3D3D3', 'outlineColor': '#696969', 'outlineWidth': 1, 'opacity': 0.8}
            },
            '地形地物': {
                'description': '适用于地形图和地物标注',
                'point': {'color': '#228B22', 'size': 6},
                'line': {'color': '#228B22', 'width': 2, 'style': 'solid'},
                'polygon': {'fillColor': '#90EE90', 'outlineColor': '#228B22', 'outlineWidth': 1, 'opacity': 0.5}
            },
            '水系': {
                'description': '适用于水系和水利设施',
                'point': {'color': '#0000FF', 'size': 6},
                'line': {'color': '#0000FF', 'width': 2, 'style': 'solid'},
                'polygon': {'fillColor': '#87CEEB', 'outlineColor': '#0000FF', 'outlineWidth': 1, 'opacity': 0.6}
            },
            '边界线': {
                'description': '适用于行政边界和地块边界',
                'point': {'color': '#FF0000', 'size': 6},
                'line': {'color': '#FF0000', 'width': 2, 'style': 'dashed'},
                'polygon': {'fillColor': '#FFE4E1', 'outlineColor': '#FF0000', 'outlineWidth': 2, 'opacity': 0.3}
            }
        }
        
        return jsonify({
            'success': True,
            'templates': templates
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取DXF样式模板失败: {str(e)}")
        return jsonify({'error': f'获取样式模板失败: {str(e)}'}), 500

@dxf_bp.route('/validate', methods=['POST'])
def validate_dxf_file():
    """验证DXF文件有效性"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 保存临时文件
        temp_path = f"/tmp/validate_{uuid.uuid4().hex}.dxf"
        file.save(temp_path)
        
        try:
            # 使用GDAL验证文件
            from osgeo import ogr
            driver = ogr.GetDriverByName('DXF')
            datasource = driver.Open(temp_path, 0)
            
            if not datasource:
                return jsonify({
                    'valid': False,
                    'error': '不是有效的DXF文件'
                }), 200
            
            # 获取文件信息
            layer_count = datasource.GetLayerCount()
            total_features = 0
            layers_info = []
            
            for i in range(layer_count):
                layer = datasource.GetLayer(i)
                feature_count = layer.GetFeatureCount()
                total_features += feature_count
                
                layers_info.append({
                    'name': layer.GetName(),
                    'feature_count': feature_count,
                    'geometry_type': layer.GetGeomType()
                })
            
            datasource = None
            
            return jsonify({
                'valid': True,
                'layer_count': layer_count,
                'total_features': total_features,
                'layers_info': layers_info
            }), 200
            
        finally:
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
                
    except Exception as e:
        current_app.logger.error(f"DXF文件验证错误: {str(e)}")
        return jsonify({'error': f'文件验证失败: {str(e)}'}), 500 