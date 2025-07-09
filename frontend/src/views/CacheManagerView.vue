<template>
  <div class="cache-manager">
    <!-- 工具栏 -->
    <div class="cache-toolbar">
      <div class="toolbar-left">
        <el-button type="success" size="small" @click="updateScenesFromBackend" :loading="isUpdatingScenes">
          <i class="el-icon-refresh-right"></i> 更新场景
        </el-button>
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
          style="display: inline-flex; align-items: center;"
        >
          <el-button type="info" size="small">
            <i class="el-icon-upload2"></i> 导入
          </el-button>
        </el-upload>
      </div>

      <!-- 移动端搜索切换按钮 -->
      <div class="mobile-search-toggle" @click="toggleMobileSearch">
        <i class="el-icon-search toggle-icon" :class="{ 'rotated': mobileSearchExpanded }"></i>
        <span class="toggle-text">搜索筛选</span>
        <div class="search-summary" v-if="!mobileSearchExpanded && hasActiveFilters">
          <el-tag size="small" type="primary">{{ getActiveFiltersText() }}</el-tag>
        </div>
      </div>

      <!-- 搜索筛选区域 -->
      <div class="search-filters" :class="{ 'mobile-collapsed': !mobileSearchExpanded }">
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
      <!-- 移动端卡片布局 -->
      <div class="mobile-cache-cards">
        <div v-for="row in filteredCacheData" :key="row.sceneId + '_' + row.layerId" class="mobile-cache-card">
          <!-- 卡片头部 -->
          <div class="mobile-cache-card-header">
            <div class="mobile-cache-title">
              <div class="mobile-scene-name">{{ row.sceneName }}</div>
              <div class="mobile-layer-name">{{ row.layerName }}</div>
            </div>
            <div class="mobile-cache-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click="startLayerCache(row)"
                :disabled="row.originalLayer && row.originalLayer.wms_url"
              >
                缓存
              </el-button>
              <el-button 
                type="danger" 
                size="small" 
                @click="deleteLayerCache(row)"
                :disabled="(row.originalLayer && row.originalLayer.wms_url) || (!row.tiles || row.tiles.length === 0)"
              >
                删除
              </el-button>
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="mobile-cache-info">
            <div class="mobile-info-row">
              <div class="mobile-info-item">
                <span class="mobile-info-label">服务类型</span>
                <span class="mobile-info-value">{{ row.originalLayer && row.originalLayer.service_type ? row.originalLayer.service_type : row.layerType }}</span>
              </div>
              <div class="mobile-info-item">
                <span class="mobile-info-label">缓存状态</span>
                <span class="mobile-info-value">
                  <el-tag 
                    v-if="row.originalLayer && row.originalLayer.wms_url"
                    size="small" 
                    type="warning"
                  >
                    不缓存
                  </el-tag>
                  <el-tag 
                    v-else
                    size="small" 
                    :type="row.tiles && row.tiles.length > 0 ? 'success' : 'info'"
                  >
                    {{ row.tiles && row.tiles.length > 0 ? '已缓存' : '未缓存' }}
                  </el-tag>
                </span>
              </div>
            </div>
            <div class="mobile-info-row">
              <div class="mobile-info-item">
                <span class="mobile-info-label">瓦片数</span>
                <span class="mobile-info-value">
                  <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
                  <span v-else-if="row.tiles && row.tiles.length > 0">{{ row.tiles.length }}</span>
                  <span v-else class="no-data">-</span>
                </span>
              </div>
              <div class="mobile-info-item">
                <span class="mobile-info-label">大小</span>
                <span class="mobile-info-value">
                  <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
                  <span v-else-if="row.totalSize > 0">{{ formatFileSize(row.totalSize) }}</span>
                  <span v-else class="no-data">-</span>
                </span>
              </div>
            </div>
            <div class="mobile-info-row">
              <div class="mobile-info-item">
                <span class="mobile-info-label">层级</span>
                <span class="mobile-info-value">
                  <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
                  <span v-else-if="Array.isArray(row.zoomLevels) && row.zoomLevels.length > 0">
                    {{ row.zoomLevels.length === 1 ? row.zoomLevels[0] : `${row.zoomLevels[0]}-${row.zoomLevels[row.zoomLevels.length - 1]}` }}
                  </span>
                  <span v-else class="no-data">-</span>
                </span>
              </div>
              <div class="mobile-info-item">
                <span class="mobile-info-label">边界框</span>
                <span class="mobile-info-value">
                  <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
                  <span v-else-if="Array.isArray(row.bounds)">
                    {{ row.bounds.map(n => n.toFixed(2)).join(', ') }}
                  </span>
                  <span v-else class="no-data">{{ row.bounds }}</span>
                </span>
              </div>
            </div>
          </div>

          <!-- 瓦片详情 -->
          <div v-if="row.tiles && row.tiles.length > 0 && !row.originalLayer?.wms_url" class="mobile-tiles-section">
            <div class="mobile-tiles-header" @click="toggleTileDetails(row)">
              <span class="mobile-tiles-title">瓦片详情 ({{ row.tiles.length }} 个)</span>
              <i class="el-icon-arrow-down" :class="{ 'rotated': row.tilesExpanded }"></i>
            </div>
            <div v-if="row.tilesExpanded" class="mobile-tiles-content">
              <div v-for="tile in row.tiles.slice(0, 5)" :key="`${tile.zoomLevel}_${tile.tileX}_${tile.tileY}`" class="mobile-tile-item">
                <div class="mobile-tile-info">
                  <span class="mobile-tile-coord">{{ tile.zoomLevel }}/{{ tile.tileX }}/{{ tile.tileY }}</span>
                  <span class="mobile-tile-size">{{ formatFileSize(tile.size) }}</span>
                  <span class="mobile-tile-time">{{ new Date(tile.timestamp).toLocaleString() }}</span>
                </div>
                <div class="mobile-tile-actions">
                  <el-button size="small" @click="previewTile(tile)">预览</el-button>
                  <el-button size="small" type="danger" @click="deleteTile(tile)">删除</el-button>
                </div>
              </div>
              <div v-if="row.tiles.length > 5" class="mobile-tiles-more">
                还有 {{ row.tiles.length - 5 }} 个瓦片...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 桌面端表格布局 -->
      <div class="desktop-cache-table">
        <el-table 
          :data="filteredCacheData" 
          size="small"
          stripe
          :row-key="row => row.sceneId + '_' + row.layerId"
          :expand-row-keys="expandedRowKeys"
          :row-class-name="({ row }) => row.originalLayer && row.originalLayer.wms_url ? 'wms-layer-row' : ''"
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
                v-if="row.originalLayer && row.originalLayer.wms_url"
                size="small" 
                type="warning"
              >
                不缓存
              </el-tag>
              <el-tag 
                v-else
                size="small" 
                :type="row.tiles && row.tiles.length > 0 ? 'success' : 'info'"
              >
                {{ row.originalLayer && row.originalLayer.wms_url ? '不能缓存' : (row.tiles && row.tiles.length > 0 ? '已缓存' : '未缓存') }}
              </el-tag>
            </template>
          </el-table-column>
          
          <!-- 瓦片数量 -->
          <el-table-column label="瓦片数" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
              <span v-else-if="row.tiles && row.tiles.length > 0">{{ row.tiles.length }}</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>
          
          <!-- 缓存大小 -->
          <el-table-column label="大小" width="90" align="center">
            <template #default="{ row }">
              <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
              <span v-else-if="row.totalSize > 0">{{ formatFileSize(row.totalSize) }}</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>
          
          <!-- 缩放层级 -->
          <el-table-column label="层级" width="120" align="center">
            <template #default="{ row }">
              <span class="zoom-levels">
                <template v-if="row.originalLayer && row.originalLayer.wms_url">N/A</template>
                <template v-else-if="Array.isArray(row.zoomLevels) && row.zoomLevels.length > 0">
                  {{ row.zoomLevels.length === 1 ? row.zoomLevels[0] : `${row.zoomLevels[0]}-${row.zoomLevels[row.zoomLevels.length - 1]}` }}
                </template>
                <template v-else>-</template>
              </span>
            </template>
          </el-table-column>
          
          <!-- 边界框 -->
          <el-table-column label="边界框" min-width="180" align="center">
            <template #default="{ row }">
              <span v-if="row.originalLayer && row.originalLayer.wms_url" class="no-data">N/A</span>
              <span v-else-if="Array.isArray(row.bounds)">
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
                :disabled="row.originalLayer && row.originalLayer.wms_url"
                :title="row.originalLayer && row.originalLayer.wms_url ? 'WMS图层不支持缓存' : '缓存图层'"
              >
                <i class="el-icon-download"></i> 缓存
              </el-button>              
              <el-button 
                type="danger" 
                size="small" 
                @click="deleteLayerCache(row)"
                :disabled="(row.originalLayer && row.originalLayer.wms_url) || (!row.tiles || row.tiles.length === 0)"
                :title="row.originalLayer && row.originalLayer.wms_url ? 'WMS图层不支持缓存操作' : (!row.tiles || row.tiles.length === 0) ? '无缓存数据可删除' : '删除缓存'"
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
      :title="isMobile ? '' : '图层缓存配置'" 
      v-model="cacheConfigVisible" 
      :width="isMobile ? '100%' : '90%'"
      :top="isMobile ? '0' : '5vh'"
      :close-on-click-modal="false"
      custom-class="cache-config-dialog"
      destroy-on-close
      @opened="onCacheConfigDialogOpened"
      @close="onCacheConfigDialogClosed"
    >
      <div class="cache-config-content">
        <!-- 桌面端布局 -->
        <div class="cache-config-panel desktop-layout">
          <div class="config-left">
            <h4>{{ currentCacheLayer.layerName }}</h4>
            <div class="config-form">
              <el-form label-width="120px" size="small">
                <el-form-item label="缩放级别">
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
            <div id="cache-config-map-desktop"></div>
          </div>
        </div>
        
        <!-- 移动端布局 -->
        <div class="cache-config-panel mobile-layout">
          <!-- 顶部信息栏 -->
          <div class="mobile-map-info-bar">
            <span class="mobile-layer-title">{{ currentCacheLayer.layerName }}</span>
            <span class="mobile-zoom-info">{{ currentMapZoom }}</span>
            <span class="mobile-cache-status-badge" :class="{ 'status-enabled': currentLayerCacheEnabled, 'status-disabled': !currentLayerCacheEnabled }">
              <i class="el-icon-circle-check" v-if="currentLayerCacheEnabled"></i>
              <i class="el-icon-circle-close" v-else></i>
            </span>
            <button class="mobile-map-close-btn" @click="cacheConfigVisible = false">
              <i class="el-icon-close"></i>
            </button>
          </div>
          <!-- 地图全屏区域 -->
          <div class="mobile-map-fullscreen">
            <div id="cache-config-map-mobile"></div>
            <!-- 缓存开关可选，极简悬浮 -->
            <div class="mobile-map-fab">
              <el-switch
                v-model="currentLayerCacheEnabled"
                @change="toggleLayerCache"
                active-text="开启"
                inactive-text="关闭"
                active-color="#13ce66"
                inactive-color="#ff4949"
              />
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    

    <!-- 瓦片预览对话框 -->
    <el-dialog 
      v-model="tilePreviewVisible" 
      title="瓦片预览" 
      :width="isMobile ? '90%' : '400px'"
      :top="isMobile ? '10vh' : '15vh'"
      custom-class="tile-preview-dialog"
    >
      <div v-if="tileImageUrl">
        <img :src="tileImageUrl" style="max-width:100%;" />
      </div>
      <div v-else>
        <span>该瓦片不是图片类型或无法预览。</span>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import gisApi from '@/api/gis.js';
