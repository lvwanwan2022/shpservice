#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TIF 转 MBTiles 测试程序
用于测试 TifMartinService 的转换功能
"""

import os
import sys
import time
import uuid
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入必要的模块
from services.tif_martin_service import TifMartinService
from config import MARTIN_CONFIG, FILE_STORAGE

def test_tif_to_mbtiles_conversion():
    """测试 TIF 转 MBTiles 转换功能"""
    
    print("🚀 开始测试 TIF 转 MBTiles 转换功能")
    print("=" * 60)
    
    # 创建服务实例
    service = TifMartinService()
    
    # 测试文件路径 - 请根据实际情况修改
    test_tif_path = input("请输入要测试的 TIF 文件路径 (或按回车使用默认路径): ").strip()
    
    if not test_tif_path:
        # 默认测试路径
        default_path = os.path.join(FILE_STORAGE['upload_folder'], 'test.tif')
        if os.path.exists(default_path):
            test_tif_path = default_path
        else:
            print("❌ 未找到默认测试文件，请手动输入文件路径")
            return False
    
    # 检查文件是否存在
    if not os.path.exists(test_tif_path):
        print(f"❌ 文件不存在: {test_tif_path}")
        return False
    
    print(f"📁 测试文件: {test_tif_path}")
    print(f"📊 文件大小: {os.path.getsize(test_tif_path) / (1024*1024):.2f} MB")
    
    # 生成测试参数
    file_id = str(uuid.uuid4())
    original_filename = os.path.basename(test_tif_path)
    user_id = "test_user"
    task_id = f"test_task_{int(time.time())}"
    
    print(f"🆔 文件ID: {file_id}")
    print(f"👤 用户ID: {user_id}")
    print(f"📋 任务ID: {task_id}")
    
    # 转换参数
    max_zoom = 18
    min_zoom = 2
    
    print(f"🔍 缩放级别: {min_zoom} - {max_zoom}")
    print("=" * 60)
    
    try:
        # 开始转换
        print("🔄 开始转换...")
        start_time = time.time()
        
        # 调用转换方法
        result = service.tif_to_mbtiles_and_publish(
            file_id=file_id,
            file_path=test_tif_path,
            original_filename=original_filename,
            user_id=user_id,
            max_zoom=max_zoom,
            min_zoom=min_zoom,
            task_id=task_id
        )
        
        end_time = time.time()
        conversion_time = end_time - start_time
        
        print("=" * 60)
        print("📊 转换结果:")
        print(f"  状态: {'✅ 成功' if result else '❌ 失败'}")
        print(f"  耗时: {conversion_time:.2f} 秒")
        
        if result:
            print("🎉 转换成功完成！")
            
            # 检查生成的文件
            mbtiles_path = result.get('mbtiles_path', '')
            if mbtiles_path and os.path.exists(mbtiles_path):
                mbtiles_size = os.path.getsize(mbtiles_path) / (1024*1024)
                print(f"📦 MBTiles 文件: {mbtiles_path}")
                print(f"📊 MBTiles 大小: {mbtiles_size:.2f} MB")
                
                # 检查瓦片目录
                tiles_dir = result.get('tiles_dir', '')
                if tiles_dir and os.path.exists(tiles_dir):
                    tile_count = 0
                    for root, dirs, files in os.walk(tiles_dir):
                        tile_count += len([f for f in files if f.endswith('.png')])
                    print(f"🧱 生成瓦片数量: {tile_count}")
            
            # 检查 Martin 服务状态
            print("\n🔍 检查 Martin 服务状态...")
            try:
                import requests
                martin_url = f"http://{MARTIN_CONFIG['host']}:{MARTIN_CONFIG['port']}/health"
                response = requests.get(martin_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Martin 服务运行正常")
                else:
                    print(f"⚠️ Martin 服务响应异常: {response.status_code}")
            except Exception as e:
                print(f"❌ 无法连接到 Martin 服务: {str(e)}")
        
        else:
            print("❌ 转换失败")
            # 显示错误信息
            if hasattr(service, 'progress_data') and task_id in service.progress_data:
                error_info = service.progress_data[task_id]
                print(f"错误详情: {error_info.get('message', '未知错误')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 转换过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_conversion():
    """测试批量转换功能"""
    
    print("\n🔄 开始测试批量转换功能")
    print("=" * 60)
    
    # 创建服务实例
    service = TifMartinService()
    
    # 查找测试目录中的所有 TIF 文件
    test_dir = input("请输入包含 TIF 文件的测试目录路径 (或按回车使用默认路径): ").strip()
    
    if not test_dir:
        test_dir = FILE_STORAGE['upload_folder']
    
    if not os.path.exists(test_dir):
        print(f"❌ 目录不存在: {test_dir}")
        return False
    
    # 查找所有 TIF 文件
    tif_files = []
    for ext in ['.tif', '.tiff']:
        tif_files.extend(Path(test_dir).glob(f"*{ext}"))
    
    if not tif_files:
        print(f"❌ 在目录 {test_dir} 中未找到 TIF 文件")
        return False
    
    print(f"📁 测试目录: {test_dir}")
    print(f"🔍 找到 {len(tif_files)} 个 TIF 文件:")
    
    for i, tif_file in enumerate(tif_files, 1):
        size_mb = tif_file.stat().st_size / (1024*1024)
        print(f"  {i}. {tif_file.name} ({size_mb:.2f} MB)")
    
    # 选择要测试的文件
    try:
        choice = input(f"\n请选择要测试的文件编号 (1-{len(tif_files)}) 或输入 'all' 测试所有文件: ").strip()
        
        if choice.lower() == 'all':
            selected_files = tif_files
        else:
            file_index = int(choice) - 1
            if 0 <= file_index < len(tif_files):
                selected_files = [tif_files[file_index]]
            else:
                print("❌ 无效的选择")
                return False
    except ValueError:
        print("❌ 请输入有效的数字")
        return False
    
    print(f"\n🚀 开始批量转换 {len(selected_files)} 个文件...")
    
    success_count = 0
    total_time = 0
    
    for i, tif_file in enumerate(selected_files, 1):
        print(f"\n📁 处理文件 {i}/{len(selected_files)}: {tif_file.name}")
        print("-" * 40)
        
        try:
            # 生成测试参数
            file_id = str(uuid.uuid4())
            user_id = "batch_test_user"
            task_id = f"batch_test_task_{int(time.time())}_{i}"
            
            start_time = time.time()
            
            # 执行转换
            result = service.tif_to_mbtiles_and_publish(
                file_id=file_id,
                file_path=str(tif_file),
                original_filename=tif_file.name,
                user_id=user_id,
                max_zoom=16,  # 降低缩放级别以加快测试
                min_zoom=2,
                task_id=task_id
            )
            
            end_time = time.time()
            file_time = end_time - start_time
            total_time += file_time
            
            if result:
                success_count += 1
                print(f"✅ 转换成功 - 耗时: {file_time:.2f} 秒")
            else:
                print(f"❌ 转换失败 - 耗时: {file_time:.2f} 秒")
                
        except Exception as e:
            print(f"❌ 转换异常: {str(e)}")
    
    # 输出批量转换结果
    print("\n" + "=" * 60)
    print("📊 批量转换结果:")
    print(f"  总文件数: {len(selected_files)}")
    print(f"  成功数量: {success_count}")
    print(f"  失败数量: {len(selected_files) - success_count}")
    print(f"  成功率: {(success_count/len(selected_files)*100):.1f}%")
    print(f"  总耗时: {total_time:.2f} 秒")
    print(f"  平均耗时: {(total_time/len(selected_files)):.2f} 秒/文件")

def main():
    """主函数"""
    print("🧪 TIF 转 MBTiles 测试程序")
    print("=" * 60)
    
    while True:
        print("\n请选择测试模式:")
        print("1. 单文件转换测试")
        print("2. 批量转换测试")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            test_tif_to_mbtiles_conversion()
        elif choice == '2':
            test_batch_conversion()
        elif choice == '3':
            print("👋 测试程序结束")
            break
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序运行异常: {str(e)}")
        import traceback
        traceback.print_exc()
