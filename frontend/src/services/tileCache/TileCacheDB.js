/**
 * 瓦片缓存 IndexedDB 数据库管理类
 * 用于存储和管理地图瓦片缓存数据
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

      // 兼容浏览器
      const indexedDB = window.indexedDB || 
                       window.mozIndexedDB || 
                       window.webkitIndexedDB || 
                       window.msIndexedDB;

      if (!indexedDB) {
        reject(new Error('浏览器不支持 IndexedDB'));
        return;
      }

      const request = indexedDB.open(this.dbName, this.dbVersion);

      // 数据库打开成功
      request.onsuccess = (event) => {
        this.db = event.target.result;
        console.log('瓦片缓存数据库打开成功');
        resolve(this.db);
      };

      // 数据库打开失败
      request.onerror = (event) => {
        console.error('瓦片缓存数据库打开失败:', event.target.error);
        reject(event.target.error);
      };

      // 数据库版本升级或首次创建
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // 删除旧的存储对象（如果存在）
        if (db.objectStoreNames.contains(this.storeName)) {
          db.deleteObjectStore(this.storeName);
        }

        // 创建存储对象
        const objectStore = db.createObjectStore(this.storeName, {
          keyPath: 'id' // 使用复合主键：layerId_zoomLevel_tileX_tileY
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

        console.log('瓦片缓存数据库结构创建成功');
      };
    });
  }

  /**
   * 生成瓦片的唯一ID
   * @param {string} layerId 图层ID
   * @param {number} zoomLevel 缩放级别
   * @param {number} tileX 瓦片X坐标
   * @param {number} tileY 瓦片Y坐标
   * @returns {string} 瓦片唯一ID
   */
  generateTileId(layerId, zoomLevel, tileX, tileY) {
    return `${layerId}_${zoomLevel}_${tileX}_${tileY}`;
  }

  /**
   * 解析瓦片ID
   * @param {string} tileId 瓦片ID
   * @returns {object} 解析后的瓦片信息
   */
  parseTileId(tileId) {
    const parts = tileId.split('_');
    if (parts.length < 4) {
      throw new Error('无效的瓦片ID格式');
    }
    
    return {
      layerId: parts.slice(0, -3).join('_'), // 处理layerId中可能包含下划线的情况
      zoomLevel: parseInt(parts[parts.length - 3]),
      tileX: parseInt(parts[parts.length - 2]),
      tileY: parseInt(parts[parts.length - 1])
    };
  }

  /**
   * 获取事务对象
   * @param {string} mode 事务模式：'readonly' 或 'readwrite'
   * @returns {Promise<IDBObjectStore>} 存储对象
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
      console.log('瓦片缓存数据库已关闭');
    }
  }

  /**
   * 删除整个数据库
   * @returns {Promise<void>}
   */
  async deleteDatabase() {
    return new Promise((resolve, reject) => {
      this.closeDB();
      
      const deleteRequest = window.indexedDB.deleteDatabase(this.dbName);
      
      deleteRequest.onsuccess = () => {
        console.log('瓦片缓存数据库删除成功');
        resolve();
      };
      
      deleteRequest.onerror = (event) => {
        console.error('瓦片缓存数据库删除失败:', event.target.error);
        reject(event.target.error);
      };
    });
  }
}

export default TileCacheDB; 