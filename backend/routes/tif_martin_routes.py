#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TIF Martin 瓦片服务相关 API 路由 - 简化版本
将TIF文件转换为MBTiles并发布为Martin服务，支持实时进度反馈
"""

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
import logging
from services.tif_martin_service import TifMartinService
from services.file_service import FileService
from auth.auth_service import require_auth, get_current_user
import threading

logger = logging.getLogger(__name__)

# 创建蓝图
tif_martin_bp = Blueprint('tif_martin', __name__, url_prefix='/api/tif-martin')

# 创建服务实例
tif_martin_service = TifMartinService()
file_service = FileService()

@tif_martin_bp.route('/convert-and-publish/<string:file_id>', methods=['POST'])
@require_auth
def convert_tif_and_publish_martin(file_id):
    """将已上传的TIF文件转换为MBTiles并发布为Martin服务"""
    try:
        print(f"\n=== TIF转MBTiles并发布Martin服务请求 ===")
        print(f"文件ID: {file_id}")
        
        # 转换文件ID
        try:
            if isinstance(file_id, str) and file_id.isdigit():
                file_id_int = int(file_id)
            else:
                file_id_int = file_id
        except (ValueError, TypeError):
            return jsonify({'error': '无效的文件ID格式'}), 400
        
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id_int)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型
        file_type = file_info.get('file_type', '').lower()
        if file_type not in ['tif', 'tiff', 'dem.tif', 'dom.tif']:
            return jsonify({'error': '只支持TIF/TIFF文件'}), 400
        
        # 检查文件是否已经转换过
        from models.db import execute_query
        check_sql = """
        SELECT id, service_url FROM vector_martin_services 
        WHERE file_id = %s AND vector_type IN ('raster', 'raster_mbtiles') AND status = 'active'
        """
        existing = execute_query(check_sql, (str(file_id_int),))
        if existing:
            return jsonify({
                'error': 'TIF文件已转换并发布为Martin服务',
                'existing_service': {
                    'service_id': existing[0]['id'],
                    'service_url': existing[0]['service_url']
                }
            }), 400
        
        # 获取请求参数
        data = request.get_json() or {}
        max_zoom = data.get('max_zoom', 18)
        min_zoom = data.get('min_zoom', 2)
        
        # 验证缩放级别参数
        if not isinstance(max_zoom, int) or max_zoom < 1 or max_zoom > 25:
            return jsonify({'error': 'max_zoom必须是1-25之间的整数'}), 400
        
        if not isinstance(min_zoom, int) or min_zoom < 0 or min_zoom >= max_zoom:
            return jsonify({'error': 'min_zoom必须是0到max_zoom-1之间的整数'}), 400
        
        # 获取当前用户信息
        current_user = get_current_user()
        user_id = current_user.get('id', current_user.get('username', 'unknown'))
        
        print(f"开始转换TIF文件: {file_info['file_name']}")
        print(f"文件路径: {file_info['file_path']}")
        print(f"缩放级别: {min_zoom}-{max_zoom}")
        print(f"用户ID: {user_id}")
        
        # 启动异步转换任务
        def async_convert():
            tif_martin_service.tif_to_mbtiles_and_publish(
                file_id=str(file_id_int),
                file_path=file_info['file_path'],
                original_filename=file_info['file_name'],
                user_id=user_id,
                max_zoom=max_zoom,
                min_zoom=min_zoom
            )
        
        # 先同步启动以获取task_id
        result = tif_martin_service.tif_to_mbtiles_and_publish(
            file_id=str(file_id_int),
            file_path=file_info['file_path'],
            original_filename=file_info['file_name'],
            user_id=user_id,
            max_zoom=max_zoom,
            min_zoom=min_zoom
        )
        
        if result['success']:
            print(f"✅ TIF转MBTiles并发布成功")
            
            return jsonify({
                'success': True,
                'message': 'TIF文件成功转换为MBTiles并发布为Martin服务',
                'data': {
                    'task_id': result['task_id'],
                    'original_file': {
                        'id': str(file_id_int),
                        'name': file_info['file_name'],
                        'type': file_info['file_type']
                    },
                    'conversion': {
                        'mbtiles_filename': result['mbtiles_filename'],
                        'min_zoom': min_zoom,
                        'max_zoom': max_zoom,
                        'coordinate_system': result['coordinate_system']
                    },
                    'martin_service': result['martin_service']
                }
            }), 200
        else:
            print(f"❌ TIF转MBTiles并发布失败: {result['error']}")
            return jsonify({
                'error': f'TIF转MBTiles并发布失败: {result["error"]}',
                'task_id': result.get('task_id')
            }), 500
        
    except Exception as e:
        logger.error(f"TIF转MBTiles并发布服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务内部错误: {str(e)}'}), 500

@tif_martin_bp.route('/convert-async/<string:file_id>', methods=['POST'])
@require_auth
def convert_tif_async(file_id):
    """异步转换TIF文件，立即返回task_id用于进度查询"""
    try:
        print(f"\n=== 异步TIF转换请求 ===")
        print(f"文件ID: {file_id}")
        
        # 转换文件ID
        try:
            if isinstance(file_id, str) and file_id.isdigit():
                file_id_int = int(file_id)
            else:
                file_id_int = file_id
        except (ValueError, TypeError):
            return jsonify({'error': '无效的文件ID格式'}), 400
        
        # 检查文件是否存在
        file_info = file_service.get_file_by_id(file_id_int)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 检查文件类型
        file_type = file_info.get('file_type', '').lower()
        if file_type not in ['tif', 'tiff', 'dem.tif', 'dom.tif']:
            return jsonify({'error': '只支持TIF/TIFF文件'}), 400
        
        # 获取请求参数
        data = request.get_json() or {}
        max_zoom = data.get('max_zoom', 18)
        min_zoom = data.get('min_zoom', 2)
        
        # 验证缩放级别参数
        if not isinstance(max_zoom, int) or max_zoom < 1 or max_zoom > 25:
            return jsonify({'error': 'max_zoom必须是1-25之间的整数'}), 400
        
        if not isinstance(min_zoom, int) or min_zoom < 0 or min_zoom >= max_zoom:
            return jsonify({'error': 'min_zoom必须是0到max_zoom-1之间的整数'}), 400
        
        # 获取当前用户信息
        current_user = get_current_user()
        user_id = current_user.get('id', current_user.get('username', 'unknown'))
        
        # 生成task_id并初始化进度
        import uuid
        task_id = str(uuid.uuid4())
        tif_martin_service.progress_data[task_id] = {
            'status': 'queued',
            'progress': 0,
            'message': '任务已排队...',
            'current_step': 'queued'
        }
        
        # 启动异步转换任务
        def async_convert():
            try:
                result = tif_martin_service.tif_to_mbtiles_and_publish(
                    file_id=str(file_id_int),
                    file_path=file_info['file_path'],
                    original_filename=file_info['file_name'],
                    user_id=user_id,
                    max_zoom=max_zoom,
                    min_zoom=min_zoom
                )
                
                # 更新最终结果到进度数据中
                if task_id in tif_martin_service.progress_data:
                    tif_martin_service.progress_data[task_id]['result'] = result
                    
            except Exception as e:
                if task_id in tif_martin_service.progress_data:
                    tif_martin_service.progress_data[task_id].update({
                        'status': 'error',
                        'message': f'异步处理失败: {str(e)}',
                        'current_step': 'error'
                    })
        
        # 启动后台线程
        thread = threading.Thread(target=async_convert)
        thread.daemon = True
        thread.start()
        
        print(f"✅ 异步转换任务已启动，task_id: {task_id}")
        
        return jsonify({
            'success': True,
            'message': '异步转换任务已启动',
            'task_id': task_id,
            'file_info': {
                'id': str(file_id_int),
                'name': file_info['file_name'],
                'type': file_info['file_type']
            },
            'conversion_params': {
                'min_zoom': min_zoom,
                'max_zoom': max_zoom
            }
        }), 200
        
    except Exception as e:
        logger.error(f"异步TIF转换启动失败: {str(e)}")
        return jsonify({'error': f'启动异步任务失败: {str(e)}'}), 500

@tif_martin_bp.route('/progress/<string:task_id>', methods=['GET'])
@require_auth
def get_conversion_progress(task_id):
    """获取转换任务的实时进度"""
    try:
        progress = tif_martin_service.get_progress(task_id)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'progress': progress
        }), 200
        
    except Exception as e:
        logger.error(f"获取转换进度失败: {str(e)}")
        return jsonify({'error': f'获取进度失败: {str(e)}'}), 500

@tif_martin_bp.route('/batch-convert', methods=['POST'])
@require_auth
def batch_convert_tif_files():
    """批量转换多个TIF文件为MBTiles并发布为Martin服务"""
    try:
        print(f"\n=== 批量TIF转MBTiles请求 ===")
        
        data = request.get_json() or {}
        file_ids = data.get('file_ids', [])
        max_zoom = data.get('max_zoom', 18)
        min_zoom = data.get('min_zoom', 2)
        
        if not file_ids or not isinstance(file_ids, list):
            return jsonify({'error': '请提供有效的文件ID列表'}), 400
        
        if len(file_ids) > 5:  # 限制批量处理数量
            return jsonify({'error': '批量处理最多支持5个文件'}), 400
        
        # 验证缩放级别参数
        if not isinstance(max_zoom, int) or max_zoom < 1 or max_zoom > 25:
            return jsonify({'error': 'max_zoom必须是1-25之间的整数'}), 400
        
        if not isinstance(min_zoom, int) or min_zoom < 0 or min_zoom >= max_zoom:
            return jsonify({'error': 'min_zoom必须是0到max_zoom-1之间的整数'}), 400
        
        # 获取当前用户信息
        current_user = get_current_user()
        user_id = current_user.get('id', current_user.get('username', 'unknown'))
        
        print(f"批量处理 {len(file_ids)} 个文件，缩放级别: {min_zoom}-{max_zoom}")
        
        batch_results = []
        
        for file_id in file_ids:
            try:
                # 转换文件ID
                if isinstance(file_id, str) and file_id.isdigit():
                    file_id_int = int(file_id)
                else:
                    file_id_int = file_id
                
                # 检查文件
                file_info = file_service.get_file_by_id(file_id_int)
                if not file_info:
                    batch_results.append({
                        'file_id': str(file_id),
                        'success': False,
                        'error': '文件不存在'
                    })
                    continue
                
                # 检查文件类型
                file_type = file_info.get('file_type', '').lower()
                if file_type not in ['tif', 'tiff', 'dem.tif', 'dom.tif']:
                    batch_results.append({
                        'file_id': str(file_id),
                        'file_name': file_info['file_name'],
                        'success': False,
                        'error': '不是TIF文件'
                    })
                    continue
                
                print(f"处理文件: {file_info['file_name']}")
                
                # 执行转换
                result = tif_martin_service.tif_to_mbtiles_and_publish(
                    file_id=str(file_id_int),
                    file_path=file_info['file_path'],
                    original_filename=file_info['file_name'],
                    user_id=user_id,
                    max_zoom=max_zoom,
                    min_zoom=min_zoom
                )
                
                if result['success']:
                    batch_results.append({
                        'file_id': str(file_id_int),
                        'file_name': file_info['file_name'],
                        'success': True,
                        'task_id': result['task_id'],
                        'mbtiles_filename': result['mbtiles_filename'],
                        'martin_service': result['martin_service']
                    })
                    print(f"✅ {file_info['file_name']} 转换成功")
                else:
                    batch_results.append({
                        'file_id': str(file_id_int),
                        'file_name': file_info['file_name'],
                        'success': False,
                        'error': result['error'],
                        'task_id': result.get('task_id')
                    })
                    print(f"❌ {file_info['file_name']} 转换失败: {result['error']}")
                
            except Exception as e:
                batch_results.append({
                    'file_id': str(file_id),
                    'success': False,
                    'error': f'处理异常: {str(e)}'
                })
                print(f"❌ 文件 {file_id} 处理异常: {str(e)}")
        
        # 统计结果
        success_count = sum(1 for r in batch_results if r['success'])
        error_count = len(batch_results) - success_count
        
        print(f"批量处理完成: 成功 {success_count} 个, 失败 {error_count} 个")
        
        return jsonify({
            'success': True,
            'message': f'批量处理完成: 成功 {success_count} 个, 失败 {error_count} 个',
            'summary': {
                'total': len(file_ids),
                'success_count': success_count,
                'error_count': error_count,
                'min_zoom': min_zoom,
                'max_zoom': max_zoom
            },
            'results': batch_results
        }), 200
        
    except Exception as e:
        logger.error(f"批量TIF转MBTiles失败: {str(e)}")
        return jsonify({'error': f'批量处理失败: {str(e)}'}), 500

@tif_martin_bp.route('/conversion-status/<string:file_id>', methods=['GET'])
@require_auth
def get_conversion_status(file_id):
    """获取TIF文件的转换状态"""
    try:
        # 转换文件ID
        try:
            if isinstance(file_id, str) and file_id.isdigit():
                file_id_int = int(file_id)
            else:
                file_id_int = file_id
        except (ValueError, TypeError):
            return jsonify({'error': '无效的文件ID格式'}), 400
        
        # 检查原始文件
        file_info = file_service.get_file_by_id(file_id_int)
        if not file_info:
            return jsonify({'error': '文件不存在'}), 404
        
        # 查找相关的MBTiles服务
        from models.db import execute_query
        service_sql = """
        SELECT id, service_url, mvt_url, tilejson_url, created_at, vector_type
        FROM vector_martin_services 
        WHERE file_id = %s AND vector_type IN ('raster', 'raster_mbtiles') AND status = 'active'
        ORDER BY created_at DESC
        """
        services = execute_query(service_sql, (str(file_id_int),))
        
        response = {
            'file_id': str(file_id_int),
            'file_name': file_info['file_name'],
            'file_type': file_info['file_type'],
            'converted': len(services) > 0,
            'services': []
        }
        
        if services:
            for service in services:
                response['services'].append({
                    'service_id': service['id'],
                    'service_url': service['service_url'],
                    'mvt_url': service['mvt_url'],
                    'tilejson_url': service['tilejson_url'],
                    'vector_type': service['vector_type'],
                    'created_at': service['created_at'].isoformat() if service['created_at'] else None
                })
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"获取转换状态失败: {str(e)}")
        return jsonify({'error': f'获取状态失败: {str(e)}'}), 500

@tif_martin_bp.route('/cleanup-progress/<string:task_id>', methods=['DELETE'])
@require_auth
def cleanup_task_progress(task_id):
    """清理任务进度数据"""
    try:
        tif_martin_service.cleanup_progress(task_id)
        return jsonify({
            'success': True,
            'message': '进度数据已清理'
        }), 200
        
    except Exception as e:
        logger.error(f"清理进度数据失败: {str(e)}")
        return jsonify({'error': f'清理失败: {str(e)}'}), 500

# 错误处理器
@tif_martin_bp.errorhandler(413)
def too_large(e):
    """文件太大的错误处理"""
    return jsonify({'error': '文件太大，请选择更小的文件'}), 413

@tif_martin_bp.errorhandler(500)
def internal_error(e):
    """内部服务器错误处理"""
    logger.error(f"TIF Martin服务内部错误: {str(e)}")
    return jsonify({'error': '服务器内部错误，请稍后重试'}), 500