import { formatFileSize, formatTimeAgo, SimpleCacheService, TileCacheService, getGlobalSceneDataCacheService } from '@/services/tileCache';

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
    const isUpdatingScenes = ref(false); // 更新场景图层的loading状态
    const mobileSearchExpanded = ref(false); // 移动端搜索展开状态
    
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

    // 缓存服务实例
    let tileCacheService = null;
    let dataCacheService = null;
    let sceneDataCacheService = null;

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

    const initCacheService = async () => {
      try {
        tileCacheService = new TileCacheService({
          maxCacheSize: 500 * 1024 * 1024, // 500MB
          maxCacheAge: 7 * 24 * 60 * 60 * 1000 // 7天
        });

        dataCacheService = new SimpleCacheService(tileCacheService, gisApi);
        
        // 初始化场景数据缓存服务
        sceneDataCacheService = getGlobalSceneDataCacheService();
        
        // 设置进度回调
        dataCacheService.setProgressCallback((progress) => {
          cacheProgress.current = progress.current;
          cacheProgress.total = progress.total;
          cacheProgress.percent = progress.percent;
          cacheProgress.message = progress.message;
        });

        //console.log('缓存服务初始化成功');
        
        // 优先从IndexedDB加载场景和图层数据
        await loadScenesFromCache();
        await refreshCacheData();
      } catch (error) {
        console.error('初始化缓存服务失败:', error);
        ElMessage.error('初始化缓存服务失败: ' + error.message);
      }
    };

    // 从缓存加载场景数据，如果过期则从后端更新
    const loadScenesFromCache = async () => {
      try {
        // 检查缓存是否过期
        const isExpired = await sceneDataCacheService.isDataExpired('scenes_last_update');
        
        if (isExpired) {
          console.log('场景数据已过期，从后端更新...');
          await updateScenesFromBackend();
        } else {
          console.log('从缓存加载场景数据...');
          const cachedScenes = await sceneDataCacheService.getCachedScenes();
          sceneList.value = cachedScenes || [];
        }
      } catch (error) {
        console.error('从缓存加载场景数据失败:', error);
        ElMessage.warning('加载缓存数据失败，尝试从服务器获取...');
        await loadScenes(); // 回退到原来的方式
      }
    };

    // 手动从后端更新场景图层数据
    const updateScenesFromBackend = async () => {
      if (isUpdatingScenes.value) {
        ElMessage.warning('正在更新中，请稍候...');
        return;
      }

      isUpdatingScenes.value = true;
      try {
        ElMessage.info('正在从服务器更新场景图层数据...');
        
        // 1. 获取场景列表
        const scenesResponse = await gisApi.getScenes();
        const scenes = scenesResponse.data?.scenes || scenesResponse.data || [];
        
        // 2. 缓存场景列表
        await sceneDataCacheService.cacheScenes(scenes);
        sceneList.value = scenes;
        
        // 3. 获取并缓存每个场景的图层数据
        for (const scene of scenes) {
          try {
            const sceneResponse = await gisApi.getScene(scene.id);
            const layers = sceneResponse.data?.layers || [];
            await sceneDataCacheService.cacheSceneLayers(scene.id, layers);
            
            // 获取并缓存图层边界
            for (const layer of layers) {
              try {
                const layerId = layer.layer_id || layer.id;
                const sceneLayerId = layer.scene_layer_id;
                if (sceneLayerId) {
                  const boundsResp = await gisApi.getSceneLayerBounds(sceneLayerId);
                  let bounds = null;
                  if (boundsResp.data && boundsResp.data.bbox) {
                    bounds = boundsResp.data.bbox;
                  } else if (boundsResp.bbox) {
                    bounds = boundsResp.bbox;
                  } else if (Array.isArray(boundsResp) && boundsResp.length === 4) {
                    bounds = boundsResp;
                  }
                  if (bounds && Array.isArray(bounds) && bounds.length === 4) {
                    await sceneDataCacheService.cacheLayerBounds(layerId, bounds);
                  } else if (bounds && typeof bounds === 'object' && 'minx' in bounds) {
                    const normalizedBounds = [bounds.minx, bounds.miny, bounds.maxx, bounds.maxy];
                    await sceneDataCacheService.cacheLayerBounds(layerId, normalizedBounds);
                  }
                }
              } catch (boundsError) {
                console.warn(`获取图层 ${layer.layer_name} 边界失败:`, boundsError);
              }
            }
          } catch (sceneError) {
            console.warn(`获取场景 ${scene.name} 图层失败:`, sceneError);
          }
        }
        
        ElMessage.success(`成功更新 ${scenes.length} 个场景的数据到缓存`);
        
        // 重新加载页面数据
        await refreshCacheData();
        
      } catch (error) {
        console.error('更新场景图层数据失败:', error);
        ElMessage.error('更新失败: ' + error.message);
      } finally {
        isUpdatingScenes.value = false;
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
        
        // 1. 优先从缓存获取场景列表
        let scenes = [];
        try {
          const cachedScenes = await sceneDataCacheService.getCachedScenes();
          if (cachedScenes && cachedScenes.length > 0) {
            scenes = cachedScenes;
            console.log('使用缓存的场景数据');
          } else {
            // 缓存为空，从后端获取
            const scenesResponse = await gisApi.getScenes();
            scenes = scenesResponse.data?.scenes || scenesResponse.data || [];
            await sceneDataCacheService.cacheScenes(scenes);
            console.log('从后端获取场景数据并缓存');
          }
        } catch (cacheError) {
          console.warn('读取缓存场景数据失败，从后端获取:', cacheError);
          const scenesResponse = await gisApi.getScenes();
          scenes = scenesResponse.data?.scenes || scenesResponse.data || [];
        }
        
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
            // 优先从缓存获取场景图层
            let layers = [];
            try {
              const cachedLayers = await sceneDataCacheService.getCachedSceneLayers(scene.id);
              if (cachedLayers && cachedLayers.length > 0) {
                layers = cachedLayers;
                console.log(`使用缓存的场景 ${scene.id} 图层数据`);
              } else {
                // 缓存为空，从后端获取
                const sceneResponse = await gisApi.getScene(scene.id);
                layers = sceneResponse.data?.layers || [];
                await sceneDataCacheService.cacheSceneLayers(scene.id, layers);
                console.log(`从后端获取场景 ${scene.id} 图层数据并缓存`);
              }
            } catch (layerCacheError) {
              console.warn(`读取缓存场景 ${scene.id} 图层数据失败，从后端获取:`, layerCacheError);
              const sceneResponse = await gisApi.getScene(scene.id);
              layers = sceneResponse.data?.layers || [];
            }
            
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
            // 优先从缓存获取边界
            const cachedBounds = await sceneDataCacheService.getCachedLayerBounds(layer.sceneLayerId);
            if (cachedBounds) {
              layer.bounds = cachedBounds;
              continue;
            }
            
            // 缓存中没有，从后端获取
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
              await sceneDataCacheService.cacheLayerBounds(layer.sceneLayerId, bounds);
            } else if (bounds && typeof bounds === 'object' && 'minx' in bounds) {
              const normalizedBounds = [bounds.minx, bounds.miny, bounds.maxx, bounds.maxy];
              layer.bounds = normalizedBounds;
              await sceneDataCacheService.cacheLayerBounds(layer.sceneLayerId, normalizedBounds);
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
      // 检查是否为WMS图层
      if (layer.originalLayer && layer.originalLayer.wms_url) {
        ElMessage.warning('WMS图层不支持缓存操作');
        return;
      }
      
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
      // 检查是否为WMS图层
      if (layer.originalLayer && layer.originalLayer.wms_url) {
        ElMessage.warning('WMS图层不支持缓存功能');
        return;
      }
      
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
      // 移动端需要更长的延迟时间确保布局完成
      const delay = isMobile.value ? 500 : 300;
      setTimeout(() => {
        console.log(`对话框打开，准备初始化地图 - 移动端: ${isMobile.value}`);
        initConfigMap();
      }, delay);
    };

    // 缓存配置对话框关闭事件
    const onCacheConfigDialogClosed = async () => {
      // 清理地图实例
      if (configMap) {
        configMap.setTarget(null);
        configMap = null;
        console.log('地图实例已清理');
      }
      await refreshCacheData();
    };

    // 初始化配置地图
    const initConfigMap = () => {
      // 根据屏幕尺寸选择正确的地图容器
      const mapContainerId = isMobile.value ? 'cache-config-map-mobile' : 'cache-config-map-desktop';
      const mapContainer = document.getElementById(mapContainerId);
      if (!mapContainer) {
        console.error(`配置地图容器未找到: ${mapContainerId}`);
        return;
      }

      // 检查容器尺寸
      const rect = mapContainer.getBoundingClientRect();
      console.log(`地图容器尺寸 - 宽度: ${rect.width}, 高度: ${rect.height}`);
      
      if (rect.width === 0 || rect.height === 0) {
        console.warn('地图容器尺寸为0，延迟再次尝试');
        setTimeout(() => initConfigMap(), 200);
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
        target: mapContainerId,
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

      // 强制更新地图尺寸，移动端需要更长延迟
      const delay = isMobile.value ? 300 : 100;
      setTimeout(() => {
        if (configMap) {
          configMap.updateSize();
          console.log(`地图初始化完成 - 容器: ${mapContainerId}, 移动端: ${isMobile.value}`);
          
          // 移动端再次更新尺寸
          if (isMobile.value) {
            setTimeout(() => {
              configMap.updateSize();
              console.log('移动端地图尺寸二次更新完成');
            }, 100);
          }
        }
      }, delay);
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
      expandedRowKeys.value = expandedRows.map(r => r.sceneId + '_' + r.layerId);
    };

    const toggleLayerCache = () => {
      // 显示状态反馈
      if (currentLayerCacheEnabled.value) {
        ElMessage.success(`图层 "${currentCacheLayer.value.layerName}" 缓存已开启`);
      } else {
        ElMessage.warning(`图层 "${currentCacheLayer.value.layerName}" 缓存已关闭`);
      }
      
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
      
      console.log(`图层 ${currentCacheLayer.value.layerId} 缓存状态已更新: ${currentLayerCacheEnabled.value ? '开启' : '关闭'}`);
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

    const toggleMobileSearch = () => {
      mobileSearchExpanded.value = !mobileSearchExpanded.value;
    };

    const hasActiveFilters = computed(() => {
      return selectedSceneFilter.value || cacheSearchText.value;
    });

    const getActiveFiltersText = () => {
      const filters = [];
      if (selectedSceneFilter.value) {
        const scene = sceneList.value.find(s => s.id === selectedSceneFilter.value);
        if (scene) {
          filters.push(`场景: ${scene.name}`);
        }
      }
      if (cacheSearchText.value) {
        filters.push(`搜索: "${cacheSearchText.value}"`);
      }
      return filters.join('，');
    };

    const toggleTileDetails = (row) => {
      // 确保响应式属性存在
      if (!('tilesExpanded' in row)) {
        row.tilesExpanded = false;
      }
      row.tilesExpanded = !row.tilesExpanded;
    };

    // 移动端检测
    const windowWidth = ref(window.innerWidth);
    const isMobile = computed(() => {
      return windowWidth.value <= 768;
    });

    // 监听窗口大小变化
    const handleResize = () => {
      windowWidth.value = window.innerWidth;
    };

    onMounted(() => {
      initCacheService();
      window.addEventListener('resize', handleResize);
    });

    // 清理事件监听器
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize);
    });

    return {
      selectedSceneFilter,
      sceneList,
      cacheSearchText,
      expandedRowKeys,
      isUpdatingScenes,
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
      onCacheConfigDialogClosed,
      enableLayerCache,
      disableLayerCache,
      updateScenesFromBackend,
      toggleMobileSearch,
      mobileSearchExpanded,
      hasActiveFilters,
      getActiveFiltersText,
      toggleTileDetails,
      isMobile
    };
  }
};
</script>

