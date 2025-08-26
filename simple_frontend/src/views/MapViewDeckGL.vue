<template>
  <div class="map-view">
    <!-- 主要内容区域 -->
    <div class="map-content">
      <!-- 左侧图层面板 - 桌面端显示 -->
      <div class="layer-panel desktop-only" :class="{ 'collapsed': layerPanelCollapsed }">
        <div class="panel-content" v-show="!layerPanelCollapsed">
          <div class="panel-header">
            <h3>图层管理</h3>
            <div class="header-right">
              <span class="layer-count">{{ (layersList || []).length }} 个图层</span>
              <el-button type="primary" size="small" @click="showAddLayerDialog">
                <i class="el-icon-plus"></i> 添加图层
              </el-button>
              <!-- 面板切换按钮 -->
              <el-button 
                link 
                size="small" 
                @click="toggleLayerPanel"
                class="panel-toggle-btn"
                :title="layerPanelCollapsed ? '展开面板' : '收起面板'"
              >
                <span class="toggle-icon">{{ layerPanelCollapsed ? '》' : '《' }}</span>
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
            <!-- 图层卡片列表 -->
            <div class="layer-cards" v-if="layersList && layersList.length > 0">
              <div 
                v-for="(layer) in sortedLayersList" 
                :key="layer.scene_layer_id || layer.id" 
                class="layer-card"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                  'invisible': !layer.visibility
                }"
                @click="selectLayer(layer)"
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
                    <span class="layer-name">{{ layer.layer_name || layer.name || '未命名图层' }}</span>
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
                
                <!-- 🔥 透明度控制 -->
                <div 
                  class="layer-opacity-control" 
                  @click.stop
                  @mousedown.stop
                  @dragstart.stop="$event.preventDefault()"
                  @drag.stop="$event.preventDefault()"
                >
                  <div class="opacity-row">
                    <i class="el-icon-view opacity-icon"></i>
                    <span class="opacity-label">透明度</span>
                    <el-slider
                      :model-value="layer.opacity || 1"
                      @update:model-value="val => updateLayerOpacity(layer, val)"
                      :min="0"
                      :max="1"
                      :step="0.01"
                      size="small"
                      class="opacity-slider"
                      :show-tooltip="false"
                    />
                    <span class="opacity-value">{{ Math.round((layer.opacity || 1) * 100) }}%</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">🗺️</div>
              <div class="empty-text">暂无图层</div>
              <div class="empty-description">点击"添加图层"开始使用</div>
            </div>
          </div>
        </div>
        
        <!-- 收起状态下的内容 -->
        <div class="collapsed-content" v-show="layerPanelCollapsed">
          <!-- 展开按钮 -->
          <div class="collapsed-toggle" @click="toggleLayerPanel">
            <el-button 
              link 
              size="small"
              class="expand-btn"
              title="展开面板"
            >
            <span class="toggle-icon">》</span>
            </el-button>
          </div>
          
          <!-- 收起状态下的场景选择样式 -->
          <div class="collapsed-scene-selector" v-if="sceneList && sceneList.length > 0">
            <!-- 场景区域标题 -->
             
            <div class="collapsed-section-title">场景</div>
            <div 
              v-for="scene in sceneList" 
              :key="scene.id" 
              class="collapsed-scene-item"
              :class="{ 'active': selectedSceneId === scene.id }"
              @click="onSceneChange(scene.id)"
              :title="`场景: ${scene.name}
👆 点击切换到此场景`"
            >
              <div class="scene-short-name">{{ scene.name.substring(0, 2) }}</div>
              <div v-if="selectedSceneId === scene.id" class="scene-active-dot"></div>
            </div>
          </div>
          
          <!-- 分隔线 -->
          <div class="collapsed-separator" v-if="sceneList && sceneList.length > 0 && layersList && layersList.length > 0"></div>
          
          <!-- 收起状态下的图层列表 -->
          <div class="collapsed-layers" v-if="layersList && layersList.length > 0">
            <!-- 图层区域标题 -->
            <div class="collapsed-section-title">图层</div>
            <div 
              v-for="(layer) in sortedLayersList" 
              :key="layer.scene_layer_id || layer.id" 
              class="collapsed-layer-item"
              :class="{ 
                'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                'invisible': !layer.visibility
              }"
              @click="selectLayer(layer)"
              :title="`图层: ${layer.layer_name || layer.name || '未命名图层'}
