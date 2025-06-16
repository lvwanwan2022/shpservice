@echo off
chcp 65001 >nul

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 切换到项目目录
cd /d "%SCRIPT_DIR%"

REM 从Python配置文件中获取Martin可执行文件路径
set "MARTIN_EXECUTABLE="
for /f "tokens=*" %%a in ('python -c "from backend.config import MARTIN_CONFIG; print(MARTIN_CONFIG['martin_executable'])"') do (
    set "MARTIN_EXECUTABLE=%%a"
)

REM 检查是否成功获取到路径
if "%MARTIN_EXECUTABLE%"=="" (
    echo 无法从配置文件获取Martin可执行文件路径，使用默认路径
    set "MARTIN_EXECUTABLE=martin"
) else (
    REM 检查可执行文件是否存在
    if not exist "%MARTIN_EXECUTABLE%" (
        echo 配置的Martin可执行文件不存在，使用默认路径
        set "MARTIN_EXECUTABLE=martin"
    )
)

REM 检查配置文件是否存在
if not exist "martin_config.yaml" (
    echo 错误: 配置文件不存在 martin_config.yaml
    exit /b 1
)

REM 使用wmic启动后台进程，不显示窗口
wmic process call create 'cmd.exe /c "%MARTIN_EXECUTABLE%" --config "%SCRIPT_DIR%martin_config.yaml" > "%SCRIPT_DIR%martin_log.txt" 2>&1' > nul

echo Martin服务已在后台启动
echo 可执行文件: %MARTIN_EXECUTABLE%
echo 配置文件: %SCRIPT_DIR%martin_config.yaml
echo 日志文件: %SCRIPT_DIR%martin_log.txt
echo 服务地址: http://localhost:3000 