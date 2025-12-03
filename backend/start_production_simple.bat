@echo off
REM ========================================
REM   SHP Service 生产环境快速启动
REM   适用于已配置环境的快速启动
REM ========================================

echo.
echo ========================================
echo   SHP Service 生产环境启动
echo ========================================
echo.

REM 设置环境变量
set FLASK_ENV=production
set PYTHONUNBUFFERED=1

REM 检查必要目录
if not exist logs mkdir logs
if not exist temp mkdir temp

REM 显示启动信息
echo 🚀 启动 SHP Service 生产环境
echo.
echo 📱 本地访问: http://localhost:5030
echo 🌐 网络访问: http://10.20.148.169:5030
echo 📚 API文档: http://10.20.148.169:5030/swagger/
echo.
echo ⚙️  配置: 高性能 Waitress + 资源监控
echo 📊 日志: logs/waitress_production.log
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

REM 启动高性能生产服务器
python waitress_production.py

echo.
echo 服务器已停止
pause
