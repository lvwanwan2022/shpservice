#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.file_service import FileService
from models.db import execute_query
from werkzeug.utils import secure_filename
from config import FILE_STORAGE
import os
import json
import time

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

# ========== 分片上传相关路由 ==========

# 存储分片上传的临时信息
chunked_uploads = {}

@file_bp.route('/upload/chunked/init', methods=['POST'])
def init_chunked_upload():
    """初始化分片上传"""
    print("=== 初始化分片上传 ===")
    
    data = request.get_json()
    upload_id = data.get('upload_id')
    file_name = data.get('file_name')
    total_chunks = data.get('total_chunks')
    metadata = data.get('metadata', {})
    
    print(f"上传ID: {upload_id}")
    print(f"文件名: {file_name}")
    print(f"总分片数: {total_chunks}")
    print(f"元数据: {metadata}")
    
    if not all([upload_id, file_name, total_chunks]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 创建临时目录
    temp_base = FILE_STORAGE.get('temp_folder', 'temp')
    temp_dir = os.path.join(temp_base, 'chunks', upload_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    # 存储上传信息
    chunked_uploads[upload_id] = {
        'file_name': file_name,
        'total_chunks': total_chunks,
        'received_chunks': set(),
        'temp_dir': temp_dir,
        'metadata': metadata,
        'created_at': time.time()
    }
    
    print(f"分片上传初始化成功，临时目录: {temp_dir}")
    return jsonify({'message': '分片上传初始化成功', 'upload_id': upload_id})

@file_bp.route('/upload/chunked/chunk', methods=['POST'])
def upload_chunk():
    """上传单个分片"""
    upload_id = request.form.get('upload_id')
    chunk_index = int(request.form.get('chunk_index'))
    
    if 'chunk' not in request.files:
        return jsonify({'error': '未找到分片文件'}), 400
    
    chunk_file = request.files['chunk']
    
    print(f"接收分片: upload_id={upload_id}, chunk_index={chunk_index}, size={len(chunk_file.read())}B")
    chunk_file.seek(0)  # 重置文件指针
    
    if upload_id not in chunked_uploads:
        return jsonify({'error': '无效的上传ID'}), 400
    
    upload_info = chunked_uploads[upload_id]
    
    # 保存分片文件
    chunk_path = os.path.join(upload_info['temp_dir'], f'chunk_{chunk_index}')
    chunk_file.save(chunk_path)
    
    # 记录已接收的分片
    upload_info['received_chunks'].add(chunk_index)
    
    print(f"分片 {chunk_index} 保存成功，已接收: {len(upload_info['received_chunks'])}/{upload_info['total_chunks']}")
    
    return jsonify({
        'message': '分片上传成功',
        'chunk_index': chunk_index,
        'received_chunks': len(upload_info['received_chunks']),
        'total_chunks': upload_info['total_chunks']
    })

@file_bp.route('/upload/chunked/complete', methods=['POST'])
def complete_chunked_upload():
    """完成分片上传，合并文件"""
    print("=== 完成分片上传 ===")
    
    data = request.get_json()
    upload_id = data.get('upload_id')
    
    if upload_id not in chunked_uploads:
        return jsonify({'error': '无效的上传ID'}), 400
    
    upload_info = chunked_uploads[upload_id]
    
    # 检查是否所有分片都已接收
    expected_chunks = set(range(upload_info['total_chunks']))
    if upload_info['received_chunks'] != expected_chunks:
        missing_chunks = expected_chunks - upload_info['received_chunks']
        return jsonify({'error': f'缺少分片: {list(missing_chunks)}'}), 400
    
    try:
        # 合并文件
        print("开始合并文件...")
        final_file_path = os.path.join(upload_info['temp_dir'], upload_info['file_name'])
        
        with open(final_file_path, 'wb') as final_file:
            for chunk_index in range(upload_info['total_chunks']):
                chunk_path = os.path.join(upload_info['temp_dir'], f'chunk_{chunk_index}')
                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
                # 删除分片文件
                os.remove(chunk_path)
        
        print(f"文件合并完成: {final_file_path}")
        
        # 创建文件对象用于保存
        class FileObject:
            def __init__(self, file_path, filename):
                self.file_path = file_path
                self.filename = filename
                with open(file_path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    self.size = f.tell()
            
            def save(self, destination):
                import shutil
                shutil.move(self.file_path, destination)
                return destination
            
            def read(self):
                with open(self.file_path, 'rb') as f:
                    return f.read()
        
        file_obj = FileObject(final_file_path, upload_info['file_name'])
        
        # 使用现有的文件保存逻辑
        metadata = upload_info['metadata']
        metadata['file_name'] = metadata.get('file_name') or secure_filename(upload_info['file_name'])
        metadata['original_name'] = upload_info['file_name']
        
        # 验证必填字段
        required_fields = ['file_name', 'original_name', 'discipline', 'dimension', 'file_type']
        for field in required_fields:
            if not metadata.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 保存文件并记录元数据
        file_id, file_data = file_service.save_file(file_obj, metadata)
        
        # 清理临时数据
        import shutil
        shutil.rmtree(upload_info['temp_dir'], ignore_errors=True)
        del chunked_uploads[upload_id]
        
        print(f"分片上传完成，文件ID: {file_id}")
        
        return jsonify({
            'id': file_id,
            'message': '分片上传成功，如需发布服务请手动点击发布按钮',
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
    
    except Exception as e:
        print(f"合并文件失败: {str(e)}")
        current_app.logger.error(f"分片上传合并失败: {str(e)}")
        return jsonify({'error': '文件合并失败'}), 500

@file_bp.route('/upload/chunked/abort', methods=['POST'])
def abort_chunked_upload():
    """取消分片上传"""
    print("=== 取消分片上传 ===")
    
    data = request.get_json()
    upload_id = data.get('upload_id')
    
    if upload_id not in chunked_uploads:
        return jsonify({'error': '无效的上传ID'}), 400
    
    upload_info = chunked_uploads[upload_id]
    
    # 清理临时文件
    import shutil
    shutil.rmtree(upload_info['temp_dir'], ignore_errors=True)
    del chunked_uploads[upload_id]
    
    print(f"分片上传已取消: {upload_id}")
    return jsonify({'message': '分片上传已取消'})

@file_bp.route('/files/list', methods=['GET'])
def get_files_list():
    """获取文件列表 - /files/list 端点
    """
    return get_file_list()

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
        
        # 构建基础查询 - 使用统一的vector_martin_services表
        base_query = """
        SELECT f.*, u.username as uploader,
               gl.id as geoserver_layer_id, 
               CONCAT(gw.name, ':', gl.name) as geoserver_layer_name, 
               gl.wms_url as geoserver_wms_url, 
               gl.wfs_url as geoserver_wfs_url,
               vms.id as martin_service_id,
               vms.file_id as martin_file_id,
               vms.vector_type as martin_vector_type,
               vms.table_name as martin_table_name,
               vms.mvt_url as martin_mvt_url,
               vms.tilejson_url as martin_tilejson_url,
               vms.style as martin_style,
               vms.status as martin_status
        FROM files f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN geoserver_layers gl ON f.id = gl.file_id
        LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        LEFT JOIN vector_martin_services vms ON f.file_name = vms.original_filename AND vms.status = 'active'
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
        LEFT JOIN vector_martin_services vms ON f.file_name = vms.original_filename AND vms.status = 'active'
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

@file_bp.route('/files/<int:file_id>', methods=['GET'])
def get_files_file(file_id):
    """获取文件详情 - /files/<file_id> 端点"""
    return get_file(file_id)

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

@file_bp.route('/files/users', methods=['GET'])
def get_files_users():
    """获取用户列表 - /files/users 端点"""
    return get_users()

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
        if file_type not in ['geojson', 'shp', 'dxf']:
            return jsonify({'error': 'Martin服务仅支持GeoJSON、SHP和DXF文件'}), 400
        
        # 检查是否已发布到Martin（统一表查询）
        check_sql = """
        SELECT id, file_id, vector_type FROM vector_martin_services 
        WHERE original_filename = %s AND status = 'active'
        """
        existing = execute_query(check_sql, (file_info['file_name'],))
        if existing:
            return jsonify({
                'error': '文件已发布到Martin服务',
                'martin_file_id': existing[0]['file_id'],
                'vector_type': existing[0]['vector_type']
            }), 400
        
        # 根据文件类型选择发布服务
        if file_type in ['geojson', 'shp']:
            # 使用统一的Vector Martin服务
            from services.vector_martin_service import VectorMartinService
            martin_service = VectorMartinService()
            
            if file_type == 'geojson':
                result = martin_service.publish_geojson_martin(
                    file_id=str(file_id),
                    file_path=file_info['file_path'],
                    original_filename=file_info['file_name'],
                    user_id=file_info.get('user_id')
                )
            elif file_type == 'shp':
                result = martin_service.publish_shp_martin(
                    file_id=str(file_id),
                    zip_file_path=file_info['file_path'],
                    original_filename=file_info['file_name'],
                    user_id=file_info.get('user_id')
                )
        
        elif file_type == 'dxf':
            # 使用DXF服务发布
            from services.dxf_service import DXFService
            dxf_service = DXFService()
            
            # 从请求中获取坐标系参数
            coordinate_system = request.json.get('coordinate_system', 'EPSG:4326') if request.is_json else 'EPSG:4326'
            
            result = dxf_service.publish_dxf_martin_service(
                file_id=str(file_id),
                file_path=file_info['file_path'],
                original_filename=file_info['file_name'],
                coordinate_system=coordinate_system,
                user_id=file_info.get('user_id')
            )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Martin服务发布成功',
                'martin_info': result
            }), 200
        else:
            return jsonify({
                'error': f'Martin服务发布失败: {result.get("error", "未知错误")}'
            }), 500
    
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
        supported_types = ['shp', 'geojson', 'tif', 'tiff', 'dem', 'dom', 'dem.tif', 'dom.tif', 'dxf']
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
        
        # 根据文件类型选择发布方式
        if file_type in ['shp', 'geojson', 'tif', 'tiff', 'dem', 'dom', 'dem.tif', 'dom.tif']:
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
            elif file_type in ['tif', 'tiff', 'dem', 'dom', 'dem.tif', 'dom.tif']:
                result = geoserver_service.publish_geotiff(file_path, store_name, file_id)
        
        elif file_type == 'dxf':
            # 使用DXF服务发布到GeoServer
            from services.dxf_service import DXFService
            dxf_service = DXFService()
            
            # 从请求中获取坐标系参数
            coordinate_system = request.json.get('coordinate_system', 'EPSG:4326') if request.is_json else 'EPSG:4326'
            
            # 检查是否可以复用已存在的PostGIS表
            table_name = None
            # 查询是否有相同文件的Martin服务（可复用PostGIS表）
            martin_check_sql = """
            SELECT table_name FROM vector_martin_services 
            WHERE original_filename = %s AND vector_type = 'dxf' AND status = 'active'
            """
            martin_result = execute_query(martin_check_sql, (file_info['file_name'],))
            if martin_result:
                table_name = martin_result[0]['table_name']
                current_app.logger.info(f"复用Martin服务的PostGIS表: {table_name}")
            
            result = dxf_service.publish_dxf_geoserver_service(
                file_id=str(file_id),
                table_name=table_name,
                coordinate_system=coordinate_system
            )
        
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
        
        # 查找Martin服务记录（统一表查询）
        check_sql = """
        SELECT id, file_id, vector_type FROM vector_martin_services 
        WHERE original_filename = %s AND status = 'active'
        """
        existing = execute_query(check_sql, (file_info['file_name'],))
        
        if not existing:
            return jsonify({'error': '文件未发布到Martin服务'}), 404
        
        service_id = existing[0]['id']
        martin_file_id = existing[0]['file_id']
        vector_type = existing[0]['vector_type']
        
        # 根据vector_type选择删除方式
        if vector_type == 'dxf':
            from services.dxf_service import DXFService
            dxf_service = DXFService()
            result = dxf_service.delete_dxf_martin_service(service_id)
            success = result.get('success', False)
        else:
            # 使用统一的Vector Martin服务删除
            from services.vector_martin_service import VectorMartinService
            martin_service = VectorMartinService()
            success = martin_service.delete_martin_service(service_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Martin服务取消发布成功',
                'vector_type': vector_type
            }), 200
        else:
            return jsonify({'error': 'Martin服务删除失败'}), 500
    
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

@file_bp.route('/coordinate-systems/search', methods=['GET'])
def search_coordinate_systems():
    """搜索坐标系"""
    try:
        # 获取搜索关键词
        keyword = request.args.get('keyword', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({'error': '请提供搜索关键词'}), 400
        
        # 按空格分割关键词，支持多关键词搜索
        keywords = [k.strip() for k in keyword.split() if k.strip()]
        
        if not keywords:
            return jsonify({'error': '请提供有效的搜索关键词'}), 400
        
        # 构建多关键词搜索SQL
        # 每个关键词都要在所有字段中搜索，使用AND连接不同关键词
        keyword_conditions = []
        params = []
        
        for i, kw in enumerate(keywords):
            # 为每个关键词构建OR条件（在不同字段中搜索）
            keyword_condition = f"""
            (
                LOWER(srtext) LIKE LOWER(%s) 
                OR LOWER(proj4text) LIKE LOWER(%s)
                OR CAST(srid AS TEXT) LIKE %s
                OR CAST(auth_srid AS TEXT) LIKE %s
            )
            """
            keyword_conditions.append(keyword_condition)
            
            # 添加参数（每个关键词需要4个参数）
            search_pattern = f'%{kw}%'
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        # 使用AND连接所有关键词条件
        where_clause = " AND ".join(keyword_conditions)
        
        search_sql = f"""
        SELECT 
            srid,
            auth_name,
            auth_srid,
            srtext,
            proj4text
        FROM spatial_ref_sys 
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN CAST(srid AS TEXT) = %s THEN 1
                WHEN CAST(auth_srid AS TEXT) = %s THEN 2
                WHEN LOWER(srtext) LIKE LOWER(%s) THEN 3
                ELSE 4
            END,
            srid
        LIMIT %s
        """
        
        # 添加排序和限制参数
        # 使用第一个关键词进行排序优先级判断
        first_keyword = keywords[0]
        params.extend([first_keyword, first_keyword, f'%{first_keyword}%', limit])
        
        # 执行查询
        results = execute_query(search_sql, params)
        
        # 处理结果，提取有用信息
        coordinate_systems = []
        for row in results:
            # 从srtext中提取坐标系名称
            srtext = row['srtext'] or ''
            name = extract_coordinate_system_name(srtext)
            
            # 构建显示名称
            display_name = f"EPSG:{row['auth_srid']}"
            if name:
                display_name += f" - {name}"
            
            coordinate_systems.append({
                'srid': row['srid'],
                'auth_name': row['auth_name'],
                'auth_srid': row['auth_srid'],
                'epsg_code': f"EPSG:{row['auth_srid']}",
                'name': name,
                'display_name': display_name,
                'srtext': srtext,
                'proj4text': row['proj4text']
            })
        
        return jsonify({
            'success': True,
            'coordinate_systems': coordinate_systems,
            'total': len(coordinate_systems),
            'keyword': keyword,
            'keywords': keywords
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"搜索坐标系失败: {str(e)}")
        return jsonify({'error': f'搜索坐标系失败: {str(e)}'}), 500

def extract_coordinate_system_name(srtext):
    """从srtext中提取坐标系名称"""
    try:
        if not srtext:
            return None
            
        # 使用正则表达式提取PROJCS或GEOGCS中的名称
        import re
        
        # 匹配PROJCS["name",...] 或 GEOGCS["name",...]
        pattern = r'(?:PROJCS|GEOGCS)\["([^"]+)"'
        match = re.search(pattern, srtext)
        
        if match:
            name = match.group(1)
            # 清理名称，移除一些常见的后缀
            name = re.sub(r'\s*\(.*?\)\s*$', '', name)  # 移除括号内容
            return name
            
        return None
        
    except Exception:
        return None

@file_bp.route('/coordinate-systems/common', methods=['GET'])
def get_common_coordinate_systems():
    """获取常用坐标系列表"""
    try:
        # 定义常用坐标系的EPSG代码
        common_epsgs = [
            4326,   # WGS 84
            3857,   # Web Mercator
            4490,   # CGCS2000
            4214,   # Beijing 1954
            4610,   # Xian 1980
            2383,   # Xian 1980 / 3-degree Gauss-Kruger CM 114E
            4549,   # CGCS2000 / 3-degree Gauss-Kruger CM 114E
            4548,   # CGCS2000 / 3-degree Gauss-Kruger CM 111E
            4547,   # CGCS2000 / 3-degree Gauss-Kruger CM 108E
            4546,   # CGCS2000 / 3-degree Gauss-Kruger CM 105E
        ]
        
        # 构建查询SQL
        placeholders = ','.join(['%s'] * len(common_epsgs))
        sql = f"""
        SELECT 
            srid,
            auth_name,
            auth_srid,
            srtext,
            proj4text
        FROM spatial_ref_sys 
        WHERE auth_srid IN ({placeholders})
        ORDER BY 
            CASE auth_srid
                WHEN 4326 THEN 1
                WHEN 3857 THEN 2  
                WHEN 4490 THEN 3
                WHEN 4214 THEN 4
                WHEN 4610 THEN 5
                ELSE 6
            END
        """
        
        results = execute_query(sql, common_epsgs)
        
        # 处理结果
        coordinate_systems = []
        for row in results:
            srtext = row['srtext'] or ''
            name = extract_coordinate_system_name(srtext)
            
            display_name = f"EPSG:{row['auth_srid']}"
            if name:
                display_name += f" - {name}"
            
            coordinate_systems.append({
                'srid': row['srid'],
                'auth_name': row['auth_name'],
                'auth_srid': row['auth_srid'],
                'epsg_code': f"EPSG:{row['auth_srid']}",
                'name': name,
                'display_name': display_name,
                'srtext': srtext,
                'proj4text': row['proj4text']
            })
        
        return jsonify({
            'success': True,
            'coordinate_systems': coordinate_systems,
            'total': len(coordinate_systems)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"获取常用坐标系失败: {str(e)}")
        return jsonify({'error': f'获取常用坐标系失败: {str(e)}'}), 500 