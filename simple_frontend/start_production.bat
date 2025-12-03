@echo off
echo ========================================
echo   前端生产环境启动脚本
echo ========================================
echo.

echo 1. 安装依赖...
call npm install

echo.
echo 2. 构建生产版本...
call npm run build

echo.
echo 3. 启动生产服务器...
echo 本地访问: http://localhost:8080
echo 网络访问: http://10.20.148.169:8080
echo.
call npm start

pause
