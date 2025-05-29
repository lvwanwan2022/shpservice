@echo off
chcp 65001 >nul
echo ==========================================
echo        启动 Martin 地图瓦片服务
echo ==========================================

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
echo 当前目录: %SCRIPT_DIR%

REM 切换到项目目录
cd /d "%SCRIPT_DIR%"

REM 检查配置文件是否存在
if not exist "martin_config.yaml" (
    echo ❌ 错误: 配置文件不存在 martin_config.yaml
    pause
    exit /b 1
)

echo ✅ 找到配置文件: martin_config.yaml

REM 检查Martin是否已安装
martin --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Martin 未安装或不在PATH中
    echo 请先安装Martin: cargo install martin
    pause
    exit /b 1
)

echo ✅ Martin 已安装

REM 启动Martin服务
echo.
echo 🚀 正在启动 Martin 地图瓦片服务...
echo 配置文件: martin_config.yaml
echo 服务地址: http://localhost:3000
echo.
echo 按 Ctrl+C 可停止服务
echo ==========================================

martin --config martin_config.yaml

echo.
echo ❌ Martin 服务已停止
pause 