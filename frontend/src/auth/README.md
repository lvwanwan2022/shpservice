# 登录认证模块使用说明

这是一个独立的登录认证模块，方便移植到其他Vue.js项目。

## 功能特性

- ✅ 简洁美观的登录页面
- ✅ JWT token认证
- ✅ 一行代码实现路由权限验证
- ✅ 一行代码实现API调用带认证
- ✅ 自动token过期处理
- ✅ 本地存储用户信息
- ✅ 最少文件数量，方便移植

## 文件结构

```
src/auth/
├── authService.js      # 认证服务核心
├── authGuard.js        # 路由守卫
├── LoginPage.vue       # 登录页面组件
└── README.md          # 使用说明
```

## 快速开始

### 1. 路由权限验证（一行代码）

已在 `router/index.js` 中配置：

```javascript
import { authGuard } from '@/auth/authGuard'
router.beforeEach(authGuard)  // 一行代码实现全局路由验证
```

### 2. API调用带认证（一行代码）

```javascript
// 方法1：使用authHttp（推荐）
import { authHttp } from '@/auth/authService'
const response = await authHttp.get('/api/protected-data')

// 方法2：使用authService实例
import authService from '@/auth/authService'
const response = await authService.apiClient.get('/api/protected-data')
```

### 3. 检查登录状态

```javascript
import authService from '@/auth/authService'

// 检查是否已登录
if (authService.isAuthenticated()) {
  console.log('用户已登录')
}

// 获取用户信息
const user = authService.getUser()
console.log('当前用户:', user)
```

### 4. 手动登录/登出

```javascript
import authService from '@/auth/authService'

// 登录
const result = await authService.login('username', 'password')
if (result.success) {
  console.log('登录成功')
}

// 登出
await authService.logout()
```

## 测试账号

- 管理员: `admin` / `admin123`
- 普通用户: `user` / `user123`

## 移植到其他项目

1. 复制 `src/auth/` 整个文件夹到目标项目
2. 在路由文件中添加登录路由和守卫
3. 安装依赖：`npm install axios`
4. 根据需要修改API baseURL

## 后端配置

确保后端已安装 `PyJWT` 依赖：

```bash
pip install PyJWT>=2.8.0
```

## 自定义配置

### 修改token存储key

```javascript
// 在authService.js中修改
this.tokenKey = 'your_custom_token_key'
this.userKey = 'your_custom_user_key'
```

### 修改公开路由

```javascript
// 在authGuard.js中修改
const publicRoutes = ['/login', '/register', '/about']
```

### 修改API baseURL

```javascript
// 在authService.js中修改
this.baseURL = 'https://your-api-domain.com/api'
```

## 安全注意事项

1. 生产环境请修改JWT密钥
2. 建议启用HTTPS
3. 可以根据需要调整token过期时间
4. 生产环境建议使用真实的用户数据库

## 故障排除

### 登录后仍然跳转到登录页

检查token是否正确存储：

```javascript
console.log('Token:', authService.getToken())
```

### API调用返回401错误

确保：
1. token有效且未过期
2. 后端正确验证Authorization header
3. API路径正确

### 路由守卫不生效

确保在router配置中正确导入和使用了authGuard。 