类型: ${getLayerTypeText(layer)}
👆 点击选中此图层
🔄 双击缩放到图层范围`"
              @dblclick="zoomToLayer(layer)"
            >
              <div class="layer-short-name">{{ (layer.layer_name || layer.name || '未命名').substring(0, 2) }}</div>
              <div v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" class="layer-active-dot"></div>
              <div v-if="!layer.visibility" class="layer-invisible-dot"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 地图区域 -->
      <div class="map-container-wrapper" :class="{ 'with-panel': !layerPanelCollapsed }">
        <MapViewerDeckGL
          ref="mapViewer"
          :layers="layersList"
          :layers-cache-enabled="layersCacheEnabled"
          @map-ready="onMapReady"
          @layer-click="onLayerClick"
          @layers-cache-toggle="toggleLayersCache"
        />
        
        <!-- 🔥 手机端底部浮动按钮 -->
        <div class="mobile-layer-fab" @click="toggleMobileDrawer">
          <div class="fab-content">
            <i class="el-icon-menu"></i>
            <span class="fab-text">图层</span>
            <div class="fab-badge" v-if="layersList && layersList.length > 0">
              {{ layersList.length }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 🔥 手机端抽屉式图层面板 -->
    <div class="mobile-drawer-overlay mobile-only" :class="{ 'show': mobileDrawerVisible }" @click="closeMobileDrawer">
      <div class="mobile-drawer" :class="{ 'show': mobileDrawerVisible }" @click.stop>
        <!-- 抽屉头部 -->
        <div class="mobile-drawer-header">
          <div class="drawer-handle"></div>
          <div class="drawer-title">
            <h3>图层管理</h3>
            <div class="drawer-actions">
              <el-button type="primary" size="small" @click="showAddLayerDialog">
                <i class="el-icon-plus"></i>
                <span>添加图层</span>
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 抽屉内容 -->
        <div class="mobile-drawer-content">
          <!-- 场景选择标签页 -->
          <div class="mobile-tabs">
            <div 
              class="mobile-tab" 
              :class="{ 'active': mobileActiveTab === 'scene' }"
              @click="mobileActiveTab = 'scene'"
            >
              <i class="el-icon-folder"></i>
              <span>场景</span>
            </div>
            <div 
              class="mobile-tab" 
              :class="{ 'active': mobileActiveTab === 'layers' }"
              @click="mobileActiveTab = 'layers'"
            >
              <i class="el-icon-menu"></i>
              <span>图层</span>
              <div class="tab-badge" v-if="layersList && layersList.length > 0">
                {{ layersList.length }}
              </div>
            </div>
          </div>
          
          <!-- 场景选择内容 -->
          <div class="mobile-tab-content" v-show="mobileActiveTab === 'scene'">
            <div class="mobile-scene-list">
              <div 
                v-for="scene in sceneList" 
                :key="scene.id"
                class="mobile-scene-item"
                :class="{ 'active': selectedSceneId === scene.id }"
                @click="selectMobileScene(scene.id)"
              >
                <div class="scene-info">
                  <h4>{{ scene.name }}</h4>
                  <p>{{ scene.description || '暂无描述' }}</p>
                </div>
                <div class="scene-meta">
                  <el-tag v-if="scene.is_public" type="success" size="small">公开</el-tag>
                  <el-tag v-else type="warning" size="small">私有</el-tag>
                </div>
              </div>
              
              <!-- 场景空状态 -->
              <div v-if="!sceneList || sceneList.length === 0" class="mobile-empty">
                <i class="el-icon-folder"></i>
                <p>暂无场景</p>
              </div>
            </div>
          </div>
          
          <!-- 图层列表内容 -->
          <div class="mobile-tab-content" v-show="mobileActiveTab === 'layers'">
            <div class="mobile-layer-list">
              <div 
                v-for="layer in sortedLayersList" 
                :key="layer.scene_layer_id || layer.id"
                class="mobile-layer-item"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                  'invisible': !layer.visibility
                }"
                @click="selectLayer(layer)"
              >
                <div class="layer-main-info">
                  <div class="layer-header">
                    <el-checkbox 
                      v-model="layer.visibility" 
                      @change="toggleLayerVisibility(layer)"
                      @click.stop
                    />
                    <span class="layer-name">{{ layer.layer_name }}</span>
                    <i v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" 
                       class="el-icon-location active-indicator"></i>
                  </div>
                  
                  <div class="layer-tags">
                    <span class="tag">{{ layer.file_type }}</span>
                    <span class="tag">{{ layer.discipline }}</span>
                    <span v-if="layer.service_type" class="tag" :class="getServiceTypeClass(layer.service_type)">
                      {{ getServiceTypeText(layer) }}
                    </span>
                  </div>
                  
                  <!-- 移动端透明度控制 -->
                  <div class="mobile-opacity-control" @click.stop>
                    <span class="opacity-label">透明度</span>
                    <el-slider
                      v-model="layer.opacity"
                      :min="0"
                      :max="1"
                      :step="0.1"
                      :show-tooltip="false"
                      size="small"
                      @input="updateLayerOpacity(layer)"
                      class="mobile-opacity-slider"
                    />
                    <span class="opacity-value">{{ Math.round((layer.opacity || 1) * 100) }}%</span>
                  </div>
                </div>
                
                <div class="layer-actions">
                  <el-button size="small" @click.stop="zoomToLayer(layer)" title="缩放到图层" class="action-btn zoom-btn">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M15.5 14h-.79l-.28-.27A6.5 6.5 0 1 0 13 15.5l.27.28v.79l5 4.99L19.49 20l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/>
                      <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
                    </svg>
                  </el-button>
                  <el-button size="small" @click.stop="showStyleDialog(layer)" title="样式设置" class="action-btn style-btn">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
                    </svg>
                  </el-button>
                  <el-button size="small" @click.stop="removeLayer(layer)" title="删除图层" class="action-btn delete-btn">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
                    </svg>
                  </el-button>
                </div>
              </div>
              
              <!-- 图层空状态 -->
              <div v-if="!layersList || layersList.length === 0" class="mobile-empty">
                <i class="el-icon-map-location"></i>
                <p>当前场景暂无图层</p>
                <el-button type="primary" @click="showAddLayerDialog">添加图层</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加图层对话框 -->
    <el-dialog title="添加图层" v-model="addLayerDialogVisible" :width="isMobile ? '95%' : '800px'" :fullscreen="isMobile">
      <div class="add-layer-dialog-content">
        <!-- 搜索和筛选 -->
        <div class="layer-search-section">
          <el-form :inline="!isMobile" :model="layerSearchForm">
            <el-form-item label="服务类型">
              <el-select v-model="layerSearchForm.service_type" placeholder="全部" clearable>
                <el-option label="全部" value="" />
                <el-option label="GeoServer" value="geoserver" />
                <el-option label="Martin" value="martin" />
              </el-select>
            </el-form-item>
            <el-form-item label="数据类型">
              <el-select v-model="layerSearchForm.file_type" placeholder="全部" clearable>
                <el-option label="全部" value="" />
                <el-option label="Shapefile" value="shp" />
                <el-option label="GeoTIFF" value="tif" />
                <el-option label="DXF" value="dxf" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchLayers">搜索</el-button>
              <el-button @click="resetSearch">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 可用图层列表 -->
        <div class="available-layers" v-loading="loadingLayers">
          <div 
            v-for="layer in availableLayers" 
            :key="layer.id"
            class="available-layer-item"
            :class="{ 'selected': selectedLayers.includes(layer.id) }"
          >
            <div class="layer-preview">
              <div class="preview-placeholder">
                {{ getLayerIcon(layer) }}
              </div>
            </div>
            <div class="layer-details">
              <div class="layer-name">{{ layer.layer_name || layer.file_name || layer.original_name || '未命名图层' }}</div>
              <div class="layer-description">{{ layer.description || getLayerTypeText(layer) }}</div>
              <div class="layer-meta">
                <span class="meta-item">{{ layer.file_type?.toUpperCase() }}</span>
                <span class="meta-item">专业: {{ layer.discipline || '未知' }}</span>
              </div>
              
              <!-- 服务状态和操作按钮 -->
              <div class="layer-services">
                <!-- GeoServer服务 -->
                <div v-if="layer.geoserver_service?.is_published" class="service-item">
                  <el-tag type="success" size="small">GeoServer已发布</el-tag>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="addLayerToScene(layer, 'geoserver')"
                    :disabled="isLayerInScene(layer.id, 'geoserver')"
                  >
                    {{ isLayerInScene(layer.id, 'geoserver') ? '已添加' : '添加GeoServer' }}
                  </el-button>
                </div>
                
                <!-- Martin服务 -->
                <div v-if="layer.martin_service?.is_published" class="service-item">
                  <el-tag type="primary" size="small">Martin已发布</el-tag>
                  <el-button 
                    size="small" 
                    type="success" 
                    @click="addLayerToScene(layer, 'martin')"
                    :disabled="isLayerInScene(layer.id, 'martin')"
                  >
                    {{ isLayerInScene(layer.id, 'martin') ? '已添加' : '添加Martin' }}
                  </el-button>
                </div>
                
                <!-- 未发布状态 -->
                <div v-if="!hasAnyPublishedService(layer)" class="service-item">
                  <el-tag type="warning" size="small">服务未发布</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="totalLayers > 0">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalLayers"
            layout="prev, pager, next, total"
            @current-change="handlePageChange"
          />
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addLayerDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="addSelectedLayers"
            :disabled="selectedLayers.length === 0"
          >
            添加选中图层 ({{ selectedLayers.length }})
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import MapViewerDeckGL from '@/components/MapViewerDeckGL.vue'
import { isMobileDevice } from '@/utils/deviceUtils'
import gisApi from '@/api/gis'

export default {
  name: 'MapViewDeckGL',
  components: {
    MapViewerDeckGL
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    // 响应式数据
    const mapViewer = ref(null)
    const deckglMap = ref(null)
    const layerPanelCollapsed = ref(false)
    // 🔥 手机端抽屉相关状态
    const mobileDrawerVisible = ref(false)
    const mobileActiveTab = ref('layers') // 'scene' or 'layers'
    
    // 🔥 拖拽手柄相关状态
    const isDragging = ref(false)
    const dragStartY = ref(0)
    const drawerStartY = ref(0)
    const addLayerDialogVisible = ref(false)
    const loadingLayers = ref(false)
    const layersCacheEnabled = ref(true)
    const loading = ref(false)
    const currentActiveLayer = ref(null)
    
    // 图层管理
    const layersList = ref([])
    const availableLayers = ref([])
    const selectedLayers = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalLayers = ref(0)
    
    // 场景管理
    const sceneList = ref([])
    const selectedSceneId = ref(null)
    
    // 搜索表单
    const layerSearchForm = reactive({
      service_type: '',
      file_type: '',
      keyword: ''
    })
    
    // 计算属性
    const isMobile = computed(() => isMobileDevice())
    
    const sortedLayersList = computed(() => {
      return [...layersList.value].sort((a, b) => (b.zIndex || 0) - (a.zIndex || 0))
    })
    
    // 地图准备完成
    const onMapReady = (mapInstance) => {
      deckglMap.value = mapInstance
      console.log('Deck.gl地图准备完成')
    }
    
    // 图层点击事件
    const onLayerClick = (event) => {
      console.log('图层点击:', event)
      // 这里可以显示要素信息弹窗
    }
    
    // 切换图层面板
    const toggleLayerPanel = () => {
      layerPanelCollapsed.value = !layerPanelCollapsed.value
    }
    
    // 显示移动端图层面板
    // 🔥 手机端抽屉控制方法
    const toggleMobileDrawer = () => {
      mobileDrawerVisible.value = !mobileDrawerVisible.value
      // 默认显示图层标签页
      if (mobileDrawerVisible.value) {
        mobileActiveTab.value = 'layers'
      }
    }
    
    const closeMobileDrawer = () => {
      mobileDrawerVisible.value = false
      // 重置拖拽状态
      isDragging.value = false
      dragStartY.value = 0
      drawerStartY.value = 0
    }
    
    const selectMobileScene = (sceneId) => {
      // 选择场景后自动切换到图层标签页
      onSceneChange(sceneId)
      mobileActiveTab.value = 'layers'
    }
    
    // 🔥 拖拽手柄事件处理
    const handleDrawerHandleClick = () => {
      // 点击拖拽手柄直接关闭抽屉
      closeMobileDrawer()
    }
    
    const handleDrawerDragStart = (event) => {
      isDragging.value = true
      
      // 支持触摸和鼠标事件
      const clientY = event.touches ? event.touches[0].clientY : event.clientY
      dragStartY.value = clientY
      
      // 获取抽屉当前位置
      const drawer = event.target.closest('.mobile-drawer')
      if (drawer) {
        const rect = drawer.getBoundingClientRect()
        drawerStartY.value = rect.top
      }
      
      // 阻止默认行为和事件冒泡
      event.preventDefault()
      event.stopPropagation()
      
      // 添加全局事件监听器
      if (event.touches) {
        document.addEventListener('touchmove', handleDrawerDragMove, { passive: false })
        document.addEventListener('touchend', handleDrawerDragEnd, { once: true })
      } else {
        document.addEventListener('mousemove', handleDrawerDragMove)
        document.addEventListener('mouseup', handleDrawerDragEnd, { once: true })
      }
    }
    
    const handleDrawerDragMove = (event) => {
      if (!isDragging.value) return
      
      // 支持触摸和鼠标事件
      const clientY = event.touches ? event.touches[0].clientY : event.clientY
      const deltaY = clientY - dragStartY.value
      
      // 只有向下拖拽才有效果
      if (deltaY > 10) {
        // 计算透明度，越往下拖越透明
        const opacity = Math.max(0.3, 1 - (deltaY / 200))
        
        // 获取抽屉元素并应用样式
        const drawer = document.querySelector('.mobile-drawer')
        if (drawer) {
          drawer.style.transform = `translateY(${deltaY}px)`
          drawer.style.opacity = opacity.toString()
        }
        
        // 如果拖拽距离超过阈值，准备关闭
        if (deltaY > 100) {
          const overlay = document.querySelector('.mobile-drawer-overlay')
          if (overlay) {
            overlay.style.opacity = (1 - (deltaY - 100) / 100).toString()
          }
        }
      }
      
      // 阻止默认行为
      event.preventDefault()
    }
    
    const handleDrawerDragEnd = (event) => {
      if (!isDragging.value) return
      
      // 支持触摸和鼠标事件
      const clientY = event.touches ? 
        (event.changedTouches ? event.changedTouches[0].clientY : dragStartY.value) : 
        event.clientY
      const deltaY = clientY - dragStartY.value
      
      // 移除全局事件监听器
      document.removeEventListener('touchmove', handleDrawerDragMove)
      document.removeEventListener('mousemove', handleDrawerDragMove)
      
      // 重置样式
      const drawer = document.querySelector('.mobile-drawer')
      if (drawer) {
        drawer.style.transform = ''
        drawer.style.opacity = ''
      }
      
      const overlay = document.querySelector('.mobile-drawer-overlay')
      if (overlay) {
        overlay.style.opacity = ''
      }
      
      // 如果向下拖拽距离足够，关闭抽屉
      if (deltaY > 80) {
        closeMobileDrawer()
      }
      
      // 重置拖拽状态
      isDragging.value = false
      dragStartY.value = 0
      drawerStartY.value = 0
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = (layer) => {
      // 更新图层状态
      layer.visibility = !layer.visibility
      console.log(`切换图层 ${layer.layer_name} 可见性: ${layer.visibility}`)
      
      // 通知地图组件更新
      if (mapViewer.value) {
        // 触发图层列表的响应式更新
        layersList.value = [...layersList.value]
      }
    }
    
    // 更新图层透明度
    const updateLayerOpacity = (layer, newOpacity = null) => {
      if (newOpacity !== null) {
        layer.opacity = newOpacity
      }
      
      console.log(`更新图层 ${layer.layer_name} 透明度: ${Math.round(layer.opacity * 100)}%`)
      
      // 确保透明度在有效范围内
      layer.opacity = Math.max(0, Math.min(1, parseFloat(layer.opacity) || 1.0))
      
      // 通知地图组件更新
      if (mapViewer.value) {
        // 触发图层列表的响应式更新
        layersList.value = [...layersList.value]
      }
    }
    
    // 显示样式设置对话框
    const showStyleDialog = (layer) => {
      console.log('显示样式设置对话框:', layer.layer_name)
      
      // 🔥 手机端：样式设置后自动关闭图层管理抽屉
      if (isMobile.value && mobileDrawerVisible.value) {
        closeMobileDrawer()
      }
      
      ElMessage.info('样式设置功能开发中...')
      // TODO: 实现样式设置对话框
    }
    
    // 获取服务类型样式类
    const getServiceTypeClass = (serviceType) => {
      const classMap = {
        'geoserver': 'service-geoserver',
        'martin': 'service-martin',
        'wms': 'service-wms',
        'mvt': 'service-mvt'
      }
      return classMap[serviceType] || 'service-default'
    }
    
    // 获取服务类型文本
    const getServiceTypeText = (layer) => {
      const textMap = {
        'geoserver': 'GeoServer',
        'martin': 'Martin',
        'wms': 'WMS',
        'mvt': 'MVT'
      }
      return textMap[layer.service_type] || layer.service_type || '未知'
    }
    
    // 获取图层状态样式类
    const getLayerStatusClass = (layer) => {
      if (layer.visibility === false) {
        return 'status-hidden'
      }
      return 'status-visible'
    }
    
    // 获取图层状态文本
    const getLayerStatusText = (layer) => {
      if (layer.visibility === false) {
        return '隐藏'
      }
      return '可见'
    }
    
    // 缩放到图层 - 适配Deck.gl
    const zoomToLayer = async (layer) => {
      try {
        // 检查地图实例
        if (!mapViewer.value || !mapViewer.value.deckgl) {
          ElMessage.error('地图实例未初始化')
          return
        }
        
        let bbox = null
        let originalCRS = 'EPSG:4326'
        
        // 1. 优先使用图层边界API
        try {
          const response = await gisApi.getSceneLayerBounds(layer.scene_layer_id)
          if (response?.success && response.data?.bbox) {
            bbox = response.data.bbox
            originalCRS = response.data.coordinate_system || 'EPSG:4326'
            console.log('从图层边界API获取到边界:', bbox, '原始坐标系:', originalCRS)
          }
        } catch (apiError) {
          console.warn('图层边界API调用失败，尝试其他方式:', apiError)
        }
        
        // 2. 如果API调用失败，尝试从图层属性获取
        if (!bbox && layer.bbox) {
          if (typeof layer.bbox === 'string') {
            try {
              bbox = JSON.parse(layer.bbox)
            } catch (e) {
              console.error('解析图层边界框失败:', e)
            }
          } else {
            bbox = layer.bbox
          }
        }
        
        // 3. 如果仍然没有边界，尝试从文件信息获取
        if (!bbox && layer.file_id) {
          try {
            const response = await gisApi.getFileBounds(layer.file_id)
            if (response?.bbox) {
              bbox = response.bbox
              if (typeof bbox === 'string') {
                bbox = JSON.parse(bbox)
              }
            }
          } catch (fileError) {
            console.warn('获取文件边界失败:', fileError)
          }
        }
        
        if (!bbox) {
          ElMessage.warning('无法获取图层边界信息')
          return
        }
        
        // 4. 验证边界框数据
        let bounds = null
        if (Array.isArray(bbox) && bbox.length === 4) {
          // [minx, miny, maxx, maxy] 格式
          bounds = {
            minx: parseFloat(bbox[0]),
            miny: parseFloat(bbox[1]), 
            maxx: parseFloat(bbox[2]),
            maxy: parseFloat(bbox[3])
          }
        } else if (bbox.minx !== undefined) {
          // {minx, miny, maxx, maxy} 格式
          bounds = {
            minx: parseFloat(bbox.minx),
            miny: parseFloat(bbox.miny),
            maxx: parseFloat(bbox.maxx),
            maxy: parseFloat(bbox.maxy)
          }
        } else {
          ElMessage.warning('边界框数据格式不正确')
          return
        }
        
        // 5. 验证数值有效性
        if (isNaN(bounds.minx) || isNaN(bounds.miny) || isNaN(bounds.maxx) || isNaN(bounds.maxy)) {
          ElMessage.warning('边界框数据格式错误')
          return
        }
        
        // 6. 计算中心点和缩放级别
        const centerLon = (bounds.minx + bounds.maxx) / 2
        const centerLat = (bounds.miny + bounds.maxy) / 2
        
        // 计算合适的缩放级别（基于边界框大小）
        const lonDiff = Math.abs(bounds.maxx - bounds.minx)
        const latDiff = Math.abs(bounds.maxy - bounds.miny)
        const maxDiff = Math.max(lonDiff, latDiff)
        
        let zoom = 10
        if (maxDiff < 0.001) zoom = 16
        else if (maxDiff < 0.01) zoom = 14
        else if (maxDiff < 0.1) zoom = 12
        else if (maxDiff < 1) zoom = 10
        else if (maxDiff < 10) zoom = 8
        else zoom = 6
        
        // 7. 使用Deck.gl进行视图动画
        const deckglInstance = mapViewer.value.deckgl
        if (deckglInstance) {
          deckglInstance.setProps({
            initialViewState: {
              longitude: centerLon,
              latitude: centerLat,
              zoom: zoom,
              pitch: 0,
              bearing: 0,
              transitionDuration: 1000,
              transitionInterpolator: null // 使用默认插值器
            }
          })
          
          // 设置当前活动图层
          currentActiveLayer.value = layer
          
          // 🔥 手机端：缩放后自动关闭图层管理抽屉
          if (isMobile.value && mobileDrawerVisible.value) {
            closeMobileDrawer()
          }
          
          ElMessage.success(`已缩放到图层"${layer.layer_name}"范围 (${originalCRS})`)
        }
        
      } catch (error) {
        console.error('缩放到图层失败:', error)
        ElMessage.error(`缩放到图层失败: ${error.message}`)
      }
    }
    
    // 选择图层
    const selectLayer = (layer) => {
      console.log('选择图层:', layer.layer_name)
      currentActiveLayer.value = layer
      
      ElMessage.success(`已选中图层: ${layer.layer_name}`)
    }

    // 移除图层
    const removeLayer = async (layer) => {
      try {
        await ElMessageBox.confirm(`确认从场景中移除图层"${layer.layer_name}"？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        try {
          await gisApi.removeLayerFromScene(selectedSceneId.value, layer.id)
          ElMessage.success('图层移除成功')
          // 刷新图层列表
          fetchSceneLayers(selectedSceneId.value)
        } catch (error) {
          console.error('移除图层失败', error)
          ElMessage.error('移除图层失败')
        }
      } catch {
        // 用户取消
      }
    }
    
    // 获取图层类型文本
    const getLayerTypeText = (layer) => {
      const typeMap = {
        'geoserver': 'GeoServer服务',
        'martin': 'Martin服务',
        'shp': 'Shapefile',
        'tif': 'GeoTIFF',
        'dxf': 'DXF图纸'
      }
      return typeMap[layer.service_type] || typeMap[layer.file_type] || '未知类型'
    }
    
    // 获取图层图标
    const getLayerIcon = (layer) => {
      const iconMap = {
        'raster': '🖼️',
        'vector': '📍',
        'geoserver': '🌐',
        'martin': '⚡',
        'shp': '📄',
        'tif': '🖼️',
        'dxf': '📐'
      }
      return iconMap[layer.type] || iconMap[layer.service_type] || iconMap[layer.file_type] || '📄'
    }
    
    // 显示添加图层对话框
    const showAddLayerDialog = async () => {
      addLayerDialogVisible.value = true
      await loadAvailableLayers()
    }
    
    // 加载可用图层
    const loadAvailableLayers = async () => {
      loadingLayers.value = true
      try {
        // 参考OpenLayers版本的实现 - 使用正确的API
        const params = { ...layerSearchForm }
        Object.keys(params).forEach(key => params[key] === '' && delete params[key])

        const response = await gisApi.getFiles(params)
        let filteredFiles = response.data.files || []

        if (layerSearchForm.service_type) {
          filteredFiles = filteredFiles.filter(file => {
            if (layerSearchForm.service_type === 'geoserver') {
              return file.geoserver_service?.is_published
            } else if (layerSearchForm.service_type === 'martin') {
              return file.martin_service?.is_published
            }
            return false
          })
        }

        availableLayers.value = filteredFiles.map(file => ({
          ...file,
          layer_name: file.layer_name || file.file_name || file.original_name || '未命名图层'
        }))
        totalLayers.value = availableLayers.value.length
      } catch (error) {
        console.error('加载图层失败:', error)
        ElMessage.error('加载图层列表失败')
        // 使用模拟数据作为降级处理
        availableLayers.value = [
          {
            id: 1,
            name: '示例矢量图层',
            description: '这是一个示例矢量图层',
            service_type: 'geoserver',
            file_type: 'shp',
            type: 'vector',
            url: 'http://example.com/geoserver/wms'
          },
          {
            id: 2,
            name: '示例栅格图层',
            description: '这是一个示例栅格图层',
            service_type: 'martin',
            file_type: 'tif',
            type: 'raster',
            url: 'http://example.com/tiles/{z}/{x}/{y}.png'
          }
        ]
        totalLayers.value = availableLayers.value.length
      } finally {
        loadingLayers.value = false
      }
    }
    
    // 搜索图层
    const searchLayers = () => {
      currentPage.value = 1
      loadAvailableLayers()
    }
    
    // 重置搜索
    const resetSearch = () => {
      Object.assign(layerSearchForm, {
        service_type: '',
        file_type: '',
        keyword: ''
      })
      searchLayers()
    }
    
    // 切换图层选择
    const toggleLayerSelection = (layer) => {
      const index = selectedLayers.value.indexOf(layer.id)
      if (index > -1) {
        selectedLayers.value.splice(index, 1)
      } else {
        selectedLayers.value.push(layer.id)
      }
    }

    // 检查图层是否已在场景中
    const isLayerInScene = (fileId, serviceType) => {
      return layersList.value.some(layer => layer.file_id === fileId && layer.service_type === serviceType)
    }

    // 检查文件是否有任何已发布的服务
    const hasAnyPublishedService = (file) => {
      return (file.geoserver_service?.is_published) || (file.martin_service?.is_published)
    }

    // 添加图层到场景 - 参考OpenLayers版本实现
    const addLayerToScene = async (file, serviceType) => {
      try {
        if (!selectedSceneId.value) {
          ElMessage.error('缺少场景ID，无法添加图层')
          return
        }
        
        const serviceInfo = serviceType === 'martin' ? file.martin_service : file.geoserver_service
        
        if (!serviceInfo?.is_published) {
          ElMessage.error('服务未发布或不存在')
          return
        }
        
        let layerData = {
          layer_name: file.file_name,
          visible: true,
          service_type: serviceType,
          file_id: file.id,
          file_type: file.file_type,
          discipline: file.discipline
        }
        
        if (serviceType === 'martin') {
          const martinServices = await gisApi.searchMartinServices({ file_id: serviceInfo.file_id })
          
          const martinService = martinServices.data.services.find(service => service.file_id === serviceInfo.file_id)
          
          if (!martinService) {
            ElMessage.error('未找到对应的Martin服务')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: String(martinService.database_record_id || martinService.id),
            martin_service_id: String(martinService.database_record_id || martinService.id),
            mvt_url: serviceInfo.mvt_url,
            tilejson_url: serviceInfo.tilejson_url
          }
        } else {
          const geoserverLayerId = serviceInfo.layer_id
          if (!geoserverLayerId) {
            ElMessage.error('GeoServer服务缺少图层ID')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: String(geoserverLayerId),
            geoserver_layer_name: serviceInfo.layer_name,
            wms_url: serviceInfo.wms_url,
            wfs_url: serviceInfo.wfs_url
          }
        }
        
        await gisApi.addLayerToScene(selectedSceneId.value, layerData)
        
        ElMessage.success(`图层 "${file.file_name}" 添加成功`)
        
        addLayerDialogVisible.value = false
        fetchSceneLayers(selectedSceneId.value)
        
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || '添加图层失败'
        ElMessage.error(`添加图层失败: ${errorMessage}`)
      }
    }
    
    // 添加选中图层
    const addSelectedLayers = () => {
      const layersToAdd = availableLayers.value.filter(layer => 
        selectedLayers.value.includes(layer.id)
      )
      
      layersToAdd.forEach(async (layer) => {
        // 检查是否有可用的服务
        if (layer.martin_service?.is_published) {
          await addLayerToScene(layer, 'martin')
        } else if (layer.geoserver_service?.is_published) {
          await addLayerToScene(layer, 'geoserver')
        }
      })
      
      selectedLayers.value = []
      addLayerDialogVisible.value = false
    }
    
    // 处理分页变化
    const handlePageChange = (page) => {
      currentPage.value = page
      loadAvailableLayers()
    }
    
    // 场景变化
    const onSceneChange = (sceneId) => {
      selectedSceneId.value = sceneId
      
      // 更新URL参数
      router.replace({
        name: 'MapDeckGL',
        query: { scene_id: sceneId }
      })
      
      fetchSceneLayers(sceneId)
    }
    
    // 切换图层缓存
    const toggleLayersCache = () => {
      layersCacheEnabled.value = !layersCacheEnabled.value
      ElMessage.success(layersCacheEnabled.value ? '已开启图层缓存' : '已关闭图层缓存')
    }
    
    // 获取场景列表
    const fetchSceneList = async () => {
      try {
        const response = await gisApi.getScenes()
        sceneList.value = response.data.scenes
        //console.log('sceneListlen:', sceneList.value.length)
        // 如果URL中有scene_id参数，设置为当前选中的场景
        const sceneIdFromQuery = route.query.scene_id
        //console.log('sceneIdFromQuery:', sceneIdFromQuery)
        if (sceneIdFromQuery) {
          selectedSceneId.value = sceneIdFromQuery
        } else if (sceneList.value.length > 0) {
          // 如果没有指定场景，选择第一个场景
          selectedSceneId.value = sceneList.value[0].id
        }
      } catch (error) {
        console.error('获取场景列表失败', error)
        ElMessage.error('获取场景列表失败')
      }
    }

    // 获取场景图层
    const fetchSceneLayers = async (sceneId) => {
      if (!sceneId) {
        layersList.value = []
        currentActiveLayer.value = null
        return
      }
      
      try {
        loading.value = true
        const response = await gisApi.getScene(sceneId)
        layersList.value = response.data.layers || []
        
        // 🔥 初始化图层不透明度（如果没有设置或为0则默认为1）
        layersList.value.forEach(layer => {
          if (layer.opacity === undefined || layer.opacity === null || layer.opacity === 0) {
            layer.opacity = 1.0  // 默认100%不透明度
          }
          // 确保数值在有效范围内
          layer.opacity = Math.max(0, Math.min(1, parseFloat(layer.opacity) || 1.0))
        })
        
        // 清除选中状态
        currentActiveLayer.value = null
      } catch (error) {
        console.error('获取场景图层失败', error)
        ElMessage.error('获取场景图层失败')
        layersList.value = []
      } finally {
        loading.value = false
      }
    }

    // 监听选中场景变化
    watch(selectedSceneId, (newSceneId) => {
      if (newSceneId) {
        fetchSceneLayers(newSceneId)
      }
    })

    // 组件挂载时获取数据
    onMounted(() => {
      fetchSceneList()
    })
    
    return {
      // 组件引用
      mapViewer,
      
      // 响应式数据
      layerPanelCollapsed,
      // 🔥 手机端抽屉相关
      mobileDrawerVisible,
      mobileActiveTab,
      toggleMobileDrawer,
      closeMobileDrawer,
      selectMobileScene,
      
      // 🔥 拖拽手柄相关
      isDragging,
      handleDrawerHandleClick,
      handleDrawerDragStart,
      addLayerDialogVisible,
      loadingLayers,
      layersCacheEnabled,
      loading,
      layersList,
      availableLayers,
      selectedLayers,
      currentPage,
      pageSize,
      totalLayers,
      sceneList,
      selectedSceneId,
      layerSearchForm,
      currentActiveLayer,
      
      // 计算属性
      isMobile,
      sortedLayersList,
      
      // 方法
      onMapReady,
      onLayerClick,
      toggleLayerPanel,

      toggleLayerVisibility,
      updateLayerOpacity,
      zoomToLayer,
      removeLayer,
      getLayerTypeText,
      getLayerIcon,
      showAddLayerDialog,
      showStyleDialog,
      getServiceTypeClass,
      getServiceTypeText,
      getLayerStatusClass,
      getLayerStatusText,
      searchLayers,
      resetSearch,
      
      toggleLayerSelection,
      addSelectedLayers,
      addLayerToScene,
      isLayerInScene,
      hasAnyPublishedService,
      loadAvailableLayers,
      handlePageChange,
      onSceneChange,
      toggleLayersCache,
      fetchSceneList,
      fetchSceneLayers,
      selectLayer
    }
  }
}
</script>

