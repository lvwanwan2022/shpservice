#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SLD样式管理功能测试脚本
"""

import requests
import json
import os

# 测试配置
BASE_URL = "http://localhost:5030"
API_BASE = f"{BASE_URL}/api/sld-styles"

def test_initialize_database():
    """测试数据库初始化"""
    print("🔧 测试数据库初始化...")
    try:
        response = requests.post(f"{API_BASE}/initialize")
        if response.status_code == 200:
            print("✅ 数据库初始化成功")
            return True
        else:
            print(f"❌ 数据库初始化失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 数据库初始化异常: {str(e)}")
        return False

def test_get_sld_styles():
    """测试获取SLD样式列表"""
    print("📋 测试获取SLD样式列表...")
    try:
        response = requests.get(API_BASE)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取样式列表成功，共 {data.get('total', 0)} 个样式")
            return True
        else:
            print(f"❌ 获取样式列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取样式列表异常: {str(e)}")
        return False

def test_upload_sld_file():
    """测试上传SLD文件"""
    print("📤 测试上传SLD文件...")
    
    # 创建一个简单的测试SLD文件
    test_sld_content = '''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
 xmlns="http://www.opengis.net/sld" 
 xmlns:ogc="http://www.opengis.net/ogc" 
 xmlns:xlink="http://www.w3.org/1999/xlink" 
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>test_point_style</Name>
    <UserStyle>
      <Title>Test Point Style</Title>
      <Abstract>A test style for point features</Abstract>
      <FeatureTypeStyle>
        <Rule>
          <Name>point_rule</Name>
          <Title>Point Style</Title>
          <Abstract>Point symbolizer</Abstract>
            <PointSymbolizer>
              <Graphic>
                <Mark>
                  <WellKnownName>circle</WellKnownName>
                  <Fill>
                    <CssParameter name="fill">#FF0000</CssParameter>
                    <CssParameter name="fill-opacity">1.0</CssParameter>
                  </Fill>
                </Mark>
              <Size>8</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
    
    # 创建临时测试文件
    test_file_path = "test_style.sld"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_sld_content)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_style.sld', f, 'application/xml')}
            data = {
                'name': '测试点样式',
                'description': '这是一个测试用的点样式',
                'geometry_type': 'point'
            }
            response = requests.post(f"{API_BASE}/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SLD文件上传成功")
            print(f"   样式ID: {result.get('data', {}).get('id')}")
            return result.get('data', {}).get('id')
        else:
            print(f"❌ SLD文件上传失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"❌ SLD文件上传异常: {str(e)}")
        return None
    finally:
        # 清理临时文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_apply_style_to_layer(style_id):
    """测试应用样式到图层"""
    if not style_id:
        print("⚠️ 跳过样式应用测试（无样式ID）")
        return False
    
    print(f"🎨 测试应用样式到图层 (样式ID: {style_id})...")
    try:
        # 这里使用一个测试图层ID，实际使用时需要替换为真实的图层ID
        test_layer_id = 1
        data = {
            'layer_id': test_layer_id,
            'sld_style_id': style_id
        }
        response = requests.post(f"{API_BASE}/apply", json=data)
        
        if response.status_code == 200:
            print("✅ 样式应用成功")
            return True
        else:
            print(f"❌ 样式应用失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 样式应用异常: {str(e)}")
        return False

def test_get_layer_style(layer_id=1):
    """测试获取图层当前样式"""
    print(f"📖 测试获取图层当前样式 (图层ID: {layer_id})...")
    try:
        response = requests.get(f"{API_BASE}/layer/{layer_id}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 获取图层样式成功")
            print(f"   样式名称: {data.get('data', {}).get('name')}")
            return True
        elif response.status_code == 404:
            print("ℹ️ 图层没有应用样式")
            return True
        else:
            print(f"❌ 获取图层样式失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取图层样式异常: {str(e)}")
        return False

def test_download_style(style_id):
    """测试下载SLD文件"""
    if not style_id:
        print("⚠️ 跳过样式下载测试（无样式ID）")
        return False
    
    print(f"📥 测试下载SLD文件 (样式ID: {style_id})...")
    try:
        response = requests.get(f"{API_BASE}/{style_id}/download")
        if response.status_code == 200:
            print("✅ SLD文件下载成功")
            # 保存下载的文件
            with open(f"downloaded_style_{style_id}.sld", 'wb') as f:
                f.write(response.content)
            print(f"   文件已保存为: downloaded_style_{style_id}.sld")
            return True
        else:
            print(f"❌ SLD文件下载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SLD文件下载异常: {str(e)}")
        return False

def test_delete_style(style_id):
    """测试删除SLD样式"""
    if not style_id:
        print("⚠️ 跳过样式删除测试（无样式ID）")
        return False
    
    print(f"🗑️ 测试删除SLD样式 (样式ID: {style_id})...")
    try:
        response = requests.delete(f"{API_BASE}/{style_id}")
        if response.status_code == 200:
            print("✅ SLD样式删除成功")
            return True
        else:
            print(f"❌ SLD样式删除失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SLD样式删除异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始SLD样式管理功能测试")
    print("=" * 50)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未正常运行")
            return
    except:
        print("❌ 无法连接到后端服务，请确保服务已启动")
        return
    
    print("✅ 后端服务连接正常")
    print()
    
    # 执行测试
    tests = [
        ("数据库初始化", test_initialize_database),
        ("获取样式列表", test_get_sld_styles),
        ("上传SLD文件", test_upload_sld_file),
        ("应用样式到图层", lambda: test_apply_style_to_layer(style_id)),
        ("获取图层样式", test_get_layer_style),
        ("下载SLD文件", lambda: test_download_style(style_id)),
        ("删除SLD样式", lambda: test_delete_style(style_id)),
    ]
    
    style_id = None
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 测试: {test_name}")
        print("-" * 30)
        
        try:
            if "上传SLD文件" in test_name:
                result = test_func()
                if result:
                    style_id = result
                    passed += 1
            elif "应用样式到图层" in test_name or "下载SLD文件" in test_name or "删除SLD样式" in test_name:
                if test_func():
                    passed += 1
            else:
                if test_func():
                    passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
        
        print()
    
    # 测试结果汇总
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！SLD样式管理功能正常工作")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    # 清理下载的文件
    for file in os.listdir('.'):
        if file.startswith('downloaded_style_') and file.endswith('.sld'):
            try:
                os.remove(file)
                print(f"🧹 已清理临时文件: {file}")
            except:
                pass

if __name__ == "__main__":
    main()
