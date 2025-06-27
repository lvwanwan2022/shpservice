/**
 * 瓦片缓存模块主入口
 * 
 * 这个模块提供了完整的瓦片缓存解决方案，包括：
 * - IndexedDB 数据库管理
 * - 瓦片缓存服务
 * - OpenLayers 适配器
 * - Leaflet 适配器
 * - 实用工具函数
 */

// 核心类
export { default as TileCacheDB } from './TileCacheDB.js';
export { default as TileCacheService } from './TileCacheService.js';

// 地图库适配器
export { default as OpenLayersCacheAdapter } from './OpenLayersCacheAdapter.js';
export { default as LeafletCacheAdapter } from './LeafletCacheAdapter.js';

// 工具函数
export * from './utils.js';
export { default as utils } from './utils.js';

// 使用示例
export { default as examples } from './examples.js';

// 便捷导入
import TileCacheService from './TileCacheService.js';
import OpenLayersCacheAdapter from './OpenLayersCacheAdapter.js';
import LeafletCacheAdapter from './LeafletCacheAdapter.js';
import { getGlobalCacheService, isIndexedDBSupported } from './utils.js';

/**
 * 创建瓦片缓存实例的工厂函数
 * @param {object} options 配置选项
 * @returns {TileCacheService} 缓存服务实例
 */
export function createTileCache(options = {}) {
  const cacheService = new TileCacheService();
  
  if (options.maxCacheSize) {
    cacheService.setMaxCacheSize(options.maxCacheSize);
  }
  
  if (options.maxCacheAge) {
    cacheService.setMaxCacheAge(options.maxCacheAge);
  }
  
  return cacheService;
}

/**
 * 创建 OpenLayers 缓存适配器
 * @param {object} options 配置选项
 * @returns {OpenLayersCacheAdapter} OpenLayers 适配器实例
 */
export function createOpenLayersAdapter(options = {}) {
  return new OpenLayersCacheAdapter(options);
}

/**
 * 创建 Leaflet 缓存适配器
 * @param {object} options 配置选项
 * @returns {LeafletCacheAdapter} Leaflet 适配器实例
 */
export function createLeafletAdapter(options = {}) {
  return new LeafletCacheAdapter(options);
}

/**
 * 快速设置：检查环境并初始化缓存
 * @param {object} options 配置选项
 * @returns {object} 设置结果
 */
export function quickSetup(options = {}) {
  const result = {
    supported: false,
    cacheService: null,
    adapters: {},
    error: null
  };

  try {
    // 检查 IndexedDB 支持
    if (!isIndexedDBSupported()) {
      result.error = '浏览器不支持 IndexedDB';
      return result;
    }

    result.supported = true;

    // 创建缓存服务
    result.cacheService = options.useGlobal ? 
      getGlobalCacheService() : 
      createTileCache(options);

    // 创建适配器
    if (options.enableOpenLayers !== false) {
      try {
        result.adapters.openLayers = createOpenLayersAdapter(options);
      } catch (error) {
        console.warn('OpenLayers 适配器创建失败:', error.message);
      }
    }

    if (options.enableLeaflet !== false) {
      try {
        result.adapters.leaflet = createLeafletAdapter(options);
      } catch (error) {
        console.warn('Leaflet 适配器创建失败:', error.message);
      }
    }

    console.log('瓦片缓存系统初始化成功');
  } catch (error) {
    result.error = error.message;
    console.error('瓦片缓存系统初始化失败:', error);
  }

  return result;
}

// 默认导出主要组件
export default {
  TileCacheService,
  OpenLayersCacheAdapter,
  LeafletCacheAdapter,
  createTileCache,
  createOpenLayersAdapter,
  createLeafletAdapter,
  quickSetup,
  utils: { getGlobalCacheService, isIndexedDBSupported }
}; 