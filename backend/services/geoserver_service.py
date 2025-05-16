#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import json
import zipfile
import shutil
import tempfile
from config import GEOSERVER_CONFIG

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
        headers = {'Content-type': 'application/json'}
        workspace_url = f"{self.rest_url}/workspaces/{self.workspace}"
        
        # 检查工作空间是否存在
        response = requests.get(workspace_url, auth=self.auth)
        
        if response.status_code != 200:
            # 创建工作空间
            create_url = f"{self.rest_url}/workspaces"
            workspace_data = {
                "workspace": {
                    "name": self.workspace
                }
            }
            response = requests.post(
                create_url, 
                data=json.dumps(workspace_data), 
                headers=headers, 
                auth=self.auth
            )
            
            if response.status_code not in [201, 200]:
                raise Exception(f"创建工作空间失败: {response.text}")
    
    def publish_shapefile(self, shp_zip_path, store_name):
        """发布Shapefile服务
        
        Args:
            shp_zip_path: Shapefile ZIP包路径
            store_name: 数据存储名称
            
        Returns:
            服务URL
        """
        # 确保是zip文件
        if not shp_zip_path.endswith('.zip'):
            raise ValueError("Shapefile必须是zip格式")
        
        # 创建数据存储URL
        datastore_url = f"{self.rest_url}/workspaces/{self.workspace}/datastores/{store_name}/file.shp"
        
        # 上传shapefile
        headers = {'Content-type': 'application/zip'}
        with open(shp_zip_path, 'rb') as f:
            response = requests.put(
                datastore_url,
                data=f,
                headers=headers,
                auth=self.auth
            )
        
        if response.status_code not in [201, 200]:
            raise Exception(f"发布Shapefile服务失败: {response.text}")
        
        # 返回WMS和WFS服务URL
        wms_url = f"{self.url}/wms"
        wfs_url = f"{self.url}/wfs"
        layer_name = f"{self.workspace}:{store_name}"
        
        return {
            "wms_url": wms_url,
            "wfs_url": wfs_url,
            "layer_name": layer_name
        }
    
    def publish_geotiff(self, tif_path, store_name):
        """发布GeoTIFF服务
        
        Args:
            tif_path: GeoTIFF文件路径
            store_name: 数据存储名称
            
        Returns:
            服务URL
        """
        # 创建coverage store URL
        coveragestore_url = f"{self.rest_url}/workspaces/{self.workspace}/coveragestores/{store_name}/file.geotiff"
        
        # 上传GeoTIFF
        headers = {'Content-type': 'image/tiff'}
        with open(tif_path, 'rb') as f:
            response = requests.put(
                coveragestore_url,
                data=f,
                headers=headers,
                auth=self.auth
            )
        
        if response.status_code not in [201, 200]:
            raise Exception(f"发布GeoTIFF服务失败: {response.text}")
        
        # 返回WMS服务URL
        wms_url = f"{self.url}/wms"
        layer_name = f"{self.workspace}:{store_name}"
        
        return {
            "wms_url": wms_url,
            "layer_name": layer_name
        }
    
    def publish_dwg_dxf(self, file_path, store_name, coord_system):
        """发布DWG/DXF服务
        
        Args:
            file_path: DWG/DXF文件路径
            store_name: 数据存储名称
            coord_system: 坐标系统(如"EPSG:4326")
            
        Returns:
            服务URL
        """
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            # 调用外部工具转换DWG/DXF为Shapefile
            # 注意: 这里需要集成实际的转换工具，这只是一个示例
            # ogr2ogr可以用于DXF转SHP，但DWG可能需要其他工具
            
            # 假设转换后的shapefile放在temp_dir中
            shp_dir = os.path.join(temp_dir, "shp")
            os.makedirs(shp_dir, exist_ok=True)
            
            # 创建zip文件
            zip_path = os.path.join(temp_dir, f"{store_name}.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # 假设这里有添加shapefile相关文件的代码
                pass
            
            # 发布shapefile
            result = self.publish_shapefile(zip_path, store_name)
            return result
        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
    def publish_geojson(self, geojson_path, store_name):
        """发布GeoJSON服务
        
        Args:
            geojson_path: GeoJSON文件路径
            store_name: 数据存储名称
            
        Returns:
            服务URL
        """
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        try:
            # 调用ogr2ogr转换GeoJSON为Shapefile
            # 注意: 这里需要集成实际的转换工具，这只是一个示例
            
            # 假设转换后的shapefile放在temp_dir中
            shp_dir = os.path.join(temp_dir, "shp")
            os.makedirs(shp_dir, exist_ok=True)
            
            # 创建zip文件
            zip_path = os.path.join(temp_dir, f"{store_name}.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # 假设这里有添加shapefile相关文件的代码
                pass
            
            # 发布shapefile
            result = self.publish_shapefile(zip_path, store_name)
            return result
        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
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