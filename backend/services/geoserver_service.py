#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
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
        """发布Shapefile服务 - 解压验证版本
        
        发布流程：
        1. 解压ZIP文件到临时目录
        2. 验证Shapefile文件完整性
        3. 在GeoServer中创建数据存储
        4. 上传解压后的文件到GeoServer
        5. 创建数据库记录
        6. 清理临时文件
        
        Args:
            shp_zip_path: Shapefile ZIP包路径
            store_name: 数据存储名称（将被重新生成为"文件名_store"格式）
            file_id: 文件ID
            
        Returns:
            发布结果信息
        """
        extracted_folder = None
        try:
            print(f"开始发布Shapefile（解压验证版本）: {shp_zip_path}")
            
            # 1. 修复文件路径问题
            corrected_path = self._correct_path(shp_zip_path)
            print(f"修正后的文件路径: {corrected_path}")
            
            # 确保是zip文件
            if not corrected_path.endswith('.zip'):
                raise ValueError("Shapefile必须是zip格式")
            
            # 2. 解压并验证ZIP文件
            extracted_folder = self._extract_and_validate_shapefile_simple(corrected_path)
            print(f"✅ ZIP文件解压并验证成功: {extracted_folder}")
            
            # 3. 根据文件名生成store名称
            filename = os.path.splitext(os.path.basename(corrected_path))[0]
            clean_filename = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '_', filename)
            generated_store_name = f"{clean_filename}_store"
            print(f"自动生成的存储名称: {generated_store_name}")
            
            # 4. 获取SHP文件名并处理文件重命名
            original_shp_name = self._get_shp_name_from_folder(extracted_folder)
            print(f"解压文件夹中的原始SHP文件名: {original_shp_name}")
            
            # 检查并重命名包含中文或特殊字符的文件
            safe_shp_name = self._ensure_safe_shapefile_names(extracted_folder, original_shp_name, clean_filename)
            print(f"处理后的SHP文件名: {safe_shp_name}")
            
            # 5. 获取工作空间ID
            workspace_id = self._get_workspace_id()
            
            # 6. 在数据库中创建数据存储记录
            store_id = self._create_datastore_in_db(generated_store_name, workspace_id, 'Shapefile', file_id)
            print(f"✅ 数据存储记录创建成功，store_id={store_id}")
            
            # 7. 在GeoServer中创建空的数据存储
            self._create_empty_shapefile_datastore(generated_store_name)
            print(f"✅ GeoServer中空数据存储创建成功")
            
            # 8. 上传解压后的Shapefile到GeoServer
            self._upload_extracted_shapefile_to_geoserver(extracted_folder, generated_store_name)
            print(f"✅ Shapefile文件已上传到GeoServer")
            
            # 9. 等待GeoServer处理
            time.sleep(3)
            
            # 10. 获取要素类型信息（让GeoServer自动确定要素类型名称）
            featuretype_info = self._get_featuretype_info(generated_store_name)
            print(f"✅ 获取要素类型信息成功")
            
            # 11. 在数据库中创建要素类型记录
            featuretype_id = self._create_featuretype_in_db(featuretype_info, store_id)
            print(f"✅ 要素类型记录创建成功，featuretype_id={featuretype_id}")
            
            # 12. 在数据库中创建图层记录
            layer_info = self._create_layer_in_db(featuretype_info, workspace_id, featuretype_id, file_id, 'datastore')
            print(f"✅ 图层记录创建成功，layer_id={layer_info['id']}")
            
            # 13. 返回服务信息
            result = {
                "success": True,
                "store_name": generated_store_name,
                "layer_name": layer_info['full_name'],
                "wms_url": layer_info['wms_url'],
                "wfs_url": layer_info['wfs_url'],
                "layer_info": layer_info,
                "filename": filename
            }
            
            print(f"✅ Shapefile服务发布成功: {result['layer_name']}")
            return result
            
        except Exception as e:
            print(f"❌ 发布Shapefile失败: {str(e)}")
            
            # 清理可能创建的GeoServer资源
            if 'generated_store_name' in locals():
                self._cleanup_failed_publish(generated_store_name, 'datastore')
            
            # 重新抛出异常，让调用方知道发布失败
            raise Exception(f"发布Shapefile失败: {str(e)}")
            
        finally:
            # 清理解压的临时文件夹
            if extracted_folder and os.path.exists(extracted_folder):
                import shutil
                try:
                    shutil.rmtree(extracted_folder)
                    print(f"✅ 清理临时文件夹: {extracted_folder}")
                except Exception as cleanup_error:
                    print(f"⚠️ 清理临时文件夹失败: {cleanup_error}")
    
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
            
            # 预清理：删除可能存在的同名coveragestore
            print(f"预清理：检查并删除可能存在的同名coveragestore")
            self._cleanup_existing_coveragestore(generated_store_name)
            
            # 1. 创建覆盖存储记录
            store_id = self._create_coveragestore_in_db(generated_store_name, workspace_id, 'GeoTIFF', file_id)
            print(f"✅ 覆盖存储记录创建成功，store_id={store_id}")
            
            # 2. 上传GeoTIFF到GeoServer
            upload_success = False
            try:
                self._upload_geotiff_to_geoserver(corrected_path, generated_store_name)
                print(f"✅ GeoTIFF已上传到GeoServer")
                upload_success = True
            except Exception as upload_error:
                upload_error_msg = str(upload_error)
                print(f"⚠️ GeoTIFF上传失败: {upload_error_msg}")
                
                # 检查是否是文件已存在的错误
                if "Error while storing uploaded file" in upload_error_msg:
                    print(f"🔄 检测到文件存储错误，可能文件已存在，尝试跳过上传直接发布服务")
                    
                    # 检查coveragestore是否已自动创建
                    check_store_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{generated_store_name}"
                    check_response = requests.get(check_store_url, auth=self.auth)
                    
                    if check_response.status_code == 200:
                        print(f"✅ Coveragestore已存在，跳过上传步骤")
                        upload_success = True
                    else:
                        print(f"❌ Coveragestore不存在，尝试创建空的coveragestore")
                        # 尝试创建空的coveragestore，然后直接发布
                        try:
                            self._create_empty_coveragestore_for_existing_file(generated_store_name, corrected_path)
                            print(f"✅ 空coveragestore创建成功")
                            upload_success = True
                        except Exception as create_error:
                            print(f"❌ 创建空coveragestore失败: {str(create_error)}")
                            raise upload_error  # 如果都失败了，抛出原始上传错误
                else:
                    # 其他类型的上传错误，直接抛出
                    raise upload_error
            
            if not upload_success:
                raise Exception("GeoTIFF上传失败")
            
            # 3. 等待GeoServer处理
            time.sleep(3)
            
            # 4. 获取覆盖信息
            coverage_info = self._get_coverage_info(generated_store_name)
            print(f"✅ 获取覆盖信息成功")
            
            # 5. 在数据库中创建覆盖记录
            coverage_id = self._create_coverage_in_db(coverage_info, store_id)
            print(f"✅ 覆盖记录创建成功，coverage_id={coverage_id}")
            
            # 6. 在数据库中创建覆盖图层记录
            layer_info = self._create_layer_in_db(coverage_info, workspace_id, coverage_id, file_id, 'coveragestore')
            print(f"✅ 覆盖图层记录创建成功，layer_id={layer_info['id']}")
            
            # 7. 返回服务信息
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
    
    def _create_coverage_in_db(self, coverage_info, store_id):
        """在数据库中创建覆盖记录
        
        Args:
            coverage_info: 覆盖信息（可能包装在featureType结构中）
            store_id: 存储ID
            
        Returns:
            覆盖ID
        """
        try:
            # 处理数据结构，支持两种格式：coverage和featureType
            if 'coverage' in coverage_info:
                coverage_data = coverage_info['coverage']
            elif 'featureType' in coverage_info:
                # 从featureType结构中提取coverage信息
                coverage_data = coverage_info['featureType']
            else:
                raise Exception("无效的覆盖信息结构")
            
            coverage_name = coverage_data['name']
            title = coverage_data.get('title', coverage_name)
            abstract = coverage_data.get('abstract', '')
            srs = coverage_data.get('srs', 'EPSG:4326')
            enabled = coverage_data.get('enabled', True)
            
            print(f"创建覆盖记录: name={coverage_name}, store_id={store_id}")
            
            # 检查是否已存在同名的覆盖
            check_sql = """
            SELECT id FROM geoserver_coverages 
            WHERE name = %s AND store_id = %s
            """
            existing_result = execute_query(check_sql, (coverage_name, store_id))
            
            if existing_result:
                print(f"⚠️ 覆盖 '{coverage_name}' 已存在，coverage_id={existing_result[0]['id']}")
                
                # 删除现有的覆盖记录以便重新创建
                delete_sql = "DELETE FROM geoserver_coverages WHERE id = %s"
                execute_query(delete_sql, (existing_result[0]['id'],), fetch=False)
                print(f"🗑️ 删除现有覆盖记录")
            
            # 创建新的覆盖记录
            sql = """
            INSERT INTO geoserver_coverages (name, store_id, title, abstract, srs, enabled)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            result = execute_query(sql, (coverage_name, store_id, title, abstract, srs, enabled))
            coverage_id = result[0]['id']
            
            print(f"✅ 覆盖记录创建成功，coverage_id={coverage_id}")
            return coverage_id
            
        except Exception as e:
            print(f"❌ 创建覆盖记录失败: {str(e)}")
            print(f"store_id={store_id}, coverage_info={coverage_info}")
            raise Exception(f"创建覆盖记录失败: {str(e)}")
    
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
                    # 栅格数据，使用coveragestore，调用增强清理方法
                    print(f"开始删除coveragestore: {store_name}")
                    self._cleanup_existing_coveragestore(store_name)
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
    
    def _extract_and_validate_shapefile_simple(self, zip_path):
        """简化的解压和验证Shapefile文件方法
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            str: 解压后的文件夹路径
            
        Raises:
            Exception: 如果文件不完整或格式不正确
        """
        import zipfile
        import os
        import tempfile
        
        print(f"开始解压Shapefile: {zip_path}")
        
        # 创建临时解压目录
        temp_dir = tempfile.mkdtemp()
        filename = os.path.splitext(os.path.basename(zip_path))[0]
        extracted_folder = os.path.join(temp_dir, filename)
        os.makedirs(extracted_folder, exist_ok=True)
        
        try:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                zip_file.extractall(extracted_folder)
                print(f"ZIP文件解压完成: {extracted_folder}")
            
            # 获取解压后的文件列表
            extracted_files = []
            for root, dirs, files in os.walk(extracted_folder):
                for file in files:
                    extracted_files.append(file.lower())
            
            print(f"解压后的文件列表: {extracted_files}")
            
            # 简单验证：检查必需文件是否存在
            has_shp = any(f.endswith('.shp') for f in extracted_files)
            has_dbf = any(f.endswith('.dbf') for f in extracted_files)
            has_shx = any(f.endswith('.shx') for f in extracted_files)
            
            if not has_shp:
                raise Exception("ZIP文件中未找到.shp文件")
            if not has_dbf:
                raise Exception("ZIP文件中未找到.dbf文件")
            if not has_shx:
                raise Exception("ZIP文件中未找到.shx文件")
            
            print(f"✅ Shapefile文件验证通过")
            return extracted_folder
            
        except Exception as e:
            # 如果验证失败，清理解压的文件
            if os.path.exists(extracted_folder):
                import shutil
                shutil.rmtree(extracted_folder)
            raise Exception(f"Shapefile文件解压或验证失败: {str(e)}")
    
    def _get_shp_name_from_folder(self, folder_path):
        """从解压的文件夹中获取SHP文件名
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            str: SHP文件的基础名称（不含扩展名）
        """
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.shp'):
                    return os.path.splitext(file)[0]
        
        raise Exception("在解压文件夹中未找到.shp文件")
    
    def _ensure_safe_shapefile_names(self, folder_path, original_name, safe_base_name):
        """确保Shapefile文件名是GeoServer友好的
        
        如果原始文件名包含中文或特殊字符，就重命名为安全的英文名称
        
        Args:
            folder_path: 解压后的文件夹路径
            original_name: 原始SHP文件名（不含扩展名）
            safe_base_name: 安全的基础名称
            
        Returns:
            str: 最终的SHP文件名（不含扩展名）
        """
        import re
        import os
        
        # 检查原始文件名是否包含中文或特殊字符
        has_chinese = re.search(r'[\u4e00-\u9fff]', original_name)
        has_special_chars = any(char in original_name for char in ['(', ')', ' ', '（', '）', '-', '+', '=', '@', '#', '$', '%', '^', '&', '*'])
        
        if not (has_chinese or has_special_chars):
            print(f"文件名安全，无需重命名: {original_name}")
            return original_name
        
        print(f"检测到不安全的文件名，需要重命名: {original_name}")
        print(f"使用安全名称: {safe_base_name}")
        
        # 需要重命名的文件扩展名
        extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.sbn', '.sbx', '.qix']
        
        renamed_count = 0
        for ext in extensions:
            original_file = os.path.join(folder_path, f"{original_name}{ext}")
            new_file = os.path.join(folder_path, f"{safe_base_name}{ext}")
            
            if os.path.exists(original_file):
                try:
                    os.rename(original_file, new_file)
                    print(f"✅ 重命名文件: {original_name}{ext} -> {safe_base_name}{ext}")
                    renamed_count += 1
                except Exception as e:
                    print(f"⚠️ 重命名文件失败: {original_file} -> {new_file}, 错误: {e}")
        
        if renamed_count > 0:
            print(f"✅ 成功重命名 {renamed_count} 个文件")
            return safe_base_name
        else:
            print(f"⚠️ 没有文件被重命名，使用原始名称")
            return original_name
    
    def _upload_extracted_shapefile_to_geoserver(self, folder_path, store_name):
        """上传解压后的Shapefile文件到GeoServer
        
        直接上传.shp文件，GeoServer会自动找到同目录下的配套文件
        
        Args:
            folder_path: 解压后的文件夹路径
            store_name: 数据存储名称
        """
        import os
        
        print(f"准备上传解压后的Shapefile到GeoServer: {folder_path}")
        
        # 找到.shp文件
        shp_file_path = None
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.shp'):
                    shp_file_path = os.path.join(root, file)
                    break
            if shp_file_path:
                break
        
        if not shp_file_path:
            raise Exception(f"在文件夹中未找到.shp文件: {folder_path}")
        
        print(f"找到SHP文件: {shp_file_path}")
        print(f"文件大小: {os.path.getsize(shp_file_path)} 字节")
        
        # 上传.shp文件到GeoServer
        # GeoServer会自动查找同目录下的.dbf, .shx, .prj等配套文件
        datastore_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/file.shp"
        headers = {'Content-Type': 'application/octet-stream'}
        
        print(f"上传URL: {datastore_url}")
        
        try:
            with open(shp_file_path, 'rb') as f:
                response = requests.put(
                    datastore_url,
                    data=f,
                    headers=headers,
                    auth=self.auth,
                    timeout=300  # 5分钟超时
                )
            
            print(f"Shapefile上传响应状态码: {response.status_code}")
            if response.text:
                print(f"响应内容: {response.text[:500]}...")
            
            if response.status_code not in [201, 200]:
                raise Exception(f"上传Shapefile失败: HTTP {response.status_code} - {response.text}")
            
            print("✅ Shapefile上传成功")
            
        except requests.exceptions.Timeout:
            raise Exception("上传Shapefile超时，请检查文件大小和网络连接")
        except requests.exceptions.RequestException as e:
            raise Exception(f"上传Shapefile网络错误: {str(e)}")
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
    
    def _create_empty_coveragestore_for_existing_file(self, store_name, file_path):
        """为已存在的文件创建空的coveragestore
        
        当文件已经存在于GeoServer的data目录中时，创建一个指向该文件的coveragestore
        
        Args:
            store_name: 存储名称
            file_path: 文件路径（用于确定文件名）
        """
        import os
        
        print(f"为已存在文件创建coveragestore: {store_name}")
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        # 构建coveragestore配置，指向GeoServer data目录中的文件
        coveragestore_config = {
            "coverageStore": {
                "name": store_name,
                "type": "GeoTIFF",
                "enabled": True,
                "workspace": {
                    "name": self.workspace,
                    "href": f"{self.rest_url}/workspaces/{self.workspace}.json"
                },
                "url": f"file:data/{self.workspace}/{store_name}/{filename}"
            }
        }
        
        # 发送请求创建coveragestore
        url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores"
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(
            url,
            json=coveragestore_config,
            auth=self.auth,
            headers=headers,
            timeout=60
        )
        
        print(f"创建coveragestore响应状态码: {response.status_code}")
        if response.text:
            print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code not in [201, 200]:
            # 如果创建失败，尝试直接引用可能存在的文件
            print(f"⚠️ 标准创建失败，尝试直接引用文件")
            
            # 尝试不同的URL格式
            alt_urls = [
                f"file:data/{self.workspace}/{store_name}/{store_name}.geotiff",
                f"file:data/{self.workspace}/{store_name}.geotiff",
                f"file:{filename}",
                f"file:data/{filename}"
            ]
            
            for alt_url in alt_urls:
                print(f"  尝试URL: {alt_url}")
                alt_config = {
                    "coverageStore": {
                        "name": store_name,
                        "type": "GeoTIFF",
                        "enabled": True,
                        "workspace": {
                            "name": self.workspace,
                            "href": f"{self.rest_url}/workspaces/{self.workspace}.json"
                        },
                        "url": alt_url
                    }
                }
                
                alt_response = requests.post(
                    url,
                    json=alt_config,
                    auth=self.auth,
                    headers=headers,
                    timeout=60
                )
                
                print(f"  响应状态码: {alt_response.status_code}")
                
                if alt_response.status_code in [201, 200]:
                    print(f"  ✅ 使用URL {alt_url} 创建成功")
                    break
            else:
                raise Exception(f"创建coveragestore失败: {response.text}")
        
        # 等待GeoServer处理
        time.sleep(2)
        
        # 验证创建结果
        verify_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}.json"
        verify_response = requests.get(verify_url, auth=self.auth)
        
        if verify_response.status_code != 200:
            raise Exception(f"Coveragestore创建后验证失败: {verify_response.text}")
        
        print(f"✅ Coveragestore创建并验证成功: {store_name}")
    
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
    
    def _get_featuretype_info(self, store_name, featuretype_name=None):
        """获取要素类型信息
        
        Args:
            store_name: 数据存储名称
            featuretype_name: 要素类型名称（可选，如果不提供则获取第一个）
        
        Returns:
            要素类型信息
        """
        # 如果没有提供featuretype_name，先获取数据存储中的要素类型列表
        if not featuretype_name:
            featuretypes_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/featuretypes.json"
            print(f"获取要素类型列表URL: {featuretypes_url}")
            
            response = requests.get(featuretypes_url, auth=self.auth)
            print(f"获取要素类型列表响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                raise Exception(f"获取要素类型列表失败: {response.text}")
            
            # 解析要素类型列表
            data = response.json()
            print(f"要素类型列表数据: {data}")
            
            if 'featureTypes' in data and 'featureType' in data['featureTypes']:
                feature_types = data['featureTypes']['featureType']
                
                if isinstance(feature_types, list) and len(feature_types) > 0:
                    featuretype_name = feature_types[0]['name']
                elif isinstance(feature_types, dict):
                    featuretype_name = feature_types['name']
            
            if not featuretype_name:
                raise Exception(f"数据存储 {store_name} 中没有找到要素类型")
            
            print(f"找到要素类型名称: {featuretype_name}")
        
        # 获取要素类型详细信息
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
            # 处理数据结构，支持两种格式：featureType和coverage
            if 'featureType' in featuretype_info:
                layer_data = featuretype_info['featureType']
            elif 'coverage' in featuretype_info:
                layer_data = featuretype_info['coverage']
            else:
                raise Exception("无效的图层信息结构，缺少featureType或coverage")
            
            layer_name = layer_data['name']
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
                    # 对于coveragestore，featuretype_id参数实际传递的是coverage_id
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
                    # 对于coveragestore，featuretype_id参数实际传递的是coverage_id
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
        """清理可能存在的覆盖存储
        
        增强版清理方法，确保删除GeoServer中的coveragestore及其物理文件
        """
        try:
            print(f"检查覆盖存储是否存在: {store_name}")
            check_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}"
            check_response = requests.get(check_url, auth=self.auth)
            
            if check_response.status_code == 200:
                print(f"⚠️ 覆盖存储 {store_name} 已存在，开始删除")
                
                # 步骤1: 先获取并删除所有相关的coverage
                print(f"步骤1: 删除相关的coverage")
                try:
                    coverages_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}/coverages.json"
                    coverages_response = requests.get(coverages_url, auth=self.auth)
                    
                    if coverages_response.status_code == 200:
                        coverages_data = coverages_response.json()
                        if 'coverages' in coverages_data and 'coverage' in coverages_data['coverages']:
                            coverages = coverages_data['coverages']['coverage']
                            if isinstance(coverages, list):
                                coverage_list = coverages
                            else:
                                coverage_list = [coverages]
                            
                            for coverage in coverage_list:
                                coverage_name = coverage['name']
                                print(f"  删除coverage: {coverage_name}")
                                coverage_delete_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}/coverages/{coverage_name}?recurse=true"
                                coverage_delete_response = requests.delete(coverage_delete_url, auth=self.auth)
                                print(f"  coverage删除响应: {coverage_delete_response.status_code}")
                except Exception as e:
                    print(f"  删除coverage时出错: {str(e)}")
                
                # 等待处理
                time.sleep(1)
                
                # 步骤2: 删除coveragestore，使用purge=all参数确保删除物理文件
                print(f"步骤2: 删除coveragestore及物理文件")
                delete_url = f"{check_url}?recurse=true&purge=all"
                print(f"删除URL: {delete_url}")
                
                delete_response = requests.delete(delete_url, auth=self.auth)
                print(f"coveragestore删除响应状态码: {delete_response.status_code}")
                print(f"coveragestore删除响应内容: {delete_response.text}")
                
                if delete_response.status_code in [200, 404]:
                    print(f"✅ coveragestore删除成功")
                else:
                    print(f"⚠️ coveragestore删除失败，尝试其他参数")
                    
                    # 尝试使用不同的参数组合
                    for purge_param in ['true', 'metadata', 'all']:
                        print(f"  尝试purge={purge_param}")
                        alt_delete_url = f"{check_url}?recurse=true&purge={purge_param}"
                        alt_delete_response = requests.delete(alt_delete_url, auth=self.auth)
                        print(f"  响应状态码: {alt_delete_response.status_code}")
                        
                        if alt_delete_response.status_code in [200, 404]:
                            print(f"  ✅ 使用purge={purge_param}删除成功")
                            break
                    else:
                        # 最后尝试不使用purge参数
                        print(f"  最后尝试不使用purge参数")
                        final_delete_url = f"{check_url}?recurse=true"
                        final_delete_response = requests.delete(final_delete_url, auth=self.auth)
                        print(f"  最终删除响应: {final_delete_response.status_code}")
                
                # 等待GeoServer处理完成
                time.sleep(3)
                
                # 步骤3: 验证删除结果
                print(f"步骤3: 验证删除结果")
                verify_response = requests.get(check_url, auth=self.auth)
                if verify_response.status_code == 404:
                    print(f"✅ 覆盖存储删除验证成功")
                else:
                    print(f"⚠️ 覆盖存储可能未完全删除，状态码: {verify_response.status_code}")
                    print(f"验证响应内容: {verify_response.text}")
                    
                    # 额外的清理步骤：直接通过工作空间删除
                    print(f"尝试通过工作空间级别删除")
                    workspace_delete_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}?recurse=true&purge=all"
                    workspace_delete_response = requests.delete(workspace_delete_url, auth=self.auth)
                    print(f"工作空间级别删除响应: {workspace_delete_response.status_code}")
                    time.sleep(2)
                    
            elif check_response.status_code == 404:
                print(f"✅ 覆盖存储 {store_name} 不存在，无需清理")
            else:
                print(f"⚠️ 检查覆盖存储状态异常: {check_response.status_code} - {check_response.text}")
                
        except Exception as e:
            print(f"⚠️ 清理覆盖存储异常: {str(e)}")
            import traceback
            traceback.print_exc()
            # 不抛出异常，允许继续执行发布流程
    
    def _create_empty_shapefile_datastore(self, store_name):
        """在GeoServer中创建空的Shapefile数据存储
        
        这是创建Shapefile数据存储的推荐方式：
        1. 先创建空的datastore
        2. 然后上传文件到已存在的datastore
        
        Args:
            store_name: 数据存储名称
        """
        print(f"在GeoServer中创建空的Shapefile数据存储: {store_name}")
        
        # 先清理可能存在的同名数据存储
        self._cleanup_existing_datastore(store_name)
        
        # 构建Shapefile数据存储配置
        datastore_config = {
            "dataStore": {
                "name": store_name,
                "type": "Shapefile",
                "enabled": True,
                "workspace": {
                    "name": self.workspace,
                    "href": f"{self.rest_url}/workspaces/{self.workspace}.json"
                },
                "connectionParameters": {
                    "entry": [
                        {"@key": "url", "$": f"file:data/{self.workspace}/{store_name}/"},
                        {"@key": "namespace", "$": f"http://{self.workspace}"},
                        {"@key": "create spatial index", "$": "true"},
                        {"@key": "charset", "$": "UTF-8"}
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
        
        print(f"创建Shapefile数据存储响应状态码: {response.status_code}")
        if response.text:
            print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code not in [201, 200]:
            raise Exception(f"创建Shapefile数据存储失败: HTTP {response.status_code} - {response.text}")
        
        # 验证数据存储是否创建成功
        time.sleep(1)  # 等待GeoServer处理
        
        verify_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}.json"
        verify_response = requests.get(verify_url, auth=self.auth)
        
        if verify_response.status_code != 200:
            raise Exception(f"Shapefile数据存储创建后验证失败: {verify_response.text}")
        
        print(f"✅ Shapefile数据存储创建并验证成功: {store_name}")
    
    def _upload_zip_to_geoserver_datastore(self, zip_path, store_name):
        """直接上传ZIP文件到GeoServer数据存储
        
        采用GeoServer官方推荐的方式，通过REST API直接上传ZIP文件。
        GeoServer会自动：
        1. 解压ZIP文件
        2. 验证Shapefile文件完整性
        3. 处理中文文件名和特殊字符
        4. 创建数据存储和要素类型
        
        Args:
            zip_path: ZIP文件路径
            store_name: 数据存储名称
        """
        print(f"直接上传ZIP文件到GeoServer数据存储: {zip_path}")
        
        # 验证文件是否存在
        if not os.path.exists(zip_path):
            raise Exception(f"ZIP文件不存在: {zip_path}")
        
        # 使用GeoServer REST API上传ZIP文件
        # PUT /workspaces/{ws}/datastores/{ds}/file.shp
        datastore_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/file.shp"
        headers = {'Content-Type': 'application/zip'}
        
        print(f"上传URL: {datastore_url}")
        print(f"文件大小: {os.path.getsize(zip_path)} 字节")
        
        try:
            with open(zip_path, 'rb') as f:
                response = requests.put(
                    datastore_url,
                    data=f,
                    headers=headers,
                    auth=self.auth,
                    timeout=300  # 5分钟超时，适合大文件
                )
            
            print(f"ZIP上传响应状态码: {response.status_code}")
            if response.text:
                print(f"响应内容: {response.text[:500]}...")
            
            if response.status_code not in [201, 200]:
                raise Exception(f"上传ZIP文件失败: HTTP {response.status_code} - {response.text}")
            
            print("✅ ZIP文件上传成功，GeoServer正在自动处理...")
            
        except requests.exceptions.Timeout:
            raise Exception("上传ZIP文件超时，请检查文件大小和网络连接")
        except requests.exceptions.RequestException as e:
            raise Exception(f"上传ZIP文件网络错误: {str(e)}")
        except Exception as e:
            raise Exception(f"上传ZIP文件失败: {str(e)}")
    
    def _get_auto_created_featuretype_info(self, store_name):
        """获取GeoServer自动创建的要素类型信息
        
        当ZIP文件上传成功后，GeoServer会自动创建要素类型。
        此方法尝试获取这些自动创建的要素类型信息。
        
        Args:
            store_name: 数据存储名称
            
        Returns:
            要素类型信息
        """
        print(f"获取数据存储 {store_name} 中自动创建的要素类型...")
        
        # 首先获取数据存储中的要素类型列表
        featuretypes_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/featuretypes.json"
        
        try:
            response = requests.get(featuretypes_url, auth=self.auth)
            
            if response.status_code != 200:
                raise Exception(f"获取要素类型列表失败: HTTP {response.status_code} - {response.text}")
            
            data = response.json()
            print(f"要素类型列表响应: {data}")
            
            # 解析要素类型列表
            featuretype_name = None
            if 'featureTypes' in data and 'featureType' in data['featureTypes']:
                feature_types = data['featureTypes']['featureType']
                
                if isinstance(feature_types, list) and len(feature_types) > 0:
                    featuretype_name = feature_types[0]['name']
                elif isinstance(feature_types, dict):
                    featuretype_name = feature_types['name']
            
            if not featuretype_name:
                raise Exception("未找到自动创建的要素类型")
            
            print(f"找到自动创建的要素类型: {featuretype_name}")
            
            # 获取要素类型的详细信息
            featuretype_detail_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/featuretypes/{featuretype_name}.json"
            detail_response = requests.get(featuretype_detail_url, auth=self.auth)
            
            if detail_response.status_code != 200:
                raise Exception(f"获取要素类型详细信息失败: HTTP {detail_response.status_code} - {detail_response.text}")
            
            featuretype_info = detail_response.json()
            print(f"✅ 成功获取要素类型详细信息: {featuretype_name}")
            
            return featuretype_info
            
        except Exception as e:
            print(f"❌ 获取自动创建的要素类型失败: {str(e)}")
            raise Exception(f"获取自动创建的要素类型失败: {str(e)}")
