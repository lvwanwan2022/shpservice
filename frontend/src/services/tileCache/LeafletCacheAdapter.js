import TileCacheService from './TileCacheService.js';

/**
 * Leaflet 瓦片缓存适配器
 * 将瓦片缓存功能集成到 Leaflet 中
 */
class LeafletCacheAdapter {
  constructor(options = {}) {
    this.cacheService = new TileCacheService();
    this.enableCache = options.enableCache !== false; // 默认启用缓存
    this.cacheBeforeNetwork = options.cacheBeforeNetwork !== false; // 默认优先使用缓存
    this.debug = options.debug || false;
  }

  /**
   * 创建带缓存功能的Leaflet瓦片图层
   * @param {string} layerId 图层ID
   * @param {string} urlTemplate URL模板
   * @param {object} options Leaflet瓦片图层选项
   * @returns {object} Leaflet瓦片图层
   */
  createCachedTileLayer(layerId, urlTemplate, options = {}) {
    // 检查Leaflet是否可用
    if (typeof window === 'undefined' || !window.L) {
      console.error('Leaflet 未加载');
      return null;
    }

    // 扩展Leaflet的TileLayer
    const CachedTileLayer = window.L.TileLayer.extend({
      initialize: function(url, opts) {
        this.layerId = layerId;
        this.cacheAdapter = this;
        window.L.TileLayer.prototype.initialize.call(this, url, opts);
      }.bind(this),

      createTile: function(coords, done) {
        const tile = document.createElement('img');
        const url = this.getTileUrl(coords);
        
        // 设置瓦片属性
        if (this.options.crossOrigin || this.options.crossOrigin === '') {
          tile.crossOrigin = this.options.crossOrigin;
        }

        // 使用缓存加载瓦片
        this.loadTileWithCache(tile, url, coords, done);
        
        return tile;
      }.bind(this),

      loadTileWithCache: async function(tile, url, coords, done) {
        if (!this.enableCache) {
          // 如果缓存未启用，直接加载
          this.loadTileFromNetwork(tile, url, done);
          return;
        }

        const { x, y, z } = coords;

        try {
          if (this.cacheBeforeNetwork) {
            // 优先从缓存加载
            const cachedTile = await this.cacheService.getTile(layerId, z, x, y);
            if (cachedTile) {
              this.loadTileFromCache(tile, cachedTile, done);
              
              return;
            }
          }

          // 从网络加载并缓存
          await this.loadTileFromNetworkWithCache(tile, url, layerId, z, x, y, done);
        } catch (error) {
          console.error('瓦片加载失败:', error);
          this.loadTileFromNetwork(tile, url, done); // 降级到普通加载
        }
      }.bind(this),

      loadTileFromNetworkWithCache: async function(tile, url, layerId, z, x, y, done) {
        const img = new Image();
        
        // 设置跨域
        if (this.options.crossOrigin || this.options.crossOrigin === '') {
          img.crossOrigin = this.options.crossOrigin;
        }

        img.onload = async () => {
          try {
            // 将图片转换为Blob进行缓存
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob(async (blob) => {
              if (blob) {
                // 保存到缓存
                await this.cacheService.saveTile(layerId, z, x, y, blob, {
                  contentType: 'image/png',
                  url
                });
                
                
              }
            }, 'image/png');

            // 设置瓦片图像
            tile.src = url;
            done(null, tile);
          } catch (error) {
            console.error('缓存瓦片时出错:', error);
            done(error, tile);
          }
        };

        img.onerror = (error) => {
          console.error(`瓦片加载失败: ${url}`, error);
          done(error, tile);
        };

        img.src = url;
      }.bind(this),

      loadTileFromCache: function(tile, cachedTile, done) {
        const url = URL.createObjectURL(cachedTile.data);
        
        tile.onload = () => {
          URL.revokeObjectURL(url); // 清理URL对象
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
   * 创建带缓存的WMS图层
   * @param {string} layerId 图层ID
   * @param {string} baseUrl WMS服务基础URL
   * @param {object} options WMS图层选项
   * @returns {object} Leaflet WMS图层
   */
  createCachedWMSLayer(layerId, baseUrl, options = {}) {
    if (typeof window === 'undefined' || !window.L) {
      console.error('Leaflet 未加载');
      return null;
    }

    const wmsOptions = {
      layers: options.layers,
      format: options.format || 'image/png',
      transparent: options.transparent !== false,
      version: options.version || '1.1.1',
      crs: options.crs || window.L.CRS.EPSG3857,
      ...options
    };

    // 创建WMS图层，但使用自定义的瓦片加载
    const CachedWMSLayer = window.L.TileLayer.WMS.extend({
      initialize: function(url, opts) {
        this.layerId = layerId;
        this.cacheAdapter = this;
        window.L.TileLayer.WMS.prototype.initialize.call(this, url, opts);
      }.bind(this),

      createTile: function(coords, done) {
        const tile = document.createElement('img');
        const url = this.getTileUrl(coords);
        
        if (this.options.crossOrigin || this.options.crossOrigin === '') {
          tile.crossOrigin = this.options.crossOrigin;
        }

        this.loadTileWithCache(tile, url, coords, done);
        return tile;
      }.bind(this),

      loadTileWithCache: async function(tile, url, coords, done) {
        if (!this.enableCache) {
          this.loadTileFromNetwork(tile, url, done);
          return;
        }

        const { x, y, z } = coords;

        try {
          if (this.cacheBeforeNetwork) {
            const cachedTile = await this.cacheService.getTile(layerId, z, x, y);
            if (cachedTile) {
              this.loadTileFromCache(tile, cachedTile, done);
              
              return;
            }
          }

          await this.loadTileFromNetworkWithCache(tile, url, layerId, z, x, y, done);
        } catch (error) {
          console.error('WMS瓦片加载失败:', error);
          this.loadTileFromNetwork(tile, url, done);
        }
      }.bind(this),

      loadTileFromNetworkWithCache: async function(tile, url, layerId, z, x, y, done) {
        const img = new Image();
        
        if (this.options.crossOrigin || this.options.crossOrigin === '') {
          img.crossOrigin = this.options.crossOrigin;
        }

        img.onload = async () => {
          try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob(async (blob) => {
              if (blob) {
                await this.cacheService.saveTile(layerId, z, x, y, blob, {
                  contentType: this.options.format || 'image/png',
                  url
                });
                
               
              }
            }, this.options.format || 'image/png');

            tile.src = url;
            done(null, tile);
          } catch (error) {
            console.error('缓存WMS瓦片时出错:', error);
            done(error, tile);
          }
        };

        img.onerror = (error) => {
          console.error(`WMS瓦片加载失败: ${url}`, error);
          done(error, tile);
        };

        img.src = url;
      }.bind(this),

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

    return new CachedWMSLayer(baseUrl, wmsOptions);
  }

  /**
   * 预加载指定区域的瓦片
   * @param {string} layerId 图层ID
   * @param {string} urlTemplate URL模板
   * @param {object} bounds Leaflet LatLngBounds对象
   * @param {number} minZoom 最小缩放级别
   * @param {number} maxZoom 最大缩放级别
   * @param {Function} progressCallback 进度回调
   */
  async preloadTiles(layerId, urlTemplate, bounds, minZoom, maxZoom, progressCallback) {
    if (typeof L === 'undefined') {
      console.error('Leaflet 未加载');
      return;
    }

    try {
      let totalTiles = 0;
      let loadedTiles = 0;

      // 计算总瓦片数
      for (let zoom = minZoom; zoom <= maxZoom; zoom++) {
        const tileBounds = this.getTileBounds(bounds, zoom);
        totalTiles += (tileBounds.maxX - tileBounds.minX + 1) * (tileBounds.maxY - tileBounds.minY + 1);
      }

      // 逐级预加载
      for (let zoom = minZoom; zoom <= maxZoom; zoom++) {
        const tileBounds = this.getTileBounds(bounds, zoom);
        const promises = [];

        for (let x = tileBounds.minX; x <= tileBounds.maxX; x++) {
          for (let y = tileBounds.minY; y <= tileBounds.maxY; y++) {
            // 检查是否已缓存
            const hasCached = await this.cacheService.hasTile(layerId, zoom, x, y);
            if (!hasCached) {
              const tileUrl = this.buildTileUrl(urlTemplate, zoom, x, y);
              
              const promise = this.preloadSingleTile(layerId, tileUrl, zoom, x, y)
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
        //console.log(`缩放级别 ${zoom} 预加载完成`);
      }

      //console.log(`预加载完成: ${layerId}`);
    } catch (error) {
      console.error('预加载瓦片时出错:', error);
    }
  }

  /**
   * 预加载单个瓦片
   * @param {string} layerId 图层ID
   * @param {string} url 瓦片URL
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   */
  async preloadSingleTile(layerId, url, z, x, y) {
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
              await this.cacheService.saveTile(layerId, z, x, y, blob, {
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
   * 获取瓦片边界
   * @param {object} bounds Leaflet LatLngBounds对象
   * @param {number} zoom 缩放级别
   * @returns {object} 瓦片边界
   */
  getTileBounds(bounds, zoom) {
    if (typeof window === 'undefined' || !window.L) {
      throw new Error('Leaflet 未加载');
    }

    const tileSize = 256;
    const northWest = bounds.getNorthWest();
    const southEast = bounds.getSouthEast();
    
    const nwPoint = window.L.CRS.EPSG3857.latLngToPoint(northWest, zoom);
    const sePoint = window.L.CRS.EPSG3857.latLngToPoint(southEast, zoom);
    
    return {
      minX: Math.floor(nwPoint.x / tileSize),
      minY: Math.floor(nwPoint.y / tileSize),
      maxX: Math.floor(sePoint.x / tileSize),
      maxY: Math.floor(sePoint.y / tileSize)
    };
  }

  /**
   * 构建瓦片URL
   * @param {string} urlTemplate URL模板
   * @param {number} z 缩放级别
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @returns {string} 瓦片URL
   */
  buildTileUrl(urlTemplate, z, x, y) {
    return urlTemplate
      .replace('{z}', z.toString())
      .replace('{x}', x.toString())
      .replace('{y}', y.toString())
      .replace('{s}', 'a'); // 默认子域名
  }

  /**
   * 获取缓存服务实例
   * @returns {TileCacheService} 缓存服务实例
   */
  getCacheService() {
    return this.cacheService;
  }

  /**
   * 启用/禁用缓存
   * @param {boolean} enabled 是否启用
   */
  setEnableCache(enabled) {
    this.enableCache = enabled;
  }

  /**
   * 设置是否优先使用缓存
   * @param {boolean} cacheFirst 是否优先使用缓存
   */
  setCacheFirst(cacheFirst) {
    this.cacheBeforeNetwork = cacheFirst;
  }

  /**
   * 创建缓存管理控件
   * @param {object} options 控件选项
   * @returns {object} Leaflet控件
   */
  createCacheControl(options = {}) {
    if (typeof window === 'undefined' || !window.L) {
      console.error('Leaflet 未加载');
      return null;
    }

    const CacheControl = window.L.Control.extend({
      options: {
        position: 'topright'
      },

      onAdd: function() {
        const container = window.L.DomUtil.create('div', 'leaflet-cache-control leaflet-bar');
        container.style.backgroundColor = 'white';
        container.style.padding = '5px';
        
        // 创建按钮
        const clearButton = window.L.DomUtil.create('button', '', container);
        clearButton.innerHTML = '清理缓存';
        clearButton.title = '清理所有瓦片缓存';
        
        const statsButton = window.L.DomUtil.create('button', '', container);
        statsButton.innerHTML = '缓存统计';
        statsButton.title = '查看缓存统计信息';
        
        // 绑定事件
        window.L.DomEvent.on(clearButton, 'click', async () => {
          if (confirm('确定要清理所有瓦片缓存吗？')) {
            await this.cacheService.clearAllCache();
            alert('缓存已清理');
          }
        }, this);
        
        window.L.DomEvent.on(statsButton, 'click', async () => {
          const stats = await this.cacheService.getCacheStats();
          const message = `总瓦片数: ${stats.totalTiles}\n总大小: ${(stats.totalSize / 1024 / 1024).toFixed(2)} MB\n图层数: ${Object.keys(stats.layerStats).length}`;
          alert(message);
        }, this);
        
        return container;
      }.bind(this)
    });

    return new CacheControl(options);
  }
}

export default LeafletCacheAdapter; 