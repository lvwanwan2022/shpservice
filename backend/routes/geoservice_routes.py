#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app, send_file
from services.geoserver_service import GeoServerService
from models.db import execute_query
import os
import tempfile
import requests
from services.file_service import FileService

geoservice_bp = Blueprint('geoservice', __name__)
geoserver_service = GeoServerService()

@geoservice_bp.route('/layer_info/<layer_name>', methods=['GET'])
def get_layer_info(layer_name):
    """获取图层信息
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: layer_name
        in: path
        type: string
        required: true
        description: 图层名称
    responses:
      200:
        description: 图层信息
      404:
        description: 图层不存在
    """
    try:
        # 从GeoServer获取图层信息
        layer_info = geoserver_service.get_layer_info(layer_name)
        
        return jsonify(layer_info), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层信息错误: {str(e)}")
        return jsonify({'error': '图层不存在或无法访问'}), 404

@geoservice_bp.route('/wms_capabilities', methods=['GET'])
def get_wms_capabilities():
    """获取WMS服务能力
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: WMS服务能力
    """
    try:
        url = f"{geoserver_service.url}/wms?service=WMS&version=1.3.0&request=GetCapabilities"
        
        return jsonify({
            'wms_capabilities_url': url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取WMS服务能力错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/wfs_capabilities', methods=['GET'])
def get_wfs_capabilities():
    """获取WFS服务能力
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: WFS服务能力
    """
    try:
        url = f"{geoserver_service.url}/wfs?service=WFS&version=2.0.0&request=GetCapabilities"
        
        return jsonify({
            'wfs_capabilities_url': url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取WFS服务能力错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/layers', methods=['GET'])
def list_layers():
    """获取所有图层
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: 图层列表
    """
    try:
        # 从数据库获取图层列表
        sql = """
        SELECT DISTINCT f.id, f.file_name, f.file_type, f.discipline,
               f.geoserver_layer, f.wms_url, f.wfs_url
        FROM files f
        WHERE f.geoserver_layer IS NOT NULL
        ORDER BY f.upload_date DESC
        """
        
        layers = execute_query(sql)
        
        return jsonify({
            'layers': layers
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/layer_preview/<layer_name>', methods=['GET'])
def layer_preview(layer_name):
    """获取图层预览
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: layer_name
        in: path
        type: string
        required: true
        description: 图层名称
      - name: width
        in: query
        type: integer
        required: false
        default: 800
        description: 预览宽度
      - name: height
        in: query
        type: integer
        required: false
        default: 600
        description: 预览高度
    responses:
      200:
        description: 图层预览图片
      404:
        description: 图层不存在
    """
    try:
        # 获取查询参数
        width = request.args.get('width', 800)
        height = request.args.get('height', 600)
        
        # 构建WMS请求URL
        bbox = request.args.get('bbox')
        bbox_param = f"&bbox={bbox}" if bbox else ""
        
        preview_url = f"{geoserver_service.url}/wms?service=WMS&version=1.3.0&request=GetMap&layers={layer_name}&styles=&width={width}&height={height}&format=image/png{bbox_param}&transparent=true&CRS=EPSG:4326"
        
        return jsonify({
            'preview_url': preview_url
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取图层预览错误: {str(e)}")
        return jsonify({'error': '图层不存在或无法访问'}), 404

@geoservice_bp.route('/published_layers', methods=['GET'])
def get_published_layers():
    """获取已发布的图层列表（用于场景管理）
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: discipline
        in: query
        type: string
        required: false
        description: 专业过滤
      - name: file_type
        in: query
        type: string
        required: false
        description: 文件类型过滤
    responses:
      200:
        description: 已发布的图层列表
    """
    try:
        # 获取查询参数
        discipline = request.args.get('discipline')
        file_type = request.args.get('file_type')
        
        # 构建SQL查询
        sql = """
        SELECT f.id, f.file_name, f.file_type, f.dimension, f.discipline,
               f.geoserver_layer, f.wms_url, f.wfs_url, f.is_public,
               u.username as uploader, f.upload_date
        FROM files f
        LEFT JOIN users u ON f.user_id = u.id
        WHERE f.geoserver_layer IS NOT NULL 
          AND f.wms_url IS NOT NULL
        """
        
        params = {}
        
        # 添加过滤条件
        if discipline:
            sql += " AND f.discipline = %(discipline)s"
            params['discipline'] = discipline
            
        if file_type:
            sql += " AND f.file_type = %(file_type)s"
            params['file_type'] = file_type
        
        sql += " ORDER BY f.upload_date DESC"
        
        layers = execute_query(sql, params)
        
        return jsonify({
            'layers': layers,
            'total': len(layers)
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取已发布图层列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/publish/<int:file_id>', methods=['POST'])
def publish_service(file_id):
    """发布文件服务到GeoServer
    
    Args:
        file_id: 文件ID
        
    Returns:
        JSON response with layer info
    """
    try:
        print(f"\n=== 开始发布服务，文件ID: {file_id} ===")
        
        # 获取文件信息
        file_service = FileService()
        file_info = file_service.get_file_by_id(file_id)
        
        if not file_info:
            print(f"❌ 文件不存在: {file_id}")
            return jsonify({'error': '文件不存在'}), 404
        
        print(f"文件信息: {dict(file_info)}")
        
        # 检查文件类型是否支持发布
        file_type = file_info.get('file_type', '').lower()
        
        # 不同类型文件的处理方式
        if file_type == 'geojson':
            # GeoJSON文件优先尝试使用PostGIS方式，如果失败则回退到直接发布
            try:
                from services.postgis_service import PostGISService
                postgis_service = PostGISService()
                
                # 简单测试数据库连接
                conn = postgis_service.get_connection()
                
                # 检查PostGIS扩展
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'postgis'
                    ) as has_postgis;
                """)
                has_postgis = cursor.fetchone()[0]
                
                if has_postgis:
                    # 尝试获取PostGIS版本
                    try:
                        cursor.execute("SELECT postgis_version()")
                        version = cursor.fetchone()[0]
                        print(f"✅ PostGIS数据库连接测试成功，版本: {version}")
                    except:
                        try:
                            cursor.execute("SELECT PostGIS_Version()")
                            version = cursor.fetchone()[0]
                            print(f"✅ PostGIS数据库连接测试成功，版本: {version}")
                        except Exception as e:
                            print(f"⚠️ 无法获取PostGIS版本，但已检测到扩展: {str(e)}")
                else:
                    print("⚠️ PostgreSQL数据库中未安装PostGIS扩展")
                    print("将尝试直接发布GeoJSON文件，但功能可能受限")
                
                conn.close()
                
            except Exception as e:
                print(f"⚠️ PostGIS数据库连接测试失败: {str(e)}")
                print("将尝试直接发布GeoJSON文件，但功能可能受限")
                # 不立即返回错误，让服务继续尝试发布
        
        # 生成数据存储名称
        store_name = f"file_{file_id}"
        print(f"数据存储名称: {store_name}")
        
        # 检查文件是否已发布 - 同时查询geoserver_layers表和geoserver_stores表
        check_layer_sql = "SELECT id, name FROM geoserver_layers WHERE file_id = %s"
        layer_result = execute_query(check_layer_sql, (file_id,))
        
        if layer_result:
            layer_info = layer_result[0]
            print(f"⚠️ 文件已发布为图层: 图层ID={layer_info['id']}, 图层名称={layer_info['name']}")
            return jsonify({
                'error': f'文件已发布服务',
                'layer_id': layer_info['id'],
                'layer_name': layer_info['name'],
                'message': f'该文件已发布为图层 "{layer_info["name"]}"，请勿重复发布'
            }), 400
        
        # 检查存储是否已存在（避免重复键错误）
        check_store_sql = "SELECT id, name FROM geoserver_stores WHERE name = %s"
        store_result = execute_query(check_store_sql, (store_name,))
        
        if store_result:
            store_info = store_result[0]
            print(f"⚠️ 存储已存在: 存储ID={store_info['id']}, 存储名称={store_info['name']}")
            
            # 检查存储是否关联了其他文件
            check_store_file_sql = "SELECT file_id FROM geoserver_stores WHERE id = %s"
            store_file_result = execute_query(check_store_file_sql, (store_info['id'],))
            
            if store_file_result and store_file_result[0]['file_id'] == file_id:
                # 同一个文件的存储，但没有图层记录，可能是之前发布失败留下的残留
                print(f"检测到残留的存储记录，尝试清理...")
                try:
                    # 清理残留的存储记录
                    cleanup_store_sql = "DELETE FROM geoserver_stores WHERE id = %s"
                    execute_query(cleanup_store_sql, (store_info['id'],))
                    print(f"✅ 清理残留存储记录成功")
                except Exception as cleanup_error:
                    print(f"❌ 清理残留存储记录失败: {str(cleanup_error)}")
                    return jsonify({
                        'error': '存储记录冲突，清理失败',
                        'message': f'存储 "{store_name}" 已存在且无法清理，请联系管理员'
                    }), 500
            else:
                # 存储被其他文件使用
                return jsonify({
                    'error': '存储名称冲突',
                    'message': f'存储 "{store_name}" 已被其他文件使用，请联系管理员'
                }), 400
        
        # 检查文件类型是否支持发布
        supported_types = ['shp', 'geojson', 'tif', 'dem', 'dom']
        
        print(f"文件类型: {file_type}")
        
        if file_type not in supported_types:
            print(f"❌ 不支持的文件类型: {file_type}")
            return jsonify({'error': f'文件类型 {file_type} 暂不支持自动发布'}), 400
        
        # 检查文件是否存在
        file_path = file_info['file_path']
        print(f"文件路径: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            
            # 尝试修复路径
            possible_paths = [
                file_path,
                os.path.join('..', 'FilesData', os.path.basename(file_path)),
                os.path.join('FilesData', os.path.basename(file_path)),
                file_path.replace('\\', '/'),
                file_path.replace('../', './')
            ]
            
            fixed_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"✅ 找到修复路径: {path}")
                    fixed_path = path
                    break
            
            if not fixed_path:
                print(f"❌ 无法找到文件")
                return jsonify({'error': '文件不存在'}), 404
            
            file_path = fixed_path
        
        print(f"✅ 文件存在: {file_path}")
        file_size = os.path.getsize(file_path)
        print(f"文件大小: {file_size} 字节")
        
        # 测试GeoServer连接
        print("\n--- 测试GeoServer连接 ---")
        try:
            from config import GEOSERVER_CONFIG
            import requests
            
            geoserver_url = GEOSERVER_CONFIG['url']
            auth = (GEOSERVER_CONFIG['user'], GEOSERVER_CONFIG['password'])
            
            # 测试REST API
            rest_response = requests.get(f"{geoserver_url}/rest", auth=auth, timeout=10)
            print(f"GeoServer REST API状态码: {rest_response.status_code}")
            
            if rest_response.status_code != 200:
                print(f"❌ GeoServer连接失败: {rest_response.text}")
                return jsonify({'error': 'GeoServer连接失败，请检查GeoServer是否正在运行'}), 500
            
            print("✅ GeoServer连接正常")
            
        except Exception as conn_error:
            print(f"❌ GeoServer连接异常: {str(conn_error)}")
            return jsonify({'error': f'GeoServer连接异常: {str(conn_error)}'}), 500
        
        # 根据文件类型发布服务
        print(f"\n--- 开始发布 {file_type} 服务 ---")
        try:
            if file_type == 'shp':
                print("调用 publish_shapefile...")
                result = geoserver_service.publish_shapefile(file_path, store_name, file_id)
            elif file_type == 'geojson':
                print("调用 publish_geojson...")
                result = geoserver_service.publish_geojson(file_path, store_name, file_id)
            elif file_type in ['tif', 'dem', 'dom']:
                print("调用 publish_geotiff...")
                result = geoserver_service.publish_geotiff(file_path, store_name, file_id)
            else:
                print(f"❌ 不支持的文件类型: {file_type}")
                return jsonify({'error': f'不支持的文件类型: {file_type}'}), 400
            
            print(f"✅ 服务发布成功，返回结果: {result}")
            
            # 验证发布结果
            if not result or not result.get('success'):
                print(f"❌ 发布结果无效: {result}")
                return jsonify({'error': '发布失败，返回结果无效'}), 500
            
            # 构建响应数据
            response_data = {
                'success': True,
                'message': '服务发布成功',
                'layer_name': result.get('layer_name'),
                'wms_url': result.get('wms_url'),
                'wfs_url': result.get('wfs_url'),
                'store_name': result.get('store_name'),
                'layer_info': result.get('layer_info')
            }
            
            print(f"✅ 响应数据: {response_data}")
            return jsonify(response_data), 200
            
        except Exception as publish_error:
            print(f"❌ 发布服务异常: {str(publish_error)}")
            import traceback
            traceback.print_exc()
            
            current_app.logger.error(f"发布服务失败: {str(publish_error)}")
            return jsonify({'error': f'发布服务失败: {str(publish_error)}'}), 500
    
    except Exception as e:
        print(f"❌ 发布服务总体异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        current_app.logger.error(f"发布服务错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/unpublish/<int:file_id>', methods=['DELETE'])
def unpublish_service(file_id):
    """取消发布文件服务
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: 文件ID
    responses:
      200:
        description: 取消发布成功
      404:
        description: 文件不存在或未发布
      500:
        description: 取消发布失败
    """
    try:
        print(f"\n=== 开始取消发布服务，文件ID: {file_id} ===")
        
        # 获取文件信息
        sql = "SELECT * FROM files WHERE id = %(file_id)s"
        result = execute_query(sql, {'file_id': file_id})
        
        if not result:
            print(f"❌ 文件不存在: {file_id}")
            return jsonify({'error': '文件不存在'}), 404
        
        file_info = result[0]
        print(f"文件信息: {file_info['file_name']}, 类型: {file_info['file_type']}")
        
        # 检查文件是否已发布 - 查询geoserver_layers表
        layer_sql = """
        SELECT gl.id as layer_id, gl.name as layer_name, gl.workspace_id, gl.featuretype_id, gl.coverage_id,
               gw.name as workspace_name
        FROM geoserver_layers gl
        JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        WHERE gl.file_id = %s
        """
        layer_result = execute_query(layer_sql, (file_id,))
        
        if not layer_result:
            print(f"⚠️ 文件未发布服务: {file_id}")
            return jsonify({'error': '文件未发布服务'}), 400
        
        layer_info = layer_result[0]
        print(f"图层信息: {layer_info}")
        
        # 查找相关的存储记录
        store_sql = """
        SELECT s.id as store_id, s.name as store_name, s.store_type
        FROM geoserver_stores s
        WHERE s.file_id = %s
        """
        store_result = execute_query(store_sql, (file_id,))
        
        if store_result:
            store_info = store_result[0]
            print(f"存储信息: {store_info}")
        else:
            # 如果没有找到存储记录，尝试根据命名规则查找
            store_name = f"file_{file_id}"
            store_sql_by_name = """
            SELECT s.id as store_id, s.name as store_name, s.store_type
            FROM geoserver_stores s
            WHERE s.name = %s
            """
            store_result = execute_query(store_sql_by_name, (store_name,))
            store_info = store_result[0] if store_result else None
            print(f"按名称查找的存储信息: {store_info}")
        
        # 从GeoServer删除服务
        store_name = f"file_{file_id}"
        file_type = file_info['file_type'].lower()
        
        print(f"\n--- 从GeoServer删除服务 ---")
        try:
            if file_type in ['tif', 'dem', 'dom']:
                geoserver_service.delete_layer(store_name, "coveragestore")
                print(f"✅ 从GeoServer删除覆盖存储: {store_name}")
            else:
                geoserver_service.delete_layer(store_name, "datastore")
                print(f"✅ 从GeoServer删除数据存储: {store_name}")
        except Exception as delete_error:
            print(f"⚠️ 从GeoServer删除服务失败: {str(delete_error)}")
            current_app.logger.warning(f"从GeoServer删除服务失败: {str(delete_error)}")
        
        # 删除数据库中的相关记录
        print(f"\n--- 删除数据库记录 ---")
        
        # 1. 删除图层记录（这会级联删除要素类型/覆盖记录）
        delete_layer_sql = "DELETE FROM geoserver_layers WHERE id = %s"
        affected_rows = execute_query(delete_layer_sql, (layer_info['layer_id'],), fetch=False)
        print(f"✅ 删除图层记录: {layer_info['layer_id']} (影响行数: {affected_rows})")
        
        # 2. 删除存储记录（如果存在）
        if store_info:
            # 检查是否还有其他图层使用此存储
            check_other_layers_sql = """
            SELECT COUNT(*) as count FROM geoserver_layers gl
            LEFT JOIN geoserver_featuretypes ft ON gl.featuretype_id = ft.id
            LEFT JOIN geoserver_coverages cov ON gl.coverage_id = cov.id
            WHERE (ft.store_id = %s OR cov.store_id = %s)
            """
            check_result = execute_query(check_other_layers_sql, (store_info['store_id'], store_info['store_id']))
            
            if check_result[0]['count'] == 0:
                # 没有其他图层使用此存储，可以安全删除
                delete_store_sql = "DELETE FROM geoserver_stores WHERE id = %s"
                affected_rows = execute_query(delete_store_sql, (store_info['store_id'],), fetch=False)
                print(f"✅ 删除存储记录: {store_info['store_id']} ({store_info['store_name']}) (影响行数: {affected_rows})")
            else:
                print(f"⚠️ 存储 {store_info['store_name']} 仍被其他图层使用，不删除")
        else:
            print(f"⚠️ 未找到对应的存储记录")
        
        print(f"✅ 取消发布服务完成")
        return jsonify({
            'success': True,
            'message': '取消发布成功',
            'deleted_layer': f"{layer_info['workspace_name']}:{layer_info['layer_name']}"
        }), 200
    
    except Exception as e:
        print(f"❌ 取消发布服务异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        current_app.logger.error(f"取消发布服务错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/debug/layer/<int:file_id>', methods=['GET'])
def debug_layer(file_id):
    """调试图层配置
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: 文件ID
    responses:
      200:
        description: 调试信息
    """
    try:
        # 获取文件信息
        sql = "SELECT * FROM files WHERE id = %(file_id)s"
        result = execute_query(sql, {'file_id': file_id})
        
        if not result:
            return jsonify({'error': '文件不存在'}), 404
        
        file_info = result[0]
        debug_info = {
            'file_info': file_info,
            'checks': []
        }
        
        # 检查文件是否存在
        file_path = file_info['file_path']
        debug_info['checks'].append({
            'name': '文件存在性检查',
            'status': 'success' if os.path.exists(file_path) else 'error',
            'message': f'文件路径: {file_path}',
            'result': '文件存在' if os.path.exists(file_path) else '文件不存在'
        })
        
        # 检查GeoServer图层
        if file_info.get('geoserver_layer'):
            layer_exists = geoserver_service.verify_layer_exists(file_info['geoserver_layer'])
            debug_info['checks'].append({
                'name': 'GeoServer图层检查',
                'status': 'success' if layer_exists else 'error',
                'message': f'图层名称: {file_info["geoserver_layer"]}',
                'result': '图层存在' if layer_exists else '图层不存在'
            })
            
            # 检查WMS服务
            if file_info.get('wms_url'):
                try:
                    wms_test_url = f"{file_info['wms_url']}?service=WMS&version=1.1.1&request=GetCapabilities"
                    response = requests.get(wms_test_url, timeout=10)
                    wms_available = response.status_code == 200
                    debug_info['checks'].append({
                        'name': 'WMS服务检查',
                        'status': 'success' if wms_available else 'error',
                        'message': f'WMS URL: {file_info["wms_url"]}',
                        'result': f'服务可用 (状态码: {response.status_code})' if wms_available else f'服务不可用 (状态码: {response.status_code})'
                    })
                except Exception as e:
                    debug_info['checks'].append({
                        'name': 'WMS服务检查',
                        'status': 'error',
                        'message': f'WMS URL: {file_info["wms_url"]}',
                        'result': f'连接失败: {str(e)}'
                    })
        else:
            debug_info['checks'].append({
                'name': 'GeoServer图层检查',
                'status': 'warning',
                'message': '未发布到GeoServer',
                'result': '图层未发布'
            })
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        current_app.logger.error(f"调试图层错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/geoserver/info', methods=['GET'])
def get_geoserver_info():
    """获取GeoServer完整信息
    ---
    tags:
      - GeoServer服务
    responses:
      200:
        description: GeoServer信息
    """
    try:
        # 获取工作空间信息
        workspaces_sql = """
        SELECT w.*, 
               COUNT(DISTINCT s.id) as store_count,
               COUNT(DISTINCT l.id) as layer_count
        FROM geoserver_workspaces w
        LEFT JOIN geoserver_stores s ON w.id = s.workspace_id
        LEFT JOIN geoserver_layers l ON w.id = l.workspace_id
        GROUP BY w.id
        ORDER BY w.is_default DESC, w.name
        """
        workspaces = execute_query(workspaces_sql)
        
        # 获取存储仓库信息
        stores_sql = """
        SELECT s.*, w.name as workspace_name, f.file_name
        FROM geoserver_stores s
        JOIN geoserver_workspaces w ON s.workspace_id = w.id
        LEFT JOIN files f ON s.file_id = f.id
        ORDER BY w.name, s.name
        """
        stores = execute_query(stores_sql)
        
        # 获取图层信息
        layers_sql = """
        SELECT l.*, w.name as workspace_name, 
               ft.name as featuretype_name, ft.srs,
               s.name as store_name, s.store_type, s.data_type,
               f.file_name, f.file_type
        FROM geoserver_layers l
        JOIN geoserver_workspaces w ON l.workspace_id = w.id
        LEFT JOIN geoserver_featuretypes ft ON l.featuretype_id = ft.id
        LEFT JOIN geoserver_stores s ON ft.store_id = s.id OR l.workspace_id = s.workspace_id
        LEFT JOIN files f ON l.file_id = f.id
        ORDER BY w.name, l.name
        """
        layers = execute_query(layers_sql)
        
        # 获取要素类型信息
        featuretypes_sql = """
        SELECT ft.*, s.name as store_name, w.name as workspace_name
        FROM geoserver_featuretypes ft
        JOIN geoserver_stores s ON ft.store_id = s.id
        JOIN geoserver_workspaces w ON s.workspace_id = w.id
        ORDER BY w.name, s.name, ft.name
        """
        featuretypes = execute_query(featuretypes_sql)
        
        # 获取样式信息
        styles_sql = """
        SELECT st.*, w.name as workspace_name
        FROM geoserver_styles st
        LEFT JOIN geoserver_workspaces w ON st.workspace_id = w.id
        ORDER BY w.name, st.name
        """
        styles = execute_query(styles_sql)
        
        return jsonify({
            'workspaces': workspaces,
            'stores': stores,
            'layers': layers,
            'featuretypes': featuretypes,
            'styles': styles,
            'summary': {
                'workspace_count': len(workspaces),
                'store_count': len(stores),
                'layer_count': len(layers),
                'featuretype_count': len(featuretypes),
                'style_count': len(styles)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取GeoServer信息错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/workspace/<workspace_name>/info', methods=['GET'])
def get_workspace_info(workspace_name):
    """获取特定工作空间的详细信息
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: workspace_name
        in: path
        type: string
        required: true
        description: 工作空间名称
    responses:
      200:
        description: 工作空间信息
      404:
        description: 工作空间不存在
    """
    try:
        # 获取工作空间基本信息
        workspace_sql = "SELECT * FROM geoserver_workspaces WHERE name = %s"
        workspace_result = execute_query(workspace_sql, (workspace_name,))
        
        if not workspace_result:
            return jsonify({'error': '工作空间不存在'}), 404
        
        workspace = workspace_result[0]
        
        # 获取该工作空间的存储仓库
        stores_sql = """
        SELECT s.*, f.file_name, f.file_type
        FROM geoserver_stores s
        LEFT JOIN files f ON s.file_id = f.id
        WHERE s.workspace_id = %s
        ORDER BY s.name
        """
        stores = execute_query(stores_sql, (workspace['id'],))
        
        # 获取该工作空间的图层
        layers_sql = """
        SELECT l.*, ft.name as featuretype_name, ft.srs,
               s.name as store_name, f.file_name
        FROM geoserver_layers l
        LEFT JOIN geoserver_featuretypes ft ON l.featuretype_id = ft.id
        LEFT JOIN geoserver_stores s ON ft.store_id = s.id
        LEFT JOIN files f ON l.file_id = f.id
        WHERE l.workspace_id = %s
        ORDER BY l.name
        """
        layers = execute_query(layers_sql, (workspace['id'],))
        
        # 获取该工作空间的样式
        styles_sql = """
        SELECT * FROM geoserver_styles 
        WHERE workspace_id = %s
        ORDER BY name
        """
        styles = execute_query(styles_sql, (workspace['id'],))
        
        return jsonify({
            'workspace': workspace,
            'stores': stores,
            'layers': layers,
            'styles': styles,
            'summary': {
                'store_count': len(stores),
                'layer_count': len(layers),
                'style_count': len(styles)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取工作空间信息错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@geoservice_bp.route('/layer/<int:layer_id>/details', methods=['GET'])
def get_layer_details(layer_id):
    """获取图层详细信息
    ---
    tags:
      - GeoServer服务
    parameters:
      - name: layer_id
        in: path
        type: integer
        required: true
        description: 图层ID
    responses:
      200:
        description: 图层详细信息
      404:
        description: 图层不存在
    """
    try:
        # 获取图层详细信息
        layer_sql = """
        SELECT l.*, w.name as workspace_name, w.namespace_uri,
               ft.name as featuretype_name, ft.native_name, ft.title as ft_title,
               ft.abstract as ft_abstract, ft.keywords, ft.srs, 
               ft.native_bbox, ft.lat_lon_bbox, ft.attributes,
               s.name as store_name, s.store_type, s.data_type, s.connection_params,
               f.file_name, f.file_type, f.file_path, f.file_size, f.upload_date
        FROM geoserver_layers l
        JOIN geoserver_workspaces w ON l.workspace_id = w.id
        LEFT JOIN geoserver_featuretypes ft ON l.featuretype_id = ft.id
        LEFT JOIN geoserver_stores s ON ft.store_id = s.id
        LEFT JOIN files f ON l.file_id = f.id
        WHERE l.id = %s
        """
        layer_result = execute_query(layer_sql, (layer_id,))
        
        if not layer_result:
            return jsonify({'error': '图层不存在'}), 404
        
        layer = layer_result[0]
        
        # 构建完整的图层名称
        full_layer_name = f"{layer['workspace_name']}:{layer['name']}"
        
        # 构建服务URL
        service_urls = {
            'wms_capabilities': f"{geoserver_service.url}/wms?service=WMS&version=1.3.0&request=GetCapabilities",
            'wfs_capabilities': f"{geoserver_service.url}/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
            'wms_getmap': f"{geoserver_service.url}/wms?service=WMS&version=1.3.0&request=GetMap&layers={full_layer_name}&styles=&bbox=-180,-90,180,90&width=768&height=384&srs=EPSG:4326&format=image/png",
            'wfs_getfeature': f"{geoserver_service.url}/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName={full_layer_name}&outputFormat=application/json"
        }
        
        return jsonify({
            'layer': layer,
            'full_layer_name': full_layer_name,
            'service_urls': service_urls
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取图层详细信息错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500 