<style>
/* 全局样式 - 重置el-main的默认样式 */
.el-main {
  padding: 0 !important;
}
</style>

<style scoped>
.map-view {
  height: 100%; /* 使用100%适应父容器(el-main)的高度：calc(100vh - 60px) */
  width: 100%; /* 确保宽度也是100% */
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin: 0 !important; /* 强制移除外边距，消除与el-main的白边 */
  padding: 0 !important; /* 强制移除内边距 */
}

.map-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  height: 100%;
  width: 100%; /* 确保宽度100% */
  overflow: hidden;
  margin: 0; /* 移除外边距 */
  padding: 0; /* 移除内边距 */
  border: none; /* 移除边框 */
  background: transparent; /* 透明背景 */
}

/* 左侧图层面板 */
.layer-panel {
  width: 350px;
  background: #f8f9fa;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  z-index: 1000;
  position: relative;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
}

.layer-panel.collapsed {
  width: 48px;
  min-width: 48px;
  max-width: 48px;
  background: #e8f4f8;
}

.panel-content {
  width: 350px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 0 8px 8px 0;
  margin: 4px 0 4px 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #fafbfc 0%, #f8f9fa 100%);
  border-radius: 0 8px 0 0;
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
  color: #909399;
}

.panel-toggle-btn {
  padding: 4px 8px !important;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.panel-toggle-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.toggle-icon {
  font-size: 14px;
  color: #606266;
  font-weight: bold;
}

.panel-toggle-btn:hover .toggle-icon {
  color: #409eff;
}

/* 收起状态下的内容样式 */
.collapsed-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

/* 收起状态下的场景选择样式 */
.collapsed-scene-selector {
  padding: 8px 0 5px 0;
  border-bottom: 1px solid #e4e7ed;
}

.collapsed-section-title {
  font-size: 8px;
  color: #909399;
  text-align: center;
  margin-bottom: 4px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.collapsed-scene-item {
  position: relative;
  height: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 1px 2px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 2px;
  user-select: none;
}

.collapsed-scene-item:hover {
  background: rgba(103, 194, 58, 0.1);
  cursor: pointer;
}

.collapsed-scene-item:active {
  transform: scale(0.95);
  background: rgba(103, 194, 58, 0.2);
}

.collapsed-scene-item.active {
  background: rgba(103, 194, 58, 0.15);
  border-left: 3px solid #67c23a;
}

.scene-short-name {
  font-size: 11px;
  font-weight: 600;
  color: #67c23a;
  text-align: center;
  line-height: 1.1;
  max-width: 36px;
  word-break: break-all;
  padding: 0 2px;
}

.collapsed-scene-item.active .scene-short-name {
  color: #5ca632;
}

.scene-active-dot {
  position: absolute;
  bottom: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #67c23a;
}

/* 分隔线样式 */
.collapsed-separator {
  height: 1px;
  background: linear-gradient(90deg, transparent, #e4e7ed 20%, #e4e7ed 80%, transparent);
  margin: 5px 4px;
}

.collapsed-layers {
  flex: 1;
  overflow-y: auto;
  padding: 5px 0;
}

.collapsed-layer-item {
  position: relative;
  height: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 1px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
  margin: 1px 2px;
  user-select: none; /* 防止双击时选中文本 */
}

.collapsed-layer-item:hover {
  background: rgba(64, 158, 255, 0.1);
  cursor: pointer;
}

/* 双击时的反馈效果 */
.collapsed-layer-item:active {
  transform: scale(0.95);
  background: rgba(64, 158, 255, 0.2);
}

/* 双击动画效果 */
@keyframes dblclick-zoom {
  0% { transform: scale(1); }
  50% { transform: scale(0.9); }
  100% { transform: scale(1); }
}

.collapsed-layer-item.zoom-animation {
  animation: dblclick-zoom 0.2s ease-in-out;
}

.collapsed-layer-item.active {
  background: rgba(64, 158, 255, 0.15);
  border-left: 3px solid #409eff;
}

.collapsed-layer-item.invisible {
  opacity: 0.5;
}
.collapsed-toggle {
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.collapsed-toggle:hover {
  background: #e6f1fc;
}

.scene-selector {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* 图层卡片 */
.layer-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.layer-card {
  /* CSS变量定义 - 与OpenLayers保持一致 */
  --layer-card-spacing: 4px;
  --layer-card-padding: 6px 10px;
  --layer-card-border-radius: 6px;
  --layer-info-spacing: 2px;
  --tag-padding: 0px 4px;

  background: white;
  border: 1px solid #e4e7ed;
  border-radius: var(--layer-card-border-radius);
  margin-bottom: var(--layer-card-spacing);
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}


.layer-card:hover {
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.08);
  border-color: #c6e2ff;
}

.layer-card.active {
  border-color: #409eff;
  box-shadow: 0 1px 8px rgba(64, 158, 255, 0.15);
}

.layer-card.invisible {
  opacity: 0.6;
}

.layer-card-header {
  padding: var(--layer-card-padding);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f5f7fa;
  background: white;
  border-radius: var(--layer-card-border-radius) var(--layer-card-border-radius) 0 0;
}

.layer-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  flex: 1;
}

.layer-name {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.active-indicator {
  color: #409eff;
  font-size: 16px;
}

.layer-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.zoom-btn, .remove-btn {
  padding: 4px;
  color: #666;
  transition: color 0.2s;
}

.zoom-btn:hover {
  color: #409eff;
}

.remove-btn:hover {
  color: #f56c6c;
}

.layer-card-info {
  padding: var(--layer-card-padding);
  display: flex;
  flex-wrap: wrap;
  gap: var(--layer-info-spacing);
  border-bottom: 1px solid #f5f7fa;
}

.tag {
  display: inline-block;
  padding: var(--tag-padding);
  background: #f5f7fa;
  color: #4e5969;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
}

.tag.service-geoserver {
  background: #e1f3d8;
  color: #67c23a;
}

.tag.service-martin {
  background: #fdf6ec;
  color: #e6a23c;
}

.tag.service-wms {
  background: #f0f9ff;
  color: #409eff;
}

.tag.service-mvt {
  background: #f5f2ff;
  color: #9c88ff;
}

.tag.status-visible {
  background: #e1f3d8;
  color: #67c23a;
}

.tag.status-hidden {
  background: #fef0f0;
  color: #f56c6c;
}

/* 🔥 透明度控制样式 */
.layer-opacity-control {
  padding: var(--layer-card-padding);
  background: #fafbfc;
  border-radius: 0 0 var(--layer-card-border-radius) var(--layer-card-border-radius);
}

.opacity-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.opacity-icon {
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}

.opacity-label {
  font-size: 11px;
  color: #606266;
  white-space: nowrap;
  flex-shrink: 0;
}

.opacity-value {
  font-size: 11px;
  color: #409eff;
  font-weight: 500;
  min-width: 30px;
  text-align: right;
  flex-shrink: 0;
}

.opacity-slider {
  flex: 1;
  margin: 0 8px;
}

.opacity-slider :deep(.el-slider__runway) {
  height: 4px;
  background: #e4e7ed;
}

.opacity-slider :deep(.el-slider__bar) {
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a);
}

.opacity-slider :deep(.el-slider__button) {
  width: 14px;
  height: 14px;
  border: 2px solid #409eff;
  background: #fff;
}




.collapsed-section-title {
  writing-mode: horizontal-tb;
  text-orientation: mixed;
  padding: 4px 2px;
  text-align: center;
  font-size: 10px;
  color: #909399;
  font-weight: 500;
  background: #f0f2f5;
  margin: 1px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed-scene-selector {
  padding: 8px 0;
}





.scene-short-name {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
  word-break: break-all;
}

.scene-active-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 6px;
  height: 6px;
  background: #67c23a;
  border-radius: 50%;
  border: 1px solid white;
}

.collapsed-separator {
  height: 1px;
  background: #e4e7ed;
  margin: 8px 4px;
}

.collapsed-layers {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.collapsed-layer-item {
  margin: 4px;
  padding: 6px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  text-align: center;
}

.collapsed-layer-item:hover {
  background: #ecf5ff;
  transform: translateX(2px);
}

.collapsed-layer-item.active {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.collapsed-layer-item.invisible {
  opacity: 0.5;
  background: #f5f7fa;
}

.layer-short-name {
  font-size: 10px;
  font-weight: 500;
  line-height: 1.2;
  word-break: break-all;
}

.layer-active-dot {
  position: absolute;
  top: 1px;
  right: 1px;
  width: 6px;
  height: 6px;
  background: #67c23a;
  border-radius: 50%;
  border: 1px solid white;
}

.layer-invisible-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 6px;
  height: 6px;
  background: #f56c6c;
  border-radius: 50%;
  border: 1px solid white;
}

.layer-card-body {
  padding: 12px;
  border-top: 1px solid #f0f0f0;
}

.layer-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.layer-type, .layer-service {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #f0f2f5;
  color: #666;
}

.layer-opacity {
  margin-top: 8px;
}

.opacity-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.opacity-slider {
  width: 100%;
}

.layer-control {
  margin-bottom: 12px;
}

.layer-control label {
  display: block;
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.layer-buttons {
  display: flex;
  gap: 8px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.empty-description {
  font-size: 12px;
}



.expand-btn {
  padding: 8px 12px !important;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.expand-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.expand-btn .toggle-icon {
  font-size: 16px;
  color: #606266;
  font-weight: bold;
}

.expand-btn:hover .toggle-icon {
  color: #409eff;
}

/* 地图区域 */
.map-container-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: transparent;
  min-height: 0; /* 防止flex容器高度计算问题 */
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  outline: none;
}

.map-container-wrapper.with-panel {
  /* 当面板展开时不需要额外的margin */
}

/* 🔥 手机端专用样式 - 桌面端隐藏移动端组件 */
.mobile-layer-fab,
.mobile-drawer-overlay {
  display: none;
}

/* 桌面端显示侧边栏，手机端隐藏 */
.desktop-only {
  display: block;
}



/* 手机端样式 */
@media (max-width: 768px) {
  /* 隐藏桌面端组件 */
  .desktop-only {
    display: none !important;
  }

  /* 显示手机端组件 */
  .mobile-only {
    display: block !important;
  }

  /* 手机端抽屉样式 */
  .mobile-drawer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 2000;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
  }

  .mobile-drawer-overlay.show {
    opacity: 1;
    visibility: visible;
  }
/* 🔥 抽屉面板 */
.mobile-drawer {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-radius: 20px 20px 0 0;
    transform: translateY(100%);
    transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    max-height: 75vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.15);
    overflow: hidden;
    /* 🔥 为拖拽准备的变量 */
    --drawer-opacity: 1;
    opacity: var(--drawer-opacity);
  }
  
  .mobile-drawer.show {
    transform: translateY(0);
  }
  
  /* 抽屉头部 */
  .mobile-drawer-header {
    padding: 15px 20px 10px;
    border-bottom: 1px solid #f0f0f0;
    flex-shrink: 0;
    background: white;
  }
  
  .drawer-handle {
    width: 50px; /* 🔥 手机应用常见的短横线宽度 */
    height: 4px; /* 🔥 适中的高度 */
    background: #e4e7ed; /* 🔥 更淡的颜色，低调不显眼 */
    border-radius: 2px; /* 🔥 圆润的圆角 */
    margin: 8px auto 16px; /* 🔥 上下间距，居中 */
    cursor: grab; /* 🔥 显示拖拽光标 */
    transition: all 0.15s ease; /* 🔥 更快的过渡 */
    position: relative;
    user-select: none; /* 🔥 防止选中文本 */
    opacity: 0.6; /* 🔥 更透明，更低调 */
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08); /* 🔥 微妙的阴影 */
  }

  /* 🔥 为了增加点击区域，使用伪元素 */
  .drawer-handle::before {
    content: '';
    position: absolute;
    top: -8px;
    left: -8px;
    right: -8px;
    bottom: -8px;
    cursor: grab;
  }
  
  .drawer-handle:hover {
    background: #d3d4d6; /* 🔥 悬停时稍微深一点，但仍然低调 */
    opacity: 1; /* 🔥 悬停时不透明 */
    cursor: grab;
  }
  
  .drawer-handle:active,
  .drawer-handle.dragging {
    background: #c0c4cc; /* 🔥 拖拽时稍微深一点 */
    opacity: 1; /* 🔥 拖拽时不透明 */
    cursor: grabbing; /* 🔥 拖拽光标 */
  }

  .drawer-handle:active::before,
  .drawer-handle.dragging::before {
    cursor: grabbing; /* 🔥 伪元素也要改变光标 */
  }
  
  .drawer-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .drawer-title h3 {
    margin: 0;
    font-size: 18px;
    color: #303133;
    font-weight: 600;
  }
  
  .drawer-actions {
    display: flex;
    gap: 8px;
  }
  
  .drawer-actions .el-button {
    border-radius: 8px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 4px; /* 🔥 图标和文字间距 */
    padding: 8px 12px; /* 🔥 调整内边距适应文字 */
  }
  
  .drawer-actions .el-button i {
    font-size: 14px; /* 🔥 确保图标大小合适 */
  }
  
  .drawer-actions .el-button span {
    font-size: 13px; /* 🔥 文字大小 */
    white-space: nowrap; /* 🔥 防止文字换行 */
  }
  
  /* 抽屉内容 */
  .mobile-drawer-content {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: white;
  }

  .mobile-drawer-close {
    background: none;
    border: none;
    font-size: 24px;
    color: #909399;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mobile-drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  /* 手机端标签页 */
  .mobile-tabs {
    display: flex;
    border-bottom: 1px solid #e4e7ed;
    background: #f8f9fa;
  }

  .mobile-tab {
    flex: 1;
    padding: 16px;
    text-align: center;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: #606266;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    position: relative;
  }

  .mobile-tab.active {
    color: #409eff;
    border-bottom-color: #409eff;
    background: white;
  }

  .tab-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: #f56c6c;
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    min-width: 16px;
    text-align: center;
  }

  .mobile-tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  /* 手机端场景列表 */
  .mobile-scene-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .mobile-scene-item {
    border: 1px solid #e4e7ed;
    border-radius: 12px;
    padding: 16px;
    background: white;
    transition: all 0.3s;
    cursor: pointer;
  }

  .mobile-scene-item:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }

  .mobile-scene-item.active {
    border-color: #409eff;
    background: #f0f9ff;
  }

  .scene-info h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }

  .scene-info p {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }

  .scene-meta {
    margin-top: 8px;
  }

  /* 手机端图层列表 */
  .mobile-layer-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .mobile-layer-item {
    border: 1px solid #e4e7ed;
    border-radius: 12px;
    padding: 16px;
    background: white;
    transition: all 0.3s;
  }

  .mobile-layer-item:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }

  .mobile-layer-item.active {
    border-color: #409eff;
    background: #f0f9ff;
  }

  .mobile-layer-item.invisible {
    opacity: 0.6;
  }

  .layer-main-info {
    margin-bottom: 12px;
  }

  .layer-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .layer-name {
    font-weight: 600;
    font-size: 15px;
    color: #303133;
    flex: 1;
  }

  .active-indicator {
    color: #409eff;
    font-size: 16px;
  }

  .layer-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }

  .tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    background: #f0f0f0;
    color: #606266;
  }

  .mobile-opacity-control {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .opacity-label {
    font-size: 13px;
    color: #606266;
    min-width: 60px;
  }

  .mobile-opacity-slider {
    flex: 1;
  }

  .opacity-value {
    font-size: 13px;
    color: #409eff;
    min-width: 40px;
    text-align: right;
  }

  .layer-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .action-btn {
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #dcdfe6;
    background: white;
    color: #606266;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .action-btn:hover {
    border-color: #409eff;
    color: #409eff;
  }

  .action-btn.zoom-btn:hover {
    border-color: #67c23a;
    color: #67c23a;
  }

  .action-btn.style-btn:hover {
    border-color: #e6a23c;
    color: #e6a23c;
  }

  .action-btn.delete-btn:hover {
    border-color: #f56c6c;
    color: #f56c6c;
  }

  .mobile-empty {
    text-align: center;
    padding: 40px 20px;
    color: #909399;
  }

  .mobile-empty i {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .mobile-empty p {
    margin: 0 0 16px 0;
    font-size: 14px;
  }

  /* 手机端浮动按钮 */
  .mobile-layer-fab {
    position: fixed;
    left: 50%;
    bottom: 5px;
    transform: translateX(-50%);
    z-index: 2000;
    background: #409EFF;
    color: #fff;
    border-radius: 24px;
    box-shadow: 0 4px 16px rgba(64,158,255,0.18);
    padding: 0 5px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 2px;
    cursor: pointer;
    transition: box-shadow 0.2s, background 0.2s;
    border: none;
    outline: none;
    user-select: none;
    will-change: transform;
    opacity: 0.96;
  }
  .mobile-layer-fab:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
  }
  
  .mobile-layer-fab:active {
    transform: scale(0.95);
  }
  
  .fab-content {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 20px;
    color: white;
    font-weight: 500;
    position: relative;
  }
  
  .fab-content i {
    font-size: 18px;
  }
  
  .fab-text {
    font-size: 14px;
    font-weight: 600;
    
  }
  
  .fab-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: #f56c6c;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    border: 2px solid white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  /* 手机端地图容器 */
  .map-container {
    height: 100vh;
    width: 100vw;
  }

  /* 手机端按钮样式 */
  .mobile-btn {
    padding: 8px 16px;
    font-size: 13px;
    border-radius: 6px;
    border: 1px solid #dcdfe6;
    background: white;
    color: #606266;
    cursor: pointer;
    transition: all 0.3s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }

  .mobile-btn:hover {
    border-color: #409eff;
    color: #409eff;
  }

  .mobile-btn.primary {
    background: #409eff;
    border-color: #409eff;
    color: white;
  }

  .mobile-btn.primary:hover {
    background: #337ecc;
    border-color: #337ecc;
  }

  .mobile-btn.danger {
    background: #f56c6c;
    border-color: #f56c6c;
    color: white;
  }

  .mobile-btn.danger:hover {
    background: #e74c3c;
    border-color: #e74c3c;
  }
}

