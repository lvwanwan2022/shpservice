<template>
  <div class="tile-load-test">
    <div class="test-header">
      <h1>瓦片加载函数测试页面</h1>
      <div class="test-controls">
        <button @click="initMap" :disabled="mapInitialized">初始化地图</button>
        <button @click="clearCache" :disabled="!mapInitialized">清空缓存</button>
        <button @click="checkCacheStats" :disabled="!mapInitialized">查看缓存统计</button>
        <button @click="toggleOfflineMode">{{ offlineMode ? '关闭离线模式' : '开启离线模式' }}</button>
      </div>
      <div class="test-info">
        <p>地图状态: {{ mapInitialized ? '已初始化' : '未初始化' }}</p>
        <p>离线模式: {{ offlineMode ? '开启' : '关闭' }}</p>
        <p>缓存统计: {{ cacheStats }}</p>
      </div>
    </div>
    
    <div class="map-container">
      <div id="test-map" ref="mapContainer"></div>
    </div>
    
    <div class="test-logs">
      <h3>测试日志</h3>
      <div class="log-container" ref="logContainer">
        <div v-for="(log, index) in logs" :key="index" :class="['log-item', log.type]">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
      <button @click="clearLogs">清空日志</button>
    </div>
  </div>
</template>

<script>
import 'ol/ol.css';
import { Map, View } from 'ol';
import { Tile as TileLayer, VectorTile as VectorTileLayer } from 'ol/layer';
import { XYZ, VectorTile as VectorTileSource } from 'ol/source';
import { fromLonLat } from 'ol/proj';
import { MVT } from 'ol/format';
import { Style, Stroke, Fill, Circle } from 'ol/style';

import { 
  createWmtsTileLoadFunction, 
  createMvtTileLoadFunction
} from '@/services/tileCache/tileLoadFunctions.js';
import { getGlobalCacheService } from '@/services/tileCache/indexedDBOperations.js';

