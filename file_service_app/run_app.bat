@echo off
echo 启动 file_service_app...

:: 检查虚拟环境是否存在
if not exist venv (
    echo 错误：虚拟环境不存在！
    echo 请先运行 setup_venv.bat 创建虚拟环境
    pause
    exit /b 1
)

:: 激活虚拟环境并运行应用
echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 启动应用程序...
python main.py

:: 退出虚拟环境
deactivate 