<style scoped>
.cache-manager {
  padding: 16px;
  min-height: 100vh;
  background-color: #f5f5f5;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
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
  align-items: center;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

/* 确保上传按钮与其他按钮对齐 */
.toolbar-left .el-upload {
  display: inline-flex !important;
  align-items: center;
  vertical-align: top;
  height: auto;

}

.toolbar-left .el-upload .el-button {
  margin: 0;
  vertical-align: top;
  height: small;
  line-height: normal;
}

/* 确保所有工具栏按钮的基础样式一致 */
.toolbar-left .el-button {
  vertical-align: top;
  line-height: small;
}

.mobile-search-toggle {
  display: none; /* 默认隐藏移动端搜索切换按钮 */
  cursor: pointer;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f5f7fa;
  color: #606266;
  font-size: 14px;
  align-items: center;
  gap: 8px;
  margin-left: 10px; /* 与搜索框保持一定间距 */
  transition: all 0.3s ease;
}

.mobile-search-toggle:hover {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}

.mobile-search-toggle .toggle-icon {
  transition: transform 0.3s ease;
}

.mobile-search-toggle .rotated {
  transform: rotate(180deg);
}

.mobile-search-toggle .toggle-text {
  flex-grow: 1;
}

.search-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-left: 10px; /* 与搜索框保持一定间距 */
}

