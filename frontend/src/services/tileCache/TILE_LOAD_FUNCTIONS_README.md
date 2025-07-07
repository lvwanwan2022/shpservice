# 瓦片加载函数使用说明

## 概述

`tileLoadFunctions.js` 提供了两个主要的瓦片加载函数，支持缓存和离线模式：

- `createWmtsTileLoadFunction`: 创建WMTS/栅格瓦片加载函数
- `createMvtTileLoadFunction`: 创建MVT/矢量瓦片加载函数

## 主要特性

1. **智能缓存**: 自动缓存瓦片到IndexedDB
2. **离线支持**: 网络不可用时使用缓存数据
3. **附近瓦片替代**: 找不到精确缓存时使用附近瓦片
4. **错误恢复**: 完善的错误处理和重试机制
5. **性能优化**: 减少网络请求，提升加载速度
6. **缓存控制**: 可选择是否启用缓存存储，支持只读缓存模式

## 使用方法

### 1. WMTS瓦片加载函数

```javascript
import { createWmtsTileLoadFunction } from '@/services/tileCache/tileLoadFunctions.js';
import { XYZ } from 'ol/source';
import { Tile as TileLayer } from 'ol/layer';

// 创建瓦片加载函数
const wmtsTileLoadFunction = createWmtsTileLoadFunction({
  layerId: 'gaode_base',  // 图层ID，用于缓存标识
  tileCacheService: tileCacheService,  // 可选，缓存服务实例
  retryCodes: [404, 503, 500],  // 可选，需要重试的HTTP状态码
  retries: {},  // 可选，重试计数器
  enableCacheStorage: true  // 可选，是否启用缓存存储，默认为true
});

// 创建地图源并应用加载函数
const source = new XYZ({
  url: 'https://example.com/tiles/{z}/{x}/{y}.png',
  crossOrigin: 'anonymous'
});

source.setTileLoadFunction(wmtsTileLoadFunction);

// 创建图层
const layer = new TileLayer({ source });
```

### 2. MVT瓦片加载函数

```javascript
import { createMvtTileLoadFunction } from '@/services/tileCache/tileLoadFunctions.js';
import { VectorTile as VectorTileSource } from 'ol/source';
import { VectorTile as VectorTileLayer } from 'ol/layer';
import { MVT } from 'ol/format';

// 创建MVT瓦片加载函数
const mvtTileLoadFunction = createMvtTileLoadFunction({
  layerId: 'vector_layer',  // 图层ID
  tileCacheService: tileCacheService,  // 可选，缓存服务实例
  enableCacheStorage: true  // 可选，是否启用缓存存储，默认为true
});

// 创建MVT源并应用加载函数
const mvtSource = new VectorTileSource({
  url: 'http://example.com/mvt/{z}/{x}/{y}',
  format: new MVT(),
  tileLoadFunction: mvtTileLoadFunction
});

// 创建图层
const mvtLayer = new VectorTileLayer({ source: mvtSource });
```

### 3. 使用默认函数

```javascript
import { 
  getDefaultWmtsTileLoadFunction,
  getDefaultMvtTileLoadFunction 
} from '@/services/tileCache/tileLoadFunctions.js';

// 使用默认配置
const wmtsLoader = getDefaultWmtsTileLoadFunction('my_layer');
const mvtLoader = getDefaultMvtTileLoadFunction('my_mvt_layer');

// 禁用缓存存储（只从缓存读取，不存储新数据）
const wmtsLoaderNoCache = getDefaultWmtsTileLoadFunction('my_layer', false);
const mvtLoaderNoCache = getDefaultMvtTileLoadFunction('my_mvt_layer', false);

// 或者使用完整配置方式
const customWmtsLoader = createWmtsTileLoadFunction({
  layerId: 'my_layer',
  enableCacheStorage: false
});
const customMvtLoader = createMvtTileLoadFunction({
  layerId: 'my_mvt_layer',
  enableCacheStorage: false
});
```

## 配置选项

### WMTS瓦片加载函数选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| layerId | string | 'default_layer' | 图层标识符，用于缓存分组 |
| tileCacheService | Object | getGlobalCacheService() | 缓存服务实例 |
| retryCodes | Array | [404, 503, 500] | 需要重试的HTTP状态码 |
| retries | Object | {} | 重试计数器对象 |
| enableCacheStorage | boolean | true | 是否启用缓存存储到IndexedDB |

