#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查GeoServer REST API中是否存在指定的工作空间
"""

import requests
import json
import sys
import os

def check_geoserver_workspace(url, workspace, username='admin', password='geoserver'):
    """
    检查GeoServer REST API中是否存在指定的工作空间
    
    Args:
        url: GeoServer URL (例如 http://localhost:8083/geoserver)
        workspace: 工作空间名称
        username: GeoServer管理员用户名
        password: GeoServer管理员密码
        
    Returns:
        存在返回True，不存在返回False
    """
    # 构建REST API URL
    rest_url = f"{url}/rest"
    workspace_url = f"{rest_url}/workspaces/{workspace}"
    
    print(f"检查GeoServer工作空间: {workspace}")
    print(f"REST API URL: {workspace_url}")
    
    try:
        # 发送请求
        response = requests.get(
            workspace_url,
            auth=(username, password),
            headers={'Accept': 'application/json'}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 工作空间存在
            try:
                workspace_data = response.json()
                print(f"工作空间信息: {json.dumps(workspace_data, indent=2, ensure_ascii=False)}")
            except:
                print("无法解析响应JSON")
            
            print(f"✅ 工作空间 '{workspace}' 存在")
            return True
        elif response.status_code == 404:
            # 工作空间不存在
            print(f"❌ 工作空间 '{workspace}' 不存在")
            return False
        else:
            # 其他错误
            print(f"⚠️ 检查失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:500]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他异常: {str(e)}")
        return False

def create_geoserver_workspace(url, workspace, username='admin', password='geoserver'):
    """
    在GeoServer中创建工作空间
    
    Args:
        url: GeoServer URL (例如 http://localhost:8083/geoserver)
        workspace: 工作空间名称
        username: GeoServer管理员用户名
        password: GeoServer管理员密码
        
    Returns:
        创建成功返回True，失败返回False
    """
    # 构建REST API URL
    rest_url = f"{url}/rest"
    workspaces_url = f"{rest_url}/workspaces"
    
    print(f"创建GeoServer工作空间: {workspace}")
    print(f"REST API URL: {workspaces_url}")
    
    # 构建请求体
    workspace_data = {
        "workspace": {
            "name": workspace
        }
    }
    
    try:
        # 发送请求
        response = requests.post(
            workspaces_url,
            auth=(username, password),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(workspace_data)
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code in [201, 200]:
            # 工作空间创建成功
            print(f"✅ 工作空间 '{workspace}' 创建成功")
            return True
        else:
            # 创建失败
            print(f"❌ 工作空间创建失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:500]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他异常: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # 从配置文件加载GeoServer配置
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from backend.config import GEOSERVER_CONFIG
        
        url = GEOSERVER_CONFIG['url']
        workspace = GEOSERVER_CONFIG['workspace']
        username = GEOSERVER_CONFIG['user']
        password = GEOSERVER_CONFIG['password']
        
        print(f"GeoServer URL: {url}")
        print(f"工作空间: {workspace}")
        print(f"用户名: {username}")
        print(f"密码: {'*' * len(password)}")
        print()
        
        # 检查工作空间是否存在
        exists = check_geoserver_workspace(url, workspace, username, password)
        
        # 如果不存在，尝试创建
        if not exists:
            print("\n工作空间不存在，尝试创建...")
            create_geoserver_workspace(url, workspace, username, password)
            
            # 再次检查是否创建成功
            print("\n验证工作空间是否创建成功...")
            check_geoserver_workspace(url, workspace, username, password)
            
    except ImportError:
        print("无法导入配置，使用默认参数")
        url = "http://localhost:8083/geoserver"
        workspace = "shpservice"
        username = "admin"
        password = "geoserver"
        
        # 检查工作空间是否存在
        check_geoserver_workspace(url, workspace, username, password)
    except Exception as e:
        print(f"脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc() 