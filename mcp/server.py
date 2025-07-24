"""
MCP服务器模块
实现Model Context Protocol服务器，处理大模型调用请求
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from .decorators import get_mcp_tools, get_tool_by_name

logger = logging.getLogger(__name__)

class MCPServer:
    """MCP服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.tools = get_mcp_tools()
        self.server = None
    
    async def start(self):
        """启动MCP服务器"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            logger.info(f"MCP服务器启动成功: {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
        except Exception as e:
            logger.error(f"MCP服务器启动失败: {e}")
    
    async def handle_client(self, reader, writer):
        """处理客户端连接"""
        try:
            while True:
                # 读取请求
                data = await reader.read(1024)
                if not data:
                    break
                
                request = json.loads(data.decode())
                response = await self.process_request(request)
                
                # 发送响应
                writer.write(json.dumps(response).encode())
                await writer.drain()
                
        except Exception as e:
            logger.error(f"处理客户端请求失败: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            
            if method == "tools/list":
                return await self.list_tools()
            elif method == "tools/call":
                return await self.call_tool(request.get("params", {}))
            elif method == "initialize":
                return await self.initialize(request.get("params", {}))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"未知方法: {method}"
                    }
                }
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"内部错误: {str(e)}"
                }
            }
    
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """初始化MCP连接"""
        return {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "GIS-Service-MCP",
                    "version": "1.0.0"
                }
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """列出所有可用工具"""
        tools_list = []
        
        for tool_name, tool_info in self.tools.items():
            tools_list.append({
                "name": tool_name,
                "description": tool_info["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": tool_info["parameters"],
                    "required": [
                        name for name, info in tool_info["parameters"].items() 
                        if info["required"]
                    ]
                }
            })
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": tools_list
            }
        }
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        tool_info = get_tool_by_name(tool_name)
        if not tool_info:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"工具不存在: {tool_name}"
                }
            }
        
        try:
            # 调用工具函数
            result = tool_info["function"](**arguments)
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"工具调用失败: {str(e)}"
                }
            }

def create_mcp_server() -> MCPServer:
    """创建MCP服务器实例"""
    return MCPServer()

# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = create_mcp_server()
        await server.start()
    
    asyncio.run(main()) 