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
        <el-button type="success" size="small" @click="generateTestData" plain>
          <i class="el-icon-magic-stick"></i> 生成测试数据
        </el-button>
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
          :row-key="row => row.layerId"
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
                type="info" 
                size="small" 
                @click="visualizeCache(row)"
                :disabled="!row.tiles || row.tiles.length === 0"
                title="可视化缓存"
              >
                <i class="el-icon-view"></i> 可视化
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

    <!-- 瓦片预览对话框 -->
    <el-dialog 
      title="瓦片预览" 
      v-model="tilePreviewVisible" 
      width="500px"
    >
      <div class="tile-preview">
        <div class="tile-info">
          <p><strong>图层ID:</strong> {{ currentTile?.layerId }}</p>
          <p><strong>缩放级别:</strong> {{ currentTile?.zoomLevel }}</p>
          <p><strong>坐标:</strong> X={{ currentTile?.tileX }}, Y={{ currentTile?.tileY }}</p>
          <p><strong>大小:</strong> {{ formatFileSize(currentTile?.size || 0) }}</p>
          <p><strong>类型:</strong> {{ currentTile?.contentType || 'image/png' }}</p>
        </div>
        <div class="tile-image">
          <template v-if="currentTile && currentTile.contentType && (currentTile.contentType.startsWith('image/') || currentTile.contentType === 'image/png' || currentTile.contentType === 'image/jpeg')">
            <img 
              v-if="tileImageUrl" 
              :src="tileImageUrl" 
              alt="瓦片图像"
              style="max-width: 100%; border: 1px solid #ddd; border-radius: 4px;"
            />
            <div v-else class="loading-placeholder">
              <i class="el-icon-loading"></i>
              <p>加载中...</p>
            </div>
          </template>
          <template v-else>
            <div class="loading-placeholder">
              <i class="el-icon-warning-outline"></i>
              <p>暂不支持该类型瓦片预览</p>
            </div>
          </template>
        </div>
      </div>
    </el-dialog>

    <!-- 缓存进度对话框 -->
    <el-dialog 
      title="缓存操作进度" 
      v-model="cacheProgressVisible" 
      :closable="false"
      :close-on-click-modal="false"
      width="500px"
    >
      <div class="cache-progress">
        <el-progress 
          :percentage="cacheProgress.percent" 
          :status="cacheProgress.status"
          :stroke-width="8"
        ></el-progress>
        <p class="progress-text">{{ cacheProgress.message }}</p>
        <div class="progress-details">
          <span>{{ cacheProgress.current }} / {{ cacheProgress.total }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="stopCacheOperation" :disabled="!cacheOperationRunning">停止操作</el-button>
      </template>
    </el-dialog>

    <!-- 缓存配置对话框 -->
    <el-dialog 
      title="图层缓存配置" 
      v-model="cacheConfigVisible" 
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      custom-class="cache-config-dialog"
      @opened="onCacheConfigDialogOpened"
    >
      <div class="cache-config-content">
        <div class="cache-config-panel">
          <div class="config-left">
            <h4>{{ currentCacheLayer.layerName }}</h4>
            <div class="config-form">
              <el-form :model="cacheConfig" label-width="120px" size="small">
                <el-form-item label="起始缩放级别">
                  <el-input-number 
                    v-model="cacheConfig.minZoom" 
                    :min="1" 
                    :max="18" 
                    style="width: 120px"
                  />
                </el-form-item>
                <el-form-item label="终止缩放级别">
                  <el-input-number 
                    v-model="cacheConfig.maxZoom" 
                    :min="1" 
                    :max="18" 
                    style="width: 120px"
                  />
                </el-form-item>
                <el-form-item label="当前缩放级别">
                  <span>{{ currentMapZoom }}</span>
                </el-form-item>
                <el-form-item label="预计瓦片数">
                  <span>{{ estimatedTileCount }}</span>
                </el-form-item>
                <el-form-item label="缓存范围">
                  <el-radio-group v-model="cacheConfig.useDefaultBounds">
                    <el-radio :label="true">使用默认边界框</el-radio>
                    <el-radio :label="false">框选范围</el-radio>
                  </el-radio-group>
                </el-form-item>
                <div class="config-actions">
                  <el-button 
                    type="primary" 
                    @click="startCacheWithConfig"
                    :disabled="!canStartCache"
                  >
                    开始缓存
                  </el-button>
                  <el-button @click="cacheConfigVisible = false">取消</el-button>
                </div>
              </el-form>
            </div>
          </div>
          <div class="config-right">
            <div id="cache-config-map" style="width: 100%; height: 400px; border: 1px solid #ddd;"></div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 缓存可视化对话框 -->
    <el-dialog 
      title="缓存数据可视化" 
      v-model="cacheVisualizationVisible" 
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      custom-class="cache-visualization-dialog"
      @opened="onVisualizationDialogOpened"
    >
      <div class="cache-visualization-content">
        <div class="cache-info-panel">
          <div class="info-left">
            <h4>{{ currentVisualizationLayer.layerName }}</h4>
            <div class="cache-stats-row">
              <span>场景: {{ currentVisualizationLayer.sceneName }}</span>
              <span>瓦片数: {{ currentVisualizationLayer.tiles?.length || 0 }}</span>
              <span>缓存大小: {{ formatFileSize(currentVisualizationLayer.totalSize || 0) }}</span>
            </div>
          </div>
          <div class="info-right">
            <el-button-group>
              <el-button 
                :type="showCacheGrid ? 'primary' : 'default'" 
                size="small"
                @click="toggleCacheGrid"
              >
                {{ showCacheGrid ? '隐藏' : '显示' }}缓存网格
              </el-button>
              <el-button 
                :type="showCachePoints ? 'primary' : 'default'" 
                size="small"
                @click="toggleCachePoints"
              >
                {{ showCachePoints ? '隐藏' : '显示' }}缓存点位
              </el-button>
              <el-button 
                type="info" 
                size="small"
                @click="resetMapView"
              >
                重置视图
              </el-button>
            </el-button-group>
          </div>
        </div>
        <div id="cache-visualization-map" class="cache-map-container"></div>
      </div>
      <template #footer>
        <el-button @click="cacheVisualizationVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
/*eslint-disable*/
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import gisApi from '@/api/gis.js';
import { formatFileSize, formatTimeAgo, SimpleCacheService, calculateTileCount, TileCacheService } from '@/services/tileCache';

// OpenLayers导入
import { Map, View, Feature } from 'ol';
import { Tile as TileLayer, Vector as VectorLayer, VectorTile as VectorTileLayer } from 'ol/layer';
import { OSM, Vector as VectorSource, TileImage, XYZ, VectorTile as VectorTileSource } from 'ol/source';
import { createXYZ } from 'ol/tilegrid';
import MVT from 'ol/format/MVT';
import { Polygon, Point } from 'ol/geom';
import { Style, Stroke, Fill, Text } from 'ol/style';
import { fromLonLat, transformExtent, toLonLat } from 'ol/proj';
import { defaults as defaultControls } from 'ol/control';
import Circle from 'ol/style/Circle';

// 引入proj4库用于坐标系转换
import proj4 from 'proj4';
import { register } from 'ol/proj/proj4';
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

    // 缓存可视化相关
    const cacheVisualizationVisible = ref(false);
    const currentVisualizationLayer = ref({});
    let visualizationMap = null;

    // 缓存配置相关
    const cacheConfigVisible = ref(false);
    const currentCacheLayer = ref({});
    let configMap = null;
    let drawSource = null;
    let drawVector = null;
    let drawInteraction = null;
    
    const cacheConfig = reactive({
      minZoom: 10,
      maxZoom: 15,
      useDefaultBounds: true,
      selectedBounds: null
    });
    
    const currentMapZoom = ref(10);
    const estimatedTileCount = ref(0);
    
    const canStartCache = computed(() => {
      return cacheConfig.minZoom <= cacheConfig.maxZoom && 
             (cacheConfig.useDefaultBounds || cacheConfig.selectedBounds);
    });

    const observer = new ResizeObserver(entries => {
      try {
        // 你的回调逻辑
      } catch (e) {
        console.error('ResizeObserver 异常:', e);
        // 处理异常
      }
    });
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
        
        // 输出缓存中的layerId列表用于调试
        const cacheLayerIds = [...new Set(allTiles.map(tile => tile.layerId))];
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

        // 输出场景图层中的layerId列表用于调试
        const sceneLayerIds = cacheData.value.map(layer => layer.layerId);
        //console.log('场景图层的layerId列表:', sceneLayerIds);
        //console.log('layerId匹配情况:');
        
        // 4. 将缓存数据合并到场景图层数据中
        cacheData.value.forEach(layer => {
          // 尝试多种匹配方式
          let cachedData = null;
          let matchedLayerId = null;
          
          // 方式1: 直接匹配
          cachedData = layerGroups[layer.layerId];
          if (cachedData) {
            matchedLayerId = layer.layerId;
          }
          
          // 方式2: 如果是场景ID_图层ID格式，尝试用图层ID部分匹配
          if (!cachedData && layer.layerId.includes('_')) {
            const layerIdPart = layer.layerId.split('_')[1]; // 提取图层ID部分
            cachedData = layerGroups[layerIdPart];
            if (cachedData) {
              matchedLayerId = layerIdPart;
            }
          }
          
          // 方式3: 尝试匹配martin-vector格式
          if (!cachedData && layer.sceneLayerId) {
            // 尝试martin-vector-{layerId}-{layerName}格式
            for (const cacheLayerId in layerGroups) {
              if (cacheLayerId.startsWith('martin-vector-') && 
                  cacheLayerId.includes(layer.sceneLayerId.toString())) {
                cachedData = layerGroups[cacheLayerId];
                matchedLayerId = cacheLayerId;
                break;
              }
            }
          }
          
          // 方式4: 根据sceneLayerId匹配
          if (!cachedData && layer.sceneLayerId) {
            cachedData = layerGroups[layer.sceneLayerId.toString()];
            if (cachedData) {
              matchedLayerId = layer.sceneLayerId.toString();
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
        
        // 四个常用底图（可根据你OpenLayers页面实际key和名称调整）
        const baseMaps = [
          { key: 'gaode', name: '高德地图', type: 'raster' },
          { key: 'gaodeSatellite', name: '高德卫星', type: 'raster' },
          { key: 'osm', name: 'OpenStreetMap', type: 'raster' },
          { key: 'esriSatellite', name: 'Esri卫星', type: 'raster' },
        ];
        // 默认中国全图范围
        const defaultBaseMapBounds = [73.0, 3.0, 135.0, 53.0];
        const baseMapLayers = baseMaps.map((bm) => ({
          layerId: `basemap_${bm.key}`,
          sceneId: 'basemap',
          sceneName: '底图',
          layerName: bm.name,
          layerType: bm.type,
          minZoom: 2,
          maxZoom: 18,
          bounds: defaultBaseMapBounds,
          sceneLayerId: `basemap_${bm.key}`,
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
              allLayersData.push({
                layerId: `${scene.id}_${layer.id || layer.layer_id}`,
                sceneId: scene.id,
                sceneName: scene.name,
                layerName: layer.layer_name || layer.name || `图层_${layer.id || layer.layer_id}`,
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

        await tileCacheService.clearAllCache();
        
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
                  //console.log('导入瓦片元数据:', tile);
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
    
    // 开始缓存图层
    const startLayerCache = async (layer) => {
      if (!dataCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      // 设置当前图层并显示配置对话框
      currentCacheLayer.value = layer;
      
      // 初始化配置
      const layerBounds = layer.bounds;
      if (Array.isArray(layerBounds) && layerBounds.length === 4) {
        cacheConfig.selectedBounds = layerBounds;
        
        // 根据边界框计算合适的缩放级别
        const recommendedZoom = calculateRecommendedZoom(layerBounds);
        cacheConfig.minZoom = Math.max(1, recommendedZoom - 2);
        cacheConfig.maxZoom = Math.min(18, recommendedZoom + 2);
        currentMapZoom.value = recommendedZoom;
      } else {
        // 默认配置
        cacheConfig.minZoom = 10;
        cacheConfig.maxZoom = 15;
        currentMapZoom.value = 10;
        cacheConfig.selectedBounds = [104.04, 30.64, 104.08, 30.68]; // 成都默认区域
      }
      
      cacheConfig.useDefaultBounds = true;
      updateEstimatedTileCount();
      
      cacheConfigVisible.value = true;
    };

    // 计算推荐的缩放级别
    const calculateRecommendedZoom = (bounds) => {
      if (!Array.isArray(bounds) || bounds.length !== 4) return 10;
      
      const [minX, minY, maxX, maxY] = bounds;
      const width = Math.abs(maxX - minX);
      const height = Math.abs(maxY - minY);
      const area = width * height;
      
      // 根据面积估算合适的缩放级别
      if (area > 100) return 8;      // 大范围
      if (area > 10) return 10;      // 中等范围
      if (area > 1) return 12;       // 小范围
      if (area > 0.1) return 14;     // 很小范围
      return 16;                     // 微小范围
    };

    // 更新估算的瓦片数量
    const updateEstimatedTileCount = () => {
      if (!cacheConfig.selectedBounds) {
        estimatedTileCount.value = 0;
        return;
      }
      
      const bounds = {
        west: cacheConfig.selectedBounds[0],
        south: cacheConfig.selectedBounds[1],
        east: cacheConfig.selectedBounds[2],
        north: cacheConfig.selectedBounds[3]
      };
      
      try {
        estimatedTileCount.value = calculateTileCount(bounds, {
          min: cacheConfig.minZoom,
          max: cacheConfig.maxZoom
        });
      } catch (error) {
        console.warn('计算瓦片数量失败:', error);
        estimatedTileCount.value = 0;
      }
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

      const boundsSource = new VectorSource({
        features: [boundsFeature]
      });

      const boundsLayer = new VectorLayer({
        source: boundsSource
      });

      // 创建地图
      configMap = new Map({
        target: 'cache-config-map',
        layers: [
          new TileLayer({
            source: new XYZ({
              url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
              crossOrigin: 'anonymous'
            })
          }),
          boundsLayer
        ],
        view: new View({
          center: fromLonLat([centerLon, centerLat]),
          zoom: currentMapZoom.value
        })
      });

      // 监听缩放级别变化
      configMap.getView().on('change:resolution', () => {
        currentMapZoom.value = Math.round(configMap.getView().getZoom());
        updateEstimatedTileCount();
      });

      // 强制更新地图尺寸
      setTimeout(() => {
        if (configMap) {
          configMap.updateSize();
        }
      }, 100);
    };

    // 开始实际缓存
    const startCacheWithConfig = async () => {
      if (!dataCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        cacheConfigVisible.value = false;
        
        cacheProgressVisible.value = true;
        cacheOperationRunning.value = true;
        cacheProgress.message = `正在缓存图层 "${currentCacheLayer.value.layerName}"...`;
        cacheProgress.percent = 0;
        cacheProgress.current = 0;
        cacheProgress.total = estimatedTileCount.value;

        ElMessage.info(`开始缓存图层: ${currentCacheLayer.value.layerName}`);
        
        // 使用配置的参数进行缓存
        const bounds = cacheConfig.useDefaultBounds ? 
          currentCacheLayer.value.bounds : 
          cacheConfig.selectedBounds;
        
        const zoomLevels = {
          min: cacheConfig.minZoom,
          max: cacheConfig.maxZoom
        };

        // 这里需要实现具体的缓存逻辑
        // 暂时使用原有的缓存策略作为示例
        if (currentCacheLayer.value.sceneId === 'basemap') {
          await dataCacheService.executeLoginStrategy();
        } else {
          // 只缓存当前图层
          await dataCacheService.cacheLayerData(
            currentCacheLayer.value.sceneId,
            {
              ...currentCacheLayer.value,
              layer_id: currentCacheLayer.value.layerId,
              layer_name: currentCacheLayer.value.layerName,
              scene_layer_id: currentCacheLayer.value.sceneLayerId,
            },
            'scene',
            {
              bounds: cacheConfig.useDefaultBounds ? currentCacheLayer.value.bounds : cacheConfig.selectedBounds,
              zoomLevels: { min: cacheConfig.minZoom, max: cacheConfig.maxZoom },
              maxTiles: 1000,
              onProgress: (current, total) => {
                cacheProgress.current = current;
                cacheProgress.total = total;
                cacheProgress.percent = total > 0 ? Math.round((current / total) * 100) : 0;
                cacheProgress.message = `已缓存 ${current} / ${total} 瓦片...`;
              }
            }
          );
          //await dataCacheService.executeSceneSwitchStrategy(currentCacheLayer.value.sceneId);
        }
        
        cacheProgress.status = 'success';
        cacheProgress.percent = 100;
        cacheProgress.message = '缓存完成！';
        
        ElMessage.success(`图层 ${currentCacheLayer.value.layerName} 缓存完成！`);
        
        setTimeout(() => {
          cacheProgressVisible.value = false;
          cacheOperationRunning.value = false;
        }, 1500);

        await refreshCacheData();
        
// 重新同步 currentCacheLayer，确保引用的是最新的表格数据
const updated = cacheData.value.find(
  l => l.layerId === currentCacheLayer.value.layerId
);
if (updated) {
  currentCacheLayer.value = updated;
}

      } catch (error) {
        cacheProgressVisible.value = false;
        cacheOperationRunning.value = false;
        
        console.error('缓存图层失败:', error);
        cacheProgress.status = 'exception';
        cacheProgress.message = '缓存失败: ' + error.message;
        ElMessage.error('缓存失败: ' + error.message);
      }
    };

    // 生成测试数据
    const generateTestData = async () => {
      if (!dataCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        await ElMessageBox.confirm(
          '确定要生成测试缓存数据吗？这将执行登录缓存策略生成一些测试瓦片。',
          '确认生成测试数据',
          {
            confirmButtonText: '生成',
            cancelButtonText: '取消',
            type: 'info',
          }
        );

        cacheProgressVisible.value = true;
        cacheOperationRunning.value = true;
        cacheProgress.message = '正在生成测试缓存数据...';
        cacheProgress.percent = 0;

        ElMessage.info('开始生成测试缓存数据...');
        
        // 执行登录缓存策略来生成测试数据
        await dataCacheService.executeLoginStrategy();
        
        cacheProgress.status = 'success';
        cacheProgress.percent = 100;
        cacheProgress.message = '测试数据生成完成！';
        
        ElMessage.success('测试数据生成完成');
        
        setTimeout(() => {
          cacheProgressVisible.value = false;
          cacheOperationRunning.value = false;
        }, 1500);

        await refreshCacheData();
      } catch (error) {
        cacheProgressVisible.value = false;
        cacheOperationRunning.value = false;
        
        if (error !== 'cancel') {
          console.error('生成测试数据失败:', error);
          cacheProgress.status = 'exception';
          cacheProgress.message = '生成失败: ' + error.message;
          ElMessage.error('生成测试数据失败: ' + error.message);
        }
      }
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
      expandedRowKeys.value = expandedRows.map(r => r.layerId);
    };

    const visualizeCache = async (layer) => {
      //console.log('开始可视化缓存:', layer);
      
      if (!layer.tiles || layer.tiles.length === 0) {
        ElMessage.warning('该图层没有缓存数据');
        return;
      }

      //console.log('缓存瓦片数据:', layer.tiles);
      currentVisualizationLayer.value = layer;
      cacheVisualizationVisible.value = true;

      // 等待对话框显示后再初始化地图
      setTimeout(() => {
        //console.log('对话框已显示，开始初始化地图');
        initVisualizationMap(layer);
      }, 500);
    };

    const initVisualizationMap = async (layer) => {
      console.log('initVisualizationMap 被调用，图层:', layer);
      
      const mapContainer = document.getElementById('cache-visualization-map');
      
      if (!mapContainer) {
        console.error('地图容器未找到');
        ElMessage.error('地图容器未找到，请重试');
        return;
      }

      // 清除之前的地图实例
      if (visualizationMap) {
        visualizationMap.setTarget(null);
        visualizationMap = null;
      }

      // 计算瓦片边界
      const tileBounds = calculateTileBounds(layer.tiles);
      
      // 如果没有有效边界，使用成都默认位置
      if (!tileBounds.extent) {
        tileBounds.centerLon = 104.06;
        tileBounds.centerLat = 30.67;
        tileBounds.extent = [102.99, 30.32, 104.79, 31.32];
      }

      // 创建底图 - 使用 OSM 确保能显示
      const baseLayer = new TileLayer({
        source: new OSM(),
        zIndex: 0
      });

      // 检查缓存数据类型，决定如何加载
      const firstTile = layer.tiles[0];
      const isMVT = firstTile && firstTile.contentType === 'application/x-protobuf';
      console.log('第一个瓦片信息:', firstTile);
      console.log('是否为 MVT:', isMVT);
      
      let dataLayer;
      
      if (isMVT) {
        console.log('检测到 MVT 数据，创建矢量瓦片图层');
        // 创建 MVT 图层加载缓存数据
        const mvtFormat = new MVT();
        const mvtSource = new VectorTileSource({
          format: mvtFormat,
          tileGrid: createXYZ({
            maxZoom: 20
          }),
          tileLoadFunction: async (tile, url) => {
            const coords = tile.getTileCoord();
            const [z, x, y] = [coords[0], coords[1], -coords[2] - 1];
            console.log(`尝试加载 MVT 瓦片: ${z}/${x}/${y}`);
            
            try {
              const cachedTile = await tileCacheService.getTile(layer.layerId, z, x, y);
              if (cachedTile && cachedTile.data) {
                console.log(`找到缓存瓦片 ${z}/${x}/${y}, 大小:`, cachedTile.size);
                const arrayBuffer = await cachedTile.data.arrayBuffer();
                console.log('ArrayBuffer 大小:', arrayBuffer.byteLength);
                
                const features = mvtFormat.readFeatures(arrayBuffer, {
                  extent: tile.getExtent(),
                  featureProjection: 'EPSG:3857'
                });
                console.log(`解析到 ${features.length} 个要素`);
                tile.setFeatures(features);
              } else {
                console.log(`未找到缓存瓦片 ${z}/${x}/${y}`);
                tile.setFeatures([]);
              }
            } catch (error) {
              console.warn(`加载 MVT 瓦片 ${z}/${x}/${y} 失败:`, error);
              tile.setFeatures([]);
            }
          }
        });

        dataLayer = new VectorTileLayer({
          source: mvtSource,
          style: {
            'stroke-color': '#0000FF',
            'stroke-width': 2,
            'fill-color': 'rgba(0, 0, 255, 0.3)',
            'circle-radius': 5,
            'circle-fill-color': '#FF0000'
          },
          zIndex: 1
        });
      } else {
        console.log('非 MVT 数据，创建普通图层');
        // 对于非 MVT 数据，创建瓦片边界可视化
        const tileFeatures = layer.tiles.map((tile, index) => {
          const bounds = getTileBounds(tile.zoomLevel, tile.tileX, tile.tileY);
          
          const feature = new Feature({
            geometry: new Polygon([bounds]),
            tileInfo: tile
          });
          
          feature.setStyle(new Style({
            stroke: new Stroke({
              color: '#FF0000',
              width: 2
            }),
            fill: new Fill({
              color: 'rgba(255, 0, 0, 0.1)'
            }),
            text: new Text({
              text: `Z${tile.zoomLevel}\n${tile.tileX},${tile.tileY}`,
              font: 'bold 12px Arial',
              fill: new Fill({
                color: '#FFFFFF'
              }),
              stroke: new Stroke({
                color: '#FF0000',
                width: 1
              }),
              textAlign: 'center',
              textBaseline: 'middle'
            })
          }));
          
          return feature;
        });

        const vectorSource = new VectorSource({
          features: tileFeatures
        });

        dataLayer = new VectorLayer({
          source: vectorSource,
          zIndex: 1
        });
      }

      // 创建地图
      try {
        visualizationMap = new Map({
          target: 'cache-visualization-map',

          layers: [baseLayer, dataLayer],

          view: new View({
            center: fromLonLat([tileBounds.centerLon, tileBounds.centerLat]),
            zoom: 10,
            //projection: 'EPSG:3857'
          }),
          controls: defaultControls({
            zoom: true,
            attribution: true
          })
        });

        // 存储图层引用以便切换
        visualizationMap.dataLayer = dataLayer;

        //console.log('地图创建成功:', visualizationMap);

        // 监听地图加载完成事件
        visualizationMap.once('rendercomplete', () => {
          console.log('地图渲染完成，图层类型:', isMVT ? 'MVT' : '普通');
          
          // 调整视图到瓦片范围
          if (tileBounds.extent) {
            try {
              const transformedExtent = transformExtent(
                tileBounds.extent, 
                'EPSG:4326', 
                'EPSG:3857'
              );
              
              visualizationMap.getView().fit(transformedExtent, {
                padding: [50, 50, 50, 50],
                duration: 1000,
                maxZoom: 15
              });
            } catch (extentError) {
              console.error('调整视图范围失败:', extentError);
            }
          }
        });

        // 添加地图点击事件来调试
        visualizationMap.on('click', (evt) => {
          const features = visualizationMap.getFeaturesAtPixel(evt.pixel);
          //console.log('点击位置的特征:', features);
          
          
          // 显示点击位置的坐标
          const coordinate = evt.coordinate;
          const lonlat = toLonLat(coordinate);
          //console.log('点击坐标 (投影):', coordinate);
          //console.log('点击坐标 (经纬度):', lonlat);
        });

        // 强制更新地图尺寸
        setTimeout(() => {
          if (visualizationMap) {
            //console.log('更新地图尺寸');
            visualizationMap.updateSize();
          }
        }, 100);

      } catch (mapError) {
        console.error('创建地图失败:', mapError);
        ElMessage.error('创建地图失败: ' + mapError.message);
      }
    };

    const calculateTileBounds = (tiles) => {
      if (!tiles || tiles.length === 0) {
        return { centerLon: 0, centerLat: 0, extent: null };
      }

      let minLon = Infinity, maxLon = -Infinity;
      let minLat = Infinity, maxLat = -Infinity;

      //console.log('开始计算边界，瓦片数量:', tiles.length);

      tiles.forEach((tile, index) => {
        const bounds = getTileBounds(tile.zoomLevel, tile.tileX, tile.tileY);
        // bounds是多边形坐标数组，需要正确提取边界
        const lons = bounds.map(coord => coord[0]);
        const lats = bounds.map(coord => coord[1]);
        
        const tileminLon = Math.min(...lons);
        const tilemaxLon = Math.max(...lons);
        const tileminLat = Math.min(...lats);
        const tilemaxLat = Math.max(...lats);
        
   
        minLon = Math.min(minLon, tileminLon);
        maxLon = Math.max(maxLon, tilemaxLon);
        minLat = Math.min(minLat, tileminLat);
        maxLat = Math.max(maxLat, tilemaxLat);
        
        //console.log(`当前总边界: 经度 ${minLon.toFixed(6)} - ${maxLon.toFixed(6)}, 纬度 ${minLat.toFixed(6)} - ${maxLat.toFixed(6)}`);
      });

      const result = {
        centerLon: (minLon + maxLon) / 2,
        centerLat: (minLat + maxLat) / 2,
        extent: [minLon, minLat, maxLon, maxLat]
      };
      
      //console.log('最终计算结果:', result);
      return result;
    };

    const getTileBounds = (z, x, y) => {
      const n = Math.pow(2, z);
      const lonDeg = (x / n) * 360.0 - 180.0;
      const latRad = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n)));
      const latDeg = (latRad * 180.0) / Math.PI;
      
      const lonDeg2 = ((x + 1) / n) * 360.0 - 180.0;
      const latRad2 = Math.atan(Math.sinh(Math.PI * (1 - 2 * (y + 1) / n)));
      const latDeg2 = (latRad2 * 180.0) / Math.PI;
      
      return [
        [lonDeg, latDeg],
        [lonDeg2, latDeg],
        [lonDeg2, latDeg2],
        [lonDeg, latDeg2],
        [lonDeg, latDeg]
      ];
    };

    const onVisualizationDialogOpened = () => {
      //console.log('对话框已打开事件触发');
      // 在对话框打开后调整地图尺寸
      setTimeout(() => {
        if (visualizationMap) {
          //console.log('对话框打开后更新地图尺寸');
          visualizationMap.updateSize();
        }
      }, 200);
    };

    const showCacheGrid = ref(true);
    const showCachePoints = ref(true);

    const toggleCacheGrid = () => {
      showCacheGrid.value = !showCacheGrid.value;
      if (visualizationMap && visualizationMap.dataLayer) {
        visualizationMap.dataLayer.setVisible(showCacheGrid.value);
        console.log('缓存数据可见性:', showCacheGrid.value);
      }
    };

    const toggleCachePoints = () => {
      showCachePoints.value = !showCachePoints.value;
      if (visualizationMap && visualizationMap.pointLayer) {
        visualizationMap.pointLayer.setVisible(showCachePoints.value);
        //console.log('缓存点位可见性:', showCachePoints.value);
      }
    };

    const resetMapView = () => {
      if (visualizationMap) {
        const layer = currentVisualizationLayer.value;
        if (layer && layer.tiles && layer.tiles.length > 0) {
          const tileBounds = calculateTileBounds(layer.tiles);
          if (tileBounds.extent) {
            const transformedExtent = transformExtent(
              tileBounds.extent, 
              'EPSG:4326', 
              'EPSG:3857'
            );
            visualizationMap.getView().fit(transformedExtent, {
              padding: [50, 50, 50, 50],
              duration: 1000,
              maxZoom: 15
            });
            //console.log('重置视图到瓦片范围');
          } else {
            visualizationMap.getView().setCenter(fromLonLat([104.06, 30.67]));
            visualizationMap.getView().setZoom(10);
            //console.log('重置视图到成都默认位置');
          }
        } else {
          visualizationMap.getView().setCenter(fromLonLat([104.06, 30.67]));
          visualizationMap.getView().setZoom(10);
          //console.log('重置视图到成都默认位置');
        }
      }
    };

    const switchToTestData = () => {
      if (visualizationMap && visualizationMap.testLayer) {
        const isVisible = visualizationMap.testLayer.getVisible();
        visualizationMap.testLayer.setVisible(!isVisible);
        //console.log('测试数据可见性:', !isVisible);
        ElMessage.info(isVisible ? '隐藏测试数据' : '显示测试数据');
      }
    };

    // 监听配置变化，自动更新瓦片数量估算
    watch(() => [cacheConfig.minZoom, cacheConfig.maxZoom, cacheConfig.selectedBounds], 
      () => {
        updateEstimatedTileCount();
      }, 
      { deep: true }
    );

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
      cacheVisualizationVisible,
      currentVisualizationLayer,
      // 新增的缓存配置相关
      cacheConfigVisible,
      currentCacheLayer,
      cacheConfig,
      currentMapZoom,
      estimatedTileCount,
      canStartCache,
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
      generateTestData,
      stopCacheOperation,
      handleExpandChange,
      formatFileSize,
      formatTimeAgo,
      visualizeCache,
      onVisualizationDialogOpened,
      // 新增的方法
      onCacheConfigDialogOpened,
      startCacheWithConfig,
      updateEstimatedTileCount,
      showCacheGrid,
      showCachePoints,
      toggleCacheGrid,
      toggleCachePoints,
      resetMapView
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
  height: 500px;
}

.cache-config-panel {
  display: flex;
  height: 100%;
  gap: 16px;
}

.config-left {
  width: 300px;
  flex-shrink: 0;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 6px;
}

.config-left h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-actions {
  margin-top: 20px;
  display: flex;
  gap: 8px;
}

.config-right {
  flex: 1;
  display: flex;
  flex-direction: column;
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
#cache-config-map,
#cache-visualization-map {
  width: 100%;
  height: 100%;
  border-radius: 4px;
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