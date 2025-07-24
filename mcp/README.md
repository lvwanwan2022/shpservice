# MCP (Model Context Protocol) 集成方案

## 概述

本方案为您的GIS服务系统提供了轻量级的MCP集成，让大模型能够调用您的GIS服务接口。方案采用注解驱动的方式，最小化对现有代码的修改。

## 架构设计

```
现有Services → MCP适配器 → MCP Server → 大模型调用
```

## 实现方式

### 方式1：适配器模式（推荐）

不修改现有service代码，通过适配器包装现有方法：

```python
from mcp.adapters import ShpServiceMCPAdapter

# 创建适配器
adapter = ShpServiceMCPAdapter(your_shp_service)

# 自动注册所有带有@mcp_tool装饰器的方法
```

### 方式2：直接注解

在现有service方法上直接添加装饰器：

```python
from mcp.decorators import mcp_tool

class YourShpService:
    @mcp_tool(
        name="upload_shp_file",
        description="上传SHP文件并发布为地图服务",
        parameters={
            "file_path": "str",
            "layer_name": "str"
        }
    )
    def upload_shp_file(self, file_path, layer_name):
        # 您的现有代码保持不变
        pass
```

## 快速开始

### 1. 安装依赖

```bash
pip install asyncio
```

### 2. 创建MCP适配器

```python
# 在您的应用启动时
from mcp.adapters import ShpServiceMCPAdapter, SceneServiceMCPAdapter
from mcp.server import MCPServer

# 创建适配器
shp_adapter = ShpServiceMCPAdapter(your_shp_service)
scene_adapter = SceneServiceMCPAdapter(your_scene_service)

# 启动MCP服务器
server = MCPServer(host="localhost", port=8001)
await server.start()
```

### 3. 在现有service中添加MCP支持

```python
# 在您的service文件中
from mcp.decorators import mcp_tool

class ShpService:
    @mcp_tool(
        name="process_shp_file",
        description="处理SHP文件并生成地图服务",
        parameters={
            "file_path": "str",
            "output_format": "str"
        },
        category="file_processing"
    )
    def process_shp_file(self, file_path, output_format="geojson"):
        # 您的现有业务逻辑
        return {"success": True, "data": result}
```

## 工具分类

系统预定义了以下工具分类：

- **file_upload**: 文件上传相关
- **file_processing**: 文件处理相关  
- **scene_management**: 场景管理相关
- **cache_management**: 缓存管理相关
- **data_query**: 数据查询相关

## 配置说明

### 工具权限配置

```python
TOOL_PERMISSIONS = {
    "upload_shp_file": {
        "required_permissions": ["file_upload"],
        "max_file_size": "100MB",
        "allowed_formats": [".shp", ".zip"]
    }
}
```

### 参数验证规则

```python
TOOL_VALIDATION_RULES = {
    "upload_shp_file": {
        "file_path": {
            "type": "string",
            "required": True,
            "pattern": r"^[a-zA-Z0-9\/\-_\.]+$"
        }
    }
}
```

## 使用示例

### 大模型调用示例

```python
# 大模型可以这样调用您的工具
{
    "method": "tools/call",
    "params": {
        "name": "upload_shp_file",
        "arguments": {
            "file_path": "/data/building.shp",
            "layer_name": "building_layer"
        }
    }
}
```

### 响应格式

```json
{
    "jsonrpc": "2.0",
    "result": {
        "content": [
            {
                "type": "text",
                "text": "{\"success\": true, \"message\": \"文件上传成功\"}"
            }
        ]
    }
}
```

## 部署说明

### 1. 集成到现有应用

```python
# 在您的app.py或main.py中
from mcp.server import MCPServer
import asyncio

async def start_mcp_server():
    server = MCPServer(host="localhost", port=8001)
    await server.start()

# 在应用启动时
asyncio.create_task(start_mcp_server())
```

### 2. 配置文件

创建 `mcp_config.json`:

```json
{
    "server": {
        "host": "localhost",
        "port": 8001
    },
    "tools": {
        "enabled_categories": ["file_upload", "scene_management"]
    }
}
```

## 安全考虑

1. **权限控制**: 通过 `TOOL_PERMISSIONS` 配置工具访问权限
2. **参数验证**: 使用正则表达式和类型检查验证输入参数
3. **错误处理**: 统一的错误处理和日志记录
4. **超时控制**: 设置操作超时时间，防止长时间阻塞

## 扩展开发

### 添加新工具

1. 在 `adapters.py` 中添加新的适配器类
2. 使用 `@mcp_tool` 装饰器标记方法
3. 在 `config.py` 中添加权限和验证规则

### 自定义响应格式

```python
@mcp_tool(name="custom_tool")
def custom_tool(self, param):
    return {
        "success": True,
        "data": result,
        "message": "操作成功"
    }
```

## 故障排除

### 常见问题

1. **工具未注册**: 确保导入了包含 `@mcp_tool` 装饰器的模块
2. **权限错误**: 检查用户权限配置
3. **参数验证失败**: 检查输入参数格式
4. **服务器启动失败**: 检查端口是否被占用

### 调试技巧

```python
# 查看注册的工具
from mcp.decorators import get_mcp_tools
tools = get_mcp_tools()
print(tools.keys())
```

## 总结

这个MCP集成方案具有以下优势：

1. **最小化修改**: 通过适配器模式，无需大幅修改现有代码
2. **注解驱动**: 使用装饰器轻松标记可调用的方法
3. **配置灵活**: 支持权限控制、参数验证等配置
4. **易于扩展**: 模块化设计，便于添加新功能
5. **安全可靠**: 内置权限控制和错误处理机制

通过这个方案，您可以轻松地将现有的GIS服务接口暴露给大模型，实现智能化的GIS服务调用。 