/* 桌面端样式 */
.desktop-only {
  display: block;
}

.mobile-only {
  display: none;
}

/* 添加图层对话框 */
.add-layer-dialog-content {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.layer-search-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.available-layers {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
  padding: 10px 0;
}

.available-layer-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.available-layer-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.available-layer-item.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.layer-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-placeholder {
  font-size: 20px;
  color: #909399;
}

.layer-details {
  flex: 1;
}

.layer-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 5px;
  word-break: break-word;
}

.layer-description {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.4;
}

.layer-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.meta-item {
  font-size: 11px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 3px;
}

.layer-services {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px;
  background: #fafbfc;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.service-item .el-tag {
  flex-shrink: 0;
}

.service-item .el-button {
  flex-shrink: 0;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding: 15px 0;
  border-top: 1px solid #ebeef5;
}

/* 🔥 桌面端面板收缩功能样式加强 */
@media (min-width: 769px) {
  .desktop-only {
    display: block !important;
  }
  
  .mobile-only {
    display: none !important;
  }
  
  .layer-panel {
    width: 350px !important;
    transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
  }
  
  .layer-panel.collapsed {
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
  }
  
  .map-container-wrapper {
    transition: margin-left 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  }
  
  /* 确保收起状态下内容正确显示 */
  .layer-panel.collapsed .panel-content {
    display: none !important;
  }
  
  .layer-panel.collapsed .collapsed-content {
    display: flex !important;
    flex-direction: column;
    height: 100%;
  }
  
  /* 🔥 确保桌面端操作按钮始终可见 */
  .layer-actions {
    opacity: 1 !important;
    display: flex !important;
  }
  
  .layer-actions .el-button {
    opacity: 1 !important;
    visibility: visible !important;
  }
}

