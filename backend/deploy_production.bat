@echo off
REM ========================================
REM   SHP Service 生产环境部署脚本
REM   Windows Server 高性能部署方案
REM ========================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   SHP Service 生产环境部署向导
echo ========================================
echo.

REM 设置颜色
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "RED=%ESC%[91m"
set "BLUE=%ESC%[94m"
set "RESET=%ESC%[0m"

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%❌ 需要管理员权限才能部署生产环境%RESET%
    echo    请右键选择"以管理员身份运行"
    pause
    exit /b 1
)

echo %GREEN%✅ 管理员权限检查通过%RESET%

REM 1. 环境检查
echo.
echo %BLUE%=== 1. 环境检查 ===%RESET%

REM 检查Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%❌ Python 未安装或未添加到PATH%RESET%
    echo    请先安装 Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo %GREEN%✅ Python 版本: %PYTHON_VERSION%%RESET%

REM 检查pip
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%❌ pip 未安装%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ pip 可用%RESET%

REM 2. 创建目录结构
echo.
echo %BLUE%=== 2. 创建目录结构 ===%RESET%

set DIRS=logs temp FilesData feedback_uploads sld_styles
for %%d in (%DIRS%) do (
    if not exist "%%d" (
        mkdir "%%d"
        echo %GREEN%✅ 创建目录: %%d%RESET%
    ) else (
        echo %YELLOW%⚠️  目录已存在: %%d%RESET%
    )
)

REM 3. 安装依赖
echo.
echo %BLUE%=== 3. 安装生产环境依赖 ===%RESET%

echo %YELLOW%正在安装基础依赖...%RESET%
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo %RED%❌ 基础依赖安装失败%RESET%
    pause
    exit /b 1
)

echo %YELLOW%正在安装生产环境依赖...%RESET%
pip install waitress psutil pywin32
if %errorLevel% neq 0 (
    echo %RED%❌ 生产环境依赖安装失败%RESET%
    pause
    exit /b 1
)

echo %GREEN%✅ 依赖安装完成%RESET%

REM 4. 选择部署模式
echo.
echo %BLUE%=== 4. 选择部署模式 ===%RESET%
echo.
echo 请选择部署模式:
echo   1. 单实例模式 (简单, 适合小负载)
echo   2. 多实例负载均衡模式 (高性能, 推荐)
echo   3. Windows系统服务模式 (自动启动)
echo   4. 完整生产环境 (多实例 + 负载均衡 + 服务)
echo.

set /p DEPLOY_MODE="请输入选择 [1-4]: "

if "%DEPLOY_MODE%"=="1" goto SINGLE_INSTANCE
if "%DEPLOY_MODE%"=="2" goto MULTI_INSTANCE
if "%DEPLOY_MODE%"=="3" goto WINDOWS_SERVICE
if "%DEPLOY_MODE%"=="4" goto FULL_PRODUCTION
echo %RED%❌ 无效选择%RESET%
pause
exit /b 1

:SINGLE_INSTANCE
echo.
echo %BLUE%=== 单实例模式部署 ===%RESET%
echo %YELLOW%启动高性能 Waitress 服务器...%RESET%
python waitress_production.py
goto END

:MULTI_INSTANCE
echo.
echo %BLUE%=== 多实例负载均衡模式 ===%RESET%
echo %YELLOW%启动多实例集群...%RESET%
echo.
echo %YELLOW%注意: 需要配置 Nginx 或其他反向代理来实现负载均衡%RESET%
echo %YELLOW%配置文件: nginx_loadbalancer.conf%RESET%
echo.
pause
python multi_instance_launcher.py
goto END

:WINDOWS_SERVICE
echo.
echo %BLUE%=== Windows系统服务模式 ===%RESET%
echo %YELLOW%安装并启动 Windows 服务...%RESET%

REM 安装服务
python windows_service.py install
if %errorLevel% neq 0 (
    echo %RED%❌ 服务安装失败%RESET%
    pause
    exit /b 1
)

