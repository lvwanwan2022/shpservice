<template>
  <div class="map-view">
    <!-- 缓存进度对话框 -->
    <el-dialog 
      title="缓存数据加载中..." 
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
        <el-button @click="stopCacheLoading" :disabled="!cacheLoading">停止加载</el-button>
      </template>
    </el-dialog>

    <!-- 缓存查看对话框 -->
    <el-dialog 
      title="IndexedDB 缓存数据查看" 
      v-model="cacheViewerVisible" 
      width="80%"
      :close-on-click-modal="false"
      top="5vh"
    >
      <div class="cache-viewer">
        <!-- 工具栏 -->
        <div class="cache-toolbar">
          <div class="toolbar-left">
            <el-button type="primary" size="small" @click="refreshCacheData">
              <i class="el-icon-refresh"></i> 刷新数据
            </el-button>
            <el-button type="warning" size="small" @click="clearAllCache">
              <i class="el-icon-delete"></i> 清空缓存
            </el-button>
            <el-button type="success" size="small" @click="exportCacheData">
              <i class="el-icon-download"></i> 导出数据
            </el-button>
          </div>
          <div class="toolbar-right">
            <el-input
              v-model="cacheSearchText"
              placeholder="搜索图层ID或瓦片坐标"
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
        <div class="cache-stats">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ cacheStats.totalTiles }}</div>
                <div class="stat-label">总瓦片数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ formatFileSize(cacheStats.totalSize) }}</div>
                <div class="stat-label">总大小</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ cacheStats.layerCount }}</div>
                <div class="stat-label">图层数量</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ formatTimeAgo(cacheStats.lastUpdate) }}</div>
                <div class="stat-label">最后更新</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 图层分组 -->
        <div class="cache-layers">
          <el-collapse v-model="activeLayerGroups" accordion>
            <el-collapse-item 
              v-for="layer in filteredCacheData" 
              :key="layer.layerId" 
              :name="layer.layerId"
            >
              <template #title>
                <div class="layer-group-title">
                  <span class="layer-id">{{ layer.layerId }}</span>
                  <el-tag size="small" type="info">{{ layer.tiles.length }} 瓦片</el-tag>
                  <el-tag size="small" type="success">{{ formatFileSize(layer.totalSize) }}</el-tag>
                </div>
              </template>
              
              <!-- 瓦片列表 -->
              <div class="tiles-container">
                <el-table 
                  :data="layer.tiles" 
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
                  <el-table-column label="创建时间" width="150" align="center">
                    <template #default="scope">
                      {{ new Date(scope.row.timestamp).toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="120" align="center">
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
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredCacheData.length === 0" class="empty-cache">
          <i class="el-icon-box"></i>
          <p>暂无缓存数据</p>
        </div>
      </div>
    </el-dialog>

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
        </div>
      </div>
    </el-dialog>

    <!-- 主要内容区域 -->
    <div class="map-content">
      <!-- 左侧图层面板 -->
      <div class="layer-panel" :class="{ 'collapsed': layerPanelCollapsed }">
        <div class="panel-content" v-show="!layerPanelCollapsed">
          <div class="panel-header">
            <h3>图层管理</h3>
            <div class="header-right">
              <span class="layer-count">{{ (layersList || []).length }} 个图层</span>
              <!-- 缓存管理按钮 -->
              <el-button type="success" size="small" @click="startCacheLoading">
                <i class="el-icon-download"></i> 缓存加载
              </el-button>
              <el-button type="info" size="small" @click="showCacheViewer">
                <i class="el-icon-view"></i> 缓存查看
              </el-button>
              <el-button type="warning" size="small" @click="addTestCacheData">
                <i class="el-icon-plus"></i> 测试数据
              </el-button>
              <el-button type="primary" size="small" @click="showAddLayerDialog">
                <i class="el-icon-plus"></i> 添加图层
              </el-button>
              <!-- 面板切换按钮 -->
              <el-button 
                link 
                size="small" 
                @click="toggleLayerPanel"
                class="panel-toggle-btn"
                title="收起面板"
              >
                <span class="toggle-icon">《</span>
              </el-button>
            </div>
          </div>
          
          <!-- 场景选择 -->
          <div class="scene-selector">
            <el-select 
              v-model="selectedSceneId" 
              placeholder="选择场景" 
              @change="onSceneChange"
              style="width: 100%"
              size="small"
            >
              <el-option
                v-for="scene in sceneList"
                :key="scene.id"
                :label="scene.name"
                :value="scene.id"
              />
            </el-select>
          </div>
          
          <div class="panel-body">
            <!-- 新的图层卡片列表 -->
            <div class="layer-cards" v-if="layersList && layersList.length > 0">
              <div 
                v-for="(layer, index) in sortedLayersList" 
                :key="layer.id" 
                class="layer-card"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                  'invisible': !layer.visibility,
                  'dragging': draggingLayerId === layer.id
                }"
                draggable="true"
                @click="selectLayer(layer)"
                @dragstart="handleDragStart($event, layer, index)"
                @dragend="handleDragEnd"
                @dragover="handleDragOver($event, index)"
                @drop="handleDrop($event, index)"
              >
                <div class="layer-card-header">
                  <div class="layer-title">
                    <!-- 可见性控制checkbox -->
                    <el-checkbox 
                      v-model="layer.visibility" 
                      @change="toggleLayerVisibility(layer)"
                      @click.stop
                    ></el-checkbox>
                    <!-- 当前活动图层标识 -->
                    <i v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" 
                       class="el-icon-location active-indicator" 
                       title="当前活动图层"></i>
                    <span class="layer-name">{{ layer.layer_name }}</span>
                  </div>
                  <div class="layer-drag-handle">
                    <i class="el-icon-rank"></i>
                  </div>
                  <div class="layer-actions">
                    <!-- 缩放到图层范围 -->
                    <el-button 
                      link 
                      @click.stop="zoomToLayer(layer)"
                      class="zoom-btn"
                      title="缩放到图层范围"
                    >
                      <span>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <path d="M15.5 14h-.79l-.28-.27A6.5 6.5 0 1 0 13 15.5l.27.28v.79l5 4.99L19.49 20l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/>
                          <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
                        </svg>
                      </span>
                    </el-button>
                    
                    <!-- 样式设置 -->
                    <el-button 
                      link 
                      @click.stop="showStyleDialog(layer)"
                      class="style-btn"
                      title="样式设置"
                    >
                      <span>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
                        </svg>
                      </span>
                    </el-button>
                    
                    <!-- 删除图层 -->
                    <el-button 
                      link 
                      @click.stop="removeLayer(layer)" 
                      class="remove-btn"
                      title="删除图层"
                    >
                      <span>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
                        </svg>
                      </span>
                    </el-button>
                  </div>
                </div>
                <div class="layer-card-info">
                  <span class="tag">{{ layer.file_type }}</span>
                  <span class="tag">{{ layer.discipline }}</span>
                  <span class="tag">{{ layer.dimension }}</span>
                  <!-- 显示服务类型 -->
                  <span v-if="layer.service_type" class="tag" :class="getServiceTypeClass(layer.service_type)">
                    {{ getServiceTypeText(layer) }}
                  </span>
                  <!-- 显示图层状态 -->
                  <span class="tag" :class="getLayerStatusClass(layer)">
                    {{ getLayerStatusText(layer) }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div class="empty-layers" v-else>
              <i class="el-icon-map-location"></i>
              <p>当前场景暂无图层</p>
              <el-button type="primary" @click="showAddLayerDialog">添加图层</el-button>
            </div>
          </div>
        </div>
        
        <!-- 收起状态下的展开按钮 -->
        <div class="collapsed-toggle" v-show="layerPanelCollapsed" @click="toggleLayerPanel">
          <el-button 
            link 
            size="small"
            class="expand-btn"
            title="展开面板"
          >
            <span class="toggle-icon">》</span>
          </el-button>
        </div>
      </div>

      <!-- 右侧地图容器 -->
      <div class="map-container-wrapper" :class="{ 'with-panel': !layerPanelCollapsed }">
        <MapViewerOL 
          :scene-id="selectedSceneId" 
          :readonly="false"
          ref="mapViewerRef"
          @layer-added="onLayerAdded"
          @layer-selected="onLayerSelected"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import MapViewerOL from '@/components/MapViewerOLCache.vue';
import gisApi from '@/api/gis.js';
import { DataCacheService, formatFileSize, formatTimeAgo } from '@/services/tileCache/utils.js';
import { createTileCache } from '@/services/tileCache/index.js';

export default {
  name: 'MapViewOLCache',
  components: {
    MapViewerOL
  },
  setup() {
    // 状态管理
    const selectedSceneId = ref(null);
    const sceneList = ref([]);
    const layersList = ref([]);
    const currentActiveLayer = ref(null);
    const layerPanelCollapsed = ref(false);
    const mapViewerRef = ref(null);
    
    // 拖拽相关状态
    const draggingLayerId = ref(null);
    const dragStartIndex = ref(-1);

    // 缓存相关状态
    const cacheProgressVisible = ref(false);
    const cacheLoading = ref(false);
    const cacheProgress = reactive({
      current: 0,
      total: 0,
      percent: 0,
      message: '准备中...',
      status: ''
    });

    // 缓存服务实例
    let tileCacheService = null;
    let dataCacheService = null;

    // 缓存查看器状态
    const cacheViewerVisible = ref(false);
    const tilePreviewVisible = ref(false);
    const cacheSearchText = ref('');
    const activeLayerGroups = ref([]);
    const currentTile = ref(null);
    const tileImageUrl = ref('');
    const cacheData = ref([]);
    const cacheStats = reactive({
      totalTiles: 0,
      totalSize: 0,
      layerCount: 0,
      lastUpdate: Date.now()
    });

    // 初始化缓存服务
    const initCacheService = async () => {
      try {
        tileCacheService = createTileCache({
          maxCacheSize: 500 * 1024 * 1024, // 500MB
          maxCacheAge: 7 * 24 * 60 * 60 * 1000 // 7天
        });

        dataCacheService = new DataCacheService(tileCacheService, gisApi);
        
        // 设置进度回调
        dataCacheService.setProgressCallback((progress) => {
          cacheProgress.current = progress.current;
          cacheProgress.total = progress.total;
          cacheProgress.percent = progress.percent;
          cacheProgress.message = progress.message;
        });

        console.log('缓存服务初始化成功');
      } catch (error) {
        console.error('缓存服务初始化失败:', error);
        ElMessage.error('缓存服务初始化失败');
      }
    };

    // 开始缓存加载
    const startCacheLoading = async () => {
      if (!dataCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      if (cacheLoading.value) {
        ElMessage.info('已有缓存任务在执行中');
        return;
      }

      try {
        cacheLoading.value = true;
        cacheProgressVisible.value = true;
        cacheProgress.status = '';
        
        console.log('开始执行登录缓存策略...');
        await dataCacheService.executeLoginStrategy();
        
        cacheProgress.status = 'success';
        cacheProgress.message = '缓存加载完成！';
        
        ElMessage.success('数据缓存加载完成！');
        
        // 3秒后自动关闭进度对话框
        setTimeout(() => {
          cacheProgressVisible.value = false;
        }, 3000);
        
      } catch (error) {
        console.error('缓存加载失败:', error);
        cacheProgress.status = 'exception';
        cacheProgress.message = '缓存加载失败: ' + error.message;
        ElMessage.error('缓存加载失败: ' + error.message);
      } finally {
        cacheLoading.value = false;
      }
    };

    // 停止缓存加载
    const stopCacheLoading = () => {
      if (dataCacheService) {
        dataCacheService.stopLoading();
      }
      cacheLoading.value = false;
      cacheProgressVisible.value = false;
      ElMessage.info('已停止缓存加载');
    };

    // 场景切换时的缓存加载
    const onSceneChange = async (sceneId) => {
      console.log('场景切换:', sceneId);
      
      // 加载新场景的图层
      await loadSceneLayers(sceneId);
      
      // 自动执行场景切换缓存策略
      if (dataCacheService && !cacheLoading.value) {
        try {
          console.log('执行场景切换缓存策略...');
          await dataCacheService.executeSceneSwitchStrategy(sceneId);
          console.log('场景切换缓存完成');
        } catch (error) {
          console.warn('场景切换缓存失败:', error);
        }
      }
    };

    // 过滤缓存数据的计算属性
    const filteredCacheData = computed(() => {
      if (!cacheSearchText.value) {
        return cacheData.value;
      }
      
      const searchTerm = cacheSearchText.value.toLowerCase();
      return cacheData.value.filter(layer => {
        // 搜索图层ID
        if (layer.layerId.toLowerCase().includes(searchTerm)) {
          return true;
        }
        
        // 搜索瓦片坐标
        return layer.tiles.some(tile => 
          tile.tileX.toString().includes(searchTerm) ||
          tile.tileY.toString().includes(searchTerm) ||
          tile.zoomLevel.toString().includes(searchTerm)
        );
      });
    });

    // 缓存查看器相关方法
    const showCacheViewer = async () => {
      cacheViewerVisible.value = true;
      await refreshCacheData();
    };

    const refreshCacheData = async () => {
      if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        console.log('开始读取IndexedDB缓存数据...');
        
        // 获取所有缓存数据
        const allTiles = await tileCacheService.getAllTiles();
        console.log('获取到的瓦片数据:', allTiles);
        
        // 按图层ID分组
        const layerGroups = {};
        let totalTiles = 0;
        let totalSize = 0;
        let lastUpdate = 0;

        allTiles.forEach(tile => {
          if (!layerGroups[tile.layerId]) {
            layerGroups[tile.layerId] = {
              layerId: tile.layerId,
              tiles: [],
              totalSize: 0
            };
          }
          
          layerGroups[tile.layerId].tiles.push(tile);
          layerGroups[tile.layerId].totalSize += tile.size || 0;
          
          totalTiles++;
          totalSize += tile.size || 0;
          
          if (tile.timestamp > lastUpdate) {
            lastUpdate = tile.timestamp;
          }
        });

        // 转换为数组并排序
        cacheData.value = Object.values(layerGroups).sort((a, b) => 
          b.totalSize - a.totalSize
        );

        // 更新统计信息
        cacheStats.totalTiles = totalTiles;
        cacheStats.totalSize = totalSize;
        cacheStats.layerCount = Object.keys(layerGroups).length;
        cacheStats.lastUpdate = lastUpdate || Date.now();

        console.log('缓存数据统计:', cacheStats);
        ElMessage.success(`成功加载 ${totalTiles} 个瓦片数据`);
        
      } catch (error) {
        console.error('读取缓存数据失败:', error);
        ElMessage.error('读取缓存数据失败: ' + error.message);
      }
    };

    const filterCacheData = () => {
      // 过滤逻辑在计算属性中处理
    };

    const clearAllCache = async () => {
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

        if (!tileCacheService) {
          ElMessage.warning('缓存服务未初始化');
          return;
        }

        await tileCacheService.clearAll();
        await refreshCacheData();
        ElMessage.success('缓存已清空');
        
      } catch (error) {
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
          layers: cacheData.value.map(layer => ({
            layerId: layer.layerId,
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

    const previewTile = async (tile) => {
      try {
        currentTile.value = tile;
        tileImageUrl.value = '';
        tilePreviewVisible.value = true;

        // 从IndexedDB读取瓦片数据
        const tileData = await tileCacheService.getTile(tile.layerId, tile.zoomLevel, tile.tileX, tile.tileY);
        
        if (tileData && tileData.data) {
          // 创建Blob URL用于显示图片
          const blob = tileData.data instanceof Blob ? tileData.data : new Blob([tileData.data]);
          tileImageUrl.value = URL.createObjectURL(blob);
        } else {
          ElMessage.warning('无法读取瓦片数据');
        }
      } catch (error) {
        console.error('预览瓦片失败:', error);
        ElMessage.error('预览瓦片失败: ' + error.message);
      }
    };

    const deleteTile = async (tile) => {
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

        await tileCacheService.deleteTile(tile.layerId, tile.zoomLevel, tile.tileX, tile.tileY);
        await refreshCacheData();
        ElMessage.success('瓦片已删除');
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除瓦片失败:', error);
          ElMessage.error('删除瓦片失败: ' + error.message);
        }
      }
    };

    // 添加测试缓存数据
    const addTestCacheData = async () => {
      if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }

      try {
        console.log('开始添加测试缓存数据...');
        
        // 创建测试图片数据
        const createTestImage = (layerId, z, x, y) => {
          const canvas = document.createElement('canvas');
          canvas.width = 256;
          canvas.height = 256;
          const ctx = canvas.getContext('2d');
          
          // 根据坐标生成不同颜色
          const r = (x * 50) % 255;
          const g = (y * 80) % 255;
          const b = (z * 120) % 255;
          
          ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
          ctx.fillRect(0, 0, 256, 256);
          
          // 添加网格和文本
          ctx.strokeStyle = 'white';
          ctx.lineWidth = 2;
          ctx.strokeRect(0, 0, 256, 256);
          
          ctx.fillStyle = 'white';
          ctx.font = 'bold 16px Arial';
          ctx.textAlign = 'center';
          ctx.fillText(`Layer: ${layerId}`, 128, 80);
          ctx.fillText(`Z: ${z}`, 128, 120);
          ctx.fillText(`X: ${x}, Y: ${y}`, 128, 160);
          
          return new Promise((resolve) => {
            canvas.toBlob((blob) => {
              resolve(blob);
            }, 'image/png');
          });
        };

        // 添加多个测试图层的瓦片
        const testLayers = [
          { id: 'test_layer_001', name: '测试图层1' },
          { id: 'test_layer_002', name: '测试图层2' },
          { id: 'test_layer_003', name: '测试图层3' }
        ];

        let totalSaved = 0;
        
        for (const layer of testLayers) {
          // 为每个图层添加不同缩放级别的瓦片
          const zoomLevels = [8, 10, 12];
          
          for (const z of zoomLevels) {
            // 每个缩放级别添加几个瓦片
            const tiles = [
              { x: 100, y: 200 },
              { x: 101, y: 200 },
              { x: 100, y: 201 },
              { x: 101, y: 201 }
            ];
            
            for (const tile of tiles) {
              try {
                const imageBlob = await createTestImage(layer.id, z, tile.x, tile.y);
                
                await tileCacheService.saveTile(
                  layer.id,
                  z,
                  tile.x,
                  tile.y,
                  imageBlob,
                  {
                    contentType: 'image/png',
                    url: `https://test.example.com/${layer.id}/${z}/${tile.x}/${tile.y}.png`,
                    metadata: {
                      layerName: layer.name,
                      testData: true,
                      createdAt: new Date().toISOString()
                    }
                  }
                );
                
                totalSaved++;
                console.log(`保存测试瓦片: ${layer.id}_${z}_${tile.x}_${tile.y}`);
              } catch (error) {
                console.warn(`保存测试瓦片失败:`, error);
              }
            }
          }
        }
        
        ElMessage.success(`成功添加 ${totalSaved} 个测试瓦片数据`);
        console.log(`测试数据添加完成，共 ${totalSaved} 个瓦片`);
        
      } catch (error) {
        console.error('添加测试数据失败:', error);
        ElMessage.error('添加测试数据失败: ' + error.message);
      }
    };

    // 从MapViewOL复制的其他方法
    const loadScenes = async () => {
      try {
        const response = await gisApi.getScenes();
        sceneList.value = response.data.scenes;

        // 自动选择第一个场景
        if (sceneList.value.length > 0 ) {
          selectedSceneId.value = sceneList.value[0].id;
          await onSceneChange(selectedSceneId.value);
          //console.log('自动选择第一个场景:', selectedSceneId.value);
        }
      } catch (error) {
        console.error('获取场景列表失败:', error);
        ElMessage.error('获取场景列表失败');
      }
    };

    const loadSceneLayers = async (sceneId) => {
      if (!sceneId) return;
      
      try {
        const response = await gisApi.getScene(sceneId);
        const scene = response.data || response;
        layersList.value = scene.layers || [];
        console.log(`获取到场景 ${sceneId} 的图层:`, layersList.value);
      } catch (error) {
        console.error('获取场景图层失败:', error);
        ElMessage.error('获取场景图层失败');
      }
    };

    const toggleLayerPanel = () => {
      layerPanelCollapsed.value = !layerPanelCollapsed.value;
    };

    const selectLayer = (layer) => {
      currentActiveLayer.value = layer;
      console.log('选择图层:', layer);
    };

    const toggleLayerVisibility = (layer) => {
      console.log('切换图层可见性:', layer.layer_name, layer.visibility);
      // 这里可以调用地图组件的方法来切换图层可见性
    };

    const zoomToLayer = async (layer) => {
      try {
        const bounds = await gisApi.getSceneLayerBounds(layer.scene_layer_id);
        if (bounds && bounds.bbox && mapViewerRef.value) {
          // 调用地图组件的缩放方法
          mapViewerRef.value.zoomToBounds(bounds.bbox);
        }
      } catch (error) {
        console.error('缩放到图层失败:', error);
        ElMessage.error('缩放到图层失败');
      }
    };

    const showStyleDialog = (layer) => {
      console.log('显示样式对话框:', layer);
      ElMessage.info('样式设置功能开发中...');
    };

    const removeLayer = async (layer) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除图层 "${layer.layer_name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        );
        
        // 这里调用删除图层的API
        console.log('删除图层:', layer);
        ElMessage.success('图层删除成功');
      } catch (error) {
        console.log('取消删除');
      }
    };

    const showAddLayerDialog = () => {
      console.log('显示添加图层对话框');
      ElMessage.info('添加图层功能开发中...');
    };

    const onLayerAdded = (layer) => {
      console.log('图层已添加:', layer);
      // 重新加载图层列表
      if (selectedSceneId.value) {
        loadSceneLayers(selectedSceneId.value);
      }
    };

    const onLayerSelected = (layer) => {
      console.log('地图组件选择图层:', layer);
      currentActiveLayer.value = layer;
    };

    // 辅助方法
    const getServiceTypeClass = (serviceType) => {
      const classMap = {
        'wms': 'service-wms',
        'wfs': 'service-wfs',
        'martin': 'service-martin'
      };
      return classMap[serviceType] || 'service-unknown';
    };

    const getServiceTypeText = (layer) => {
      if (layer.service_type === 'martin') {
        return 'MVT';
      }
      return layer.service_type?.toUpperCase() || '未知';
    };

    const getLayerStatusClass = (layer) => {
      if (layer.geoserver_layer) {
        return 'status-published';
      }
      return 'status-unpublished';
    };

    const getLayerStatusText = (layer) => {
      if (layer.geoserver_layer) {
        return '已发布';
      }
      return '未发布';
    };

    // 生命周期
    onMounted(async () => {
      console.log('MapViewOLCache 组件挂载');
      await initCacheService();
      await loadScenes();
    });

    onBeforeUnmount(() => {
      // 清理资源
      if (dataCacheService) {
        dataCacheService.stopLoading();
      }
    });

    // 图层按顺序排序（layer_order大的在上面）
    const sortedLayersList = computed(() => {
      if (!layersList.value || !Array.isArray(layersList.value)) {
        return []
      }
      
      return [...layersList.value].sort((a, b) => {
        const orderA = a.layer_order || 0
        const orderB = b.layer_order || 0
        return orderB - orderA // 降序排列，大的在前面
      })
    })

    // 拖拽开始
    const handleDragStart = (event, layer, index) => {
      draggingLayerId.value = layer.id
      dragStartIndex.value = index
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', layer.id.toString())
      
      // 设置拖拽图像
      const dragImage = event.target.cloneNode(true)
      dragImage.style.opacity = '0.8'
      dragImage.style.transform = 'rotate(2deg)'
      document.body.appendChild(dragImage)
      event.dataTransfer.setDragImage(dragImage, 0, 0)
      setTimeout(() => document.body.removeChild(dragImage), 0)
    }

    // 拖拽结束
    const handleDragEnd = () => {
      draggingLayerId.value = null
      dragStartIndex.value = -1
    }

    // 拖拽悬停
    const handleDragOver = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
    }

    // 拖拽放置
    const handleDrop = async (event, dropIndex) => {
      event.preventDefault()
      
      //const draggedLayerId = parseInt(event.dataTransfer.getData('text/plain'))
      const startIndex = dragStartIndex.value
      
      if (startIndex === dropIndex || startIndex === -1) {
        return
      }

      try {
        // 计算新的图层顺序
        const newLayersOrder = calculateNewLayersOrder(startIndex, dropIndex)
        
        // 批量更新图层顺序
        await updateLayersOrder(newLayersOrder)
        
        ElMessage.success('图层顺序更新成功')
        
        // 刷新场景数据
        await onSceneChange(selectedSceneId.value)
        
      } catch (error) {
        console.error('更新图层顺序失败:', error)
        ElMessage.error('更新图层顺序失败')
      }
    }

    // 计算新的图层顺序
    const calculateNewLayersOrder = (fromIndex, toIndex) => {
      const sortedLayers = [...sortedLayersList.value]
      const movedLayer = sortedLayers[fromIndex]
      
      // 移除被拖拽的图层
      sortedLayers.splice(fromIndex, 1)
      // 插入到新位置
      sortedLayers.splice(toIndex, 0, movedLayer)
      
      // 重新分配layer_order（从大到小，因为显示时是从大到小排序）
      const newOrders = {}
      const maxOrder = sortedLayers.length
      
      sortedLayers.forEach((layer, index) => {
        const newOrder = maxOrder - index // 第一个（index=0）获得最大order
        newOrders[layer.id] = newOrder
      })
      
      return newOrders
    }

    // 批量更新图层顺序
    const updateLayersOrder = async (newOrders) => {
      // 使用现有的批量更新接口
      await gisApi.reorderSceneLayers(selectedSceneId.value, newOrders)
    }

    return {
      // 基础状态
      selectedSceneId,
      sceneList,
      layersList,
      sortedLayersList,
      currentActiveLayer,
      layerPanelCollapsed,
      mapViewerRef,
      
      // 缓存相关
      cacheProgressVisible,
      cacheLoading,
      cacheProgress,
      startCacheLoading,
      stopCacheLoading,
      
      // 缓存查看器相关
      cacheViewerVisible,
      tilePreviewVisible,
      cacheSearchText,
      activeLayerGroups,
      currentTile,
      tileImageUrl,
      cacheData,
      cacheStats,
      filteredCacheData,
      showCacheViewer,
      refreshCacheData,
      filterCacheData,
      clearAllCache,
      exportCacheData,
      previewTile,
      deleteTile,
      addTestCacheData,
      
      // 工具函数
      formatFileSize,
      formatTimeAgo,
      
      // 方法
      onSceneChange,
      toggleLayerPanel,
      selectLayer,
      toggleLayerVisibility,
      zoomToLayer,
      showStyleDialog,
      removeLayer,
      showAddLayerDialog,
      onLayerAdded,
      onLayerSelected,
      getServiceTypeClass,
      getServiceTypeText,
      getLayerStatusClass,
      getLayerStatusText,
      
      // 拖拽相关
      draggingLayerId,
      handleDragStart,
      handleDragEnd,
      handleDragOver,
      handleDrop
    };
  }
};
</script>

