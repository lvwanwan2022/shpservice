#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import json
import zipfile
import shutil
import tempfile
import time
from config import GEOSERVER_CONFIG
from models.db import execute_query

class GeoServerService:
    """GeoServer服务类，用于管理GeoServer资源"""
    
    def __init__(self):
        self.url = GEOSERVER_CONFIG['url']
        self.user = GEOSERVER_CONFIG['user']
        self.password = GEOSERVER_CONFIG['password']
        self.workspace = GEOSERVER_CONFIG['workspace']
        self.rest_url = f"{self.url}/rest"
        self.auth = (self.user, self.password)
        
        # 确保工作空间存在
        self._ensure_workspace_exists()
    
    def _ensure_workspace_exists(self):
        """确保工作空间存在"""
        try:
            # 检查数据库中的工作空间
            workspace_sql = "SELECT id FROM geoserver_workspaces WHERE name = %s"
            workspace_result = execute_query(workspace_sql, (self.workspace,))
            
            if not workspace_result:
                # 在GeoServer中创建工作空间
                self._create_workspace_in_geoserver()
                
                # 在数据库中记录工作空间
                insert_workspace_sql = """
                INSERT INTO geoserver_workspaces (name, namespace_uri, namespace_prefix, description, is_default)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """
                result = execute_query(insert_workspace_sql, (
                    self.workspace,
                    f"http://{self.workspace}",
                    self.workspace,
                    f"Workspace for {self.workspace}",
                    True
                ))
                workspace_id = result[0]['id']
                print(f"工作空间 {self.workspace} 创建成功，ID: {workspace_id}")
                return workspace_id
            else:
                workspace_id = workspace_result[0]['id']
                print(f"工作空间 {self.workspace} 已存在，ID: {workspace_id}")
                return workspace_id
                
        except Exception as e:
            error_msg = f"确保工作空间存在失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _create_workspace_in_geoserver(self):
        """在GeoServer中创建工作空间"""
        headers = {'Content-type': 'application/json'}
        workspace_url = f"{self.rest_url}/workspaces"
        
        # 检查工作空间是否存在
        check_url = f"{self.rest_url}/workspaces/{self.workspace}"
        response = requests.get(check_url, auth=self.auth)
        
        if response.status_code != 200:
            # 创建工作空间
            workspace_data = {
                "workspace": {
                    "name": self.workspace
                }
            }
            response = requests.post(
                workspace_url, 
                data=json.dumps(workspace_data), 
                headers=headers, 
                auth=self.auth
            )
            
            if response.status_code not in [201, 200]:
                raise Exception(f"创建工作空间失败: {response.text}")
    
    def publish_shapefile(self, shp_zip_path, store_name, file_id):
        """发布Shapefile服务
        
        注意：每次发布都会创建一个新的store，store名称格式为"文件名_store"
        
        Args:
            shp_zip_path: Shapefile ZIP包路径
            store_name: 数据存储名称（将被重新生成为"文件名_store"格式）
            file_id: 文件ID
            
        Returns:
            发布结果信息
        """
        try:
            print(f"开始发布Shapefile: {shp_zip_path}")
            
            # 修复文件路径问题
            corrected_path = self._correct_path(shp_zip_path)
            print(f"修正后的文件路径: {corrected_path}")
            
            # 确保是zip文件
            if not corrected_path.endswith('.zip'):
                raise ValueError("Shapefile必须是zip格式")
            
            # 根据文件名生成store名称（文件名_store格式）
            import os
            filename = os.path.splitext(os.path.basename(corrected_path))[0]
            # 清理文件名，只保留字母、数字、下划线和中划线
            import re
            clean_filename = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '_', filename)
            generated_store_name = f"{clean_filename}_store"
            print(f"自动生成的存储名称: {generated_store_name}")
            
            # 从ZIP文件中提取SHP文件
            shp_name = self._extract_shp_name_from_zip(corrected_path)
            if not shp_name:
                shp_name = generated_store_name
            
            print(f"预期的Shapefile图层名称: {shp_name}")
            
            # 获取工作空间ID
            workspace_id = self._get_workspace_id()
            
            # 1. 创建数据存储
            store_id = self._create_datastore_in_db(generated_store_name, workspace_id, 'Shapefile', file_id)
            
            # 2. 上传Shapefile到GeoServer
            self._upload_shapefile_to_geoserver(corrected_path, generated_store_name)
            
            # 3. 等待GeoServer处理
            time.sleep(3)
            
            # 4. 获取实际的要素类型信息
            featuretype_info = self._get_featuretype_info(generated_store_name, shp_name)
            
            # 5. 在数据库中创建要素类型记录
            featuretype_id = self._create_featuretype_in_db(featuretype_info, store_id)
            
            # 6. 在数据库中创建图层记录
            layer_info = self._create_layer_in_db(featuretype_info, workspace_id, featuretype_id, file_id, 'datastore')
            
            # 7. 返回服务信息
            return {
                "success": True,
                "store_name": generated_store_name,  # 返回生成的store名称
                "layer_name": layer_info['full_name'],
                "wms_url": layer_info['wms_url'],
                "wfs_url": layer_info['wfs_url'],
                "layer_info": layer_info,
                "filename": filename
            }
            
        except Exception as e:
            print(f"发布Shapefile失败: {str(e)}")
            # 清理可能创建的资源
            cleanup_store_name = generated_store_name if 'generated_store_name' in locals() else store_name
            self._cleanup_failed_publish(cleanup_store_name, 'datastore')
            raise Exception(f"发布Shapefile失败: {str(e)}")
    
    def publish_geotiff(self, tif_path, store_name, file_id):
        """发布GeoTIFF服务
        
        注意：每次发布都会创建一个新的store，store名称格式为"文件名_store"
        
        Args:
            tif_path: GeoTIFF文件路径
            store_name: 数据存储名称（将被重新生成为"文件名_store"格式）
            file_id: 文件ID
            
        Returns:
            发布结果信息
        """
        try:
            print(f"开始发布GeoTIFF: {tif_path}")
            
            # 修复文件路径问题
            corrected_path = self._correct_path(tif_path)
            print(f"修正后的文件路径: {corrected_path}")
            
            # 根据文件名生成store名称（文件名_store格式）
            import os
            filename = os.path.splitext(os.path.basename(corrected_path))[0]
            # 清理文件名，只保留字母、数字、下划线和中划线
            import re
            clean_filename = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '_', filename)
            generated_store_name = f"{clean_filename}_store"
            print(f"自动生成的存储名称: {generated_store_name}")
            
            # 获取工作空间ID
            workspace_id = self._get_workspace_id()
            
            # 1. 创建覆盖存储记录
            store_id = self._create_coveragestore_in_db(generated_store_name, workspace_id, 'GeoTIFF', file_id)
            print(f"✅ 覆盖存储记录创建成功，store_id={store_id}")
            
            # 2. 上传GeoTIFF到GeoServer
            self._upload_geotiff_to_geoserver(corrected_path, generated_store_name)
            print(f"✅ GeoTIFF已上传到GeoServer")
            
            # 3. 等待GeoServer处理
            time.sleep(3)
            
            # 4. 获取覆盖信息
            coverage_info = self._get_coverage_info(generated_store_name)
            print(f"✅ 获取覆盖信息成功")
            
            # 5. 在数据库中创建覆盖图层记录
            layer_info = self._create_layer_in_db(coverage_info, workspace_id, store_id, file_id, 'coveragestore')
            print(f"✅ 覆盖图层记录创建成功，layer_id={layer_info['id']}")
            
            # 6. 返回服务信息
            return {
                "success": True,
                "store_name": generated_store_name,  # 返回生成的store名称
                "layer_name": layer_info['full_name'],
                "wms_url": layer_info['wms_url'],
                "layer_info": layer_info,
                "filename": filename
            }
            
        except Exception as e:
            print(f"发布GeoTIFF失败: {str(e)}")
            # 清理可能创建的资源
            cleanup_store_name = generated_store_name if 'generated_store_name' in locals() else store_name
            self._cleanup_failed_publish(cleanup_store_name, 'coveragestore')
            raise Exception(f"发布GeoTIFF失败: {str(e)}")
    
    def publish_geojson(self, geojson_path, store_name, file_id):
        """发布GeoJSON服务 - 通过PostGIS数据库
        
        采用GeoServer官方推荐的最佳实践：
        1. 验证GeoJSON文件
        2. 将GeoJSON数据导入PostGIS数据库
        3. 在数据库中创建store记录
        4. 创建PostGIS数据源（包含完整连接参数）
        5. 从PostGIS发布要素类型
        6. 创建featuretype和layer数据库记录
        7. 验证发布结果
        
        支持混合几何类型：当GeoJSON包含多种几何类型时，
        会自动分离为多个表和图层
        
        Args:
            geojson_path: GeoJSON文件路径
            store_name: 数据存储名称（将被重新生成为"文件名_store"格式）
            file_id: 文件ID
            
        Returns:
            发布结果信息
        """
        try:
            print(f"\n=== 开始发布GeoJSON服务（PostGIS方案） ===")
            print(f"文件路径: {geojson_path}")
            print(f"文件ID: {file_id}")
            
            # 1. 修正和验证文件路径
            corrected_path = self._correct_path(geojson_path)
            print(f"修正后的文件路径: {corrected_path}")
            
            # 2. 根据文件名生成store名称（文件名_store格式）
            import os
            filename = os.path.splitext(os.path.basename(corrected_path))[0]
            # 清理文件名，只保留字母、数字、下划线和中划线
            import re
            clean_filename = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '_', filename)
            generated_store_name = f"{clean_filename}_store"
            print(f"自动生成的存储名称: {generated_store_name}")
            
            # 3. 验证GeoJSON文件格式
            self._validate_geojson_file(corrected_path)
            print("✅ GeoJSON文件格式验证通过")
            
            # 4. 获取工作空间ID
            workspace_id = self._get_workspace_id()
            print(f"工作空间ID: {workspace_id}")
            
            # 5. 将GeoJSON导入PostGIS数据库
            print("\n--- 将GeoJSON导入PostGIS数据库 ---")
            from services.postgis_service import PostGISService
            postgis_service = PostGISService()
            
            postgis_result = postgis_service.store_geojson(corrected_path, file_id)
            print(f"✅ GeoJSON已导入到PostGIS")
            
            # 6. 检查是否为混合几何类型
            if postgis_result.get('is_mixed', False):
                print(f"🔄 处理混合几何类型，发现 {len(postgis_result['geometry_types'])} 种几何类型: {postgis_result['geometry_types']}")
                # 新方案：混合几何类型也使用单一表，不需要特殊处理
                table_name = postgis_result['table_name']
                print(f"📊 混合几何类型，处理表: {table_name}")
                result = self._handle_single_geometry_publishing(
                    postgis_result, generated_store_name, workspace_id, file_id, filename, table_name
                )
                # 添加混合几何类型标记
                result['is_mixed'] = True
                result['geometry_types'] = postgis_result['geometry_types']
            else:
                # 单一几何类型，按原流程处理
                table_name = postgis_result['table_name']
                print(f"📊 单一几何类型，处理表: {table_name}")
                result = self._handle_single_geometry_publishing(
                    postgis_result, generated_store_name, workspace_id, file_id, filename, table_name
                )
            
            print(f"\n✅ GeoJSON服务发布成功!")
            return result
            
        except Exception as e:
            print(f"❌ 发布GeoJSON服务失败: {str(e)}")
            
            # 清理可能创建的资源
            try:
                print("开始清理可能创建的资源...")
                cleanup_store_name = generated_store_name if 'generated_store_name' in locals() else store_name
                # 新方案：无论是否为混合几何类型，都只有一个表需要清理
                tables_to_cleanup = []
                if 'postgis_result' in locals() and postgis_result:
                    table_name = postgis_result.get('table_name')
                    if table_name:
                        tables_to_cleanup.append(table_name)
                
                for table_name in tables_to_cleanup:
                    self._cleanup_failed_geojson_publish(cleanup_store_name, table_name)
                    
            except Exception as cleanup_error:
                print(f"⚠️ 清理资源失败: {str(cleanup_error)}")
            
            import traceback
            traceback.print_exc()
            raise Exception(f"发布GeoJSON服务失败: {str(e)}")
    
    def _handle_single_geometry_publishing(self, postgis_result, store_name, workspace_id, file_id, filename, table_name):
        """处理单一几何类型的发布
        
        Args:
            postgis_result: PostGIS处理结果
            store_name: store名称
            workspace_id: 工作空间ID
            file_id: 文件ID
            filename: 原始文件名
            table_name: 表名
            
        Returns:
            发布结果信息
        """
        print(f"\n--- 处理单一几何类型发布: {table_name} ---")
        
        # 1. 在数据库中创建数据存储记录（必须在GeoServer操作之前）
        print("--- 创建数据库store记录 ---")
        store_id = self._create_datastore_in_db(store_name, workspace_id, 'PostGIS', file_id)
        print(f"✅ 数据存储记录创建成功，store_id={store_id}")
        
        # 2. 在GeoServer中创建PostGIS数据源
        print("--- 创建PostGIS数据源 ---")
        self._create_postgis_datastore(store_name)
        print(f"✅ PostGIS数据源创建成功: {store_name}")
        
        # 3. 从PostGIS发布要素类型
        print("--- 发布要素类型 ---")
        featuretype_info = self._publish_featuretype_from_postgis(
            store_name, 
            table_name, 
            table_name  # 使用表名作为要素类型名称
        )
        print(f"✅ 要素类型发布成功: {featuretype_info['featureType']['name']}")
        
        # 4. 在数据库中创建要素类型和图层记录
        print("--- 创建数据库featuretype和layer记录 ---")
        
        # 创建要素类型记录
        featuretype_id = self._create_featuretype_in_db(featuretype_info, store_id)
        print(f"✅ 要素类型记录创建成功，featuretype_id={featuretype_id}")
        
        # 创建图层记录
        layer_info = self._create_layer_in_db(featuretype_info, workspace_id, featuretype_id, file_id, 'datastore')
        print(f"✅ 图层记录创建成功，layer_id={layer_info['id']}")
        
        # 5. 验证发布结果
        print("--- 验证发布结果 ---")
        full_layer_name = layer_info['full_name']
        if self.verify_layer_exists(full_layer_name):
            print(f"✅ 图层验证成功: {full_layer_name}")
        else:
            print(f"⚠️ 图层验证失败，但将继续: {full_layer_name}")
        
        # 6. 构建返回结果
        result = {
            "success": True,
            "is_mixed": False,
            "store_name": store_name,
            "layer_name": full_layer_name,
            "wms_url": layer_info['wms_url'],
            "wfs_url": layer_info['wfs_url'],
            "layer_info": layer_info,
            "postgis_table": table_name,
            "filename": filename,
            "geometry_type": postgis_result['feature_info']['geometry_type'],
            "feature_count": postgis_result['feature_info']['feature_count'],
            "preview_url": f"{self.url}/wms?service=WMS&version=1.1.0&request=GetMap&layers={full_layer_name}&styles=&bbox=-180,-90,180,90&width=768&height=384&srs=EPSG:4326&format=image/png"
        }
        
        print(f"   - 存储名称: {result['store_name']}")
        print(f"   - 图层名称: {result['layer_name']}")
        print(f"   - WMS服务: {result['wms_url']}")
        print(f"   - WFS服务: {result['wfs_url']}")
        print(f"   - PostGIS表: {result['postgis_table']}")
        
        return result
    
    def _correct_path(self, file_path):
        """修正文件路径，处理跨平台路径分隔符"""
        import os
        
        print(f"原始路径: {file_path}")
        
        # 将所有反斜杠替换为正斜杠（兼容性处理）
        corrected_path = file_path.replace('\\', '/')
        print(f"替换分隔符后: {corrected_path}")
        
        # 标准化路径
        normalized_path = os.path.normpath(corrected_path)
        print(f"标准化路径 {normalized_path}")
        
        # 检查文件是否存在
        if os.path.exists(normalized_path):
            print(f"文件存在: {normalized_path}")
            return normalized_path
        else:
            print(f"文件不存在 {normalized_path}")
            # 如果标准化路径不存在，尝试使用原始路径的标准化版本
            alt_path = os.path.normpath(file_path)
            print(f"尝试备用路径: {alt_path}")
            if os.path.exists(alt_path):
                print(f"备用路径存在: {alt_path}")
                return alt_path
            else:
                print(f"备用路径也不存在: {alt_path}")
                raise FileNotFoundError(f"无法找到文件: {file_path}")
        
        return normalized_path
    
    def _get_workspace_id(self):
        """获取工作空间ID"""
        sql = "SELECT id FROM geoserver_workspaces WHERE name = %s"
        result = execute_query(sql, (self.workspace,))
        if not result:
            raise Exception(f"工作空间 {self.workspace} 不存在")
        return result[0]['id']
    
    def _create_datastore_in_db(self, store_name, workspace_id, data_type, file_id):
        """在数据库中创建数据存储记录
        
        注意：每次都会创建新的store，如果存在同名store则先删除
        """
        try:
            # 检查是否已存在同名的数据存储，如果存在则删除
            check_sql = """
            SELECT id FROM geoserver_stores 
            WHERE name = %s AND workspace_id = %s
            """
            existing_result = execute_query(check_sql, (store_name, workspace_id))
            
            if existing_result:
                existing_store_id = existing_result[0]['id']
                print(f"⚠️ 发现同名数据存储 '{store_name}'，将先删除旧记录，store_id={existing_store_id}")
                
                # 删除相关的图层记录
                delete_layers_sql = "DELETE FROM geoserver_layers WHERE store_id = %s"
                execute_query(delete_layers_sql, (existing_store_id,), fetch=False)
                print("🗑️ 已删除相关图层记录")
                
                # 删除相关的要素类型记录
                delete_featuretypes_sql = "DELETE FROM geoserver_featuretypes WHERE store_id = %s"
                execute_query(delete_featuretypes_sql, (existing_store_id,), fetch=False)
                print("🗑️ 已删除相关要素类型记录")
                
                # 删除数据存储记录
                delete_store_sql = "DELETE FROM geoserver_stores WHERE id = %s"
                execute_query(delete_store_sql, (existing_store_id,), fetch=False)
                print("🗑️ 已删除旧的数据存储记录")
            
            # 检查file_id是否在files表中存在
            file_exists = False
            if file_id:
                try:
                    check_file_sql = "SELECT id FROM files WHERE id = %s"
                    file_result = execute_query(check_file_sql, (file_id,))
                    file_exists = bool(file_result)
                except Exception as e:
                    print(f"⚠️ 无法检查file_id={file_id}是否存在: {str(e)}")
                    file_exists = False
            
            # 创建新的数据存储记录，如果file_id不存在则设为NULL
            if file_exists:
                sql = """
                INSERT INTO geoserver_stores (name, workspace_id, store_type, data_type, file_id, enabled)
                VALUES (%s, %s, 'datastore', %s, %s, TRUE)
                RETURNING id
                """
                result = execute_query(sql, (store_name, workspace_id, data_type, file_id))
                print(f"✅ 数据存储记录创建成功，关联file_id={file_id}")
            else:
                sql = """
                INSERT INTO geoserver_stores (name, workspace_id, store_type, data_type, file_id, enabled)
                VALUES (%s, %s, 'datastore', %s, NULL, TRUE)
                RETURNING id
                """
                result = execute_query(sql, (store_name, workspace_id, data_type))
                print(f"✅ 数据存储记录创建成功，file_id为NULL（测试模式或文件不存在）")
            
            store_id = result[0]['id']
            print(f"✅ 新数据存储记录创建成功，store_id={store_id}")
            return store_id
            
        except Exception as e:
            print(f"❌ 创建数据存储记录失败: {str(e)}")
            raise Exception(f"创建数据存储记录失败: {str(e)}")
    
    def _create_coveragestore_in_db(self, store_name, workspace_id, data_type, file_id):
        """在数据库中创建覆盖存储记录"""
        sql = """
        INSERT INTO geoserver_stores (name, workspace_id, store_type, data_type, file_id, enabled)
        VALUES (%s, %s, 'coveragestore', %s, %s, TRUE)
        RETURNING id
        """
        result = execute_query(sql, (store_name, workspace_id, data_type, file_id))
        return result[0]['id']
    
    def publish_dwg_dxf(self, file_path, store_name, coord_system):
        """发布DWG/DXF服务
        
        Args:
            file_path: DWG/DXF文件路径
            store_name: 数据存储名称
            coord_system: 坐标系统(如EPSG:4326")
            
        Returns:
            服务URL
        """
        # 暂时不支持DWG/DXF格式的直接发布到GeoServer，需要外部工具进行格式转换
        raise Exception("DWG/DXF格式暂时不支持自动发布到GeoServer，请先转换为Shapefile或GeoJSON格式")
    
    def delete_layer(self, store_name, store_type="datastore"):
        """删除图层
        
        Args:
            store_name: 数据存储名称
            store_type: 存储类型(datastore或coveragestore)
        """
        if store_type == "datastore":
            url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}?recurse=true"
        else:
            url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}?recurse=true"
        
        response = requests.delete(url, auth=self.auth)
        
        if response.status_code not in [200, 404]:
            raise Exception(f"删除图层失败: {response.text}")
        
        return True
    
    def unpublish_layer(self, layer_id):
        """取消发布图层
        
        Args:
            layer_id: 图层ID
        
        Returns:
            bool: 取消发布结果
        """
        try:
            print(f"开始取消发布图层: layer_id={layer_id}")
            
            # 1. 从数据库获取图层信息
            layer_sql = """
            SELECT gl.*, gs.name as store_name, gs.data_type as store_type 
            FROM geoserver_layers gl 
            LEFT JOIN geoserver_featuretypes gf ON gl.featuretype_id = gf.id 
            LEFT JOIN geoserver_stores gs ON gf.store_id = gs.id 
            WHERE gl.id = %s
            UNION
            SELECT gl.*, gcs.name as store_name, gcs.data_type as store_type 
            FROM geoserver_layers gl 
            LEFT JOIN geoserver_coverages gc ON gl.coverage_id = gc.id 
            LEFT JOIN geoserver_stores gcs ON gc.store_id = gcs.id 
            WHERE gl.id = %s
            """
            layer_result = execute_query(layer_sql, (layer_id, layer_id))
            
            if not layer_result:
                print(f"⚠️ 图层不存在: layer_id={layer_id}")
                return False
            
            layer_info = layer_result[0]
            store_name = layer_info.get('store_name')
            store_type = layer_info.get('store_type', 'Shapefile')
            layer_name = layer_info.get('name')
            
            print(f"图层信息: name={layer_name}, store_name={store_name}, store_type={store_type}")
            
            # 2. 从GeoServer中删除图层和数据存储
            if store_name:
                # 根据存储类型确定删除的URL
                if store_type in ['GeoTIFF', 'WorldImage']:
                    # 栅格数据，使用coveragestore
                    delete_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}?recurse=true"
                else:
                    # 矢量数据，使用datastore
                    delete_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}?recurse=true"
                
                print(f"删除GeoServer资源: {delete_url}")
                response = requests.delete(delete_url, auth=self.auth)
                
                if response.status_code not in [200, 404]:
                    print(f"⚠️ 删除GeoServer资源失败: {response.status_code} - {response.text}")
                else:
                    print(f"✅ GeoServer资源删除成功")
            else:
                print(f"⚠️ 没有找到存储名称，跳过GeoServer删除")
            
            # 3. 从数据库中删除相关记录
            print(f"删除数据库记录...")
            
            # 删除图层记录
            delete_layer_sql = "DELETE FROM geoserver_layers WHERE id = %s"
            execute_query(delete_layer_sql, (layer_id,), fetch=False)
            print(f"✅ 删除图层记录: layer_id={layer_id}")
            
            # 删除相关的要素类型或覆盖记录
            if layer_info.get('featuretype_id'):
                delete_featuretype_sql = "DELETE FROM geoserver_featuretypes WHERE id = %s"
                execute_query(delete_featuretype_sql, (layer_info['featuretype_id'],), fetch=False)
                print(f"✅ 删除要素类型记录: featuretype_id={layer_info['featuretype_id']}")
            
            if layer_info.get('coverage_id'):
                delete_coverage_sql = "DELETE FROM geoserver_coverages WHERE id = %s"
                execute_query(delete_coverage_sql, (layer_info['coverage_id'],), fetch=False)
                print(f"✅ 删除覆盖记录: coverage_id={layer_info['coverage_id']}")
            
            # 检查是否有其他图层使用相同的存储，如果没有则删除存储记录
            if store_name:
                # 查找使用相同存储的其他图层
                check_store_usage_sql = """
                SELECT COUNT(*) as count FROM geoserver_layers gl 
                LEFT JOIN geoserver_featuretypes gf ON gl.featuretype_id = gf.id 
                LEFT JOIN geoserver_stores gs ON gf.store_id = gs.id 
                WHERE gs.name = %s
                UNION ALL
                SELECT COUNT(*) as count FROM geoserver_layers gl 
                LEFT JOIN geoserver_coverages gc ON gl.coverage_id = gc.id 
                LEFT JOIN geoserver_stores gcs ON gc.store_id = gcs.id 
                WHERE gcs.name = %s
                """
                usage_result = execute_query(check_store_usage_sql, (store_name, store_name))
                total_usage = sum(row['count'] for row in usage_result)
                
                if total_usage == 0:
                    # 没有其他图层使用此存储，可以删除存储记录
                    delete_store_sql = "DELETE FROM geoserver_stores WHERE name = %s"
                    execute_query(delete_store_sql, (store_name,), fetch=False)
                    print(f"✅ 删除存储记录: store_name={store_name}")
                else:
                    print(f"⚠️ 存储 {store_name} 仍被其他 {total_usage} 个图层使用，保留存储记录")
            
            print(f"✅ 图层取消发布成功: layer_id={layer_id}")
            return True
            
        except Exception as e:
            error_msg = f"取消发布图层失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_layer_info(self, layer_name):
        """获取图层信息
        
        Args:
            layer_name: 图层名称
            
        Returns:
            图层信息
        """
        url = f"{self.rest_url}/layers/{layer_name}"
        response = requests.get(url, auth=self.auth)
        
        if response.status_code != 200:
            raise Exception(f"获取图层信息失败: {response.text}")
        
        return response.json()
    
    def _get_actual_layer_name(self, store_name):
        """获取数据存储中的实际图层名称
        
        Args:
            store_name: 数据存储名称
            
        Returns:
            实际的图层名"""
        import time
        
        # 等待一下让GeoServer处理完成
        time.sleep(2)
        
        try:
            # 查询数据存储中的要素类型（图层）
            featuretypes_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/featuretypes.json"
            
            print(f"正在查询数据存储 {store_name} 的要素类型..")
            print(f"请求URL: {featuretypes_url}")
            
            response = requests.get(featuretypes_url, auth=self.auth)
            
            print(f"要素类型查询响应状态码: {response.status_code}")
            print(f"要素类型查询响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 获取要素类型列表
                if 'featureTypes' in data and 'featureType' in data['featureTypes']:
                    feature_types = data['featureTypes']['featureType']
                    
                    # 如果是列表，取第一个；如果是单个对象，直接使用
                    if isinstance(feature_types, list) and len(feature_types) > 0:
                        actual_name = feature_types[0]['name']
                        print(f"获取到实际图层名: {actual_name}")
                        return actual_name
                    elif isinstance(feature_types, dict):
                        actual_name = feature_types['name']
                        print(f"获取到实际图层名: {actual_name}")
                        return actual_name
                    else:
                        print(f"⚠️ 要素类型格式异常: {feature_types}")
                else:
                    print(f"⚠️ 响应中没有找到要素类型信息")
                    print(f"完整响应数据: {data}")
            else:
                print(f"查询要素类型失败，状态码: {response.status_code}")
                print(f"错误响应: {response.text}")
            
            # 如果无法获取实际名称，尝试直接使用store_name验证
            print(f"尝试使用store_name作为图层名称: {store_name}")
            test_layer_name = f"{self.workspace}:{store_name}"
            
            # 验证图层是否存在
            layer_info_url = f"{self.rest_url}/layers/{test_layer_name}.json"
            test_response = requests.get(layer_info_url, auth=self.auth)
            
            if test_response.status_code == 200:
                print(f"验证成功，使用store_name作为图层名称: {store_name}")
                return store_name
            else:
                print(f"使用store_name验证失败，状态码: {test_response.status_code}")
                
                # 尝试列出所有图层，看看是否有匹配的
                layers_url = f"{self.rest_url}/workspaces/{self.workspace}/layers.json"
                layers_response = requests.get(layers_url, auth=self.auth)
                
                if layers_response.status_code == 200:
                    layers_data = layers_response.json()
                    print(f"工作空间中的所有图层 {layers_data}")
                    
                    # 查找包含store_name的图层
                    if 'layers' in layers_data and 'layer' in layers_data['layers']:
                        layers = layers_data['layers']['layer']
                        if isinstance(layers, list):
                            for layer in layers:
                                layer_name = layer['name']
                                if store_name in layer_name or layer_name in store_name:
                                    print(f"找到匹配的图层: {layer_name}")
                                    return layer_name
                        elif isinstance(layers, dict):
                            layer_name = layers['name']
                            if store_name in layer_name or layer_name in store_name:
                                print(f"找到匹配的图层: {layer_name}")
                                return layer_name
            
            # 如果所有方法都失败，返回store_name作为最后的备份
            print(f"⚠️ 无法获取实际图层名称，使用store_name作为备份: {store_name}")
            return store_name
            
        except Exception as e:
            print(f"获取实际图层名称异常: {str(e)}")
            # 返回store_name作为备份
            return store_name
    
    def verify_layer_exists(self, layer_name):
        """验证图层是否存在并可访问
        
        Args:
            layer_name: 完整的图层名称（包含workspace"""
        import time
        
        # 等待一下让GeoServer处理完成
        time.sleep(1)
        
        try:
            print(f"开始验证图层: {layer_name}")
            
            # 方法1: 尝试获取图层信息
            layer_info_url = f"{self.rest_url}/layers/{layer_name}.json"
            print(f"验证URL: {layer_info_url}")
            
            response = requests.get(layer_info_url, auth=self.auth)
            print(f"图层信息查询响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"图层 {layer_name} 验证成功 (方法1: 图层信息)")
                return True
            else:
                print(f"⚠️ 图层信息查询失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
            
            # 方法2: 尝试通过WMS GetCapabilities验证
            print(f"尝试方法2: WMS GetCapabilities验证")
            wms_capabilities_url = f"{self.url}/wms?service=WMS&version=1.1.1&request=GetCapabilities"
            
            wms_response = requests.get(wms_capabilities_url, timeout=15)
            print(f"WMS Capabilities响应状态码: {wms_response.status_code}")
            
            if wms_response.status_code == 200:
                capabilities_text = wms_response.text
                if layer_name in capabilities_text:
                    print(f"图层 {layer_name} 在WMS Capabilities中找到")
                    return True
                else:
                    print(f"⚠️ 图层 {layer_name} 不在WMS Capabilities中")
                    
                    # 检查是否有类似的图层名
                    workspace = layer_name.split(':')[0] if ':' in layer_name else ''
                    if workspace and workspace in capabilities_text:
                        print(f"工作空间 {workspace} 存在于WMS Capabilities中")
                        
                        # 提取所有该工作空间的图层
                        import re
                        pattern = f'<Name>{workspace}:([^<]+)</Name>'
                        matches = re.findall(pattern, capabilities_text)
                        if matches:
                            print(f"工作空间中的图层: {matches}")
                            
                            # 检查是否有匹配的图层
                            target_layer = layer_name.split(':')[1] if ':' in layer_name else layer_name
                            for match in matches:
                                if target_layer in match or match in target_layer:
                                    print(f"找到相似图层: {workspace}:{match}")
                                    return True
                    else:
                        print(f"工作空间 {workspace} 不存在于WMS Capabilities中")
            else:
                print(f"WMS Capabilities请求失败，状态码: {wms_response.status_code}")
            
            # 方法3: 尝试直接WMS GetMap请求
            print(f"尝试方法3: WMS GetMap请求验证")
            wms_getmap_url = f"{self.url}/wms"
            params = {
                'service': 'WMS',
                'version': '1.1.1',
                'request': 'GetMap',
                'layers': layer_name,
                'styles': '',
                'bbox': '-180,-90,180,90',
                'width': '256',
                'height': '256',
                'srs': 'EPSG:4326',
                'format': 'image/png',
                'transparent': 'true'
            }
            
            getmap_response = requests.get(wms_getmap_url, params=params, timeout=15)
            print(f"WMS GetMap响应状态码: {getmap_response.status_code}")
            
            if getmap_response.status_code == 200:
                content_type = getmap_response.headers.get('content-type', '')
                print(f"WMS GetMap响应内容类型: {content_type}")
                
                if 'image' in content_type:
                    print(f"图层 {layer_name} WMS GetMap成功返回图片")
                    return True
                else:
                    print(f"⚠️ WMS GetMap返回非图片内容")
            else:
                print(f"WMS GetMap请求失败，状态码: {getmap_response.status_code}")
            
            print(f"所有验证方法都失败，图层{layer_name} 不存在或不可访问")
            return False
                
        except Exception as e:
            print(f"验证图层 {layer_name} 异常: {str(e)}")
            return False
    
    def _extract_shp_name_from_zip(self, zip_path):
        """从ZIP文件中提取SHP文件
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            SHP文件名（不含扩展名）
        """
        try:
            import zipfile
            import re
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"ZIP文件内容: {file_list}")
                
                # 查找.shp文件
                shp_files = [f for f in file_list if f.lower().endswith('.shp')]
                
                if shp_files:
                    # 取第一个shp文件
                    shp_file = shp_files[0]
                    # 提取文件名（不含路径和扩展名）
                    shp_name = os.path.splitext(os.path.basename(shp_file))[0]
                    print(f"从ZIP中提取的SHP文件: {shp_name}")
                    
                    # 如果文件名包含中文或特殊字符，需要进行清理
                    # 但保留原始名称用于显示，生成安全的英文名称用于GeoServer
                    original_name = shp_name
                    
                    # 检查是否包含中文字符或特殊字符
                    if re.search(r'[\u4e00-\u9fff]', shp_name) or any(char in shp_name for char in ['(', ')', ' ', '（', '）']):
                        print(f"检测到中文或特殊字符，原始文件名: {original_name}")
                        # 从ZIP文件路径生成安全的名称
                        zip_basename = os.path.splitext(os.path.basename(zip_path))[0]
                        # 清理文件名，只保留字母、数字、下划线和中划线
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', zip_basename)
                        print(f"生成安全的文件名: {safe_name}")
                        return safe_name
                    else:
                        return shp_name
                else:
                    print("ZIP文件中未找到.shp文件")
                    # 如果没找到shp文件，使用ZIP文件名
                    zip_basename = os.path.splitext(os.path.basename(zip_path))[0]
                    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', zip_basename)
                    print(f"使用ZIP文件名生成: {safe_name}")
                    return safe_name
                    
        except Exception as e:
            print(f"提取SHP文件名失败: {str(e)}")
            # 发生错误时，使用ZIP文件名作为备选
            try:
                zip_basename = os.path.splitext(os.path.basename(zip_path))[0]
                safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', zip_basename)
                print(f"错误处理：使用ZIP文件名: {safe_name}")
                return safe_name
            except:
                return "default_layer"
    
    def _upload_shapefile_to_geoserver(self, shp_zip_path, store_name):
        """上传Shapefile到GeoServer
        
        解决中文文件名导致的解压问题：
        1. 检查ZIP文件中是否含有中文文件名
        2. 如果有，重新打包ZIP文件，将中文文件名转换为英文
        3. 上传处理后的ZIP文件
        """
        import zipfile
        import tempfile
        import shutil
        import re
        
        print(f"准备上传Shapefile到GeoServer: {shp_zip_path}")
        
        try:
            # 检查ZIP文件内容
            with zipfile.ZipFile(shp_zip_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"原始ZIP文件内容: {file_list}")
                
                # 检查是否需要重新打包（包含中文字符或特殊字符）
                needs_repack = False
                for filename in file_list:
                    # 检查文件名是否包含中文字符或其他可能导致问题的字符
                    if re.search(r'[\u4e00-\u9fff]', filename) or any(char in filename for char in ['(', ')', ' ', '（', '）']):
                        needs_repack = True
                        break
                
                if needs_repack:
                    print("检测到中文文件名或特殊字符，需要重新打包ZIP文件")
                    
                    # 创建临时目录
                    with tempfile.TemporaryDirectory() as temp_dir:
                        print(f"创建临时目录: {temp_dir}")
                        
                        # 提取所有文件到临时目录并重命名
                        extracted_files = {}
                        base_name = store_name.replace('_store', '')  # 使用store名称作为基础文件名
                        
                        for original_name in file_list:
                            if original_name.endswith('/'):  # 跳过目录
                                continue
                                
                            # 提取文件
                            file_data = zip_file.read(original_name)
                            
                            # 获取文件扩展名
                            _, ext = os.path.splitext(original_name.lower())
                            
                            # 生成新的文件名（使用store名称 + 扩展名）
                            new_name = f"{base_name}{ext}"
                            new_path = os.path.join(temp_dir, new_name)
                            
                            # 写入文件
                            with open(new_path, 'wb') as f:
                                f.write(file_data)
                            
                            extracted_files[original_name] = new_name
                            print(f"重命名文件: {original_name} -> {new_name}")
                        
                        # 创建新的ZIP文件
                        new_zip_path = os.path.join(temp_dir, f"{base_name}_cleaned.zip")
                        with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                            for root, dirs, files in os.walk(temp_dir):
                                for file in files:
                                    if file.endswith('.zip'):  # 跳过我们正在创建的ZIP文件
                                        continue
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, temp_dir)
                                    new_zip.write(file_path, arcname)
                                    print(f"添加到新ZIP: {arcname}")
                        
                        print(f"创建清理后的ZIP文件: {new_zip_path}")
                        
                        # 使用新的ZIP文件上传
                        upload_zip_path = new_zip_path
                else:
                    print("ZIP文件无需重新打包")
                    upload_zip_path = shp_zip_path
            
            # 上传ZIP文件到GeoServer
            datastore_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/file.shp"
            headers = {'Content-type': 'application/zip'}
            
            with open(upload_zip_path, 'rb') as f:
                response = requests.put(
                    datastore_url,
                    data=f,
                    headers=headers,
                    auth=self.auth,
                    timeout=120  # 增加超时时间
                )
            
            print(f"Shapefile上传响应状态码: {response.status_code}")
            print(f"Shapefile上传响应内容: {response.text}")
            
            if response.status_code not in [201, 200]:
                raise Exception(f"上传Shapefile失败: {response.text}")
            
            print("✅ Shapefile上传成功")
            
        except Exception as e:
            print(f"❌ Shapefile上传失败: {str(e)}")
            raise e
    
    def _upload_geotiff_to_geoserver(self, tif_path, store_name):
        """上传GeoTIFF到GeoServer"""
        coveragestore_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}/file.geotiff"
        
        headers = {'Content-type': 'image/tiff'}
        with open(tif_path, 'rb') as f:
            response = requests.put(
                coveragestore_url,
                data=f,
                headers=headers,
                auth=self.auth
            )
        
        print(f"GeoTIFF上传响应状态码: {response.status_code}")
        print(f"GeoTIFF上传响应内容: {response.text}")
        
        if response.status_code not in [201, 200]:
            raise Exception(f"上传GeoTIFF失败: {response.text}")
    
    def _validate_geojson_file(self, geojson_path):
        """验证GeoJSON文件"""
        print(f"验证GeoJSON文件: {geojson_path}")
        
        # 验证文件是否存在
        if not os.path.exists(geojson_path):
            raise Exception(f"GeoJSON文件不存在: {geojson_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(geojson_path)
        print(f"文件大小: {file_size} 字节")
        
        if file_size == 0:
            raise Exception("GeoJSON文件为空")
        
        # 验证JSON格式和GeoJSON结构
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
                
                # 检查GeoJSON基本结构
                if not isinstance(geojson_data, dict):
                    raise Exception("GeoJSON必须是一个对象")
                
                geojson_type = geojson_data.get('type')
                if geojson_type not in ['FeatureCollection', 'Feature', 'Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']:
                    raise Exception(f"无效的GeoJSON类型: {geojson_type}")
                
                print(f"GeoJSON类型: {geojson_type}")
                
                # 如果是FeatureCollection，检查要素数量
                if geojson_type == 'FeatureCollection':
                    features = geojson_data.get('features', [])
                    print(f"要素数量: {len(features)}")
                    
                    if len(features) == 0:
                        print("⚠️ GeoJSON中没有要素")
                    
                print("GeoJSON格式验证通过")
                
        except json.JSONDecodeError as e:
            raise Exception(f"GeoJSON文件JSON格式无效: {e}")
        except Exception as e:
            if "无效的GeoJSON类型" in str(e) or "GeoJSON必须是一个对象" in str(e):
                raise e
            else:
                raise Exception(f"GeoJSON文件验证失败: {e}")
    
    def _cleanup_existing_datastore(self, store_name):
        """清理可能存在的数据存储"""
        try:
            check_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}"
            check_response = requests.get(check_url, auth=self.auth)
            
            if check_response.status_code == 200:
                print(f"数据存储 {store_name} 已存在，先删除")
                delete_response = requests.delete(f"{check_url}?recurse=true", auth=self.auth)
                if delete_response.status_code not in [200, 404]:
                    print(f"删除现有数据存储失败: {delete_response.text}")
                else:
                    print(f"删除现有数据存储成功")
                time.sleep(1)
        except Exception as e:
            print(f"清理现有数据存储失败: {e}")
    
    def _get_featuretype_info(self, store_name, featuretype_name):
        """获取要素类型信息"""
        url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/featuretypes/{featuretype_name}.json"
        print(f"获取要素类型信息URL: {url}")
        
        response = requests.get(url, auth=self.auth)
        
        print(f"获取要素类型信息响应状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"获取要素类型信息失败响应内容: {response.text}")
            # 更详细的错误信息
            error_message = f"获取要素类型信息失败: No such feature type: {self.workspace},{store_name},{featuretype_name}"
            print(f"错误信息: {error_message}")
            raise Exception(error_message)
        
        print(f"成功获取要素类型信息: {featuretype_name}")
        return response.json()
    
    def _get_coverage_info(self, store_name):
        """获取覆盖信息"""
        # 首先尝试获取覆盖存储中的覆盖列表
        coverages_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}/coverages.json"
        print(f"获取覆盖信息URL: {coverages_url}")
        
        response = requests.get(coverages_url, auth=self.auth)
        print(f"获取覆盖列表响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"获取覆盖列表失败响应内容: {response.text}")
            raise Exception(f"获取覆盖列表失败: {response.text}")
        
        # 解析覆盖列表
        coverages_data = response.json()
        print(f"覆盖列表数据: {coverages_data}")
        
        # 获取第一个覆盖的名称
        coverage_name = None
        if 'coverages' in coverages_data and 'coverage' in coverages_data['coverages']:
            coverages = coverages_data['coverages']['coverage']
            if isinstance(coverages, list) and len(coverages) > 0:
                coverage_name = coverages[0]['name']
            elif isinstance(coverages, dict):
                coverage_name = coverages['name']
        
        if not coverage_name:
            # 如果没有找到覆盖，尝试使用store_name
            coverage_name = store_name
            print(f"未找到覆盖，使用store_name: {coverage_name}")
        else:
            print(f"找到覆盖名称: {coverage_name}")
        
        # 获取具体覆盖的详细信息
        coverage_detail_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}/coverages/{coverage_name}.json"
        detail_response = requests.get(coverage_detail_url, auth=self.auth)
        
        if detail_response.status_code != 200:
            print(f"获取覆盖详细信息失败，构造基本信息")
            # 如果获取详细信息失败，构造基本的覆盖信息
            return {
                "coverage": {
                    "name": coverage_name,
                    "nativeName": coverage_name,
                    "title": coverage_name,
                    "abstract": f"从覆盖存储 {store_name} 发布的覆盖",
                    "enabled": True,
                    "srs": "EPSG:4326",
                    "store": {
                        "@class": "coverageStore",
                        "name": f"{self.workspace}:{store_name}"
                    }
                }
            }
        
        print(f"成功获取覆盖详细信息: {coverage_name}")
        coverage_info = detail_response.json()
        
        # 确保使用正确的结构（类似featureType）
        if 'coverage' in coverage_info:
            # 将coverage信息包装成类似featureType的结构，以便复用_create_layer_in_db方法
            return {
                "featureType": {
                    "name": coverage_info['coverage']['name'],
                    "nativeName": coverage_info['coverage'].get('nativeName', coverage_info['coverage']['name']),
                    "title": coverage_info['coverage'].get('title', coverage_info['coverage']['name']),
                    "abstract": coverage_info['coverage'].get('abstract', ''),
                    "enabled": coverage_info['coverage'].get('enabled', True),
                    "srs": coverage_info['coverage'].get('srs', 'EPSG:4326'),
                    "store": coverage_info['coverage'].get('store', {"name": f"{self.workspace}:{store_name}"})
                }
            }
        else:
            return coverage_info
    
    def _create_featuretype_in_db(self, featuretype_info, store_id):
        """在数据库中创建要素类型记录"""
        try:
            # 提取要素类型信息
            ft = featuretype_info['featureType']
            featuretype_name = ft.get('name')
            native_name = ft.get('nativeName', featuretype_name)
            title = ft.get('title', featuretype_name)
            abstract = ft.get('abstract', '')
            enabled = ft.get('enabled', True)
            srs = ft.get('srs', 'EPSG:4326')
            projection_policy = ft.get('projectionPolicy', 'REPROJECT_TO_DECLARED')
            
            print(f"要素类型信息: name={featuretype_name}, store_id={store_id}, srs={srs}")
            
            # 检查是否已存在同名的要素类型
            check_sql = """
            SELECT id FROM geoserver_featuretypes 
            WHERE name = %s AND store_id = %s
            """
            existing_result = execute_query(check_sql, (featuretype_name, store_id))
            
            if existing_result:
                print(f"⚠️ 要素类型 '{featuretype_name}' 已存在，featuretype_id={existing_result[0]['id']}")
                return existing_result[0]['id']
            
            # 创建新的要素类型记录
            sql = """
            INSERT INTO geoserver_featuretypes (name, store_id, native_name, title, abstract, enabled, srs, projection_policy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            result = execute_query(sql, (
                featuretype_name,
                store_id,
                native_name,
                title,
                abstract,
                enabled,
                srs,
                projection_policy
            ))
            featuretype_id = result[0]['id']
            print(f"✅ 新要素类型记录创建成功，featuretype_id={featuretype_id}")
            return featuretype_id
            
        except Exception as e:
            print(f"❌ 创建要素类型记录失败: {str(e)}")
            print(f"store_id={store_id}, featuretype_info={featuretype_info}")
            raise Exception(f"创建要素类型记录失败: {str(e)}")
    
    def _create_layer_in_db(self, featuretype_info, workspace_id, featuretype_id, file_id, store_type='datastore'):
        """在数据库中创建图层记录，并保存服务URL信息"""
        try:
            layer_name = featuretype_info['featureType']['name']
            full_layer_name = f"{self.workspace}:{layer_name}"
            
            # 生成服务URL
            wms_url = f"{self.url}/wms?service=WMS&version=1.1.0&request=GetCapabilities&layers={full_layer_name}"
            wfs_url = f"{self.url}/wfs?service=WFS&version=1.0.0&request=GetCapabilities&typeName={full_layer_name}"
            wcs_url = f"{self.url}/wcs?service=WCS&version=1.0.0&request=GetCapabilities&coverage={full_layer_name}" if store_type == 'coveragestore' else None
            
            print(f"创建图层记录: name={layer_name}, workspace_id={workspace_id}, featuretype_id={featuretype_id}, file_id={file_id}")
            print(f"服务URL: WMS={wms_url}")
            print(f"服务URL: WFS={wfs_url}")
            if wcs_url:
                print(f"服务URL: WCS={wcs_url}")
            
            # 检查是否已存在同名的图层
            check_sql = """
            SELECT id FROM geoserver_layers 
            WHERE name = %s AND workspace_id = %s
            """
            existing_result = execute_query(check_sql, (layer_name, workspace_id))
            
            if existing_result:
                print(f"⚠️ 图层 '{layer_name}' 已存在，layer_id={existing_result[0]['id']}")
                
                # 删除现有的图层记录以便重新创建
                delete_sql = "DELETE FROM geoserver_layers WHERE id = %s"
                execute_query(delete_sql, (existing_result[0]['id'],), fetch=False)
                print(f"🗑️ 删除现有图层记录")
            
            # 检查file_id是否在files表中存在
            file_exists = False
            if file_id:
                try:
                    check_file_sql = "SELECT id FROM files WHERE id = %s"
                    file_result = execute_query(check_file_sql, (file_id,))
                    file_exists = bool(file_result)
                except Exception as e:
                    print(f"⚠️ 无法检查file_id={file_id}是否存在: {str(e)}")
                    file_exists = False
            
            # 创建新的图层记录，包含服务URL信息
            if file_exists:
                sql = """
                INSERT INTO geoserver_layers (name, workspace_id, featuretype_id, coverage_id, file_id, enabled, 
                                            wms_url, wfs_url, wcs_url, title, queryable)
                VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, TRUE)
                RETURNING id
                """
                # 根据store类型决定featuretype_id还是coverage_id
                if store_type == 'coveragestore':
                    result = execute_query(sql, (
                        layer_name, workspace_id, None, featuretype_id, file_id,
                        wms_url, wfs_url, wcs_url, layer_name
                    ))
                else:
                    result = execute_query(sql, (
                        layer_name, workspace_id, featuretype_id, None, file_id,
                        wms_url, wfs_url, wcs_url, layer_name
                    ))
                print(f"✅ 图层记录创建成功，关联file_id={file_id}")
            else:
                sql = """
                INSERT INTO geoserver_layers (name, workspace_id, featuretype_id, coverage_id, file_id, enabled,
                                            wms_url, wfs_url, wcs_url, title, queryable)
                VALUES (%s, %s, %s, %s, NULL, TRUE, %s, %s, %s, %s, TRUE)
                RETURNING id
                """
                # 根据store类型决定featuretype_id还是coverage_id
                if store_type == 'coveragestore':
                    result = execute_query(sql, (
                        layer_name, workspace_id, None, featuretype_id,
                        wms_url, wfs_url, wcs_url, layer_name
                    ))
                else:
                    result = execute_query(sql, (
                        layer_name, workspace_id, featuretype_id, None,
                        wms_url, wfs_url, wcs_url, layer_name
                    ))
                print(f"✅ 图层记录创建成功，file_id为NULL（测试模式或文件不存在）")
            
            # 构建完整的图层名称和信息
            layer_info = {
                'id': result[0]['id'],
                'name': layer_name,
                'full_name': full_layer_name,
                'workspace_id': workspace_id,
                'featuretype_id': featuretype_id if store_type != 'coveragestore' else None,
                'coverage_id': featuretype_id if store_type == 'coveragestore' else None,
                'file_id': file_id if file_exists else None,
                'wms_url': wms_url,
                'wfs_url': wfs_url,
                'wcs_url': wcs_url
            }
            
            print(f"✅ 新图层记录创建成功，layer_id={layer_info['id']}")
            print(f"   - WMS URL: {wms_url}")
            print(f"   - WFS URL: {wfs_url}")
            if wcs_url:
                print(f"   - WCS URL: {wcs_url}")
            
            return layer_info
            
        except Exception as e:
            print(f"❌ 创建图层记录失败: {str(e)}")
            print(f"workspace_id={workspace_id}, featuretype_id={featuretype_id}, file_id={file_id}, featuretype_info={featuretype_info}")
            raise Exception(f"创建图层记录失败: {str(e)}")
    
    def _delete_related_records_from_db(self, store_name):
        """从数据库中删除相关记录"""
        # 删除图层记录
        layer_sql = "DELETE FROM geoserver_layers WHERE name = %s"
        execute_query(layer_sql, (store_name,), fetch=False)
        
        # 删除要素类型记录
        featuretype_sql = "DELETE FROM geoserver_featuretypes WHERE name = %s"
        execute_query(featuretype_sql, (store_name,), fetch=False)
        
        # 删除数据存储记录
        store_sql = "DELETE FROM geoserver_stores WHERE name = %s"
        execute_query(store_sql, (store_name,), fetch=False)
    
    def _create_postgis_datastore(self, store_name):
        """创建PostGIS数据存储
        
        根据GeoServer官方文档配置PostGIS数据源，包含完整的连接参数：
        - 基础连接参数（host、port、database、schema、user、passwd等）
        - 性能优化参数（Expose primary keys、encode functions、Loose bbox等）
        - 连接池参数（validate connections、Connection timeout、min/max connections等）
        - 几何处理参数（Support on the fly geometry simplification等）
        
        Args:
            store_name: 数据存储名称
        """
        from config import DB_CONFIG
        
        print(f"创建PostGIS数据源: {store_name}")
        
        # 清理可能存在的同名数据存储
        self._cleanup_existing_datastore(store_name)
        
        # 构建PostGIS数据存储配置，完全按照官方文档推荐参数
        datastore_config = {
            "dataStore": {
                "name": store_name,
                "type": "PostGIS",
                "enabled": True,
                "workspace": {
                    "name": self.workspace,
                    "href": f"{self.rest_url}/workspaces/{self.workspace}.json"
                },
                "connectionParameters": {
                    "entry": [
                        # === 基础连接参数 ===
                        {"@key": "dbtype", "$": "postgis"},
                        {"@key": "host", "$": DB_CONFIG['host']},
                        {"@key": "port", "$": str(DB_CONFIG['port'])},
                        {"@key": "database", "$": DB_CONFIG['database']},
                        {"@key": "schema", "$": DB_CONFIG.get('schema', 'public')},
                        {"@key": "user", "$": DB_CONFIG['user']},
                        {"@key": "passwd", "$": DB_CONFIG['password']},
                        {"@key": "namespace", "$": f"http://{self.workspace}"},
                        
                        # === SQL生成管理参数 ===
                        {"@key": "Expose primary keys", "$": "true"},
                        {"@key": "preparedStatements", "$": "true"},
                        {"@key": "Max open prepared statements", "$": "50"},
                        
                        # === 数据库交互管理参数 ===
                        {"@key": "Loose bbox", "$": "true"},
                        {"@key": "Estimated extends", "$": "true"},
                        {"@key": "encode functions", "$": "true"},
                        {"@key": "Support on the fly geometry simplification", "$": "true"},
                        {"@key": "Method used to simplify geometries", "$": "PRESERVETOPOLOGY"},
                        
                        # === 连接池参数 ===
                        {"@key": "validate connections", "$": "true"},
                        {"@key": "Connection timeout", "$": "20"},
                        {"@key": "min connections", "$": "1"},
                        {"@key": "max connections", "$": "10"},
                        {"@key": "fetch size", "$": "1000"},
                        {"@key": "Batch insert size", "$": "1"},
                        
                        # === 连接池维护参数 ===
                        {"@key": "Test while idle", "$": "true"},
                        {"@key": "Evictor run periodicity", "$": "300"},
                        {"@key": "Max connection idle time", "$": "300"},
                        {"@key": "Evictor tests per run", "$": "3"},
                        {"@key": "Min evictable idle time", "$": "300"}
                    ]
                }
            }
        }
        
        # 发送请求创建数据存储
        url = f"{self.rest_url}/workspaces/{self.workspace}/datastores"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(
            url, 
            json=datastore_config,
            auth=self.auth,
            headers=headers,
            timeout=60
        )
        
        print(f"创建数据存储响应状态码: {response.status_code}")
        if response.text:
            print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code not in [201, 200]:
            raise Exception(f"创建PostGIS数据存储失败: HTTP {response.status_code} - {response.text}")
        
        # 验证数据存储是否创建成功
        time.sleep(2)  # 等待GeoServer处理
        
        verify_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}.json"
        verify_response = requests.get(verify_url, auth=self.auth)
        
        if verify_response.status_code != 200:
            raise Exception(f"PostGIS数据存储创建后验证失败: {verify_response.text}")
        
        print(f"✅ PostGIS数据存储创建并验证成功: {store_name}")
    
    def _publish_featuretype_from_postgis(self, store_name, table_name, featuretype_name):
        """从PostGIS发布要素类型
        
        根据GeoServer官方文档，从已存在的PostGIS表发布要素类型
        
        Args:
            store_name: 数据存储名称
            table_name: PostGIS表名
            featuretype_name: 要素类型名称
            
        Returns:
            要素类型信息
        """
        print(f"从PostGIS发布要素类型: 表={table_name}, 要素类型={featuretype_name}")
        
        # 构建要素类型配置
        featuretype_config = {
            "featureType": {
                "name": featuretype_name,
                "nativeName": table_name,
                "namespace": {
                    "name": self.workspace,
                    "href": f"{self.rest_url}/namespaces/{self.workspace}.json"
                },
                "title": featuretype_name,
                "abstract": f"从PostGIS表 {table_name} 发布的要素类型",
                "enabled": True,
                "srs": "EPSG:4326",
                "projectionPolicy": "REPROJECT_TO_DECLARED",
                "store": {
                    "@class": "dataStore",
                    "name": f"{self.workspace}:{store_name}",
                    "href": f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}.json"
                }
            }
        }
        
        # 发送请求发布要素类型
        url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/featuretypes"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(
            url, 
            json=featuretype_config,
            auth=self.auth,
            headers=headers,
            timeout=60
        )
        
        print(f"发布要素类型响应状态码: {response.status_code}")
        if response.text:
            print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code not in [201, 200]:
            raise Exception(f"发布要素类型失败: HTTP {response.status_code} - {response.text}")
        
        # 等待GeoServer处理
        time.sleep(3)
        
        # 获取发布后的要素类型详细信息
        try:
            featuretype_info = self._get_featuretype_info(store_name, featuretype_name)
            return featuretype_info
        except Exception as e:
            print(f"获取要素类型信息失败，尝试其他方法: {str(e)}")
            
            # 如果获取失败，尝试使用表名
            try:
                featuretype_info = self._get_featuretype_info(store_name, table_name)
                return featuretype_info
            except Exception as e2:
                print(f"使用表名获取也失败，返回基本配置: {str(e2)}")
                
                # 返回基本的要素类型信息
                return {
                    "featureType": {
                        "name": featuretype_name,
                        "nativeName": table_name,
                        "namespace": {"name": self.workspace},
                        "title": featuretype_name,
                        "abstract": f"从PostGIS表 {table_name} 发布的要素类型",
                        "enabled": True,
                        "srs": "EPSG:4326",
                        "projectionPolicy": "REPROJECT_TO_DECLARED"
                    }
                }
    
    def _cleanup_failed_geojson_publish(self, store_name, table_name=None):
        """清理GeoJSON发布失败后的资源
        
        Args:
            store_name: 数据存储名称
            table_name: PostGIS表名（可选）
        """
        print(f"清理GeoJSON发布失败的资源...")
        
        try:
            # 1. 清理GeoServer中的数据存储
            self._cleanup_existing_datastore(store_name)
            print(f"✅ 清理GeoServer数据存储完成")
        except Exception as e:
            print(f"⚠️ 清理GeoServer数据存储失败: {str(e)}")
        
        try:
            # 2. 清理数据库中的记录
            self._delete_related_records_from_db(store_name)
            print(f"✅ 清理数据库记录完成")
        except Exception as e:
            print(f"⚠️ 清理数据库记录失败: {str(e)}")
        
        # 3. 可选：清理PostGIS表（谨慎操作）
        if table_name:
            try:
                from services.postgis_service import PostGISService
                postgis_service = PostGISService()
                postgis_service._drop_table_if_exists(table_name)
                print(f"✅ 清理PostGIS表完成: {table_name}")
            except Exception as e:
                print(f"⚠️ 清理PostGIS表失败: {str(e)}")
        
        print(f"✅ 资源清理完成")

    def _cleanup_failed_publish(self, store_name, store_type='datastore'):
        """清理发布失败后的资源
        
        Args:
            store_name: 数据存储名称
            store_type: 存储类型 ('datastore' 或 'coveragestore')
        """
        print(f"清理{store_type}发布失败的资源: {store_name}")
        
        try:
            # 1. 清理GeoServer中的存储
            if store_type == 'datastore':
                self._cleanup_existing_datastore(store_name)
            elif store_type == 'coveragestore':
                self._cleanup_existing_coveragestore(store_name)
            print(f"✅ 清理GeoServer {store_type}完成")
        except Exception as e:
            print(f"⚠️ 清理GeoServer {store_type}失败: {str(e)}")
        
        try:
            # 2. 清理数据库中的记录
            self._delete_related_records_from_db(store_name)
            print(f"✅ 清理数据库记录完成")
        except Exception as e:
            print(f"⚠️ 清理数据库记录失败: {str(e)}")
        
        print(f"✅ {store_type}资源清理完成")
    
    def _cleanup_existing_coveragestore(self, store_name):
        """清理可能存在的覆盖存储"""
        try:
            check_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}"
            check_response = requests.get(check_url, auth=self.auth)
            
            if check_response.status_code == 200:
                print(f"覆盖存储 {store_name} 已存在，先删除")
                delete_response = requests.delete(f"{check_url}?recurse=true", auth=self.auth)
                if delete_response.status_code not in [200, 404]:
                    print(f"删除现有覆盖存储失败: {delete_response.text}")
                else:
                    print(f"删除现有覆盖存储成功")
                time.sleep(1)
        except Exception as e:
            print(f"清理现有覆盖存储失败: {e}")
