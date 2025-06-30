import TileCacheService from './TileCacheService.js';

/**
 * 瓦片缓存工具函数集合
 */

// 全局缓存服务实例（单例模式）
let globalCacheService = null;

/**
 * 获取全局缓存服务实例
 * @returns {TileCacheService} 缓存服务实例
 */
export function getGlobalCacheService() {
  if (!globalCacheService) {
    globalCacheService = new TileCacheService();
  }
  return globalCacheService;
}

/**
 * 检查浏览器是否支持IndexedDB
 * @returns {boolean} 是否支持
 */
export function isIndexedDBSupported() {
  return !!(window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB);
}

/**
 * 格式化文件大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化后的大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化时间差
 * @param {number} timestamp 时间戳
 * @returns {string} 格式化后的时间差
 */
export function formatTimeAgo(timestamp) {
  const now = Date.now();
  const diff = now - timestamp;
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  return `${seconds}秒前`;
}

/**
 * 计算两个地理坐标点之间的距离（米）
 * @param {number} lat1 纬度1
 * @param {number} lon1 经度1
 * @param {number} lat2 纬度2
 * @param {number} lon2 经度2
 * @returns {number} 距离（米）
 */
export function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000; // 地球半径（米）
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * 经纬度转瓦片坐标
 * @param {number} lat 纬度
 * @param {number} lon 经度
 * @param {number} zoom 缩放级别
 * @returns {object} 瓦片坐标 {x, y}
 */
export function latLonToTile(lat, lon, zoom) {
  const x = Math.floor((lon + 180) / 360 * Math.pow(2, zoom));
  const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom));
  return { x, y };
}

/**
 * 瓦片坐标转经纬度
 * @param {number} x 瓦片X坐标
 * @param {number} y 瓦片Y坐标
 * @param {number} zoom 缩放级别
 * @returns {object} 经纬度 {lat, lon}
 */
export function tileToLatLon(x, y, zoom) {
  const n = Math.pow(2, zoom);
  const lon = x / n * 360 - 180;
  const lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n))) * 180 / Math.PI;
  return { lat, lon };
}

/**
 * 计算包含指定区域的瓦片范围
 * @param {object} bounds 边界 {north, south, east, west} 或 {top, bottom, left, right}
 * @param {number} zoom 缩放级别
 * @returns {object} 瓦片范围 {minX, minY, maxX, maxY}
 */
export function calculateTileRange(bounds, zoom) {
  // 兼容不同的bounds格式
  const north = bounds.north || bounds.top;
  const south = bounds.south || bounds.bottom;
  const east = bounds.east || bounds.right;
  const west = bounds.west || bounds.left;
  
  const nw = latLonToTile(north, west, zoom);
  const se = latLonToTile(south, east, zoom);
  
  return {
    minX: Math.min(nw.x, se.x),
    minY: Math.min(nw.y, se.y),
    maxX: Math.max(nw.x, se.x),
    maxY: Math.max(nw.y, se.y)
  };
}

/**
 * 根据bounds和缩放级别范围计算所有需要加载的瓦片坐标列表
 * @param {object} bounds 边界 {north, south, east, west} 或 {top, bottom, left, right}
 * @param {number|object} zoomLevels 缩放级别（数字）或缩放级别范围 {min: number, max: number}
 * @returns {Array} 瓦片坐标列表 [{z, x, y}, ...]
 */
export function calculateTileList(bounds, zoomLevels) {
  const tileList = [];
  
  // 处理缩放级别参数
  let minZoom, maxZoom;
  if (typeof zoomLevels === 'number') {
    minZoom = maxZoom = zoomLevels;
  } else if (Array.isArray(zoomLevels)) {
    minZoom = Math.min(...zoomLevels);
    maxZoom = Math.max(...zoomLevels);
  } else {
    minZoom = zoomLevels.min || zoomLevels.minZoom || 0;
    maxZoom = zoomLevels.max || zoomLevels.maxZoom || 18;
  }
  
  // 遍历每个缩放级别
  for (let z = minZoom; z <= maxZoom; z++) {
    const tileRange = calculateTileRange(bounds, z);
    
    // 遍历瓦片范围
    for (let x = tileRange.minX; x <= tileRange.maxX; x++) {
      for (let y = tileRange.minY; y <= tileRange.maxY; y++) {
        tileList.push({ z, x, y });
      }
    }
  }
  
  return tileList;
}

/**
 * 计算瓦片范围内的瓦片总数
 * @param {object} bounds 边界
 * @param {number|object} zoomLevels 缩放级别或范围
 * @returns {number} 瓦片总数
 */
export function calculateTileCount(bounds, zoomLevels) {
  let totalCount = 0;
  
  // 处理缩放级别参数
  let minZoom, maxZoom;
  if (typeof zoomLevels === 'number') {
    minZoom = maxZoom = zoomLevels;
  } else if (Array.isArray(zoomLevels)) {
    minZoom = Math.min(...zoomLevels);
    maxZoom = Math.max(...zoomLevels);
  } else {
    minZoom = zoomLevels.min || zoomLevels.minZoom || 0;
    maxZoom = zoomLevels.max || zoomLevels.maxZoom || 18;
  }
  
  // 计算每个缩放级别的瓦片数
  for (let z = minZoom; z <= maxZoom; z++) {
    const tileRange = calculateTileRange(bounds, z);
    const count = (tileRange.maxX - tileRange.minX + 1) * (tileRange.maxY - tileRange.minY + 1);
    totalCount += count;
  }
  
  return totalCount;
}

