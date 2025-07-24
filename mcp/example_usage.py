"""
MCP使用示例
展示如何在现有service中集成MCP功能
"""

import asyncio
from typing import Dict, Any
from .adapters import ShpServiceMCPAdapter, SceneServiceMCPAdapter, CacheServiceMCPAdapter
from .server import MCPServer

# 示例：在现有service中添加MCP支持
class ExampleIntegration:
    """示例集成类"""
    
    def __init__(self):
        # 假设这些是您现有的service实例
        self.shp_service = None  # 您的SHP服务实例
        self.scene_service = None  # 您的场景服务实例
        self.cache_service = None  # 您的缓存服务实例
        
        # 创建MCP适配器
        self.shp_adapter = ShpServiceMCPAdapter(self.shp_service)
        self.scene_adapter = SceneServiceMCPAdapter(self.scene_service)
        self.cache_adapter = CacheServiceMCPAdapter(self.cache_service)
    
    def setup_mcp_adapters(self):
        """设置MCP适配器"""
        # 这里会自动注册所有带有@mcp_tool装饰器的方法
        print("MCP适配器设置完成")
        print("可用的工具:")
        
        from .decorators import get_mcp_tools
        tools = get_mcp_tools()
        
        for tool_name, tool_info in tools.items():
            print(f"  - {tool_name}: {tool_info['description']}")
    
    async def start_mcp_server(self):
        """启动MCP服务器"""
        server = MCPServer(host="localhost", port=8001)
        print("启动MCP服务器...")
        await server.start()

# 示例：在现有service方法上直接添加MCP装饰器
class ShpServiceWithMCP:
    """带有MCP支持的SHP服务示例"""
    
    from .decorators import mcp_tool
    
    @mcp_tool(
        name="process_shp_file",
        description="处理SHP文件并生成地图服务",
        parameters={
            "file_path": "str",
            "output_format": "str",
            "coordinate_system": "str"
        },
        category="file_processing",
        examples=[
            "处理SHP文件: process_shp_file('/data/building.shp', 'geojson', 'EPSG:4326')"
        ]
    )
    def process_shp_file(self, file_path: str, output_format: str = "geojson", coordinate_system: str = "EPSG:4326") -> Dict[str, Any]:
        """处理SHP文件"""
        # 这里是您现有的业务逻辑
        try:
            # 模拟处理过程
            result = {
                "file_path": file_path,
                "output_format": output_format,
                "coordinate_system": coordinate_system,
                "status": "processed",
                "layers": ["building_layer", "road_layer"]
            }
            
            return {
                "success": True,
                "data": result,
                "message": f"成功处理SHP文件: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"处理SHP文件失败: {str(e)}"
            }
    
    @mcp_tool(
        name="validate_shp_file",
        description="验证SHP文件的有效性",
        parameters={
            "file_path": "str"
        },
        category="file_validation"
    )
    def validate_shp_file(self, file_path: str) -> Dict[str, Any]:
        """验证SHP文件"""
        try:
            # 模拟验证过程
            validation_result = {
                "file_path": file_path,
                "is_valid": True,
                "geometry_count": 1000,
                "attribute_fields": ["name", "type", "area"],
                "coordinate_system": "EPSG:4326"
            }
            
            return {
                "success": True,
                "data": validation_result,
                "message": f"SHP文件验证通过: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"SHP文件验证失败: {str(e)}"
            }

# 使用示例
async def main():
    """主函数示例"""
    
    # 方法1：使用适配器模式（推荐，不修改原代码）
    print("=== 方法1：使用适配器模式 ===")
    integration = ExampleIntegration()
    integration.setup_mcp_adapters()
    
    # 方法2：直接在现有service上添加装饰器
    print("\n=== 方法2：直接添加装饰器 ===")
    shp_service_with_mcp = ShpServiceWithMCP()
    
    # 测试调用
    result1 = shp_service_with_mcp.process_shp_file("/test/building.shp", "geojson", "EPSG:4326")
    print(f"处理结果: {result1}")
    
    result2 = shp_service_with_mcp.validate_shp_file("/test/building.shp")
    print(f"验证结果: {result2}")
    
    # 启动MCP服务器
    print("\n=== 启动MCP服务器 ===")
    await integration.start_mcp_server()

if __name__ == "__main__":
    asyncio.run(main()) 