<style scoped>
.map-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.map-content {
  flex: 1;
  display: flex;
  position: relative;
}

.layer-panel {
  width: 350px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  z-index: 10;
}

.layer-panel.collapsed {
  width: 0;
  overflow: hidden;
}

.collapsed-toggle {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 20;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-left: none;
  border-radius: 0 4px 4px 0;
  padding: 8px 4px;
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layer-count {
  font-size: 12px;
  color: #999;
}

.panel-toggle-btn,
.expand-btn {
  color: #606266;
}

.toggle-icon {
  font-size: 14px;
  font-weight: bold;
}

.scene-selector {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.layer-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.layer-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
}

.layer-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.layer-card.active {
  border-color: #409eff;
  background: #f0f9ff;
}

.layer-card.invisible {
  opacity: 0.6;
}

.layer-card.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.layer-card[draggable="true"] {
  cursor: grab;
}

.layer-card[draggable="true"]:active {
  cursor: grabbing;
}

.layer-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.layer-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.layer-name {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.active-indicator {
  color: #67c23a;
  font-size: 16px;
}

.layer-drag-handle {
  color: #c0c4cc;
  cursor: grab;
  padding: 0 4px;
}

.layer-actions {
  display: flex;
  gap: 4px;
}

.layer-actions .el-button {
  padding: 4px;
  min-height: auto;
}

.zoom-btn {
  color: #409eff;
}

.style-btn {
  color: #e6a23c;
}

.remove-btn {
  color: #f56c6c;
}

.layer-card-info {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  background: #f4f4f5;
  color: #909399;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
}

.service-wms {
  background: #e1f3d8;
  color: #67c23a;
}

.service-wfs {
  background: #fdf6ec;
  color: #e6a23c;
}

.service-martin {
  background: #ecf5ff;
  color: #409eff;
}

.status-published {
  background: #e1f3d8;
  color: #67c23a;
}

.status-unpublished {
  background: #fef0f0;
  color: #f56c6c;
}

.empty-layers {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-layers i {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.map-container-wrapper {
  flex: 1;
  position: relative;
  transition: all 0.3s ease;
}

.map-container-wrapper.with-panel {
  margin-left: 0;
}

/* 缓存进度样式 */
.cache-progress {
  text-align: center;
}

.progress-text {
  margin: 16px 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.progress-details {
  color: #909399;
  font-size: 12px;
}

/* 缓存查看器样式 */
.cache-viewer {
  max-height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cache-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #e4e7ed;
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

.cache-stats {
  margin-bottom: 20px;
}

.stat-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cache-layers {
  flex: 1;
  overflow-y: auto;
}

.layer-group-title {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.layer-id {
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.tiles-container {
  padding: 16px 0;
}

.empty-cache {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-cache i {
  font-size: 64px;
  margin-bottom: 16px;
  display: block;
  color: #c0c4cc;
}

/* 瓦片预览样式 */
.tile-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tile-info {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.tile-info p {
  margin: 8px 0;
  font-size: 14px;
}

.tile-image {
  text-align: center;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.loading-placeholder {
  padding: 40px;
  color: #909399;
}

.loading-placeholder i {
  font-size: 32px;
  margin-bottom: 8px;
  display: block;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .cache-toolbar {
    flex-direction: column;
    gap: 12px;
  }
  
  .toolbar-left {
    order: 2;
  }
  
  .toolbar-right {
    order: 1;
  }
  
  .stat-value {
    font-size: 20px;
  }
}
</style> 