/**
 * OpenLayers bounds 转换为标准 bounds 格式
 * @param {Array} olExtent OpenLayers extent [minX, minY, maxX, maxY]
 * @param {string} projection 投影坐标系，默认 'EPSG:3857'
 * @returns {object} 标准bounds {west, south, east, north}
 */
export function olExtentToBounds(olExtent, projection = 'EPSG:3857') {
  if (typeof window !== 'undefined' && window.ol && window.ol.proj) {
    const [minX, minY, maxX, maxY] = olExtent;
    
    // 如果是Web墨卡托投影，需要转换为经纬度
    if (projection === 'EPSG:3857') {
      const bottomLeft = window.ol.proj.transform([minX, minY], 'EPSG:3857', 'EPSG:4326');
      const topRight = window.ol.proj.transform([maxX, maxY], 'EPSG:3857', 'EPSG:4326');
      
      return {
        west: bottomLeft[0],
        south: bottomLeft[1],
        east: topRight[0],
        north: topRight[1]
      };
    }
  }
  
  // 假设已经是经纬度坐标
  return {
    west: olExtent[0],
    south: olExtent[1],
    east: olExtent[2],
    north: olExtent[3]
  };
}

/**
 * Leaflet bounds 转换为标准 bounds 格式
 * @param {object} leafletBounds Leaflet LatLngBounds对象
 * @returns {object} 标准bounds {west, south, east, north}
 */
export function leafletBoundsToBounds(leafletBounds) {
  if (typeof window !== 'undefined' && window.L && leafletBounds instanceof window.L.LatLngBounds) {
    const sw = leafletBounds.getSouthWest();
    const ne = leafletBounds.getNorthEast();
    
    return {
      west: sw.lng,
      south: sw.lat,
      east: ne.lng,
      north: ne.lat
    };
  }
  
  // 如果是普通对象格式
  if (leafletBounds.getSouthWest && leafletBounds.getNorthEast) {
    const sw = leafletBounds.getSouthWest();
    const ne = leafletBounds.getNorthEast();
    
    return {
      west: sw.lng,
      south: sw.lat,
      east: ne.lng,
      north: ne.lat
    };
  }
  
  return leafletBounds;
}

/**
 * 计算缓存统计信息摘要
 * @param {object} stats 原始统计信息
 * @returns {object} 摘要信息
 */
export function calculateCacheSummary(stats) {
  const summary = {
    totalTiles: stats.totalTiles,
    totalSize: stats.totalSize,
    totalSizeFormatted: formatFileSize(stats.totalSize),
    layerCount: Object.keys(stats.layerStats).length,
    averageTileSize: stats.totalTiles > 0 ? stats.totalSize / stats.totalTiles : 0,
    cacheAge: null,
    layers: []
  };

  // 计算缓存年龄
  if (stats.oldestTile) {
    summary.cacheAge = formatTimeAgo(stats.oldestTile.timestamp);
  }

  // 整理图层信息
  Object.entries(stats.layerStats).forEach(([layerId, layerStat]) => {
    summary.layers.push({
      id: layerId,
      count: layerStat.count,
      size: layerStat.size,
      sizeFormatted: formatFileSize(layerStat.size),
      zoomLevels: layerStat.zoomLevels,
      percentage: ((layerStat.size / stats.totalSize) * 100).toFixed(1)
    });
  });

  // 按大小排序图层
  summary.layers.sort((a, b) => b.size - a.size);

  return summary;
}

/**
 * 生成缓存报告（文本格式）
 * @param {object} stats 缓存统计信息
 * @returns {string} 文本格式的报告
 */
export function generateCacheReport(stats) {
  const summary = calculateCacheSummary(stats);
  
  let report = `瓦片缓存报告\n`;
  report += `==================\n`;
  report += `总瓦片数: ${summary.totalTiles}\n`;
  report += `总大小: ${summary.totalSizeFormatted}\n`;
  report += `图层数量: ${summary.layerCount}\n`;
  report += `平均瓦片大小: ${formatFileSize(summary.averageTileSize)}\n`;
  
  if (summary.cacheAge) {
    report += `最老缓存: ${summary.cacheAge}\n`;
  }
  
  report += `\n图层详情:\n`;
  report += `----------\n`;
  
  summary.layers.forEach((layer, index) => {
    report += `${index + 1}. ${layer.id}\n`;
    report += `   瓦片数: ${layer.count}\n`;
    report += `   大小: ${layer.sizeFormatted} (${layer.percentage}%)\n`;
    report += `   缩放级别: ${layer.zoomLevels.join(', ')}\n\n`;
  });
  
  return report;
}

/**
 * 预加载区域瓦片的便捷函数
 * @param {string} layerId 图层ID
 * @param {string} urlTemplate URL模板
 * @param {object} bounds 边界
 * @param {number} minZoom 最小缩放级别
 * @param {number} maxZoom 最大缩放级别
 * @param {Function} progressCallback 进度回调
 * @returns {Promise<void>}
 */
