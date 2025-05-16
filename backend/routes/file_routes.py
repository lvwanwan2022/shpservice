#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from services.file_service import FileService
from werkzeug.utils import secure_filename
import os

file_bp = Blueprint('file', __name__)
file_service = FileService()

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件
    ---
    tags:
      - 文件管理
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: 要上传的文件
      - name: file_name
        in: formData
        type: string
        required: true
        description: 文件名称
      - name: discipline
        in: formData
        type: string
        required: true
        description: 专业分类
      - name: dimension
        in: formData
        type: string
        required: true
        description: 2D/3D
      - name: is_public
        in: formData
        type: boolean
        required: true
        description: 是否共有(true/false)
      - name: file_type
        in: formData
        type: string
        required: true
        description: 文件类型(shp/dem/dom/dwg/dxf/geojson)
      - name: coordinate_system
        in: formData
        type: string
        required: false
        description: 坐标系统(仅dwg/dxf需要)
      - name: tags
        in: formData
        type: string
        required: false
        description: 文件标签(逗号分隔)
      - name: description
        in: formData
        type: string
        required: false
        description: 文件描述
    responses:
      200:
        description: 文件上传成功
      400:
        description: 上传参数错误
    """
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    try:
        # 从表单获取元数据
        metadata = {
            'file_name': request.form.get('file_name'),
            'discipline': request.form.get('discipline'),
            'dimension': request.form.get('dimension'),
            'is_public': request.form.get('is_public', 'true').lower() == 'true',
            'file_type': request.form.get('file_type'),
            'coordinate_system': request.form.get('coordinate_system'),
            'tags': request.form.get('tags', ''),
            'description': request.form.get('description', ''),
            'user_id': request.form.get('user_id', 1)  # 暂时使用固定用户ID
        }
        
        # 验证必填字段
        required_fields = ['file_name', 'discipline', 'dimension', 'file_type']
        for field in required_fields:
            if not metadata.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 验证DWG/DXF类型必须有坐标系
        if metadata['file_type'].lower() in ['dwg', 'dxf'] and not metadata.get('coordinate_system'):
            return jsonify({'error': 'DWG/DXF文件必须指定坐标系'}), 400
        
        # 保存文件并记录元数据
        file_id, file_data = file_service.save_file(file, metadata)
        
        return jsonify({
            'id': file_id,
            'message': '文件上传成功',
            'file': {
                'id': file_id,
                'file_name': file_data['file_name'],
                'file_size': file_data['file_size'],
                'file_type': file_data['file_type'],
                'upload_date': file_data.get('upload_date', '')
            }
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        current_app.logger.error(f"文件上传错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/list', methods=['GET'])
def list_files():
    """获取文件列表
    ---
    tags:
      - 文件管理
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: 上传人员ID
      - name: discipline
        in: query
        type: string
        required: false
        description: 专业分类
      - name: file_type
        in: query
        type: string
        required: false
        description: 文件类型
      - name: tags
        in: query
        type: string
        required: false
        description: 标签(搜索)
      - name: file_name
        in: query
        type: string
        required: false
        description: 文件名(搜索)
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
        default: 12
        description: 每页大小
    responses:
      200:
        description: 文件列表
    """
    try:
        # 从查询参数获取过滤条件
        filters = {}
        
        if request.args.get('user_id'):
            filters['user_id'] = int(request.args.get('user_id'))
        
        if request.args.get('discipline'):
            filters['discipline'] = request.args.get('discipline')
        
        if request.args.get('file_type'):
            filters['file_type'] = request.args.get('file_type')
        
        if request.args.get('tags'):
            filters['tags'] = request.args.get('tags')
        
        if request.args.get('file_name'):
            filters['file_name'] = request.args.get('file_name')
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 12))
        
        # 获取文件列表
        files, total = file_service.get_files(filters, page, page_size)
        
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
    """获取文件详情
    ---
    tags:
      - 文件管理
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: 文件ID
    responses:
      200:
        description: 文件详情
      404:
        description: 文件不存在
    """
    try:
        file_info = file_service.get_file_by_id(file_id)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        return jsonify(file_info), 200
    
    except Exception as e:
        current_app.logger.error(f"获取文件详情错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@file_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件
    ---
    tags:
      - 文件管理
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: 文件ID
    responses:
      200:
        description: 文件删除成功
      404:
        description: 文件不存在
    """
    try:
        file_service.delete_file(file_id)
        return jsonify({'message': '文件删除成功'}), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        current_app.logger.error(f"删除文件错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500 