# 前端服务连接页面JSON解析错误修复

## 问题描述

在前端-服务连接页面进行连接测试时，出现以下错误：
- 前端测试弹出错误：`前端测试失败: "[object Object]" is not valid JSON`
- 后端测试显示连接正常

## 问题原因

问题出现在 `frontend/src/views/ServiceConnectionView.vue` 文件的 `apiRequest` 函数中：

1. **无条件JSON解析**：函数无论响应内容类型如何，都会调用 `response.json()`
2. **缺少响应类型检查**：没有检查服务器返回的Content-Type头
3. **配置解析不安全**：直接使用 `JSON.parse()` 解析连接配置，没有考虑数据类型

## 修复内容

### 1. 改进 apiRequest 函数

**修复前：**
```javascript
const response = await fetch(url, { ...defaultOptions, ...options })
const data = await response.json()  // 无条件调用

if (!response.ok) {
  throw new Error(data.error || '请求失败')
}
```

**修复后：**
```javascript
const response = await fetch(url, { ...defaultOptions, ...options })

// 检查响应内容类型
const contentType = response.headers.get('content-type')
let data = null

if (contentType && contentType.includes('application/json')) {
  try {
    data = await response.json()
  } catch (jsonError) {
    console.error('JSON解析失败:', jsonError)
    throw new Error(`JSON解析失败: ${jsonError.message}`)
  }
} else {
  // 如果不是JSON响应，获取文本内容
  const textData = await response.text()
  console.warn('收到非JSON响应:', textData)
  data = { error: textData || '服务器返回了非JSON响应' }
}

if (!response.ok) {
  const errorMessage = data && data.error ? data.error : `请求失败 (${response.status})`
  throw new Error(errorMessage)
}
```

### 2. 安全的配置解析

**修复前：**
```javascript
const config = JSON.parse(connection.connection_config || '{}')
```

**修复后：**
```javascript
let config = {}
if (connection.connection_config) {
  if (typeof connection.connection_config === 'string') {
    try {
      config = JSON.parse(connection.connection_config)
    } catch (parseError) {
      console.warn('解析连接配置失败:', parseError)
      config = {}
    }
  } else if (typeof connection.connection_config === 'object') {
    config = connection.connection_config
  }
}
```

### 3. 改进错误处理

为所有错误处理添加了：
- 详细的控制台日志记录
- 更友好的错误消息
- 安全的错误信息提取

## 修复的好处

1. **更好的错误提示**：用户现在会看到具体的错误信息，而不是通用的JSON解析错误
2. **增强的稳定性**：应用不会因为非JSON响应而崩溃
3. **更好的调试**：控制台日志提供了详细的错误信息，便于开发者调试
4. **兼容性**：支持后端返回的不同数据格式（字符串或对象）

## 测试建议

1. 测试正常的连接场景
2. 测试网络错误场景
3. 测试后端返回非JSON响应的场景
4. 测试配置数据格式异常的场景

## 相关文件

- `frontend/src/views/ServiceConnectionView.vue` - 主要修复文件
- `backend/routes/service_connection_routes.py` - 后端API实现