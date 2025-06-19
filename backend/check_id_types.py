#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库表ID字段类型并生成修改SQL
"""

from models.db import execute_query, get_connection

def check_id_column_types():
    """检查所有表的ID字段类型"""
    # 获取所有表名
    tables_query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    """
    tables = execute_query(tables_query)
    
    # 排除PostgreSQL内部表
    excluded_tables = ['spatial_ref_sys', 'geography_columns', 'geometry_columns', 
                     'raster_columns', 'raster_overviews']
    table_names = [table['table_name'] for table in tables 
                  if table['table_name'] not in excluded_tables]
    
    print(f"发现 {len(table_names)} 个表需要检查")
    
    # 检查每个表的ID列类型
    integer_id_tables = []
    bigint_id_tables = []
    no_id_tables = []
    
    for table_name in table_names:
        # 检查是否有ID列
        column_query = f"""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND column_name = 'id'
        """
        columns = execute_query(column_query)
        
        if not columns:
            no_id_tables.append(table_name)
            continue
            
        column = columns[0]
        data_type = column['data_type']
        column_default = column['column_default']
        
        if data_type == 'integer':
            integer_id_tables.append((table_name, column_default))
        elif data_type == 'bigint':
            bigint_id_tables.append(table_name)
    
    # 打印结果
    print("\n=== ID列类型检查结果 ===")
    print(f"已使用BIGINT类型的表 ({len(bigint_id_tables)}):")
    for table in bigint_id_tables:
        print(f"  - {table}")
    
    print(f"\n使用INTEGER类型的表 ({len(integer_id_tables)}):")
    for table, default in integer_id_tables:
        print(f"  - {table} (默认值: {default})")
    
    print(f"\n没有ID列的表 ({len(no_id_tables)}):")
    for table in no_id_tables:
        print(f"  - {table}")
    
    # 生成修改SQL
    if integer_id_tables:
        print("\n=== 修改INTEGER为BIGINT的SQL语句 ===")
        for table, default in integer_id_tables:
            # 如果有序列，需要先删除默认值，然后修改类型，最后重新创建序列
            if default and 'nextval' in default:
                sequence_name = default.split("'")[1]
                print(f"-- 修改表 {table}")
                print(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT;")
                print(f"ALTER TABLE {table} ALTER COLUMN id TYPE BIGINT;")
                print(f"DROP SEQUENCE IF EXISTS {sequence_name};")
                print(f"CREATE SEQUENCE {sequence_name} AS BIGINT;")
                print(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{sequence_name}');")
            else:
                print(f"ALTER TABLE {table} ALTER COLUMN id TYPE BIGINT;")
            print()

if __name__ == "__main__":
    check_id_column_types() 