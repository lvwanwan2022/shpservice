#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostGIS服务类，用于管理PostGIS数据库操作
提供 geopandas 和手动实现两种方法
"""

import os
import json
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, RealDictCursor
import time
import uuid
import tempfile
import warnings

from config import DB_CONFIG


class PostGISService:
    """PostGIS服务类，用于管理PostGIS数据库操作"""
    
    def __init__(self):
        """初始化PostGIS服务"""
        self.db_config = DB_CONFIG
        self.table_prefix = 'geojson_'
        self.use_geopandas = self._check_geopandas_availability()
        
        if self.use_geopandas:
            try:
                self.engine = self._create_sqlalchemy_engine()
                print("✅ geopandas模式启用")
            except Exception as e:
                print(f"⚠️ SQLAlchemy引擎创建失败，回退到手动模式: {e}")
                self.use_geopandas = False
        
        if not self.use_geopandas:
            print("✅ 手动实现模式启用")
    
    def _check_geopandas_availability(self):
        """检查geopandas是否可用"""
        try:
            import geopandas as gpd
            import pandas as pd
            from sqlalchemy import create_engine, text
            import warnings
            
            # 创建一个简单测试
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # 测试基本功能
                from shapely.geometry import Point
                import tempfile
                
                # 创建简单测试数据
                data = {'geometry': [Point(0, 0)]}
                gdf = gpd.GeoDataFrame(data, crs='EPSG:4326')
                
                # 测试导出功能
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.geojson')
                gdf.to_file(temp_file.name, driver='GeoJSON')
                
                # 测试读取功能
                gdf_read = gpd.read_file(temp_file.name)
                
                # 清理
                os.unlink(temp_file.name)
                
                return True
                
        except Exception as e:
            print(f"⚠️ geopandas不可用，将使用手动实现: {e}")
            return False
    
    def _create_sqlalchemy_engine(self):
        """创建SQLAlchemy引擎"""
        from sqlalchemy import create_engine
        connection_string = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        engine = create_engine(connection_string, echo=False)
        return engine
    
    def get_connection(self):
        """获取数据库连接"""
        connection_uri = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        conn = psycopg2.connect(connection_uri, client_encoding='utf8')
        return conn
    
    def store_geojson(self, geojson_path, file_id):
        """将GeoJSON文件存储到PostGIS数据库
        
        优先尝试 geopandas 方法，失败时回退到手动实现
        
        Args:
            geojson_path: GeoJSON文件路径
            file_id: 文件ID
            
        Returns:
            表名和特性信息的字典
        """
        print(f"\n=== 开始将GeoJSON存储到PostGIS ===")
        print(f"文件路径: {geojson_path}")
        print(f"文件ID: {file_id}")
        print(f"使用模式: {'geopandas' if self.use_geopandas else '手动实现'}")
        
        # 首先检查数据库是否安装了PostGIS扩展
        self._check_postgis_extension()
        
        if self.use_geopandas:
            try:
                return self._store_geojson_with_geopandas(geojson_path, file_id)
            except Exception as e:
                print(f"⚠️ geopandas方法失败，回退到手动实现: {e}")
                # 回退到手动实现
                return self._store_geojson_manual(geojson_path, file_id)
        else:
            return self._store_geojson_manual(geojson_path, file_id)
    
    def _store_geojson_with_geopandas(self, geojson_path, file_id):
        """使用geopandas存储GeoJSON"""
        import geopandas as gpd
        import pandas as pd
        import warnings
        
        print("📖 使用 geopandas 读取 GeoJSON 文件...")
        
        # 首先读取GeoJSON文件以获取CRS信息
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # 从GeoJSON中提取CRS信息
        original_srid, original_crs = self._extract_crs_from_geojson(geojson_data)
        
        # 禁用一些不必要的警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gdf = gpd.read_file(geojson_path, encoding='utf-8')
        
        print(f"✅ 成功读取 GeoJSON 文件")
        print(f"   - 要素数量: {len(gdf)}")
        print(f"   - 列名: {list(gdf.columns)}")
        print(f"   - geopandas读取的CRS: {gdf.crs}")
        print(f"   - 从GeoJSON解析的CRS: {original_crs} (SRID: {original_srid})")
        
        if len(gdf) == 0:
            raise Exception("GeoJSON文件中没有要素")
        
        # 分析几何类型
        geometry_types = self._analyze_geometry_types_geopandas(gdf)
        print(f"🔍 几何类型分析: {geometry_types}")
        
        # 设置正确的坐标系 - 优先使用从GeoJSON解析的CRS
        if gdf.crs is None:
            print(f"⚠️ geopandas未检测到CRS，设置为从GeoJSON解析的CRS: {original_crs}")
            gdf = gdf.set_crs(original_crs)
        elif str(gdf.crs) != original_crs:
            print(f"⚠️ geopandas检测的CRS ({gdf.crs}) 与GeoJSON中的CRS ({original_crs}) 不一致")
            print(f"🔧 使用GeoJSON中的CRS: {original_crs}")
            gdf = gdf.set_crs(original_crs)
        else:
            print(f"✅ CRS一致: {gdf.crs}")
        
        # 处理属性列名（清理特殊字符）
        gdf = self._clean_column_names(gdf)
        
        # 🔧 新方案：无论是否为混合几何类型，都存储到单一表中
        table_name = f"{self.table_prefix}{file_id}"
        print(f"📊 存储到单一表: {table_name}")
        print(f"   - 几何类型: {geometry_types}")
        print(f"   - 是否混合: {'是' if len(geometry_types) > 1 else '否'}")
        print(f"   - 使用坐标系: {gdf.crs} (SRID: {original_srid})")
        
        # 添加几何类型列，用于后续查询和分离
        gdf['geom_type'] = gdf.geometry.geom_type
        
        # 使用 geopandas 导入到 PostGIS，保持原始坐标系
        self._import_gdf_to_postgis(gdf, table_name, original_srid)
        
        # 构建返回结果
        feature_info = self._build_feature_info_geopandas(gdf, geometry_types, original_srid, original_crs)
        result = {
            "success": True,
            "table_name": table_name,
            "feature_info": feature_info,
            "schema": "public",
            "full_table_name": f"public.{table_name}",
            "geometry_types": geometry_types,
            "is_mixed": len(geometry_types) > 1,
            "has_geom_type_column": True  # 标记包含几何类型列
        }
        
        return result
    
    def _store_geojson_manual(self, geojson_path, file_id):
        """使用手动实现存储GeoJSON"""
        print("📖 使用手动方法读取 GeoJSON 文件...")
        
        # 1. 读取GeoJSON文件
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # 2. 分析GeoJSON特性
        feature_info = self._analyze_geojson(geojson_data)
        print(f"GeoJSON分析结果: {feature_info}")
        
        # 🔧 新方案：无论是否为混合几何类型，都存储到单一表中
        table_name = f"{self.table_prefix}{file_id}"
        print(f"📊 存储到单一表: {table_name}")
        print(f"   - 几何类型: {feature_info['geometry_types']}")
        print(f"   - 是否混合: {'是' if len(feature_info['geometry_types']) > 1 else '否'}")
        
        # 为手动实现添加几何类型信息到每个要素
        geojson_data_with_type = self._add_geom_type_to_features(geojson_data)
        
        # 创建表并导入数据（包含几何类型列）
        self._create_and_import_data_with_geom_type(table_name, geojson_data_with_type, feature_info)
        
        result = {
            "success": True,
            "table_name": table_name,
            "feature_info": feature_info,
            "schema": "public",
            "full_table_name": f"public.{table_name}",
            "geometry_types": feature_info['geometry_types'],
            "is_mixed": len(feature_info['geometry_types']) > 1,
            "has_geom_type_column": True  # 标记包含几何类型列
        }
        
        return result
    
    def _add_geom_type_to_features(self, geojson_data):
        """为GeoJSON要素添加几何类型信息"""
        if geojson_data.get('type') == 'FeatureCollection':
            features = geojson_data.get('features', [])
            for feature in features:
                if 'geometry' in feature and feature['geometry'] and 'type' in feature['geometry']:
                    geom_type = feature['geometry']['type']
                    # 添加几何类型到属性中
                    if 'properties' not in feature:
                        feature['properties'] = {}
                    feature['properties']['geom_type'] = geom_type
        
        elif geojson_data.get('type') == 'Feature':
            if 'geometry' in geojson_data and geojson_data['geometry'] and 'type' in geojson_data['geometry']:
                geom_type = geojson_data['geometry']['type']
                if 'properties' not in geojson_data:
                    geojson_data['properties'] = {}
                geojson_data['properties']['geom_type'] = geom_type
        
        return geojson_data
    
    def _create_and_import_data_with_geom_type(self, table_name, geojson_data, feature_info):
        """创建表并导入GeoJSON数据（包含几何类型列）"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. 删除可能存在的表
            self._drop_table_if_exists(table_name, conn)
            
            # 2. 创建表（添加几何类型列）
            create_table_sql = self._generate_create_table_sql_with_geom_type(table_name, feature_info)
            print(f"创建表SQL: {create_table_sql}")
            cursor.execute(create_table_sql)
            
            # 3. 导入数据
            self._import_geojson_data(table_name, geojson_data, feature_info, conn)
            
            # 4. 创建空间索引
            index_name = f"{table_name}_geom_idx"
            create_index_sql = sql.SQL("CREATE INDEX {} ON {} USING GIST(geom)").format(
                sql.Identifier(index_name),
                sql.Identifier(table_name)
            )
            cursor.execute(create_index_sql)
            
            # 5. 创建几何类型索引（用于快速查询特定几何类型）
            geom_type_index_name = f"{table_name}_geom_type_idx"
            create_geom_type_index_sql = sql.SQL("CREATE INDEX {} ON {} (geom_type)").format(
                sql.Identifier(geom_type_index_name),
                sql.Identifier(table_name)
            )
            cursor.execute(create_geom_type_index_sql)
            
            conn.commit()
            print(f"✅ 表创建和数据导入成功")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ 创建表或导入数据失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _generate_create_table_sql_with_geom_type(self, table_name, feature_info):
        """生成创建表的SQL语句（包含几何类型列）"""
        # 表列定义
        columns = [
            sql.SQL("id SERIAL PRIMARY KEY"),
        ]
        
        # 添加属性列
        for prop_name, prop_type in feature_info['properties'].items():
            columns.append(
                sql.SQL("{} {}").format(
                    sql.Identifier(prop_name),
                    sql.SQL(prop_type)
                )
            )
        
        # 添加几何类型列
        columns.append(sql.SQL("geom_type TEXT"))
        
        # 几何列，使用通用geometry类型以支持混合几何
        columns.append(
            sql.SQL("geom geometry(GEOMETRY, {})").format(
                sql.Literal(feature_info['srid'])
            )
        )
        
        # 构建完整的CREATE TABLE语句
        create_table_sql = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(columns)
        )
        
        return create_table_sql
    
    # === geopandas相关方法 ===
    
    def _analyze_geometry_types_geopandas(self, gdf):
        """分析GeoDataFrame中的几何类型"""
        geometry_types = set()
        
        for geom in gdf.geometry:
            if geom is not None and not geom.is_empty:
                geom_type = geom.geom_type
                geometry_types.add(geom_type)
        
        return sorted(list(geometry_types))
    
    def _clean_column_names(self, gdf):
        """清理列名，确保符合PostgreSQL命名规范"""
        import re
        
        # 保存原始几何列
        geometry_column = gdf.geometry.name
        
        # 清理所有列名
        new_columns = {}
        for col in gdf.columns:
            if col == geometry_column:
                continue  # 跳过几何列
            
            # 替换特殊字符为下划线，只保留字母、数字、下划线
            clean_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', str(col))
            
            # 确保不以数字开头
            if clean_name and clean_name[0].isdigit():
                clean_name = f"col_{clean_name}"
            
            # 如果清理后为空，使用默认名称
            if not clean_name or clean_name == '_':
                clean_name = f"column_{gdf.columns.get_loc(col)}"
            
            new_columns[col] = clean_name
        
        if new_columns:
            gdf = gdf.rename(columns=new_columns)
            print(f"🧹 列名清理完成: {len(new_columns)} 个列被重命名")
            for old, new in new_columns.items():
                print(f"   - {old} -> {new}")
        
        return gdf
    
    def _import_gdf_to_postgis(self, gdf, table_name, srid, if_exists='replace'):
        """使用 geopandas 将 GeoDataFrame 导入到 PostGIS"""
        print(f"📝 使用 geopandas 导入数据到表: {table_name}")
        print(f"   - 要素数量: {len(gdf)}")
        print(f"   - 列数: {len(gdf.columns)}")
        print(f"   - 原始几何列: {gdf.geometry.name}")
        print(f"   - 目标SRID: {srid}")
        
        # 确保有几何数据
        if gdf.geometry.empty or gdf.geometry.isna().all():
            raise Exception("GeoDataFrame 中没有有效的几何数据")
        
        # 🔧 关键修复：统一几何列名称为 'geom'，与PostGIS标准一致
        gdf_copy = gdf.copy()
        if gdf_copy.geometry.name != 'geom':
            print(f"🔧 将几何列名从 '{gdf_copy.geometry.name}' 重命名为 'geom'")
            gdf_copy = gdf_copy.rename_geometry('geom')
        
        # 🔧 关键修复：保持原始坐标系，不强制转换为EPSG:4326
        if gdf_copy.crs is None:
            print(f"⚠️ 设置CRS为EPSG:{srid}")
            gdf_copy = gdf_copy.set_crs(f'EPSG:{srid}')
        else:
            print(f"✅ 保持原始CRS: {gdf_copy.crs}")
        
        print(f"   - 标准化后几何列: {gdf_copy.geometry.name}")
        print(f"   - 最终CRS: {gdf_copy.crs}")
        
        # 使用 to_postgis 方法导入数据，明确指定几何列名
        gdf_copy.to_postgis(
            name=table_name,
            con=self.engine,
            if_exists=if_exists,
            index=True,
            index_label='id',
            geom_col='geom'  # 明确指定几何列名为 'geom'
        )
        
        print(f"✅ 数据导入成功: {table_name}")
        
        # 创建空间索引 - 使用正确的几何列名
        self._create_spatial_index_sqlalchemy(table_name, 'geom')
    
    def _create_spatial_index_sqlalchemy(self, table_name, geom_col='geom'):
        """为表创建空间索引（SQLAlchemy版本）"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                # 检查是否已存在索引
                index_name = f"{table_name}_{geom_col}_idx"
                check_index_sql = f"""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = '{table_name}' 
                AND indexname = '{index_name}'
                """
                
                result = conn.execute(text(check_index_sql))
                index_exists = result.scalar() > 0
                
                if not index_exists:
                    # 创建空间索引 - 使用正确的几何列名
                    create_index_sql = f"""
                    CREATE INDEX {index_name} 
                    ON {table_name} 
                    USING GIST ({geom_col})
                    """
                    conn.execute(text(create_index_sql))
                    conn.commit()
                    print(f"✅ 空间索引创建成功: {index_name}")
                else:
                    print(f"✅ 空间索引已存在: {index_name}")
                    
        except Exception as e:
            print(f"⚠️ 创建空间索引失败: {str(e)}")
            # 不抛出异常，索引创建失败不应影响数据导入
    
    def _build_feature_info_geopandas(self, gdf, geometry_types, srid, crs):
        """构建特性信息（geopandas版本）"""
        import pandas as pd
        
        # 分析属性列类型
        properties = {}
        for col in gdf.columns:
            if col == gdf.geometry.name:
                continue  # 跳过几何列
            
            dtype = gdf[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                properties[col] = 'integer'
            elif pd.api.types.is_float_dtype(dtype):
                properties[col] = 'double precision'
            elif pd.api.types.is_bool_dtype(dtype):
                properties[col] = 'boolean'
            else:
                properties[col] = 'text'
        
        # 确定主要几何类型
        if len(geometry_types) == 1:
            geometry_type = geometry_types[0]
        else:
            geometry_type = 'Geometry'  # 混合类型使用通用类型
        
        feature_info = {
            "geometry_type": geometry_type,
            "geometry_types": geometry_types,
            "properties": properties,
            "feature_count": len(gdf),
            "srid": srid,
            "crs": crs
        }
        
        return feature_info
    
    def _handle_mixed_geometry_types_geopandas(self, file_id, gdf, geometry_types):
        """使用 geopandas 处理混合几何类型"""
        print(f"🔄 处理混合几何类型: {geometry_types}")
        
        tables = {}
        
        for geom_type in geometry_types:
            # 过滤出特定几何类型的要素
            type_gdf = gdf[gdf.geometry.geom_type == geom_type].copy()
            
            if len(type_gdf) == 0:
                print(f"⚠️ 跳过空的几何类型: {geom_type}")
                continue
            
            # 创建特定几何类型的表名
            table_name = f"{self.table_prefix}{file_id}_{geom_type.lower()}"
            print(f"📊 为 {geom_type} 类型创建表: {table_name} ({len(type_gdf)} 个要素)")
            
            try:
                # 导入该几何类型的数据
                self._import_gdf_to_postgis(type_gdf, table_name, 4326)
                
                # 构建该类型的特性信息
                type_feature_info = self._build_feature_info_geopandas(type_gdf, [geom_type], 4326, 'EPSG:4326')
                
                # 记录表信息
                tables[geom_type] = {
                    "table_name": table_name,
                    "full_table_name": f"public.{table_name}",
                    "feature_info": type_feature_info,
                    "feature_count": len(type_gdf)
                }
                
                print(f"✅ {geom_type} 类型处理完成: {table_name}")
                
            except Exception as e:
                print(f"❌ {geom_type} 类型处理失败: {str(e)}")
                continue
        
        if not tables:
            raise Exception("所有几何类型处理都失败了")
        
        # 构建总的特性信息
        total_feature_info = self._build_feature_info_geopandas(gdf, geometry_types, 4326, 'EPSG:4326')
        
        # 返回混合几何类型的结果
        result = {
            "success": True,
            "is_mixed": True,
            "geometry_types": list(tables.keys()),
            "tables": tables,
            "schema": "public",
            "main_table": None,  # 混合类型没有主表
            "feature_info": total_feature_info
        }
        
        print(f"✅ 混合几何类型处理完成，创建了 {len(tables)} 个表")
        for geom_type, table_info in tables.items():
            print(f"   - {geom_type}: {table_info['table_name']} ({table_info['feature_count']} 个要素)")
        
        return result
    
    # === 手动实现方法 ===
    
    def _extract_crs_from_geojson(self, geojson_data):
        """从GeoJSON数据中提取CRS信息
        
        Args:
            geojson_data: GeoJSON数据字典
            
        Returns:
            tuple: (srid, crs_string) 其中srid是数字，crs_string是字符串格式
        """
        # 默认值
        default_srid = 4326
        default_crs = 'EPSG:4326'
        
        # 检查是否有crs字段
        if 'crs' not in geojson_data:
            print("⚠️ GeoJSON文件中没有CRS信息，使用默认WGS84 (EPSG:4326)")
            return default_srid, default_crs
        
        crs_info = geojson_data['crs']
        
        # 处理不同的CRS格式
        if isinstance(crs_info, dict):
            if crs_info.get('type') == 'name':
                # 处理命名CRS格式: {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4547"}}
                properties = crs_info.get('properties', {})
                name = properties.get('name', '')
                
                if 'EPSG::' in name:
                    # 提取EPSG代码
                    try:
                        epsg_code = name.split('EPSG::')[-1]
                        srid = int(epsg_code)
                        crs_string = f'EPSG:{srid}'
                        print(f"✅ 从GeoJSON中解析到CRS: {crs_string}")
                        return srid, crs_string
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ 解析EPSG代码失败: {name}, 错误: {e}")
                        return default_srid, default_crs
                
                elif 'EPSG:' in name:
                    # 处理EPSG:4547格式
                    try:
                        epsg_code = name.split('EPSG:')[-1]
                        srid = int(epsg_code)
                        crs_string = f'EPSG:{srid}'
                        print(f"✅ 从GeoJSON中解析到CRS: {crs_string}")
                        return srid, crs_string
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ 解析EPSG代码失败: {name}, 错误: {e}")
                        return default_srid, default_crs
                
                else:
                    print(f"⚠️ 不支持的CRS格式: {name}")
                    return default_srid, default_crs
            
            elif crs_info.get('type') == 'EPSG':
                # 处理EPSG格式: {"type": "EPSG", "properties": {"code": 4547}}
                properties = crs_info.get('properties', {})
                code = properties.get('code')
                if code:
                    try:
                        srid = int(code)
                        crs_string = f'EPSG:{srid}'
                        print(f"✅ 从GeoJSON中解析到CRS: {crs_string}")
                        return srid, crs_string
                    except ValueError as e:
                        print(f"⚠️ 解析EPSG代码失败: {code}, 错误: {e}")
                        return default_srid, default_crs
            
            else:
                print(f"⚠️ 不支持的CRS类型: {crs_info.get('type')}")
                return default_srid, default_crs
        
        else:
            print(f"⚠️ CRS信息格式不正确: {crs_info}")
            return default_srid, default_crs

    def _analyze_geojson(self, geojson_data):
        """分析GeoJSON数据，提取特性信息"""
        # 从GeoJSON中提取CRS信息
        srid, crs_string = self._extract_crs_from_geojson(geojson_data)
        
        feature_info = {
            "geometry_type": None,
            "geometry_types": set(),  # 存储所有发现的几何类型
            "properties": {},
            "feature_count": 0,
            "srid": srid,  # 使用从GeoJSON中解析的SRID
            "crs": crs_string  # 添加CRS字符串信息
        }
        
        # 处理FeatureCollection
        if geojson_data.get('type') == 'FeatureCollection':
            features = geojson_data.get('features', [])
            feature_info['feature_count'] = len(features)
            
            # 分析所有要素的几何类型
            for feature in features:
                if 'geometry' in feature and feature['geometry'] and 'type' in feature['geometry']:
                    geom_type = feature['geometry']['type']
                    feature_info['geometry_types'].add(geom_type)
                
                # 分析属性（使用第一个有属性的要素）
                if 'properties' in feature and feature['properties'] and not feature_info['properties']:
                    for key, value in feature['properties'].items():
                        if value is not None:
                            if isinstance(value, int):
                                feature_info['properties'][key] = 'integer'
                            elif isinstance(value, float):
                                feature_info['properties'][key] = 'double precision'
                            elif isinstance(value, bool):
                                feature_info['properties'][key] = 'boolean'
                            else:
                                feature_info['properties'][key] = 'text'
            
            # 确定主要几何类型
            if len(feature_info['geometry_types']) == 1:
                feature_info['geometry_type'] = list(feature_info['geometry_types'])[0]
            elif len(feature_info['geometry_types']) > 1:
                # 混合几何类型，使用通用类型
                print(f"⚠️ 检测到混合几何类型: {feature_info['geometry_types']}")
                feature_info['geometry_type'] = 'Geometry'  # 使用通用几何类型
            else:
                print("⚠️ 未检测到有效的几何类型")
                feature_info['geometry_type'] = 'Geometry'  # 默认使用通用几何类型
        
        # 处理单个Feature
        elif geojson_data.get('type') == 'Feature':
            feature_info['feature_count'] = 1
            
            if 'geometry' in geojson_data and geojson_data['geometry'] and 'type' in geojson_data['geometry']:
                geom_type = geojson_data['geometry']['type']
                feature_info['geometry_type'] = geom_type
                feature_info['geometry_types'].add(geom_type)
            
            # 分析属性
            if 'properties' in geojson_data and geojson_data['properties']:
                for key, value in geojson_data['properties'].items():
                    if value is not None:
                        if isinstance(value, int):
                            feature_info['properties'][key] = 'integer'
                        elif isinstance(value, float):
                            feature_info['properties'][key] = 'double precision'
                        elif isinstance(value, bool):
                            feature_info['properties'][key] = 'boolean'
                        else:
                            feature_info['properties'][key] = 'text'
        
        # 转换为列表以便序列化
        feature_info['geometry_types'] = list(feature_info['geometry_types'])
        
        print(f"📊 GeoJSON分析完成:")
        print(f"   - 坐标系: {crs_string} (SRID: {srid})")
        print(f"   - 要素数量: {feature_info['feature_count']}")
        print(f"   - 几何类型: {feature_info['geometry_types']}")
        
        return feature_info
    
    def _handle_mixed_geometry_types_manual(self, file_id, geojson_data, feature_info):
        """处理混合几何类型，分离到不同表（手动实现）"""
        # 按几何类型分组要素
        features_by_type = {}
        
        if geojson_data.get('type') == 'FeatureCollection':
            features = geojson_data.get('features', [])
            
            for feature in features:
                if 'geometry' in feature and feature['geometry'] and 'type' in feature['geometry']:
                    geom_type = feature['geometry']['type']
                    
                    if geom_type not in features_by_type:
                        features_by_type[geom_type] = []
                    
                    features_by_type[geom_type].append(feature)
        
        # 为每个几何类型创建单独的表
        tables = {}
        
        for geom_type, features in features_by_type.items():
            if not features:  # 跳过空的几何类型
                continue
                
            # 创建特定几何类型的表名
            table_name = f"{self.table_prefix}{file_id}_{geom_type.lower()}"
            print(f"为 {geom_type} 类型创建表: {table_name}")
            
            # 创建该几何类型的feature_info
            type_feature_info = {
                "geometry_type": geom_type,
                "geometry_types": [geom_type],
                "properties": feature_info['properties'].copy(),
                "feature_count": len(features),
                "srid": feature_info['srid']
            }
            
            # 创建该几何类型的GeoJSON数据
            type_geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # 创建表并导入数据
            self._create_and_import_data(table_name, type_geojson, type_feature_info)
            
            # 记录表信息
            tables[geom_type] = {
                "table_name": table_name,
                "full_table_name": f"public.{table_name}",
                "feature_info": type_feature_info,
                "feature_count": len(features)
            }
        
        # 返回混合几何类型的结果
        result = {
            "success": True,
            "is_mixed": True,
            "geometry_types": list(features_by_type.keys()),
            "tables": tables,
            "schema": "public",
            "main_table": None,  # 混合类型没有主表
            "feature_info": feature_info
        }
        
        print(f"✅ 混合几何类型处理完成，创建了 {len(tables)} 个表")
        for geom_type, table_info in tables.items():
            print(f"   - {geom_type}: {table_info['table_name']} ({table_info['feature_count']} 个要素)")
        
        return result
    
    def _create_and_import_data(self, table_name, geojson_data, feature_info):
        """创建表并导入GeoJSON数据"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. 删除可能存在的表
            self._drop_table_if_exists(table_name, conn)
            
            # 2. 创建表
            create_table_sql = self._generate_create_table_sql(table_name, feature_info)
            print(f"创建表SQL: {create_table_sql}")
            cursor.execute(create_table_sql)
            
            # 3. 导入数据
            self._import_geojson_data(table_name, geojson_data, feature_info, conn)
            
            # 4. 创建空间索引
            index_name = f"{table_name}_geom_idx"
            create_index_sql = sql.SQL("CREATE INDEX {} ON {} USING GIST(geom)").format(
                sql.Identifier(index_name),
                sql.Identifier(table_name)
            )
            cursor.execute(create_index_sql)
            
            conn.commit()
            print(f"✅ 表创建和数据导入成功")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ 创建表或导入数据失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _generate_create_table_sql(self, table_name, feature_info):
        """生成创建表的SQL语句"""
        # 表列定义
        columns = [
            sql.SQL("id SERIAL PRIMARY KEY"),
        ]
        
        # 添加属性列
        for prop_name, prop_type in feature_info['properties'].items():
            # 处理可能的SQL注入问题，使用psycopg2的SQL组合
            columns.append(
                sql.SQL("{} {}").format(
                    sql.Identifier(prop_name),
                    sql.SQL(prop_type)
                )
            )
        
        # 几何列，使用通用geometry类型
        columns.append(
            sql.SQL("geom geometry({}, {})").format(
                sql.SQL(feature_info['geometry_type']),
                sql.Literal(feature_info['srid'])
            )
        )
        
        # 构建完整的CREATE TABLE语句
        create_table_sql = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(columns)
        )
        
        return create_table_sql
    
    def _import_geojson_data(self, table_name, geojson_data, feature_info, conn=None):
        """导入GeoJSON数据"""
        close_conn = False
        if conn is None:
            conn = self.get_connection()
            close_conn = True
        
        try:
            cursor = conn.cursor()
            
            success_count = 0
            error_count = 0
            total_features = feature_info['feature_count']
            
            # 处理FeatureCollection
            if geojson_data.get('type') == 'FeatureCollection':
                features = geojson_data.get('features', [])
                
                for i, feature in enumerate(features):
                    try:
                        self._insert_feature(table_name, feature, feature_info, cursor)
                        success_count += 1
                        
                        # 每处理100个要素显示一次进度
                        if (i + 1) % 100 == 0:
                            print(f"已处理 {i + 1}/{total_features} 个要素...")
                            
                    except Exception as e:
                        error_count += 1
                        print(f"⚠️ 第 {i+1} 个要素处理失败: {str(e)}")
                        # 继续处理下一个要素
                        continue
            
            # 处理单个Feature
            elif geojson_data.get('type') == 'Feature':
                try:
                    self._insert_feature(table_name, geojson_data, feature_info, cursor)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"⚠️ 要素处理失败: {str(e)}")
            
            conn.commit()
            
            print(f"✅ 数据导入完成")
            print(f"   - 成功导入: {success_count} 个要素")
            if error_count > 0:
                print(f"   - 失败跳过: {error_count} 个要素")
            
            # 如果成功导入的要素数量为0，抛出异常
            if success_count == 0:
                raise Exception("没有成功导入任何要素")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ 导入数据失败: {str(e)}")
            raise
        finally:
            if close_conn and conn:
                conn.close()
    
    def _insert_feature(self, table_name, feature, feature_info, cursor):
        """插入单个要素"""
        if 'properties' not in feature or 'geometry' not in feature:
            print("⚠️ 忽略无效要素：缺少properties或geometry")
            return
        
        properties = feature['properties']
        geometry = feature['geometry']
        
        # 检查几何对象是否为null或empty
        if not geometry or geometry.get('type') is None:
            print("⚠️ 忽略无效要素：几何对象为空")
            return
        
        # 构建列名列表
        columns = []
        values = []
        
        # 添加属性值
        for prop_name in feature_info['properties'].keys():
            columns.append(sql.Identifier(prop_name))
            prop_value = properties.get(prop_name)
            # 处理None值
            if prop_value is None:
                values.append(sql.SQL('NULL'))
            else:
                values.append(sql.Literal(prop_value))
        
        # 添加几何对象
        columns.append(sql.Identifier('geom'))
        
        # 将GeoJSON几何对象转换为PostGIS几何对象
        geom_value = None
        try:
            # 验证并清理GeoJSON几何对象
            cleaned_geometry = self._clean_geojson_geometry(geometry)
            
            # 转换为WKT格式（更稳定的方法）
            wkt = self._geojson_to_wkt(cleaned_geometry)
            geom_value = sql.SQL("ST_SetSRID(ST_GeomFromText({0}), {1})").format(
                sql.Literal(wkt),
                sql.Literal(feature_info['srid'])
            )
            
        except Exception as e:
            print(f"❌ 转换几何对象失败: {str(e)}")
            print(f"几何对象内容: {geometry}")
            # 跳过这个要素而不是抛出异常
            print("⚠️ 跳过此要素")
            return
        
        values.append(geom_value)
        
        # 构建INSERT语句
        insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(columns),
            sql.SQL(", ").join(values)
        )
        
        try:
            cursor.execute(insert_sql)
        except Exception as e:
            print(f"❌ 插入要素失败: {str(e)}")
            print(f"SQL: {insert_sql}")
            print(f"几何对象: {geometry}")
            # 跳过这个要素而不是抛出异常
            print("⚠️ 跳过此要素")
            return
    
    def _clean_geojson_geometry(self, geometry):
        """验证并清理GeoJSON几何对象"""
        if not geometry or not isinstance(geometry, dict):
            raise ValueError("无效的几何对象：不是字典类型")
        
        geom_type = geometry.get('type')
        if not geom_type:
            raise ValueError("无效的几何对象：缺少type字段")
        
        coordinates = geometry.get('coordinates')
        if coordinates is None:
            raise ValueError("无效的几何对象：缺少coordinates字段")
        
        # 验证不同类型的几何对象
        if geom_type == 'Point':
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                raise ValueError("无效的Point几何对象：坐标格式错误")
            # 确保只有x,y坐标
            return {
                'type': 'Point',
                'coordinates': [float(coordinates[0]), float(coordinates[1])]
            }
        
        elif geom_type == 'LineString':
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                raise ValueError("无效的LineString几何对象：至少需要2个点")
            # 验证每个点
            cleaned_coords = []
            for point in coordinates:
                if not isinstance(point, list) or len(point) < 2:
                    raise ValueError("无效的LineString点坐标")
                cleaned_coords.append([float(point[0]), float(point[1])])
            return {
                'type': 'LineString',
                'coordinates': cleaned_coords
            }
        
        elif geom_type == 'Polygon':
            if not isinstance(coordinates, list) or len(coordinates) == 0:
                raise ValueError("无效的Polygon几何对象：缺少环")
            cleaned_rings = []
            for ring in coordinates:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise ValueError("无效的Polygon环：至少需要4个点")
                cleaned_ring = []
                for point in ring:
                    if not isinstance(point, list) or len(point) < 2:
                        raise ValueError("无效的Polygon点坐标")
                    cleaned_ring.append([float(point[0]), float(point[1])])
                cleaned_rings.append(cleaned_ring)
            return {
                'type': 'Polygon',
                'coordinates': cleaned_rings
            }
        
        # 其他几何类型的处理...
        else:
            # 简化处理，直接返回原几何对象
            return geometry
    
    def _geojson_to_wkt(self, geometry):
        """将GeoJSON几何对象转换为WKT格式"""
        geom_type = geometry['type'].upper()
        
        if geom_type == 'POINT':
            coords = geometry['coordinates']
            return f"POINT({coords[0]} {coords[1]})"
        
        elif geom_type == 'LINESTRING':
            coords = geometry['coordinates']
            return f"LINESTRING({', '.join([f'{p[0]} {p[1]}' for p in coords])})"
        
        elif geom_type == 'POLYGON':
            outer_ring = geometry['coordinates'][0]
            rings_text = [f"({', '.join([f'{p[0]} {p[1]}' for p in ring])})" for ring in geometry['coordinates']]
            return f"POLYGON({', '.join(rings_text)})"
        
        else:
            raise ValueError(f"不支持的几何类型: {geom_type}")
    
    # === 通用方法 ===
    
    def _check_postgis_extension(self):
        """检查数据库是否安装了PostGIS扩展"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查是否安装了PostGIS扩展
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'postgis'
                ) as has_postgis;
            """)
            has_postgis = cursor.fetchone()[0]
            
            if not has_postgis:
                print("❌ PostgreSQL数据库中未安装PostGIS扩展")
                
                # 检查是否设置了环境变量来跳过PostGIS检查（仅用于开发环境）
                if os.environ.get('SKIP_POSTGIS_CHECK') == '1':
                    print("⚠️ 检测到SKIP_POSTGIS_CHECK环境变量，将继续但可能出现问题")
                    return
                
                raise Exception("PostgreSQL数据库中未安装PostGIS扩展，请先安装PostGIS扩展")
            
            # 尝试获取PostGIS版本
            try:
                cursor.execute("SELECT postgis_version()")
                version = cursor.fetchone()[0]
                print(f"✅ PostGIS扩展已安装，版本: {version}")
            except:
                try:
                    cursor.execute("SELECT PostGIS_Version()")
                    version = cursor.fetchone()[0]
                    print(f"✅ PostGIS扩展已安装，版本: {version}")
                except:
                    print("⚠️ 无法获取PostGIS版本信息，但扩展已安装")
            
        except Exception as e:
            if "未安装PostGIS扩展" in str(e):
                raise e
            else:
                print(f"⚠️ 无法获取PostGIS版本信息: {str(e)}")
                print("继续处理，但可能会在后续步骤出现问题")
        finally:
            if conn:
                conn.close()
    
    def _drop_table_if_exists(self, table_name, conn=None):
        """如果表存在则删除"""
        close_conn = False
        if conn is None:
            conn = self.get_connection()
            close_conn = True
        
        try:
            cursor = conn.cursor()
            drop_table_sql = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                sql.Identifier(table_name)
            )
            cursor.execute(drop_table_sql)
            conn.commit()
            print(f"✅ 表 {table_name} 已删除（如果存在）")
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ 删除表失败: {str(e)}")
            raise
        finally:
            if close_conn and conn:
                conn.close()
    
    def get_table_info(self, table_name):
        """获取表信息"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 获取表结构
            table_info_sql = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            """
            cursor.execute(table_info_sql, (table_name,))
            columns = cursor.fetchall()
            
            # 获取几何字段信息
            geom_info_sql = """
            SELECT f_geometry_column, srid, type 
            FROM geometry_columns 
            WHERE f_table_name = %s AND f_table_schema = 'public'
            """
            cursor.execute(geom_info_sql, (table_name,))
            geom_info = cursor.fetchone()
            
            # 获取要素数量
            count_sql = sql.SQL("SELECT COUNT(*) as count FROM {}").format(
                sql.Identifier(table_name)
            )
            cursor.execute(count_sql)
            count_result = cursor.fetchone()
            
            # 构建结果
            result = {
                "table_name": table_name,
                "schema": "public",
                "full_table_name": f"public.{table_name}",
                "columns": columns,
                "geometry_info": geom_info,
                "feature_count": count_result['count'] if count_result else 0
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 获取表信息失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close() 