@echo off
chcp 65001 >nul
echo ========================================
echo SLD样式管理功能启动脚本
echo ========================================
echo.

echo 🔧 步骤1: 初始化SLD数据库...
cd backend
python init_sld_database.py
if %errorlevel% neq 0 (
    echo ❌ 数据库初始化失败！
    pause
    exit /b 1
)
echo ✅ 数据库初始化完成
echo.

echo 🚀 步骤2: 启动后端服务...
start "Backend Service" cmd /k "python app.py"
echo ✅ 后端服务已启动 (端口5030)
echo.

echo 🌐 步骤3: 启动前端服务...
cd ..\simple_frontend
start "Frontend Service" cmd /k "npm run serve"
echo ✅ 前端服务已启动
echo.

echo 📋 步骤4: 等待服务启动...
timeout /t 10 /nobreak >nul
echo.

echo 🎉 所有服务已启动！
echo.
echo 📱 前端地址: http://localhost:8080
echo 🔧 后端地址: http://localhost:5030
echo.
echo 📖 使用说明:
echo 1. 打开浏览器访问 http://localhost:8080
echo 2. 进入地图页面
echo 3. 右键点击图层选择"样式设置"
echo 4. 选择"SLD样式"选项卡
echo 5. 上传或选择SLD样式文件
echo 6. 点击"应用"按钮
echo.
echo 🧪 运行测试: python test_sld_functionality.py
echo.
pause