export async function preloadAreaTiles(layerId, urlTemplate, bounds, minZoom, maxZoom, progressCallback) {
  const cacheService = getGlobalCacheService();
  let totalTiles = 0;
  let loadedTiles = 0;

  // 计算总瓦片数
  for (let zoom = minZoom; zoom <= maxZoom; zoom++) {
    const tileRange = calculateTileRange(bounds, zoom);
    totalTiles += (tileRange.maxX - tileRange.minX + 1) * (tileRange.maxY - tileRange.minY + 1);
  }

  // 逐级预加载
  for (let zoom = minZoom; zoom <= maxZoom; zoom++) {
    const tileRange = calculateTileRange(bounds, zoom);
    const promises = [];

    for (let x = tileRange.minX; x <= tileRange.maxX; x++) {
      for (let y = tileRange.minY; y <= tileRange.maxY; y++) {
        // 检查是否已缓存
        const hasCached = await cacheService.hasTile(layerId, zoom, x, y);
        if (!hasCached) {
          const tileUrl = buildTileUrl(urlTemplate, zoom, x, y);
          
          const promise = loadAndCacheTile(layerId, tileUrl, zoom, x, y)
            .then(() => {
              loadedTiles++;
              if (progressCallback) {
                progressCallback(loadedTiles, totalTiles, zoom);
              }
            })
            .catch(error => {
              console.error(`预加载瓦片失败 ${zoom}/${x}/${y}:`, error);
              loadedTiles++;
              if (progressCallback) {
                progressCallback(loadedTiles, totalTiles, zoom);
              }
            });
          
          promises.push(promise);
        } else {
          loadedTiles++;
          if (progressCallback) {
            progressCallback(loadedTiles, totalTiles, zoom);
          }
        }
      }
    }

    await Promise.all(promises);
    
  }

 
}

/**
 * 加载并缓存单个瓦片
 * @param {string} layerId 图层ID
 * @param {string} url 瓦片URL
 * @param {number} z 缩放级别
 * @param {number} x X坐标
 * @param {number} y Y坐标
 * @returns {Promise<void>}
 */
export async function loadAndCacheTile(layerId, url, z, x, y) {
  const cacheService = getGlobalCacheService();
  
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = async () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob(async (blob) => {
          if (blob) {
            await cacheService.saveTile(layerId, z, x, y, blob, {
              contentType: 'image/png',
              url
            });
          }
          resolve();
        }, 'image/png');
      } catch (error) {
        reject(error);
      }
    };
    
    img.onerror = () => reject(new Error(`加载失败: ${url}`));
    img.src = url;
  });
}

/**
 * 构建瓦片URL
 * @param {string} urlTemplate URL模板
 * @param {number} z 缩放级别
 * @param {number} x X坐标
 * @param {number} y Y坐标
 * @returns {string} 瓦片URL
 */
export function buildTileUrl(urlTemplate, z, x, y) {
  return urlTemplate
    .replace('{z}', z.toString())
    .replace('{x}', x.toString())
    .replace('{y}', y.toString())
    .replace('{s}', 'a'); // 默认子域名
}

/**
 * 批量删除过期缓存
 * @param {number} maxAge 最大年龄（毫秒）
 * @returns {Promise<number>} 删除的瓦片数量
 */
export async function cleanExpiredTiles(maxAge = 7 * 24 * 60 * 60 * 1000) {
  const cacheService = getGlobalCacheService();
  cacheService.setMaxCacheAge(maxAge);
  return await cacheService.cleanExpiredCache();
}

/**
 * 获取缓存使用情况
 * @returns {Promise<object>} 使用情况信息
 */
export async function getCacheUsage() {
  const cacheService = getGlobalCacheService();
  const stats = await cacheService.getCacheStats();
  return calculateCacheSummary(stats);
}

/**
 * 导出缓存配置
 * @returns {object} 缓存配置
 */
export function exportCacheConfig() {
  const cacheService = getGlobalCacheService();
  return {
    maxCacheSize: cacheService.maxCacheSize,
    maxCacheAge: cacheService.maxCacheAge,
    dbName: cacheService.db.dbName,
    dbVersion: cacheService.db.dbVersion,
    storeName: cacheService.db.storeName
  };
}

/**
 * 应用缓存配置
 * @param {object} config 缓存配置
 */
export function applyCacheConfig(config) {
  const cacheService = getGlobalCacheService();
  if (config.maxCacheSize) {
    cacheService.setMaxCacheSize(config.maxCacheSize);
  }
  if (config.maxCacheAge) {
    cacheService.setMaxCacheAge(config.maxCacheAge);
  }
}

/**
 * 缓存策略管理器
 * 管理不同操作行为触发的缓存加载策略
 */
export class CacheStrategyManager {
  constructor(options = {}) {
    this.cacheService = getGlobalCacheService();
    this.strategies = {
      login: options.loginStrategy || this.getDefaultLoginStrategy(),
      sceneSwitch: options.sceneSwitchStrategy || this.getDefaultSceneSwitchStrategy(),
      zoom: options.zoomStrategy || this.getDefaultZoomStrategy()
    };
    this.isPreloading = false;
    this.currentTasks = new Map(); // 当前预加载任务
    this.priorityQueue = []; // 优先级队列
  }

