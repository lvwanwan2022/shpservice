#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI 应用入口文件
用于生产环境部署
支持 WSGI (Flask) 和 ASGI (Uvicorn) 兼容
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')

# 导入应用
from app import app

# 🔥 添加 WSGI-to-ASGI 适配器支持
try:
    from asgiref.wsgi import WsgiToAsgi
    # 创建 ASGI 应用
    asgi_app = WsgiToAsgi(app)
    # 导出 ASGI 应用供 uvicorn 使用
    app = asgi_app
    print("✅ WSGI-to-ASGI 适配器已启用，支持 uvicorn 服务器")
except ImportError:
    print("⚠️  asgiref 未安装，将使用原生 WSGI 模式")
    print("   如需使用 uvicorn，请安装: pip install asgiref")
    # 保持原有的 WSGI 应用
    pass

if __name__ == '__main__':
    # 获取配置
    port = int(os.environ.get('PORT', 5030))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f'🚀 启动 SHP Service 后端服务')
    print(f'📱 本地访问: http://localhost:{port}')
    print(f'🌐 网络访问: http://10.20.124.20:{port}')
    print(f'📚 API文档: http://10.20.124.20:{port}/swagger/')
    
    # 启动应用
    app.run(host=host, port=port, debug=False)
