/**
 * 瓦片缓存服务主入口文件
 * 统一导出所有瓦片缓存相关功能
 */

// IndexedDB 操作相关
export {
  TileCacheDB,
  TileCacheService,
  getGlobalCacheService,
  isIndexedDBSupported
} from './indexedDBOperations.js';

// 瓦片计算相关
export {
  latLonToTile,
  tileToLatLon,
  getTileBounds,
  calculateTileRange,
  calculateTileList,
  calculateTileCount,
  olExtentToBounds,
  leafletBoundsToBounds,
  buildTileUrl,
  extractTileCoordinates,
  calculateDistance,
  expandBounds,
  calculateOpenLayersZoomLevel,
  getRecommendedZoomLevels,
  formatFileSize,
  formatTimeAgo
} from './tileCalculations.js';

// 自定义瓦片加载函数相关
export {
  createOpenLayersTileLoadFunction,
  createLeafletCachedTileLayer,
  createWMSTileLoadFunction,
  preloadAreaTiles
} from './tileLoadFunctions.js';

// 简化缓存服务
export { SimpleCacheService } from './cacheService.js';

// 默认导出全局缓存服务
export { getGlobalCacheService as default } from './indexedDBOperations.js'; 