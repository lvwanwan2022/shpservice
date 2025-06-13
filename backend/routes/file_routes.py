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

@file_bp.route('/<int:file_id>/publish/martin-mbtiles', methods=['POST'])
def publish_martin_mbtiles_service(file_id):
    """发布MBTiles文件到Martin服务"""
    try:
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型是否支持Martin服务
        file_type = file_info.get('file_type', '').lower()
        if file_type not in ['geojson', 'shp', 'dxf', 'mbtiles', 'vector.mbtiles', 'raster.mbtiles']:
            return jsonify({'error': 'Martin服务仅支持GeoJSON、SHP、DXF和MBTiles文件'}), 400
        
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
        
        elif file_type in ['mbtiles', 'vector.mbtiles', 'raster.mbtiles']:
            # 使用栅格Martin服务发布MBTiles文件
            from services.raster_martin_service import RasterMartinService
            raster_martin_service = RasterMartinService()
            
            # 确定MBTiles类型
            mbtiles_type = 'vector' if file_type == 'vector.mbtiles' else 'raster.mbtiles'
            
            result = raster_martin_service.publish_mbtiles_martin(
                file_id=str(file_id),
                file_path=file_info['file_path'],
                original_filename=file_info['file_name'],
                user_id=file_info.get('user_id'),
                mbtiles_type=mbtiles_type
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
    """发布文件到GeoServer服务 - 统一处理矢量和栅格数据"""
    try:
        # 1. 获取文件信息
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        file_type = file_info.get('file_type', '').lower()
        file_path = file_info['file_path']
        
        print(f"=== 开始发布GeoServer服务 ===")
        print(f"文件ID: {file_id}, 文件类型: {file_type}")
        print(f"文件路径: {file_path}")
        
        # 2. 检查是否已经发布
        existing_layer_sql = """
        SELECT gl.id, gl.name, gw.name as workspace_name,
               gl.featuretype_id, gl.coverage_id,
               gs.name as store_name, gs.store_type
        FROM geoserver_layers gl
        LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        LEFT JOIN geoserver_featuretypes gft ON gl.featuretype_id = gft.id
        LEFT JOIN geoserver_coverages gcov ON gl.coverage_id = gcov.id
        LEFT JOIN geoserver_stores gs ON (gft.store_id = gs.id OR gcov.store_id = gs.id)
        WHERE gl.file_id = %s
        """
        existing_layers = execute_query(existing_layer_sql, (file_id,))
        
        if existing_layers:
            layer_info = existing_layers[0]
            return jsonify({
                'success': False, 
                'error': f'文件已发布为图层: {layer_info["workspace_name"]}:{layer_info["name"]}',
                'existing_layer': {
                    'id': layer_info['id'],
                    'name': f"{layer_info['workspace_name']}:{layer_info['name']}",
                    'store_name': layer_info['store_name'],
                    'store_type': layer_info['store_type']
                }
            }), 400
        
        # 3. 获取坐标系信息
        coordinate_system = file_info.get('coordinate_system')
        if not coordinate_system and request.is_json:
            data = request.get_json()
            coordinate_system = data.get('coordinate_system')
        elif not coordinate_system and request.form:
            coordinate_system = request.form.get('coordinate_system')
        
        if coordinate_system:
            print(f"使用坐标系: {coordinate_system}")
        
        # 4. 检查文件类型支持
        vector_types = ['shp', 'geojson']
        raster_types = ['tif', 'tiff', 'dem', 'dom', 'dem.tif', 'dom.tif']
        
        if file_type not in vector_types + raster_types:
            return jsonify({
                'success': False, 
                'error': f'不支持的文件类型: {file_type}。支持的类型: {", ".join(vector_types + raster_types)}'
            }), 400
        
        # 5. 生成存储名称
        store_name = f"file_{file_id}"
        
        # 6. 根据文件类型执行发布
        from services.geoserver_service import GeoServerService
        geoserver_service = GeoServerService()
        
        print(f"开始发布到GeoServer，存储名称: {store_name}")
        
        if file_type in vector_types:
            print(f"发布矢量数据: {file_type}")
            # 矢量数据发布
            if file_type == 'shp':
                result = geoserver_service.publish_shapefile(file_path, store_name, file_id)
            elif file_type == 'geojson':
                result = geoserver_service.publish_geojson(file_path, store_name, file_id)
        else:
            print(f"发布栅格数据: {file_type}")
            # 栅格数据发布
            
            # 检查是否启用透明度（从请求参数获取，默认不启用）
            enable_transparency = False
            if file_type== 'dom.tif':                
                enable_transparency = True            
            
            print(f"透明度设置: {enable_transparency}")
            
            # 如果是DOM文件，使用增强版的处理逻辑
            is_dom_file = file_type.lower() in ['dom', 'dom.tif'] or 'dom' in file_info.get('file_name', '').lower()
            
            if is_dom_file or file_type.lower() in ['tif', 'tiff']:
                print(f"检测到DOM/TIF文件，使用增强版发布流程")
                
                # 获取强制设置的坐标系
                force_epsg = None
                if coordinate_system:
                    force_epsg = coordinate_system
                elif request.is_json:
                    data = request.get_json()
                    force_epsg = data.get('force_epsg')
                elif request.form:
                    force_epsg = request.form.get('force_epsg')
                
                # 验证坐标系格式
                if force_epsg and not force_epsg.upper().startswith('EPSG:'):
                    return jsonify({
                        'success': False, 
                        'error': f'坐标系格式错误，应为EPSG:xxxx格式，当前为: {force_epsg}'
                    }), 400
                
                if force_epsg:
                    print(f"使用强制坐标系: {force_epsg}")
                
                # 使用增强版DOM.tif发布方法
                result = geoserver_service.publish_dom_geotiff(
                    tif_path=file_path,
                    store_name=store_name,
                    file_id=file_id,
                    force_epsg=force_epsg
                )
            else:
                # 其他栅格数据使用原有方法
                if coordinate_system:
                    # 验证坐标系格式
                    if not coordinate_system.upper().startswith('EPSG:'):
                        return jsonify({
                            'success': False, 
                            'error': f'坐标系格式错误，应为EPSG:xxxx格式，当前为: {coordinate_system}'
                        }), 400
                    
                    result = geoserver_service.publish_geotiff(file_path, store_name, file_id, coordinate_system, enable_transparency)
                else:
                    result = geoserver_service.publish_geotiff(file_path, store_name, file_id, None, enable_transparency)
        
        print(f"GeoServer发布结果: {result}")
        return jsonify(result)
            
    except Exception as e:
        print(f"发布GeoServer服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'发布失败: {str(e)}'}), 500

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
        elif vector_type == 'mbtiles':
            # 使用栅格Martin服务删除MBTiles服务
            from services.raster_martin_service import RasterMartinService
            raster_martin_service = RasterMartinService()
            success = raster_martin_service.delete_martin_service(service_id)
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

@file_bp.route('/<int:file_id>/publish/dom', methods=['POST'])
def publish_dom_geoserver_service(file_id):
    """发布DOM.tif文件到GeoServer服务 - 专门处理DOM.tif文件
    
    功能特点：
    1. 使用gdalinfo检查文件坐标系信息
    2. 如果坐标系不是标准EPSG，使用gdal_translate设置坐标系
    3. 使用标准GeoTIFF方式发布（不使用ImageMosaic）
    4. 自动设置黑色背景为透明（Input Transparent Color: 000000）
    
    参数:
    - force_epsg: 强制设置的EPSG坐标系，如'EPSG:2343'（可选）
    
    返回:
    - 成功: {'success': True, 'layer_name': '图层名称', 'wms_url': 'WMS服务地址', ...}
    - 失败: {'success': False, 'error': '错误信息'}
    """
    try:
        # 1. 获取文件信息
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        file_type = file_info.get('file_type', '').lower()
        file_path = file_info['file_path']
        file_name = file_info['file_name']
        
        print(f"=== 开始发布DOM.tif文件到GeoServer ===")
        print(f"文件ID: {file_id}, 文件类型: {file_type}")
        print(f"文件路径: {file_path}")
        print(f"文件名称: {file_name}")
        
        # 2. 检查文件类型
        dom_types = ['tif', 'tiff', 'dom', 'dem', 'dom.tif', 'dem.tif']
        if file_type not in dom_types:
            return jsonify({
                'success': False, 
                'error': f'不支持的文件类型: {file_type}。该接口仅支持DOM/TIF类型: {", ".join(dom_types)}'
            }), 400
        
        # 3. 检查是否已经发布
        existing_layer_sql = """
        SELECT gl.id, gl.name, gw.name as workspace_name,
               gl.featuretype_id, gl.coverage_id,
               gs.name as store_name, gs.store_type
        FROM geoserver_layers gl
        LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        LEFT JOIN geoserver_featuretypes gft ON gl.featuretype_id = gft.id
        LEFT JOIN geoserver_coverages gcov ON gl.coverage_id = gcov.id
        LEFT JOIN geoserver_stores gs ON (gft.store_id = gs.id OR gcov.store_id = gs.id)
        WHERE gl.file_id = %s
        """
        existing_layers = execute_query(existing_layer_sql, (file_id,))
        
        if existing_layers:
            layer_info = existing_layers[0]
            # 如果请求参数包含force=true，则删除现有发布后重新发布
            force_republish = False
            if request.is_json:
                data = request.get_json()
                force_republish = data.get('force', False)
            elif request.form:
                force_republish = request.form.get('force', 'false').lower() in ['true', '1', 'yes']
            
            if not force_republish:
                return jsonify({
                    'success': False, 
                    'error': f'文件已发布为图层: {layer_info["workspace_name"]}:{layer_info["name"]}',
                    'existing_layer': {
                        'id': layer_info['id'],
                        'name': f"{layer_info['workspace_name']}:{layer_info['name']}",
                        'store_name': layer_info['store_name'],
                        'store_type': layer_info['store_type']
                    }
                }), 400
            else:
                print(f"强制重新发布：删除现有图层 {layer_info['id']}")
                from services.geoserver_service import GeoServerService
                geoserver_service = GeoServerService()
                # 删除现有图层
                geoserver_service.unpublish_layer(layer_info['id'])
                print(f"✅ 现有图层删除成功")
        
        # 4. 获取强制设置的坐标系信息
        force_epsg = None
        if request.is_json:
            data = request.get_json()
            force_epsg = data.get('force_epsg')
        elif request.form:
            force_epsg = request.form.get('force_epsg')
        
        if force_epsg:
            # 验证坐标系格式
            if not force_epsg.upper().startswith('EPSG:'):
                return jsonify({
                    'success': False, 
                    'error': f'坐标系格式错误，应为EPSG:xxxx格式，当前为: {force_epsg}'
                }), 400
            print(f"强制设置坐标系: {force_epsg}")
        
        # 5. 生成存储名称
        store_name = f"dom_{file_id}"
        
        # 6. 使用专门的DOM.tif发布方法
        from services.geoserver_service import GeoServerService
        geoserver_service = GeoServerService()
        
        print(f"开始使用DOM.tif专用方法发布到GeoServer，存储名称: {store_name}")
        result = geoserver_service.publish_dom_geotiff(
            tif_path=file_path,
            store_name=store_name,
            file_id=file_id,
            force_epsg=force_epsg
        )
        
        print(f"DOM.tif发布结果: {result}")
        return jsonify(result)
            
    except Exception as e:
        print(f"发布DOM.tif到GeoServer失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'发布失败: {str(e)}'}), 500

@file_bp.route('/<int:file_id>/unpublish/geoserver', methods=['DELETE'])
def unpublish_geoserver_service(file_id):
    """取消发布GeoServer服务 - 统一处理矢量和栅格数据"""
    try:
        print(f"=== 开始取消发布GeoServer服务 ===")
        print(f"文件ID: {file_id}")
        
        # 1. 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        file_type = file_info.get('file_type', '').lower()
        print(f"文件类型: {file_type}")
        
        # 2. 查找发布的图层信息
        layer_query_sql = """
        SELECT gl.id as layer_id, gl.name as layer_name, 
               gw.name as workspace_name,
               gl.featuretype_id, gl.coverage_id,
               gs.id as store_id, gs.name as store_name, gs.store_type,
               gft.id as featuretype_id_detail,
               gcov.id as coverage_id_detail
        FROM geoserver_layers gl
        LEFT JOIN geoserver_workspaces gw ON gl.workspace_id = gw.id
        LEFT JOIN geoserver_featuretypes gft ON gl.featuretype_id = gft.id
        LEFT JOIN geoserver_coverages gcov ON gl.coverage_id = gcov.id
        LEFT JOIN geoserver_stores gs ON (gft.store_id = gs.id OR gcov.store_id = gs.id)
        WHERE gl.file_id = %s
        """
        
        layer_results = execute_query(layer_query_sql, (file_id,))
        if not layer_results:
            return jsonify({'success': False, 'error': '文件未发布到GeoServer服务'}), 404
        
        layer_info = layer_results[0]
        layer_id = layer_info['layer_id']
        layer_name = layer_info['layer_name']
        workspace_name = layer_info['workspace_name']
        store_name = layer_info['store_name']
        store_type = layer_info['store_type']
        
        print(f"找到已发布图层: {workspace_name}:{layer_name}")
        print(f"存储信息: {store_name} (类型: {store_type})")
        
        # 3. 判断是矢量还是栅格数据
        is_raster = layer_info['coverage_id'] is not None
        is_vector = layer_info['featuretype_id'] is not None
        
        print(f"数据类型: {'栅格' if is_raster else '矢量' if is_vector else '未知'}")
        
        # 4. 从GeoServer删除服务
        from services.geoserver_service import GeoServerService
        geoserver_service = GeoServerService()
        
        print(f"--- 开始从GeoServer删除服务 ---")
        
        try:
            if is_raster:
                print(f"删除栅格数据存储: {store_name}")
                # 使用增强的coveragestore清理方法
                geoserver_service._cleanup_existing_coveragestore(store_name)
            else:
                print(f"删除矢量数据存储: {store_name}")
                # 删除datastore
                geoserver_service._cleanup_existing_datastore(store_name)
                
            print(f"✅ GeoServer服务删除完成")
        except Exception as geoserver_error:
            print(f"⚠️ GeoServer删除失败: {str(geoserver_error)}")
            # 继续执行数据库清理，不阻断流程
        
        # 5. 清理数据库记录
        print(f"--- 开始清理数据库记录 ---")
        
        try:
            # 5.1 删除图层记录
            delete_layer_sql = "DELETE FROM geoserver_layers WHERE id = %s"
            affected_rows = execute_query(delete_layer_sql, (layer_id,), fetch=False)
            print(f"✅ 删除图层记录: layer_id={layer_id} (影响行数: {affected_rows})")
            
            # 5.2 删除关联的featuretype或coverage记录
            if layer_info['featuretype_id']:
                delete_featuretype_sql = "DELETE FROM geoserver_featuretypes WHERE id = %s"
                affected_rows = execute_query(delete_featuretype_sql, (layer_info['featuretype_id'],), fetch=False)
                print(f"✅ 删除featuretype记录: featuretype_id={layer_info['featuretype_id']} (影响行数: {affected_rows})")
            
            if layer_info['coverage_id']:
                delete_coverage_sql = "DELETE FROM geoserver_coverages WHERE id = %s"
                affected_rows = execute_query(delete_coverage_sql, (layer_info['coverage_id'],), fetch=False)
                print(f"✅ 删除coverage记录: coverage_id={layer_info['coverage_id']} (影响行数: {affected_rows})")
            
            # 5.3 检查存储是否还被其他图层使用
            if layer_info['store_id']:
                check_store_usage_sql = """
                SELECT COUNT(*) as count FROM (
                    SELECT 1 FROM geoserver_featuretypes WHERE store_id = %s
                    UNION ALL
                    SELECT 1 FROM geoserver_coverages WHERE store_id = %s
                ) as usage_count
                """
                usage_result = execute_query(check_store_usage_sql, (layer_info['store_id'], layer_info['store_id']))
                usage_count = usage_result[0]['count']
                
                if usage_count == 0:
                    # 没有其他图层使用此存储，删除存储记录
                    delete_store_sql = "DELETE FROM geoserver_stores WHERE id = %s"
                    affected_rows = execute_query(delete_store_sql, (layer_info['store_id'],), fetch=False)
                    print(f"✅ 删除存储记录: store_id={layer_info['store_id']} (影响行数: {affected_rows})")
                else:
                    print(f"⚠️ 存储 {store_name} 仍被其他 {usage_count} 个图层/覆盖使用，保留存储记录")
            
            print(f"✅ 数据库记录清理完成")
            
        except Exception as db_error:
            print(f"❌ 数据库记录清理失败: {str(db_error)}")
            return jsonify({'success': False, 'error': f'数据库清理失败: {str(db_error)}'}), 500
        
        print(f"=== 取消发布GeoServer服务完成 ===")
        
        # 6. 自动重置GeoServer缓存以释放文件锁定
        try:
            print(f"--- 自动重置GeoServer缓存 ---")
            reset_result = geoserver_service.reset_geoserver_caches()
            print(f"缓存重置结果: {reset_result}")
        except Exception as cache_error:
            print(f"⚠️ 缓存重置失败: {str(cache_error)}")
            # 不影响主流程继续
        
        return jsonify({
            'success': True,
            'message': 'GeoServer服务取消发布成功，已自动重置缓存',
            'deleted_layer': f"{workspace_name}:{layer_name}",
            'store_info': {
                'name': store_name,
                'type': store_type,
                'data_type': '栅格' if is_raster else '矢量'
            },
            'cleanup_info': {
                'cache_reset': True,
                'recommendations': [
                    '如果GeoServer数据目录中仍有相关文件，可调用 /files/{file_id}/force-cleanup 进行强制清理',
                    '如遇文件被占用问题，建议重启GeoServer服务',
                    '可以检查GeoServer日志了解详细信息'
                ]
            }
        }), 200
    
    except Exception as e:
        print(f"❌ 取消发布GeoServer服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'取消发布失败: {str(e)}'}), 500

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

@file_bp.route('/<int:file_id>/force-cleanup', methods=['POST'])
def force_cleanup_geoserver_files(file_id):
    """强制清理GeoServer文件和缓存"""
    try:
        print(f"=== 开始强制清理GeoServer文件 ===")
        print(f"文件ID: {file_id}")
        
        # 1. 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 2. 强制重置GeoServer缓存和连接
        from services.geoserver_service import GeoServerService
        geoserver_service = GeoServerService()
        
        # 3. 调用GeoServer REST API重置所有缓存
        reset_result = geoserver_service.reset_geoserver_caches()
        print(f"GeoServer缓存重置结果: {reset_result}")
        
        # 4. 获取GeoServer数据目录中的相关文件
        cleanup_paths = geoserver_service.get_file_cleanup_paths(file_id)
        
        # 5. 尝试删除文件
        cleanup_results = []
        for file_path in cleanup_paths:
            result = geoserver_service.force_delete_file(file_path)
            cleanup_results.append({
                'path': file_path,
                'success': result['success'],
                'message': result['message']
            })
        
        return jsonify({
            'success': True,
            'message': '强制清理操作完成',
            'reset_result': reset_result,
            'cleanup_results': cleanup_results,
            'recommendations': [
                '如果文件仍被占用，请重启GeoServer服务',
                '可以使用Process Explorer或Resource Monitor查看文件句柄',
                '必要时可以重启整个应用服务器'
            ]
        }), 200
        
    except Exception as e:
        print(f"强制清理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'强制清理失败: {str(e)}'}), 500 