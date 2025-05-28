#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
from requests.auth import HTTPBasicAuth
from .sld_template_service import SLDTemplateService

class StyleService:
    """样式服务类，用于生成SLD和管理GeoServer样式"""
    
    def __init__(self):
        self.sld_template_service = SLDTemplateService()
    
    def generate_sld_xml(self, style_config, style_name):
        """生成SLD样式XML - 使用新的模板服务"""
        try:
            # 使用新的SLD模板服务生成SLD内容
            sld_content = self.sld_template_service.generate_sld_from_style_config(
                style_config, style_name
            )
            
            return sld_content

        except Exception as e:
            print(f"生成SLD样式失败: {str(e)}")
            raise

    def create_or_update_geoserver_style(self, workspace_name, style_name, sld_content, layer_name, geoserver_config):
        """在GeoServer中创建或更新样式并应用到图层（别名方法）"""
        return self.create_geoserver_style(workspace_name, style_name, sld_content, layer_name, geoserver_config)

    def create_geoserver_style(self, workspace_name, style_name, sld_content, layer_name, geoserver_config):
        """在GeoServer中创建或更新样式并应用到图层"""
        try:
            geoserver_url = geoserver_config['url']
            username = geoserver_config['user']
            password = geoserver_config['password']
            
            auth = HTTPBasicAuth(username, password)
            headers = {
                'Content-Type': 'application/vnd.ogc.sld+xml; charset=utf-8'
            }
            
            print(f"准备创建/更新GeoServer样式: {workspace_name}:{style_name}")
            print(f"GeoServer URL: {geoserver_url}")
            print(f"SLD内容长度: {len(sld_content)} 字符")
            
            # 将SLD内容编码为UTF-8字节
            sld_bytes = sld_content.encode('utf-8')
            
            # 1. 检查样式是否存在并进行相应操作
            style_url = f"{geoserver_url}/rest/workspaces/{workspace_name}/styles/{style_name}"
            
            # 检查样式是否存在 - 增加详细日志
            print(f"正在检查样式是否存在: {style_url}")
            check_response = requests.get(style_url, auth=auth)
            print(f"检查样式存在性响应状态: {check_response.status_code}")
            
            if check_response.status_code == 200:
                # 样式存在，更新它
                print(f"样式 {style_name} 已存在，正在更新...")
                response = requests.put(style_url, data=sld_bytes, auth=auth, headers=headers)
                operation = "更新"
            elif check_response.status_code == 404:
                # 样式确实不存在，创建它
                print(f"样式 {style_name} 不存在，正在创建...")
                create_url = f"{geoserver_url}/rest/workspaces/{workspace_name}/styles"
                create_params = {'name': style_name}
                response = requests.post(create_url, data=sld_bytes, auth=auth, headers=headers, params=create_params)
                operation = "创建"
            else:
                # 其他状态码，可能是权限问题，尝试更新
                print(f"检查样式时返回状态码 {check_response.status_code}，尝试更新样式...")
                response = requests.put(style_url, data=sld_bytes, auth=auth, headers=headers)
                operation = "更新"
                
                # 如果更新失败且是403错误（样式已存在），说明检查逻辑有问题，但样式确实存在
                if response.status_code == 403 and "already exists" in response.text:
                    print(f"样式已存在但检查失败，可能是权限问题。直接尝试更新...")
                    # 样式存在，直接更新
                    response = requests.put(style_url, data=sld_bytes, auth=auth, headers=headers)
                    operation = "强制更新"
            
            print(f"{operation}操作响应状态: {response.status_code}")
            if response.status_code not in [200, 201]:
                print(f"响应内容: {response.text}")
            
            if response.status_code in [200, 201]:
                print(f"✅ 样式 {style_name} {operation}成功")
                
                # 2. 将样式应用到图层作为默认样式和关联样式
                result = self._apply_style_to_layer(
                    geoserver_url, workspace_name, style_name, layer_name, auth
                )
                return result
                    
            else:
                print(f"❌ 样式{operation}失败: {response.status_code} - {response.text}")
                return False
            
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到GeoServer服务器: {geoserver_url}")
            return False
        except Exception as e:
            print(f"❌ 创建/更新GeoServer样式失败: {str(e)}")
            return False
    
    def _apply_style_to_layer(self, geoserver_url, workspace_name, style_name, layer_name, auth):
        """将样式应用到图层（设置为默认样式和关联样式）"""
        try:
            layer_url = f"{geoserver_url}/rest/layers/{workspace_name}:{layer_name}"
            
            # 获取当前图层配置
            layer_response = requests.get(layer_url, auth=auth, headers={'Accept': 'application/json'})
            
            if layer_response.status_code == 200:
                layer_config = layer_response.json()
                
                # 更新默认样式
                if 'layer' in layer_config:
                    # 设置默认样式
                    layer_config['layer']['defaultStyle'] = {
                        'name': style_name,
                        'workspace': workspace_name
                    }
                    
                    # 确保样式也在available styles中
                    if 'styles' not in layer_config['layer']:
                        layer_config['layer']['styles'] = {'style': []}
                    
                    # 添加样式到available styles（如果不存在的话）
                    existing_styles = layer_config['layer']['styles'].get('style', [])
                    if not isinstance(existing_styles, list):
                        existing_styles = [existing_styles] if existing_styles else []
                    
                    style_exists = any(
                        style.get('name') == style_name and style.get('workspace') == workspace_name
                        for style in existing_styles
                    )
                    
                    if not style_exists:
                        existing_styles.append({
                            'name': style_name,
                            'workspace': workspace_name
                        })
                        layer_config['layer']['styles']['style'] = existing_styles
                    
                    # 发送更新请求
                    update_headers = {'Content-Type': 'application/json'}
                    update_response = requests.put(
                        layer_url, 
                        json=layer_config, 
                        auth=auth, 
                        headers=update_headers
                    )
                    
                    if update_response.status_code == 200:
                        print(f"✅ 图层 {layer_name} 样式应用成功")
                        
                        # 额外步骤：确保样式在Publishing选项卡中被正确关联
                        # 这通过上面的配置更新已经实现了Default和Associated的设置
                        return True
                    else:
                        print(f"❌ 图层样式应用失败: {update_response.status_code} - {update_response.text}")
                        return False
                else:
                    print(f"❌ 图层配置格式错误")
                    return False
            else:
                print(f"❌ 获取图层配置失败: {layer_response.status_code} - {layer_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 应用样式到图层失败: {str(e)}")
            return False
    
    def get_layer_styles(self, workspace_name, layer_name, geoserver_config):
        """获取图层的所有样式"""
        try:
            geoserver_url = geoserver_config['url']
            username = geoserver_config['user']
            password = geoserver_config['password']
            
            auth = HTTPBasicAuth(username, password)
            layer_url = f"{geoserver_url}/rest/layers/{workspace_name}:{layer_name}"
            
            response = requests.get(layer_url, auth=auth, headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                layer_config = response.json()
                layer_info = layer_config.get('layer', {})
                
                result = {
                    'default_style': layer_info.get('defaultStyle', {}),
                    'available_styles': layer_info.get('styles', {}).get('style', [])
                }
                
                return result
            else:
                print(f"❌ 获取图层样式失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 获取图层样式失败: {str(e)}")
            return None
    
    def delete_style(self, workspace_name, style_name, geoserver_config):
        """删除GeoServer中的样式"""
        try:
            geoserver_url = geoserver_config['url']
            username = geoserver_config['user']
            password = geoserver_config['password']
            
            auth = HTTPBasicAuth(username, password)
            style_url = f"{geoserver_url}/rest/workspaces/{workspace_name}/styles/{style_name}"
            
            # 添加查询参数以确保强制删除
            params = {'purge': 'true', 'recurse': 'true'}
            response = requests.delete(style_url, auth=auth, params=params)
            
            if response.status_code == 200:
                print(f"✅ 样式 {style_name} 删除成功")
                return True
            else:
                print(f"❌ 样式删除失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 删除样式失败: {str(e)}")
            return False
    
    def validate_style_config(self, style_config):
        """验证样式配置的有效性"""
        try:
            # 检查基本结构
            if not isinstance(style_config, dict):
                return False, "样式配置必须是字典格式"
            
            # 验证点样式
            if 'point' in style_config:
                point_config = style_config['point']
                if not isinstance(point_config, dict):
                    return False, "点样式配置格式错误"
                    
                # 检查颜色格式
                if 'color' in point_config:
                    if not self._is_valid_color(point_config['color']):
                        return False, "点颜色格式无效"
                        
                # 检查大小
                if 'size' in point_config:
                    if not isinstance(point_config['size'], (int, float)) or point_config['size'] <= 0:
                        return False, "点大小必须是正数"
            
            # 验证线样式
            if 'line' in style_config:
                line_config = style_config['line']
                if not isinstance(line_config, dict):
                    return False, "线样式配置格式错误"
                    
                # 检查颜色格式
                if 'color' in line_config:
                    if not self._is_valid_color(line_config['color']):
                        return False, "线颜色格式无效"
                        
                # 检查宽度
                if 'width' in line_config:
                    if not isinstance(line_config['width'], (int, float)) or line_config['width'] <= 0:
                        return False, "线宽必须是正数"
            
            # 验证面样式
            if 'polygon' in style_config:
                polygon_config = style_config['polygon']
                if not isinstance(polygon_config, dict):
                    return False, "面样式配置格式错误"
                    
                # 检查填充颜色
                if 'fillColor' in polygon_config:
                    if not self._is_valid_color(polygon_config['fillColor']):
                        return False, "填充颜色格式无效"
                        
                # 检查描边颜色
                if 'strokeColor' in polygon_config:
                    if not self._is_valid_color(polygon_config['strokeColor']):
                        return False, "描边颜色格式无效"
                        
                # 检查透明度
                if 'fillOpacity' in polygon_config:
                    opacity = polygon_config['fillOpacity']
                    if not isinstance(opacity, (int, float)) or not 0 <= opacity <= 1:
                        return False, "填充透明度必须在0-1之间"
            
            return True, "样式配置有效"
            
        except Exception as e:
            return False, f"验证样式配置时出错: {str(e)}"
    
    def _is_valid_color(self, color):
        """验证颜色格式是否有效（支持十六进制格式）"""
        if not isinstance(color, str):
            return False
            
        # 检查十六进制颜色格式
        if color.startswith('#'):
            hex_part = color[1:]
            if len(hex_part) in [3, 6]:
                try:
                    int(hex_part, 16)
                    return True
                except ValueError:
                    return False
        
        # 可以在这里添加其他颜色格式的支持（如RGB、颜色名称等）
        return False 
