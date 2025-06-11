#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版DXF处理器
最大程度保留DXF样式信息
"""

import os
import subprocess
import json
from osgeo import ogr, gdal
from sqlalchemy import create_engine, text
from config import DB_CONFIG
import logging
import uuid
import psycopg2
from psycopg2 import sql
import psycopg2.extras

logger = logging.getLogger(__name__)

# 尝试导入 ezdxf
try:
    import ezdxf
    from ezdxf.math import Vec3
except ImportError:
    logger.error("需要安装 ezdxf 库来解析 DXF 文件。请使用以下命令安装：pip install ezdxf")

# 尝试导入 shapely (用于生成几何对象)
try:
    from shapely.geometry import Point, LineString, Polygon
    from shapely import wkb
except ImportError:
    logger.error("需要安装 shapely 库来处理几何对象。请使用以下命令安装：pip install shapely")

class EnhancedDXFProcessor:
    """增强版DXF处理器，最大程度保留样式信息"""
    
    def __init__(self):
        gdal.UseExceptions()
        db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(db_url)
    
    def process_dxf_with_enhanced_styles(self, file_path, table_name, coordinate_system='EPSG:4326'):
        """
        使用增强配置导入DXF，最大程度保留样式信息
        """
        try:
            logger.info(f"使用增强样式导入DXF: {file_path}")
            
            # 构建增强的ogr2ogr命令
            pg_connection = (
                f"PG:host={DB_CONFIG['host']} "
                f"port={DB_CONFIG['port']} "
                f"dbname={DB_CONFIG['database']} "
                f"user={DB_CONFIG['user']} "
                f"password={DB_CONFIG['password']}"
            )
            
            cmd = [
                'ogr2ogr',
                '-f', 'PostgreSQL',
                pg_connection,
                file_path,
                '-nln', table_name,
                '-overwrite',
                '-lco', 'GEOMETRY_NAME=geom',
                '-lco', 'FID=gid',
                '-t_srs', coordinate_system,
                '-dim', 'XY',
                
                # 增强样式保留配置
                '--config', 'DXF_ENCODING', 'GB18030',# 设置编码，20250610由UTF-8改为ASCII
                '--config', 'DXF_HEADER_ONLY', 'NO',          # 包含所有图层
                '--config', 'DXF_INCLUDE_RAW_CODE_VALUES', 'YES',  # 包含原始代码值
                '--config', 'DXF_TRANSLATE_ESCAPE_SEQUENCES', 'YES', # 转换转义序列
                '--config', 'DXF_CLOSED_LINE_AS_POLYGON', 'YES',    # 闭合线作为多边形
                
                # 保留更多属性
                '-preserve_fid',  # 保留原始FID
                '-sql', f"""
                SELECT 
                    *,
                    Layer as layer_name,
                    CASE 
                        WHEN Color IS NOT NULL THEN Color 
                        ELSE 'BYLAYER' 
                    END as color_info,
                    CASE 
                        WHEN Linetype IS NOT NULL THEN Linetype 
                        ELSE 'BYLAYER' 
                    END as linetype_info,
                    CASE 
                        WHEN LineWeight IS NOT NULL THEN LineWeight 
                        ELSE 'BYLAYER' 
                    END as lineweight_info,
                    SubClasses as entity_type,
                    EntityHandle as handle
                FROM {os.path.basename(file_path).replace('.dxf', '')}
                """
            ]
            
            logger.info(f"执行增强ogr2ogr命令: {' '.join(cmd[:10])}... (命令已截断)")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                # 如果增强命令失败，回退到基本命令
                logger.warning("增强命令失败，回退到基本导入")
                return self._fallback_import(file_path, table_name, coordinate_system)
            
            # 添加样式表
            self._create_style_tables(table_name)
            
            # 分析样式信息
            style_stats = self._analyze_imported_styles(table_name)
            
            logger.info("✅ 增强DXF导入完成")
            
            return {
                'success': True,
                'method': 'enhanced_ogr2ogr',
                'table_name': table_name,
                'coordinate_system': coordinate_system,
                'style_statistics': style_stats,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            logger.error(f"增强DXF导入失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fallback_import(self, file_path, table_name, coordinate_system):
        """回退到基本导入方法"""
        pg_connection = (
            f"PG:host={DB_CONFIG['host']} "
            f"port={DB_CONFIG['port']} "
            f"dbname={DB_CONFIG['database']} "
            f"user={DB_CONFIG['user']} "
            f"password={DB_CONFIG['password']}"
        )
        
        cmd = [
            'ogr2ogr',
            '-f', 'PostgreSQL',
            pg_connection,
            file_path,
            '-nln', table_name,
            '-overwrite',
            '-lco', 'GEOMETRY_NAME=geom',
            '-lco', 'FID=gid',
            '-t_srs', coordinate_system,
            '-dim', 'XY',
            '--config', 'DXF_ENCODING', 'GB18030'#改为ASCII
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"基本导入也失败: {result.stderr}")
        
        return {
            'success': True,
            'method': 'fallback_ogr2ogr',
            'table_name': table_name,
            'coordinate_system': coordinate_system
        }
    
    def _create_style_tables(self, table_name):
        """创建样式相关的辅助表"""
        try:
            with self.engine.connect() as conn:
                # 创建图层样式表 - 更新字段名从color_index改为color_value
                layer_style_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name}_layer_styles AS
                SELECT DISTINCT 
                    cad_layer,
                    color_value,
                    linetype,
                    COUNT(*) as feature_count
                FROM {table_name}
                WHERE cad_layer IS NOT NULL
                GROUP BY cad_layer, color_value, linetype;
                """
                
                conn.execute(text(layer_style_sql))
                
                # 创建颜色映射表 - 更新字段名从color_index改为color_value
                color_mapping_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name}_color_mapping AS
                SELECT DISTINCT 
                    color_value,
                    color_rgb,
                    COUNT(*) as usage_count
                FROM {table_name}
                WHERE color_value IS NOT NULL
                GROUP BY color_value, color_rgb;
                """
                
                conn.execute(text(color_mapping_sql))
                conn.commit()
                
                logger.info(f"✅ 样式辅助表创建完成: {table_name}_layer_styles, {table_name}_color_mapping")
                
        except Exception as e:
            logger.warning(f"创建样式表失败: {str(e)}")
    
    def _analyze_imported_styles(self, table_name):
        """分析导入后的样式信息"""
        try:
            with self.engine.connect() as conn:
                # 统计图层信息 - 使用color_value替代color_index
                layer_stats = conn.execute(text(f"""
                    SELECT 
                        COUNT(DISTINCT cad_layer) as layer_count,
                        COUNT(DISTINCT color_value) as color_count,
                        COUNT(DISTINCT linetype) as linetype_count,
                        COUNT(*) as total_features
                    FROM {table_name}
                """)).fetchone()
                
                # 获取样式字段统计 - 更新字段名查询条件
                style_fields = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    AND column_name IN ('cad_layer', 'color_value', 
                                       'color_rgb', 'color_name', 'linetype', 'entityhandle',
                                       'text', 'rawcodevalues')
                """)).fetchall()
                
                return {
                    'layer_count': layer_stats[0] if layer_stats else 0,
                    'color_count': layer_stats[1] if layer_stats else 0,
                    'linetype_count': layer_stats[2] if layer_stats else 0,
                    'total_features': layer_stats[3] if layer_stats else 0,
                    'preserved_style_fields': [row[0] for row in style_fields],
                    'style_field_count': len(style_fields)
                }
                
        except Exception as e:
            logger.error(f"样式分析失败: {str(e)}")
            return {'error': str(e)}
    
    def generate_style_legend(self, table_name):
        """生成样式图例"""
        try:
            with self.engine.connect() as conn:
                # 获取图层和颜色信息 - 更新字段名
                legend_data = conn.execute(text(f"""
                    SELECT 
                        ls.cad_layer,
                        cm.color_rgb,
                        ls.feature_count,
                        ls.linetype
                    FROM {table_name}_layer_styles ls
                    LEFT JOIN {table_name}_color_mapping cm ON ls.color_value = cm.color_value
                    ORDER BY ls.feature_count DESC
                """)).fetchall()
                
                legend = []
                for row in legend_data:
                    legend.append({
                        'layer': row[0],
                        'color': row[1],
                        'feature_count': row[2],
                        'linetype': row[3]
                    })
                
                return legend
                
        except Exception as e:
            logger.error(f"生成样式图例失败: {str(e)}")
            return []

    # 定义AutoCAD颜色索引(ACI)到RGB的映射
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
    }

    def get_rgb_from_aci(self, color_index):
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
        rgb = self.ACI_COLORS.get(color_index)
        if rgb:
            return f"({rgb[0]},{rgb[1]},{rgb[2]})"
        
        # 如果不在颜色表中，使用一个简单的算法生成颜色
        r = (color_index * 30) % 255
        g = (color_index * 60) % 255
        b = (color_index * 90) % 255
        return f"({r},{g},{b})"

    def extract_entity_geometry(self, entity):
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
                    # 完全重写LWPOLYLINE点处理逻辑
                    lwpoints = entity.get_points()
                    
                    for point_data in lwpoints:
                        # 有多种可能的格式:
                        # (x, y)
                        # (x, y, bulge)
                        # (x, y, start_width, end_width, bulge)
                        if isinstance(point_data, (list, tuple)):
                            # 安全地获取前两个值，忽略其他值
                            if len(point_data) >= 2:
                                x, y = point_data[0], point_data[1]
                                points.append((x, y))
                            else:
                                logger.warning(f"LWPOLYLINE点数据格式错误: {point_data}")
                        else:
                            logger.warning(f"无法解析LWPOLYLINE点数据: {point_data}")
                else:  # POLYLINE
                    points = [(p.dxf.location.x, p.dxf.location.y) for p in entity.vertices]
                
                # 确保有足够的点
                if len(points) < 2:
                    logger.warning(f"多段线点数不足: {len(points)}")
                    return None
                
                # 检查是否为闭合多边形
                is_closed = False
                if hasattr(entity.dxf, 'closed'):
                    is_closed = entity.dxf.closed
                elif hasattr(entity, 'closed'):
                    is_closed = entity.closed
                
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
                
                # 创建圆的近似多边形 - 使用16个点
                import math
                points = []
                for i in range(17):  # 使用17个点形成一个闭合的环
                    angle = i * (2 * math.pi / 16)
                    x = center.x + (radius * math.cos(angle))
                    y = center.y + (radius * math.sin(angle))
                    points.append((x, y))
                
                return Polygon(points)
            
            elif entity_type == 'ARC':
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                
                # 创建弧的近似多段线 - 角度间隔5度
                import math
                points = []
                
                # 确保end_angle大于start_angle
                if end_angle < start_angle:
                    end_angle += 360
                
                # 弧的角度间隔
                angle_step = 5  # 5度间隔
                
                # 计算弧上的点
                current_angle = start_angle
                while current_angle <= end_angle:
                    angle_rad = math.radians(current_angle)
                    x = center.x + (radius * math.cos(angle_rad))
                    y = center.y + (radius * math.sin(angle_rad))
                    points.append((x, y))
                    current_angle += angle_step
                
                # 确保添加最后一个点
                if current_angle > end_angle and abs(current_angle - end_angle) > 0.1:
                    angle_rad = math.radians(end_angle)
                    x = center.x + (radius * math.cos(angle_rad))
                    y = center.y + (radius * math.sin(angle_rad))
                    points.append((x, y))
                
                # 需要至少两个点
                if len(points) < 2:
                    return Point(center.x, center.y)
                
                return LineString(points)
            
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

    def import_dxf_to_postgis_ezdxf(self, file_path, table_name, source_srs='EPSG:4326', target_srs='EPSG:3857'):
        """
        使用ezdxf库将DXF文件导入到PostGIS数据库
        参考test_ogr2ogr.py中的实现
        
        Args:
            file_path: DXF文件路径
            table_name: 目标表名
            source_srs: 源坐标系EPSG代码字符串，如'EPSG:4326'
            target_srs: 目标坐标系EPSG代码字符串，如'EPSG:3857'
            
        Returns:
            dict: 处理结果，包含成功/失败信息、表名、统计数据等
        """
        logger.info(f"=== 使用ezdxf开始将DXF文件导入到PostGIS: {table_name} ===")
        logger.info(f"源文件: {file_path}")
        logger.info(f"坐标系转换: {source_srs} → {target_srs}")
        
        # 提取SRID数字
        source_srid = int(source_srs.replace('EPSG:', '')) if source_srs.startswith('EPSG:') else 4326
        target_srid = int(target_srs.replace('EPSG:', '')) if target_srs.startswith('EPSG:') else 3857
        
        # 统计变量
        stats = {
            'total_entities': 0,
            'inserted_entities': 0,
            'skipped_entities': 0,
            'layer_stats': {},
            'errors': [],
            'geometry_types': set(),
            'layers': set()
        }
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"错误：DXF文件不存在于路径: {file_path}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        try:
            # 尝试不同的编码打开DXF文件
            encodings_to_try = ['gb18030', 'utf-8', 'cp936', 'gbk']
            doc = None
            
            for encoding in encodings_to_try:
                try:
                    logger.info(f"尝试使用 {encoding} 编码打开DXF文件...")
                    doc = ezdxf.readfile(file_path, encoding=encoding)
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
                stats['layers'].add(layer_name)
                # 获取图层颜色
                layer_color = getattr(layer.dxf, 'color', 7)  # 默认为7(白色/黑色)
                layer_colors[layer_name] = layer_color
                # 获取图层RGB颜色
                layer_rgb_colors[layer_name] = self.get_rgb_from_aci(layer_color)
            
            logger.info(f"已加载 {len(layer_colors)} 个图层的颜色信息")
            
            # 连接到PostgreSQL数据库
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                dbname=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
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
                color_rgb character varying,    -- RGB颜色值字符串 '(R,G,B)'
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
                           color_value, color_name, color_rgb, lineweight, geom)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_Transform(ST_SetSRID(ST_GeomFromWKB(%s), %s), %s))
            """).format(sql.Identifier(table_name))
            
            # 批处理变量
            batch_entities = []
            batch_size = 100  # 每批处理的实体数量
            
            # 处理模型空间中的实体
            msp = doc.modelspace()
            all_entities = list(msp)
            stats['total_entities'] = len(all_entities)
            
            for entity in all_entities:
                try:
                    # 获取实体基本属性
                    entity_type = entity.DXFTYPE
                    stats['geometry_types'].add(entity_type)
                    
                    layer_name = entity.dxf.layer
                    
                    # 更新图层统计
                    if layer_name not in stats['layer_stats']:
                        stats['layer_stats'][layer_name] = {'total': 0, 'inserted': 0, 'skipped': 0}
                    stats['layer_stats'][layer_name]['total'] += 1
                    
                    # 提取实体属性
                    paperspace = True if getattr(entity.dxf, 'paperspace', 0) != 0 else False
                    subclasses = getattr(entity, 'subclasses', None)
                    if subclasses and hasattr(subclasses, '__iter__'):
                        subclasses = ','.join(subclasses)
                    linetype = getattr(entity.dxf, 'linetype', None)
                    entityhandle = entity.dxf.handle
                    
                    # 提取文本内容（如果是文本实体）
                    text_value = None
                    if entity_type == 'TEXT':
                        text_value = getattr(entity.dxf, 'text', '')
                    elif entity_type == 'MTEXT':
                        text_value = entity.text if hasattr(entity, 'text') else ''
                    
                    # 提取颜色信息
                    color_value = getattr(entity.dxf, 'color', 0)
                    true_color = getattr(entity.dxf, 'true_color', 0)
                    lineweight = getattr(entity.dxf, 'lineweight', 0)
                    
                    # 确保颜色值为整数，处理None值
                    color_value = 0 if color_value is None else color_value
                    true_color = 0 if true_color is None else true_color
                    lineweight = 0 if lineweight is None else lineweight
                    
                    # 初始化RGB颜色值
                    color_name = ""
                    if true_color > 0:
                        # 如果实体有真彩色值，优先使用
                        r = (true_color >> 16) & 0xFF
                        g = (true_color >> 8) & 0xFF
                        b = true_color & 0xFF
                        rgb_color = f"({r},{g},{b})"
                        color_name = "真彩色"
                    elif color_value == 255 or color_value == 0:  # BYLAYER或BYBLOCK
                        # 使用图层的颜色
                        layer_color = layer_colors.get(layer_name, 7)  # 默认为白色
                        color_value = layer_color
                        color_name = self._get_color_name(layer_color) + " (来自图层)"
                        rgb_color = layer_rgb_colors.get(layer_name, "(255,255,255)")
                    else:
                        # 使用颜色索引对应的RGB值
                        color_name = self._get_color_name(color_value)
                        rgb_color = self.get_rgb_from_aci(color_value)
                    
                    # 提取颜色和其他DXF代码值作为数组
                    raw_code_values = []
                    if hasattr(entity.dxf, 'color'):
                        raw_code_values.append(f"62:{entity.dxf.color}")
                    if hasattr(entity.dxf, 'true_color'):
                        raw_code_values.append(f"420:{entity.dxf.true_color}")
                    if hasattr(entity.dxf, 'lineweight'):
                        raw_code_values.append(f"370:{entity.dxf.lineweight}")
                    
                    # 提取几何信息
                    geometry = self.extract_entity_geometry(entity)
                    
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
                                stats['skipped_entities'] += len(batch_entities)
                    else:
                        stats['skipped_entities'] += 1
                        if layer_name in stats['layer_stats']:
                            stats['layer_stats'][layer_name]['skipped'] += 1
                    
                except Exception as e:
                    stats['skipped_entities'] += 1
                    stats['errors'].append(f"处理实体出错: {str(e)}")
                    logger.warning(f"处理实体出错: {str(e)}")
                    
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
                                host=DB_CONFIG['host'],
                                port=DB_CONFIG['port'],
                                dbname=DB_CONFIG['database'],
                                user=DB_CONFIG['user'],
                                password=DB_CONFIG['password']
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
            
            # 计算成功率
            if stats['total_entities'] > 0:
                success_rate = (stats['inserted_entities'] / stats['total_entities']) * 100
            else:
                success_rate = 0
            
            logger.info(f"✅ DXF导入完成: 处理了 {stats['inserted_entities']} 个实体，跳过 {stats['skipped_entities']} 个，成功率 {success_rate:.1f}%")
            
            # 添加样式表和分析样式信息
            self._create_style_tables(table_name)
            style_stats = self._analyze_imported_styles(table_name)
            
            return {
                'success': True,
                'table_name': table_name,
                'original_feature_count': stats['total_entities'],
                'feature_count': stats['inserted_entities'],
                'skipped_features': stats['skipped_entities'],
                'success_rate': success_rate,
                'geometry_types': list(stats['geometry_types']),
                'layers': list(stats['layers']),
                'warnings': stats['errors'],
                'style_statistics': style_stats
            }
            
        except Exception as e:
            logger.error(f"DXF导入PostGIS失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # 关闭数据库连接
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def _get_color_name(self, color_index):
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

def process_dxf_with_full_styles(file_path, table_name=None, coordinate_system='EPSG:4326'):
    """
    处理DXF文件，保留完整样式信息
    便捷的独立函数，内部使用EnhancedDXFProcessor类
    
    Args:
        file_path: DXF文件路径
        table_name: 目标表名（如果为None则自动生成）
        coordinate_system: 坐标系
        
    Returns:
        dict: 处理结果
    """
    processor = EnhancedDXFProcessor()
    
    if table_name is None:
        table_name = f"vector_dxf_{uuid.uuid4().hex[:8]}"
        
    return processor.process_dxf_with_enhanced_styles(file_path, table_name, coordinate_system)

def dxf_to_postgis(file_path, table_name, source_srs='EPSG:4326', target_srs='EPSG:3857'):
    """
    使用ezdxf库将DXF文件导入到PostGIS数据库
    此函数是import_dxf_to_postgis_ezdxf的别名，方便调用
    
    Args:
        file_path: DXF文件路径
        table_name: 目标表名
        source_srs: 源坐标系EPSG代码字符串，如'EPSG:4326'
        target_srs: 目标坐标系EPSG代码字符串，如'EPSG:3857'
            
    Returns:
        dict: 处理结果，包含成功/失败信息、表名、统计数据等
    """
    processor = EnhancedDXFProcessor()
    return processor.import_dxf_to_postgis_ezdxf(file_path, table_name, source_srs, target_srs) 