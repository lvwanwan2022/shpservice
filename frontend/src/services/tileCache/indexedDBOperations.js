 /**
 * IndexedDB 瓦片缓存操作模块
 * 统一管理所有与 IndexedDB 相关的操作
 */

/**
 * 瓦片缓存 IndexedDB 数据库管理类
 */
class TileCacheDB {
    constructor() {
      this.dbName = 'TileCacheDB';
      this.dbVersion = 1;
      this.storeName = 'tiles';
      this.db = null;
    }
  
    /**
     * 初始化并打开数据库
     * @returns {Promise<IDBDatabase>} 数据库实例
     */
    async openDB() {
      return new Promise((resolve, reject) => {
        if (this.db) {
          resolve(this.db);
          return;
        }
  
        const indexedDB = window.indexedDB || 
                         window.mozIndexedDB || 
                         window.webkitIndexedDB || 
                         window.msIndexedDB;
  
        if (!indexedDB) {
          reject(new Error('浏览器不支持 IndexedDB'));
          return;
        }
  
        const request = indexedDB.open(this.dbName, this.dbVersion);
  
        request.onsuccess = (event) => {
          this.db = event.target.result;
          resolve(this.db);
        };
  
        request.onerror = (event) => {
          console.error('瓦片缓存数据库打开失败:', event.target.error);
          reject(event.target.error);
        };
  
        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          
          if (db.objectStoreNames.contains(this.storeName)) {
            db.deleteObjectStore(this.storeName);
          }
  
          const objectStore = db.createObjectStore(this.storeName, {
            keyPath: 'id'
          });
  
          // 创建索引
          objectStore.createIndex('layerId', 'layerId', { unique: false });
          objectStore.createIndex('zoomLevel', 'zoomLevel', { unique: false });
          objectStore.createIndex('tileX', 'tileX', { unique: false });
          objectStore.createIndex('tileY', 'tileY', { unique: false });
          objectStore.createIndex('timestamp', 'timestamp', { unique: false });
          objectStore.createIndex('layerZoom', ['layerId', 'zoomLevel'], { unique: false });
          objectStore.createIndex('coordinate', ['tileX', 'tileY'], { unique: false });
          objectStore.createIndex('fullIndex', ['layerId', 'zoomLevel', 'tileX', 'tileY'], { unique: true });
        };
      });
    }
  
    /**
     * 生成瓦片的唯一ID
     */
    generateTileId(layerId, zoomLevel, tileX, tileY) {
      return `${layerId}_${zoomLevel}_${tileX}_${tileY}`;
    }
  
    /**
     * 解析瓦片ID
     */
    parseTileId(tileId) {
      const parts = tileId.split('_');
      if (parts.length < 4) {
        throw new Error('无效的瓦片ID格式');
      }
      
      return {
        layerId: parts.slice(0, -3).join('_'),
        zoomLevel: parseInt(parts[parts.length - 3]),
        tileX: parseInt(parts[parts.length - 2]),
        tileY: parseInt(parts[parts.length - 1])
      };
    }
  
    /**
     * 获取事务对象
     */
    async getStore(mode = 'readonly') {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], mode);
      return transaction.objectStore(this.storeName);
    }
  
    /**
     * 关闭数据库连接
     */
    closeDB() {
      if (this.db) {
        this.db.close();
        this.db = null;
      }
    }
  
    /**
     * 删除整个数据库
     */
    async deleteDatabase() {
      return new Promise((resolve, reject) => {
        this.closeDB();
        
        const deleteRequest = window.indexedDB.deleteDatabase(this.dbName);
        
        deleteRequest.onsuccess = () => {
          resolve();
        };
        
        deleteRequest.onerror = (event) => {
          console.error('瓦片缓存数据库删除失败:', event.target.error);
          reject(event.target.error);
        };
      });
    }
  }
  
  /**
   * 瓦片缓存服务类
   * 提供瓦片的增删改查功能
   */
  class TileCacheService {
    constructor() {
      this.db = new TileCacheDB();
    }
  
    /**
     * 保存瓦片到缓存
     */
    async saveTile(layerId, zoomLevel, tileX, tileY, data, metadata = {}) {
      try {
        const store = await this.db.getStore('readwrite');
        const id = this.db.generateTileId(layerId, zoomLevel, tileX, tileY);
        
        const tileData = {
          id,
          layerId,
          zoomLevel,
          tileX,
          tileY,
          data,
          timestamp: Date.now(),
          size: data.size || 0,
          contentType: metadata.contentType || 'image/png',
          url: metadata.url || '',
          ...metadata
        };
  
        return new Promise((resolve, reject) => {
          const request = store.put(tileData);
          request.onsuccess = () => resolve(true);
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('保存瓦片失败:', error);
        throw error;
      }
    }
  
    /**
     * 从缓存获取瓦片
     */
    async getTile(layerId, zoomLevel, tileX, tileY) {
      try {
        const store = await this.db.getStore('readonly');
        const id = this.db.generateTileId(layerId, zoomLevel, tileX, tileY);
        
        return new Promise((resolve, reject) => {
          const request = store.get(id);
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('获取瓦片失败:', error);
        return null;
      }
    }
  
    /**
     * 删除指定瓦片
     */
    async deleteTile(layerId, zoomLevel, tileX, tileY) {
      try {
        const store = await this.db.getStore('readwrite');
        const id = this.db.generateTileId(layerId, zoomLevel, tileX, tileY);
        
        return new Promise((resolve, reject) => {
          const request = store.delete(id);
          request.onsuccess = () => resolve(true);
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('删除瓦片失败:', error);
        return false;
      }
    }
  
    /**
     * 获取图层的所有瓦片
     */
    async getLayerTiles(layerId) {
      try {
        const store = await this.db.getStore('readonly');
        const index = store.index('layerId');
        
        return new Promise((resolve, reject) => {
          const request = index.getAll(layerId);
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('获取图层瓦片失败:', error);
        return [];
      }
    }
  
    /**
     * 删除图层的所有瓦片
     */
    async deleteLayerTiles(layerId) {
      try {
        const store = await this.db.getStore('readwrite');
        const index = store.index('layerId');
        
        return new Promise((resolve, reject) => {
          const request = index.openCursor(layerId);
          let deletedCount = 0;
          
          request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
              cursor.delete();
              deletedCount++;
              cursor.continue();
            } else {
              resolve(deletedCount);
            }
          };
          
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('删除图层瓦片失败:', error);
        return 0;
      }
    }
  
    /**
     * 获取所有缓存数据
     */
    async getAllTiles() {
      try {
        const store = await this.db.getStore('readonly');
        
        return new Promise((resolve, reject) => {
          const request = store.getAll();
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('获取所有瓦片失败:', error);
        return [];
      }
    }
  
    /**
     * 清空所有缓存
     */
    async clearAllTiles() {
      try {
        const store = await this.db.getStore('readwrite');
        
        return new Promise((resolve, reject) => {
          const request = store.clear();
          request.onsuccess = () => resolve(true);
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('清空缓存失败:', error);
        return false;
      }
    }
  
    /**
     * 获取缓存统计信息
     */
    async getCacheStats() {
      try {
        const tiles = await this.getAllTiles();
        const layers = new Set();
        let totalSize = 0;
        let lastUpdate = 0;
  
        tiles.forEach(tile => {
          layers.add(tile.layerId);
          totalSize += tile.size || 0;
          lastUpdate = Math.max(lastUpdate, tile.timestamp || 0);
        });
  
        return {
          totalTiles: tiles.length,
          layerCount: layers.size,
          totalSize,
          lastUpdate
        };
      } catch (error) {
        console.error('获取缓存统计失败:', error);
        return {
          totalTiles: 0,
          layerCount: 0,
          totalSize: 0,
          lastUpdate: 0
        };
      }
    }
  
    /**
     * 清理过期瓦片
     */
    async cleanExpiredTiles(maxAge = 7 * 24 * 60 * 60 * 1000) {
      try {
        const store = await this.db.getStore('readwrite');
        const expireTime = Date.now() - maxAge;
        let deletedCount = 0;
        
        return new Promise((resolve, reject) => {
          const request = store.openCursor();
          
          request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
              const tile = cursor.value;
              if (tile.timestamp < expireTime) {
                cursor.delete();
                deletedCount++;
              }
              cursor.continue();
            } else {
              resolve(deletedCount);
            }
          };
          
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('清理过期瓦片失败:', error);
        return 0;
      }
    }
  }
  
  // 全局缓存服务实例（单例模式）
  let globalCacheService = null;
  
  /**
   * 获取全局缓存服务实例
   */
  export function getGlobalCacheService() {
    if (!globalCacheService) {
      globalCacheService = new TileCacheService();
    }
    return globalCacheService;
  }
  
  /**
   * 检查浏览器是否支持IndexedDB
   */
  export function isIndexedDBSupported() {
    return !!(window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB);
  }
  
  export { TileCacheDB, TileCacheService };
  export default TileCacheService;