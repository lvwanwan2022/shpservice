"""
MCP (Model Context Protocol) 集成包
用于将GIS服务接口暴露给大模型调用
"""

from .decorators import mcp_tool
from .server import MCPServer
from .adapters import *

__all__ = ['mcp_tool', 'MCPServer'] 