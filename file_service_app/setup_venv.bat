@echo off
echo 正在设置 file_service_app 虚拟环境...

:: 删除现有的venv文件夹（如果存在）
if exist venv (
    echo 删除现有虚拟环境...
    rmdir /s /q venv
)

:: 创建新的虚拟环境
echo 创建新的虚拟环境...
python -m venv venv

:: 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

:: 升级pip
echo 升级pip...
python -m pip install --upgrade pip

:: 安装项目依赖
echo 安装项目依赖...
pip install -r requirements.txt

echo.
echo ========================================
echo 虚拟环境设置完成！
echo ========================================
echo.
echo 使用方法：
echo 1. 激活虚拟环境: venv\Scripts\activate.bat
echo 2. 运行项目: python main.py
echo 3. 退出虚拟环境: deactivate
echo 4. 打包项目: 请先激活虚拟环境，然后运行打包命令
echo.
pause 