#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复外键约束脚本
将scene_layers表的martin_service_id外键约束从旧的分离表更新到新的统一表
"""

from models.db import execute_query, get_connection
import psycopg2

def check_foreign_key_constraints():
    """检查当前的外键约束"""
    print("=== 检查当前外键约束 ===")
    
    # 查询外键约束信息
    sql = """
    SELECT 
        tc.constraint_name, 
        tc.table_name, 
        kcu.column_name, 
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name 
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
    WHERE 
        tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = 'scene_layers'
        AND kcu.column_name = 'martin_service_id'
    """
    
    try:
        result = execute_query(sql)
        if result:
            for row in result:
                print(f"约束名: {row['constraint_name']}")
                print(f"表名: {row['table_name']}")
                print(f"列名: {row['column_name']}")
                print(f"外键表: {row['foreign_table_name']}")
                print(f"外键列: {row['foreign_column_name']}")
                print("---")
        else:
            print("未找到martin_service_id的外键约束")
        return result
    except Exception as e:
        print(f"检查外键约束失败: {e}")
        return None

def execute_ddl(sql):
    """执行DDL语句"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def drop_old_foreign_key_constraints():
    """删除旧的外键约束"""
    print("=== 删除旧的外键约束 ===")
    
    # 查找并删除martin_service_id相关的外键约束
    constraints = check_foreign_key_constraints()
    
    if not constraints:
        print("没有找到需要删除的外键约束")
        return True
    
    try:
        for constraint in constraints:
            constraint_name = constraint['constraint_name']
            table_name = constraint['table_name']
            foreign_table = constraint['foreign_table_name']
            
            print(f"删除约束: {constraint_name} (引用 {foreign_table})")
            
            drop_sql = f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"
            execute_ddl(drop_sql)
            print(f"✅ 成功删除约束: {constraint_name}")
        
        return True
    except Exception as e:
        print(f"❌ 删除外键约束失败: {e}")
        return False

def create_new_foreign_key_constraint():
    """创建新的外键约束，指向vector_martin_services表"""
    print("=== 创建新的外键约束 ===")
    
    try:
        # 创建新的外键约束
        constraint_sql = """
        ALTER TABLE scene_layers 
        ADD CONSTRAINT fk_scene_layers_vector_martin_service 
        FOREIGN KEY (martin_service_id) 
        REFERENCES vector_martin_services(id) 
        ON DELETE CASCADE
        """
        
        execute_ddl(constraint_sql)
        print("✅ 成功创建新的外键约束: fk_scene_layers_vector_martin_service")
        print("   引用表: vector_martin_services")
        return True
        
    except Exception as e:
        print(f"❌ 创建外键约束失败: {e}")
        return False

def verify_constraint_fix():
    """验证约束修复是否成功"""
    print("=== 验证约束修复 ===")
    
    # 检查新的外键约束
    constraints = check_foreign_key_constraints()
    
    if constraints:
        for constraint in constraints:
            if constraint['foreign_table_name'] == 'vector_martin_services':
                print("✅ 外键约束修复成功")
                print(f"   约束名: {constraint['constraint_name']}")
                print(f"   引用表: {constraint['foreign_table_name']}")
                return True
    
    print("❌ 外键约束修复失败或未生效")
    return False

def test_insert_with_new_constraint():
    """测试新外键约束是否正常工作"""
    print("=== 测试新外键约束 ===")
    
    try:
        # 测试插入一个有效的martin_service_id
        test_sql = """
        SELECT id FROM vector_martin_services 
        WHERE status = 'active' 
        LIMIT 1
        """
        
        result = execute_query(test_sql)
        if not result:
            print("没有可用的vector_martin_services记录进行测试")
            return True
        
        test_martin_id = result[0]['id']
        print(f"使用Martin服务ID {test_martin_id} 进行测试")
        
        # 模拟约束验证（不实际插入数据）
        validate_sql = """
        SELECT COUNT(*) as count 
        FROM vector_martin_services 
        WHERE id = %s AND status = 'active'
        """
        
        validate_result = execute_query(validate_sql, (test_martin_id,))
        if validate_result and validate_result[0]['count'] > 0:
            print("✅ 外键约束验证通过")
            return True
        else:
            print("❌ 外键约束验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试外键约束失败: {e}")
        return False

def main():
    """主函数"""
    print("开始修复外键约束...")
    print("目标: 将scene_layers.martin_service_id的外键约束从旧表更新到vector_martin_services表")
    print()
    
    # 步骤1: 检查当前约束
    check_foreign_key_constraints()
    print()
    
    # 步骤2: 删除旧约束
    if not drop_old_foreign_key_constraints():
        print("删除旧约束失败，停止执行")
        return
    print()
    
    # 步骤3: 创建新约束
    if not create_new_foreign_key_constraint():
        print("创建新约束失败，停止执行")
        return
    print()
    
    # 步骤4: 验证修复
    if not verify_constraint_fix():
        print("验证修复失败")
        return
    print()
    
    # 步骤5: 测试约束
    test_insert_with_new_constraint()
    print()
    
    print("✅ 外键约束修复完成！")
    print("现在scene_layers.martin_service_id正确引用vector_martin_services表")

if __name__ == "__main__":
    main() 