.search-filters.mobile-collapsed {
  display: none; /* 移动端折叠时隐藏搜索筛选区域 */
}

/* 确保桌面端搜索筛选区域始终显示 */
@media (min-width: 769px) {
  .search-filters {
    display: flex !important;
    opacity: 1 !important;
    visibility: visible !important;
    max-height: none !important;
  }
  
  .mobile-search-toggle {
    display: none !important;
  }
}

.cache-stats-compact {
  display: flex;
  justify-content: center;
  align-items: center;
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
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
  line-height: 1.4;
}

.cache-content {
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 16px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-cache-cards {
  display: none; /* 默认隐藏移动端卡片布局 */
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); /* 自适应卡片宽度 */
  gap: 16px;
  margin-bottom: 16px;
  will-change: transform;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.mobile-cache-card {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.mobile-cache-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f0f0f0;
  border-bottom: 1px solid #eee;
}

.mobile-cache-title {
  display: flex;
  flex-direction: column;
}

.mobile-scene-name {
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.mobile-layer-name {
  font-size: 12px;
  color: #666;
}

.mobile-cache-actions {
  display: flex;
  gap: 8px;
}

.mobile-cache-info {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #555;
}

.mobile-info-item {
  display: flex;
  flex-direction: column;
}

.mobile-info-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}

.mobile-info-value {
  font-weight: 500;
  color: #333;
}

.mobile-tiles-section {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background-color: #f9f9f9;
}

.mobile-tiles-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-bottom: 1px dashed #eee;
  border-radius: 4px;
  transition: all 0.3s ease;
  background-color: #f9f9f9;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.mobile-tiles-header:hover {
  background-color: #f0f0f0;
}

