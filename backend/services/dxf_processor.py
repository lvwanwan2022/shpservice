#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DXF文件处理服务
使用GDAL/OGR方法导入PostGIS
"""

import os
import tempfile
import uuid
import subprocess
import json
from pathlib import Path
from osgeo import ogr, osr, gdal
from sqlalchemy import create_engine, text
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

class DXFProcessor:
    """DXF文件处理器，专门处理AutoCAD DXF文件"""
    
    def __init__(self):
        """初始化DXF处理器"""
        # 启用GDAL异常
        gdal.UseExceptions()
        
        # 数据库连接
        db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password'].replace('@', '%40')}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(db_url)
        
        logger.info("✅ DXF处理器初始化完成")
    
    def process_dxf_file(self, file_path, table_name, coordinate_system='EPSG:4326'):
        """
        处理DXF文件并导入PostGIS
        
        Args:
            file_path: DXF文件路径
            table_name: 目标表名
            coordinate_system: 坐标系，默认EPSG:4326
            
        Returns:
            dict: 处理结果
        """
        try:
            logger.info(f"开始处理DXF文件: {file_path}")
            
            # 1. 验证文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"DXF文件不存在: {file_path}")
            
            # 2. 分析DXF文件结构
            dxf_info = self._analyze_dxf_file(file_path)
            logger.info(f"DXF文件分析结果: {dxf_info}")
            
            # 3. 使用GDAL导入PostGIS
            result = self._import_with_gdal(file_path, table_name, coordinate_system)
            
            # 4. 创建空间索引
            self._create_spatial_index(table_name)
            
            # 5. 重命名layer字段为cad_layer（解决MVT服务layer属性冲突）
            rename_result = self._rename_layer_field_to_cad_layer(table_name)
            if rename_result['success']:
                logger.info(f"✅ 字段重命名完成: {rename_result['message']}")
            else:
                logger.warning(f"⚠️ 字段重命名失败: {rename_result['error']}")
            
            return {
                'success': True,
                'table_name': table_name,
                'coordinate_system': coordinate_system,
                'dxf_info': dxf_info,
                'import_result': result,
                'rename_result': rename_result
            }
            
        except Exception as e:
            logger.error(f"处理DXF文件失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_dxf_file(self, file_path):
        """分析DXF文件结构"""
        try:
            # 使用GDAL打开DXF文件
            driver = ogr.GetDriverByName('DXF')
            datasource = driver.Open(file_path, 0)
            
            if not datasource:
                raise Exception("无法打开DXF文件")
            
            layers_info = []
            total_features = 0
            
            # 遍历所有图层
            for i in range(datasource.GetLayerCount()):
                layer = datasource.GetLayer(i)
                layer_name = layer.GetName()
                feature_count = layer.GetFeatureCount()
                
                # 获取几何类型
                geom_type = ogr.GeometryTypeToName(layer.GetGeomType())
                
                # 获取字段信息
                layer_defn = layer.GetLayerDefn()
                fields = []
                for j in range(layer_defn.GetFieldCount()):
                    field_defn = layer_defn.GetFieldDefn(j)
                    fields.append({
                        'name': field_defn.GetName(),
                        'type': field_defn.GetFieldTypeName(field_defn.GetType())
                    })
                
                layers_info.append({
                    'name': layer_name,
                    'feature_count': feature_count,
                    'geometry_type': geom_type,
                    'fields': fields
                })
                
                total_features += feature_count
            
            datasource = None
            
            return {
                'total_layers': len(layers_info),
                'total_features': total_features,
                'layers': layers_info
            }
            
        except Exception as e:
            logger.error(f"分析DXF文件失败: {str(e)}")
            return {
                'error': str(e)
            }
    
    def _import_with_gdal(self, file_path, table_name, coordinate_system):
        """使用GDAL导入DXF到PostGIS"""
        try:
            # 构建ogr2ogr命令
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
                '-nln', table_name,  # 指定表名
                '-overwrite',  # 覆盖已存在的表
                '-lco', 'GEOMETRY_NAME=geom',  # 几何字段名
                '-lco', 'FID=gid',  # 主键字段名
                '-t_srs', coordinate_system,  # 目标坐标系
                '-dim', 'XY',  # 强制2D
                '--config', 'DXF_ENCODING', 'GB18030',  # 设置编码，20250610由UTF-8改为ASCII
                '--config', 'SHAPE_ENCODING', 'UTF-8',  # 额外的编码设置，20250610由UTF-8改为空
                '--config', 'GDAL_DATA_ENCODING', 'GB18030',  # GDAL数据编码
                # 🔧 解决MVT layer属性冲突：将DXF的layer字段重命名为cad_layer
                # 原因：MVT规范会自动添加layer属性（值为表名），与DXF的layer字段冲突
                # 解决方案：导入时保持原始字段名，导入后通过SQL重命名字段
                '-select', 'layer,paperspace,subclasses,linetype,entityhandle,text,rawcodevalues',
                '--config', 'DXF_FEATURE_LIMIT_PER_BLOCK', '-1'  # 不限制block中的要素数量
            ]
            
            logger.info(f"执行ogr2ogr命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise Exception(f"ogr2ogr执行失败: {error_msg}")
            
            logger.info("✅ GDAL导入完成")
            
            return {
                'method': 'ogr2ogr',
                'command': ' '.join(cmd),
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("DXF导入超时（超过5分钟）")
        except Exception as e:
            logger.error(f"GDAL导入失败: {str(e)}")
            raise
    
    def _create_spatial_index(self, table_name):
        """创建空间索引"""
        try:
            with self.engine.connect() as conn:
                # 创建空间索引
                index_sql = f"""
                CREATE INDEX IF NOT EXISTS {table_name}_geom_idx 
                ON {table_name} USING GIST (geom);
                """
                conn.execute(text(index_sql))
                conn.commit()
                
                logger.info(f"✅ 空间索引创建完成: {table_name}_geom_idx")
                
        except Exception as e:
            logger.error(f"创建空间索引失败: {str(e)}")
            raise

    def process_dxf_with_geopandas(self, file_path, table_name, coordinate_system='EPSG:4326'):
        """
        使用GeoPandas处理DXF文件（备选方案）
        注意：GeoPandas对DXF支持有限
        """
        try:
            import geopandas as gpd
            import fiona
            
            logger.info(f"尝试使用GeoPandas读取DXF: {file_path}")
            
            # 检查fiona是否支持DXF
            if 'DXF' not in fiona.supported_drivers:
                raise Exception("当前fiona版本不支持DXF格式")
            
            # 读取DXF文件
            gdf = gpd.read_file(file_path, driver='DXF')
            
            if gdf.empty:
                raise Exception("DXF文件为空或无法读取几何数据")
            
            # 设置坐标系
            if gdf.crs is None:
                gdf.set_crs(coordinate_system, inplace=True)
            else:
                gdf = gdf.to_crs(coordinate_system)
            
            # 导入PostGIS
            db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password'].replace('@', '%40')}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            
            gdf.to_postgis(
                table_name,
                con=self.engine,
                if_exists='replace',
                index=True,
                chunksize=1000
            )
            
            logger.info("✅ GeoPandas导入完成")
            
            return {
                'success': True,
                'method': 'geopandas',
                'rows_imported': len(gdf),
                'columns': list(gdf.columns),
                'geometry_types': gdf.geom_type.unique().tolist()
            }
            
        except ImportError:
            raise Exception("GeoPandas或相关依赖未安装")
        except Exception as e:
            logger.error(f"GeoPandas处理失败: {str(e)}")
            raise

    def import_dxf_to_postgis(self, file_path, table_name, source_srs='EPSG:4326', target_srs='EPSG:3857'):
        """
        使用ogr2ogr将DXF文件导入PostGIS，支持坐标系转换
        
        Args:
            file_path: DXF文件路径
            table_name: 目标表名
            source_srs: 源坐标系，默认EPSG:4326
            target_srs: 目标坐标系，默认EPSG:3857 (Web Mercator)
            
        Returns:
            dict: 导入结果
        """
        try:
            import subprocess
            import time
            from models.db import execute_query
            
            logger.info(f"开始导入DXF到PostGIS: {file_path} -> {table_name}")
            logger.info(f"坐标系转换: {source_srs} -> {target_srs}")
            
            start_time = time.time()
            
            # 1. 验证文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"DXF文件不存在: {file_path}")
            
            # 2. 分析DXF文件
            dxf_info = self._analyze_dxf_file(file_path)
            logger.info(f"DXF文件分析结果: {dxf_info}")
            
            # 3. 构建ogr2ogr命令
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
                '-nln', table_name,  # 指定表名
                '-overwrite',        # 覆盖已存在的表
                '-lco', 'GEOMETRY_NAME=geom',     # 几何字段名
                '-lco', 'FID=gid',               # 主键字段名
                '-lco', 'SPATIAL_INDEX=ON',      # 创建空间索引，使用ON而不是YES
                '-s_srs', source_srs,            # 源坐标系
                '-t_srs', target_srs,            # 目标坐标系
                '-dim', 'XY',                    # 强制2D
                '-skipfailures',                 # 跳过失败的要素，继续处理
                '--config', 'DXF_ENCODING', 'GB18030',  # 设置编码#改为ASCII
                '--config', 'DXF_MERGE_BLOCK_GEOMETRIES', 'YES',  # 合并块几何
                '--config', 'DXF_INCLUDE_RAW_CODE_VALUES', 'TRUE',  # 包含原始代码值（包括颜色）
                '--config', 'SHAPE_ENCODING', 'GB18030',  # 额外的编码设置
                '--config', 'GDAL_DATA_ENCODING', 'GB18030',  # GDAL数据编码
                # 🔧 解决MVT layer属性冲突：将DXF的layer字段重命名为cad_layer
                # 原因：MVT规范会自动添加layer属性（值为表名），与DXF的layer字段冲突
                # 解决方案：导入时保持原始字段名，导入后通过SQL重命名字段
                '-select', 'layer,paperspace,subclasses,linetype,entityhandle,text,rawcodevalues',
                '--config', 'DXF_FEATURE_LIMIT_PER_BLOCK', '-1'  # 不限制block中的要素数量
            ]
            
            # 如果源坐标系和目标坐标系相同，则不需要坐标转换
            if source_srs == target_srs:
                # 移除坐标转换参数
                cmd = [arg for arg in cmd if arg not in ['-s_srs', source_srs, '-t_srs', target_srs]]
                # 只设置目标坐标系
                cmd.extend(['-a_srs', target_srs])
                logger.info(f"不需要坐标转换，直接设置坐标系为: {target_srs}")
            
            logger.info(f"执行ogr2ogr命令: {' '.join(cmd)}")
            
            # 4. 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            # 由于使用了-skipfailures，即使有部分要素失败，返回码也可能是0
            # 我们需要检查stderr中是否有致命错误
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                # 检查是否是致命错误还是只是警告/跳过的要素
                if 'Terminating translation prematurely' in error_msg or 'FAILURE' in error_msg:
                    logger.error(f"ogr2ogr执行失败: {error_msg}")
                    raise Exception(f"DXF导入失败: {error_msg}")
                else:
                    # 只是警告，可以继续
                    logger.warning(f"ogr2ogr有警告但继续执行: {error_msg}")
            
            # 检查stderr中的警告和跳过信息
            if result.stderr:
                logger.info(f"ogr2ogr输出信息: {result.stderr}")
            
            logger.info("✅ ogr2ogr执行完成")
            
            # 5. 验证导入结果
            validation_result = self._validate_imported_table(table_name, target_srs)
            
            if not validation_result['success']:
                raise Exception(f"导入验证失败: {validation_result['error']}")
            
            # 6. 获取表统计信息
            stats = self._get_table_statistics(table_name)
            
            # 7. 重命名layer字段为cad_layer（解决MVT服务layer属性冲突）
            rename_result = self._rename_layer_field_to_cad_layer(table_name)
            if rename_result['success']:
                logger.info(f"✅ 字段重命名完成: {rename_result['message']}")
            else:
                logger.warning(f"⚠️ 字段重命名失败: {rename_result['error']}")
            
            import_time = time.time() - start_time
            
            logger.info(f"✅ DXF导入完成: {table_name}, 耗时: {import_time:.2f}秒")
            
            # 检查是否有要素被跳过
            skipped_features = 0
            warnings = []
            error_count = 0
            
            if result.stderr:
                # 分析stderr中的跳过信息
                stderr_lines = result.stderr.split('\n')
                for line in stderr_lines:
                    if 'Unable to write feature' in line:
                        skipped_features += 1
                    elif 'More than' in line and 'errors or warnings' in line:
                        # 如果超过1000个错误，从消息中提取数量
                        try:
                            parts = line.split()
                            if len(parts) >= 3 and parts[2].isdigit():
                                error_count = int(parts[2])
                        except:
                            pass
                    elif 'Warning' in line or 'ERROR' in line:
                        warnings.append(line.strip())
            
            # 计算成功导入的要素数量
            original_features = dxf_info.get('total_features', 0)
            imported_features = stats['feature_count']
            
            # 如果ogr2ogr停止报告错误，通过数量差计算跳过的要素
            if error_count > 0 or (original_features > imported_features and skipped_features == 0):
                skipped_features = max(skipped_features, original_features - imported_features)
            
            logger.info(f"原始要素数: {original_features}, 成功导入: {imported_features}, 跳过: {skipped_features}")
            
            # 如果有大量错误，添加特殊说明
            if error_count > 0:
                warnings.insert(0, f"检测到大量错误（>{error_count}个），部分要素可能因编码或几何问题被跳过")
            
            return {
                'success': True,
                'table_name': table_name,
                'source_srs': source_srs,
                'target_srs': target_srs,
                'import_time': import_time,
                'feature_count': imported_features,
                'original_feature_count': original_features,
                'skipped_features': skipped_features,
                'success_rate': (imported_features / original_features * 100) if original_features > 0 else 0,
                'bbox': stats['bbox'],
                'geometry_types': stats['geometry_types'],
                'layers': dxf_info.get('layers', []),
                'dxf_info': dxf_info,
                'warnings': warnings,
                'ogr_output': {
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            }
            
        except subprocess.TimeoutExpired:
            logger.error("DXF导入超时（超过10分钟）")
            return {'success': False, 'error': 'DXF导入超时（超过10分钟）'}
        except Exception as e:
            logger.error(f"DXF导入失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _validate_imported_table(self, table_name, expected_srs):
        """验证导入的表"""
        try:
            from models.db import execute_query
            
            # 检查表是否存在
            check_table_sql = """
            SELECT COUNT(*) as exists FROM information_schema.tables 
            WHERE table_name = %s AND table_schema = 'public'
            """
            table_exists = execute_query(check_table_sql, [table_name])
            
            if not table_exists or table_exists[0]['exists'] == 0:
                return {'success': False, 'error': f'表 {table_name} 不存在'}
            
            # 检查几何字段和数据
            check_geom_sql = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(geom) as geom_rows,
                ST_SRID(geom) as srid
            FROM {table_name}
            GROUP BY ST_SRID(geom)
            """
            geom_info = execute_query(check_geom_sql, [])
            
            if not geom_info:
                # 检查表是否完全为空
                check_empty_sql = f"SELECT COUNT(*) as count FROM {table_name}"
                empty_check = execute_query(check_empty_sql, [])
                if empty_check and empty_check[0]['count'] == 0:
                    return {'success': False, 'error': '表中没有数据（所有要素可能都导入失败）'}
                else:
                    return {'success': False, 'error': '表中没有有效的几何数据'}
            
            # 验证坐标系
            actual_srid = geom_info[0]['srid']
            expected_srid = int(expected_srs.replace('EPSG:', ''))
            
            if actual_srid != expected_srid:
                logger.warning(f"坐标系不匹配: 期望 {expected_srid}, 实际 {actual_srid}")
            
            total_rows = geom_info[0]['total_rows']
            geom_rows = geom_info[0]['geom_rows']
            
            # 如果有几何数据就认为成功，即使数量可能比原始文件少
            if geom_rows > 0:
                logger.info(f"成功导入 {geom_rows} 个有效几何要素（共 {total_rows} 行）")
                return {
                    'success': True,
                    'total_rows': total_rows,
                    'geom_rows': geom_rows,
                    'srid': actual_srid
                }
            else:
                return {'success': False, 'error': '没有有效的几何数据被导入'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_table_statistics(self, table_name):
        """获取表统计信息"""
        try:
            from models.db import execute_query
            
            # 获取基本统计
            stats_sql = f"""
            SELECT 
                COUNT(*) as feature_count,
                ST_GeometryType(geom) as geom_type,
                COUNT(DISTINCT ST_GeometryType(geom)) as geom_type_count
            FROM {table_name} 
            WHERE geom IS NOT NULL
            GROUP BY ST_GeometryType(geom)
            """
            
            stats = execute_query(stats_sql, [])
            
            total_features = sum(row['feature_count'] for row in stats)
            geometry_types = [row['geom_type'] for row in stats]
            
            # 获取边界框
            bbox_sql = f"""
            SELECT 
                ST_XMin(extent) as min_x,
                ST_YMin(extent) as min_y,
                ST_XMax(extent) as max_x,
                ST_YMax(extent) as max_y
            FROM (
                SELECT ST_Extent(geom) as extent 
                FROM {table_name} 
                WHERE geom IS NOT NULL
            ) as bbox_query
            """
            
            bbox_result = execute_query(bbox_sql, [])
            bbox = None
            
            if bbox_result and bbox_result[0]['min_x'] is not None:
                bbox = [
                    bbox_result[0]['min_x'],
                    bbox_result[0]['min_y'],
                    bbox_result[0]['max_x'],
                    bbox_result[0]['max_y']
                ]
            
            return {
                'feature_count': total_features,
                'bbox': bbox,
                'geometry_types': geometry_types
            }
            
        except Exception as e:
            logger.error(f"获取表统计信息失败: {str(e)}")
            return {
                'feature_count': 0,
                'bbox': None,
                'geometry_types': []
            }

    def _rename_layer_field_to_cad_layer(self, table_name):
        """重命名layer字段为cad_layer"""
        try:
            from models.db import execute_query
            
            logger.info(f"开始重命名layer字段为cad_layer: {table_name}")
            
            # 1. 检查layer字段是否存在
            check_layer_sql = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = %s AND column_name = 'layer'
            """
            layer_exists = execute_query(check_layer_sql, [table_name])
            
            if not layer_exists:
                return {'success': False, 'error': 'layer字段不存在，无法重命名'}
            
            # 2. 重命名layer字段为cad_layer
            rename_layer_sql = f"""
            ALTER TABLE {table_name} 
            RENAME COLUMN layer TO cad_layer;
            """
            execute_query(rename_layer_sql, [], fetch=False)
            logger.info("✅ layer字段重命名完成")
            
            return {
                'success': True,
                'message': f'layer字段重命名完成: {table_name} 表中layer字段已重命名为cad_layer'
            }
            
        except Exception as e:
            logger.error(f"重命名layer字段失败: {str(e)}")
            return {'success': False, 'error': str(e)}

# 使用示例函数
def process_dxf_to_postgis(file_path, table_name=None, coordinate_system='EPSG:4326', method='gdal'):
    """
    处理DXF文件到PostGIS的便捷函数
    
    Args:
        file_path: DXF文件路径
        table_name: 目标表名，如果为None则自动生成
        coordinate_system: 坐标系
        method: 处理方法 ('gdal' 或 'geopandas')
    """
    processor = DXFProcessor()
    
    if table_name is None:
        table_name = f"dxf_{uuid.uuid4().hex[:8]}"
    
    if method == 'gdal':
        return processor.process_dxf_file(file_path, table_name, coordinate_system)
    elif method == 'geopandas':
        return processor.process_dxf_with_geopandas(file_path, table_name, coordinate_system)
    else:
        raise ValueError("method必须是'gdal'或'geopandas'") 