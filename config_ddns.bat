@echo off
chcp 65001 >nul
echo ===========================================
echo      阿里云 IPv6 DDNS 配置向导
echo ===========================================
echo.
echo 🌐 域名: totodudu.com
echo 📍 当前IPv6地址: 2409:8a63:119:5e10:5f7b:cef2:8575:56e5
echo.

echo ===== 步骤1: 获取阿里云AccessKey =====
echo.
echo 请按照以下步骤获取阿里云AccessKey：
echo.
echo 1. 登录阿里云控制台: https://ram.console.aliyun.com/users
echo 2. 访问 "访问控制" > "用户"
echo 3. 创建新用户或选择现有用户
echo 4. 为用户添加权限: AliyunDNSFullAccess
echo 5. 创建AccessKey，记录AccessKey ID和Secret
echo.
echo 💡 建议创建专门用于DDNS的子用户，仅授予DNS权限
echo.

echo ===== 步骤2: 配置DNS解析 =====
echo.
echo 请在阿里云DNS控制台进行以下操作：
echo.
echo 1. 访问: https://dns.console.aliyun.com
echo 2. 找到域名 totodudu.com
echo 3. 点击 "解析设置"
echo 4. 添加以下记录：
echo.
echo    记录类型: AAAA
echo    主机记录: ipv6
echo    解析线路: 默认
echo    记录值: 2409:8a63:119:5e10:5f7b:cef2:8575:56e5
echo    TTL: 600 (10分钟)
echo.
echo 💡 也可以通过脚本自动创建，但手动创建一次更安全
echo.

echo ===== 步骤3: 配置DDNS脚本 =====
echo.
echo 是否现在配置DDNS脚本？(Y/N)
set /p setup_script=请选择: 

if /i "%setup_script%"=="Y" (
    echo.
    echo 请输入您的阿里云AccessKey信息：
    echo.
    set /p access_key_id=AccessKey ID: 
    set /p access_key_secret=AccessKey Secret: 
    
    echo.
    echo 正在配置DDNS脚本...
    
    REM 创建配置文件
    echo {> ddns_config.json
    echo   "access_key_id": "%access_key_id%",>> ddns_config.json
    echo   "access_key_secret": "%access_key_secret%",>> ddns_config.json
    echo   "domain": "totodudu.com",>> ddns_config.json
    echo   "subdomain": "ipv6",>> ddns_config.json
    echo   "update_interval": 300>> ddns_config.json
    echo }>> ddns_config.json
    
    echo ✅ 配置文件已创建: ddns_config.json
)

echo.
echo ===== 步骤4: 创建定时任务 =====
echo.
echo 是否创建Windows定时任务？(Y/N)
set /p create_task=请选择: 

if /i "%create_task%"=="Y" (
    echo.
    echo 正在创建定时任务...
    
    REM 创建定时任务执行脚本
    echo @echo off> run_ddns.bat
    echo cd /d "%~dp0">> run_ddns.bat
    echo python aliyun_ddns_ipv6.py>> run_ddns.bat
    echo if %%errorlevel%% neq 0 echo DDNS更新失败 ^>^> ddns_error.log>> run_ddns.bat
    
    REM 创建定时任务 (每5分钟执行一次)
    schtasks /create /tn "IPv6 DDNS Update" /tr "%cd%\run_ddns.bat" /sc minute /mo 5 /f >nul 2>&1
    
    if %errorlevel% equ 0 (
        echo ✅ 定时任务创建成功 (每5分钟更新一次)
        echo 📋 任务名称: IPv6 DDNS Update
    ) else (
        echo ❌ 定时任务创建失败，请手动创建或以管理员身份运行
    )
)

echo.
echo ===== 步骤5: 测试配置 =====
echo.
echo 是否现在测试DDNS更新？(Y/N)
set /p test_ddns=请选择: 

if /i "%test_ddns%"=="Y" (
    echo.
    echo 正在测试DDNS更新...
    python aliyun_ddns_ipv6.py
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ DDNS测试成功！
        echo.
        echo 🎉 配置完成！您的服务现在可以通过以下域名访问：
        echo.
        echo    🌐 前端: http://ipv6.totodudu.com:8080
        echo    🔧 后端API: http://ipv6.totodudu.com:5030  
        echo    🗺️  地图服务: http://ipv6.totodudu.com:3000
        echo.
        echo 💡 建议：
        echo    1. 配置HTTPS证书 (Let's Encrypt免费)
        echo    2. 使用标准端口 (80/443) 避免防火墙问题
        echo    3. 定期备份配置文件
        
    ) else (
        echo ❌ DDNS测试失败，请检查配置
    )
)

echo.
echo ===== 额外配置建议 =====
echo.
echo 🔒 安全配置：
echo    1. 在阿里云安全组中限制访问IP
echo    2. 配置应用层认证
echo    3. 使用HTTPS加密传输
echo.
echo 🔄 备份配置：
echo    1. 备份ddns_config.json文件
echo    2. 记录域名解析配置
echo    3. 导出定时任务配置
echo.
echo 📊 监控配置：
echo    1. 设置DNS解析监控
echo    2. 配置邮件/短信通知
echo    3. 定期检查日志文件
echo.

echo ===== 完成 =====
echo.
echo 🎊 恭喜！IPv6 DDNS配置向导完成
echo 📝 相关文件：
echo    - aliyun_ddns_ipv6.py (主程序)
echo    - ddns_config.json (配置文件)
echo    - run_ddns.bat (执行脚本)
echo    - ddns_ipv6.log (日志文件)
echo.
echo 如需帮助，请查看日志文件或联系技术支持
echo.
pause 