@echo off
echo 开始打包 file_service_app...

:: 检查虚拟环境是否存在
if not exist venv (
    echo 错误：虚拟环境不存在！
    echo 请先运行 setup_venv.bat 创建虚拟环境
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查是否安装了pyinstaller
echo 检查 PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 安装 PyInstaller...
    pip install pyinstaller
)

:: 清理之前的构建文件
echo 清理构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del main.spec

:: 开始打包
echo 开始打包应用程序...
pyinstaller --onefile --windowed --clean main.py

:: 检查打包结果
if exist dist\main.exe (
    echo.
    echo ========================================
    echo 打包成功！
    echo ========================================
    echo 可执行文件位置: dist\main.exe
    echo.
) else (
    echo.
    echo ========================================
    echo 打包失败！
    echo ========================================
    echo 请检查错误信息
    echo.
)

:: 退出虚拟环境
deactivate

pause 