.mobile-tiles-header:active {
  background-color: #e8e8e8;
  transform: scale(0.98);
}

.mobile-tiles-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.mobile-tiles-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px; /* 控制展开内容的最大高度 */
  overflow-y: auto;
  padding-right: 10px; /* 滚动条占位 */
  animation: expandIn 0.3s ease-out;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

@keyframes expandIn {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 200px;
  }
}

/* WebKit滚动条样式 */
.mobile-tiles-content::-webkit-scrollbar {
  width: 4px;
}

.mobile-tiles-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.mobile-tiles-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.mobile-tiles-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.mobile-tile-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.mobile-tile-info {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #666;
}

.mobile-tile-coord {
  font-weight: 500;
  color: #333;
}

.mobile-tile-size {
  font-size: 11px;
  color: #999;
}

.mobile-tile-time {
  font-size: 11px;
  color: #999;
}

.mobile-tile-actions {
  display: flex;
  gap: 8px;
}

.mobile-tiles-more {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding-top: 8px;
}

.desktop-cache-table {
  margin-top: 16px;
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

#cache-config-map-desktop {
  width: 100%;
  height: 100%;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  background: #f8f9fa;
}

#cache-config-map-mobile {
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

/* 桌面端布局 */
.desktop-layout {
  display: flex;
}

.mobile-layout {
  display: none;
}

