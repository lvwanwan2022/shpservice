# 🔒 服务连接安全配置指南

本指南说明如何为ShpService系统的服务连接功能配置全面的安全加密措施。

## 📋 安全功能概览

我们实现了多层安全防护：

1. **网络传输加密** - HTTPS/TLS
2. **数据库存储加密** - 敏感字段AES加密
3. **API通信加密** - RSA + AES混合加密
4. **前端数据保护** - 客户端加密

## 🔧 配置步骤

### 1. 后端加密配置

#### 自动密钥生成
系统首次启动时会自动生成加密密钥：

```bash
# 启动后端服务
cd backend
python app.py
```

生成的文件：
- `.encryption_key` - AES主密钥
- `.rsa_private_key.pem` - RSA私钥
- `.rsa_public_key.pem` - RSA公钥

#### 手动配置加密
如需手动配置，创建环境变量文件：

```bash
# backend/.env
ENCRYPTION_MASTER_KEY=your-master-key
USE_HTTPS=True
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### 2. HTTPS配置

#### 开发环境（自签名证书）
```bash
cd backend
python -c "from utils.https_config import setup_https_for_development; setup_https_for_development()"
```

#### 生产环境（证书配置）
```bash
# 使用环境变量配置
export USE_HTTPS=true
export SSL_CERT_PATH=/path/to/your/certificate.crt
export SSL_KEY_PATH=/path/to/your/private.key

# 启动HTTPS服务
python app.py
```

#### Nginx反向代理配置
使用生成的Nginx配置：

```bash
# 复制生成的配置
sudo cp backend/ssl/nginx_https.conf /etc/nginx/sites-available/shpservice
sudo ln -s /etc/nginx/sites-available/shpservice /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 3. 前端配置

前端会自动初始化加密服务，无需额外配置。

#### 手动初始化（可选）
```javascript
import frontendEncryption from '@/utils/encryption'

// 在应用启动时初始化
await frontendEncryption.initialize()
```

## 🔐 加密机制详解

### 数据库存储加密

敏感字段使用AES-256加密存储：

```python
# 加密敏感配置
encrypted_config = service_connection_encryption.encrypt_connection_config({
    'password': 'user_password',
    'api_key': 'user_api_key',
    'file_service_password': 'file_password'
})
```

加密字段：
- `password` - 服务密码
- `api_key` - API密钥
- `file_service_password` - 文件服务密码
- `username` - 用户名（可选）
- `file_service_username` - 文件服务用户名（可选）

### API通信加密

前端使用RSA公钥加密敏感数据：

```javascript
// 前端加密敏感字段
const encryptedData = await frontendEncryption.encryptFormData({
    service_name: 'My Service',
    password: 'secret_password',  // 将被加密
    api_key: 'secret_key'        // 将被加密
})
```

后端使用RSA私钥解密：

```python
# 后端解密
decrypted_password = encryption_service.rsa_decrypt(encrypted_password)
```

### 网络传输加密

使用TLS 1.2/1.3进行HTTPS传输：

```python
# Flask SSL配置
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ssl_context.load_cert_chain('server.crt', 'server.key')
app.run(ssl_context=ssl_context)
```

## 🛡️ 安全最佳实践

### 1. 密钥管理

**开发环境：**
- 使用自动生成的密钥
- 定期轮换密钥（建议每3个月）

**生产环境：**
- 使用环境变量管理密钥
- 使用专业的密钥管理服务（如AWS KMS、Azure Key Vault）
- 启用密钥备份和恢复机制

### 2. 证书管理

**开发环境：**
```bash
# 生成自签名证书（365天有效期）
python -c "from utils.https_config import HTTPSConfig; HTTPSConfig().generate_self_signed_cert(days_valid=365)"
```

**生产环境：**
- 使用受信任CA签发的证书
- 配置证书自动续期
- 启用HSTS（HTTP Strict Transport Security）

### 3. 数据库安全

```sql
-- 确保数据库连接使用SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';
```

### 4. 应用安全配置

```python
# config.py 安全配置
SECURITY_CONFIG = {
    'USE_HTTPS': True,
    'SECURE_COOKIES': True,
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Strict',
    'FORCE_HTTPS': True
}
```

## ⚡ 性能优化

### 1. 加密性能优化

```python
# 批量加密优化
async def encrypt_multiple_fields(data_list):
    tasks = []
    for data in data_list:
        tasks.append(frontendEncryption.encryptFormData(data))
    return await Promise.all(tasks)
```

### 2. SSL/TLS优化

```nginx
# Nginx SSL优化
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
```

## 🔍 安全监控

### 1. 加密操作日志

```python
# 启用加密操作日志
logging.getLogger('encryption').setLevel(logging.INFO)
```

### 2. 安全事件监控

监控以下事件：
- 加密/解密失败
- 证书过期警告
- 异常登录尝试
- 密钥访问记录

### 3. 健康检查

```bash
# 检查加密服务状态
curl -k https://localhost:5030/api/service-connections/encryption/public-key
```

## 🚨 故障排除

### 常见问题

1. **证书错误**
```bash
# 检查证书有效性
openssl x509 -in server.crt -text -noout
```

2. **加密失败**
```python
# 检查加密服务状态
from utils.encryption import encryption_service
print(encryption_service.encrypt_text("test"))
```

3. **HTTPS连接问题**
```bash
# 测试SSL连接
openssl s_client -connect localhost:5030 -servername localhost
```

### 日志分析

```bash
# 查看加密相关日志
grep "🔒\|❌\|✅" app.log | tail -50
```

## 📚 参考资料

- [OWASP Web Application Security](https://owasp.org/www-project-web-security-testing-guide/)
- [TLS最佳实践](https://wiki.mozilla.org/Security/Server_Side_TLS)
- [Python Cryptography文档](https://cryptography.io/)
- [Let's Encrypt证书申请](https://letsencrypt.org/)

## 🆘 安全支持

如遇到安全相关问题，请：

1. 查看本指南的故障排除部分
2. 检查应用日志文件
3. 验证配置文件设置
4. 联系系统管理员

**重要提示：** 在生产环境中，请务必：
- 使用受信任的SSL证书
- 定期更新加密密钥
- 启用访问日志监控
- 配置防火墙规则
- 进行定期安全审计