@echo off
echo ===============================================
echo       GeoServer 服务重启脚本
echo ===============================================

echo 正在检查GeoServer服务状态...

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 管理员权限确认
) else (
    echo 错误: 请以管理员身份运行此脚本
    echo 右键点击脚本 -> "以管理员身份运行"
    pause
    exit /B 1
)

:: 方法1: 尝试停止和启动GeoServer Windows服务
echo.
echo 尝试重启GeoServer Windows服务...
sc query "GeoServer" >nul 2>&1
if %errorLevel% == 0 (
    echo 找到GeoServer服务，正在重启...
    net stop GeoServer
    timeout /t 5
    net start GeoServer
    echo GeoServer服务重启完成
    goto :success
)

:: 方法2: 尝试停止Java进程（如果GeoServer作为普通进程运行）
echo.
echo 未找到GeoServer服务，尝试停止Java进程...
tasklist /fi "imagename eq java.exe" /fi "windowtitle eq *geoserver*" 2>nul | find /i "java.exe" >nul
if %errorLevel% == 0 (
    echo 找到GeoServer Java进程，正在停止...
    taskkill /f /im java.exe /fi "windowtitle eq *geoserver*"
    echo 请手动重新启动GeoServer
    goto :manual_start
)

:: 方法3: 查找所有可能的GeoServer进程
echo.
echo 搜索所有可能的GeoServer相关进程...
tasklist | find /i "java" | find /i "geoserver"
if %errorLevel% == 0 (
    echo 请检查上述进程是否为GeoServer，手动停止后重新启动
    goto :manual_start
)

echo.
echo 未找到运行中的GeoServer进程
echo 请检查GeoServer是否正在运行

:manual_start
echo.
echo ===============================================
echo 手动启动GeoServer的常见方法:
echo.
echo 1. 如果安装为Windows服务:
echo    services.msc -> 找到GeoServer -> 右键启动
echo.
echo 2. 如果使用startup.bat:
echo    进入GeoServer安装目录/bin/
echo    运行: startup.bat
echo.
echo 3. 如果在Tomcat中:
echo    重启Tomcat服务
echo ===============================================
goto :end

:success
echo.
echo ===============================================
echo GeoServer重启成功！
echo 请等待约30秒让服务完全启动
echo 然后访问: http://localhost:8080/geoserver
echo ===============================================

:end
echo.
echo 按任意键退出...
pause >nul 