REM 启动服务
python windows_service.py start
if %errorLevel% neq 0 (
    echo %RED%❌ 服务启动失败%RESET%
    pause
    exit /b 1
)

echo %GREEN%✅ Windows 服务部署完成%RESET%
echo.
echo %YELLOW%服务管理命令:%RESET%
echo   启动服务: python windows_service.py start
echo   停止服务: python windows_service.py stop
echo   重启服务: python windows_service.py restart
echo   查看状态: python windows_service.py status
echo   卸载服务: python windows_service.py uninstall
goto END

:FULL_PRODUCTION
echo.
echo %BLUE%=== 完整生产环境部署 ===%RESET%
echo.
echo %YELLOW%这将部署完整的生产环境，包括:%RESET%
echo   - 多个 Waitress 实例
echo   - Windows 系统服务
echo   - 负载均衡配置
echo   - 性能监控
echo.

set /p CONFIRM="确认部署完整生产环境? [y/N]: "
if /i not "%CONFIRM%"=="y" goto END

REM 创建生产环境配置
echo %YELLOW%创建生产环境配置文件...%RESET%

REM 创建启动脚本
echo @echo off > start_production_cluster.bat
echo echo 启动生产环境集群... >> start_production_cluster.bat
echo python multi_instance_launcher.py >> start_production_cluster.bat
echo pause >> start_production_cluster.bat

REM 创建停止脚本
echo @echo off > stop_production_cluster.bat
echo echo 停止生产环境集群... >> stop_production_cluster.bat
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq*instance*" >> stop_production_cluster.bat
echo echo 集群已停止 >> stop_production_cluster.bat
echo pause >> stop_production_cluster.bat

REM 安装并启动 Windows 服务
echo %YELLOW%安装 Windows 服务...%RESET%
python windows_service.py install

echo %YELLOW%启动 Windows 服务...%RESET%
python windows_service.py start

echo %GREEN%✅ 完整生产环境部署完成%RESET%
echo.
echo %YELLOW%部署信息:%RESET%
echo   - 主服务端口: 5030-5033
echo   - Windows 服务: SHPService
echo   - 负载均衡配置: nginx_loadbalancer.conf
echo   - 日志目录: logs/
echo   - 启动集群: start_production_cluster.bat
echo   - 停止集群: stop_production_cluster.bat
echo.
echo %YELLOW%推荐配置 Nginx 反向代理以获得最佳性能%RESET%
goto END

:END
echo.
echo %BLUE%=== 5. 部署完成 ===%RESET%
echo.
echo %GREEN%🎉 SHP Service 生产环境部署完成!%RESET%
echo.
echo %YELLOW%访问信息:%RESET%
echo   本地访问: http://localhost:5030
echo   网络访问: http://10.20.148.169:5030
echo   API文档: http://10.20.148.169:5030/swagger/
echo.
echo %YELLOW%管理命令:%RESET%
echo   查看服务状态: python windows_service.py status
echo   性能监控: python performance_monitor.py
echo   查看日志: type logs\waitress_production.log
echo.
echo %YELLOW%配置文件:%RESET%
echo   Nginx负载均衡: nginx_loadbalancer.conf
echo   多实例启动器: multi_instance_launcher.py
echo   Windows服务: windows_service.py
echo.

REM 6. 可选的性能测试
echo %BLUE%=== 6. 性能测试 (可选) ===%RESET%
set /p PERF_TEST="是否进行性能测试? [y/N]: "
if /i "%PERF_TEST%"=="y" (
    echo %YELLOW%启动性能测试...%RESET%
    if exist performance_test.py (
        python performance_test.py
    ) else (
        echo %YELLOW%性能测试脚本不存在，跳过测试%RESET%
    )
)

echo.
echo %GREEN%部署脚本执行完成，感谢使用 SHP Service!%RESET%
pause