  /**
   * 登录时的缓存预加载策略
   * @param {Array} scenes 场景数据
   * @param {object} options 选项
   */
  async executeLoginStrategy(scenes, options = {}) {

    
    const strategy = { ...this.strategies.login, ...options };
    const allTasks = [];

    for (const scene of scenes) {
      if (scene.layers && Array.isArray(scene.layers)) {
        for (const layer of scene.layers) {
          if (layer.bounds && layer.url) {
            const task = {
              type: 'login',
              priority: strategy.priority,
              layerId: layer.id || `${scene.id}_${layer.name}`,
              urlTemplate: layer.url,
              bounds: layer.bounds,
              zoomLevels: strategy.zoomLevels,
              sceneId: scene.id,
              layerName: layer.name
            };
            allTasks.push(task);
          }
        }
      }
    }

    await this.executeTasks(allTasks, strategy.progressCallback);
  }

  /**
   * 场景切换时的缓存预加载策略
   * @param {object} scene 场景数据
   * @param {object} options 选项
   */
  async executeSceneSwitchStrategy(scene, options = {}) {

    
    const strategy = { ...this.strategies.sceneSwitch, ...options };
    const tasks = [];

    if (scene.layers && Array.isArray(scene.layers)) {
      for (const layer of scene.layers) {
        if (layer.bounds && layer.url) {
          const task = {
            type: 'sceneSwitch',
            priority: strategy.priority,
            layerId: layer.id || `${scene.id}_${layer.name}`,
            urlTemplate: layer.url,
            bounds: layer.bounds,
            zoomLevels: strategy.zoomLevels,
            sceneId: scene.id,
            layerName: layer.name
          };
          tasks.push(task);
        }
      }
    }

    await this.executeTasks(tasks, strategy.progressCallback);
  }

  /**
   * 缩放时的缓存预加载策略
   * @param {Array} visibleLayers 当前可见图层
   * @param {object} currentBounds 当前视图范围
   * @param {number} currentZoom 当前缩放级别
   * @param {object} options 选项
   */
  async executeZoomStrategy(visibleLayers, currentBounds, currentZoom, options = {}) {

    
    const strategy = { ...this.strategies.zoom, ...options };
    const tasks = [];

    // 计算预加载的缩放级别范围
    const zoomRange = this.calculateZoomRange(currentZoom, strategy);

    for (const layer of visibleLayers) {
      if (layer.url) {
        // 扩展当前bounds以预加载周边区域
        const expandedBounds = this.expandBounds(currentBounds, strategy.boundsExpansion || 0.5);
        
        const task = {
          type: 'zoom',
          priority: strategy.priority,
          layerId: layer.id || layer.name,
          urlTemplate: layer.url,
          bounds: expandedBounds,
          zoomLevels: zoomRange,
          currentZoom: currentZoom
        };
        tasks.push(task);
      }
    }

    await this.executeTasks(tasks, strategy.progressCallback);
  }

  /**
   * 执行预加载任务
   * @param {Array} tasks 任务列表
   * @param {Function} progressCallback 进度回调
   */
  async executeTasks(tasks, progressCallback) {
    if (this.isPreloading) {

      this.priorityQueue.push(...tasks);
      return;
    }

    this.isPreloading = true;
    
    try {
      // 按优先级排序任务
      tasks.sort((a, b) => (b.priority || 0) - (a.priority || 0));
      
      let completedTasks = 0;
      const totalTasks = tasks.length;

      for (const task of tasks) {
        try {
          await this.executeTask(task);
          completedTasks++;
          
          if (progressCallback) {
            progressCallback({
              completed: completedTasks,
              total: totalTasks,
              task: task
            });
          }
        } catch (error) {
          console.error(`预加载任务失败:`, task, error);
        }
      }

      // 处理队列中的任务
      if (this.priorityQueue.length > 0) {
        const queuedTasks = this.priorityQueue.splice(0);
        await this.executeTasks(queuedTasks, progressCallback);
      }
    } finally {
      this.isPreloading = false;
    }
  }

  /**
   * 执行单个预加载任务
   * @param {object} task 任务对象
   */
  async executeTask(task) {
    const { layerId, urlTemplate, bounds, zoomLevels } = task;
    
    // 检查是否已有相同任务在执行
    const taskKey = `${layerId}_${JSON.stringify(bounds)}_${JSON.stringify(zoomLevels)}`;
    if (this.currentTasks.has(taskKey)) {
      return;
    }

    this.currentTasks.set(taskKey, task);
    
    try {
      await preloadAreaTiles(layerId, urlTemplate, bounds, zoomLevels.min, zoomLevels.max);
    } finally {
      this.currentTasks.delete(taskKey);
    }
  }

  /**
   * 计算缩放级别范围
   * @param {number} currentZoom 当前缩放级别
   * @param {object} strategy 策略配置
   * @returns {object} 缩放级别范围
   */
  calculateZoomRange(currentZoom, strategy) {
    const bufferZoom = strategy.zoomBuffer || 2;
    return {
      min: Math.max(0, currentZoom - bufferZoom),
      max: Math.min(18, currentZoom + bufferZoom)
    };
  }

  /**
   * 扩展边界范围
   * @param {object} bounds 原始边界
   * @param {number} expansion 扩展比例
   * @returns {object} 扩展后的边界
   */
  expandBounds(bounds, expansion = 0.5) {
    const latRange = bounds.north - bounds.south;
    const lonRange = bounds.east - bounds.west;
    
    return {
      north: bounds.north + latRange * expansion,
      south: bounds.south - latRange * expansion,
      east: bounds.east + lonRange * expansion,
      west: bounds.west - lonRange * expansion
    };
  }

  /**
   * 获取默认登录策略
   */
  getDefaultLoginStrategy() {
    return {
      priority: 3,
      zoomLevels: { min: 8, max: 12 },
      maxConcurrent: 3,
      progressCallback: null
    };
  }

