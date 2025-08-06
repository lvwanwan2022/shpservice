# 文件服务 API 文档

## 概述
这个文件服务提供了RESTful API接口，支持外部系统进行文件上传、下载、列表查看等操作。

## 认证方式

支持三种认证方式：

### 1. Basic Authentication（推荐用于API调用）
```
Authorization: Basic <base64(username:password)>
```

### 2. API Key（可选配置）
```
X-API-Key: your-api-key
```

### 3. Session Authentication（仅限Web界面）
通过Web界面登录后获得的session。

## API 端点

### 获取服务状态
```
GET /api/status
```

**响应示例：**
```json
{
    "status": "online",
    "storage": {
        "used_mb": 125.45,
        "max_mb": 1024.0,
        "used_percentage": 12.3,
        "available_mb": 898.55
    },
    "file_count": 15
}
```

### 获取文件列表（详细信息）
```
GET /api/files
```

**响应示例：**
```json
{
    "files": [
        {
            "name": "example.txt",
            "size_bytes": 1024,
            "size_mb": 0.001,
            "modified": 1699123456.789,
            "download_url": "/files/example.txt"
        }
    ],
    "total_count": 1,
    "total_size_mb": 0.001
}
```

### 获取简单文件列表
```
GET /list
```

**响应示例：**
```json
{
    "files": ["example.txt", "document.pdf"]
}
```

### 上传文件
```
POST /api/upload
Content-Type: multipart/form-data

file: <文件数据>
```

**成功响应：**
```json
{
    "message": "File uploaded successfully",
    "filename": "example.txt",
    "size_mb": 0.001,
    "download_url": "/files/example.txt"
}
```

**错误响应示例：**
```json
{
    "error": "Upload would exceed maximum capacity",
    "file_size_mb": 500.0,
    "available_mb": 100.0
}
```

### 下载文件
```
GET /files/<filename>
```

直接返回文件内容，可以通过浏览器或下载工具访问。

### 删除文件
```
DELETE /api/files/<filename>
```

**成功响应：**
```json
{
    "message": "File example.txt deleted successfully"
}
```

## 错误代码

- `400` - 请求格式错误
- `401` - 认证失败
- `404` - 文件未找到
- `409` - 文件已存在
- `507` - 存储空间不足

## 使用示例

### Python 示例
```python
import requests

# 配置认证
auth = ('admin', 'your-password')
base_url = 'http://localhost:5055'

# 获取状态
response = requests.get(f'{base_url}/api/status', auth=auth)
print(response.json())

# 上传文件
with open('example.txt', 'rb') as f:
    files = {'file': f}
    response = requests.post(f'{base_url}/api/upload', files=files, auth=auth)
    print(response.json())

# 获取文件列表
response = requests.get(f'{base_url}/api/files', auth=auth)
print(response.json())

# 下载文件
response = requests.get(f'{base_url}/files/example.txt', auth=auth)
with open('downloaded_example.txt', 'wb') as f:
    f.write(response.content)

# 删除文件
response = requests.delete(f'{base_url}/api/files/example.txt', auth=auth)
print(response.json())
```

### curl 示例
```bash
# 获取状态
curl -u admin:password http://localhost:5055/api/status

# 上传文件
curl -u admin:password -X POST -F "file=@example.txt" http://localhost:5055/api/upload

# 获取文件列表
curl -u admin:password http://localhost:5055/api/files

# 下载文件
curl -u admin:password -O http://localhost:5055/files/example.txt

# 删除文件
curl -u admin:password -X DELETE http://localhost:5055/api/files/example.txt
```

### JavaScript 示例
```javascript
// 配置基本认证
const auth = btoa('admin:password');
const headers = {
    'Authorization': `Basic ${auth}`,
    'Content-Type': 'application/json'
};

// 获取状态
fetch('http://localhost:5055/api/status', { headers })
    .then(response => response.json())
    .then(data => console.log(data));

// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:5055/api/upload', {
    method: 'POST',
    headers: { 'Authorization': `Basic ${auth}` },
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## CORS 支持

服务已启用CORS支持，允许跨域访问。可以从任何域名的网页调用这些API。

## 注意事项

1. 文件名会经过安全处理（secure_filename）
2. 上传前会检查存储空间是否足够
3. 重复文件名会返回409错误
4. 所有文件大小以MB为单位显示，保留2位小数
5. 时间戳为Unix时间戳格式