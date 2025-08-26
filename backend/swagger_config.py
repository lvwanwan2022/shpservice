#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Swagger配置文件
用于统一加载所有YAML格式的API文档配置
"""

import os
import yaml
from flask_restx import Api
from flask import Flask

def load_swagger_configs(api: Api, swagger_dir: str = None):
    """
    加载所有Swagger YAML配置文件到Flask-RESTX API实例
    
    Args:
        api: Flask-RESTX的Api实例
        swagger_dir: Swagger配置文件目录，默认为当前目录下的swagger文件夹
    """
    if swagger_dir is None:
        swagger_dir = os.path.join(os.path.dirname(__file__), 'swagger')
    
    if not os.path.exists(swagger_dir):
        print(f"⚠️ Swagger配置目录不存在: {swagger_dir}")
        return
    
    # 获取所有YAML配置文件
    yaml_files = [f for f in os.listdir(swagger_dir) if f.endswith('.yaml') or f.endswith('.yml')]
    
    if not yaml_files:
        print(f"⚠️ 在目录 {swagger_dir} 中未找到YAML配置文件")
        return
    
    print(f"📁 开始加载 {len(yaml_files)} 个Swagger配置文件...")
    
    # 合并所有YAML配置
    combined_config = {
        'openapi': '3.0.3',
        'info': {
            'title': 'SHP Service API',
            'description': 'GIS文件管理和地图服务API',
            'version': '1.0.0',
            'contact': {
                'name': 'SHP Service Team',
                'email': 'support@shpservice.com'
            }
        },
        'servers': [
            {
                'url': '',
                'description': 'API服务'
            }
        ],
        'paths': {},
        'components': {
            'securitySchemes': {
                'BearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT',
                    'description': 'JWT认证令牌'
                }
            },
            'schemas': {}
        },
        'tags': []
    }
    
    for yaml_file in sorted(yaml_files):
        file_path = os.path.join(swagger_dir, yaml_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 合并配置
            if config and 'paths' in config:
                # 处理路径前缀
                paths_to_add = {}
                if 'servers' in config and config['servers']:
                    # 获取第一个server的url作为前缀
                    server_url = config['servers'][0]['url']
                    for path, path_config in config['paths'].items():
                        # 如果路径不是以/开头，添加/
                        if not path.startswith('/'):
                            path = '/' + path
                        
                        # 处理路径前缀，避免重复的/api
                        if server_url.startswith('/api') and path.startswith('/api'):
                            # 如果server_url和path都包含/api，只保留一个
                            full_path = path
                        else:
                            # 组合完整路径
                            full_path = server_url + path
                        
                        paths_to_add[full_path] = path_config
                else:
                    # 如果没有servers配置，直接使用路径
                    paths_to_add = config['paths']
                
                # 合并paths
                combined_config['paths'].update(paths_to_add)
                
                # 合并components
                if 'components' in config and 'schemas' in config['components']:
                    combined_config['components']['schemas'].update(config['components']['schemas'])
                
                # 合并tags
                if 'tags' in config:
                    combined_config['tags'].extend(config['tags'])
                
                print(f"✅ 成功加载配置文件: {yaml_file}")
            else:
                print(f"⚠️ 配置文件格式不正确: {yaml_file}")
                
        except Exception as e:
            print(f"❌ 加载配置文件失败 {yaml_file}: {str(e)}")
    
    # 去重tags
    seen_tags = set()
    unique_tags = []
    for tag in combined_config['tags']:
        tag_name = tag.get('name', '')
        if tag_name not in seen_tags:
            seen_tags.add(tag_name)
            unique_tags.append(tag)
    combined_config['tags'] = unique_tags
    
    # 将合并后的配置应用到Flask-RESTX API
    try:
        # 使用Flask-RESTX的add_resource方法添加路径
        # 注意：这里我们需要创建实际的Resource类来匹配YAML中定义的路径
        print(f"📊 合并后的配置包含 {len(combined_config['paths'])} 个路径")
        print(f"📊 合并后的配置包含 {len(combined_config['components']['schemas'])} 个Schema")
        print(f"📊 合并后的配置包含 {len(combined_config['tags'])} 个标签")
        
        # 将配置保存到API实例的属性中，供Swagger UI使用
        if api is not None:
            api.__dict__['_swagger_config'] = combined_config
        
        # 保存到全局变量
        global _combined_config
        _combined_config = combined_config
        
    except Exception as e:
        print(f"❌ 应用配置到API实例失败: {str(e)}")
    
    print("🎉 Swagger配置文件加载完成")

# 全局变量存储合并后的配置
_combined_config = None

def get_combined_swagger_config():
    """获取合并后的Swagger配置"""
    global _combined_config
    if _combined_config is None:
        # 如果还没有加载，先加载一次
        load_swagger_configs(None)
    return _combined_config

def create_swagger_api(app: Flask, title: str = "SHP Service API",
                      description: str = "GIS文件管理和地图服务API",
                      version: str = "1.0",
                      doc_url: str = "/swagger/"):
    """
    创建并配置Swagger API实例
    
    Args:
        app: Flask应用实例
        title: API标题
        description: API描述
        version: API版本
        doc_url: 文档访问URL
    
    Returns:
        Api: 配置好的Api实例
    """
    api = Api(
        app,
        version=version,
        title=title,
        description=description,
        doc=doc_url,
        prefix='/api'
    )
    
    # 加载所有Swagger配置
    load_swagger_configs(api)
    
    return api

# 预定义的API分组
API_TAGS = [
    {
        "name": "文件管理",
        "description": "文件上传、下载、管理相关接口"
    },
    {
        "name": "地图服务", 
        "description": "GeoService地图服务相关接口"
    },
    {
        "name": "图层管理",
        "description": "图层CRUD、样式管理相关接口"
    },
    {
        "name": "场景管理",
        "description": "3D场景管理相关接口"
    },
    {
        "name": "Martin瓦片服务",
        "description": "Martin瓦片服务相关接口"
    },
    {
        "name": "数据格式服务",
        "description": "DXF、GeoJSON、MBTiles等格式服务接口"
    },
    {
        "name": "样式管理",
        "description": "SLD样式管理相关接口"
    },
    {
        "name": "GIS工具",
        "description": "GIS通用工具接口"
    },
    {
        "name": "用户管理",
        "description": "用户认证、权限管理相关接口"
    },
    {
        "name": "系统管理",
        "description": "系统配置、连接管理相关接口"
    }
]

# 通用响应模型
COMMON_RESPONSES = {
    "200": {
        "description": "请求成功",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 200},
                        "message": {"type": "string", "example": "操作成功"},
                        "data": {"type": "object"}
                    }
                }
            }
        }
    },
    "400": {
        "description": "请求参数错误",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 400},
                        "message": {"type": "string", "example": "请求参数错误"},
                        "error": {"type": "string"}
                    }
                }
            }
        }
    },
    "401": {
        "description": "未授权访问",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 401},
                        "message": {"type": "string", "example": "未授权访问"}
                    }
                }
            }
        }
    },
    "404": {
        "description": "资源不存在",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 404},
                        "message": {"type": "string", "example": "资源不存在"}
                    }
                }
            }
        }
    },
    "500": {
        "description": "服务器内部错误",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "example": 500},
                        "message": {"type": "string", "example": "服务器内部错误"}
                    }
                }
            }
        }
    }
}
