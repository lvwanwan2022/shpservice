@echo off
chcp 65001 >nul

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 切换到项目目录
cd /d "%SCRIPT_DIR%"

REM 检查端口3000是否被占用
echo 🔍 检查端口3000占用情况...
netstat -an | findstr ":3000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 端口3000已被占用
    echo 💡 Martin服务已经在运行中
    echo 🌐 服务地址: http://localhost:3000
    echo ❌ 无需重复启动，退出
    exit /b 0
) else (
    echo ✅ 端口3000可用，可以启动Martin服务
)

REM 设置Martin可执行文件路径
set "MARTIN_EXECUTABLE=D:\simple_shpservice\martin-x86_64-pc-windows-msvc"

REM 检查可执行文件是否存在
if not exist "%MARTIN_EXECUTABLE%" (
    echo 错误: Martin可执行文件不存在 %MARTIN_EXECUTABLE%
    exit /b 1
)

REM 检查配置文件是否存在
if not exist "martin_config.yaml" (
    echo 错误: 配置文件不存在 martin_config.yaml
    exit /b 1
)

REM 启动Martin服务并显示窗口
start "" "%MARTIN_EXECUTABLE%" --config "%SCRIPT_DIR%martin_config.yaml"

echo ✅ Martin服务已启动
echo 可执行文件: %MARTIN_EXECUTABLE%
echo 配置文件: %SCRIPT_DIR%martin_config.yaml
echo 服务地址: http://localhost:3000

REM 等待一小段时间后再次检查端口是否被占用，确认启动成功
timeout /t 2 /nobreak >nul
echo.
echo 🔍 验证服务启动状态...
netstat -an | findstr ":3000 " >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Martin服务启动成功！端口3000已被占用
) else (
    echo ❌ Martin服务启动可能失败，端口3000未被占用
    echo 💡 请检查日志文件: %SCRIPT_DIR%martin_log.txt
) 