/* 🔥 移动端浮动按钮样式 */
.mobile-layer-toggle {
  position: absolute;
  bottom: 80px;
  right: 20px;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.mobile-layer-toggle .el-button {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border: none;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.4);
}

.mobile-layer-toggle .el-button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.5);
}

/* 🔥 移动端抽屉样式 */
.mobile-layer-drawer {
  z-index: 1500;
}

.mobile-layer-drawer :deep(.el-drawer) {
  background: #f8f9fa;
}

.mobile-layer-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 16px 20px;
  background: linear-gradient(90deg, #fafbfc 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e4e7ed;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.scene-selector.mobile {
  padding: 16px 20px;
  background: white;
  margin: 0 0 16px 0;
  border-radius: 8px;
  margin: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.mobile-layer-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.mobile-layer-item {
  background: white;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
}

.mobile-layer-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.mobile-layer-item .layer-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #fafbfc 0%, #fff 100%);
}

.mobile-layer-item .layer-info .layer-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.mobile-layer-item .layer-info .layer-type {
  font-size: 12px;
  color: #909399;
}

.mobile-layer-item .layer-controls {
  padding: 16px;
  border-top: 1px solid #f5f7fa;
  background: #fafbfc;
}

.mobile-layer-item .opacity-control {
  margin-bottom: 16px;
}

.mobile-layer-item .opacity-control span {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  display: block;
}

.mobile-layer-item .layer-actions {
  display: flex;
  gap: 12px;
}

.mobile-layer-item .layer-actions .el-button {
  flex: 1;
}

/* 🔥 手机端样式 */
@media (max-width: 768px) {
  /* 🔥 确保手机端没有白边和高度问题 */
  .map-view {
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }
  
  .map-content {
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  
  .map-container-wrapper {
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  
  /* 隐藏桌面端侧边栏 */
  .desktop-only {
    display: none !important;
  }
  
  /* 显示手机端组件 */
  .mobile-only {
    display: block !important;
  }
  
  /* 🔥 确保Element Plus对话框在手机端能正确显示 */
  :deep(.el-dialog__wrapper) {
    z-index: 2000 !important;
  }
  
  :deep(.el-overlay) {
    z-index: 2000 !important;
  }
  
  /* 地图容器占满全屏 */
  .map-container-wrapper {
    width: 100% !important;
    margin-left: 0 !important;
  }
}
</style>