#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DXF到PostGIS直接导入工具
使用ezdxf库解析DXF文件并直接存入PostGIS数据库

主要解决的问题:
1. 解决ogr2ogr处理带中文图层名的DXF文件时编码问题
2. 提供更精确的颜色处理，包括图层颜色和实体颜色
3. 支持不同的DXF实体类型转换为PostGIS几何对象

处理步骤:
1. 使用ezdxf库打开DXF文件并解析内容
2. 提取图层信息和颜色属性
3. 创建PostgreSQL表结构，与ogr2ogr生成的结构兼容
4. 将DXF实体转换为PostGIS几何对象并插入数据库
5. 创建空间索引并更新元数据

使用方法:
1. 作为独立脚本运行: python test_ogr2ogr.py
2. 作为模块导入: 调用dxf_to_postgis函数

日期: 2025-06
"""

import os
import sys
import uuid
import logging
from pathlib import Path
import psycopg2
from psycopg2 import sql
import psycopg2.extras

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入 ezdxf
try:
    import ezdxf
    from ezdxf.math import Vec3
except ImportError:
    logger.error("需要安装 ezdxf 库来解析 DXF 文件。请使用以下命令安装：pip install ezdxf")
    sys.exit(1)

# 尝试导入 shapely (用于生成几何对象)
try:
    from shapely.geometry import Point, LineString, Polygon
    from shapely import wkb
except ImportError:
    logger.error("需要安装 shapely 库来处理几何对象。请使用以下命令安装：pip install shapely")
    sys.exit(1)


# 从配置文件加载DXF颜色映射表
def load_dxf_colors(config_file='dxf_color_index.cfg'):
    """从配置文件加载DXF颜色索引到RGB值的映射"""
    color_map = {}
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
    
    if not os.path.exists(config_path):
        logger.warning(f"警告：颜色配置文件 {config_path} 不存在，使用内置颜色表")
        return ACI_COLORS
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 4:
                    index = int(parts[0])
                    r = int(parts[1])
                    g = int(parts[2])
                    b = int(parts[3])
                    color_map[index] = (r, g, b)
        
        logger.info(f"✅ 成功从 {config_path} 加载了 {len(color_map)} 个颜色定义")
        return color_map
    except Exception as e:
        logger.error(f"❌ 加载颜色配置文件失败: {str(e)}")
        return ACI_COLORS


# 定义自己的颜色字典，不依赖ezdxf的颜色模块
ACI_COLORS = {
    1: (255, 0, 0),       # 红色
    2: (255, 255, 0),     # 黄色
    3: (0, 255, 0),       # 绿色
    4: (0, 255, 255),     # 青色
    5: (0, 0, 255),       # 蓝色
    6: (255, 0, 255),     # 洋红
    7: (255, 255, 255),   # 白色
    8: (128, 128, 128),   # 灰色
    9: (192, 192, 192),   # 浅灰色
    # 更多颜色定义在dxf_color_index.cfg文件中
}


def get_color_name(color_index):
    """
    根据AutoCAD颜色索引(ACI)获取颜色名称
    颜色索引范围是1-255, 其中：
    1=红色, 2=黄色, 3=绿色, 4=青色, 5=蓝色, 6=洋红, 7=白色/黑色
    """
    # 常用颜色映射
    color_map = {
        0: "BYBLOCK",
        1: "红色",
        2: "黄色",
        3: "绿色", 
        4: "青色",
        5: "蓝色",
        6: "洋红",
        7: "白色",
        8: "灰色",
        9: "浅灰色",
        250: "深灰色",
        251: "深中灰",
        252: "中灰",
        253: "浅中灰",
        254: "更浅灰色",
        255: "BYLAYER"
    }
    
    # 返回已知颜色名称或通用描述
    return color_map.get(color_index, f"自定义颜色_{color_index}")


def get_rgb_from_aci(color_index, color_table):
    """
    将AutoCAD颜色索引(ACI)转换为RGB值
    返回格式: '(R,G,B)'字符串
    """
    # 如果是特殊颜色，返回默认值
    if color_index == 0:  # BYBLOCK
        return "(0,0,0)"
    elif color_index == 255:  # BYLAYER
        return "(255,255,255)"
        
    # 尝试从颜色表获取
    rgb = color_table.get(color_index)
    if rgb:
        return f"({rgb[0]},{rgb[1]},{rgb[2]})"
    
    # 如果不在颜色表中，使用一个简单的算法生成颜色
    r = (color_index * 30) % 255
    g = (color_index * 60) % 255
    b = (color_index * 90) % 255
    return f"({r},{g},{b})"


def extract_entity_geometry(entity):
    """
    从DXF实体提取几何信息，转换为Shapely几何对象
    支持点、线、多段线、圆、弧、文本等实体类型
    
    Args:
        entity: DXF实体对象
        
    Returns:
        shapely几何对象或None（如果无法提取几何）
    """
    entity_type = entity.DXFTYPE
    
    try:
        if entity_type == 'POINT':
            point = entity.dxf.location
            return Point(point.x, point.y)
        
        elif entity_type == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            return LineString([(start.x, start.y), (end.x, end.y)])
        
        elif entity_type == 'LWPOLYLINE' or entity_type == 'POLYLINE':
            # 获取多线段的点
            points = []
            if entity_type == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
            else:  # POLYLINE
                points = [(p.dxf.location.x, p.dxf.location.y) for p in entity.vertices]
            
            # 检查是否为闭合多边形
            is_closed = getattr(entity.dxf, 'closed', False)
            
            if len(points) > 1:
                if is_closed and points[0] != points[-1] and len(points) >= 3:
                    # 闭合多边形
                    points.append(points[0])  # 确保首尾相连
                    return Polygon(points)
                else:
                    # 开放线段
                    return LineString(points)
        
        elif entity_type == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            
            # 简化为点 (实际应该创建一个圆多边形，但这里简化处理)
            return Point(center.x, center.y)
        
        elif entity_type == 'ARC':
            # 简化为点 (实际应该创建一个弧线，但这里简化处理)
            center = entity.dxf.center
            return Point(center.x, center.y)
        
        elif entity_type == 'TEXT' or entity_type == 'MTEXT':
            # 文本实体处理为点
            if entity_type == 'TEXT':
                position = entity.dxf.insert
            else:  # MTEXT
                position = entity.dxf.insert
            
            return Point(position.x, position.y)
    
    except Exception as e:
        logger.warning(f"提取几何信息时出错 ({entity_type}): {str(e)}")
    
    return None


def dxf_to_postgis(dxf_file_path, db_config, table_name=None, source_srid=4326, target_srid=3857, batch_size=100):
    """
    将DXF文件直接导入到PostGIS数据库
    
    Args:
        dxf_file_path: DXF文件路径
        db_config: 数据库连接配置字典，包含host, port, dbname, user, password
        table_name: 目标表名（如果为None则自动生成）
        source_srid: 源坐标系SRID
        target_srid: 目标坐标系SRID
        batch_size: 批处理大小
        
    Returns:
        dict: 处理结果，包含成功/失败信息、表名、统计数据等
    """
    if table_name is None:
        table_name = f"vector_dxf_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"=== 开始将DXF文件导入到PostGIS: {table_name} ===")
    logger.info(f"源文件: {dxf_file_path}")
    logger.info(f"坐标系转换: EPSG:{source_srid} → EPSG:{target_srid}")
    
    # 统计变量
    stats = {
        'total_entities': 0,
        'inserted_entities': 0,
        'skipped_entities': 0,
        'layer_stats': {},
        'errors': []
    }
    
    # 检查文件是否存在
    if not os.path.exists(dxf_file_path):
        error_msg = f"错误：DXF文件不存在于路径: {dxf_file_path}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    try:
        # 加载DXF颜色表
        dxf_color_table = load_dxf_colors('dxf_color_index.cfg')
        
        # 尝试不同的编码打开DXF文件
        encodings_to_try = ['gb18030', 'utf-8', 'cp936', 'gbk']
        doc = None
        
        for encoding in encodings_to_try:
            try:
                logger.info(f"尝试使用 {encoding} 编码打开DXF文件...")
                doc = ezdxf.readfile(dxf_file_path, encoding=encoding)
                logger.info(f"✅ 成功使用 {encoding} 编码打开DXF文件")
                break
            except UnicodeDecodeError:
                logger.warning(f"❌ 使用 {encoding} 编码打开失败，尝试下一个编码...")
            except Exception as e:
                logger.warning(f"❌ 使用 {encoding} 编码打开时发生错误: {str(e)}")
        
        if doc is None:
            error_msg = "❌ 无法解析DXF文件，所有编码尝试均失败。"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # 获取图层表和图层颜色信息
        layer_colors = {}
        layer_rgb_colors = {}
        layers = doc.layers
        
        # 正确迭代图层表对象
        for layer in layers:
            layer_name = layer.dxf.name
            # 获取图层颜色
            layer_color = getattr(layer.dxf, 'color', 7)  # 默认为7(白色/黑色)
            layer_colors[layer_name] = layer_color
            # 获取图层RGB颜色
            layer_rgb_colors[layer_name] = get_rgb_from_aci(layer_color, dxf_color_table)
        
        logger.info(f"已加载 {len(layer_colors)} 个图层的颜色信息")
        
        # 连接到PostgreSQL数据库
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        
        # 检查表是否已存在，如果存在则删除
        cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name))
        )
        
        # 创建序列（自增ID）
        cursor.execute(
            sql.SQL("CREATE SEQUENCE {}").format(
                sql.Identifier(f"{table_name}_gid_seq")
            )
        )
        
        # 创建新表，与ogr2ogr导入的表结构兼容
        create_table_sql = sql.SQL("""
        CREATE TABLE {} (
            gid integer NOT NULL DEFAULT nextval({}::regclass),
            cad_layer character varying,
            paperspace boolean,
            subclasses character varying,
            linetype character varying,
            entityhandle character varying,
            text character varying,
            rawcodevalues character varying[],
            color_value integer,            -- 颜色索引值(ACI)
            color_name character varying,   -- 颜色名称
            rgb_color character varying,    -- RGB颜色值字符串 '(R,G,B)'
            lineweight integer,             -- 线宽
            geom geometry(Geometry,{}),
            CONSTRAINT {} PRIMARY KEY (gid)
        )
        """).format(
            sql.Identifier(table_name),
            sql.Literal(f"{table_name}_gid_seq"),
            sql.Literal(target_srid),
            sql.Identifier(f"{table_name}_pkey")
        )
        
        cursor.execute(create_table_sql)
        logger.info("✅ 已成功创建表结构")
        
        # 添加空间索引
        try:
            index_name = f"{table_name}_geom_idx"
            cursor.execute(
                sql.SQL("CREATE INDEX {} ON {} USING GIST (geom)").format(
                    sql.Identifier(index_name),
                    sql.Identifier(table_name)
                )
            )
            logger.info("✅ 已成功创建空间索引")
        except Exception as e:
            error_msg = f"❌ 创建空间索引失败: {str(e)}"
            logger.warning(error_msg)
            stats['errors'].append(error_msg)
            conn.rollback()
            conn.commit()
        
        # 准备插入语句
        insert_sql = sql.SQL("""
        INSERT INTO {} (cad_layer, paperspace, subclasses, linetype, entityhandle, text, rawcodevalues, 
                       color_value, color_name, rgb_color, lineweight, geom)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_Transform(ST_SetSRID(ST_GeomFromWKB(%s), %s), %s))
        """).format(sql.Identifier(table_name))
        
        # 批处理变量
        batch_entities = []
        
        # 处理模型空间中的实体
        msp = doc.modelspace()
        
        for entity in msp:
            stats['total_entities'] += 1
            
            try:
                # 获取实体基本属性
                layer_name = entity.dxf.layer
                entity_type = entity.DXFTYPE
                
                # 更新图层统计
                if layer_name not in stats['layer_stats']:
                    stats['layer_stats'][layer_name] = {'total': 0, 'inserted': 0, 'skipped': 0}
                stats['layer_stats'][layer_name]['total'] += 1
                
                # 提取实体属性
                paperspace = True if entity.dxf.paperspace != 0 else False
                subclasses = getattr(entity, 'subclasses', None)
                linetype = getattr(entity.dxf, 'linetype', None)
                entityhandle = entity.dxf.handle
                text_value = getattr(entity.dxf, 'text', None) if hasattr(entity, 'text') else None
                
                # 提取颜色信息
                color_value = getattr(entity.dxf, 'color', 0)
                true_color = getattr(entity.dxf, 'true_color', 0)
                lineweight = getattr(entity.dxf, 'lineweight', 0)
                
                # 确保颜色值为整数，处理None值
                color_value = 0 if color_value is None else color_value
                true_color = 0 if true_color is None else true_color
                lineweight = 0 if lineweight is None else lineweight
                
                # 初始化RGB颜色值
                if true_color > 0:
                    # 如果实体有真彩色值，优先使用
                    r = (true_color >> 16) & 0xFF
                    g = (true_color >> 8) & 0xFF
                    b = true_color & 0xFF
                    rgb_color = f"({r},{g},{b})"
                elif color_value == 255 or color_value == 0:  # BYLAYER或BYBLOCK
                    # 使用图层的颜色
                    layer_color = layer_colors.get(layer_name, 7)  # 默认为白色
                    color_value = layer_color
                    color_name = get_color_name(layer_color) + " (来自图层)"
                    rgb_color = layer_rgb_colors.get(layer_name, "(255,255,255)")
                else:
                    # 使用颜色索引对应的RGB值
                    color_name = get_color_name(color_value)
                    rgb_color = get_rgb_from_aci(color_value, dxf_color_table)
                
                # 提取颜色和其他DXF代码值作为数组
                raw_code_values = []
                if hasattr(entity.dxf, 'color'):
                    raw_code_values.append(f"62:{entity.dxf.color}")
                if hasattr(entity.dxf, 'true_color'):
                    raw_code_values.append(f"420:{entity.dxf.true_color}")
                if hasattr(entity.dxf, 'lineweight'):
                    raw_code_values.append(f"370:{entity.dxf.lineweight}")
                
                # 提取几何信息
                geometry = extract_entity_geometry(entity)
                
                # 只有有几何的实体才插入
                if geometry is not None:
                    geometry_wkb = wkb.dumps(geometry)
                    
                    # 添加到批处理
                    batch_entities.append((
                        layer_name,                 # 图层名
                        paperspace,                 # 图纸空间（布尔值）
                        subclasses,                 # 子类
                        linetype,                   # 线型
                        entityhandle,               # 实体句柄
                        text_value,                 # 文本内容
                        raw_code_values,            # 原始代码值数组
                        color_value,                # 颜色值
                        color_name,                 # 颜色名称
                        rgb_color,                  # RGB颜色字符串
                        lineweight,                 # 线宽
                        geometry_wkb,               # 几何WKB
                        source_srid,                # 源坐标系SRID
                        target_srid                 # 目标坐标系SRID
                    ))
                    
                    # 如果达到批处理大小，执行批量插入
                    if len(batch_entities) >= batch_size:
                        try:
                            psycopg2.extras.execute_batch(cursor, insert_sql, batch_entities)
                            stats['inserted_entities'] += len(batch_entities)
                            
                            # 更新图层统计
                            for entity_data in batch_entities:
                                entity_layer = entity_data[0]  # layer_name在元组中的索引
                                if entity_layer in stats['layer_stats']:
                                    stats['layer_stats'][entity_layer]['inserted'] += 1
                            
                            # 清空批处理列表
                            batch_entities = []
                            
                            # 提交事务以释放内存
                            conn.commit()
                            if stats['inserted_entities'] % 1000 == 0:
                                logger.info(f"已插入 {stats['inserted_entities']} 个实体...")
                        except Exception as e:
                            error_msg = f"批量插入失败: {str(e)}"
                            logger.warning(error_msg)
                            stats['errors'].append(error_msg)
                            # 回滚并重新开始事务
                            conn.rollback()
                            conn.commit()
                            # 清空批处理列表
                            batch_entities = []
                            # 更新跳过的计数
                            stats['skipped_entities'] += batch_size
                else:
                    stats['skipped_entities'] += 1
                    stats['layer_stats'][layer_name]['skipped'] += 1
                
            except Exception as e:
                error_msg = f"处理实体时出错 ({entity_type}, 图层: {layer_name}): {str(e)}"
                logger.warning(error_msg)
                stats['errors'].append(error_msg)
                stats['skipped_entities'] += 1
                if layer_name in stats['layer_stats']:
                    stats['layer_stats'][layer_name]['skipped'] += 1
                
                # 检查事务状态并尝试恢复
                try:
                    # 查询以检查事务状态
                    cursor.execute("SELECT 1")
                except psycopg2.OperationalError:
                    # 事务已被终止，需要重置连接
                    try:
                        conn.rollback()
                        logger.warning("事务已被终止，正在恢复...")
                    except:
                        # 如果回滚失败，重新连接
                        cursor.close()
                        conn.close()
                        conn = psycopg2.connect(
                            host=db_config['host'],
                            port=db_config['port'],
                            dbname=db_config['dbname'],
                            user=db_config['user'],
                            password=db_config['password']
                        )
                        conn.autocommit = False
                        cursor = conn.cursor()
                        logger.info("已重新连接数据库")
        
        # 处理剩余的批次
        if batch_entities:
            try:
                psycopg2.extras.execute_batch(cursor, insert_sql, batch_entities)
                stats['inserted_entities'] += len(batch_entities)
                
                # 更新图层统计
                for entity_data in batch_entities:
                    entity_layer = entity_data[0]  # layer_name在元组中的索引
                    if entity_layer in stats['layer_stats']:
                        stats['layer_stats'][entity_layer]['inserted'] += 1
                
                # 提交最后的事务
                conn.commit()
            except Exception as e:
                error_msg = f"最后批次插入失败: {str(e)}"
                logger.warning(error_msg)
                stats['errors'].append(error_msg)
                conn.rollback()
                stats['skipped_entities'] += len(batch_entities)
        
        # 添加到几何图层元数据
        try:
            register_sql = """
            SELECT Populate_Geometry_Columns(%s::regclass)
            """
            cursor.execute(register_sql, (table_name,))
            conn.commit()
            logger.info("✅ 已注册到几何图层元数据")
        except Exception as e:
            error_msg = f"注册几何图层元数据时出错: {str(e)}"
            logger.warning(error_msg)
            stats['errors'].append(error_msg)
        
        # 打印统计信息
        logger.info("\n=== 导入统计 ===")
        logger.info(f"表名: {table_name}")
        logger.info(f"总实体数: {stats['total_entities']}")
        logger.info(f"成功插入: {stats['inserted_entities']} ({stats['inserted_entities']/max(stats['total_entities'], 1)*100:.1f}%)")
        logger.info(f"跳过的实体: {stats['skipped_entities']} ({stats['skipped_entities']/max(stats['total_entities'], 1)*100:.1f}%)")
        
        success = stats['inserted_entities'] > 0
        
        return {
            'success': success,
            'table_name': table_name,
            'stats': stats,
            'source_srid': source_srid,
            'target_srid': target_srid
        }
        
    except Exception as e:
        error_msg = f"处理过程中出错: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    finally:
        # 关闭数据库连接
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


# 如果作为独立脚本运行
if __name__ == "__main__":
    # 示例数据库连接配置
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'dbname': 'Geometry',
        'user': 'postgres',
        'password': '123456'
    }
    
    # 测试文件路径
    test_file = r"G:\code\shpservice\FilesData\77e11fb2f26f413e893f837111f8d1e0.dxf"
    
    # 运行导入
    result = dxf_to_postgis(
        dxf_file_path=test_file,
        db_config=db_config,
        source_srid=4545,
        target_srid=3857
    )
    
    # 打印最终结果
    if result['success']:
        logger.info(f"\n✅ DXF 数据已成功导入到表 '{result['table_name']}'")
        logger.info(f"您可以使用以下 SQL 查询数据:")
        logger.info(f"SELECT * FROM {result['table_name']} LIMIT 10;")
        logger.info(f"SELECT cad_layer, COUNT(*) FROM {result['table_name']} GROUP BY cad_layer ORDER BY cad_layer;")
    else:
        logger.error(f"\n❌ DXF 导入失败: {result.get('error', '未知错误')}")