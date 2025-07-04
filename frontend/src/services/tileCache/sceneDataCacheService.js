/**
 * 场景图层数据缓存服务
 * 负责将场景列表、图层信息等元数据缓存到 IndexedDB
 */

const DB_NAME = 'SceneDataCache';
const DB_VERSION = 1;
const STORE_NAMES = {
  SCENES: 'scenes',
  LAYERS: 'layers',
  METADATA: 'metadata'
};

// 缓存过期时间（1天）
const CACHE_EXPIRE_TIME = 24 * 60 * 60 * 1000;

export class SceneDataCacheService {
  constructor() {
    this.db = null;
    this.initPromise = this.initDB();
  }

  /**
   * 初始化数据库
   */
  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        reject(new Error('Failed to open SceneDataCache database'));
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // 场景存储
        if (!db.objectStoreNames.contains(STORE_NAMES.SCENES)) {
          const scenesStore = db.createObjectStore(STORE_NAMES.SCENES, { keyPath: 'id' });
          scenesStore.createIndex('name', 'name', { unique: false });
        }

        // 图层存储
        if (!db.objectStoreNames.contains(STORE_NAMES.LAYERS)) {
          const layersStore = db.createObjectStore(STORE_NAMES.LAYERS, { keyPath: 'key' });
          layersStore.createIndex('sceneId', 'sceneId', { unique: false });
          layersStore.createIndex('layerId', 'layerId', { unique: false });
        }

