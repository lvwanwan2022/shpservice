"""
MCP适配器模块
将现有service方法包装成MCP工具，无需修改原代码
"""

from typing import Dict, Any, List
from .decorators import mcp_tool

class ShpServiceMCPAdapter:
    """SHP服务MCP适配器"""
    
    def __init__(self, shp_service):
        self.service = shp_service
    
    @mcp_tool(
        name="upload_shp_file",
        description="上传SHP文件并发布为地图服务",
        parameters={
            "file_path": "str",
            "layer_name": "str"
        },
        category="file_upload",
        examples=[
            "上传SHP文件: upload_shp_file('/path/to/file.shp', 'my_layer')"
        ]
    )
    def upload_shp_file(self, file_path: str, layer_name: str) -> Dict[str, Any]:
        """上传SHP文件"""
        try:
            result = self.service.upload_shp_file(file_path, layer_name)
            return {
                "success": True,
                "data": result,
                "message": f"成功上传SHP文件: {layer_name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"上传SHP文件失败: {str(e)}"
            }
    
    @mcp_tool(
        name="get_shp_layers",
        description="获取所有SHP图层列表",
        category="data_query"
    )
    def get_shp_layers(self) -> Dict[str, Any]:
        """获取SHP图层列表"""
        try:
            layers = self.service.get_all_layers()
            return {
                "success": True,
                "data": layers,
                "message": f"找到 {len(layers)} 个SHP图层"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"获取SHP图层失败: {str(e)}"
            }

class SceneServiceMCPAdapter:
    """场景服务MCP适配器"""
    
    def __init__(self, scene_service):
        self.service = scene_service
    
    @mcp_tool(
        name="create_scene",
        description="创建新的地图场景",
        parameters={
            "scene_name": "str",
            "description": "str"
        },
        category="scene_management"
    )
    def create_scene(self, scene_name: str, description: str = "") -> Dict[str, Any]:
        """创建场景"""
        try:
            scene_id = self.service.create_scene(scene_name, description)
            return {
                "success": True,
                "data": {"scene_id": scene_id},
                "message": f"成功创建场景: {scene_name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"创建场景失败: {str(e)}"
            }
    
    @mcp_tool(
        name="get_scenes",
        description="获取所有场景列表",
        category="scene_management"
    )
    def get_scenes(self) -> Dict[str, Any]:
        """获取场景列表"""
        try:
            scenes = self.service.get_all_scenes()
            return {
                "success": True,
                "data": scenes,
                "message": f"找到 {len(scenes)} 个场景"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"获取场景列表失败: {str(e)}"
            }

class CacheServiceMCPAdapter:
    """缓存服务MCP适配器"""
    
    def __init__(self, cache_service):
        self.service = cache_service
    
    @mcp_tool(
        name="clear_cache",
        description="清空地图瓦片缓存",
        category="cache_management"
    )
    def clear_cache(self) -> Dict[str, Any]:
        """清空缓存"""
        try:
            result = self.service.clear_all_cache()
            return {
                "success": True,
                "data": result,
                "message": "成功清空缓存"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"清空缓存失败: {str(e)}"
            }
    
    @mcp_tool(
        name="get_cache_stats",
        description="获取缓存统计信息",
        category="cache_management"
    )
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            stats = self.service.get_cache_statistics()
            return {
                "success": True,
                "data": stats,
                "message": "成功获取缓存统计"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"获取缓存统计失败: {str(e)}"
            } 