  /**
   * 获取默认场景切换策略
   */
  getDefaultSceneSwitchStrategy() {
    return {
      priority: 2,
      zoomLevels: { min: 10, max: 14 },
      maxConcurrent: 5,
      progressCallback: null
    };
  }

  /**
   * 获取默认缩放策略
   */
  getDefaultZoomStrategy() {
    return {
      priority: 1,
      zoomBuffer: 2,
      boundsExpansion: 0.5,
      maxConcurrent: 2,
      progressCallback: null
    };
  }

  /**
   * 设置策略配置
   * @param {string} strategyName 策略名称
   * @param {object} config 配置
   */
  setStrategy(strategyName, config) {
    if (this.strategies[strategyName]) {
      this.strategies[strategyName] = { ...this.strategies[strategyName], ...config };
    }
  }

  /**
   * 停止所有预加载任务
   */
  stopAllTasks() {
    this.isPreloading = false;
    this.currentTasks.clear();
    this.priorityQueue = [];

  }

  /**
   * 获取当前任务状态
   */
  getTaskStatus() {
    return {
      isPreloading: this.isPreloading,
      currentTasksCount: this.currentTasks.size,
      queuedTasksCount: this.priorityQueue.length,
      currentTasks: Array.from(this.currentTasks.keys())
    };
  }
}

/**
 * 瓦片缓存调试工具
 */
export const CacheDebugger = {
  /**
   * 打印缓存统计信息到控制台
   */

  /**
   * 验证特定瓦片是否存在
   */
  async checkTile(layerId, z, x, y) {
    const cacheService = getGlobalCacheService();
    const tile = await cacheService.getTile(layerId, z, x, y);

    return !!tile;
  },

  /**
   * 列出所有缓存的图层ID
   */
  async listLayers() {
    const stats = await getCacheUsage();
    const layers = stats.layers.map(layer => layer.id);

    return layers;
  }
};

/**
 * 数据缓存服务 - 调用后端API获取scenes、layers、bounds数据
 */
export class DataCacheService {
  constructor(tileCacheService, gisApi) {
    this.tileCacheService = tileCacheService;
    this.gisApi = gisApi;
    this.loading = false;
    this.progressCallback = null;
    
    // 确保tileCacheService可用
    if (!tileCacheService) {
      console.warn('DataCacheService: tileCacheService未提供');
    }
  }

  /**
   * 设置进度回调
   */
  setProgressCallback(callback) {
    this.progressCallback = callback;
  }

  /**
   * 触发进度更新
   */
  updateProgress(current, total, message) {
    if (this.progressCallback) {
      this.progressCallback({
        current,
        total,
        percent: Math.round((current / total) * 100),
        message
      });
    }
  }

  /**
   * 获取所有scenes数据
   */
  async fetchScenes() {
    try {

      const response = await this.gisApi.getScenes();

      
      // 解析API响应数据
      let scenes = null;
      if (response.data && response.data.scenes) {
        scenes = response.data.scenes;
      } else if (response.data && Array.isArray(response.data)) {
        scenes = response.data;
      } else if (Array.isArray(response)) {
        scenes = response;
      } else {
        console.warn('未能解析scenes数据，响应格式:', response);
        return [];
      }

      return scenes;
    } catch (error) {
      console.error('获取scenes数据失败:', error);
      throw error;
    }
  }

  /**
   * 获取scene详情和其包含的layers
   */
  async fetchSceneWithLayers(sceneId) {
    try {

      const sceneResponse = await this.gisApi.getScene(sceneId);

      
      // 解析scene数据
      let scene = null;
      let layers = [];
      
      if (sceneResponse.data) {
        // 场景信息
        scene = sceneResponse.data.scene || sceneResponse.data;
        // 图层信息 - 从API响应中直接获取
        layers = sceneResponse.data.layers || scene.layers || [];
      } else {
        scene = sceneResponse;
        layers = scene.layers || [];
      }
      
      //console.log(`Scene ${sceneId} 包含 ${layers.length} 个图层:`, layers);
      
      return {
        scene,
        layers
      };
    } catch (error) {
      console.error(`获取scene ${sceneId} 数据失败:`, error);
      throw error;
    }
  }

  /**
   * 获取图层bounds信息
   */
  async fetchLayerBounds(sceneLayerId) {
    try {
      //console.log(`开始获取scene图层 ${sceneLayerId} 的bounds...`);
      const response = await this.gisApi.getSceneLayerBounds(sceneLayerId);
      //console.log(`scene图层 ${sceneLayerId} API响应:`, response);
      
      // 解析bounds数据
      let bounds = null;
      if (response.data && response.data.bounds) {
        bounds = response.data.bounds;
      } else if (response.data) {
        bounds = response.data;
      } else {
        bounds = response;
      }
      
      //console.log(`scene图层 ${sceneLayerId} bounds:`, bounds);
      return bounds;
    } catch (error) {
      console.error(`获取scene图层 ${sceneLayerId} bounds失败:`, error);
      // 返回null而不是抛出错误，让流程继续
      return null;
    }
  }