/* 移动端布局 */
@media (max-width: 768px) {
  .desktop-layout {
    display: none !important;
  }
  
  .mobile-layout {
    display: flex !important;
    flex-direction: column;
    height: 100%;
  }
  
  /* 顶部拖拽条和标题栏 */
  .mobile-sheet-header {
    padding: 12px 20px 8px;
    background: #ffffff;
    border-radius: 20px 20px 0 0;
    flex-shrink: 0;
  }
  
  .mobile-drag-handle {
    width: 40px;
    height: 4px;
    background: #e1e4e8;
    border-radius: 2px;
    margin: 0 auto 16px;
    transition: background-color 0.2s ease;
  }
  
  .mobile-drag-handle:active {
    background: #c0c4cc;
  }
  
  .mobile-title-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .mobile-dialog-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    letter-spacing: -0.01em;
  }
  
  .mobile-close-btn {
    padding: 8px !important;
    margin: 0 !important;
    color: #909399 !important;
    font-size: 18px !important;
    background: #f5f7fa !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    min-height: 36px !important;
    transition: all 0.2s ease !important;
  }
  
  .mobile-close-btn:hover {
    background: #ecf5ff !important;
    color: #409eff !important;
  }
  
  .mobile-close-btn:active {
    transform: scale(0.95) !important;
  }
  
  /* 图层信息卡片 */
  .mobile-layer-info-card {
    margin: 0 20px 16px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 12px;
    border: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }
  
  .mobile-layer-details {
    flex: 1;
    min-width: 0;
  }
  
  .mobile-layer-title {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .mobile-layer-meta {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .mobile-zoom-info {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    color: #606266;
  }
  
  .mobile-zoom-info i {
    color: #409eff;
  }
  
  .mobile-cache-status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 500;
  }
  
  .mobile-cache-status-badge.status-enabled {
    color: #67c23a;
  }
  
  .mobile-cache-status-badge.status-disabled {
    color: #f56c6c;
  }
  
  .mobile-cache-toggle {
    flex-shrink: 0;
    padding-top: 4px;
  }
  
  .mobile-cache-toggle :deep(.el-switch) {
    height: 24px;
  }
  
  .mobile-cache-toggle :deep(.el-switch__core) {
    min-width: 44px;
    height: 24px;
    border-radius: 12px;
  }
  
  .mobile-cache-toggle :deep(.el-switch__action) {
    width: 20px;
    height: 20px;
    top: 2px;
  }
  
  .mobile-cache-toggle :deep(.el-switch__label) {
    color: #606266;
    font-size: 12px;
    font-weight: 500;
  }
  
  .mobile-cache-toggle :deep(.el-switch__label.is-active) {
    color: #13ce66;
  }
  
  /* 地图区域 */
  .mobile-map-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin: 0 20px 20px;
    min-height: 0;
  }
  
  .mobile-map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .mobile-map-header h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
  
  .mobile-map-tips {
    font-size: 12px;
    color: #909399;
  }
  
  .mobile-config-map {
    flex: 1;
    min-height: 280px;
    border-radius: 12px;
    overflow: hidden;
    background: #f8f9fa;
    border: 1px solid #e4e7ed;
    position: relative;
  }
  
  .mobile-config-map #cache-config-map-mobile {
    width: 100%;
    height: 100%;
    border-radius: 12px;
  }
  
  .mobile-config-map #cache-config-map-mobile .ol-viewport {
    border-radius: 12px;
  }
  
  .mobile-config-map #cache-config-map-mobile .ol-zoom {
    left: 12px;
    top: 12px;
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(8px);
    border-radius: 8px !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1) !important;
  }
  
  .mobile-config-map #cache-config-map-mobile .ol-attribution {
    right: 12px;
    bottom: 12px;
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(8px);
    border-radius: 6px !important;
    padding: 4px 8px !important;
    font-size: 11px !important;
  }
}

