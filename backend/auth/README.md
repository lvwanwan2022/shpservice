# 后端登录认证模块使用说明

这是一个独立的Flask登录认证模块，方便移植到其他Flask项目。

## 功能特性

- ✅ JWT token认证
- ✅ 一行代码实现接口权限验证 `@require_auth`
- ✅ 密码哈希存储
- ✅ 灵活的用户存储（可替换为数据库）
- ✅ 最少文件数量，方便移植

## 文件结构

```
backend/auth/
├── __init__.py         # Python包标识
├── auth_service.py     # 认证服务核心
├── auth_routes.py      # 登录相关API路由
└── README.md          # 使用说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install PyJWT>=2.8.0
```

### 2. 注册蓝图

在 `app.py` 中添加：

```python
from auth.auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')
```

### 3. 一行代码实现接口权限验证

```python
from auth.auth_service import require_auth, get_current_user

@app.route('/api/protected')
@require_auth  # 一行代码实现登录验证
def protected_route():
    user = get_current_user()
    return jsonify({'message': f'你好 {user["name"]}'})
```

## API接口

### 登录接口

```
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

响应：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "username": "admin",
      "name": "管理员",
      "role": "admin",
      "email": "admin@example.com"
    }
  }
}
```

### 验证token接口

```
POST /api/auth/verify
Authorization: Bearer <token>
```

### 获取用户信息接口

```
GET /api/auth/userinfo
Authorization: Bearer <token>
```

### 登出接口

```
POST /api/auth/logout
Authorization: Bearer <token>
```

## 测试账号

- 管理员: `admin` / `admin123`
- 普通用户: `user` / `user123`

## 使用方法

### 在其他路由中使用认证

```python
from auth.auth_service import require_auth, get_current_user

@app.route('/api/my-data')
@require_auth  # 添加登录验证
def get_my_data():
    user = get_current_user()
    # 根据用户信息返回数据
    return jsonify({
        'user': user['username'],
        'data': '用户专属数据'
    })
```

### 角色权限控制

```python
from auth.auth_service import require_auth, get_current_user

@app.route('/api/admin-only')
@require_auth
def admin_only():
    user = get_current_user()
    if user['role'] != 'admin':
        return jsonify({'message': '权限不足'}), 403
    return jsonify({'message': '管理员专用接口'})
```

## 移植到其他项目

1. 复制 `backend/auth/` 整个文件夹到目标项目
2. 安装依赖：`pip install PyJWT>=2.8.0`
3. 在Flask应用中注册蓝图
4. 根据需要修改用户存储方式

## 自定义配置

### 使用数据库存储用户

替换 `auth_service.py` 中的用户存储：

```python
class AuthService:
    def __init__(self, secret_key='your-secret-key'):
        self.secret_key = secret_key
        # 使用数据库替换内存存储
        
    def authenticate(self, username, password):
        # 从数据库查询用户
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return True, user.to_dict(), "登录成功"
        return False, None, "用户名或密码错误"
```

### 修改JWT密钥

```python
# 在app.py中配置
auth_service = AuthService(secret_key='your-production-secret-key')
```

### 修改token过期时间

```python
auth_service = AuthService(token_expiry_hours=168)  # 7天
```

## 安全注意事项

1. **生产环境必须修改JWT密钥**
2. 使用强密码策略
3. 建议启用HTTPS
4. 定期更新依赖包
5. 考虑添加登录失败次数限制

## 扩展功能

### 添加刷新token

```python
@auth_bp.route('/refresh', methods=['POST'])
@require_auth
def refresh_token():
    user = get_current_user()
    new_token = auth_service.generate_token(user)
    return jsonify({
        'code': 200,
        'data': {'token': new_token}
    })
```

### 添加用户注册

```python
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 检查用户是否存在
    if username in auth_service.users:
        return jsonify({'code': 400, 'message': '用户已存在'}), 400
    
    # 创建新用户
    auth_service.users[username] = {
        'password': auth_service._hash_password(password),
        'name': username,
        'role': 'user'
    }
    
    return jsonify({'code': 200, 'message': '注册成功'})
```

## 故障排除

### token验证失败

1. 检查JWT密钥是否一致
2. 确认token格式正确（Bearer <token>）
3. 检查token是否过期

### 导入错误

确保 `auth` 目录在Python路径中，或使用相对导入。 