# 瓦片缓存系统

基于IndexedDB的前端瓦片缓存解决方案，支持OpenLayers和Leaflet，提供智能缓存策略和数据API集成。

## 🎯 核心特性

- **IndexedDB存储**：基于浏览器原生数据库，支持大容量存储
- **多维度索引**：支持layerId、zoomLevel、tileX、tileY等多维度查询
- **智能缓存策略**：登录预加载、场景切换缓存、缩放自适应
- **API数据集成**：自动调用后端接口获取scenes、layers、bounds数据
- **双地图库支持**：OpenLayers和Leaflet完全兼容
- **自动过期管理**：智能清理过期缓存，控制存储空间
- **进度监控**：实时显示缓存加载进度
- **调试工具**：完整的缓存统计和调试功能

## 📁 文件结构

```
frontend/src/services/tileCache/
├── TileCacheDB.js              # IndexedDB数据库管理类
├── TileCacheService.js         # 瓦片缓存服务类  
├── OpenLayersCacheAdapter.js   # OpenLayers适配器
├── LeafletCacheAdapter.js      # Leaflet适配器
├── utils.js                    # 工具函数集合
├── index.js                    # 主入口文件
├── examples.js                 # 使用示例
└── README.md                   # 文档说明

frontend/src/views/
└── MapViewOLCache.vue          # 带缓存功能的地图页面
```

## 🚀 快速开始

### 1. 基础使用

```javascript
import { createTileCache, DataCacheService } from '@/services/tileCache';
import gisApi from '@/api/gis.js';

// 创建缓存服务
const tileCacheService = createTileCache({
  maxCacheSize: 500 * 1024 * 1024, // 500MB
  maxCacheAge: 7 * 24 * 60 * 60 * 1000 // 7天
});

// 创建数据缓存服务
const dataCacheService = new DataCacheService(tileCacheService, gisApi);

// 设置进度回调
dataCacheService.setProgressCallback((progress) => {
  console.log(`缓存进度: ${progress.percent}% - ${progress.message}`);
});
```

### 2. 登录缓存策略

```javascript
// 用户登录成功后执行
async function onLoginSuccess() {
  try {
    // 执行登录缓存策略：预加载所有scenes及其图层数据
    await dataCacheService.executeLoginStrategy();
    console.log('登录缓存完成');
  } catch (error) {
    console.error('登录缓存失败:', error);
  }
}
```

### 3. 场景切换缓存

```javascript
// 场景切换时执行
async function onSceneChange(sceneId) {
  try {
    // 执行场景切换缓存策略：预加载当前场景的图层数据
    await dataCacheService.executeSceneSwitchStrategy(sceneId);
    console.log(`场景 ${sceneId} 缓存完成`);
  } catch (error) {
    console.error('场景切换缓存失败:', error);
  }
}
```

## 📊 数据结构

### 瓦片记录格式

```javascript
{
  id: "layerId_zoomLevel_tileX_tileY",           // 唯一标识
  layerId: "layer_001",                          // 图层ID
  zoomLevel: 10,                                 // 缩放级别
  tileX: 100,                                    // 瓦片X坐标
  tileY: 200,                                    // 瓦片Y坐标
  data: Blob,                                    // 瓦片数据(Blob格式)
  timestamp: 1634567890123,                      // 存储时间戳
  size: 15360,                                   // 数据大小(字节)
  contentType: "image/png",                      // 内容类型
  url: "https://server.com/tiles/10/100/200",   // 原始URL
  metadata: {}                                   // 扩展元数据
}
```

### API数据格式

```javascript
// getScenes() 返回格式
{
  data: [
    { id: 1, name: "城市规划场景", description: "..." },
    { id: 2, name: "环境监测场景", description: "..." }
  ]
}

// getScene(sceneId) 返回格式
{
  data: {
    id: 1,
    name: "城市规划场景",
    layers: [
      { layer_id: 101, layer_name: "建筑物", file_type: "SHP" },
      { layer_id: 102, layer_name: "道路", file_type: "DXF" }
    ]
  }
}

// getSceneLayerBounds(layerId) 返回格式
{
  data: {
    bbox: [116.3, 39.9, 116.5, 40.1] // [minX, minY, maxX, maxY]
  }
}
```

## 🎨 MapViewOL-cache 页面

新增的 `MapViewOL-cache` 页面提供完整的缓存功能演示：

### 主要功能

1. **自动缓存加载**：页面加载时自动初始化缓存服务
2. **手动缓存触发**：点击"缓存加载"按钮手动触发数据缓存
3. **进度显示**：实时显示缓存加载进度
4. **场景缓存**：场景切换时自动执行缓存策略
5. **图层管理**：完整的图层可见性、样式设置等功能

### 访问方式

1. **路由地址**：`/map-ol-cache`
2. **导航菜单**：点击"地图浏览(缓存版)"
3. **登录要求**：需要先登录才能访问

### 核心代码

```vue
<template>
  <!-- 缓存进度对话框 -->
  <el-dialog title="缓存数据加载中..." v-model="cacheProgressVisible">
    <el-progress :percentage="cacheProgress.percent"></el-progress>
    <p>{{ cacheProgress.message }}</p>
  </el-dialog>
  
  <!-- 缓存管理按钮 -->
  <el-button type="success" @click="startCacheLoading">
    <i class="el-icon-download"></i> 缓存加载
  </el-button>
</template>

<script>
import { DataCacheService } from '@/services/tileCache/utils.js';

export default {
  setup() {
    const startCacheLoading = async () => {
      await dataCacheService.executeLoginStrategy();
    };
    
    const onSceneChange = async (sceneId) => {
      await dataCacheService.executeSceneSwitchStrategy(sceneId);
    };
    
    return { startCacheLoading, onSceneChange };
  }
};
</script>
```

