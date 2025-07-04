<template>
  <div class="cache-manager">
    <!-- 工具栏 -->
    <div class="cache-toolbar">
      <div class="toolbar-left">
        <el-button type="primary" size="small" @click="refreshCacheData">
          <i class="el-icon-refresh"></i> 刷新
        </el-button>
        <el-button type="warning" size="small" @click="clearAllCache">
          <i class="el-icon-delete"></i> 清空
        </el-button>
        <el-button type="success" size="small" @click="exportCacheData">
          <i class="el-icon-download"></i> 导出
        </el-button>
        <el-upload
          :show-file-list="false"
          :before-upload="importCacheData"
          accept=".json"
          style="display: inline-block;"
        >
          <el-button type="info" size="small">
            <i class="el-icon-upload2"></i> 导入
          </el-button>
        </el-upload>
        
      </div>
      <div class="toolbar-right">
        <el-select
          v-model="selectedSceneFilter"
          placeholder="按场景筛选"
          clearable
          size="small"
          style="width: 160px; margin-right: 8px;"
          @change="filterCacheData"
        >
          <el-option
            v-for="scene in sceneList"
            :key="scene.id"
            :label="scene.name"
            :value="scene.id"
          />
        </el-select>
        <el-input
          v-model="cacheSearchText"
          placeholder="搜索场景名或图层名"
          size="small"
          style="width: 200px"
          @input="filterCacheData"
        >
          <template #prefix>
            <i class="el-icon-search"></i>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="cache-stats-compact">
      <div class="stat-item">
        <span class="stat-label">瓦片数</span>
        <span class="stat-value">{{ cacheStats.totalTiles }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">总大小</span>
        <span class="stat-value">{{ formatFileSize(cacheStats.totalSize) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">图层数</span>
        <span class="stat-value">{{ cacheStats.layerCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">更新时间</span>
        <span class="stat-value">{{ formatTimeAgo(cacheStats.lastUpdate) }}</span>
      </div>
    </div>

    <!-- 缓存数据内容 -->
    <div class="cache-content">
      <!-- 图层缓存表格 -->
      <div class="cache-layers">
        <el-table 
          :data="filteredCacheData" 
          size="small"
          stripe
          :row-key="row => row.sceneId + '_' + row.layerId"
          :expand-row-keys="expandedRowKeys"
          @expand-change="handleExpandChange"
        >
          <!-- 展开列 -->
          <el-table-column type="expand" width="40">
            <template #default="{ row }">
              <div class="expanded-content">
                <div class="tiles-header">
                  <h4>瓦片详情 ({{ row.tiles.length }} 个)</h4>
                </div>
                <el-table 
                  :data="row.tiles" 
                  size="small" 
                  max-height="300"
                  stripe
                >
                  <el-table-column prop="zoomLevel" label="缩放级别" width="80" align="center" />
                  <el-table-column prop="tileX" label="X坐标" width="80" align="center" />
                  <el-table-column prop="tileY" label="Y坐标" width="80" align="center" />
                  <el-table-column label="大小" width="80" align="center">
                    <template #default="scope">
                      {{ formatFileSize(scope.row.size) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="类型" width="100" align="center">
                    <template #default="scope">
                      <el-tag size="small">{{ scope.row.contentType || 'image/png' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="创建时间" width="140" align="center">
                    <template #default="scope">
                      {{ new Date(scope.row.timestamp).toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="130" align="center">
                    <template #default="scope">
                      <el-button 
                        type="primary" 
                        size="small" 
                        @click="previewTile(scope.row)"
                      >
                        预览
                      </el-button>
                      <el-button 
                        type="danger" 
                        size="small" 
                        @click="deleteTile(scope.row)"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </el-table-column>

          <!-- 场景名称 -->
          <el-table-column prop="sceneName" label="场景" width="120" show-overflow-tooltip />
          
          <!-- 图层名称 -->
          <el-table-column prop="layerName" label="图层名称" min-width="150" show-overflow-tooltip />
          <el-table-column  label="服务类型" min-width="150">
            <template #default="{ row }">
    <span>{{ row.originalLayer && row.originalLayer.service_type ? row.originalLayer.service_type : row.layerType }}</span>
  </template>
  </el-table-column>
          
          <!-- 缓存状态 -->
          <el-table-column label="缓存状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag 
                size="small" 
                :type="row.tiles && row.tiles.length > 0 ? 'success' : 'info'"
              >
                {{ row.tiles && row.tiles.length > 0 ? '已缓存' : '未缓存' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <!-- 瓦片数量 -->
          <el-table-column label="瓦片数" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.tiles && row.tiles.length > 0">{{ row.tiles.length }}</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>
          
          <!-- 缓存大小 -->
          <el-table-column label="大小" width="90" align="center">
            <template #default="{ row }">
              <span v-if="row.totalSize > 0">{{ formatFileSize(row.totalSize) }}</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>
          
          <!-- 缩放层级 -->
          <el-table-column label="层级" width="120" align="center">
            <template #default="{ row }">
              <span class="zoom-levels">
                <template v-if="Array.isArray(row.zoomLevels) && row.zoomLevels.length > 0">
                  {{ row.zoomLevels.length === 1 ? row.zoomLevels[0] : `${row.zoomLevels[0]}-${row.zoomLevels[row.zoomLevels.length - 1]}` }}
                </template>
                <template v-else>-</template>
              </span>
            </template>
          </el-table-column>
          
          <!-- 边界框 -->
          <el-table-column label="边界框" min-width="180" align="center">
            <template #default="{ row }">
              <span v-if="Array.isArray(row.bounds)">
                {{ row.bounds.map(n => n.toFixed(6)).join(', ') }}
              </span>
              <span v-else class="no-data">{{ row.bounds }}</span>
            </template>
          </el-table-column>
          
          <!-- 操作 -->
          <el-table-column label="操作" width="200" align="center" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click="startLayerCache(row)"
                title="缓存图层"
              >
                <i class="el-icon-download"></i> 缓存
              </el-button>              
              <el-button 
                type="danger" 
                size="small" 
                @click="deleteLayerCache(row)"
                :disabled="!row.tiles || row.tiles.length === 0"
                title="删除缓存"
              >
                <i class="el-icon-delete"></i> 删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredCacheData.length === 0" class="empty-cache">
        <i class="el-icon-box"></i>
        <p>暂无缓存数据</p>
        
      </div>
    </div>



    <!-- 缓存配置对话框 -->
    <el-dialog 
      title="图层缓存配置" 
      v-model="cacheConfigVisible" 
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      custom-class="cache-config-dialog"
      destroy-on-close
      @opened="onCacheConfigDialogOpened"
    >
      <div class="cache-config-content">
        <div class="cache-config-panel">
          <div class="config-left">
            <h4>{{ currentCacheLayer.layerName }}</h4>
            <div class="config-form">
              <el-form label-width="120px" size="small">
                <el-form-item label="当前缩放级别">
                  <span>{{ currentMapZoom }}</span>
                </el-form-item>
                <el-form-item label="缓存状态">
                  <span :class="{ 'cache-enabled': currentLayerCacheEnabled, 'cache-disabled': !currentLayerCacheEnabled }">
                    {{ currentLayerCacheEnabled ? '已开启' : '已关闭' }}
                  </span>
                </el-form-item>
                <div class="config-actions">
                  <el-button
                    :type="currentLayerCacheEnabled ? 'success' : 'warning'"
                    @click="toggleLayerCache"
                    icon="el-icon-refresh"
                  >
                    {{ currentLayerCacheEnabled ? '关闭缓存' : '开启缓存' }}
                  </el-button>
                  <el-button @click="cacheConfigVisible = false">关闭</el-button>
                </div>
              </el-form>
            </div>
          </div>
          <div class="config-right">
            <div id="cache-config-map"></div>
          </div>
        </div>
      </div>
    </el-dialog>
    
  </div>
  <el-dialog v-model="tilePreviewVisible" title="瓦片预览" width="400px">
  <div v-if="tileImageUrl">
    <img :src="tileImageUrl" style="max-width:100%;" />
  </div>
  <div v-else>
    <span>该瓦片不是图片类型或无法预览。</span>
  </div>
</el-dialog>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import gisApi from '@/api/gis.js';
import { formatFileSize, formatTimeAgo, SimpleCacheService, TileCacheService } from '@/services/tileCache';

// OpenLayers导入
import { Map, View, Feature } from 'ol';
import { Tile as TileLayer, VectorTile as VectorTileLayer, Vector as VectorLayer } from 'ol/layer';
import { XYZ, VectorTile as VectorTileSource, Vector as VectorSource } from 'ol/source';
import { Polygon } from 'ol/geom';
import { Style, Stroke, Fill, Circle } from 'ol/style';
import { fromLonLat } from 'ol/proj';
import { MVT } from 'ol/format';
import TileDebug from 'ol/source/TileDebug.js';
import { 
  createWmtsTileLoadFunction, 
  createMvtTileLoadFunction
} from '@/services/tileCache/tileLoadFunctions.js';


// 引入GCJ02坐标系
//import gcj02Mecator from '@/utils/GCJ02';

export default {
  name: 'CacheManagerView',
  setup() {
    const selectedSceneFilter = ref('');
    const sceneList = ref([]);
    const cacheSearchText = ref('');
    const expandedRowKeys = ref([]);
    
    const cacheProgressVisible = ref(false);
    const cacheOperationRunning = ref(false);
    const cacheProgress = reactive({
      current: 0,
      total: 0,
      percent: 0,
      message: '准备中...',
      status: ''
    });
    
    const tilePreviewVisible = ref(false);
    const currentTile = ref(null);
    const tileImageUrl = ref('');

    const cacheData = ref([]);
    const cacheStats = reactive({
      totalTiles: 0,
      totalSize: 0,
      layerCount: 0,
      lastUpdate: Date.now()
    });



    // 缓存配置相关
    const cacheConfigVisible = ref(false);
    const currentCacheLayer = ref({});
    let configMap = null;

    
    const cacheConfig = reactive({
      minZoom: 10,
      maxZoom: 15,
      useDefaultBounds: true,
      selectedBounds: null
    });
    
    const currentMapZoom = ref(10);
    const currentLayerCacheEnabled = ref(true); // 当前图层的缓存状态
    
    // 开启图层缓存
    const enableLayerCache = () => {
      currentLayerCacheEnabled.value = true;
      ElMessage.success(`图层 "${currentCacheLayer.value.layerName}" 缓存已开启`);
      console.log(`图层 ${currentCacheLayer.value.layerId} 缓存已开启，enableCacheStorage = true`);
    };
    
    // 关闭图层缓存
    const disableLayerCache = () => {
      currentLayerCacheEnabled.value = false;
      ElMessage.warning(`图层 "${currentCacheLayer.value.layerName}" 缓存已关闭`);
      console.log(`图层 ${currentCacheLayer.value.layerId} 缓存已关闭，enableCacheStorage = false`);
    };
// 四个常用底图（可根据你OpenLayers页面实际key和名称调整）
const baseMaps = [
          { 
            key: 'gaode', 
            name: '高德地图', 
            type: 'raster',
            url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
          },
          { 
            key: 'gaodeSatellite', 
            name: '高德卫星', 
            type: 'raster',
            url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
          },
          { 
            key: 'osm', 
            name: 'OpenStreetMap', 
            type: 'raster',
            url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
          },
          { 
            key: 'esriSatellite', 
            name: 'Esri卫星', 
            type: 'raster',
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
          },
        ];
        let baseLayer;
        let mvtLayer = null;
    // 缓存服务实例
    let tileCacheService = null;
    let dataCacheService = null;

    const initCacheService = async () => {
      try {
        tileCacheService = new TileCacheService({
          maxCacheSize: 500 * 1024 * 1024, // 500MB
          maxCacheAge: 7 * 24 * 60 * 60 * 1000 // 7天
        });

        dataCacheService = new SimpleCacheService(tileCacheService, gisApi);
        
        // 设置进度回调
        dataCacheService.setProgressCallback((progress) => {
          cacheProgress.current = progress.current;
          cacheProgress.total = progress.total;
          cacheProgress.percent = progress.percent;
          cacheProgress.message = progress.message;
        });

        //console.log('缓存服务初始化成功');
        
        await loadScenes();
        await refreshCacheData();
      } catch (error) {
        console.error('初始化缓存服务失败:', error);
        ElMessage.error('初始化缓存服务失败: ' + error.message);
      }
    };

    const loadScenes = async () => {
      try {
        const response = await gisApi.getScenes();
        sceneList.value = response.data?.scenes || response.data || [];
        ////console.log('加载的场景列表:', sceneList.value);
      } catch (error) {
        //console.error('加载场景列表失败:', error);
        ElMessage.error('加载场景列表失败: ' + error.message);
        
      }
    };

    const refreshCacheData = async () => {
      if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        //console.log('开始读取IndexedDB缓存数据...');
        
        // 1. 先加载用户的所有场景和图层
        await loadScenesAndLayers();
        
        // 2. 获取所有缓存数据
        const allTiles = await tileCacheService.getAllTiles();
        //console.log('获取到的瓦片数据:', allTiles);
        
        //console.log('缓存中的layerId列表:', cacheLayerIds);
        
        // 3. 按图层ID分组缓存数据
        const layerGroups = {};
        let totalTiles = 0;
        let totalSize = 0;
        let lastUpdate = 0;

        allTiles.forEach(tile => {
          if (!layerGroups[tile.layerId]) {
            layerGroups[tile.layerId] = {
              tiles: [],
              totalSize: 0,
              zoomLevels: new Set()
            };
          }
          
          layerGroups[tile.layerId].tiles.push(tile);
          layerGroups[tile.layerId].totalSize += tile.size || 0;
          layerGroups[tile.layerId].zoomLevels.add(tile.zoomLevel);
          
          totalTiles++;
          totalSize += tile.size || 0;
          
          if (tile.timestamp > lastUpdate) {
            lastUpdate = tile.timestamp;
          }
        });

       
        //console.log('场景图层的layerId列表:', sceneLayerIds);
        //console.log('layerId匹配情况:');
        
        // 4. 将缓存数据合并到场景图层数据中
        cacheData.value.forEach(layer => {
          // 统一使用layer_id进行匹配
          let cachedData = null;
          
          // 方式1: 直接使用layerId匹配（现在就是layer_id）
          cachedData = layerGroups[layer.layerId];
          
          // 方式2: 如果直接匹配失败，尝试使用sceneLayerId匹配
          if (!cachedData && layer.sceneLayerId) {
            cachedData = layerGroups[layer.sceneLayerId.toString()];
          }
          
          // 方式3: 尝试匹配martin-vector格式（保留兼容性）
          if (!cachedData && layer.sceneLayerId) {
            // 尝试martin-vector-{layerId}-{layerName}格式
            for (const cacheLayerId in layerGroups) {
              if (cacheLayerId.startsWith('martin-vector-') && 
                  cacheLayerId.includes(layer.sceneLayerId.toString())) {
                cachedData = layerGroups[cacheLayerId];
                break;
              }
            }
          }
          
          // 方式4: 尝试旧格式兼容（场景ID_图层ID格式）
          if (!cachedData) {
            for (const cacheLayerId in layerGroups) {
              if (cacheLayerId.includes('_') && cacheLayerId.endsWith('_' + layer.layerId)) {
                cachedData = layerGroups[cacheLayerId];
                break;
              }
            }
          }
          
          if (cachedData) {
            //console.log(`✓ 匹配成功: ${layer.layerId} -> ${matchedLayerId} (${cachedData.tiles.length} 个瓦片)`);
            layer.tiles = cachedData.tiles;
            layer.totalSize = cachedData.totalSize;
            const levels = Array.from(cachedData.zoomLevels).sort((a, b) => a - b);
            layer.zoomLevels = levels; // 保持为数组格式
          } else {
            //console.log(`✗ 未匹配: ${layer.layerId} (sceneLayerId: ${layer.sceneLayerId})`);
            layer.tiles = [];
            layer.totalSize = 0;
            layer.zoomLevels = []; // 保持为数组格式
          }
        });

        // 5. 更新统计信息
        cacheStats.totalTiles = totalTiles;
        cacheStats.totalSize = totalSize;
        cacheStats.layerCount = Object.keys(layerGroups).length;
        cacheStats.lastUpdate = lastUpdate || Date.now();

        //console.log('缓存数据统计:', cacheStats);
        
      } catch (error) {
        console.error('读取缓存数据失败:', error);
        ElMessage.error('读取缓存数据失败: ' + error.message);
      }
    };
    
    // 加载用户的场景和图层
    const loadScenesAndLayers = async () => {
      try {
        // 初始化为空数组
        cacheData.value = [];
        
        // 1. 先获取所有场景
        const scenesResponse = await gisApi.getScenes();
        const scenes = scenesResponse.data?.scenes || scenesResponse.data || [];
        
        // 2. 增加底图场景
        
        
        // 默认中国全图范围
        const defaultBaseMapBounds = [73.0, 3.0, 135.0, 53.0];
        const baseMapLayers = baseMaps.map((bm) => ({
          layerId: bm.key, // 直接使用底图的key作为layer_id
          sceneId: 'basemap',
          sceneName: '底图',
          layerName: bm.name,
          layerType: bm.type,
          minZoom: 2,
          maxZoom: 18,
          bounds: defaultBaseMapBounds,
          sceneLayerId: bm.key,
          tiles: [],
          totalSize: 0,
          zoomLevels: [],
          originalLayer: bm
        }));
        // 3. 普通场景
        if (scenes.length === 0) {
          cacheData.value = baseMapLayers;
          return;
        }
        // 4. 为每个场景获取其图层
        const allLayersData = [...baseMapLayers];
        for (const scene of scenes) {
          try {
            const sceneResponse = await gisApi.getScene(scene.id);
            const layers = sceneResponse.data?.layers || [];
            layers.forEach(layer => {
              // 统一使用 layer_id 作为缓存key
              const layerId = layer.layer_id || layer.id || layer.scene_layer_id;
              allLayersData.push({
                layerId: layerId,
                sceneId: scene.id,
                sceneName: scene.name,
                layerName: layer.layer_name || layer.name || `图层_${layerId}`,
                layerType: determineLayerType(layer),
                minZoom: layer.min_zoom || 0,
                maxZoom: layer.max_zoom || 18,
                bounds: '获取中', // 初始为"获取中"
                sceneLayerId: layer.scene_layer_id || layer.id || layer.layer_id, // 用于后续查边界
                tiles: [],
                totalSize: 0,
                zoomLevels: [],
                originalLayer: layer
              });
            });
          } catch (error) {
            console.warn(`获取场景 ${scene.name} 的图层失败:`, error);
            // 即使某个场景失败，也继续处理其他场景
          }
        }
        cacheData.value = allLayersData;
        // 5. 异步获取每个图层的真实边界框（普通场景图层，底图不需要）
        for (const layer of cacheData.value) {
          if (layer.sceneId === 'basemap') {
            // 底图直接用默认边界
            layer.bounds = defaultBaseMapBounds;
            continue;
          }
          if (!layer.sceneLayerId) {
            layer.bounds = '-';
            continue;
          }
          try {
            const boundsResp = await gisApi.getSceneLayerBounds(layer.sceneLayerId);
            let bounds = null;
            if (boundsResp.data && boundsResp.data.bbox) {
              bounds = boundsResp.data.bbox;
            } else if (boundsResp.bbox) {
              bounds = boundsResp.bbox;
            } else if (Array.isArray(boundsResp) && boundsResp.length === 4) {
              bounds = boundsResp;
            }
            if (bounds && Array.isArray(bounds) && bounds.length === 4) {
              layer.bounds = bounds;
            } else if (bounds && typeof bounds === 'object' && 'minx' in bounds) {
              layer.bounds = [bounds.minx, bounds.miny, bounds.maxx, bounds.maxy];
            } else {
              layer.bounds = '-';
            }
          } catch (e) {
            layer.bounds = '-';
          }
        }
      } catch (error) {
        console.error('加载场景和图层失败:', error);
        ElMessage.error('加载场景和图层失败: ' + error.message);
        
        // 出错时使用模拟数据作为备选
        //console.log('使用模拟数据作为备选...');
        const fallbackData = await generateScenesAndLayers();
        cacheData.value = fallbackData;
      }
    };
    
    // 确定图层类型
    const determineLayerType = (layer) => {
      // 根据图层属性判断类型
      if (layer.file_type) {
        const fileType = layer.file_type.toLowerCase();
        if (fileType.includes('shp') || fileType.includes('geojson') || fileType.includes('dxf')) {
          return 'vector';
        } else if (fileType.includes('tif') || fileType.includes('tiff')) {
          return 'raster';
        } else if (fileType.includes('mbtiles')) {
          return layer.dimension === '2.5D' ? 'raster' : 'vector';
        }
      }
      
      // 根据服务类型判断
      if (layer.service_type) {
        const serviceType = layer.service_type.toLowerCase();
        if (serviceType.includes('wms')) return 'wms';
        if (serviceType.includes('wmts')) return 'wmts';
        if (serviceType.includes('martin')) return 'vector';
      }
      
      // 默认返回vector
      return 'vector';
    };
    
    // 生成场景和图层数据（模拟后端API）
    const generateScenesAndLayers = async () => {
      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const scenesAndLayers = [];
      const scenes = [
        { id: 1, name: '城市规划项目' },
        { id: 2, name: '环境监测区域' },
        { id: 3, name: '交通分析场景' },
        { id: 4, name: '地质勘探区域' }
      ];
      
      const layerTypes = ['vector', 'raster', 'wms', 'wmts'];
      
      scenes.forEach(scene => {
        const layerCount = Math.floor(Math.random() * 4) + 2; // 2-5个图层
        
        for (let i = 0; i < layerCount; i++) {
          const layerType = layerTypes[Math.floor(Math.random() * layerTypes.length)];
          scenesAndLayers.push({
            layerId: `${scene.id}_layer_${i + 1}`,
            sceneId: scene.id,
            sceneName: scene.name,
            layerName: `${scene.name}_${layerType}_图层_${i + 1}`,
            layerType: layerType,
            minZoom: Math.floor(Math.random() * 3),
            maxZoom: Math.floor(Math.random() * 5) + 15,
            bounds: [
              Math.random() * 20 + 110, // 经度范围大致在中国
              Math.random() * 20 + 20,  // 纬度范围
              Math.random() * 20 + 120,
              Math.random() * 20 + 30
            ],
            tiles: [], // 初始为空
            totalSize: 0,
            zoomLevels: []
          });
        }
      });
      
      return scenesAndLayers;
    };
    const filteredCacheData = computed(() => {
      let filtered = cacheData.value;

      if (selectedSceneFilter.value) {
        const selectedScene = sceneList.value.find(s => s.id === selectedSceneFilter.value);
        if (selectedScene) {
          filtered = filtered.filter(layer => 
            layer.sceneName === selectedScene.name
          );
        }
      }
      //console.log(filtered);

      if (cacheSearchText.value) {
        const searchText = cacheSearchText.value.toLowerCase();
        filtered = filtered.filter(layer => 
          layer.sceneName.toLowerCase().includes(searchText) ||
          layer.layerName.toLowerCase().includes(searchText) ||
          layer.layerId.toLowerCase().includes(searchText)
        );
      }

      return filtered;
    });

    const filterCacheData = () => {
      // 过滤逻辑在计算属性中处理
    };

    const clearAllCache = async () => {
      if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        await ElMessageBox.confirm(
          '确定要清空所有缓存数据吗？此操作不可恢复！',
          '确认清空',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        );

        cacheProgressVisible.value = true;
        cacheOperationRunning.value = true;
        cacheProgress.message = '正在清空缓存...';
        cacheProgress.percent = 0;

        await tileCacheService.clearAllTiles();
        
        cacheProgress.percent = 100;
        cacheProgress.message = '清空完成';
        
        setTimeout(() => {
          cacheProgressVisible.value = false;
          cacheOperationRunning.value = false;
        }, 1000);

        await refreshCacheData();
        ElMessage.success('所有缓存已清空');
        
      } catch (error) {
        cacheProgressVisible.value = false;
        cacheOperationRunning.value = false;
        
        if (error !== 'cancel') {
          console.error('清空缓存失败:', error);
          ElMessage.error('清空缓存失败: ' + error.message);
        }
      }
    };

    const exportCacheData = () => {
      try {
        const exportData = {
          exportTime: new Date().toISOString(),
          stats: cacheStats,
          scenes: sceneList.value,
          layers: cacheData.value.map(layer => ({
            layerId: layer.layerId,
            sceneName: layer.sceneName,
            layerName: layer.layerName,
            bounds: layer.bounds,
            zoomLevels: layer.zoomLevels,
            tileCount: layer.tiles.length,
            totalSize: layer.totalSize,
            tiles: layer.tiles.map(tile => ({
              id: tile.id,
              zoomLevel: tile.zoomLevel,
              tileX: tile.tileX,
              tileY: tile.tileY,
              size: tile.size,
              contentType: tile.contentType,
              timestamp: tile.timestamp,
              url: tile.url
            }))
          }))
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
          type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cache-data-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        ElMessage.success('缓存数据已导出');
      } catch (error) {
        console.error('导出失败:', error);
        ElMessage.error('导出失败: ' + error.message);
      }
    };

    const importCacheData = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = async (e) => {
          try {
            cacheProgressVisible.value = true;
            cacheOperationRunning.value = true;
            cacheProgress.message = '正在导入缓存数据...';
            cacheProgress.percent = 0;

            const importData = JSON.parse(e.target.result);
            
            if (!importData.layers || !Array.isArray(importData.layers)) {
              throw new Error('无效的缓存数据格式');
            }

            let importedCount = 0;
            const totalTiles = importData.layers.reduce((sum, layer) => sum + layer.tiles.length, 0);

            for (const layer of importData.layers) {
              for (const tile of layer.tiles) {
                try {
                  console.log('导入瓦片元数据:', tile);
                  
                  importedCount++;
                  
                  cacheProgress.current = importedCount;
                  cacheProgress.total = totalTiles;
                  cacheProgress.percent = Math.round((importedCount / totalTiles) * 100);
                  cacheProgress.message = `正在导入缓存 ${importedCount}/${totalTiles}`;
                  
                } catch (error) {
                  console.warn('导入瓦片失败:', error);
                }
              }
            }

            cacheProgress.percent = 100;
            cacheProgress.message = '导入完成';
            
            setTimeout(() => {
              cacheProgressVisible.value = false;
              cacheOperationRunning.value = false;
            }, 1000);

            await refreshCacheData();
            ElMessage.success(`成功导入 ${importedCount} 个瓦片的元数据`);
            
            resolve(true);
          } catch (error) {
            cacheProgressVisible.value = false;
            cacheOperationRunning.value = false;
            
            console.error('导入失败:', error);
            ElMessage.error('导入失败: ' + error.message);
            reject(error);
          }
        };

        reader.onerror = () => {
          ElMessage.error('读取文件失败');
          reject(new Error('读取文件失败'));
        };

        reader.readAsText(file);
      });
    };

    const deleteLayerCache = async (layer) => {
      if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      if (!layer.tiles || layer.tiles.length === 0) {
        ElMessage.warning('该图层没有缓存数据');
        return;
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除图层 "${layer.layerName}" 的所有缓存数据吗？\n共 ${layer.tiles.length} 个瓦片缓存将被删除。`,
          '确认删除缓存',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning',
          }
        );

        cacheProgressVisible.value = true;
        cacheOperationRunning.value = true;
        cacheProgress.message = '正在删除图层缓存...';
        cacheProgress.percent = 0;
        cacheProgress.current = 0;
        cacheProgress.total = layer.tiles.length;

        // 用实际 tile 的 layerId 进行删除，确保所有相关缓存都被清除
        const actualLayerIds = [...new Set(layer.tiles.map(t => t.layerId))];
        let deletedCount = 0;
        for (const realLayerId of actualLayerIds) {
          deletedCount += await tileCacheService.deleteLayerTiles(realLayerId);
        }

        cacheProgress.percent = 100;
        cacheProgress.message = '删除完成';

        setTimeout(() => {
          cacheProgressVisible.value = false;
          cacheOperationRunning.value = false;
        }, 1000);

        await refreshCacheData();
        ElMessage.success(`成功删除图层 "${layer.layerName}" 的 ${deletedCount} 个瓦片缓存`);

      } catch (error) {
        cacheProgressVisible.value = false;
        cacheOperationRunning.value = false;

        if (error !== 'cancel') {
          console.error('删除图层缓存失败:', error);
          ElMessage.error('删除图层缓存失败: ' + error.message);
        }
      }
    };

    

    const deleteTile = async (tile) => {
      if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除瓦片 ${tile.layerId}_${tile.zoomLevel}_${tile.tileX}_${tile.tileY} 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        );

        const success = await tileCacheService.deleteTile(tile.layerId, tile.zoomLevel, tile.tileX, tile.tileY);
        if (success) {
          await refreshCacheData();
          ElMessage.success('瓦片已删除');
        } else {
          ElMessage.error('删除瓦片失败');
        }
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除瓦片失败:', error);
          ElMessage.error('删除瓦片失败: ' + error.message);
        }
      }
    };
    
    // 开始配置图层缓存
    const startLayerCache = async (layer) => {
      // 设置当前图层并显示配置对话框
      currentCacheLayer.value = layer;
      
      // 初始化缓存状态（默认开启）
      currentLayerCacheEnabled.value = true;
      
      // 设置默认缩放级别
      currentMapZoom.value = 10;
      
      // 显示配置对话框
      cacheConfigVisible.value = true;
    };



    // 缓存配置对话框打开事件
    const onCacheConfigDialogOpened = () => {
      setTimeout(() => {
        initConfigMap();
      }, 300);
    };

    // 初始化配置地图
    const initConfigMap = () => {
      const mapContainer = document.getElementById('cache-config-map');
      if (!mapContainer) {
        console.error('配置地图容器未找到');
        return;
      }

      // 清除之前的地图实例
      if (configMap) {
        configMap.setTarget(null);
        configMap = null;
      }

      // 获取图层边界
      const layerBounds = currentCacheLayer.value.bounds || [104.04, 30.64, 104.08, 30.68];
      const centerLon = (layerBounds[0] + layerBounds[2]) / 2;
      const centerLat = (layerBounds[1] + layerBounds[3]) / 2;

      // 创建边界框特征
      const boundsFeature = new Feature({
        geometry: new Polygon([[
          [layerBounds[0], layerBounds[1]],
          [layerBounds[2], layerBounds[1]],
          [layerBounds[2], layerBounds[3]],
          [layerBounds[0], layerBounds[3]],
          [layerBounds[0], layerBounds[1]]
        ]])
      });

      boundsFeature.setStyle(new Style({
        stroke: new Stroke({
          color: 'rgba(0, 0, 255, 0.8)',
          width: 2,
          lineDash: [5, 5]
        }),
        fill: new Fill({
          color: 'rgba(0, 0, 255, 0.1)'
        })
      }));
      // 检查当前图层是否在baseMaps中    
      
      const isBaseMap = baseMaps.find(bm => bm.key === currentCacheLayer.value.layerId);
      
      
      
      if (isBaseMap) {
        // 如果当前图层是底图，则使用底图的url和layerId创建WMTS图层
        const wmtsTileLoadFunction = createWmtsTileLoadFunction({
          layerId: isBaseMap.key,
          tileCacheService: tileCacheService,
          enableCacheStorage: currentLayerCacheEnabled.value
        });
        
        const baseMapSource = new XYZ({
          url: isBaseMap.url,
          crossOrigin: 'anonymous',
          maxZoom: 18,
          minZoom: 3
        });
        
        baseMapSource.setTileLoadFunction(wmtsTileLoadFunction);
        
        baseLayer = new TileLayer({
          source: baseMapSource
        });
        
        // 底图不创建MVT图层
        console.log(`当前图层 ${currentCacheLayer.value.layerName} 是底图，只创建WMTS图层`);
        
      } else {
        // 如果不是底图，则创建默认的高德底图 + 可能的MVT图层
        const wmtsTileLoadFunction = createWmtsTileLoadFunction({
          layerId: 'gaode',
          tileCacheService: tileCacheService,
          enableCacheStorage: true // 默认底图始终开启缓存
        });
        
        const gaodeSource = new XYZ({
          url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
          crossOrigin: 'anonymous',
          maxZoom: 18,
          minZoom: 3
        });
        
        gaodeSource.setTileLoadFunction(wmtsTileLoadFunction);
        
        baseLayer = new TileLayer({
          source: gaodeSource
        });
        
        // 如果有MVT URL，创建MVT图层
        if (currentCacheLayer.value.originalLayer?.mvt_url) {
          const mvtTileLoadFunction = createMvtTileLoadFunction({
            layerId: currentCacheLayer.value.layerId,
            tileCacheService: tileCacheService,
            enableCacheStorage: currentLayerCacheEnabled.value
          });
          
          let url = currentCacheLayer.value.originalLayer.mvt_url;
          url = url.replace('.pbf', '');
          
          const mvtSource = new VectorTileSource({
            url: url,
            format: new MVT(),
            tileLoadFunction: mvtTileLoadFunction
          });
          
          mvtLayer = new VectorTileLayer({
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
          
          console.log(`当前图层 ${currentCacheLayer.value.layerName} 不是底图，创建默认底图 + MVT图层`);
        } else {
          console.log(`当前图层 ${currentCacheLayer.value.layerName} 不是底图且无MVT URL，只创建默认底图`);
        }
      }
      
      // 创建边界框图层
      const boundsSource = new VectorSource({
        features: [boundsFeature]
      });

      const boundsLayer = new VectorLayer({
        source: boundsSource
      });
      const gridLayer = new TileLayer({
          source: new TileDebug(),
        });
      // 创建地图
      const layers = [baseLayer, boundsLayer, gridLayer];
      if (mvtLayer) {
        layers.push(mvtLayer);
      }

      configMap = new Map({
        target: 'cache-config-map',
        layers: layers,
        view: new View({
          center: fromLonLat([centerLon, centerLat]),
          zoom: currentMapZoom.value
        })
      });

      // 监听缩放级别变化
      configMap.getView().on('change:resolution', () => {
        currentMapZoom.value = Math.round(configMap.getView().getZoom());
        
      });

      // 强制更新地图尺寸
      setTimeout(() => {
        if (configMap) {
          configMap.updateSize();
        }
      }, 100);
    };




    const stopCacheOperation = () => {
      if (dataCacheService) {
        dataCacheService.stopLoading();
      }
      cacheOperationRunning.value = false;
      cacheProgressVisible.value = false;
      ElMessage.info('操作已停止');
    };

    const handleExpandChange = (row, expandedRows) => {
      expandedRowKeys.value = expandedRows.map(r => r.sceneId + '_' +r.layerId);
    };

    const toggleLayerCache = () => {
      currentLayerCacheEnabled.value = !currentLayerCacheEnabled.value;
      
      // 重新设置 tileLoadFunction
      if (configMap) {
        // 这里假设你有 baseLayer 和/或 mvtLayer 的引用
        if (baseLayer && baseLayer.getSource && baseLayer.getSource().setTileLoadFunction) {
          const wmtsTileLoadFunction = createWmtsTileLoadFunction({
            layerId: currentCacheLayer.value.layerId,
            tileCacheService: tileCacheService,
            enableCacheStorage: currentLayerCacheEnabled.value
          });
          baseLayer.getSource().setTileLoadFunction(wmtsTileLoadFunction);
        }
        if (mvtLayer && mvtLayer.getSource && mvtLayer.getSource().setTileLoadFunction) {
          const mvtTileLoadFunction = createMvtTileLoadFunction({
            layerId: currentCacheLayer.value.layerId,
            tileCacheService: tileCacheService,
            enableCacheStorage: currentLayerCacheEnabled.value
          });
          mvtLayer.getSource().setTileLoadFunction(mvtTileLoadFunction);
        }
      }
    };

    const previewTile = async (tile) => {
      try {
        currentTile.value = tile;
        tileImageUrl.value = '';
        tilePreviewVisible.value = true;

        // 判断是否为图片类型
        const isImage = tile.contentType && (tile.contentType.startsWith('image/') || tile.contentType === 'image/png' || tile.contentType === 'image/jpeg');
        if (!isImage) {
          tileImageUrl.value = null;
          return;
        }

        // 获取瓦片数据
        const tileData = await tileCacheService.getTile(tile.layerId, tile.zoomLevel, tile.tileX, tile.tileY);
        if (tileData && tileData.data) {
          const blob = tileData.data instanceof Blob ? tileData.data : new Blob([tileData.data], { type: tile.contentType || 'image/png' });
          tileImageUrl.value = URL.createObjectURL(blob);
        } else {
          tileImageUrl.value = null;
        }
      } catch (error) {
        console.error('预览瓦片失败:', error);
        ElMessage.error('预览瓦片失败: ' + error.message);
        tileImageUrl.value = null;
      }
    };



    onMounted(() => {
      initCacheService();
    });

    return {
      selectedSceneFilter,
      sceneList,
      cacheSearchText,
      expandedRowKeys,
      cacheProgressVisible,
      cacheOperationRunning,
      cacheProgress,
      tilePreviewVisible,
      currentTile,
      tileImageUrl,
      cacheData,
      cacheStats,
      toggleLayerCache,
      // 新增的缓存配置相关
      cacheConfigVisible,
      currentCacheLayer,
      cacheConfig,
      currentMapZoom,
      currentLayerCacheEnabled,
      filteredCacheData,
      refreshCacheData,
      filterCacheData,
      clearAllCache,
      exportCacheData,
      importCacheData,
      deleteLayerCache,
      startLayerCache,
      previewTile,
      deleteTile,
      stopCacheOperation,
      handleExpandChange,
      formatFileSize,
      formatTimeAgo,
      // 新增的方法
      onCacheConfigDialogOpened,
      enableLayerCache,
      disableLayerCache
    };
  }
};
</script>

<style scoped>
.cache-manager {
  padding: 16px;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.cache-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 12px 16px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.cache-stats-compact {
  display: flex;
  justify-content: center;
  gap: 24px;
  background: white;
  padding: 12px 16px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
}

.cache-content {
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 16px;
}

.cache-layers {
  margin-bottom: 16px;
}

.expanded-content {
  background-color: #fafafa;
  padding: 16px;
  border-radius: 4px;
  margin: 8px 0;
}

.tiles-header {
  margin-bottom: 12px;
}

.tiles-header h4 {
  margin: 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.zoom-levels {
  font-size: 12px;
  color: #666;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.bounds-text {
  font-size: 11px;
  color: #666;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.no-bounds {
  color: #ccc;
}

.no-data {
  color: #ccc;
  font-style: italic;
}

.empty-cache {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.empty-cache i {
  font-size: 48px;
  color: #ddd;
  margin-bottom: 12px;
}

.empty-cache p {
  font-size: 16px;
  margin-bottom: 16px;
}

.tile-preview {
  text-align: center;
}

.tile-info {
  text-align: left;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.tile-info p {
  margin: 8px 0;
}

.tile-image {
  text-align: center;
}

.loading-placeholder {
  padding: 40px;
  color: #666;
}

.loading-placeholder i {
  font-size: 24px;
  margin-bottom: 10px;
}

/* 缓存配置对话框样式 */
.cache-config-content {
  height: 600px;
}

.cache-config-panel {
  display: flex;
  height: 100%;
  gap: 20px;
}

.config-left {
  width: 240px;
  flex-shrink: 0;
  padding: 20px;
  background: #fafbfc;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.config-left h4 {
  margin: 0 0 20px 0;
  color: #24292e;
  font-size: 16px;
  font-weight: 600;
  position: relative;
  padding-bottom: 10px;
  border-bottom: 2px solid #409eff;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.config-form :deep(.el-form-item__label) {
  color: #606266 !important;
  font-weight: 500;
}

.config-form :deep(.el-input-number) {
  border-radius: 6px;
}

.config-form :deep(.el-input__wrapper) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.config-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-form :deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-form :deep(.el-radio) {
  color: #606266;
  margin-right: 0;
}

.config-form :deep(.el-radio__label) {
  color: #606266 !important;
  font-weight: 500;
}

.config-form :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #409eff !important;
}

.config-actions {
  margin-top: auto;
  padding-top: 16px;
  display: flex;
  gap: 8px;
  border-top: 1px solid #e1e4e8;
  flex-wrap: wrap;
  justify-content: flex-start;
}

.config-actions :deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.config-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

#cache-config-map {
  width: 100%;
  height: 100%;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  background: #f8f9fa;
}

/* 缓存状态样式 */
.cache-enabled {
  color: #67c23a;
  font-weight: 600;
}

.cache-disabled {
  color: #f56c6c;
  font-weight: 600;
}

/* 缓存可视化对话框增强样式 */
.cache-visualization-dialog {
  max-width: 95vw;
  max-height: 95vh;
}

.cache-visualization-content {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.cache-info-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 16px;
}

.info-left h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
}

.cache-stats-row {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.visualization-map {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* 地图容器样式 */
#cache-visualization-map {
  width: 100%;
  height: 100%;
  border-radius: 4px;
}

/* 缓存配置对话框特定样式 */
:deep(.cache-config-dialog) {
  .el-dialog__body {
    padding: 20px;
  }
}

/* 工具提示样式 */
.tile-tooltip {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
}

.cache-progress {
  text-align: center;
}

.progress-text {
  margin: 15px 0 5px 0;
  color: #666;
}

.progress-details {
  margin-top: 10px;
  font-size: 14px;
  color: #999;
}

@media (max-width: 768px) {
  .cache-manager {
    padding: 12px;
  }
  
  .cache-toolbar {
    flex-direction: column;
    gap: 12px;
    padding: 12px;
  }
  
  .toolbar-left {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .cache-stats-compact {
    flex-wrap: wrap;
    gap: 16px;
    padding: 12px;
  }
  
  .stat-item {
    min-width: 120px;
  }
  
  .expanded-content {
    padding: 12px;
  }
}

/* 缓存可视化对话框样式 */
:deep(.cache-visualization-dialog) {
  .el-dialog__body {
    padding: 0;
    height: 80vh;
    overflow: hidden;
  }
  
  .el-dialog__header {
    border-bottom: 1px solid #e4e7ed;
    padding: 16px 20px;
  }
  
  .el-dialog {
    margin-top: 5vh !important;
  }
}

.cache-visualization-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.cache-info-panel {
  padding: 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #ddd;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-left {
  flex: 1;
}

.info-right {
  flex-shrink: 0;
  margin-left: 20px;
}

.cache-info-panel h4 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.cache-stats-row {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #666;
}

.cache-map-container {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 600px;
  position: relative;
  overflow: hidden;
  background-color: #f0f0f0;
}

.cache-map-container .ol-viewport {
  width: 100% !important;
  height: 100% !important;
}

/* 确保OpenLayers地图控件样式正常 */
.cache-map-container .ol-zoom {
  left: 8px;
  top: 8px;
}

.cache-map-container .ol-attribution {
  right: 8px;
  bottom: 8px;
}
</style>