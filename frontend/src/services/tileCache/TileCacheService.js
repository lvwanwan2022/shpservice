import TileCacheDB from './TileCacheDB.js';

/**
 * 瓦片缓存服务类
 * 提供瓦片数据的增删改查等操作
 */
class TileCacheService {
  constructor() {
    this.db = new TileCacheDB();
    this.maxCacheSize = 500 * 1024 * 1024; // 最大缓存大小 500MB
    this.maxCacheAge = 7 * 24 * 60 * 60 * 1000; // 最大缓存时间 7天
  }

  /**
   * 保存瓦片数据到缓存
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @param {number} tileX 瓦片X坐标
   * @param {number} tileY 瓦片Y坐标
   * @param {Blob|ArrayBuffer|Uint8Array} tileData 瓦片数据
   * @param {object} options 额外选项
   * @returns {Promise<boolean>} 是否保存成功
   */
  async saveTile(layerId, zoomLevel, tileX, tileY, tileData, options = {}) {
    try {
      const tileId = this.db.generateTileId(layerId, zoomLevel, tileX, tileY);
      const timestamp = Date.now();
      
      // 确保tileData是Blob格式
      let blob;
      
      // 添加调试信息
      console.log('瓦片数据类型:', typeof tileData, tileData?.constructor?.name);
      
      if (tileData instanceof Blob) {
        blob = tileData;
      } else if (tileData instanceof ArrayBuffer) {
        blob = new Blob([tileData]);
      } else if (tileData instanceof Uint8Array) {
        blob = new Blob([tileData]);
      } else if (tileData && typeof tileData === 'object' && tileData.then) {
        // 如果是Promise，等待它完成
        console.warn('检测到Promise对象，正在等待...');
        blob = await tileData;
        if (!(blob instanceof Blob)) {
          throw new Error(`Promise解析后的数据格式不正确: ${typeof blob}`);
        }
      } else {
        console.error('不支持的瓦片数据:', {
          type: typeof tileData,
          constructor: tileData?.constructor?.name,
          isBlob: tileData instanceof Blob,
          isArrayBuffer: tileData instanceof ArrayBuffer,
          isUint8Array: tileData instanceof Uint8Array,
          data: tileData
        });
        throw new Error(`不支持的瓦片数据格式: ${typeof tileData} (${tileData?.constructor?.name})`);
      }

      const tileRecord = {
        id: tileId,
        layerId,
        zoomLevel,
        tileX,
        tileY,
        data: blob,
        timestamp,
        size: blob.size,
        contentType: options.contentType || 'image/png',
        url: options.url || '', // 原始URL（可选）
        metadata: options.metadata || {} // 额外元数据
      };

      const store = await this.db.getStore('readwrite');
      
      return new Promise((resolve, reject) => {
        const request = store.put(tileRecord);
        
        request.onsuccess = () => {
          console.log(`瓦片缓存保存成功: ${tileId}`);
          resolve(true);
        };
        
        request.onerror = (event) => {
          console.error('瓦片缓存保存失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('保存瓦片时出错:', error);
      return false;
    }
  }

  /**
   * 获取瓦片数据
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @param {number} tileX 瓦片X坐标
   * @param {number} tileY 瓦片Y坐标
   * @returns {Promise<object|null>} 瓦片数据对象或null
   */
  async getTile(layerId, zoomLevel, tileX, tileY) {
    try {
      const tileId = this.db.generateTileId(layerId, zoomLevel, tileX, tileY);
      const store = await this.db.getStore('readonly');
      
      return new Promise((resolve, reject) => {
        const request = store.get(tileId);
        
        request.onsuccess = (event) => {
          const result = event.target.result;
          if (result) {
            // 检查缓存是否过期
            if (this.isCacheExpired(result.timestamp)) {
              console.log(`瓦片缓存已过期: ${tileId}`);
              this.deleteTile(layerId, zoomLevel, tileX, tileY); // 异步删除过期缓存
              resolve(null);
            } else {
              resolve(result);
            }
          } else {
            resolve(null);
          }
        };
        
        request.onerror = (event) => {
          console.error('获取瓦片缓存失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('获取瓦片时出错:', error);
      return null;
    }
  }

  /**
   * 检查瓦片是否存在缓存
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @param {number} tileX 瓦片X坐标
   * @param {number} tileY 瓦片Y坐标
   * @returns {Promise<boolean>} 是否存在缓存
   */
  async hasTile(layerId, zoomLevel, tileX, tileY) {
    const tile = await this.getTile(layerId, zoomLevel, tileX, tileY);
    return tile !== null;
  }

  /**
   * 删除指定瓦片缓存
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @param {number} tileX 瓦片X坐标
   * @param {number} tileY 瓦片Y坐标
   * @returns {Promise<boolean>} 是否删除成功
   */
  async deleteTile(layerId, zoomLevel, tileX, tileY) {
    try {
      const tileId = this.db.generateTileId(layerId, zoomLevel, tileX, tileY);
      const store = await this.db.getStore('readwrite');
      
      return new Promise((resolve, reject) => {
        const request = store.delete(tileId);
        
        request.onsuccess = () => {
          console.log(`瓦片缓存删除成功: ${tileId}`);
          resolve(true);
        };
        
        request.onerror = (event) => {
          console.error('瓦片缓存删除失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('删除瓦片时出错:', error);
      return false;
    }
  }

  /**
   * 删除指定图层的所有缓存
   * @param {string} layerId 图层ID
   * @returns {Promise<number>} 删除的瓦片数量
   */
  async deleteLayerCache(layerId) {
    try {
      const store = await this.db.getStore('readwrite');
      const index = store.index('layerId');
      let deleteCount = 0;
      
      return new Promise((resolve, reject) => {
        const request = index.openCursor(IDBKeyRange.only(layerId));
        
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor) {
            const deleteRequest = cursor.delete();
            deleteRequest.onsuccess = () => {
              deleteCount++;
            };
            cursor.continue();
          } else {
            console.log(`删除图层 ${layerId} 的 ${deleteCount} 个瓦片缓存`);
            resolve(deleteCount);
          }
        };
        
        request.onerror = (event) => {
          console.error('删除图层缓存失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('删除图层缓存时出错:', error);
      return 0;
    }
  }

  /**
   * 删除指定图层和缩放级别的缓存
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @returns {Promise<number>} 删除的瓦片数量
   */
  async deleteLayerZoomCache(layerId, zoomLevel) {
    try {
      const store = await this.db.getStore('readwrite');
      const index = store.index('layerZoom');
      let deleteCount = 0;
      
      return new Promise((resolve, reject) => {
        const request = index.openCursor(IDBKeyRange.only([layerId, zoomLevel]));
        
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor) {
            const deleteRequest = cursor.delete();
            deleteRequest.onsuccess = () => {
              deleteCount++;
            };
            cursor.continue();
          } else {
            console.log(`删除图层 ${layerId} 缩放级别 ${zoomLevel} 的 ${deleteCount} 个瓦片缓存`);
            resolve(deleteCount);
          }
        };
        
        request.onerror = (event) => {
          console.error('删除图层缩放级别缓存失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('删除图层缩放级别缓存时出错:', error);
      return 0;
    }
  }

  /**
   * 获取瓦片数据的URL（用于显示）
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @param {number} tileX 瓦片X坐标
   * @param {number} tileY 瓦片Y坐标
   * @returns {Promise<string|null>} 瓦片数据URL或null
   */
  async getTileUrl(layerId, zoomLevel, tileX, tileY) {
    const tile = await this.getTile(layerId, zoomLevel, tileX, tileY);
    if (tile && tile.data) {
      return URL.createObjectURL(tile.data);
    }
    return null;
  }

  /**
   * 获取缓存统计信息
   * @returns {Promise<object>} 缓存统计信息
   */
  async getCacheStats() {
    try {
      const store = await this.db.getStore('readonly');
      const stats = {
        totalTiles: 0,
        totalSize: 0,
        layerStats: {},
        oldestTile: null,
        newestTile: null
      };
      
      return new Promise((resolve, reject) => {
        const request = store.openCursor();
        
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor) {
            const tile = cursor.value;
            stats.totalTiles++;
            stats.totalSize += tile.size || 0;
            
            // 按图层统计
            if (!stats.layerStats[tile.layerId]) {
              stats.layerStats[tile.layerId] = {
                count: 0,
                size: 0,
                zoomLevels: new Set()
              };
            }
            stats.layerStats[tile.layerId].count++;
            stats.layerStats[tile.layerId].size += tile.size || 0;
            stats.layerStats[tile.layerId].zoomLevels.add(tile.zoomLevel);
            
            // 时间统计
            if (!stats.oldestTile || tile.timestamp < stats.oldestTile.timestamp) {
              stats.oldestTile = tile;
            }
            if (!stats.newestTile || tile.timestamp > stats.newestTile.timestamp) {
              stats.newestTile = tile;
            }
            
            cursor.continue();
          } else {
            // 转换Set为数组
            Object.keys(stats.layerStats).forEach(layerId => {
              stats.layerStats[layerId].zoomLevels = Array.from(stats.layerStats[layerId].zoomLevels);
            });
            
            resolve(stats);
          }
        };
        
        request.onerror = (event) => {
          console.error('获取缓存统计失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('获取缓存统计时出错:', error);
      return null;
    }
  }

  /**
   * 清理过期缓存
   * @returns {Promise<number>} 清理的瓦片数量
   */
  async cleanExpiredCache() {
    try {
      const store = await this.db.getStore('readwrite');
      const index = store.index('timestamp');
      const cutoffTime = Date.now() - this.maxCacheAge;
      let cleanCount = 0;
      
      return new Promise((resolve, reject) => {
        const request = index.openCursor(IDBKeyRange.upperBound(cutoffTime));
        
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor) {
            const deleteRequest = cursor.delete();
            deleteRequest.onsuccess = () => {
              cleanCount++;
            };
            cursor.continue();
          } else {
            console.log(`清理了 ${cleanCount} 个过期瓦片缓存`);
            resolve(cleanCount);
          }
        };
        
        request.onerror = (event) => {
          console.error('清理过期缓存失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('清理过期缓存时出错:', error);
      return 0;
    }
  }

  /**
   * 清理所有缓存
   * @returns {Promise<boolean>} 是否清理成功
   */
  async clearAllCache() {
    try {
      const store = await this.db.getStore('readwrite');
      
      return new Promise((resolve, reject) => {
        const request = store.clear();
        
        request.onsuccess = () => {
          console.log('所有瓦片缓存已清理');
          resolve(true);
        };
        
        request.onerror = (event) => {
          console.error('清理所有缓存失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('清理所有缓存时出错:', error);
      return false;
    }
  }

  /**
   * 获取所有瓦片数据
   * @returns {Promise<Array>} 所有瓦片数据数组
   */
  async getAllTiles() {
    try {
      const store = await this.db.getStore('readonly');
      
      return new Promise((resolve, reject) => {
        const request = store.getAll();
        
        request.onsuccess = (event) => {
          const tiles = event.target.result || [];
          console.log(`获取到 ${tiles.length} 个瓦片数据`);
          resolve(tiles);
        };
        
        request.onerror = (event) => {
          console.error('获取所有瓦片失败:', event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error('获取所有瓦片时出错:', error);
      return [];
    }
  }

  /**
   * 检查缓存是否过期
   * @param {number} timestamp 缓存时间戳
   * @returns {boolean} 是否过期
   */
  isCacheExpired(timestamp) {
    return (Date.now() - timestamp) > this.maxCacheAge;
  }

  /**
   * 设置最大缓存大小
   * @param {number} size 大小（字节）
   */
  setMaxCacheSize(size) {
    this.maxCacheSize = size;
  }

  /**
   * 设置最大缓存时间
   * @param {number} age 时间（毫秒）
   */
  setMaxCacheAge(age) {
    this.maxCacheAge = age;
  }

  /**
   * 清空所有缓存（别名方法）
   * @returns {Promise<boolean>} 是否清空成功
   */
  async clearAll() {
    return this.clearAllCache();
  }

  /**
   * 关闭数据库连接
   */
  close() {
    this.db.closeDB();
  }
}

export default TileCacheService; 