#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DOM.tif文件发布测试脚本
演示新的publish_dom_geotiff方法的使用
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.geoserver_service import GeoServerService

def test_dom_publish():
    """测试DOM.tif文件发布"""
    
    # 初始化GeoServer服务
    geoserver = GeoServerService()
    
    # 测试文件路径
    tif_path = "G:/code/shpservice/FilesData/58cc01040e69460eb9fc8d96311d2e30.tif"
    store_name = "test_dom_store"  # 这个会被自动重新生成
    file_id = 12345  # 使用整数类型的file_id
    force_epsg = "EPSG:2343"  # 强制设置为EPSG:2343
    
    print("=" * 60)
    print("🎯 DOM.tif文件发布测试")
    print("=" * 60)
    print(f"文件路径: {tif_path}")
    print(f"强制坐标系: {force_epsg}")
    print(f"文件ID: {file_id}")
    print()
    
    try:
        # 使用新的DOM发布方法
        result = geoserver.publish_dom_geotiff(
            tif_path=tif_path,
            store_name=store_name,
            file_id=file_id,
            force_epsg=force_epsg
        )
        
        print("=" * 60)
        print("✅ DOM.tif发布成功！")
        print("=" * 60)
        print(f"存储名称: {result['store_name']}")
        print(f"图层名称: {result['layer_name']}")
        print(f"WMS URL: {result['wms_url']}")
        print(f"坐标系: {result['coordinate_system']}")
        print(f"透明度启用: {result['transparency_enabled']}")
        print(f"GDAL处理: {result['processed_with_gdal']}")
        print(f"原始坐标系: {result['original_srs']}")
        print()
        
        # 显示访问URL示例
        print("🌐 访问URL示例:")
        print(f"WMS GetMap: {result['wms_url']}&REQUEST=GetMap&LAYERS={result['layer_name']}&STYLES=&FORMAT=image/png&TRANSPARENT=true&VERSION=1.1.1&WIDTH=512&HEIGHT=512&SRS={result['coordinate_system']}&BBOX=...")
        print()
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print("❌ DOM.tif发布失败！")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        print()
        return False

def test_coordinate_check():
    """测试坐标系检查功能"""
    
    geoserver = GeoServerService()
    tif_path = "G:/code/shpservice/FilesData/58cc01040e69460eb9fc8d96311d2e30.tif"
    
    print("=" * 60)
    print("🔍 坐标系检查测试")
    print("=" * 60)
    print(f"文件路径: {tif_path}")
    print()
    
    try:
        # 检查坐标系信息
        result = geoserver._check_coordinate_system_with_gdalinfo(tif_path)
        
        print("📊 坐标系检查结果:")
        print(f"  原始坐标系: {result.get('srs')}")
        print(f"  需要修复: {result.get('needs_fix')}")
        print(f"  投影名称: {result.get('proj_name')}")
        print(f"  中央经线: {result.get('central_meridian')}")
        print()
        
        if result.get('needs_fix'):
            # 推断目标坐标系
            target_epsg = geoserver._determine_target_epsg(result)
            print(f"🎯 推断目标坐标系: {target_epsg}")
        
        return True
        
    except Exception as e:
        print(f"❌ 坐标系检查失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 开始DOM.tif发布测试...")
    print()
    
    # 1. 测试坐标系检查
    print("步骤1: 测试坐标系检查功能")
    coord_check_success = test_coordinate_check()
    
    if coord_check_success:
        print("✅ 坐标系检查测试通过")
    else:
        print("❌ 坐标系检查测试失败")
    
    print()
    
    # 2. 测试DOM发布
    print("步骤2: 测试DOM.tif发布功能")
    publish_success = test_dom_publish()
    
    if publish_success:
        print("✅ DOM.tif发布测试通过")
    else:
        print("❌ DOM.tif发布测试失败")
    
    print()
    print("=" * 60)
    if coord_check_success and publish_success:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
    print("=" * 60) 