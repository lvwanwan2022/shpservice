# Deck.gl 地图组件安装说明

## 当前状态

✅ **Deck.gl地图页面已创建完成**
- 路由配置：`/map-deckgl`
- 主页导航已添加
- 组件结构完整
- 临时使用Leaflet作为底层地图

⚠️ **需要安装Deck.gl依赖**

## 安装Deck.gl依赖

由于当前环境的Node.js版本较新，可能与某些依赖存在兼容性问题。建议按以下步骤安装：

### 方法1：使用npm安装（推荐）

```bash
# 进入前端目录
cd frontend

# 安装Deck.gl核心包（无React依赖）
npm install @deck.gl/core @deck.gl/layers @deck.gl/geo-layers --legacy-peer-deps

# 或者指定版本
npm install @deck.gl/core@^8.9.0 @deck.gl/layers@^8.9.0 @deck.gl/geo-layers@^8.9.0 --legacy-peer-deps
```

### 方法2：使用yarn安装

```bash
# 使用yarn安装
yarn add @deck.gl/core @deck.gl/layers @deck.gl/geo-layers --ignore-engines
```

### 方法3：修改package.json后安装

直接在package.json中添加依赖：

```json
{
  "dependencies": {
    "@deck.gl/core": "^8.9.0",
    "@deck.gl/layers": "^8.9.0",
    "@deck.gl/geo-layers": "^8.9.0"
  }
}
```

然后运行：
```bash
npm install --legacy-peer-deps
```

## 安装成功后的配置

安装成功后，需要修改 `MapViewerDeckGL.vue` 组件：

1. 将 `initLeafletMap()` 替换为真正的 `initDeckGL()` 实现
2. 启用Deck.gl相关功能
3. 更新底图切换器使用Deck.gl API

## 组件功能特性

### ✅ 已实现功能
- 地图容器和控制界面
- 底图切换器（6种底图选择）
- 鼠标坐标显示
- 刷新按钮
- 缓存控制
- 用户定位功能
- 移动端响应式设计

### 🔄 使用Leaflet临时替代
- 基础地图显示
- 底图切换
- 鼠标坐标更新
- 地图交互控制

### 🎯 Deck.gl依赖安装后将支持
- 3D地图可视化
- GPU加速渲染
- 大数据量图层显示
- 高性能动画效果
- 专业的GIS数据可视化

## 页面访问

启动开发服务器后，可以通过以下方式访问：

1. **主页导航**：点击"地图浏览(Deck.gl)"卡片
2. **直接访问**：`http://localhost:8080/#/map-deckgl`

## 故障排除

### 如果遇到React相关错误
```bash
# 安装React（仅作为peer dependency）
npm install react react-dom --save-dev
```

### 如果遇到WebGL相关错误
确保浏览器支持WebGL 2.0：
- Chrome 56+
- Firefox 51+
- Safari 15+

### Node.js版本兼容性
如果遇到版本兼容性问题，可以考虑：
1. 使用nvm切换到Node.js 18或20
2. 使用 `--legacy-peer-deps` 参数
3. 使用yarn替代npm

## 下一步

1. 安装Deck.gl依赖
2. 测试地图功能
3. 根据需要添加更多3D可视化特性
4. 集成现有的图层管理功能 