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

REM 从Python配置文件中获取Martin可执行文件路径
echo 正在从配置文件获取Martin可执行文件路径...
set "MARTIN_EXECUTABLE="
for /f "tokens=*" %%a in ('python -c "from backend.config import MARTIN_CONFIG; print(MARTIN_CONFIG['martin_executable'])"') do (
    set "MARTIN_EXECUTABLE=%%a"
)

REM 检查是否成功获取到路径
if "%MARTIN_EXECUTABLE%"=="" (
    echo ❌ 错误: 无法从配置文件获取Martin可执行文件路径
    echo 将尝试使用系统PATH中的martin命令
    set "MARTIN_EXECUTABLE=martin"
) else (
    echo ✅ 从配置文件获取到Martin可执行文件路径: %MARTIN_EXECUTABLE%
    REM 检查可执行文件是否存在
    if not exist "%MARTIN_EXECUTABLE%" (
        echo ❌ 错误: 配置的Martin可执行文件不存在: %MARTIN_EXECUTABLE%
        echo 将尝试使用系统PATH中的martin命令
        set "MARTIN_EXECUTABLE=martin"
    )
)

REM 检查配置文件是否存在
if not exist "martin_config.yaml" (
    echo ❌ 错误: 配置文件不存在 martin_config.yaml
    pause
    exit /b 1
)

echo ✅ 找到配置文件: martin_config.yaml

REM 检查Martin是否可用
"%MARTIN_EXECUTABLE%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Martin 未安装或路径无效: %MARTIN_EXECUTABLE%
    pause
    exit /b 1
)

echo ✅ Martin 可执行文件有效: %MARTIN_EXECUTABLE%

REM 启动Martin服务
echo.
echo 🚀 正在启动 Martin 地图瓦片服务...
echo 可执行文件: %MARTIN_EXECUTABLE%
echo 配置文件: martin_config.yaml
echo 服务地址: http://localhost:3000
echo.
echo 按 Ctrl+C 可停止服务
echo ==========================================

"%MARTIN_EXECUTABLE%" --config martin_config.yaml

echo.
echo ❌ Martin 服务已停止
pause 