export default {
  name: 'TileLoadTestView',
  data() {
    return {
      map: null,
      mapInitialized: false,
      offlineMode: false,
      cacheStats: '未获取',
      logs: [],
      tileCacheService: null,
      originalFetch: null
    };
  },
  async mounted() {
    // 初始化缓存服务
    this.tileCacheService = getGlobalCacheService();
    await this.tileCacheService.db.openDB();
    
    // 保存原始的fetch函数
    this.originalFetch = window.fetch;
    
    this.addLog('info', '页面加载完成，缓存服务已初始化');
  },
  methods: {
    async initMap() {
      try {
        this.addLog('info', '开始初始化地图...');
        
        // 创建WMTS瓦片加载函数
        const wmtsTileLoadFunction = createWmtsTileLoadFunction({
          layerId: 'gaode_base',
          tileCacheService: this.tileCacheService
        });
        
        // 创建高德地图底图源
        const gaodeSource = new XYZ({
          url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
          crossOrigin: 'anonymous',
          maxZoom: 18,
          minZoom: 3
        });
        
        // 设置自定义瓦片加载函数
        gaodeSource.setTileLoadFunction(wmtsTileLoadFunction);
        
        // 创建底图图层
        const baseLayer = new TileLayer({
          source: gaodeSource
        });
        
        // 创建MVT瓦片加载函数
        const mvtTileLoadFunction = createMvtTileLoadFunction({
          layerId: 'test_mvt_layer',
          tileCacheService: this.tileCacheService
        });
        
        // 创建MVT图层源（使用测试数据）
        const mvtSource = new VectorTileSource({
          url: 'http://172.16.118.124:3000/vector_0b80a9e0/{z}/{x}/{y}',
          format: new MVT(),
          tileLoadFunction: mvtTileLoadFunction
        });
        
        // 创建MVT图层
        const mvtLayer = new VectorTileLayer({
          source: mvtSource,
          style: new Style({
            stroke: new Stroke({
              color: '#FF0000',
              width: 2
            }),
            fill: new Fill({
              color: 'rgba(255, 0, 0, 0.3)'
            }),
            image: new Circle({
              radius: 5,
              fill: new Fill({
                color: '#FF0000'
              })
            })
          })
        });
        
        // 创建地图
        this.map = new Map({
          target: 'test-map',
          layers: [baseLayer, mvtLayer],
          view: new View({
            center: fromLonLat([106.28, 31.61]), // 数据范围中心
            zoom: 12
          })
        });
        
        this.mapInitialized = true;
        this.addLog('success', '地图初始化成功');
        
        // 添加地图事件监听
        this.map.on('moveend', () => {
          this.addLog('info', `地图视图更新: 中心点 ${this.map.getView().getCenter()}, 缩放级别 ${this.map.getView().getZoom()}`);
        });
        
      } catch (error) {
        this.addLog('error', `地图初始化失败: ${error.message}`);
        console.error('地图初始化失败:', error);
      }
    },
    
    async clearCache() {
      try {
        await this.tileCacheService.clearAllTiles();
        this.addLog('success', '缓存已清空');
        await this.checkCacheStats();
      } catch (error) {
        this.addLog('error', `清空缓存失败: ${error.message}`);
      }
    },
    
    async checkCacheStats() {
      try {
        const stats = await this.tileCacheService.getCacheStats();
        this.cacheStats = `总瓦片: ${stats.totalTiles}, 图层数: ${stats.layerCount}, 总大小: ${this.formatBytes(stats.totalSize)}`;
        this.addLog('info', `缓存统计: ${this.cacheStats}`);
      } catch (error) {
        this.addLog('error', `获取缓存统计失败: ${error.message}`);
      }
    },
    
    toggleOfflineMode() {
      this.offlineMode = !this.offlineMode;
      
      if (this.offlineMode) {
        // 开启离线模式 - 拦截所有网络请求
        window.fetch = (...args) => {
          this.addLog('warning', `离线模式: 拦截网络请求 ${args[0]}`);
          return Promise.reject(new Error('离线模式: 网络请求被拦截'));
        };
        this.addLog('warning', '离线模式已开启，所有网络请求将被拦截');
      } else {
        // 关闭离线模式 - 恢复原始fetch
        window.fetch = this.originalFetch;
        this.addLog('info', '离线模式已关闭，网络请求已恢复');
      }
    },
    
    addLog(type, message) {
      const now = new Date();
      const time = now.toLocaleTimeString();
      this.logs.push({
        type,
        time,
        message
      });
      
      // 保持最多100条日志
      if (this.logs.length > 100) {
        this.logs.shift();
      }
      
      // 自动滚动到底部
      this.$nextTick(() => {
        const logContainer = this.$refs.logContainer;
        if (logContainer) {
          logContainer.scrollTop = logContainer.scrollHeight;
        }
      });
    },
    
    clearLogs() {
      this.logs = [];
    },
    
    formatBytes(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  },
  
  beforeUnmount() {
    // 恢复原始fetch函数
    if (this.originalFetch) {
      window.fetch = this.originalFetch;
    }
    
    // 销毁地图
    if (this.map) {
      this.map.setTarget(null);
      this.map = null;
    }
  }
};
</script>

<style scoped>
.tile-load-test {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.test-header {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.test-header h1 {
  margin: 0 0 20px 0;
  color: #333;
}

.test-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.test-controls button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.test-controls button:hover:not(:disabled) {
  background: #0056b3;
}

.test-controls button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.test-info {
  font-size: 14px;
  color: #666;
}

.test-info p {
  margin: 5px 0;
}

.map-container {
  flex: 1;
  min-height: 400px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

#test-map {
  width: 100%;
  height: 100%;
}

.test-logs {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  max-height: 300px;
  display: flex;
  flex-direction: column;
}

.test-logs h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  background: white;
  font-family: monospace;
  font-size: 12px;
  margin-bottom: 10px;
}

.log-item {
  margin-bottom: 5px;
  padding: 2px 0;
  border-bottom: 1px solid #eee;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #666;
  margin-right: 10px;
}

.log-message {
  word-break: break-all;
}

.log-item.info .log-message {
  color: #007bff;
}

.log-item.success .log-message {
  color: #28a745;
}

.log-item.warning .log-message {
  color: #ffc107;
}

.log-item.error .log-message {
  color: #dc3545;
}

.test-logs button {
  align-self: flex-start;
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  background: #6c757d;
  color: white;
  cursor: pointer;
  font-size: 12px;
}

.test-logs button:hover {
  background: #545b62;
}
</style> 