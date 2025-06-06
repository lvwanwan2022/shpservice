#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app
from models.db import get_connection as get_db_connection
import json
import logging

# 创建logger
logger = logging.getLogger(__name__)

gis_bp = Blueprint('gis', __name__)

@gis_bp.route('/layer/<int:layer_id>/crs-info', methods=['GET'])
def get_layer_crs_info(layer_id):
    """获取图层的坐标系信息，根据scene_layers表的layer_type路由到对应的服务表获取file_id
    
    Args:
        layer_id: scene_layers表中的layer_id
        
    Returns:
        坐标系信息，包括EPSG代码、proj4定义等
    """
    try:
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 首先从scene_layers表获取layer_type和对应的服务ID
        cursor.execute("""
            SELECT 
                id,
                layer_type,
                layer_id as service_layer_id
            FROM scene_layers
            WHERE layer_id = %s
        """, (layer_id,))
        
        scene_layer_record = cursor.fetchone()
        
        if not scene_layer_record:
            return jsonify({
                "success": False,
                "message": f"未找到ID为{layer_id}的场景图层"
            }), 404
        
        scene_layer_id = scene_layer_record[0]
        layer_type = scene_layer_record[1] or 'geoserver'  # 默认为geoserver
        service_layer_id = scene_layer_record[2]
        
        logger.info(f"场景图层{layer_id}: layer_type={layer_type}, service_layer_id={service_layer_id}")
        
        if not service_layer_id:
            return jsonify({
                "success": False,
                "message": f"场景图层{layer_id}缺少服务图层ID"
            }), 404
        
        file_id = None
        
        # 根据layer_type决定查询哪个表获取file_id
        if layer_type.lower() == 'martin':
            # 从vector_martin_services表获取file_id
            cursor.execute("""
                SELECT file_id, table_name
                FROM vector_martin_services
                WHERE id = %s
            """, (service_layer_id,))
            
            martin_record = cursor.fetchone()
            if martin_record:
                file_id = martin_record[0]
                logger.info(f"从vector_martin_services表获取file_id: {file_id}")
            else:
                logger.warning(f"在vector_martin_services表中未找到ID为{service_layer_id}的记录")
                
        else:  # geoserver或其他类型
            # 从geoserver_layers表获取file_id
            cursor.execute("""
                SELECT file_id, name
                FROM geoserver_layers
                WHERE id = %s
            """, (service_layer_id,))
            
            geoserver_record = cursor.fetchone()
            if geoserver_record:
                file_id = geoserver_record[0]
                logger.info(f"从geoserver_layers表获取file_id: {file_id}")
            else:
                logger.warning(f"在geoserver_layers表中未找到ID为{service_layer_id}的记录")
        
        if not file_id:
            return jsonify({
                "success": False,
                "message": f"无法获取场景图层{layer_id}对应的文件ID，layer_type: {layer_type}, service_layer_id: {service_layer_id}"
            }), 404
        
        # 从files表获取坐标系信息
        cursor.execute("""
            SELECT 
                id,
                file_name,
                coordinate_system,
                file_type,
                original_name
            FROM files
            WHERE id = %s
        """, (file_id,))
        
        file_record = cursor.fetchone()
        
        if not file_record:
            return jsonify({
                "success": False,
                "message": f"未找到ID为{file_id}的文件记录"
            }), 404
        
        # 获取坐标系，如果为空则使用EPSG:4326
        coordinate_system = file_record[2]
        if not coordinate_system or coordinate_system.strip() == '':
            coordinate_system = 'EPSG:4326'
            logger.info(f"文件{file_id}坐标系为空，使用默认值: EPSG:4326")
        else:
            logger.info(f"从files表获取文件{file_id}的坐标系: {coordinate_system}")
        
        # 标准化EPSG代码格式
        epsg_code = coordinate_system
        if coordinate_system and coordinate_system.upper().startswith('EPSG:'):
            try:
                epsg_number = int(coordinate_system.split(':')[1])
                epsg_code = f"EPSG:{epsg_number}"
            except:
                epsg_number = 4326
                epsg_code = 'EPSG:4326'
                logger.warning(f"无法解析坐标系{coordinate_system}，使用默认值EPSG:4326")
        else:
            # 如果不是EPSG格式，尝试解析或使用默认值
            epsg_number = 4326
            epsg_code = 'EPSG:4326'
            logger.warning(f"坐标系格式不标准{coordinate_system}，使用默认值EPSG:4326")
        
        # 从spatial_ref_sys表获取完整的坐标系信息
        cursor.execute("""
            SELECT 
                srid,
                auth_name,
                auth_srid,
                srtext,
                proj4text
            FROM spatial_ref_sys 
            WHERE auth_srid = %s
            LIMIT 1
        """, (epsg_number,))
        
        spatial_ref_record = cursor.fetchone()
        
        if spatial_ref_record:
            srid = spatial_ref_record[0]
            auth_name = spatial_ref_record[1]
            auth_srid = spatial_ref_record[2]
            srtext = spatial_ref_record[3]
            proj4text = spatial_ref_record[4]
            
            # 从srtext中提取坐标系名称
            name = extract_coordinate_system_name(srtext)
            
            logger.info(f"从spatial_ref_sys表获取到坐标系信息: EPSG:{auth_srid}")
        else:
            # 如果spatial_ref_sys表中没有找到，使用默认值
            logger.warning(f"spatial_ref_sys表中未找到EPSG:{epsg_number}，使用默认值")
            srid = epsg_number
            auth_name = 'EPSG'
            auth_srid = epsg_number
            srtext = None
            proj4text = None
            name = f"EPSG:{epsg_number}" if epsg_number != 4326 else "WGS 84"
        
        # 关闭数据库连接
        cursor.close()
        conn.close()
        
        # 构建响应数据
        crs_info = {
            "epsg_code": epsg_code,
            "srid": srid,
            "auth_name": auth_name,
            "auth_srid": auth_srid,
            "name": name,
            "srtext": srtext,
            "proj4_definition": proj4text,
            "is_geographic": epsg_number in [4326, 4490, 4214, 4610],  # 常见的地理坐标系
            "is_projected": epsg_number not in [4326, 4490, 4214, 4610],  # 投影坐标系
            "recommended_wms_version": "1.1.0" if epsg_number not in [4326, 3857] else "1.1.1",
            "source": "files_table",  # 标识数据来源
            "original_coordinate_system": file_record[2],  # 原始坐标系字段值
            "file_id": file_id,  # 实际的文件ID
            "file_name": file_record[1],  # 文件名
            "file_type": file_record[3],  # 文件类型
            "layer_type": layer_type,  # 图层类型
            "service_layer_id": service_layer_id  # 服务图层ID
        }
        
        return jsonify({
            "success": True,
            "crs_info": crs_info,
            "message": f"成功获取场景图层{layer_id}的坐标系信息: {epsg_code} (file_id: {file_id})"
        })
        
    except Exception as e:
        logger.error(f"获取图层坐标系信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取坐标系信息失败: {str(e)}"
        }), 500

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

