#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import uuid
import zipfile
import tempfile
import shutil
import geopandas as gpd
from pathlib import Path
from models.db import execute_query
from sqlalchemy import create_engine, text
from config import DB_CONFIG, MARTIN_CONFIG

class VectorMartinService:
    """统一的矢量Martin服务类，处理GeoJSON和SHP文件的Martin服务发布"""
    
    def __init__(self):
        """初始化服务"""
        # 构建PostgreSQL连接字符串
        self.db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        self.engine = create_engine(self.db_url)
        
    def publish_geojson_martin(self, file_id, file_path, original_filename, user_id=None):
        """发布GeoJSON文件为Martin服务
        
        Args:
            file_id: 文件ID
            file_path: GeoJSON文件路径
            original_filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            发布结果字典
        """
        try:
            # 读取GeoJSON文件
            print(f"正在读取GeoJSON文件: {file_path}")
            gdf = gpd.read_file(file_path)
            
            # 生成PostGIS表名
            table_name = f"vector_{uuid.uuid4().hex[:8]}"
            
            # 将数据导入PostGIS，使用vector前缀
            print(f"正在将数据导入PostGIS表: {table_name}")
            gdf.to_postgis(
                name=table_name,
                con=self.engine,
                if_exists='replace',
                index=False
            )
            
            # 为表创建空间索引
            with self.engine.connect() as conn:
                # 创建空间索引
                index_sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_geom ON {table_name} USING GIST (geometry)"
                conn.execute(text(index_sql))
                conn.commit()
                
                print(f"✅ 空间索引创建成功: idx_{table_name}_geom")
            
            # 构建Martin服务URL
            service_url = f"{MARTIN_CONFIG['base_url']}/{table_name}"
            mvt_url = f"{service_url}/{{z}}/{{x}}/{{y}}.pbf"  # 移除.pbf后缀
            tilejson_url = service_url  # TileJSON URL就是service_url，不需要.json后缀
            
            # 收集GeoJSON信息
            geojson_info = {
                'total_features': len(gdf),
                'columns': list(gdf.columns),
                'geometry_types': gdf.geometry.geom_type.unique().tolist(),
                'crs': str(gdf.crs) if gdf.crs else None,
                'bounds': gdf.total_bounds.tolist() if not gdf.empty else None
            }
            
            # 收集PostGIS信息
            postgis_info = {
                'table_name': table_name,
                'geometry_column': 'geometry',
                'srid': gdf.crs.to_epsg() if gdf.crs else 4326
            }
            
            # 保存服务信息到数据库
            insert_sql = """
            INSERT INTO vector_martin_services 
            (file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, vector_info, postgis_info, user_id)
            VALUES (%(file_id)s, %(original_filename)s, %(file_path)s, %(vector_type)s, %(table_name)s, %(service_url)s, %(mvt_url)s, %(tilejson_url)s, %(vector_info)s, %(postgis_info)s, %(user_id)s)
            RETURNING id
            """
            
            params = {
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': file_path,
                'vector_type': 'geojson',
                'table_name': table_name,
                'service_url': service_url,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
                'vector_info': json.dumps(geojson_info),
                'postgis_info': json.dumps(postgis_info),
                'user_id': user_id
            }
            
            result = execute_query(insert_sql, params)
            service_id = result[0]['id']
            
            print(f"✅ GeoJSON Martin服务发布成功，服务ID: {service_id}")
            
            return {
                'success': True,
                'service_id': service_id,
                'table_name': table_name,
                'service_url': service_url,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
                'vector_info': geojson_info,
                'postgis_info': postgis_info
            }
            
        except Exception as e:
            print(f"❌ GeoJSON Martin服务发布失败: {str(e)}")
            # 清理可能创建的表
            try:
                if 'table_name' in locals():
                    with self.engine.connect() as conn:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        conn.commit()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def publish_shp_martin(self, file_id, zip_file_path, original_filename, user_id=None):
        """发布SHP压缩包为Martin服务
        
        Args:
            file_id: 文件ID
            zip_file_path: SHP压缩包路径
            original_filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            发布结果字典
        """
        temp_dir = None
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            print(f"临时目录: {temp_dir}")
            
            # 解压ZIP文件
            print(f"正在解压SHP文件: {zip_file_path}")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找.shp文件
            shp_files = list(Path(temp_dir).rglob('*.shp'))
            if not shp_files:
                raise Exception("压缩包中未找到.shp文件")
            
            shp_file = shp_files[0]
            print(f"找到SHP文件: {shp_file}")
            
            # 读取SHP文件
            print("正在读取SHP文件...")
            gdf = gpd.read_file(str(shp_file))
            
            # 确保有几何列和数据
            if gdf.empty:
                raise Exception("SHP文件中没有数据")
            
            if gdf.geometry is None or len(gdf.geometry) == 0:
                raise Exception("SHP文件中没有几何列")
            
            # 检查是否有有效的几何数据
            valid_geoms = gdf.geometry.notna()
            if not valid_geoms.any():
                raise Exception("SHP文件中没有有效的几何数据")
            
            # 过滤掉无效的几何数据
            gdf = gdf[valid_geoms]
            
            # 转换坐标系为WGS84（如果需要）
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                print(f"正在转换坐标系从 {gdf.crs} 到 EPSG:4326")
                gdf = gdf.to_crs(epsg=4326)
            
            # 生成PostGIS表名，使用vector前缀
            table_name = f"vector_{uuid.uuid4().hex[:8]}"
            
            # 将数据导入PostGIS，使用vector前缀
            print(f"正在将数据导入PostGIS表: {table_name}")
            gdf.to_postgis(
                name=table_name,
                con=self.engine,
                if_exists='replace',
                index=False
            )
            
            # 为表创建空间索引
            with self.engine.connect() as conn:
                # 创建空间索引
                index_sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_geom ON {table_name} USING GIST (geometry)"
                conn.execute(text(index_sql))
                conn.commit()
                
                print(f"✅ 空间索引创建成功: idx_{table_name}_geom")
            
            # 构建Martin服务URL
            service_url = f"{MARTIN_CONFIG['base_url']}/{table_name}"
            mvt_url = f"{service_url}/{{z}}/{{x}}/{{y}}"  # 移除.pbf后缀
            tilejson_url = service_url  # TileJSON URL就是service_url，不需要.json后缀
            
            # 收集SHP信息
            shp_info = {
                'total_features': len(gdf),
                'columns': list(gdf.columns),
                'geometry_types': gdf.geometry.geom_type.unique().tolist(),
                'crs': str(gdf.crs) if gdf.crs else None,
                'bounds': gdf.total_bounds.tolist() if not gdf.empty else None,
                'original_shp_file': shp_file.name
            }
            
            # 收集PostGIS信息
            postgis_info = {
                'table_name': table_name,
                'geometry_column': 'geometry',
                'srid': gdf.crs.to_epsg() if gdf.crs else 4326
            }
            
            # 保存服务信息到数据库
            insert_sql = """
            INSERT INTO vector_martin_services 
            (file_id, original_filename, file_path, vector_type, table_name, service_url, mvt_url, tilejson_url, vector_info, postgis_info, user_id)
            VALUES (%(file_id)s, %(original_filename)s, %(file_path)s, %(vector_type)s, %(table_name)s, %(service_url)s, %(mvt_url)s, %(tilejson_url)s, %(vector_info)s, %(postgis_info)s, %(user_id)s)
            RETURNING id
            """
            
            params = {
                'file_id': file_id,
                'original_filename': original_filename,
                'file_path': zip_file_path,
                'vector_type': 'shp',
                'table_name': table_name,
                'service_url': service_url,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
                'vector_info': json.dumps(shp_info),
                'postgis_info': json.dumps(postgis_info),
                'user_id': user_id
            }
            
            result = execute_query(insert_sql, params)
            service_id = result[0]['id']
            
            print(f"✅ SHP Martin服务发布成功，服务ID: {service_id}")
            
            return {
                'success': True,
                'service_id': service_id,
                'table_name': table_name,
                'service_url': service_url,
                'mvt_url': mvt_url,
                'tilejson_url': tilejson_url,
                'vector_info': shp_info,
                'postgis_info': postgis_info
            }
            
        except Exception as e:
            print(f"❌ SHP Martin服务发布失败: {str(e)}")
            # 清理可能创建的表
            try:
                if 'table_name' in locals():
                    with self.engine.connect() as conn:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        conn.commit()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
            
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"✅ 临时目录已清理: {temp_dir}")
                except Exception as e:
                    print(f"⚠️ 清理临时目录失败: {e}")
    
    def get_martin_services(self, vector_type=None, status='active'):
        """获取Martin服务列表
        
        Args:
            vector_type: 矢量类型过滤 ('geojson', 'shp', None)
            status: 状态过滤
            
        Returns:
            服务列表
        """
        sql = """
        SELECT * FROM vector_martin_services
        WHERE status = %(status)s
        """
        
        params = {'status': status}
        
        if vector_type:
            sql += " AND vector_type = %(vector_type)s"
            params['vector_type'] = vector_type
        
        sql += " ORDER BY created_at DESC"
        
        return execute_query(sql, params)
    
    def get_martin_service_by_id(self, service_id):
        """根据ID获取Martin服务信息
        
        Args:
            service_id: 服务ID
            
        Returns:
            服务信息
        """
        sql = """
        SELECT * FROM vector_martin_services
        WHERE id = %(service_id)s AND status = 'active'
        """
        
        result = execute_query(sql, {'service_id': service_id})
        return result[0] if result else None
    
    def delete_martin_service(self, service_id):
        """删除Martin服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            删除是否成功
        """
        try:
            # 获取服务信息
            service = self.get_martin_service_by_id(service_id)
            if not service:
                return False
            
            table_name = service['table_name']
            
            # 删除PostGIS表
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
                print(f"✅ PostGIS表已删除: {table_name}")
            
            # 更新服务状态为已删除
            sql = """
            UPDATE vector_martin_services
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE id = %(service_id)s
            """
            
            execute_query(sql, {'service_id': service_id}, fetch=False)
            print(f"✅ Martin服务已删除: {service_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 删除Martin服务失败: {str(e)}")
            return False 