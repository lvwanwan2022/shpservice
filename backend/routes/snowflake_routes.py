#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
雪花算法ID生成测试路由
"""

from flask import Blueprint, jsonify, request
from services.snowflake_example_service import SnowflakeExampleService

snowflake_bp = Blueprint('snowflake', __name__)
snowflake_service = SnowflakeExampleService()

@snowflake_bp.route('/generate', methods=['GET'])
def generate_id():
    """生成一个雪花算法ID"""
    table_name = request.args.get('table')
    snowflake_id = snowflake_service.generate_id(table_name)
    return jsonify({
        'id': snowflake_id,
        'info': snowflake_service.get_id_info(snowflake_id)
    })

@snowflake_bp.route('/batch', methods=['GET'])
def batch_generate():
    """批量生成雪花算法ID"""
    count = request.args.get('count', 10, type=int)
    if count > 100:
        count = 100  # 限制最大数量
    
    ids = snowflake_service.batch_generate_ids(count)
    return jsonify({
        'count': len(ids),
        'ids': ids
    })

@snowflake_bp.route('/info/<int:snowflake_id>', methods=['GET'])
def get_id_info(snowflake_id):
    """获取雪花算法ID的信息"""
    return jsonify(snowflake_service.get_id_info(snowflake_id))

@snowflake_bp.route('/example', methods=['POST'])
def create_example():
    """创建一条示例记录"""
    data = request.json
    if not data:
        return jsonify({'error': '未提供数据'}), 400
    
    table_name = data.pop('table_name', None)
    if not table_name:
        return jsonify({'error': '未提供表名'}), 400
    
    try:
        record_id = snowflake_service.create_example_record(table_name, data)
        return jsonify({
            'success': True,
            'id': record_id,
            'info': snowflake_service.get_id_info(record_id)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 