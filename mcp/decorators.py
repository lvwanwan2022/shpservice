"""
MCP装饰器模块
用于标记和配置可被大模型调用的方法
"""

import functools
import inspect
from typing import Dict, Any, Optional, List

# 全局工具注册表
_mcp_tools = {}

def mcp_tool(
    name: str,
    description: str,
    parameters: Optional[Dict[str, str]] = None,
    category: str = "gis",
    examples: Optional[List[str]] = None
):
    """
    MCP工具装饰器
    
    Args:
        name: 工具名称
        description: 工具描述
        parameters: 参数定义 {"param_name": "param_type"}
        category: 工具分类
        examples: 使用示例列表
    """
    def decorator(func):
        # 获取函数签名
        sig = inspect.signature(func)
        param_info = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            param_type = parameters.get(param_name, "str") if parameters else "str"
            param_info[param_name] = {
                "type": param_type,
                "required": param.default == inspect.Parameter.empty,
                "description": f"参数 {param_name}"
            }
        
        # 注册工具信息
        tool_info = {
            "name": name,
            "description": description,
            "parameters": param_info,
            "category": category,
            "examples": examples or [],
            "function": func
        }
        
        _mcp_tools[name] = tool_info
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def get_mcp_tools() -> Dict[str, Any]:
    """获取所有注册的MCP工具"""
    return _mcp_tools.copy()

def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据名称获取工具信息"""
    return _mcp_tools.get(name) 