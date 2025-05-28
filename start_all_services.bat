@echo off
chcp 65001 >nul
echo =============================================================
echo 启动SHP服务系统 - 所有服务
echo =============================================================
echo.
echo 正在启动以下服务:
echo 1. 前端服务 (Vue.js)
echo 2. 后端服务 (Python Flask)
echo 3. Martin 地图服务
echo 4. GeoServer 服务
echo.

REM 获取当前脚本所在目录（去掉末尾反斜杠）
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 设置各服务的目录路径
set "FRONTEND_DIR=%SCRIPT_DIR%\frontend"
set "BACKEND_DIR=%SCRIPT_DIR%\backend"
set "GEOSERVER_DIR=D:\Program Files\GeoServer\bin"

echo 当前工作目录: %SCRIPT_DIR%
echo 前端目录: %FRONTEND_DIR%
echo 后端目录: %BACKEND_DIR%
echo GeoServer目录: %GEOSERVER_DIR%
echo.

REM 检查目录是否存在
if not exist "%FRONTEND_DIR%" (
    echo 错误: 前端目录不存在: %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%" (
    echo 错误: 后端目录不存在: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%GEOSERVER_DIR%" (
    echo 警告: GeoServer目录不存在: %GEOSERVER_DIR%
    echo 请检查GeoServer安装路径是否正确
)

REM 1. 启动前端服务
echo [1/4] 启动前端服务...
start "前端服务-Vue.js" cmd /k "cd /d "%FRONTEND_DIR%" && echo 正在启动前端服务... && npm run dev"

REM 等待2秒
timeout /t 2 /nobreak >nul

REM 2. 启动后端服务
echo [2/4] 启动后端服务...
start "后端服务-Flask" cmd /k "cd /d "%BACKEND_DIR%" && echo 正在启动后端服务... && python app.py"

REM 等待2秒
timeout /t 2 /nobreak >nul

REM 3. 启动Martin地图服务
echo [3/4] 启动Martin地图服务...
start "Martin地图服务" cmd /k "cd /d "%SCRIPT_DIR%" && echo 正在启动Martin地图服务... && martin --config martin_config.yaml"

REM 等待2秒
timeout /t 2 /nobreak >nul

REM 4. 启动GeoServer服务（如果目录存在）
if exist "%GEOSERVER_DIR%" (
    echo [4/4] 启动GeoServer服务...
    start "GeoServer服务" cmd /k "cd /d "%GEOSERVER_DIR%" && echo 正在启动GeoServer服务... && startup.bat"
) else (
    echo [4/4] 跳过GeoServer服务（目录不存在）
)

echo.
echo =============================================================
echo 所有服务启动完成！
echo =============================================================
echo.
echo 服务信息:
echo   前端服务: http://localhost:8080
echo   后端服务: http://localhost:5030
echo   Martin服务: http://localhost:3000
echo   GeoServer: http://localhost:8083/geoserver
echo.
echo 提示：
echo   - 各服务启动需要一些时间，请稍等
echo   - 如果某个服务启动失败，请检查相应的命令行窗口错误信息
echo   - 使用 stop_all_services.bat 可以停止所有服务
echo.
echo 按任意键关闭此窗口...
pause >nul 