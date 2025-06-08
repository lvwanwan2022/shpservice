@echo off
REM 后台启动Martin服务（不显示窗口）

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 切换到项目目录
cd /d "%SCRIPT_DIR%"

REM 检查配置文件
if not exist "martin_config.yaml" (
    exit /b 1
)

REM 后台启动Martin
start /B martin --config martin_config.yaml 