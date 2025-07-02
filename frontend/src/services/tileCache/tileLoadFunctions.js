/**
 * 自定义瓦片加载函数模块
 * 提供OpenLayers和Leaflet的瓦片缓存加载函数
 */

import { getGlobalCacheService } from './indexedDBOperations.js';
import { extractTileCoordinates, buildTileUrl } from './tileCalculations.js';

/**
 * 创建OpenLayers的瓦片缓存加载函数
 * @param {string} layerId 图层ID
 * @param {string} baseUrl 基础URL模板
 * @param {object} options 选项
 * @returns {Function} 瓦片加载函数
 */
export function createOpenLayersTileLoadFunction(layerId, baseUrl, options = {}) {
  const cacheService = getGlobalCacheService();
  const enableCache = options.enableCache !== false;
  const cacheFirst = options.cacheFirst !== false;
  const debug = options.debug || false;
  
  return (tile, src) => {
    if (!enableCache) {
      // 缓存未启用，直接加载
      loadTileFromNetwork(tile, src);
      return;
    }

    const coords = extractTileCoordinates(src, baseUrl);
    if (!coords) {
      // 无法提取坐标，降级到普通加载
      loadTileFromNetwork(tile, src);
      return;
    }

    const { z, x, y } = coords;

    if (tile.getImage) {
      // 栅格瓦片处理
      handleRasterTile(tile, src, layerId, z, x, y, cacheService, cacheFirst, debug);
    } else {
      // 矢量瓦片处理
      handleVectorTile(tile, src, layerId, z, x, y, cacheService, cacheFirst, debug);
    }
  };
}

/**
 * 处理栅格瓦片加载
 */
function handleRasterTile(tile, src, layerId, z, x, y, cacheService, cacheFirst, debug) {
  const image = tile.getImage();
  
  if (cacheFirst) {
    // 优先检查缓存
    cacheService.getTile(layerId, z, x, y).then((cachedTile) => {
      if (cachedTile) {
        // 从缓存加载
        loadImageFromCache(image, cachedTile, debug);
      } else {
        // 缓存未命中，从网络加载并缓存
        loadImageFromNetworkWithCache(image, src, layerId, z, x, y, cacheService, debug);
      }
    }).catch((error) => {
      console.error('检查缓存失败:', error);
      // 降级到普通加载
      image.src = src;
    });
  } else {
    // 直接从网络加载并缓存
    loadImageFromNetworkWithCache(image, src, layerId, z, x, y, cacheService, debug);
  }
}

/**
 * 处理矢量瓦片加载
 */
function handleVectorTile(tile, src, layerId, z, x, y, cacheService, cacheFirst, debug) {
  if (cacheFirst) {
    // 优先检查缓存
    cacheService.getTile(layerId, z, x, y).then((cachedTile) => {
      if (cachedTile) {
        // 从缓存加载
        loadVectorTileFromCache(tile, cachedTile, debug);
      } else {
        // 缓存未命中，从网络加载并缓存
        loadVectorTileFromNetworkWithCache(tile, src, layerId, z, x, y, cacheService, debug);
      }
    }).catch((error) => {
      console.error('检查缓存失败:', error);
      // 降级到普通加载
      loadVectorTileFromNetwork(tile, src);
    });
  } else {
    // 直接从网络加载并缓存
    loadVectorTileFromNetworkWithCache(tile, src, layerId, z, x, y, cacheService, debug);
  }
}

/**
 * 从缓存加载图片
 */
function loadImageFromCache(image, cachedTile, debug) {
  const imageUrl = URL.createObjectURL(cachedTile.data);
  
  image.onload = () => {
    URL.revokeObjectURL(imageUrl);
    if (debug) {
      console.log(`✅ 缓存瓦片加载成功: ${cachedTile.id}`);
    }
  };
  
  image.onerror = () => {
    URL.revokeObjectURL(imageUrl);
    console.error(`❌ 缓存瓦片加载失败: ${cachedTile.id}`);
  };
  
  image.src = imageUrl;
}

/**
 * 从网络加载图片并缓存
 */
function loadImageFromNetworkWithCache(image, src, layerId, z, x, y, cacheService, debug) {
  fetch(src, {
    method: 'GET',
    mode: 'cors',
    cache: 'force-cache'
  }).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.blob();
  }).then((blob) => {
    // 创建图片URL
    const imageUrl = URL.createObjectURL(blob);
    
    image.onload = () => {
      URL.revokeObjectURL(imageUrl);
      if (debug) {
        console.log(`✅ 网络瓦片加载成功: ${layerId}_${z}_${x}_${y}`);
      }
    };
    
    image.onerror = () => {
      URL.revokeObjectURL(imageUrl);
      console.error(`❌ 网络瓦片图像加载失败: ${layerId}_${z}_${x}_${y}`);
    };
    
    image.src = imageUrl;
    
    // 异步保存到缓存
    cacheService.saveTile(layerId, z, x, y, blob, {
      contentType: blob.type || 'image/png',
      url: src
    }).catch(err => {
      console.warn('缓存瓦片失败:', err);
    });
    
  }).catch((error) => {
    console.warn('网络请求失败，降级到标准加载:', error.message);
    image.src = src;
  });
}

