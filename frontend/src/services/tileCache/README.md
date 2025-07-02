# 瓦片缓存服务

这个模块提供了完整的地图瓦片缓存解决方案，支持 OpenLayers 和 Leaflet，使用 IndexedDB 进行本地存储。

## 文件结构

```
tileCache/
├── index.js                    # 主入口文件
├── indexedDBOperations.js      # IndexedDB 操作模块
├── tileCalculations.js         # 瓦片计算工具模块
├── tileLoadFunctions.js        # 自定义瓦片加载函数模块
└── README.md                   # 说明文档
```

## 核心模块

### 1. IndexedDB 操作模块 (`indexedDBOperations.js`)

负责所有与 IndexedDB 相关的操作，包括：

- `TileCacheDB` - 数据库管理类
- `TileCacheService` - 瓦片缓存服务类
- `getGlobalCacheService()` - 获取全局缓存服务实例
- `isIndexedDBSupported()` - 检查浏览器支持

### 2. 瓦片计算模块 (`tileCalculations.js`)

包含所有瓦片相关的计算函数：

- 坐标转换：`latLonToTile()`, `tileToLatLon()`
- 边界计算：`getTileBounds()`, `calculateTileRange()`
- 瓦片列表：`calculateTileList()`, `calculateTileCount()`
- URL 处理：`buildTileUrl()`, `extractTileCoordinates()`
- 工具函数：`formatFileSize()`, `formatTimeAgo()`

### 3. 瓦片加载函数模块 (`tileLoadFunctions.js`)

提供自定义的瓦片加载函数：

- `createOpenLayersTileLoadFunction()` - OpenLayers 瓦片加载函数
- `createLeafletCachedTileLayer()` - Leaflet 缓存瓦片图层
- `createWMSTileLoadFunction()` - WMS 瓦片加载函数
- `preloadAreaTiles()` - 预加载区域瓦片

## 使用示例

### OpenLayers 集成

```javascript
import { createOpenLayersTileLoadFunction, getGlobalCacheService } from './services/tileCache';
import TileLayer from 'ol/layer/Tile';
import XYZ from 'ol/source/XYZ';

// 创建带缓存的瓦片图层
const layerId = 'my-layer';
const baseUrl = 'https://tile-server.com/{z}/{x}/{y}.png';

const tileLayer = new TileLayer({
  source: new XYZ({
    url: baseUrl,
    tileLoadFunction: createOpenLayersTileLoadFunction(layerId, baseUrl, {
      enableCache: true,
      cacheFirst: true,
      debug: false
    })
  })
});
```

### Leaflet 集成

```javascript
import { createLeafletCachedTileLayer } from './services/tileCache';

// 创建带缓存的 Leaflet 瓦片图层
const cachedLayer = createLeafletCachedTileLayer(
  'my-layer',
  'https://tile-server.com/{z}/{x}/{y}.png',
  {
    enableCache: true,
    cacheFirst: true,
    attribution: '© OpenStreetMap'
  }
);

// 添加到地图
map.addLayer(cachedLayer);
```

### WMS 图层缓存

```javascript
import { createWMSTileLoadFunction } from './services/tileCache';
import TileLayer from 'ol/layer/Tile';
import TileWMS from 'ol/source/TileWMS';

const wmsLayer = new TileLayer({
  source: new TileWMS({
    url: 'https://geoserver.com/wms',
    params: {
      'LAYERS': 'workspace:layer',
      'TILED': true,
      'VERSION': '1.1.1',
      'FORMAT': 'image/png',
      'TRANSPARENT': true
    },
    tileLoadFunction: createWMSTileLoadFunction('wms-layer', 'https://geoserver.com/wms', {
      enableCache: true,
      cacheFirst: true
    })
  })
});
```

### 缓存管理

```javascript
import { getGlobalCacheService } from './services/tileCache';

const cacheService = getGlobalCacheService();

// 获取缓存统计
const stats = await cacheService.getCacheStats();
console.log('缓存统计:', stats);

// 清理过期缓存（7天前的）
const deletedCount = await cacheService.cleanExpiredTiles(7 * 24 * 60 * 60 * 1000);
console.log('清理了', deletedCount, '个过期瓦片');

// 删除指定图层的所有缓存
const layerDeletedCount = await cacheService.deleteLayerTiles('my-layer');
console.log('删除了', layerDeletedCount, '个图层瓦片');

// 清空所有缓存
await cacheService.clearAllTiles();
```

### 预加载区域瓦片

```javascript
import { preloadAreaTiles } from './services/tileCache';

// 预加载指定区域的瓦片
const bounds = {
  north: 40.0,
  south: 39.0,
  east: 117.0,
  west: 116.0
};

await preloadAreaTiles(
  'my-layer',
  'https://tile-server.com/{z}/{x}/{y}.png',
  bounds,
  10, // minZoom
  15, // maxZoom
  (completed, total) => {
    console.log(`预加载进度: ${completed}/${total}`);
  }
);
```

### 瓦片计算工具

```javascript
import { 
  latLonToTile, 
  tileToLatLon, 
  calculateTileRange,
  getTileBounds 
} from './services/tileCache';

// 经纬度转瓦片坐标
const tileCoord = latLonToTile(39.9042, 116.4074, 10);
console.log('瓦片坐标:', tileCoord); // {x: 843, y: 389}

// 瓦片坐标转经纬度
const latLon = tileToLatLon(843, 389, 10);
console.log('经纬度:', latLon); // {lat: 39.9042, lon: 116.4074}

// 计算区域的瓦片范围
const tileRange = calculateTileRange(bounds, 10);
console.log('瓦片范围:', tileRange); // {minX: 842, minY: 388, maxX: 844, maxY: 390}

// 获取瓦片的地理边界
const tileBounds = getTileBounds(10, 843, 389);
console.log('瓦片边界:', tileBounds); // [[lon, lat], [lon, lat], ...]
```

## 配置选项

### 通用选项

- `enableCache`: 是否启用缓存（默认：true）
- `cacheFirst`: 是否优先使用缓存（默认：true）
- `debug`: 是否启用调试日志（默认：false）

### OpenLayers 特有选项

- `maxRetries`: 最大重试次数（默认：3）
- `retryDelay`: 重试延迟（默认：250ms）
- `retryCodes`: 需要重试的HTTP状态码

### Leaflet 特有选项

- 支持所有标准的 Leaflet TileLayer 选项
- `crossOrigin`: 跨域设置

## 浏览器兼容性

- 支持所有现代浏览器（Chrome、Firefox、Safari、Edge）
- 需要 IndexedDB 支持
- 需要 ES6+ 支持

## 性能建议

1. **合理设置缓存策略**：根据应用场景选择 `cacheFirst` 模式
2. **定期清理缓存**：使用 `cleanExpiredTiles()` 清理过期数据
3. **控制预加载范围**：避免一次性预加载过多瓦片
4. **监控缓存大小**：定期检查 `getCacheStats()` 避免存储空间过大

## 故障排除

### 常见问题

1. **瓦片不显示**
   - 检查网络连接
   - 确认 URL 模板正确
   - 查看浏览器控制台错误

2. **缓存不工作**
   - 确认浏览器支持 IndexedDB
   - 检查 `enableCache` 设置
   - 查看存储权限

3. **性能问题**
   - 检查缓存大小
   - 清理过期数据
   - 调整重试策略

### 调试模式

启用 `debug: true` 可以查看详细的缓存操作日志：

```javascript
const tileLoadFunction = createOpenLayersTileLoadFunction(layerId, baseUrl, {
  debug: true
});
``` 