  /**
   * 登录策略：预加载所有scenes及其图层的bounds，并缓存固定缩放级别的瓦片
   */
  async executeLoginStrategy() {
    if (this.loading) {
      //console.log('已有加载任务在执行中，跳过');
      return;
    }

    this.loading = true;
    //console.log('🚀 开始执行登录缓存策略...');

    try {
      // 1. 获取所有scenes
      this.updateProgress(1, 10, '获取场景列表...');
      const scenes = await this.fetchScenes();
      
      if (!scenes || scenes.length === 0) {
        //console.log('没有找到scenes数据');
        return;
      }

      //console.log(`找到 ${scenes.length} 个场景`);
      let processedScenes = 0;
      let totalLayers = 0;
      
      // 2. 遍历每个scene
      for (const scene of scenes) {
        try {
          this.updateProgress(
            2 + (processedScenes * 3), 
            2 + (scenes.length * 3), 
            `处理场景: ${scene.name}...`
          );

          const { layers } = await this.fetchSceneWithLayers(scene.id);
          totalLayers += layers.length;

          // 3. 获取每个图层的bounds
          for (const layer of layers) {
            try {
              // 使用scene_layer_id调用bounds API
              const bounds = await this.fetchLayerBounds(layer.scene_layer_id);
              if (bounds && bounds.bbox) {
                // 4. 根据bounds预加载瓦片
                await this.preloadTilesForBounds(
                  layer.layer_id, 
                  bounds.bbox,
                  'login' // 策略类型
                );
              }
            } catch (error) {
              console.warn(`处理图层 ${layer.layer_id} 失败:`, error);
            }
          }

          processedScenes++;
        } catch (error) {
          console.warn(`处理场景 ${scene.id} 失败:`, error);
          processedScenes++;
        }
      }

      this.updateProgress(10, 10, `完成！处理了 ${scenes.length} 个场景，${totalLayers} 个图层`);
      //console.log(`✅ 登录缓存策略执行完成！处理了 ${scenes.length} 个场景，${totalLayers} 个图层`);

    } catch (error) {
      console.error('❌ 登录缓存策略执行失败:', error);
      throw error;
    } finally {
      this.loading = false;
    }
  }

  /**
   * 场景切换策略：预加载指定场景下所有图层的瓦片
   */
  async executeSceneSwitchStrategy(sceneId) {
    if (this.loading) {
      //console.log('已有加载任务在执行中，跳过');
      return;
    }

    this.loading = true;
    //console.log(`🔄 开始执行场景切换缓存策略，场景ID: ${sceneId}...`);

    try {
      this.updateProgress(1, 5, `获取场景 ${sceneId} 信息...`);
      const { scene, layers } = await this.fetchSceneWithLayers(sceneId);
      
      this.updateProgress(2, 5, `处理 ${layers.length} 个图层...`);
      
      for (let i = 0; i < layers.length; i++) {
        const layer = layers[i];
        
        this.updateProgress(
          2 + ((i + 1) / layers.length * 3), 
          5, 
          `处理图层: ${layer.layer_name}...`
        );

        try {
          // 使用scene_layer_id调用bounds API
          const bounds = await this.fetchLayerBounds(layer.scene_layer_id);
          if (bounds && bounds.bbox) {
            await this.preloadTilesForBounds(
              layer.layer_id, 
              bounds.bbox,
              'scene_switch'
            );
          }
        } catch (error) {
          console.warn(`处理图层 ${layer.layer_id} 失败:`, error);
        }
      }

      this.updateProgress(5, 5, `完成场景 ${scene.name} 的缓存！`);
      //console.log(`✅ 场景切换缓存策略执行完成！场景: ${scene.name}`);

    } catch (error) {
      console.error('❌ 场景切换缓存策略执行失败:', error);
      throw error;
    } finally {
      this.loading = false;
    }
  }

  /**
   * 根据bounds预加载瓦片
   */
  async preloadTilesForBounds(layerId, bbox, strategyType = 'login') {
    try {
      // 将API返回的bbox格式转换为标准bounds格式
      // API返回: {bbox: {minx, miny, maxx, maxy}, ...}
      // 需要转换为: {west, south, east, north}
      const bboxData = bbox.bbox || bbox; // 兼容两种格式
      const bounds = {
        west: bboxData.minx,
        south: bboxData.miny,
        east: bboxData.maxx,
        north: bboxData.maxy
      };
      
      //console.log(`图层 ${layerId} bounds:`, bounds);
      
      // 使用智能缩放级别计算
      const mapSize = [1024, 768]; // 假设的地图容器大小
      const zoomInfo = calculateOpenLayersZoomLevel(bounds, mapSize);
      const optimalZoom = zoomInfo.zoom.integer;
      
      console.log(`图层 ${layerId} OpenLayers计算信息:`, {
        optimalZoom: optimalZoom,
        extentSize: zoomInfo.extentSize,
        resolutions: zoomInfo.resolutions
      });

      // 根据策略类型和计算出的最优缩放级别确定缓存范围
      let zoomLevels;
      switch (strategyType) {
        case 'login':
          // 登录策略：以最优级别为中心，偏向低级别（概览）
          zoomLevels = getRecommendedZoomLevels(bounds, mapSize, 'overview');
          break;
        case 'scene_switch':
          // 场景切换：平衡策略，围绕最优级别
          zoomLevels = getRecommendedZoomLevels(bounds, mapSize, 'balanced');
          break;
        default:
          // 默认：保守策略
          zoomLevels = getRecommendedZoomLevels(bounds, mapSize, 'conservative');
      }
      
      //console.log(`图层 ${layerId} 推荐缩放级别:`, zoomLevels);
      
      for (const zoomLevel of zoomLevels) {
        try {
          const tileList = calculateTileList(bounds, zoomLevel);
          //console.log(`图层 ${layerId} 在缩放级别 ${zoomLevel} 需要 ${tileList.length} 个瓦片`);
          
          // 这里可以调用瓦片预加载逻辑
          // 暂时只记录日志，实际的瓦片加载会在地图组件中实现
          await this.simulatePreloadTiles(layerId, tileList, zoomLevel);
          
        } catch (error) {
          console.warn(`预加载图层 ${layerId} 缩放级别 ${zoomLevel} 失败:`, error);
        }
      }
    } catch (error) {
      console.error(`预加载图层 ${layerId} 瓦片失败:`, error);
    }
  }