        // 元数据存储（时间戳等）
        if (!db.objectStoreNames.contains(STORE_NAMES.METADATA)) {
          db.createObjectStore(STORE_NAMES.METADATA, { keyPath: 'key' });
        }
      };
    });
  }

  /**
   * 确保数据库已初始化
   */
  async ensureDB() {
    if (!this.db) {
      await this.initPromise;
    }
    return this.db;
  }

  /**
   * 获取元数据
   */
  async getMetadata(key) {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.METADATA], 'readonly');
      const store = transaction.objectStore(STORE_NAMES.METADATA);
      const request = store.get(key);

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 设置元数据
   */
  async setMetadata(key, value) {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.METADATA], 'readwrite');
      const store = transaction.objectStore(STORE_NAMES.METADATA);
      const request = store.put({ key, value, timestamp: Date.now() });

      request.onsuccess = () => {
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 检查数据是否过期
   */
  async isDataExpired(key) {
    try {
      const metadata = await this.getMetadata(key);
      if (!metadata || !metadata.timestamp) {
        return true; // 没有数据或没有时间戳，认为过期
      }
      
      const now = Date.now();
      const elapsed = now - metadata.timestamp;
      return elapsed > CACHE_EXPIRE_TIME;
    } catch (error) {
      console.warn('检查数据过期状态失败:', error);
      return true; // 出错时认为过期
    }
  }

  /**
   * 缓存场景列表
   */
  async cacheScenes(scenes) {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.SCENES, STORE_NAMES.METADATA], 'readwrite');
      
      transaction.oncomplete = () => {
        resolve();
      };

      transaction.onerror = () => {
        reject(transaction.error);
      };

      // 清空现有场景数据
      const scenesStore = transaction.objectStore(STORE_NAMES.SCENES);
      scenesStore.clear();

      // 存储新的场景数据
      scenes.forEach(scene => {
        scenesStore.add({
          ...scene,
          cachedAt: Date.now()
        });
      });

      // 更新元数据
      const metadataStore = transaction.objectStore(STORE_NAMES.METADATA);
      metadataStore.put({
        key: 'scenes_last_update',
        value: Date.now(),
        timestamp: Date.now()
      });
    });
  }

  /**
   * 获取缓存的场景列表
   */
  async getCachedScenes() {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.SCENES], 'readonly');
      const store = transaction.objectStore(STORE_NAMES.SCENES);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 缓存场景的图层数据
   */
  async cacheSceneLayers(sceneId, layers) {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.LAYERS, STORE_NAMES.METADATA], 'readwrite');
      
      transaction.oncomplete = () => {
        resolve();
      };

      transaction.onerror = () => {
        reject(transaction.error);
      };

      const layersStore = transaction.objectStore(STORE_NAMES.LAYERS);
      
      // 删除该场景的旧图层数据
      const index = layersStore.index('sceneId');
      const deleteRequest = index.openCursor(IDBKeyRange.only(sceneId));
      
      deleteRequest.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          // 删除完成，添加新数据
          layers.forEach(layer => {
            layersStore.add({
              key: `${sceneId}_${layer.layer_id || layer.id}`,
              sceneId: sceneId,
              layerId: layer.layer_id || layer.id,
              ...layer,
              cachedAt: Date.now()
            });
          });

          // 更新元数据
          const metadataStore = transaction.objectStore(STORE_NAMES.METADATA);
          metadataStore.put({
            key: `scene_${sceneId}_layers_last_update`,
            value: Date.now(),
            timestamp: Date.now()
          });
        }
      };
    });
  }

  /**
   * 获取场景的缓存图层数据
   */
  async getCachedSceneLayers(sceneId) {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.LAYERS], 'readonly');
      const store = transaction.objectStore(STORE_NAMES.LAYERS);
      const index = store.index('sceneId');
      const request = index.getAll(sceneId);

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 缓存图层边界数据
   */
  async cacheLayerBounds(layerId, bounds) {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.METADATA], 'readwrite');
      const store = transaction.objectStore(STORE_NAMES.METADATA);
      
      const request = store.put({
        key: `layer_${layerId}_bounds`,
        value: bounds,
        timestamp: Date.now()
      });

      request.onsuccess = () => {
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 获取图层边界数据
   */
  async getCachedLayerBounds(layerId) {
    const metadata = await this.getMetadata(`layer_${layerId}_bounds`);
    return metadata ? metadata.value : null;
  }

  /**
   * 清空所有缓存
   */
  async clearAllCache() {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.SCENES, STORE_NAMES.LAYERS, STORE_NAMES.METADATA], 'readwrite');
      
      transaction.oncomplete = () => {
        resolve();
      };

      transaction.onerror = () => {
        reject(transaction.error);
      };

      // 清空所有存储
      transaction.objectStore(STORE_NAMES.SCENES).clear();
      transaction.objectStore(STORE_NAMES.LAYERS).clear();
      transaction.objectStore(STORE_NAMES.METADATA).clear();
    });
  }

  /**
   * 获取缓存统计信息
   */
  async getCacheStats() {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAMES.SCENES, STORE_NAMES.LAYERS, STORE_NAMES.METADATA], 'readonly');
      
      let scenesCount = 0;
      let layersCount = 0;
      let lastUpdate = 0;

      // 计算场景数量
      const scenesRequest = transaction.objectStore(STORE_NAMES.SCENES).count();
      scenesRequest.onsuccess = () => {
        scenesCount = scenesRequest.result;
      };

      // 计算图层数量
      const layersRequest = transaction.objectStore(STORE_NAMES.LAYERS).count();
      layersRequest.onsuccess = () => {
        layersCount = layersRequest.result;
      };

      // 获取最后更新时间
      const metadataRequest = transaction.objectStore(STORE_NAMES.METADATA).get('scenes_last_update');
      metadataRequest.onsuccess = () => {
        if (metadataRequest.result) {
          lastUpdate = metadataRequest.result.value;
        }
      };

      transaction.oncomplete = () => {
        resolve({
          scenesCount,
          layersCount,
          lastUpdate,
          isExpired: Date.now() - lastUpdate > CACHE_EXPIRE_TIME
        });
      };

      transaction.onerror = () => {
        reject(transaction.error);
      };
    });
  }
}

// 创建全局实例
let globalSceneDataCacheService = null;

export function getGlobalSceneDataCacheService() {
  if (!globalSceneDataCacheService) {
    globalSceneDataCacheService = new SceneDataCacheService();
  }
  return globalSceneDataCacheService;
} 