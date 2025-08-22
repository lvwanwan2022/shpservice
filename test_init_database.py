#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('backend')

from models.db import init_database, execute_query

print("=== 测试数据库初始化 ===")

# 先删除SLD相关表以测试重新创建
print("删除现有SLD表进行测试...")
try:
    execute_query("DROP TABLE IF EXISTS layer_sld_mapping CASCADE", fetch=False)
    execute_query("DROP TABLE IF EXISTS sld_styles CASCADE", fetch=False)
    print("✅ 现有SLD表已删除")
except Exception as e:
    print(f"删除表时出错（可能不存在）: {e}")

# 运行数据库初始化
print("\n开始运行数据库初始化...")
try:
    init_database()
    print("\n✅ 数据库初始化完成")
except Exception as e:
    print(f"\n❌ 数据库初始化失败: {e}")

# 验证SLD表是否创建成功
print("\n=== 验证SLD表创建结果 ===")
try:
    # 检查sld_styles表
    result1 = execute_query("SELECT COUNT(*) as count FROM sld_styles")
    print(f"✅ sld_styles表存在，记录数: {result1[0]['count']}")
except Exception as e:
    print(f"❌ sld_styles表检查失败: {e}")

try:
    # 检查layer_sld_mapping表
    result2 = execute_query("SELECT COUNT(*) as count FROM layer_sld_mapping")
    print(f"✅ layer_sld_mapping表存在，记录数: {result2[0]['count']}")
except Exception as e:
    print(f"❌ layer_sld_mapping表检查失败: {e}")

print("\n=== 测试完成 ===")
