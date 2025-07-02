import serverConfig from '@/config/serverConfig';

const { protocol, host, port } = serverConfig.geoserver;
/*eslint-disable*/
const GEOSERVER_BASE_URL = `${protocol}://${host}:${port}`;
/**
 * 简化的缓存服务
 * 替代原来复杂的DataCacheService，提供基本的缓存策略功能
 */

import { getGlobalCacheService } from './indexedDBOperations.js';
import { calculateTileList } from './tileCalculations.js';

export class SimpleCacheService {
  constructor(tileCacheService, gisApi) {
    this.tileCacheService = tileCacheService || getGlobalCacheService();
    this.gisApi = gisApi;
    this.progressCallback = null;
    this.isLoading = false;
    this.shouldStop = false;
  }

  /**
   * 设置进度回调函数
   */
  setProgressCallback(callback) {
    this.progressCallback = callback;
  }

  /**
   * 更新进度
   */
  updateProgress(current, total, message) {
    if (this.progressCallback) {
      const percent = total > 0 ? Math.round((current / total) * 100) : 0;
      this.progressCallback({
        current,
        total,
        percent,
        message,
        error: null
      });
    }
  }

  /**
   * 执行登录缓存策略
   * 预加载所有场景的基础数据
   */
  async executeLoginStrategy() {
    if (this.isLoading) {
      throw new Error('缓存操作正在进行中');
    }

    this.isLoading = true;
    this.shouldStop = false;

    try {
      this.updateProgress(0, 100, '正在获取场景列表...');

      // 1. 获取所有场景
      const scenesResponse = await this.gisApi.getScenes();
      const scenes = scenesResponse.data?.scenes || scenesResponse.data || [];

      if (scenes.length === 0) {
        this.updateProgress(100, 100, '没有找到场景数据');
        return;
      }

      let totalTasks = 0;
      let completedTasks = 0;

      // 2. 计算总任务数
      for (const scene of scenes) {
        if (this.shouldStop) break;
        
        try {
          const sceneResponse = await this.gisApi.getScene(scene.id);
          const layers = sceneResponse.data?.layers || [];
          totalTasks += layers.length;
        } catch (error) {
          console.warn(`获取场景 ${scene.id} 失败:`, error);
        }
      }

      // 3. 处理每个场景的图层
      for (const scene of scenes) {
        if (this.shouldStop) break;

        try {
          this.updateProgress(completedTasks, totalTasks, `正在处理场景: ${scene.name}`);

          const sceneResponse = await this.gisApi.getScene(scene.id);
          const layers = sceneResponse.data?.layers || [];

          for (const layer of layers) {
            if (this.shouldStop) break;

            try {
              await this.cacheLayerData(scene.id, layer, 'login');
              completedTasks++;
              this.updateProgress(completedTasks, totalTasks, `已缓存: ${layer.layer_name}`);
            } catch (error) {
              console.warn(`缓存图层 ${layer.layer_name} 失败:`, error);
              completedTasks++;
            }
          }
        } catch (error) {
          console.warn(`处理场景 ${scene.name} 失败:`, error);
        }
      }

      this.updateProgress(100, 100, '登录缓存策略执行完成');

    } catch (error) {
      console.error('执行登录缓存策略失败:', error);
      if (this.progressCallback) {
        this.progressCallback({
          current: 0,
          total: 100,
          percent: 0,
          message: '缓存失败',
          error: error.message
        });
      }
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 执行场景切换缓存策略
   * 缓存指定场景的所有图层
   */
  async executeSceneSwitchStrategy(sceneId) {
    if (this.isLoading) {
      throw new Error('缓存操作正在进行中');
    }

    this.isLoading = true;
    this.shouldStop = false;

    try {
      this.updateProgress(0, 100, `正在获取场景 ${sceneId} 的数据...`);

      // 1. 获取场景详情
      const sceneResponse = await this.gisApi.getScene(sceneId);
      const layers = sceneResponse.data?.layers || [];

      if (layers.length === 0) {
        this.updateProgress(100, 100, '该场景没有图层数据');
        return;
      }

      let completedLayers = 0;
      const totalLayers = layers.length;

      // 2. 缓存每个图层
      for (const layer of layers) {
        if (this.shouldStop) break;

        try {
          this.updateProgress(completedLayers, totalLayers, `正在缓存图层: ${layer.layer_name}`);
          await this.cacheLayerData(sceneId, layer, 'scene');
          completedLayers++;
          this.updateProgress(completedLayers, totalLayers, `已缓存: ${layer.layer_name}`);
        } catch (error) {
          console.warn(`缓存图层 ${layer.layer_name} 失败:`, error);
          completedLayers++;
        }
      }

      this.updateProgress(100, 100, '场景缓存策略执行完成');

    } catch (error) {
      console.error('执行场景缓存策略失败:', error);
      if (this.progressCallback) {
        this.progressCallback({
          current: 0,
          total: 100,
          percent: 0,
          message: '缓存失败',
          error: error.message
        });
      }
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 缓存单个图层的数据
   */
  async cacheLayerData(sceneId, layer, strategy = 'scene', options = {}) {
    try {
      // 1. 获取图层边界
      let bounds;
      if (options.bounds) {
        bounds = {
          west: options.bounds[0],
          south: options.bounds[1],
          east: options.bounds[2],
          north: options.bounds[3]
        };
      } else {
        const boundsResponse = await this.gisApi.getSceneLayerBounds(layer.scene_layer_id);
        const bbox = boundsResponse.data?.bbox;
        if (!bbox) {
          console.warn(`图层 ${layer.layer_name} 没有有效的边界数据`);
          return;
        }
        bounds = {
          west: bbox.minx,
          south: bbox.miny,
          east: bbox.maxx,
          north: bbox.maxy
        };
      }
  
      // 2. 缩放级别
      const zoomLevels = options.zoomLevels || (strategy === 'login'
        ? { min: 8, max: 12 }
        : { min: 10, max: 14 });
  
      // 3. 计算瓦片
      const tileList = calculateTileList(bounds, zoomLevels);
      const maxTiles = options.maxTiles || (strategy === 'login' ? 100 : 500);
      const limitedTileList = tileList.slice(0, maxTiles);
  
      // 4. 缓存
      const layerId = layer.layerId || `${sceneId}_${layer.layer_id}`;
      // 你需要传入 urlTemplate
      console.log(layer);
      const urlTemplate = options.urlTemplate || layer.originalLayer.wms_url || layer.originalLayer.mvt_url
      ;
      if (!urlTemplate) throw new Error('缺少瓦片URL模板');
      await this.fetchAndCacheTiles(layerId, limitedTileList, urlTemplate, options.onProgress);

    } catch (error) {
      console.error(`缓存图层数据失败:`, error);
      throw error;
    }
  }

  
  async fetchAndCacheTiles(layerId, tileList, urlTemplate, onProgress) {
    for (let i = 0; i < tileList.length; i++) {
      if (this.shouldStop) break;
      const { z, x, y } = tileList[i];
      try {
        const existing = await this.tileCacheService.getTile(layerId, z, x, y);
        if (existing) {
          if (onProgress) onProgress(i + 1, tileList.length);
          continue;
        }
        // 生成真实URL
        let url = urlTemplate
          .replace('{z}', z)
          .replace('{x}', x)
          .replace('{y}', y);
          // 替换 localhost:8083
      //url = url.replace('localhost:8083', GEOSERVER_BASE_URL.replace(/^https?:\/\//, ''));
      url = url.replace('http://localhost:8083', '');
      url = url.replace('.pbf', '');
      // // 补全协议
      // if (!/^https?:\/\//.test(url)) {
      //   url = GEOSERVER_BASE_URL.replace(/\/$/, '') + (url.startsWith('/') ? url : '/' + url);
      // }
      //console.log(GEOSERVER_BASE_URL);
        // 请求瓦片
        const response = await fetch(url);
        console.log(response);
        if (!response.ok) throw new Error(`请求失败: ${url}`);
        const blob = await response.blob();
        await this.tileCacheService.saveTile(layerId, z, x, y, blob, {
          contentType: blob.type,
          url
        });
      } catch (error) {
        console.warn(`拉取瓦片 ${z}/${x}/${y} 失败:`, error);
      }
      if (onProgress) onProgress(i + 1, tileList.length);
    }
  }



  /**
   * 停止加载
   */
  stopLoading() {
    this.shouldStop = true;
    this.isLoading = false;
  }

  /**
   * 检查是否正在加载
   */
  isLoading() {
    return this.isLoading;
  }
}

export default SimpleCacheService; 