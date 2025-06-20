# 用户信息组件使用说明

## 功能概述

`UserInfo.vue` 组件是一个顶部菜单栏用户信息显示组件，集成了登录状态检测和用户操作功能。

## 主要功能

### 🔒 未登录状态
- 显示"登录"按钮
- 点击按钮跳转到登录页面

### ✅ 已登录状态
- 显示用户头像图标和用户名
- 下拉菜单包含：
  - 用户详细信息（用户名、姓名、角色、邮箱）
  - 个人资料（开发中）
  - 设置（开发中）
  - 退出登录

## 实时状态更新

组件使用监听器模式，当用户登录或退出时，界面会自动更新，无需手动刷新页面。

## 集成方式

已在 `App.vue` 中集成：

```vue
<template>
  <nav class="main-header">
    <div class="logo">...</div>
    <div class="nav-center">...</div>
    <!-- 用户信息组件 -->
    <div class="user-section">
      <UserInfo />
    </div>
  </nav>
</template>
```

## 样式特点

- 与顶部导航栏风格保持一致
- 登录按钮使用透明背景，鼠标悬停有高亮效果
- 用户下拉菜单有hover动画效果
- 响应式设计，适配不同屏幕尺寸

## 操作流程

1. **未登录用户**：点击"登录"按钮 → 跳转登录页面
2. **已登录用户**：点击用户名 → 展开下拉菜单 → 选择操作
3. **退出登录**：点击"退出登录" → 清除本地存储 → 跳转首页

## 技术特性

- ✅ 使用Element Plus组件
- ✅ Vue 3 Composition API兼容
- ✅ 实时状态监听
- ✅ 自动内存清理（beforeUnmount）
- ✅ 错误处理和用户反馈

## 自定义配置

### 修改默认跳转页面

```javascript
// 在goToLogin方法中修改
goToLogin() {
  this.$router.push('/custom-login')
}
```

### 添加更多菜单项

```vue
<el-dropdown-item command="new-feature">
  <el-icon><Star /></el-icon> 新功能
</el-dropdown-item>
```

### 自定义用户角色显示

```javascript
getRoleName(role) {
  const roleMap = {
    'admin': '管理员',
    'user': '普通用户',
    'vip': 'VIP用户'  // 添加新角色
  }
  return roleMap[role] || role
}
```

## 注意事项

1. 组件依赖于 `authService` 服务
2. 需要Element Plus图标库支持
3. 建议在App.vue级别使用，确保全局可见 