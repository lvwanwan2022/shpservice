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

logger = logging.getLogger(__name__)

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
                '--config', 'DXF_ENCODING', 'UTF-8',
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
            '--config', 'DXF_ENCODING', 'UTF-8'
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
                # 创建图层样式表
                layer_style_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name}_layer_styles AS
                SELECT DISTINCT 
                    layer_name,
                    color_info,
                    linetype_info,
                    lineweight_info,
                    COUNT(*) as feature_count
                FROM {table_name}
                WHERE layer_name IS NOT NULL
                GROUP BY layer_name, color_info, linetype_info, lineweight_info;
                """
                
                conn.execute(text(layer_style_sql))
                
                # 创建颜色映射表
                color_mapping_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name}_color_mapping AS
                SELECT DISTINCT 
                    color_info,
                    CASE 
                        WHEN color_info ~ '^[0-9]+$' THEN 
                            CASE CAST(color_info AS INTEGER)
                                WHEN 1 THEN '#FF0000'  -- 红色
                                WHEN 2 THEN '#FFFF00'  -- 黄色
                                WHEN 3 THEN '#00FF00'  -- 绿色
                                WHEN 4 THEN '#00FFFF'  -- 青色
                                WHEN 5 THEN '#0000FF'  -- 蓝色
                                WHEN 6 THEN '#FF00FF'  -- 洋红
                                WHEN 7 THEN '#FFFFFF'  -- 白色
                                WHEN 8 THEN '#808080'  -- 灰色
                                ELSE '#000000'         -- 默认黑色
                            END
                        ELSE '#000000'
                    END as hex_color,
                    COUNT(*) as usage_count
                FROM {table_name}
                WHERE color_info IS NOT NULL
                GROUP BY color_info;
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
                # 统计图层信息
                layer_stats = conn.execute(text(f"""
                    SELECT 
                        COUNT(DISTINCT layer_name) as layer_count,
                        COUNT(DISTINCT color_info) as color_count,
                        COUNT(DISTINCT linetype_info) as linetype_count,
                        COUNT(*) as total_features
                    FROM {table_name}
                """)).fetchone()
                
                # 获取样式字段统计
                style_fields = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    AND column_name IN ('layer', 'layer_name', 'color', 'color_info', 
                                       'linetype', 'linetype_info', 'lineweight', 'lineweight_info',
                                       'subclasses', 'entity_type', 'entityhandle', 'handle',
                                       'text', 'blockname')
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
        """生成样式图例信息"""
        try:
            with self.engine.connect() as conn:
                # 获取图层样式信息
                layer_styles = conn.execute(text(f"""
                    SELECT * FROM {table_name}_layer_styles 
                    ORDER BY feature_count DESC
                """)).fetchall()
                
                # 获取颜色映射
                color_mapping = conn.execute(text(f"""
                    SELECT * FROM {table_name}_color_mapping
                    ORDER BY usage_count DESC
                """)).fetchall()
                
                return {
                    'layer_styles': [dict(row._mapping) for row in layer_styles],
                    'color_mapping': [dict(row._mapping) for row in color_mapping]
                }
                
        except Exception as e:
            logger.error(f"生成样式图例失败: {str(e)}")
            return {'error': str(e)}

# 使用示例
def process_dxf_with_full_styles(file_path, table_name=None, coordinate_system='EPSG:4326'):
    """
    完整样式导入DXF的便捷函数
    """
    processor = EnhancedDXFProcessor()
    
    if table_name is None:
        import uuid
        table_name = f"dxf_styled_{uuid.uuid4().hex[:8]}"
    
    # 导入DXF
    result = processor.process_dxf_with_enhanced_styles(file_path, table_name, coordinate_system)
    
    if result['success']:
        # 生成样式图例
        legend = processor.generate_style_legend(table_name)
        result['style_legend'] = legend
    
    return result 