/* 瓦片预览对话框样式 */
:deep(.tile-preview-dialog) {
  .el-dialog__body {
    padding: 20px;
    text-align: center;
  }
  
  .el-dialog__body img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
    padding: 8px;
  }
  
  .cache-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    padding: 8px;
  }
  
  .toolbar-left {
    flex-wrap: nowrap;
    justify-content: space-between;
    align-items: center;
    gap: 4px;
    width: 100%;
    overflow-x: auto;
  }

  .toolbar-left .el-button {
    font-size: 10px;
    padding: 4px 6px;
    flex: 1;
    min-width: 60px;
    max-width: none;
    white-space: nowrap;
  }

  .toolbar-left .el-upload {
    flex: 1;
    min-width: 60px;
    max-width: none;
  }

  .toolbar-left .el-upload {
    display: inline-flex !important;
    align-items: center;
    vertical-align: top;
  }

  .toolbar-left .el-upload .el-button {
    width: 100%;
    margin: 0;
    vertical-align: top;
  }

  /* 移动端工具栏滚动条样式 */
  .toolbar-left::-webkit-scrollbar {
    height: 3px;
  }

  .toolbar-left::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 2px;
  }

  .toolbar-left::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 2px;
  }

  .toolbar-left::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
  }

  /* 移动端底部sheet对话框样式 */
  :deep(.cache-config-dialog) {
    .el-overlay {
      background-color: rgba(0, 0, 0, 0.4) !important;
    }
    
    .el-dialog__wrapper {
      display: flex !important;
      align-items: flex-end !important;
      justify-content: center !important;
    }
    
    .el-dialog {
      position: fixed !important;
      bottom: 0 !important;
      left: 0 !important;
      right: 0 !important;
      top: auto !important;
      margin: 0 !important;
      width: 100% !important;
      height: 85vh !important;
      max-width: none !important;
      max-height: 85vh !important;
      border-radius: 20px 20px 0 0 !important;
      box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15) !important;
      transform: translateY(0) !important;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .el-dialog__header {
      display: none !important;
    }
    
    .el-dialog__body {
      padding: 0 !important;
      height: 85vh !important;
      overflow: hidden !important;
      border-radius: 20px 20px 0 0 !important;
    }
    
    .cache-config-content {
      height: 100% !important;
      background: #ffffff !important;
      border-radius: 20px 20px 0 0 !important;
    }
    
    .mobile-layout {
      height: 100% !important;
      display: flex !important;
      flex-direction: column !important;
    }
  }

  :deep(.tile-preview-dialog) {
    .el-dialog {
      margin: 0 auto !important;
      width: 95% !important;
      max-width: none !important;
    }
    
    .el-dialog__body {
      padding: 15px !important;
    }
    
    .el-dialog__body img {
      max-width: 100% !important;
      height: auto !important;
    }
  }

  .mobile-search-toggle {
    display: flex !important;
    align-items: center;
    margin-left: 0;
    width: 100%;
    justify-content: space-between;
    padding: 10px 12px;
    background-color: #ffffff;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-search-toggle:hover {
    background-color: #f8f9fa;
    border-color: #409eff;
  }

  .mobile-search-toggle:active {
    background-color: #ecf5ff;
    transform: scale(0.98);
  }

  .mobile-search-toggle .toggle-icon {
    font-size: 16px;
    color: #409eff;
    transition: transform 0.3s ease;
  }

  .mobile-search-toggle .toggle-icon.rotated {
    transform: rotate(180deg);
  }

  .mobile-search-toggle .toggle-text {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    margin-left: 8px;
  }

  .mobile-search-toggle .search-summary {
    margin-left: auto;
  }

  .search-filters {
    overflow: hidden;
    transition: max-height 0.3s ease;
    max-height: 200px;
    flex-direction: column;
    gap: 8px;
    margin-left: 0;
    width: 100%;
  }

  .search-filters.mobile-collapsed {
    max-height: 0;
    opacity: 0;
    visibility: hidden;
  }

  .search-filters .toolbar-right {
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }

  .search-filters .el-select,
  .search-filters .el-input {
    width: 100% !important;
  }
  
  .cache-stats-compact {
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px;
  }
  
  .stat-item {
    min-width: 100px;
    font-size: 12px;
  }

  .stat-label {
    font-size: 11px;
  }

  .stat-value {
    font-size: 13px;
    font-weight: 600;
  }

  /* 移动端显示卡片布局 */
  .mobile-cache-cards {
    display: block !important;
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .mobile-cache-card {
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.08);
    margin-bottom: 10px;
    background: white;
    border: 1px solid #e1e4e8;
    transition: all 0.3s ease;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-cache-card:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
  }

  .mobile-cache-card:active {
    transform: translateY(0);
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.08);
  }

  .mobile-cache-card:last-child {
    margin-bottom: 0;
  }

  .mobile-cache-card-header {
    padding: 10px 12px;
  }

  .mobile-scene-name {
    font-size: 13px;
  }

  .mobile-layer-name {
    font-size: 11px;
  }

  .mobile-cache-actions {
    gap: 6px;
  }

  .mobile-cache-actions .el-button {
    font-size: 11px;
    padding: 4px 8px;
    min-height: 32px;
    border-radius: 4px;
    transition: all 0.2s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-cache-actions .el-button:active {
    transform: scale(0.95);
  }

  .mobile-cache-info {
    padding: 10px 12px;
    gap: 6px;
  }

  .mobile-info-row {
    font-size: 12px;
  }

  .mobile-info-label {
    font-size: 10px;
  }

  .mobile-info-value {
    font-size: 11px;
  }

  .mobile-tiles-section {
    padding: 10px 12px;
  }

  .mobile-tiles-title {
    font-size: 13px;
  }

  .mobile-tile-item {
    padding: 6px 8px;
  }

  .mobile-tile-info {
    font-size: 11px;
  }

  .mobile-tile-coord {
    font-size: 11px;
  }

  .mobile-tile-size,
  .mobile-tile-time {
    font-size: 10px;
  }

  .mobile-tile-actions .el-button {
    font-size: 10px;
    padding: 2px 6px;
    min-height: 28px;
    border-radius: 4px;
    transition: all 0.2s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-tile-actions .el-button:active {
    transform: scale(0.95);
  }

  /* 移动端隐藏桌面端表格 */
  .desktop-cache-table {
    display: none !important;
  }
  
  .expanded-content {
    padding: 10px;
  }

  /* 移动端标签样式优化 */
  .mobile-cache-info .el-tag {
    font-size: 10px !important;
    padding: 1px 4px !important;
    height: 16px !important;
    line-height: 14px !important;
    transform: scale(0.9);
  }
}

/* 超小屏幕适配 */
@media (max-width: 480px) {
  .cache-manager {
    padding: 6px;
  }

  .cache-toolbar {
    padding: 6px;
    gap: 6px;
    align-items: stretch;
  }

  .toolbar-left {
    gap: 2px;
    align-items: center;
    flex-wrap: nowrap;
    overflow-x: auto;
  }

  .toolbar-left .el-button {
    font-size: 9px;
    padding: 3px 4px;
    min-height: 28px;
    border-radius: 4px;
    transition: all 0.2s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    flex: 1;
    min-width: 45px;
    white-space: nowrap;
  }

  .toolbar-left .el-button:active {
    transform: scale(0.95);
  }

  .toolbar-left .el-upload {
    display: inline-flex !important;
    align-items: center;
    vertical-align: top;
    flex: 1;
    min-width: 45px;
  }

  .toolbar-left .el-upload .el-button {
    margin: 0;
    vertical-align: top;
    width: 100%;
    font-size: 9px;
    padding: 3px 4px;
    min-height: 28px;
    white-space: nowrap;
  }

  /* 超小屏幕工具栏滚动条样式 */
  .toolbar-left::-webkit-scrollbar {
    height: 2px;
  }

  .toolbar-left::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 1px;
  }

  .toolbar-left::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 1px;
  }

  .toolbar-left::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
  }

  .mobile-search-toggle {
    padding: 8px 10px;
  }

  .mobile-search-toggle .toggle-text {
    font-size: 13px;
  }

  .cache-stats-compact {
    gap: 6px;
    padding: 6px;
    align-items: center;
  }

  .stat-item {
    min-width: 80px;
    font-size: 11px;
    align-items: center;
    justify-content: center;
  }

  .stat-label {
    font-size: 10px;
  }

  .stat-value {
    font-size: 12px;
  }

  .mobile-cache-cards {
    gap: 8px;
  }

  .mobile-cache-card-header {
    padding: 8px 10px;
  }

  .mobile-scene-name {
    font-size: 12px;
  }

  .mobile-layer-name {
    font-size: 10px;
  }

  .mobile-cache-actions {
    gap: 4px;
  }

  .mobile-cache-actions .el-button {
    font-size: 10px;
    padding: 3px 6px;
    min-height: 30px;
    border-radius: 4px;
    transition: all 0.2s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-cache-actions .el-button:active {
    transform: scale(0.95);
  }

  .mobile-cache-info {
    padding: 8px 10px;
    gap: 4px;
  }

  .mobile-info-row {
    font-size: 11px;
  }

  .mobile-info-label {
    font-size: 9px;
  }

  .mobile-info-value {
    font-size: 10px;
  }

  .mobile-tiles-section {
    padding: 8px 10px;
  }

  .mobile-tiles-title {
    font-size: 12px;
  }

  .mobile-tile-item {
    padding: 4px 6px;
  }

  .mobile-tile-info {
    font-size: 10px;
  }

  .mobile-tile-coord {
    font-size: 10px;
  }

  .mobile-tile-size,
  .mobile-tile-time {
    font-size: 9px;
  }

  .mobile-tile-actions .el-button {
    font-size: 9px;
    padding: 2px 4px;
    min-height: 26px;
    border-radius: 4px;
    transition: all 0.2s ease;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  .mobile-tile-actions .el-button:active {
    transform: scale(0.95);
  }

  .mobile-cache-info .el-tag {
    font-size: 9px !important;
    padding: 1px 3px !important;
    height: 14px !important;
    line-height: 12px !important;
    transform: scale(0.85);
  }
  
  /* 超小屏幕缓存配置对话框适配 */
  :deep(.cache-config-dialog) {
    .el-dialog {
      height: 90vh !important;
      max-height: 90vh !important;
    }
    
    .el-dialog__body {
      height: 90vh !important;
    }
  }
  
  .mobile-sheet-header {
    padding: 8px 16px 6px !important;
  }
  
  .mobile-drag-handle {
    margin-bottom: 12px !important;
  }
  
  .mobile-dialog-title {
    font-size: 16px !important;
  }
  
  .mobile-close-btn {
    width: 32px !important;
    height: 32px !important;
    min-height: 32px !important;
    font-size: 16px !important;
  }
  
  .mobile-layer-info-card {
    margin: 0 16px 12px !important;
    padding: 12px !important;
    flex-direction: column !important;
    gap: 12px !important;
  }
  
  .mobile-layer-title {
    font-size: 15px !important;
  }
  
  .mobile-layer-meta {
    gap: 4px !important;
  }
  
  .mobile-zoom-info,
  .mobile-cache-status-badge {
    font-size: 13px !important;
  }
  
  .mobile-cache-toggle {
    align-self: flex-end !important;
    padding-top: 0 !important;
  }
  
  .mobile-cache-toggle :deep(.el-switch) {
    height: 22px !important;
  }
  
  .mobile-cache-toggle :deep(.el-switch__core) {
    min-width: 40px !important;
    height: 22px !important;
  }
  
  .mobile-cache-toggle :deep(.el-switch__action) {
    width: 18px !important;
    height: 18px !important;
  }
  
  .mobile-cache-toggle :deep(.el-switch__label) {
    font-size: 11px !important;
  }
  
  .mobile-map-section {
    margin: 0 16px 16px !important;
  }
  
  .mobile-map-header h4 {
    font-size: 15px !important;
  }
  
  .mobile-map-tips {
    font-size: 11px !important;
  }
  
  .mobile-config-map {
    min-height: 220px !important;
    border-radius: 10px !important;
  }
  
  .mobile-config-map #cache-config-map-mobile {
    border-radius: 10px !important;
  }
  
  .mobile-config-map #cache-config-map-mobile .ol-viewport {
    border-radius: 10px !important;
  }
  
  .mobile-config-map #cache-config-map-mobile .ol-zoom {
    left: 8px !important;
    top: 8px !important;
    border-radius: 6px !important;
  }
  
  .mobile-config-map #cache-config-map-mobile .ol-attribution {
    right: 8px !important;
    bottom: 8px !important;
    padding: 3px 6px !important;
    font-size: 10px !important;
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



