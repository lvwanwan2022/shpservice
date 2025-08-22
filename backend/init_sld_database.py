#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SLD样式数据库初始化脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.sld_style_service import SLDStyleService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_sld_database():
    """初始化SLD样式数据库"""
    try:
        sld_service = SLDStyleService()
        
        logger.info("开始初始化SLD样式数据库...")
        
        # 初始化数据库表
        success = sld_service.initialize_database()
        
        if success:
            logger.info("✅ SLD样式数据库初始化成功")
            logger.info("已创建以下表:")
            logger.info("  - sld_styles: SLD样式文件表")
            logger.info("  - layer_sld_mapping: 图层SLD样式映射表")
            logger.info("  - 触发器: 自动更新updated_at字段")
            return True
        else:
            logger.error("❌ SLD样式数据库初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ SLD样式数据库初始化过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("SLD样式数据库初始化工具")
    print("=" * 50)
    
    success = init_sld_database()
    
    if success:
        print("\n✅ 初始化完成！")
        print("\n现在你可以:")
        print("1. 启动后端服务")
        print("2. 在前端使用SLD样式管理功能")
        print("3. 上传和管理SLD样式文件")
        print("4. 为GeoServer图层应用SLD样式")
    else:
        print("\n❌ 初始化失败！")
        print("请检查:")
        print("1. 数据库连接配置")
        print("2. 数据库权限")
        print("3. 错误日志信息")
        sys.exit(1)