/**
 * 从缓存加载矢量瓦片
 */
function loadVectorTileFromCache(tile, cachedTile, debug) {
  try {
    // 设置瓦片数据
    if (tile.setFeatures && cachedTile.data) {
      // 如果是解析后的要素数据
      tile.setFeatures(cachedTile.data);
    } else if (tile.setData && cachedTile.data) {
      // 如果是原始二进制数据
      tile.setData(cachedTile.data);
    }
    
    if (debug) {
      console.log(`✅ 缓存矢量瓦片加载成功: ${cachedTile.id}`);
    }
  } catch (error) {
    console.error('加载缓存矢量瓦片失败:', error);
    throw error;
  }
}

/**
 * 从网络加载矢量瓦片并缓存
 */
function loadVectorTileFromNetworkWithCache(tile, src, layerId, z, x, y, cacheService, debug) {
  fetch(src, {
    method: 'GET',
    mode: 'cors'
  }).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.arrayBuffer();
  }).then((arrayBuffer) => {
    // 设置瓦片数据
    tile.setData(arrayBuffer);
    
    if (debug) {
      console.log(`✅ 网络矢量瓦片加载成功: ${layerId}_${z}_${x}_${y}`);
    }
    
    // 异步保存到缓存
    const blob = new Blob([arrayBuffer], { type: 'application/x-protobuf' });
    cacheService.saveTile(layerId, z, x, y, blob, {
      contentType: 'application/x-protobuf',
      url: src
    }).catch(err => {
      console.warn('缓存矢量瓦片失败:', err);
    });
    
  }).catch((error) => {
    console.warn('矢量瓦片网络请求失败:', error.message);
    loadVectorTileFromNetwork(tile, src);
  });
}

/**
 * 普通的瓦片网络加载（降级方案）
 */
function loadTileFromNetwork(tile, src) {
  if (tile.getImage) {
    // 栅格瓦片
    const image = tile.getImage();
    image.onload = () => {};
    image.onerror = () => console.error('瓦片加载失败:', src);
    image.src = src;
  } else {
    // 矢量瓦片
    loadVectorTileFromNetwork(tile, src);
  }
}

/**
 * 普通的矢量瓦片网络加载
 */
function loadVectorTileFromNetwork(tile, src) {
  fetch(src).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.arrayBuffer();
  }).then((arrayBuffer) => {
    tile.setData(arrayBuffer);
  }).catch((error) => {
    console.error('矢量瓦片加载失败:', error);
  });
}

/**
 * 创建Leaflet的瓦片缓存加载函数
 * @param {string} layerId 图层ID
 * @param {object} options 选项
 * @returns {object} Leaflet瓦片图层扩展
 */