  /**
   * 模拟预加载瓦片（实际实现时会调用地图组件的预加载方法）
   */
  async simulatePreloadTiles(layerId, tileList, zoomLevel) {
    if (!this.tileCacheService) {
      console.warn('缓存服务未初始化，跳过瓦片保存');
      return;
    }

    try {
      //console.log(`开始模拟预加载图层 ${layerId} 的 ${tileList.length} 个瓦片...`);
      
      // 为了演示，我们只保存前几个瓦片的模拟数据
      const maxTilesToSave = Math.min(tileList.length, 5); // 限制保存数量避免过多
      
      for (let i = 0; i < maxTilesToSave; i++) {
        const tile = tileList[i];
        
        try {
          // 创建一个简单的测试图片数据 (1x1像素的PNG)
          const testImageData = await this.createTestTileImage(tile.x, tile.y, zoomLevel);
          
          // 保存到IndexedDB
          await this.tileCacheService.saveTile(
            layerId,
            zoomLevel,
            tile.x,
            tile.y,
            testImageData,
            {
              contentType: 'image/png',
              url: `https://example.com/tiles/${zoomLevel}/${tile.x}/${tile.y}.png`,
              metadata: {
                strategy: 'background_preload',
                simulatedAt: Date.now()
              }
            }
          );
          
          //console.log(`保存测试瓦片: ${layerId}_${zoomLevel}_${tile.x}_${tile.y}`);
        } catch (error) {
          console.warn(`保存瓦片 ${tile.x},${tile.y} 失败:`, error);
        }
        
        // 添加小延迟避免阻塞UI
        if (i % 2 === 0) {
          await new Promise(resolve => setTimeout(resolve, 10));
        }
      }
      
      // 记录预加载信息到缓存系统的元数据中
      // const metadata = {
      //   layerId,
      //   zoomLevel,
      //   tileCount: tileList.length,
      //   savedTiles: maxTilesToSave,
      //   preloadedAt: Date.now(),
      //   strategy: 'background_preload'
      // };
      
      //console.log(`预加载完成:`, metadata);
    } catch (error) {
      console.error('模拟预加载瓦片失败:', error);
    }
  }

  /**
   * 创建测试瓦片图片数据
   */
  createTestTileImage(x, y, z) {
    // 创建一个简单的64x64像素的彩色测试图片
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    // 根据瓦片坐标生成不同颜色
    const r = (x * 50) % 255;
    const g = (y * 80) % 255;
    const b = (z * 120) % 255;
    
    ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
    ctx.fillRect(0, 0, 64, 64);
    
    // 添加文本标识
    ctx.fillStyle = 'white';
    ctx.font = '8px Arial';
    ctx.fillText(`${z}/${x}/${y}`, 2, 12);
    
    // 转换为Blob
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/png');
    });
  }

  /**
   * 检查当前加载状态
   */
  isLoading() {
    return this.loading;
  }

  /**
   * 停止当前加载任务
   */
  stopLoading() {
    this.loading = false;
  }
}

/**
 * 计算OpenLayers view.fit()会使用的缩放级别
 * 模拟OpenLayers内部的缩放级别计算逻辑
 * @param {object} bounds 边界 {west, south, east, north}
 * @param {Array<number>} mapSize 地图容器大小 [width, height] 像素
 * @param {Array<number>} padding 内边距 [top, right, bottom, left] 像素
 * @param {object} options 选项
 * @returns {object} 计算结果
 */
