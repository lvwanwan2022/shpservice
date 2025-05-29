#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.file_service import FileService
from models.db import execute_query
from werkzeug.utils import secure_filename
import os
import json

file_bp = Blueprint('file', __name__)
file_service = FileService()

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件接口"""
    print("=== 文件上传请求开始 ===")
    print("请求文件:", request.files.keys())
    print("请求表单:", dict(request.form))
    
    if 'file' not in request.files:
        print("错误: 未找到文件")
        return jsonify({'error': '未找到文件'}), 400
    
    file = request.files['file']
    print(f"文件名: {file.filename}")
    
    if file.filename == '':
        print("错误: 未选择文件")
        return jsonify({'error': '未选择文件'}), 400
    
    try:
        # 从表单获取元数据
        metadata = {
            'file_name': request.form.get('file_name') or secure_filename(file.filename),
            'original_name': file.filename,  # 新增原始文件名
            'discipline': request.form.get('discipline'),
            'dimension': request.form.get('dimension'),
            'is_public': request.form.get('is_public', 'true').lower() == 'true',
            'file_type': request.form.get('file_type'),
            'coordinate_system': request.form.get('coordinate_system'),
            'tags': request.form.get('tags', ''),
            'description': request.form.get('description', ''),
            'user_id': request.form.get('user_id', 1),  # 暂时使用固定用户ID
            'status': 'uploaded',  # 新增状态字段
            'geometry_type': request.form.get('geometry_type'),  # 新增几何类型
            'feature_count': request.form.get('feature_count'),  # 新增要素数量
            'bbox': request.form.get('bbox'),  # 新增边界框
            'metadata': request.form.get('metadata')  # 新增元数据JSON
        }
        
        print("元数据:", metadata)
        
        # 验证必填字段
        required_fields = ['file_name', 'original_name', 'discipline', 'dimension', 'file_type']
        for field in required_fields:
            if not metadata.get(field):
                print(f"错误: 缺少必填字段: {field}")
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证DWG/DXF类型必须有坐标系
        if metadata['file_type'].lower() in ['dwg', 'dxf'] and not metadata.get('coordinate_system'):
            print("错误: DWG/DXF文件必须指定坐标系")
            return jsonify({'error': 'DWG/DXF文件必须指定坐标系'}), 400
        
        # 保存文件并记录元数据
        file_id, file_data = file_service.save_file(file, metadata)
        
        print(f"文件上传成功，ID: {file_id}")
        return jsonify({
            'id': file_id,
            'message': '数据上传成功，如需发布服务请手动点击发布按钮',
            'file': {
                'id': file_id,
                'file_name': file_data['file_name'],
                'original_name': file_data.get('original_name', ''),
                'file_size': file_data['file_size'],
                'file_type': file_data['file_type'],
                'discipline': file_data.get('discipline', ''),
                'dimension': file_data.get('dimension', ''),
                'coordinate_system': file_data.get('coordinate_system', ''),
                'status': file_data.get('status', 'uploaded'),
                'geometry_type': file_data.get('geometry_type', ''),
                'feature_count': file_data.get('feature_count', 0),
                'bbox': file_data.get('bbox'),
                'upload_date': file_data.get('upload_date', '')
            }
        }), 200
    
    except ValueError as e:
        print(f"值错误: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        print(f"服务器错误: {str(e)}")
        current_app.logger.error(f"文件上传错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/list', methods=['GET'])
def get_file_list():
    """获取文件列表
    ---
    tags:
      - 文件管理
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: 页码
      - name: page_size
        in: query
        type: integer
        required: false
        default: 20
        description: 每页数量
      - name: user_id
        in: query
        type: integer
        required: false
        description: 用户ID过滤
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
      - name: dimension
        in: query
        type: string
        required: false
        description: 维度过滤
      - name: status
        in: query
        type: string
        required: false
        description: 状态过滤
      - name: geometry_type
        in: query
        type: string
        required: false
        description: 几何类型过滤
      - name: search
        in: query
        type: string
        required: false
        description: 搜索关键词
      - name: sort_by
        in: query
        type: string
        required: false
        default: upload_date
        description: 排序字段
      - name: sort_order
        in: query
        type: string
        required: false
        default: desc
        description: 排序方向
    responses:
      200:
        description: 文件列表
    """
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        user_id = request.args.get('user_id')
        discipline = request.args.get('discipline')
        file_type = request.args.get('file_type')
        dimension = request.args.get('dimension')
        status = request.args.get('status')
        geometry_type = request.args.get('geometry_type')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'upload_date')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 构建基础查询 - 添加LEFT JOIN来获取发布状态（包括Martin服务）
        base_query = """
        SELECT f.*, u.username as uploader,
               gl.id as geoserver_layer_id, 
               CONCAT(gw.name, ':', gl.name) as geoserver_layer_name, 
               gl.wms_url as geoserver_wms_url, 
               gl.wfs_url as geoserver_wfs_url,
               COALESCE(gms.id, sms.id) as martin_service_id,
               COALESCE(gms.file_id, sms.file_id) as martin_file_id,
               COALESCE(gms.table_name, sms.table_name) as martin_table_name,
               COALESCE(gms.mvt_url, sms.mvt_url) as martin_mvt_url,
               COALESCE(gms.tilejson_url, sms.tilejson_url) as martin_tilejson_url,
               COALESCE(gms.style, sms.style) as martin_style,
               COALESCE(gms.status, sms.status) as martin_status
        FROM files f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN geoserver_layers gl ON f.id = gl.file_id
        LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        LEFT JOIN geojson_martin_services gms ON f.file_name = gms.original_filename AND gms.status = 'active'
        LEFT JOIN shp_martin_services sms ON f.file_name = sms.original_filename AND sms.status = 'active'
        """
        
        # 构建WHERE条件
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("f.user_id = %s")
            params.append(user_id)
        
        if discipline:
            where_conditions.append("f.discipline = %s")
            params.append(discipline)
        
        if file_type:
            where_conditions.append("f.file_type = %s")
            params.append(file_type)
        
        if dimension:
            where_conditions.append("f.dimension = %s")
            params.append(dimension)
        
        if status:
            where_conditions.append("f.status = %s")
            params.append(status)
        
        if geometry_type:
            where_conditions.append("f.geometry_type = %s")
            params.append(geometry_type)
        
        if search:
            where_conditions.append("(f.file_name ILIKE %s OR f.description ILIKE %s OR f.tags ILIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # 添加WHERE子句
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        # 添加排序
        allowed_sort_fields = ['upload_date', 'file_name', 'file_size', 'file_type', 'discipline']
        if sort_by not in allowed_sort_fields:
            sort_by = 'upload_date'
        
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        base_query += f" ORDER BY f.{sort_by} {sort_order.upper()}"
        
        # 添加分页
        offset = (page - 1) * page_size
        query = base_query + f" LIMIT {page_size} OFFSET {offset}"
        
        # 执行查询
        files = execute_query(query, params)
        
        # 获取总数
        count_query = """
        SELECT COUNT(DISTINCT f.id)
        FROM files f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN geoserver_layers gl ON f.id = gl.file_id
        LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        LEFT JOIN geojson_martin_services gms ON f.file_name = gms.original_filename AND gms.status = 'active'
        LEFT JOIN shp_martin_services sms ON f.file_name = sms.original_filename AND sms.status = 'active'
        """
        
        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions)
        
        total_result = execute_query(count_query, params)
        total = total_result[0]['count'] if total_result else 0
        
        # 处理结果
        for file in files:
            # 处理JSON字段
            if file.get('bbox'):
                try:
                    file['bbox'] = json.loads(file['bbox']) if isinstance(file['bbox'], str) else file['bbox']
                except:
                    file['bbox'] = None
            
            if file.get('metadata'):
                try:
                    file['metadata'] = json.loads(file['metadata']) if isinstance(file['metadata'], str) else file['metadata']
                except:
                    file['metadata'] = {}
            
            # 获取服务类型和Martin服务信息
            martin_service_id = file.get('martin_service_id')
            martin_file_id = file.get('martin_file_id')
            martin_table_name = file.get('martin_table_name')
            martin_status = file.get('martin_status')
            geoserver_layer_id = file.get('geoserver_layer_id')
            
            # 添加Martin服务状态信息
            martin_service_info = {
                'is_published': martin_service_id is not None and martin_status == 'active',
                'service_id': martin_service_id,
                'file_id': martin_file_id,
                'table_name': martin_table_name,
                'mvt_url': file.get('martin_mvt_url'),
                'tilejson_url': file.get('martin_tilejson_url'),
                'style': file.get('martin_style'),
                'status': martin_status
            }
            
            # 添加GeoServer服务状态信息
            geoserver_service_info = {
                'is_published': geoserver_layer_id is not None,
                'layer_id': geoserver_layer_id,
                'layer_name': file.get('geoserver_layer_name'),
                'wms_url': file.get('geoserver_wms_url'),
                'wfs_url': file.get('geoserver_wfs_url')
            }
            
            # 保持向后兼容的published_info字段（优先显示Martin服务）
            if martin_service_info['is_published']:
                published_info = {
                    'is_published': True,
                    'service_type': 'martin',
                    **martin_service_info
                }
            elif geoserver_service_info['is_published']:
                published_info = {
                    'is_published': True,
                    'service_type': 'geoserver',
                    **geoserver_service_info
                }
            else:
                published_info = {
                    'is_published': False,
                    'service_type': None
                }
            
            file['martin_service'] = martin_service_info
            file['geoserver_service'] = geoserver_service_info
            file['published_info'] = published_info
            
            # 清理临时字段
            for key in ['geoserver_layer_id', 'geoserver_layer_name', 'geoserver_wms_url', 'geoserver_wfs_url', 
                       'martin_service_id', 'martin_file_id', 'martin_table_name', 'martin_mvt_url', 'martin_tilejson_url',
                       'martin_style', 'martin_status', 'is_published', 'service_type']:
                file.pop(key, None)
        
        return jsonify({
            'files': files,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取文件列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/<int:file_id>', methods=['GET'])
def get_file(file_id):
    """获取文件详情"""
    try:
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        return jsonify(file_info), 200
    
    except Exception as e:
        current_app.logger.error(f"获取文件详情错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    """更新文件信息"""
    try:
        data = request.json
        
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 准备更新数据
        update_data = {}
        allowed_fields = [
            'file_name', 'discipline', 'dimension', 'file_type', 
            'coordinate_system', 'tags', 'description', 'is_public',
            'status', 'geometry_type', 'feature_count', 'bbox', 'metadata'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # 更新文件信息
        file_service.update_file(file_id, update_data)
        
        return jsonify({'message': '文件信息更新成功'}), 200
    
    except Exception as e:
        current_app.logger.error(f"更新文件信息错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件"""
    try:
        file_service.delete_file(file_id)
        return jsonify({'message': '文件删除成功'}), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        current_app.logger.error(f"删除文件错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    try:
        sql = "SELECT id, username FROM users ORDER BY username"
        users = execute_query(sql)
        
        return jsonify({
            'users': users
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取用户列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/statistics', methods=['GET'])
def get_file_statistics():
    """获取文件统计信息"""
    try:
        stats = file_service.get_file_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        current_app.logger.error(f"获取文件统计错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/disciplines', methods=['GET'])
def get_disciplines():
    """获取学科列表"""
    try:
        sql = "SELECT DISTINCT discipline FROM files WHERE discipline IS NOT NULL ORDER BY discipline"
        result = execute_query(sql)
        disciplines = [row['discipline'] for row in result]
        
        return jsonify({
            'disciplines': disciplines
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取学科列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/file-types', methods=['GET'])
def get_file_types():
    """获取文件类型列表"""
    try:
        sql = "SELECT DISTINCT file_type FROM files WHERE file_type IS NOT NULL ORDER BY file_type"
        result = execute_query(sql)
        file_types = [row['file_type'] for row in result]
        
        return jsonify({
            'file_types': file_types
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"获取文件类型列表错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/<int:file_id>/publish/martin', methods=['POST'])
def publish_martin_service(file_id):
    """发布文件到Martin服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型是否支持Martin服务
        file_type = file_info.get('file_type', '').lower()
        if file_type not in ['geojson', 'shp']:
            return jsonify({'error': 'Martin服务仅支持GeoJSON和SHP文件'}), 400
        
        if file_type == 'geojson':
            # GeoJSON文件处理
            # 检查是否已发布到Martin
            check_sql = """
            SELECT id, file_id FROM geojson_martin_services 
            WHERE original_filename = %s AND status = 'active'
            """
            existing = execute_query(check_sql, (file_info['file_name'],))
            if existing:
                return jsonify({
                    'error': '文件已发布到Martin服务',
                    'martin_file_id': existing[0]['file_id']
                }), 400
            
            # 发布到Martin服务
            from services.geojson_martin_service import GeoJsonMartinService
            martin_service = GeoJsonMartinService()
            result = martin_service.publish_existing_file(file_id)
            
        elif file_type == 'shp':
            # SHP文件处理
            # 检查是否已发布到Martin
            check_sql = """
            SELECT id, file_id FROM shp_martin_services 
            WHERE original_filename = %s AND status = 'active'
            """
            existing = execute_query(check_sql, (file_info['file_name'],))
            if existing:
                return jsonify({
                    'error': '文件已发布到Martin服务',
                    'martin_file_id': existing[0]['file_id']
                }), 400
            
            # 发布到Martin服务
            from services.shp_martin_service import ShpMartinService
            martin_service = ShpMartinService()
            result = martin_service.publish_existing_file(file_id)
        
        return jsonify({
            'success': True,
            'message': 'Martin服务发布成功',
            'martin_info': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"发布Martin服务错误: {str(e)}")
        return jsonify({'error': f'发布Martin服务失败: {str(e)}'}), 500

@file_bp.route('/<int:file_id>/publish/geoserver', methods=['POST'])
def publish_geoserver_service(file_id):
    """发布文件到GeoServer服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型是否支持GeoServer服务
        file_type = file_info.get('file_type', '').lower()
        supported_types = ['shp', 'geojson', 'tif', 'dem', 'dom']
        if file_type not in supported_types:
            return jsonify({'error': f'GeoServer服务不支持{file_type}文件类型'}), 400
        
        # 检查是否已发布到GeoServer
        check_sql = "SELECT id, name FROM geoserver_layers WHERE file_id = %s"
        existing = execute_query(check_sql, (file_id,))
        if existing:
            return jsonify({
                'error': '文件已发布到GeoServer服务',
                'layer_id': existing[0]['id'],
                'layer_name': existing[0]['name']
            }), 400
        
        # 发布到GeoServer服务
        from services.geoserver_service import GeoServerService
        geoserver_service = GeoServerService()
        
        # 生成数据存储名称
        store_name = f"file_{file_id}"
        file_path = file_info['file_path']
        
        # 根据文件类型发布服务
        if file_type == 'shp':
            result = geoserver_service.publish_shapefile(file_path, store_name, file_id)
        elif file_type == 'geojson':
            result = geoserver_service.publish_geojson(file_path, store_name, file_id)
        elif file_type in ['tif', 'dem', 'dom']:
            result = geoserver_service.publish_geotiff(file_path, store_name, file_id)
        
        return jsonify({
            'success': True,
            'message': 'GeoServer服务发布成功',
            'geoserver_info': result
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"发布GeoServer服务错误: {str(e)}")
        return jsonify({'error': f'发布GeoServer服务失败: {str(e)}'}), 500

@file_bp.route('/<int:file_id>/unpublish/martin', methods=['DELETE'])
def unpublish_martin_service(file_id):
    """取消发布Martin服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        file_type = file_info.get('file_type', '').lower()
        martin_file_id = None
        service_type = None
        
        # 查找GeoJSON Martin服务记录
        geojson_check_sql = """
        SELECT file_id FROM geojson_martin_services 
        WHERE original_filename = %s AND status = 'active'
        """
        geojson_existing = execute_query(geojson_check_sql, (file_info['file_name'],))
        
        # 查找SHP Martin服务记录
        shp_check_sql = """
        SELECT file_id FROM shp_martin_services 
        WHERE original_filename = %s AND status = 'active'
        """
        shp_existing = execute_query(shp_check_sql, (file_info['file_name'],))
        
        if geojson_existing:
            martin_file_id = geojson_existing[0]['file_id']
            service_type = 'geojson'
        elif shp_existing:
            martin_file_id = shp_existing[0]['file_id']
            service_type = 'shp'
        else:
            return jsonify({'error': '文件未发布到Martin服务'}), 404
        
        # 根据服务类型删除对应的Martin服务
        if service_type == 'geojson':
            from services.geojson_martin_service import GeoJsonMartinService
            martin_service = GeoJsonMartinService()
            result = martin_service.delete_service(martin_file_id)
        elif service_type == 'shp':
            from services.shp_martin_service import ShpMartinService
            martin_service = ShpMartinService()
            # 需要为SHP Martin服务添加delete_service方法
            result = martin_service.delete_service(martin_file_id)
        
        return jsonify({
            'success': True,
            'message': 'Martin服务取消发布成功',
            'service_type': service_type
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"取消发布Martin服务错误: {str(e)}")
        return jsonify({'error': f'取消发布Martin服务失败: {str(e)}'}), 500

@file_bp.route('/<int:file_id>/unpublish/geoserver', methods=['DELETE'])
def unpublish_geoserver_service(file_id):
    """取消发布GeoServer服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 查找GeoServer图层记录
        check_sql = "SELECT id, name FROM geoserver_layers WHERE file_id = %s"
        existing = execute_query(check_sql, (file_id,))
        if not existing:
            return jsonify({'error': '文件未发布到GeoServer服务'}), 404
        
        layer_id = existing[0]['id']
        
        # 删除GeoServer服务
        from services.geoserver_service import GeoServerService
        geoserver_service = GeoServerService()
        
        result = geoserver_service.unpublish_layer(layer_id)
        
        return jsonify({
            'success': True,
            'message': 'GeoServer服务取消发布成功'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"取消发布GeoServer服务错误: {str(e)}")
        return jsonify({'error': f'取消发布GeoServer服务失败: {str(e)}'}), 500 