## 🔧 缓存策略详解

### 1. 登录策略 (Login Strategy)

- **触发时机**：用户登录成功后
- **缓存内容**：所有scenes及其图层的bounds数据
- **缩放级别**：8-12级（中等精度）
- **优先级**：3（高优先级）
- **适用场景**：初始化加载，提供基础缓存覆盖

### 2. 场景切换策略 (Scene Switch Strategy)

- **触发时机**：用户切换场景时
- **缓存内容**：当前场景下所有图层数据
- **缩放级别**：10-14级（高精度）
- **优先级**：2（中等优先级）
- **适用场景**：场景预览，快速响应

### 3. 缩放策略 (Zoom Strategy)

- **触发时机**：用户缩放地图时
- **缓存内容**：当前视野范围内的瓦片
- **缩放级别**：当前级别±2级
- **优先级**：1（最高优先级）
- **适用场景**：实时浏览，即时响应

## 📈 性能优化

### 缓存配置建议

```javascript
// 推荐配置
const cacheConfig = {
  maxCacheSize: 500 * 1024 * 1024,     // 500MB存储空间
  maxCacheAge: 7 * 24 * 60 * 60 * 1000, // 7天过期时间
  cleanupInterval: 60 * 60 * 1000,      // 1小时清理间隔
  batchSize: 50,                        // 批量处理50个瓦片
  concurrency: 5                        // 同时下载5个瓦片
};
```

### 性能监控

```javascript
// 获取缓存统计
const stats = await tileCacheService.getStats();
console.log('缓存命中率:', stats.hitRate);
console.log('缓存大小:', stats.totalSize);
console.log('瓦片数量:', stats.tileCount);

// 获取详细报告
const report = await tileCacheService.generateDetailedReport();
console.log('详细缓存报告:', report);
```

## 🐛 调试工具

### 1. 缓存调试器

```javascript
import { CacheDebugger } from '@/services/tileCache/utils.js';

const debugger = new CacheDebugger(tileCacheService);

// 检查特定瓦片
await debugger.checkTile('layer_001', 10, 100, 200);

// 列出所有缓存图层
const layers = await debugger.listLayers();

// 打印统计信息
await debugger.printStats();
```

### 2. 浏览器控制台调试

```javascript
// 在浏览器控制台中执行
window.tileCache = tileCacheService;
window.dataCache = dataCacheService;

// 查看缓存状态
await window.tileCache.getStats();

// 手动执行缓存策略
await window.dataCache.executeLoginStrategy();
```

## 🔗 API集成

### 必需的后端接口

确保后端提供以下API接口：

```javascript
// 1. 获取场景列表
GET /api/scenes
// 返回: { data: [{ id, name, description }] }

// 2. 获取场景详情
GET /api/scenes/:sceneId  
// 返回: { data: { id, name, layers: [...] } }

// 3. 获取图层边界
GET /api/layers/:layerId/bounds
// 返回: { data: { bbox: [minX, minY, maxX, maxY] } }
```

### API错误处理

```javascript
// 数据缓存服务会自动处理API错误
dataCacheService.setProgressCallback((progress) => {
  if (progress.error) {
    console.error('API调用失败:', progress.error);
    // 可以在这里添加错误上报逻辑
  }
});
```

## 🌐 浏览器兼容性

- **Chrome 23+**：完全支持
- **Firefox 16+**：完全支持  
- **Safari 10+**：完全支持
- **Edge 12+**：完全支持
- **IE**：不支持（需要IndexedDB）

## 📝 使用示例

完整的使用示例请参考 `examples.js` 文件，包含8个详细示例：

1. **基础设置**：初始化缓存系统
2. **瓦片计算**：bounds到瓦片坐标转换
3. **OpenLayers集成**：地图库适配器使用
4. **Leaflet集成**：Leaflet地图集成
5. **缓存策略**：智能缓存策略管理
6. **缓存管理**：缓存清理和统计
7. **调试工具**：调试和诊断工具
8. **数据缓存服务**：完整的API集成演示

## 🚨 故障排除

### 常见问题

1. **IndexedDB不支持**
   ```javascript
   if (!window.indexedDB) {
     console.error('浏览器不支持IndexedDB');
   }
   ```

2. **缓存配额超限**
   ```javascript
   try {
     await tileCacheService.saveTile(tileData);
   } catch (error) {
     if (error.name === 'QuotaExceededError') {
       await tileCacheService.cleanup();
     }
   }
   ```

3. **API调用失败**
   ```javascript
   // DataCacheService会自动重试和降级处理
   dataCacheService.setProgressCallback((progress) => {
     if (progress.error) {
       // 处理API错误
     }
   });
   ```

## 📞 技术支持

如需技术支持或反馈问题，请通过以下方式联系：

- 在页面中点击"反馈"按钮提交问题
- 查看浏览器控制台错误信息
- 使用调试工具进行问题诊断

---

> 💡 提示：建议在生产环境中根据实际情况调整缓存配置，特别是缓存大小和过期时间。 