export function calculateOpenLayersZoomLevel(bounds, mapSize = [1024, 768], padding = [20, 20, 20, 20], options = {}) {
  // OpenLayers默认配置（Web墨卡托投影 EPSG:3857）
  const config = {
    maxResolution: 156543.03392804097, // 40075016.68557849 / 256
    minResolution: 0.0005831682455839253, // maxResolution / Math.pow(2, 28)
    zoomFactor: 2,
    maxZoom: 28,
    minZoom: 0,
    ...options
  };

  // 1. 计算有效显示区域（减去padding）
  const effectiveWidth = mapSize[0] - padding[1] - padding[3];
  const effectiveHeight = mapSize[1] - padding[0] - padding[2];

  // 2. 计算地理范围的大小（假设已转换为Web墨卡托坐标，单位：米）
  // 对于经纬度坐标，需要转换为Web墨卡托
  const extentWidth = Math.abs(bounds.east - bounds.west);
  const extentHeight = Math.abs(bounds.north - bounds.south);
  
  // 简化的经纬度到Web墨卡托转换（近似）
  // 实际OpenLayers会使用精确的投影变换
  const avgLat = (bounds.north + bounds.south) / 2;
  const metersPerDegree = 111319.9 * Math.cos(avgLat * Math.PI / 180);
  
  const extentWidthMeters = extentWidth * metersPerDegree;
  const extentHeightMeters = extentHeight * 111319.9; // 纬度方向相对固定

  // 3. 计算所需分辨率
  const resolutionX = extentWidthMeters / effectiveWidth;
  const resolutionY = extentHeightMeters / effectiveHeight;
  
  // 取较大值确保整个范围都能显示
  let targetResolution = Math.max(resolutionX, resolutionY);

  // 4. 应用分辨率约束
  targetResolution = Math.max(targetResolution, config.minResolution);
  targetResolution = Math.min(targetResolution, config.maxResolution);

  // 5. 计算对应的缩放级别
  const exactZoom = Math.log(config.maxResolution / targetResolution) / Math.log(config.zoomFactor);
  
  // 6. 应用缩放级别约束
  const constrainedZoom = Math.max(config.minZoom, Math.min(config.maxZoom, exactZoom));
  
  // 7. 如果需要整数缩放级别
  const integerZoom = Math.floor(constrainedZoom);
  const finalResolution = config.maxResolution / Math.pow(config.zoomFactor, integerZoom);

  return {
    bounds,
    mapSize,
    effectiveSize: [effectiveWidth, effectiveHeight],
    extentSize: {
      degrees: { width: extentWidth, height: extentHeight },
      meters: { width: extentWidthMeters, height: extentHeightMeters }
    },
    resolutions: {
      x: resolutionX,
      y: resolutionY,
      target: targetResolution,
      final: finalResolution
    },
    zoom: {
      exact: exactZoom,
      constrained: constrainedZoom,
      integer: integerZoom,
      recommended: integerZoom // view.fit通常使用整数缩放级别
    },
    tileInfo: {
      // 在推荐缩放级别下的瓦片信息
      zoomLevel: integerZoom,
      tileCount: calculateTileCount(bounds, integerZoom),
      // 建议的缓存缩放级别范围
      cacheRange: {
        min: Math.max(0, integerZoom - 2),
        max: Math.min(config.maxZoom, integerZoom + 3),
        levels: []
      }
    }
  };
}

/**
 * 为指定bounds推荐瓦片缓存的缩放级别
 * @param {object} bounds 边界
 * @param {Array<number>} mapSize 地图大小
 * @param {string} strategy 策略类型
 * @returns {Array<number>} 推荐的缩放级别数组
 */
export function getRecommendedZoomLevels(bounds, mapSize = [1024, 768], strategy = 'balanced') {
  const zoomInfo = calculateOpenLayersZoomLevel(bounds, mapSize);
  const baseZoom = zoomInfo.zoom.integer;
  
  let levels = [];
  
  switch (strategy) {
    case 'minimal':
      // 最小策略：只缓存当前最适合的级别
      levels = [baseZoom];
      break;
      
    case 'conservative':
      // 保守策略：当前级别 ± 1
      levels = [
        Math.max(0, baseZoom - 1),
        baseZoom,
        Math.min(28, baseZoom + 1)
      ];
      break;
      
    case 'balanced':
      // 平衡策略：当前级别 ± 2，重点在中高级别
      levels = [
        Math.max(0, baseZoom - 2),
        Math.max(0, baseZoom - 1),
        baseZoom,
        Math.min(28, baseZoom + 1),
        Math.min(28, baseZoom + 2)
      ];
      break;
      
    case 'aggressive':
      // 激进策略：更大范围，适合频繁缩放的场景
      levels = [
        Math.max(0, baseZoom - 3),
        Math.max(0, baseZoom - 2),
        Math.max(0, baseZoom - 1),
        baseZoom,
        Math.min(28, baseZoom + 1),
        Math.min(28, baseZoom + 2),
        Math.min(28, baseZoom + 3)
      ];
      break;
      
    case 'overview': {
      // 概览策略：偏向较低缩放级别，适合大范围预览
      const overviewBase = Math.max(0, baseZoom - 3);
      levels = [
        overviewBase,
        overviewBase + 1,
        overviewBase + 2,
        baseZoom
      ];
      break;
    }
      
    case 'detail':
      // 详细策略：偏向较高缩放级别，适合详细查看
      levels = [
        baseZoom,
        Math.min(28, baseZoom + 1),
        Math.min(28, baseZoom + 2),
        Math.min(28, baseZoom + 3),
        Math.min(28, baseZoom + 4)
      ];
      break;
      
    default:
      levels = [baseZoom];
  }
  
  // 去重并排序
  return [...new Set(levels)].sort((a, b) => a - b);
}

// 默认导出工具对象
export default {
  getGlobalCacheService,
  isIndexedDBSupported,
  formatFileSize,
  formatTimeAgo,
  calculateDistance,
  latLonToTile,
  tileToLatLon,
  calculateTileRange,
  calculateTileList,
  calculateTileCount,
  olExtentToBounds,
  leafletBoundsToBounds,
  calculateCacheSummary,
  generateCacheReport,
  preloadAreaTiles,
  loadAndCacheTile,
  buildTileUrl,
  cleanExpiredTiles,
  getCacheUsage,
  exportCacheConfig,
  applyCacheConfig,
  calculateOpenLayersZoomLevel,
  getRecommendedZoomLevels,
  CacheStrategyManager,
  CacheDebugger,
  DataCacheService
}; 