export function createLeafletCachedTileLayer(layerId, urlTemplate, options = {}) {
  // 检查Leaflet是否可用
  if (typeof window === 'undefined' || !window.L) {
    console.error('Leaflet 未加载');
    return null;
  }

  const cacheService = getGlobalCacheService();
  const enableCache = options.enableCache !== false;
  const cacheFirst = options.cacheFirst !== false;

  // 扩展Leaflet的TileLayer
  const CachedTileLayer = window.L.TileLayer.extend({
    initialize: function(url, opts) {
      this.layerId = layerId;
      this.cacheService = cacheService;
      this.enableCache = enableCache;
      this.cacheFirst = cacheFirst;
      window.L.TileLayer.prototype.initialize.call(this, url, opts);
    },

    createTile: function(coords, done) {
      const tile = document.createElement('img');
      const url = this.getTileUrl(coords);
      
      if (this.options.crossOrigin || this.options.crossOrigin === '') {
        tile.crossOrigin = this.options.crossOrigin;
      }

      this.loadTileWithCache(tile, url, coords, done);
      return tile;
    },

    loadTileWithCache: async function(tile, url, coords, done) {
      if (!this.enableCache) {
        this.loadTileFromNetwork(tile, url, done);
        return;
      }

      const { x, y, z } = coords;

      try {
        if (this.cacheFirst) {
          const cachedTile = await this.cacheService.getTile(this.layerId, z, x, y);
          if (cachedTile) {
            this.loadTileFromCache(tile, cachedTile, done);
            return;
          }
        }

        await this.loadTileFromNetworkWithCache(tile, url, this.layerId, z, x, y, done);
      } catch (error) {
        console.error('瓦片加载失败:', error);
        this.loadTileFromNetwork(tile, url, done);
      }
    },

    loadTileFromNetworkWithCache: async function(tile, url, layerId, z, x, y, done) {
      try {
        const response = await fetch(url, { mode: 'cors' });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        tile.onload = () => {
          URL.revokeObjectURL(imageUrl);
          done(null, tile);
        };
        
        tile.onerror = (error) => {
          URL.revokeObjectURL(imageUrl);
          done(error, tile);
        };
        
        tile.src = imageUrl;
        
        // 异步保存到缓存
        this.cacheService.saveTile(layerId, z, x, y, blob, {
          contentType: blob.type || 'image/png',
          url
        }).catch(err => {
          console.warn('缓存瓦片失败:', err);
        });
        
      } catch (error) {
        console.error('网络请求失败:', error);
        done(error, tile);
      }
    },

    loadTileFromCache: function(tile, cachedTile, done) {
      const url = URL.createObjectURL(cachedTile.data);
      
      tile.onload = () => {
        URL.revokeObjectURL(url);
        done(null, tile);
      };
      
      tile.onerror = (error) => {
        URL.revokeObjectURL(url);
        done(error, tile);
      };
      
      tile.src = url;
    },

    loadTileFromNetwork: function(tile, url, done) {
      tile.onload = () => done(null, tile);
      tile.onerror = (error) => done(error, tile);
      tile.src = url;
    }
  });

  return new CachedTileLayer(urlTemplate, options);
}

/**
 * 创建带缓存的WMS图层加载函数
 * @param {string} layerId 图层ID
 * @param {string} baseUrl WMS服务基础URL
 * @param {object} options WMS图层选项
 * @returns {Function} WMS瓦片加载函数
 */
export function createWMSTileLoadFunction(layerId, baseUrl, options = {}) {
  const cacheService = getGlobalCacheService();
  const enableCache = options.enableCache !== false;
  const cacheFirst = options.cacheFirst !== false;
  
  return (tile, src) => {
    if (!enableCache) {
      loadTileFromNetwork(tile, src);
      return;
    }

    // WMS URL通常包含bbox参数，需要特殊处理来提取坐标
    const coords = extractWMSCoordinates(src);
    if (!coords) {
      loadTileFromNetwork(tile, src);
      return;
    }

    const { z, x, y } = coords;
    
    if (tile.getImage) {
      handleRasterTile(tile, src, layerId, z, x, y, cacheService, cacheFirst, false);
    } else {
      loadTileFromNetwork(tile, src);
    }
  };
}

/**
 * 从WMS URL中提取瓦片坐标（简化实现）
 */
function extractWMSCoordinates(url) {
  // 这是一个简化的实现，实际使用中可能需要更复杂的逻辑
  // 根据bbox参数和图层配置计算瓦片坐标
  const coords = extractTileCoordinates(url);
  return coords;
}

/**
 * 预加载区域瓦片
 * @param {string} layerId 图层ID
 * @param {string} urlTemplate URL模板
 * @param {object} bounds 边界
 * @param {number} minZoom 最小缩放级别
 * @param {number} maxZoom 最大缩放级别
 * @param {Function} progressCallback 进度回调
 */
export async function preloadAreaTiles(layerId, urlTemplate, bounds, minZoom, maxZoom, progressCallback) {
  const cacheService = getGlobalCacheService();
  const { calculateTileList } = await import('./tileCalculations.js');
  
  const tileList = calculateTileList(bounds, { min: minZoom, max: maxZoom });
  let completed = 0;
  
  for (const { z, x, y } of tileList) {
    try {
      // 检查是否已缓存
      const cached = await cacheService.getTile(layerId, z, x, y);
      if (!cached) {
        // 构建URL并下载
        const url = buildTileUrl(urlTemplate, z, x, y);
        const response = await fetch(url);
        if (response.ok) {
          const blob = await response.blob();
          await cacheService.saveTile(layerId, z, x, y, blob, {
            contentType: blob.type || 'image/png',
            url
          });
        }
      }
      
      completed++;
      if (progressCallback) {
        progressCallback(completed, tileList.length);
      }
    } catch (error) {
      console.warn(`预加载瓦片失败 ${z}/${x}/${y}:`, error);
      completed++;
      if (progressCallback) {
        progressCallback(completed, tileList.length);
      }
    }
  }
}

export default {
  createOpenLayersTileLoadFunction,
  createLeafletCachedTileLayer,
  createWMSTileLoadFunction,
  preloadAreaTiles
}; 