@gis_bp.route('/coordinate-systems/proj4-definitions', methods=['GET'])
def get_proj4_definitions():
    """获取常用坐标系的proj4定义，用于前端初始化
    
    Returns:
        常用坐标系的proj4定义字典
    """
    try:
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 定义常用坐标系的EPSG代码
        common_epsgs = [
            4326,   # WGS 84
            3857,   # Web Mercator
            4490,   # CGCS2000
            4214,   # Beijing 1954
            4610,   # Xian 1980
            2379,   # Xian 1980 / 3-degree Gauss-Kruger CM 102E
            2343,   # Pulkovo 1942 / 3-degree Gauss-Kruger CM 105E
            2431,   # Beijing 1954 / 3-degree Gauss-Kruger CM 105E
            4545,   # CGCS2000 / 3-degree Gauss-Kruger CM 105E
            4547,   # CGCS2000 / 3-degree Gauss-Kruger CM 102E
        ]
        
        # 查询spatial_ref_sys表获取proj4定义
        placeholders = ','.join(['%s'] * len(common_epsgs))
        sql = f"""
        SELECT 
            auth_srid,
            proj4text,
            srtext
        FROM spatial_ref_sys 
        WHERE auth_srid IN ({placeholders})
        AND proj4text IS NOT NULL
        ORDER BY auth_srid
        """
        
        cursor.execute(sql, common_epsgs)
        results = cursor.fetchall()
        
        # 构建proj4定义字典
        proj4_definitions = {}
        for row in results:
            epsg_code = f"EPSG:{row[0]}"
            proj4_def = row[1]
            srtext = row[2]
            
            # 提取坐标系名称
            name = extract_coordinate_system_name(srtext)
            
            proj4_definitions[epsg_code] = {
                'proj4': proj4_def,
                'name': name,
                'epsg_code': epsg_code,
                'auth_srid': row[0]
            }
        
        # 关闭数据库连接
        cursor.close()
        conn.close()
        
        logger.info(f"获取到{len(proj4_definitions)}个常用坐标系的proj4定义")
        
        return jsonify({
            "success": True,
            "proj4_definitions": proj4_definitions,
            "total": len(proj4_definitions)
        })
        
    except Exception as e:
        logger.error(f"获取proj4定义失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取proj4定义失败: {str(e)}"
        }), 500

@gis_bp.route('/coordinate-systems/<epsg_code>/proj4', methods=['GET'])
def get_single_proj4_definition(epsg_code):
    """获取单个坐标系的proj4定义
    
    Args:
        epsg_code: EPSG代码，如'EPSG:2379'或'2379'
        
    Returns:
        指定坐标系的proj4定义
    """
    try:
        # 解析EPSG代码
        if epsg_code.upper().startswith('EPSG:'):
            epsg_number = int(epsg_code.split(':')[1])
        else:
            epsg_number = int(epsg_code)
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询spatial_ref_sys表
        cursor.execute("""
            SELECT 
                srid,
                auth_name,
                auth_srid,
                srtext,
                proj4text
            FROM spatial_ref_sys 
            WHERE auth_srid = %s
            LIMIT 1
        """, (epsg_number,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"未找到EPSG:{epsg_number}的定义"
            }), 404
        
        # 提取信息
        srid = result[0]
        auth_name = result[1]
        auth_srid = result[2]
        srtext = result[3]
        proj4text = result[4]
        
        # 提取坐标系名称
        name = extract_coordinate_system_name(srtext)
        
        # 关闭数据库连接
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "crs_info": {
                "epsg_code": f"EPSG:{auth_srid}",
                "srid": srid,
                "auth_name": auth_name,
                "auth_srid": auth_srid,
                "name": name,
                "srtext": srtext,
                "proj4_definition": proj4text
            }
        })
        
    except ValueError:
        return jsonify({
            "success": False,
            "message": f"无效的EPSG代码格式: {epsg_code}"
        }), 400
    except Exception as e:
        logger.error(f"获取EPSG:{epsg_code}的proj4定义失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取proj4定义失败: {str(e)}"
        }), 500 