/* 不能缓存的标签样式 */
.el-tag.el-tag--warning {
  background-color: #fdf6ec;
  border-color: #f5dab1;
  color: #e6a23c;
}

/* 移动端极简底部弹窗风格 */
@media (max-width: 768px) {
  .cache-config-panel.mobile-layout {
    position: relative;
    height: 100%;
    background: transparent;
    border-radius: 20px 20px 0 0;
    overflow: hidden;
    padding: 0;
  }
  .mobile-map-info-bar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 38px;
    background: rgba(255,255,255,0.92);
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 10px;
    padding: 0 12px;
    border-radius: 20px 20px 0 0;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }
  .mobile-layer-title {
    max-width: 40vw;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #222;
    font-weight: 600;
    font-size: 14px;
  }
  .mobile-zoom-info {
    color: #666;
    font-size: 13px;
  }
  .mobile-cache-status-badge {
    font-size: 15px;
    margin-left: 4px;
  }
  .mobile-cache-status-badge.status-enabled { color: #13ce66; }
  .mobile-cache-status-badge.status-disabled { color: #ff4949; }
  .mobile-map-close-btn {
    position: absolute;
    right: 8px;
    top: 6px;
    background: none;
    border: none;
    outline: none;
    color: #909399;
    font-size: 20px;
    z-index: 3;
    padding: 2px;
    border-radius: 50%;
    transition: background 0.2s;
  }
  .mobile-map-close-btn:active {
    background: #f2f2f2;
  }
  .mobile-map-fullscreen {
    position: absolute;
    top: 38px;
    left: 0; right: 0; bottom: 0;
    width: 100%; height: calc(100% - 38px);
    background: #f8f9fa;
    border-radius: 0 0 20px 20px;
    overflow: hidden;
  }
  .mobile-map-fullscreen #cache-config-map-mobile {
    width: 100%; height: 100%; border-radius: 0 0 20px 20px;
  }
  .mobile-map-fab {
    position: absolute;
    right: 16px;
    bottom: 18px;
    z-index: 10;
    background: rgba(255,255,255,0.95);
    border-radius: 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10);
    padding: 4px 12px;
    display: flex;
    align-items: center;
  }
  .mobile-map-fab :deep(.el-switch) {
    height: 24px;
  }
  .mobile-map-fab :deep(.el-switch__core) {
    min-width: 44px;
    height: 24px;
    border-radius: 12px;
  }
  .mobile-map-fab :deep(.el-switch__action) {
    width: 20px;
    height: 20px;
    top: 2px;
  }
  .mobile-map-fab :deep(.el-switch__label) {
    color: #606266;
    font-size: 12px;
    font-weight: 500;
  }
  .mobile-map-fab :deep(.el-switch__label.is-active) {
    color: #13ce66;
  }
}


</style>