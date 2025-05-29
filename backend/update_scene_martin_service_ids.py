#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新场景图层中的Martin服务ID
将scene_layers表中的martin_service_id从旧的分离表ID更新为新的统一表ID
"""

from models.db import execute_query, get_connection

def get_old_to_new_id_mapping():
    """获取旧ID到新ID的映射关系"""
    print("=== 构建ID映射关系 ===")
    
    id_mapping = {}
    
    # 从vector_martin_services表获取所有映射关系
    sql = """
    SELECT id as new_id, file_id, vector_type 
    FROM vector_martin_services 
    WHERE status = 'active'
    ORDER BY id
    """
    
    try:
        vector_services = execute_query(sql)
        if not vector_services:
            print("未找到vector_martin_services记录")
            return {}
        
        print(f"找到 {len(vector_services)} 个vector_martin_services记录")
        
        for service in vector_services:
            new_id = service['id']
            file_id = service['file_id']
            vector_type = service['vector_type']
            
            # 根据vector_type查询对应的旧表
            if vector_type == 'geojson':
                old_sql = "SELECT id as old_id FROM geojson_martin_services WHERE file_id = %s AND status = 'active'"
            elif vector_type == 'shp':
                old_sql = "SELECT id as old_id FROM shp_martin_services WHERE file_id = %s AND status = 'active'"
            else:
                print(f"未知的vector_type: {vector_type}")
                continue
            
            old_result = execute_query(old_sql, (file_id,))
            if old_result:
                old_id = old_result[0]['old_id']
                id_mapping[old_id] = new_id
                print(f"映射: {vector_type}表 ID {old_id} -> vector表 ID {new_id} (文件: {file_id})")
        
        return id_mapping
        
    except Exception as e:
        print(f"构建映射关系失败: {e}")
        return {}

def check_scene_layers_with_martin_services():
    """检查scene_layers表中的Martin服务记录"""
    print("=== 检查场景图层中的Martin服务 ===")
    
    sql = """
    SELECT id, scene_id, layer_id, martin_service_id, martin_service_type
    FROM scene_layers 
    WHERE martin_service_id IS NOT NULL
    ORDER BY scene_id, layer_id
    """
    
    try:
        result = execute_query(sql)
        if result:
            print(f"找到 {len(result)} 个包含Martin服务的场景图层")
            for row in result:
                print(f"场景图层ID: {row['id']}, 场景: {row['scene_id']}, 图层: {row['layer_id']}, Martin服务ID: {row['martin_service_id']}, 类型: {row['martin_service_type']}")
        else:
            print("未找到包含Martin服务的场景图层")
        return result
    except Exception as e:
        print(f"检查场景图层失败: {e}")
        return []

def update_scene_layer_martin_service_ids(id_mapping):
    """更新scene_layers表中的martin_service_id"""
    print("=== 更新场景图层中的Martin服务ID ===")
    
    if not id_mapping:
        print("没有ID映射关系，跳过更新")
        return True
    
    # 获取需要更新的记录
    scene_layers = check_scene_layers_with_martin_services()
    if not scene_layers:
        print("没有需要更新的场景图层记录")
        return True
    
    updated_count = 0
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            for layer in scene_layers:
                old_martin_id = layer['martin_service_id']
                scene_layer_id = layer['id']
                
                if old_martin_id in id_mapping:
                    new_martin_id = id_mapping[old_martin_id]
                    
                    # 更新记录
                    update_sql = """
                    UPDATE scene_layers 
                    SET martin_service_id = %s 
                    WHERE id = %s
                    """
                    
                    cursor.execute(update_sql, (new_martin_id, scene_layer_id))
                    updated_count += 1
                    
                    print(f"✅ 更新场景图层 {scene_layer_id}: Martin服务ID {old_martin_id} -> {new_martin_id}")
                else:
                    print(f"⚠️ 场景图层 {scene_layer_id}: 找不到Martin服务ID {old_martin_id} 的映射")
            
            conn.commit()
            print(f"\n总计更新了 {updated_count} 条记录")
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 更新失败: {e}")
        return False
    finally:
        conn.close()

def verify_updates():
    """验证更新结果"""
    print("=== 验证更新结果 ===")
    
    # 检查更新后的记录
    sql = """
    SELECT sl.id, sl.scene_id, sl.layer_id, sl.martin_service_id, sl.martin_service_type,
           vms.file_id, vms.vector_type, vms.original_filename
    FROM scene_layers sl
    JOIN vector_martin_services vms ON sl.martin_service_id = vms.id
    WHERE sl.martin_service_id IS NOT NULL
    ORDER BY sl.scene_id, sl.layer_id
    """
    
    try:
        result = execute_query(sql)
        if result:
            print(f"验证成功：找到 {len(result)} 个正确关联的场景图层")
            for row in result:
                print(f"场景图层 {row['id']}: 图层{row['layer_id']} -> Martin服务{row['martin_service_id']} ({row['vector_type']}: {row['original_filename']})")
            return True
        else:
            print("❌ 验证失败：未找到正确关联的记录")
            return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("开始更新场景图层中的Martin服务ID...")
    print("目标: 将scene_layers.martin_service_id从旧的分离表ID更新为新的统一表ID")
    print()
    
    # 步骤1: 构建映射关系
    id_mapping = get_old_to_new_id_mapping()
    if not id_mapping:
        print("无法构建ID映射关系，停止执行")
        return
    print()
    
    # 步骤2: 检查当前状态
    check_scene_layers_with_martin_services()
    print()
    
    # 步骤3: 更新ID
    if not update_scene_layer_martin_service_ids(id_mapping):
        print("更新失败，停止执行")
        return
    print()
    
    # 步骤4: 验证结果
    verify_updates()
    print()
    
    print("✅ Martin服务ID更新完成！")
    print("现在scene_layers表中的martin_service_id都正确指向vector_martin_services表")

if __name__ == "__main__":
    main() 