### MVT瓦片加载函数选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| layerId | string | 'mvt_layer' | 图层标识符 |
| tileCacheService | Object | getGlobalCacheService() | 缓存服务实例 |
| enableCacheStorage | boolean | true | 是否启用缓存存储到IndexedDB |

## 工作流程

### 1. 瓦片加载流程

```
请求瓦片
    ↓
检查缓存
    ↓
缓存命中? → 是 → 使用缓存数据
    ↓ 否
网络加载
    ↓
加载成功? → 是 → 保存到缓存 → 显示瓦片
    ↓ 否
查找附近缓存
    ↓
找到替代? → 是 → 使用替代瓦片
    ↓ 否
显示错误状态
```

### 2. 离线模式支持

当网络不可用时：
1. 优先使用精确匹配的缓存瓦片
2. 如果没有精确匹配，搜索附近的缓存瓦片作为替代
3. 搜索范围包括同一缩放级别的相邻8个瓦片
4. 提供详细的日志信息便于调试

## 缓存控制

### 缓存存储选项

通过 `enableCacheStorage` 参数可以控制是否将新获取的瓦片存储到缓存中：

- **true（默认）**: 启用缓存存储，新获取的瓦片会自动保存到IndexedDB
- **false**: 禁用缓存存储，只从现有缓存读取数据，不存储新数据

### 使用场景

1. **完整缓存模式** (`enableCacheStorage: true`)：
   - 适用于大多数场景
   - 自动缓存所有访问的瓦片
   - 提供最佳的离线体验

2. **只读缓存模式** (`enableCacheStorage: false`)：
   - 适用于临时浏览或演示
   - 不会增加存储空间占用
   - 仍然可以使用已有的缓存数据
   - 适合在存储空间有限的设备上使用

## 缓存策略

### 缓存数据结构

```javascript
{
  id: "layerId_z_x_y",           // 唯一标识
  layerId: "layer_name",         // 图层ID
  zoomLevel: 12,                 // 缩放级别
  tileX: 123,                    // X坐标
  tileY: 456,                    // Y坐标
  data: Blob/ArrayBuffer,        // 瓦片数据
  size: 12345,                   // 数据大小
  contentType: "image/png",      // 内容类型
  timestamp: 1640995200000,      // 缓存时间戳
  url: "https://..."             // 原始URL
}
```

### 缓存管理

- 自动缓存成功加载的瓦片
- 支持按图层清理缓存
- 提供缓存统计信息
- 支持过期清理机制

## 错误处理

### 网络错误处理
- 自动重试机制（最多3次）
- 渐进式重试延迟（250ms, 500ms, 750ms）
- 详细的错误日志记录

### 缓存错误处理
- 缓存读取失败时降级到网络加载
- 缓存数据损坏时自动重新获取
- 提供友好的错误提示

## 最佳实践

1. **图层ID命名**: 使用有意义的图层ID，便于缓存管理
2. **缓存策略**: 根据数据更新频率设置合适的缓存时间
3. **错误监控**: 监听加载错误，及时发现问题
4. **性能优化**: 定期清理过期缓存，保持性能
5. **离线支持**: 为重要图层预加载缓存数据
6. **缓存控制**: 
   - 对于经常访问的底图启用缓存存储
   - 对于临时或测试图层可以禁用缓存存储
   - 根据设备存储空间情况灵活调整缓存策略

## 注意事项

1. IndexedDB有存储限制，注意控制缓存大小
2. CORS策略可能影响瓦片加载，确保服务端配置正确
3. 移动设备上注意内存使用，避免缓存过多数据
4. 定期更新缓存数据，确保数据时效性

## 故障排除

### 常见问题

1. **瓦片不显示**: 检查URL格式和CORS设置
2. **缓存不生效**: 确认IndexedDB支持和权限
3. **性能问题**: 检查缓存大小和清理策略
4. **离线模式失效**: 确认缓存数据完整性

### 调试技巧

1. 打开浏览器开发者工具查看网络请求
2. 检查IndexedDB中的缓存数据结构
3. 使用Performance面板分析性能瓶颈 