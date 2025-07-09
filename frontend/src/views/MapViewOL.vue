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
                    <span class="opacity-text">不透明度</span>
                    <el-slider
                      v-model="layer.opacity"
                      :min="0"
                      :max="1"
                      :step="0.1"
                      :show-tooltip="false"
                      size="small"
                      @input="onLayerOpacityChange(layer)"
                      @click.stop
                      @mousedown.stop
                      @dragstart.stop="$event.preventDefault()"
                      class="opacity-slider"
                    />
                    <span class="opacity-value">{{ Math.round((layer.opacity || 1) * 100) }}%</span>
                  </div>
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
          
          <!-- 收起状态下的场景选择 -->
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
                :key="layer.id" 
                class="collapsed-layer-item"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                  'invisible': !layer.visibility
                }"
                @click="selectLayer(layer)"
                @dblclick="handleCollapsedLayerDblClick(layer, $event)"
                :title="`${layer.layer_name}
🔍 双击缩放到图层范围
👆 单击选择图层`"
              >
              <!-- 可见性指示器 -->
              <div class="visibility-indicator" :class="{ 'visible': layer.visibility }"></div>
              <!-- 图层名称前两个字 -->
              <div class="layer-short-name">{{ layer.layer_name.substring(0, 2) }}</div>
              <!-- 当前活动图层标识 -->
              <div v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" 
                   class="active-dot"></div>
            </div>
          </div>
          
          <!-- 图层空状态 -->
          <div class="collapsed-empty" v-else-if="selectedSceneId">
            <i class="el-icon-map-location"></i>
            <div class="empty-text">无图层</div>
          </div>
          
          <!-- 场景空状态 -->
          <div class="collapsed-empty" v-else-if="sceneList && sceneList.length === 0">
            <i class="el-icon-folder"></i>
            <div class="empty-text">无场景</div>
          </div>
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
    <div class="mobile-drawer-overlay" :class="{ 'show': mobileDrawerVisible }" @click="closeMobileDrawer">
      <div class="mobile-drawer" :class="{ 'show': mobileDrawerVisible }" @click.stop>
        <!-- 抽屉头部 -->
        <div class="mobile-drawer-header">
          <div 
            class="drawer-handle" 
            :class="{ 'dragging': isDragging }"
            @click="handleDrawerHandleClick"
            @mousedown="handleDrawerDragStart"
            @touchstart="handleDrawerDragStart"
          ></div>
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
                :key="layer.id"
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
                      @input="onLayerOpacityChange(layer)"
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

    <!-- 图层信息对话框 -->
    <el-dialog title="图层信息" v-model="layerInfoDialogVisible" width="500px">
      <div v-if="currentLayerInfo">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="图层名称">
            {{ currentLayerInfo.layer_name }}
          </el-descriptions-item>
          <el-descriptions-item label="文件类型">
            {{ currentLayerInfo.file_type }}
          </el-descriptions-item>
          <el-descriptions-item label="专业">
            {{ currentLayerInfo.discipline }}
          </el-descriptions-item>
          <el-descriptions-item label="维度">
            {{ currentLayerInfo.dimension }}
          </el-descriptions-item>
          <el-descriptions-item label="可见性">
            {{ currentLayerInfo.visibility ? '可见' : '隐藏' }}
          </el-descriptions-item>
          <el-descriptions-item label="GeoServer图层">
            {{ currentLayerInfo.geoserver_layer }}
          </el-descriptions-item>
          <el-descriptions-item label="WMS服务">
            <el-link :href="currentLayerInfo.wms_url" target="_blank" type="primary">
              {{ currentLayerInfo.wms_url }}
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="WFS服务" v-if="currentLayerInfo.wfs_url">
            <el-link :href="currentLayerInfo.wfs_url" target="_blank" type="primary">
              {{ currentLayerInfo.wfs_url }}
            </el-link>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 场景管理对话框 -->
    <el-dialog 
      :title="editingScene ? '编辑场景' : '创建场景'" 
      v-model="sceneDialogVisible" 
      width="500px"
    >
      <el-form :model="sceneForm" label-width="80px">
        <el-form-item label="场景名称" required>
          <el-input v-model="sceneForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="场景描述">
          <el-input 
            v-model="sceneForm.description" 
            type="textarea"
            :rows="3"
            placeholder="请输入场景描述（可选）" 
          />
        </el-form-item>
        <el-form-item label="访问权限">
          <el-switch 
            v-model="sceneForm.is_public" 
            active-text="公开"
            inactive-text="私有"
            :active-value="true"
            :inactive-value="false"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            公开场景所有用户可见，私有场景仅创建者可见
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sceneDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveScene">
          {{ editingScene ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, reactive, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import gisApi from '@/api/gis'
import MapViewerOL from '@/components/MapViewerOL.vue'
import { transformExtent } from 'ol/proj'

export default {
  name: 'MapViewOL',
  components: { MapViewerOL },
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    const mapViewerRef = ref(null)
    const layerPanelCollapsed = ref(false)
    
    // 场景对话框
    const sceneDialogVisible = ref(false)
    const editingScene = ref(null)
    const sceneForm = reactive({
      name: '',
      description: '',
      is_public: true
    })
    
    // 响应式数据
    const sceneList = ref([])
    const selectedSceneId = ref(null)
    const layersList = ref([])  // 确保初始化为空数组
    const loading = ref(false)
    const layerInfoDialogVisible = ref(false)
    const currentLayerInfo = ref(null)
    
    // 拖拽相关状态
    const draggingLayerId = ref(null)
    const dragStartIndex = ref(-1)
    const currentActiveLayer = ref(null)
    
    // 🔥 手机端抽屉相关状态
    const mobileDrawerVisible = ref(false)
    const mobileActiveTab = ref('layers') // 'scene' or 'layers'
    
    // 🔥 拖拽手柄相关状态
    const isDragging = ref(false)
    const dragStartY = ref(0)
    const drawerStartY = ref(0)
    
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
    
    // 选择场景
     const selectScene = async (sceneId) => {
      if (selectedSceneId.value === sceneId) return
      
      selectedSceneId.value = sceneId
      
      try {
        const response = await gisApi.getScene(sceneId)
        layersList.value = response.data.layers || []
        //console.log('lv-response22:', layersList)
      } catch (error) {
        console.error('加载场景详情失败:', error)
        ElMessage.error('加载场景详情失败')
      }
    } 
    
    // 显示创建场景对话框
    const showCreateSceneDialog = () => {
      editingScene.value = null
      sceneForm.name = ''
      sceneForm.description = ''
      sceneForm.is_public = true
      sceneDialogVisible.value = true
    }
    
    // 编辑场景
    const editScene = (scene) => {
      editingScene.value = scene
      sceneForm.name = scene.name
      sceneForm.description = scene.description || ''
      sceneForm.is_public = scene.is_public
      sceneDialogVisible.value = true
    }
    
    // 保存场景
    const saveScene = async () => {
      if (!sceneForm.name) {
        ElMessage.warning('请输入场景名称')
        return
      }
      
      try {
        if (editingScene.value) {
          await gisApi.updateScene(editingScene.value.id, sceneForm)
          ElMessage.success('场景更新成功')
        } else {
          const response = await gisApi.createScene(sceneForm)
          ElMessage.success('场景创建成功')
          // 如果需要，可以自动选择新创建的场景
          // selectedSceneId.value = response.data.id
        }
        
        sceneDialogVisible.value = false
        await fetchSceneList()
      } catch (error) {
        console.error('保存场景失败:', error)
        ElMessage.error('保存场景失败')
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
        layersList.value = response.data.layers
        
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
    
    // 场景变化处理
    const onSceneChange = (sceneId) => {
      selectedSceneId.value = sceneId
      
      // 更新URL参数
      router.replace({
        name: 'MapOL',
        query: { scene_id: sceneId }
      })
      
      fetchSceneLayers(sceneId)
    }
    
    // 刷新场景
    const refreshScene = () => {
      if (selectedSceneId.value) {
        fetchSceneLayers(selectedSceneId.value)
      }
    }
    
    // 切换图层面板显示
    const toggleLayerPanel = () => {
      layerPanelCollapsed.value = !layerPanelCollapsed.value
      console.log('🔄 面板状态切换:', layerPanelCollapsed.value ? '收起' : '展开')
      
      // 强制DOM更新并检查样式
      nextTick(() => {
        console.log('✅ DOM已更新，当前面板状态:', layerPanelCollapsed.value)
        
        // 调试：检查DOM元素和样式
        const panelElement = document.querySelector('.layer-panel')
        if (panelElement) {
          const computedStyle = window.getComputedStyle(panelElement)
          console.log('📐 面板当前宽度:', computedStyle.width)
          console.log('🎯 面板类名:', panelElement.className)
          console.log('🔄 面板collapsed状态:', panelElement.classList.contains('collapsed'))
        }
      })
    }
    

    
    // 跳转到场景管理
    const goToSceneManage = () => {
      router.push({ name: 'Scene' })
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = async (layer) => {
      try {
        // 先更新数据库中的可见性状态
        await gisApi.updateSceneLayer(selectedSceneId.value, layer.id, {
          visible: layer.visibility
        })
        
        // 通知MapViewerOL组件更新地图显示
        if (mapViewerRef.value && mapViewerRef.value.toggleLayerVisibility) {
          mapViewerRef.value.toggleLayerVisibility(layer)
        } else {
          // 如果直接调用方法不可用，则发送自定义事件
          const event = new CustomEvent('layerVisibilityChanged', {
            detail: {
              layerId: layer.id,
              layer: layer,
              visibility: layer.visibility
            }
          })
          window.dispatchEvent(event)
        }
        
      } catch (error) {
        console.error('更新图层可见性失败', error)
        ElMessage.error('更新图层可见性失败')
        // 回滚状态
        layer.visibility = !layer.visibility
      }
    }

    // 🔥 图层透明度变化处理
    const onLayerOpacityChange = (layer) => {
      // 限制透明度范围
      if (layer.opacity < 0) layer.opacity = 0
      if (layer.opacity > 1) layer.opacity = 1
      
      // 1. 立即更新地图中的图层透明度
      if (mapViewerRef.value && mapViewerRef.value.updateLayerOpacity) {
        mapViewerRef.value.updateLayerOpacity(layer, layer.opacity)
      }
      
      // 2. 防抖更新数据库
      updateLayerOpacityInDatabase(layer)
    }
    
    // 防抖定时器映射
    const opacityUpdateTimers = ref(new Map())
    
    // 🔥 更新数据库中的图层透明度（防抖）
    const updateLayerOpacityInDatabase = async (layer) => {
      if (!selectedSceneId.value || !layer.scene_layer_id) {
        console.warn('缺少场景ID或图层ID，跳过数据库更新')
        return
      }
      
      // 清除之前的定时器
      if (opacityUpdateTimers.value.has(layer.id)) {
        clearTimeout(opacityUpdateTimers.value.get(layer.id))
      }
      
      // 设置新的防抖定时器（500ms后执行）
      const timer = setTimeout(async () => {
        try {
          const updateData = {
            opacity: layer.opacity
          }
          
          //console.log('保存透明度到数据库:', {
          //   scene_id: selectedSceneId.value,
          //   layer_id: layer.id,
          //   opacity: layer.opacity
          // })
          
          // 调用后端API更新透明度
          await gisApi.updateSceneLayer(selectedSceneId.value, layer.id, updateData)
          //console.log('✅ 透明度已保存到数据库')
          
          // 清除定时器
          opacityUpdateTimers.value.delete(layer.id)
        } catch (error) {
          console.error('保存透明度失败:', error)
          ElMessage.error('透明度设置保存失败')
        }
      }, 500)
      
      opacityUpdateTimers.value.set(layer.id, timer)
    }
    
    // 上移图层
    const moveLayerUp = async (index) => {
      if (index === 0) return
      
      // 交换数组中的位置
      const temp = layersList.value[index]
      layersList.value[index] = layersList.value[index - 1]
      layersList.value[index - 1] = temp
      
      // 更新服务器端的顺序
      await updateLayerOrder()
    }
    
    // 下移图层
    const moveLayerDown = async (index) => {
      if (index === layersList.value.length - 1) return
      
      // 交换数组中的位置
      const temp = layersList.value[index]
      layersList.value[index] = layersList.value[index + 1]
      layersList.value[index + 1] = temp
      
      // 更新服务器端的顺序
      await updateLayerOrder()
    }
    
    // 更新图层顺序
    const updateLayerOrder = async () => {
      // 创建顺序映射
      const orderMap = {}
      layersList.value.forEach((layer, index) => {
        orderMap[layer.id] = layersList.value.length - index
      })
      
      try {
        await gisApi.reorderSceneLayers(selectedSceneId.value, orderMap)
      } catch (error) {
        console.error('更新图层顺序失败', error)
        ElMessage.error('更新图层顺序失败')
        // 重新获取图层列表
        fetchSceneLayers(selectedSceneId.value)
      }
    }
    
    // 处理图层操作
    const handleLayerAction = ({ action, layer }) => {
      switch (action) {
        case 'style':
          // 调用MapViewerOL组件的样式设置方法
          if (mapViewerRef.value) {
            mapViewerRef.value.showStyleDialog(layer)
          }
          break
        case 'zoom':
          zoomToLayer(layer)
          break
        case 'info':
          showLayerInfo(layer)
          break
        case 'remove':
          removeLayer(layer)
          break
      }
    }
    
    // 缩放到图层 - 针对OpenLayers优化，支持动态坐标系
    const zoomToLayer = async (layer) => {
      try {
        //console.log('lvzoomToLayer:', layer)
        // 更安全的地图可用性检查
        if (!mapViewerRef.value) {
          ElMessage.error('地图组件引用不存在')
          return
        }
        
        if (!mapViewerRef.value.map) {
          ElMessage.error('地图实例未初始化')
          return
        }
        
        // 确保地图实例是有效的
        const map = mapViewerRef.value.map
        if (!map || typeof map.getView !== 'function') {
          ElMessage.error('地图实例无效')
          return
        }
        
        let bbox = null
        let originalCRS = 'EPSG:4326' // 用于显示的原始坐标系
        
        // 1. 优先使用新的图层边界API（bbox已经是转换后的EPSG:4326坐标）
        try {
          //20250617更改给后端传scene_layer_id，而不是layer.id
          const response = await gisApi.getSceneLayerBounds(layer.scene_layer_id)
          if (response?.success && response.data?.bbox) {
            bbox = response.data.bbox
            // coordinate_system字段仅用于显示原始坐标系，bbox已经是EPSG:4326坐标
            originalCRS = response.data.coordinate_system || 'EPSG:4326'
            //console.log('从图层边界API获取到边界:', bbox, '(已转换为EPSG:4326), 原始坐标系:', originalCRS)
          }
        } catch (apiError) {
          console.warn('图层边界API调用失败，尝试其他方式:', apiError)
        }
        
        // 2. 如果边界API调用失败，尝试从图层属性获取
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
        //console.log('bbox:', bbox)
        // 4. 验证边界框数据并转换格式
        let minx, miny, maxx, maxy
        
        if (bbox.minx !== undefined) {
          // 对象格式 {minx, miny, maxx, maxy}
          minx = parseFloat(bbox.minx)
          miny = parseFloat(bbox.miny)
          maxx = parseFloat(bbox.maxx)
          maxy = parseFloat(bbox.maxy)
        }  else {
          ElMessage.warning('边界框数据格式不正确')
          return
        }
        
        if (isNaN(minx) || isNaN(miny) || isNaN(maxx) || isNaN(maxy)) {
          ElMessage.warning('边界框数据格式错误')
          return
        }
        
        // 5. 构建范围并进行坐标转换
        const originalExtent = [minx, miny, maxx, maxy]
        //console.log(`边界框坐标 (后端已转换为EPSG:4326):`, originalExtent, `原始坐标系: ${originalCRS}`)
        
        let transformedExtent
        try {
          // 由于后端返回的bbox已经是EPSG:4326坐标，直接从EPSG:4326转换到EPSG:3857
          if (mapViewerRef.value.transformCoordinates) {
            transformedExtent = mapViewerRef.value.transformCoordinates(originalExtent, 'EPSG:4326', 'EPSG:3857')
          } else {
            // 备用方案：直接使用OpenLayers的transformExtent
            transformedExtent = ol.proj.transformExtent(originalExtent, 'EPSG:4326', 'EPSG:3857')
          }
          //console.log(`转换后边界 (EPSG:3857):`, transformedExtent)
        } catch (transformError) {
          console.error('坐标转换失败:', transformError)
          ElMessage.error(`坐标转换失败: ${transformError.message}`)
          return
        }
        
        // 6. 缩放到转换后的范围
        const view = map.getView()
        view.fit(transformedExtent, {
          padding: [20, 20, 20, 20], // 边距
          maxZoom: 16, // 最大缩放级别限制
          duration: 1000 // 动画持续时间
        })
        
        // 7. 缩放完成后，设置当前活动图层
        currentActiveLayer.value = layer
        
        // 🔥 手机端：缩放后自动隐藏图层管理面板
        if (mobileDrawerVisible.value) {
          closeMobileDrawer()
        }
        
        ElMessage.success(`已缩放到图层"${layer.layer_name}"范围 (${originalCRS})`)
        
      } catch (error) {
        console.error('缩放到图层失败:', error)
        ElMessage.error(`缩放到图层失败: ${error.message}`)
      }
    }
    
    // 处理收起状态下的图层双击事件
    const handleCollapsedLayerDblClick = async (layer, event) => {
      // 阻止事件冒泡和默认行为
      event.preventDefault()
      event.stopPropagation()
      
      // 添加动画效果
      const target = event.currentTarget
      target.classList.add('zoom-animation')
      
      // 移除动画类（在动画结束后）
      setTimeout(() => {
        target.classList.remove('zoom-animation')
      }, 200)
      
      // 调用缩放函数
      await zoomToLayer(layer)
    }
    
    // 显示图层信息
    const showLayerInfo = (layer) => {
      currentLayerInfo.value = layer
      layerInfoDialogVisible.value = true
    }
    
    // 移除图层
    const removeLayer = (layer) => {
      ElMessageBox.confirm(`确认从场景中移除图层"${layer.layer_name}"？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await gisApi.removeLayerFromScene(selectedSceneId.value, layer.id)
          ElMessage.success('图层移除成功')
          // 刷新图层列表
          fetchSceneLayers(selectedSceneId.value)
        } catch (error) {
          console.error('移除图层失败', error)
          ElMessage.error('移除图层失败')
        }
      }).catch(() => {})
    }

    // 显示添加图层对话框
    const showAddLayerDialog = async () => {
      // 🔥 手机端：显示添加图层对话框前先隐藏图层管理面板
      if (mobileDrawerVisible.value) {
        closeMobileDrawer()
        // 等待下一个tick，确保面板完全隐藏后再显示对话框
        await nextTick()
      }
      
      if (!mapViewerRef.value) {
        console.error('mapViewerRef.value is null or undefined')
        ElMessage.error('地图组件未准备就绪，请稍后再试')
        return
      }
      
      if (typeof mapViewerRef.value.showAddLayerDialog !== 'function') {
        console.error('showAddLayerDialog method not found on mapViewerRef')
        ElMessage.error('添加图层功能暂不可用')
        return
      }
      
      try {
        mapViewerRef.value.showAddLayerDialog()
      } catch (error) {
        console.error('Error calling showAddLayerDialog:', error)
        ElMessage.error('显示添加图层对话框失败')
      }
    }

    // 显示样式设置对话框
    const showStyleDialog = (layer) => {
      // 显示样式对话框前，先将该图层设置为当前图层
      selectLayer(layer)
      
      if (mapViewerRef.value) {
        mapViewerRef.value.showStyleDialog(layer)
      }
      // 🔥 手机端：缩放后自动隐藏图层管理面板
      if (mobileDrawerVisible.value) {
          closeMobileDrawer()
        }
    }

    // 获取服务类型样式类
    const getServiceTypeClass = (serviceType) => {
      switch (serviceType) {
        case 'martin':
          return 'service-martin'
        case 'geoserver':
          return 'service-geoserver'
        default:
          return ''
      }
    }

    // 获取服务类型文本
    const getServiceTypeText = (layer) => {
      switch (layer.service_type) {
        case 'martin':
          // 如果有子类型信息，显示详细类型
          if (layer.martin_service_subtype) {
            const subtype = layer.martin_service_subtype.toUpperCase()
            return `Martin(${subtype})`
          }
          return 'Martin'
        case 'geoserver':
          return 'GeoServer'
        default:
          return '未知'
      }
    }

    // 获取图层状态样式类
    const getLayerStatusClass = (layer) => {
      if (layer.service_type === 'martin') {
        return 'status-published' // Martin服务通常都是已发布的
      }
      if (!layer.geoserver_layer || !layer.wms_url) {
        return 'status-unpublished'
      }
      return 'status-published'
    }

    // 获取图层状态文本
    const getLayerStatusText = (layer) => {
      if (layer.service_type === 'martin') {
        return '已发布'
      }
      if (!layer.geoserver_layer || !layer.wms_url) {
        return '未发布'
      }
      return '已发布'
    }

    // 处理图层添加事件
    const onLayerAdded = () => {
      // 刷新当前场景的图层列表
      if (selectedSceneId.value) {
        fetchSceneLayers(selectedSceneId.value)
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
    
    // 组件卸载时清理资源
    onUnmounted(() => {
      // 清理资源逻辑
    })
    
    // 选择图层
    const selectLayer = (layer) => {
      //console.log('选择图层:', layer.layer_name)
      currentActiveLayer.value = layer
      
      // 通知MapViewerOL组件将该图层置顶
      // if (mapViewerRef.value) {
      //   mapViewerRef.value.bringLayerToTop(layer)
      // }
      
      ElMessage.success(`已选中图层: ${layer.layer_name}`)
    }
    
    // 处理图层选择事件
    const onLayerSelected = (layer) => {
      //console.log('收到图层选择事件:', layer)
      // 直接设置当前活动图层，避免循环调用
      currentActiveLayer.value = layer
    }
    
    // 获取图层类型颜色
    const getLayerTypeColor = (serviceType) => {
      switch (serviceType) {
        case 'martin':
          return 'success'
        case 'geoserver':
          return 'primary'
        default:
          return 'info'
      }
    }
    
    // 检查当前图层是否可交互
    const isCurrentLayerInteractive = computed(() => {
      if (!currentActiveLayer.value || !mapViewerRef.value) {
        return false
      }
      
      // 调用MapViewerOL的方法获取当前图层信息
      try {
        const layerInfo = mapViewerRef.value.getCurrentLayerInfo()
        return layerInfo.canInteract
      } catch (error) {
        console.warn('获取图层交互状态失败:', error)
        return false
      }
    })
    
    // 重置所有图层
    const resetAllLayers = () => {
      if (mapViewerRef.value && mapViewerRef.value.resetAllLayersToDefault) {
        mapViewerRef.value.resetAllLayersToDefault()
        currentActiveLayer.value = null
      }
    }
    
    // 删除场景
    const deleteScene = async (sceneId) => {
      try {
        await ElMessageBox.confirm('确认删除该场景吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await gisApi.deleteScene(sceneId)
        ElMessage.success('场景删除成功')
        await fetchSceneList()
        
        // 如果删除的是当前选中的场景，清除选择
        if (selectedSceneId.value === sceneId) {
          selectedSceneId.value = null
          layersList.value = []
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除场景失败:', error)
          ElMessage.error('删除场景失败')
        }
      }
    }
    
    // 计算属性 - 当前场景
    /* const currentScene = computed(() => {
      return sceneList.value.find(scene => scene.id === selectedSceneId.value)
    }) */
    
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

    // 图层数量计算属性
    const layerCount = computed(() => {
      return layersList.value ? layersList.value.length : 0
    })
    
    // 获取图层数量文本
    const getLayerCountText = () => {
      const count = layerCount.value
      return count === 0 ? '暂无图层' : `${count} 个图层`
    }

    // 拖拽开始
    const handleDragStart = (event, layer, index) => {
      draggingLayerId.value = String(layer.id)  // 🔥 确保为字符串
      dragStartIndex.value = index
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', String(layer.id))  // 🔥 确保为字符串
      
      // 🔥 创建优化的拖拽图像
      createOptimizedDragImage(event, layer)
    }

    // 🔥 创建优化的拖拽图像
    const createOptimizedDragImage = (event, layer) => {
      // 创建一个小巧精美的拖拽图像
      const dragImage = document.createElement('div')
      
      // 限制图层名称长度
      const displayName = layer.layer_name.length > 20 ? 
        layer.layer_name.substring(0, 20) + '...' : 
        layer.layer_name
      
      dragImage.innerHTML = `
        <div style="display: flex; align-items: center; gap: 6px;">
          <i class="el-icon-rank" style="font-size: 14px;"></i>
          <span style="font-size: 12px; font-weight: 500;">${displayName}</span>
        </div>
      `
      
      // 设置简洁的样式
      dragImage.style.cssText = `
        position: absolute;
        top: -1000px;
        left: -1000px;
        background: linear-gradient(135deg, #409EFF, #36A3F7);
        color: white;
        padding: 6px 10px;
        border-radius: 16px;
        font-size: 12px;
        box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
        opacity: 0.95;
        max-width: 180px;
        white-space: nowrap;
        z-index: 9999;
        pointer-events: none;
        transform: rotate(1deg) scale(0.9);
        border: 2px solid rgba(255,255,255,0.3);
      `
      
      // 添加到body
      document.body.appendChild(dragImage)
      
      // 设置拖拽图像，调整偏移位置
      event.dataTransfer.setDragImage(dragImage, 15, 8)
      
      // 立即清理
      setTimeout(() => {
        if (dragImage.parentNode) {
          document.body.removeChild(dragImage)
        }
      }, 0)
    }

    // 拖拽结束
    const handleDragEnd = () => {
      draggingLayerId.value = null
      dragStartIndex.value = -1
      //console.log('拖拽操作结束')
    }

    // 拖拽悬停
    const handleDragOver = (event, index) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
    }

    // 拖拽放置
    const handleDrop = async (event, dropIndex) => {
      event.preventDefault()
      
      const draggedLayerId = parseInt(event.dataTransfer.getData('text/plain'))
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
        
        // 🔥 立即刷新UI和地图图层顺序
        await refreshLayersAfterReorder()
        
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
        // 🔥 保持layer_id为字符串，避免大整数精度丢失
        const layerId = String(layer.id)
        newOrders[layerId] = newOrder
      })
      
      //console.log('计算的新图层顺序:', newOrders)
      return newOrders
    }

    // 批量更新图层顺序
    const updateLayersOrder = async (newOrders) => {
      //console.log('准备发送的数据:', {
      //   sceneId: selectedSceneId.value,
      //   layerOrders: newOrders
      // })
      // 使用现有的批量更新接口
      await gisApi.reorderSceneLayers(selectedSceneId.value, newOrders)
    }

    // 🔥 拖拽重新排序后的刷新函数
    const refreshLayersAfterReorder = async () => {
      try {
        //console.log('开始刷新图层顺序...')
        
        // 1. 重新获取场景数据，更新UI中的图层卡片顺序
        //console.log('重新获取场景图层数据...')
        await fetchSceneLayers(selectedSceneId.value)
        
        // 2. 等待下一个tick确保UI已更新
        await nextTick()
        
        // 3. 通知地图组件刷新图层显示顺序
        if (mapViewerRef.value) {
          //console.log('通知地图组件刷新图层...')
          
          // 尝试调用不同的刷新方法
          if (mapViewerRef.value.refreshAllLayers) {
            await mapViewerRef.value.refreshAllLayers()
            //console.log('✅ 地图图层已刷新(refreshAllLayers)')
          }
          
          if (mapViewerRef.value.refreshLayerOrder) {
            await mapViewerRef.value.refreshLayerOrder()
            //console.log('✅ 地图图层顺序已重新排列(refreshLayerOrder)')
          }
          
          // 如果没有专门的刷新方法，尝试重新加载场景
          if (mapViewerRef.value.loadScene) {
            await mapViewerRef.value.loadScene(selectedSceneId.value)
            //console.log('✅ 地图场景已重新加载(loadScene)')
          }
        } else {
          console.warn('mapViewerRef不可用，无法刷新地图')
        }
        
        //console.log('✅ 图层顺序刷新完成')
        
      } catch (error) {
        console.error('❌ 刷新图层顺序失败:', error)
        // 如果刷新失败，至少要重新获取数据
        try {
          await fetchSceneLayers(selectedSceneId.value)
          //console.log('备用方案：重新获取图层数据成功')
        } catch (fallbackError) {
          console.error('备用方案也失败了:', fallbackError)
        }
      }
    }
    
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
    
    return {
      sceneList,
      selectedSceneId,
      layersList,
      sortedLayersList,
      loading,
      layerInfoDialogVisible,
      currentLayerInfo,
      mapViewerRef,
      layerPanelCollapsed,
      currentActiveLayer,
      fetchSceneList,
      onSceneChange,
      refreshScene,
      toggleLayerPanel,
      goToSceneManage,
      toggleLayerVisibility,
      onLayerOpacityChange,
      moveLayerUp,
      moveLayerDown,
      handleLayerAction,
      zoomToLayer,
      handleCollapsedLayerDblClick,
      showLayerInfo,
      removeLayer,
      showAddLayerDialog,
      showStyleDialog,
      onLayerAdded,
      getServiceTypeClass,
      getServiceTypeText,
      getLayerStatusClass,
      getLayerStatusText,
      selectLayer,
      onLayerSelected,
      getLayerTypeColor,
      isCurrentLayerInteractive,
      resetAllLayers,
      sceneDialogVisible,
      editingScene,
      sceneForm,
      showCreateSceneDialog,
      editScene,
      saveScene,
      deleteScene,
      getLayerCountText,
      
      // 拖拽相关
      draggingLayerId,
      handleDragStart,
      handleDragEnd,
      handleDragOver,
      handleDrop,
      
      // 🔥 手机端抽屉相关
      mobileDrawerVisible,
      mobileActiveTab,
      toggleMobileDrawer,
      closeMobileDrawer,
      selectMobileScene,
      
      // 🔥 拖拽手柄相关
      isDragging,
      handleDrawerHandleClick,
      handleDrawerDragStart
    }
  }
}
</script>

<style scoped>
.map-view {
  height: 100%; /* 🔥 使用100%适应父容器(el-main)的高度：calc(100vh - 60px) */
  width: 100%; /* 🔥 确保宽度也是100% */
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin: 0 !important; /* 🔥 强制移除外边距，消除与el-main的白边 */
  padding: 0 !important; /* 🔥 强制移除内边距 */
  border: none !important; /* 🔥 移除边框 */
  background: transparent !important; /* 🔥 透明背景 */
  box-sizing: border-box !important; /* 🔥 确保盒模型正确 */
}

.map-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  height: 100%;
  width: 100%; /* 🔥 确保宽度100% */
  overflow: hidden;
  margin: 0; /* 🔥 移除外边距 */
  padding: 0; /* 🔥 移除内边距 */
  border: none; /* 🔥 移除边框 */
  background: transparent; /* 🔥 透明背景 */
}

.layer-panel {
  width: 350px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0; /* 防止面板被压缩 */
  height: 100%;
  overflow: hidden;
  position: relative;
  box-sizing: border-box;
  margin: 0; /* 🔥 移除外边距 */
  padding: 0; /* 🔥 移除内边距 */
}

.layer-panel.collapsed {
  width: 48px !important;
  min-width: 48px !important;
  max-width: 48px !important;
  flex-basis: 48px !important;
}

.map-container-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: transparent; /* 🔥 移除白色背景，使用透明背景 */
  min-height: 0; /* 防止flex容器高度计算问题 */
  contain: layout style; /* CSS containment 优化 */
  height: 100%;
  width: 100%; /* 🔥 确保宽度也是100% */
  margin: 0; /* 🔥 移除外边距 */
  padding: 0; /* 🔥 移除内边距 */
  border: none; /* 🔥 移除边框 */
  outline: none; /* 🔥 移除轮廓 */
}

.map-container-wrapper.with-panel {
  /* 当面板展开时不需要额外的margin */
}

.panel-header {
  padding: 15px;
  background: #fff;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.collapse-btn {
  padding: 4px;
  font-size: 16px;
}

.scene-content, .layer-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.scene-actions, .layer-actions {
  padding: 15px;
  border-bottom: 1px solid #dee2e6;
}

.scene-list, .layer-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.scene-item, .layer-item {
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.scene-item:hover, .layer-item:hover {
  background-color: #f0f0f0;
}

.scene-item.active, .layer-item.active {
  background-color: #e3f2fd;
  border-left: 3px solid #409EFF;
}

.scene-info {
  margin-bottom: 10px;
}

.scene-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.scene-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.4;
}

.scene-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
}

.scene-actions {
  display: flex;
  gap: 5px;
}

.layer-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.layer-visibility {
  flex-shrink: 0;
}

.layer-info {
  flex: 1;
  min-width: 0;
}

.layer-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layer-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.service-type {
  padding: 2px 6px;
  border-radius: 3px;
  color: white;
  font-weight: bold;
}

.service-type.martin {
  background-color: #28a745;
}

.service-type.geoserver {
  background-color: #007bff;
}

.file-type {
  color: #666;
  text-transform: uppercase;
  font-weight: bold;
}

.layer-controls {
  flex-shrink: 0;
}

.no-scene {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f8f9fa;
}

.no-scene-content {
  text-align: center;
  color: #666;
}

.no-scene-content i {
  font-size: 64px;
  margin-bottom: 20px;
  color: #ccc;
}

.no-scene-content h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.no-scene-content p {
  margin: 0;
  color: #666;
}

.danger {
  color: #f56c6c;
}

.empty-layers {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
}

.empty-layers i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #c0c4cc;
}

.empty-layers p {
  margin: 15px 0;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
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

.visibility-indicator {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #dcdfe6;
  transition: all 0.2s ease;
}

.visibility-indicator.visible {
  background: #67c23a;
}

.layer-short-name {
  font-size: 10px;
  font-weight: 500;
  color: #303133;
  text-align: center;
  line-height: 1.1;
  max-width: 36px;
  word-break: break-all;
  padding: 0 2px;
}

.collapsed-layer-item.invisible .layer-short-name {
  color: #909399;
}

.active-dot {
  position: absolute;
  bottom: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #409eff;
}

.collapsed-empty {
  padding: 20px 0;
  text-align: center;
  color: #c0c4cc;
}

.collapsed-empty i {
  font-size: 20px;
  margin-bottom: 4px;
}

.collapsed-empty .empty-text {
  font-size: 9px;
  color: #c0c4cc;
  text-align: center;
}

/* 收起状态下的滚动条样式 */
.collapsed-layers::-webkit-scrollbar {
  width: 3px;
}

.collapsed-layers::-webkit-scrollbar-track {
  background: transparent;
}

.collapsed-layers::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.collapsed-layers::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}



/* 图层卡片样式 - 紧凑型 */
.layer-cards {
  padding: 0;
  overflow-y: auto;
  max-height: 100%;
  /* CSS变量定义 - 紧凑模式 */
  --layer-card-spacing: 4px;
  --layer-card-padding: 6px 10px;
  --layer-card-border-radius: 6px;
  --layer-info-spacing: 2px;
  --tag-padding: 0px 4px;
}

.layer-card {
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

.layer-card.dragging {
  opacity: 0.7;
  transform: scale(0.98) rotate(1deg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  transition: all 0.2s ease;
}

.layer-card[draggable="true"] {
  cursor: grab;
}

.layer-card[draggable="true"]:active {
  cursor: grabbing;
}

.layer-card-header {
  padding: var(--layer-card-padding);
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 32px;
}

.layer-title {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.layer-name {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
  line-height: 1.3;
}

.active-indicator {
  color: #409eff;
  font-size: 14px;
  margin-right: 3px;
}

.layer-drag-handle {
  color: #c0c4cc;
  cursor: grab;
  margin-right: 6px;
  font-size: 14px;
}

.layer-drag-handle:hover {
  color: #909399;
}

.layer-actions {
  display: flex;
  gap: 2px;
  opacity: 1; /* 🔥 修复：默认显示，不需要hover才显示 */
  transition: opacity 0.2s;
}

/* 🔥 保留hover效果用于强调，但不影响基础显示 */
.layer-card:hover .layer-actions {
  opacity: 1;
}

.layer-actions .el-button {
  padding: 3px;
  width: 20px;
  height: 20px;
  border: 1px solid #e4e7ed; /* 🔥 添加边框让按钮更明显 */
  background: rgba(255, 255, 255, 0.8); /* 🔥 添加半透明背景 */
  color: #606266;
  transition: all 0.2s;
  border-radius: 4px; /* 🔥 添加圆角 */
  opacity: 1 !important; /* 🔥 确保始终可见 */
  visibility: visible !important; /* 🔥 确保始终可见 */
}

.layer-actions .zoom-btn:hover {
  color: #409eff;
  background: #ecf5ff;
}

.layer-actions .style-btn:hover {
  color: #67c23a;
  background: #f0f9ff;
}

.layer-actions .remove-btn:hover {
  color: #f56c6c;
  background: #fef0f0;
}

.layer-card-info {
  padding: var(--layer-info-spacing) 12px 8px;
  display: flex;
  gap: var(--layer-info-spacing);
  flex-wrap: wrap;
}

.tag {
  display: inline-block;
  padding: var(--tag-padding);
  font-size: 9px;
  border-radius: 8px;
  background: #f4f4f5;
  color: #909399;
  border: 1px solid transparent;
  line-height: 1.3;
}

/* 服务类型样式 */
.tag.service-martin {
  background: #f0f9ff;
  color: #67c23a;
  border-color: #b3e19d;
}

.tag.service-geoserver {
  background: #ecf5ff;
  color: #409eff;
  border-color: #b3d8ff;
}

/* 状态样式 */
.tag.status-published {
  background: #f0f9ff;
  color: #67c23a;
  border-color: #b3e19d;
}

.tag.status-unpublished {
  background: #fef0f0;
  color: #f56c6c;
  border-color: #fbc4c4;
}

.scene-selector {
  padding: 0 15px 12px;
}

.layer-count {
  font-size: 12px;
  color: #909399;
  margin-right: 10px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  max-height: calc(100% - 120px); /* 减去面板头部和场景选择器的高度 */
}

.panel-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 🔥 透明度控制样式 - 紧凑型 */
.layer-opacity-control {
  padding: 4px 12px 6px;
  background: #fafbfc;
  border-top: 1px solid #f0f0f0;
  margin: 0;
  border-radius: 0 0 6px 6px;
}

.opacity-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #606266;
  min-height: 20px;
}

.opacity-icon {
  font-size: 11px;
  color: #909399;
  flex-shrink: 0;
}

.opacity-text {
  font-size: 9px;
  color: #606266;
  white-space: nowrap;
  flex-shrink: 0;
}

.opacity-value {
  font-weight: 500;
  color: #409eff;
  font-size: 9px;
  min-width: 28px;
  text-align: right;
  flex-shrink: 0;
}

.opacity-slider {
  flex: 1;
  margin: 0 6px;
}

.opacity-slider .el-slider__runway {
  height: 3px;
  background-color: #e4e7ed;
  margin: 8px 0;
}

.opacity-slider .el-slider__bar {
  height: 3px;
  background-color: #409eff;
}

.opacity-slider .el-slider__button {
  width: 10px;
  height: 10px;
  border: 2px solid #409eff;
  background-color: #fff;
}

.opacity-slider .el-slider__button:hover {
  transform: scale(1.1);
}

/* 当图层卡片被拖拽时隐藏透明度控制 */
.layer-card.dragging .layer-opacity-control {
  opacity: 0.3;
  pointer-events: none;
}

/* 隐藏状态的图层，透明度控制也相应调整 */
.layer-card.invisible .layer-opacity-control {
  opacity: 0.6;
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

/* 🔥 桌面端面板收缩功能样式加强 */
@media (min-width: 769px) {
  .layer-panel {
    width: 350px !important;
    transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    background: #f8f9fa !important; /* 调试用背景色 */
  }
  
  .layer-panel.collapsed {
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
    background: #e8f4f8 !important; /* 收起状态调试用背景色 */
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

/* 🔥 手机端底部浮动按钮和抽屉样式 */
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
  .mobile-layer-fab,
  .mobile-drawer-overlay {
    display: block;
  }
  
  /* 🔥 确保Element Plus对话框在手机端能正确显示在抽屉前面 */
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
  
  /* 确保手机端不受桌面端面板样式影响 */
  .layer-panel {
    display: none !important;
  }
  
  /* 底部浮动按钮 */
  .mobile-layer-fab {
    position: fixed;
    bottom: 10px;
    left: 10px;
    z-index: 999; /* 🔥 保持较低的z-index，确保对话框能显示在前面 */
    background: linear-gradient(135deg, #409eff, #337ecc);
    border-radius: 50px;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
    cursor: pointer;
    transition: all 0.3s ease;
    user-select: none;
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
  
  /* 🔥 抽屉遮罩层 */
  .mobile-drawer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0);
    z-index: 1500; /* 🔥 降低z-index，确保Element Plus对话框能显示在前面 */
    transition: all 0.3s ease;
    pointer-events: none;
  }
  
  .mobile-drawer-overlay.show {
    background: rgba(0, 0, 0, 0.5);
    pointer-events: all;
    backdrop-filter: blur(4px);
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
  
  /* 🔥 标签页切换 */
  .mobile-tabs {
    display: flex;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
    flex-shrink: 0;
  }
  
  .mobile-tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 15px 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    color: #606266;
    font-size: 14px;
    position: relative;
    font-weight: 500;
  }
  
  .mobile-tab.active {
    color: #409eff;
    background: white;
    font-weight: 600;
  }
  
  .mobile-tab.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: #409eff;
    border-radius: 3px 3px 0 0;
  }
  
  .mobile-tab i {
    font-size: 16px;
  }
  
  .tab-badge {
    position: absolute;
    top: 8px;
    right: 12px;
    background: #409eff;
    color: white;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: bold;
  }
  
  /* 标签页内容 */
  .mobile-tab-content {
    flex: 1;
    overflow-y: auto;
    background: white;
  }
  
  /* 🔥 手机端场景列表 */
  .mobile-scene-list {
    padding: 0;
  }
  
  .mobile-scene-item {
    padding: 18px 20px;
    border-bottom: 1px solid #f5f5f5;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
  }
  
  .mobile-scene-item:hover {
    background: #f8f9fa;
  }
  
  .mobile-scene-item.active {
    background: linear-gradient(135deg, #ecf5ff, #f0f9ff);
    border-left: 4px solid #409eff;
    border-bottom-color: #e1f0fe;
  }
  
  .mobile-scene-item .scene-info h4 {
    margin: 0 0 6px 0;
    font-size: 16px;
    color: #303133;
    font-weight: 600;
  }
  
  .mobile-scene-item .scene-info p {
    margin: 0;
    font-size: 13px;
    color: #909399;
    line-height: 1.4;
  }
  
  .mobile-scene-item.active .scene-info h4 {
    color: #409eff;
  }
  
  .mobile-scene-item .scene-meta {
    flex-shrink: 0;
  }
  
  /* 🔥 手机端图层列表 */
  .mobile-layer-list {
    padding: 0;
  }
  
  .mobile-layer-item {
    padding: 16px 18px; /* 🔥 优化内边距 */
    border-bottom: 1px solid #f5f5f5;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: stretch; /* 🔥 让内容区域和按钮区域同样高度 */
    gap: 12px; /* 🔥 内容和按钮间距 */
    background: white;
    min-height: 120px; /* 🔥 确保有足够高度 */
    position: relative; /* 🔥 为后续微调提供定位上下文 */
  }
  
  .mobile-layer-item:hover {
    background: #f8f9fa;
  }
  
  .mobile-layer-item.active {
    background: linear-gradient(135deg, #ecf5ff, #f0f9ff);
    border-left: 4px solid #409eff;
    border-bottom-color: #e1f0fe;
  }
  
  .mobile-layer-item.invisible {
    opacity: 0.6;
  }
  
  .layer-main-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center; /* 🔥 让内容在垂直方向上居中 */
    padding: 2px 0; /* 🔥 微调垂直间距 */
  }
  
  .layer-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
  }
  
  .layer-header .layer-name {
    flex: 1;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .mobile-layer-item.active .layer-header .layer-name {
    color: #409eff;
  }
  
  .layer-header .active-indicator {
    color: #409eff;
    font-size: 16px;
  }
  
  .layer-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }
  
  .layer-tags .tag {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 12px;
    background: #f4f4f5;
    color: #909399;
    font-weight: 500;
  }
  
  .layer-tags .tag.service-martin {
    background: #f0f9ff;
    color: #67c23a;
    border: 1px solid #c9e9d0;
  }
  
  .layer-tags .tag.service-geoserver {
    background: #ecf5ff;
    color: #409eff;
    border: 1px solid #b3d8ff;
  }
  
  /* 手机端透明度控制 */
  .mobile-opacity-control {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
    padding: 8px 12px;
    background: #fafbfc;
    border-radius: 8px;
    border: 1px solid #f0f0f0;
  }
  
  .opacity-label {
    font-size: 12px;
    color: #606266;
    white-space: nowrap;
    font-weight: 500;
  }
  
  .mobile-opacity-slider {
    flex: 1;
    margin: 0 8px;
  }
  
  .mobile-opacity-slider .el-slider__runway {
    height: 6px;
    background-color: #e4e7ed;
    border-radius: 3px;
  }
  
  .mobile-opacity-slider .el-slider__bar {
    height: 6px;
    background: linear-gradient(90deg, #409eff, #36a3f7);
    border-radius: 3px;
  }
  
  .mobile-opacity-slider .el-slider__button {
    width: 18px;
    height: 18px;
    border: 3px solid #409eff;
    background-color: #fff;
    box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
  }
  
  .mobile-opacity-control .opacity-value {
    font-size: 12px;
    color: #409eff;
    font-weight: 600;
    min-width: 35px;
    text-align: right;
  }
  
  .layer-actions {
    display: flex !important; /* 🔥 强制显示 */
    flex-direction: column;
    justify-content: center; /* 🔥 垂直居中 */
    align-items: stretch; /* 🔥 让所有按钮宽度一致 */
    gap: 6px; /* 🔥 统一间距 */
    flex-shrink: 0;
    opacity: 1 !important; /* 🔥 确保可见 */
    visibility: visible !important; /* 🔥 确保可见 */
    min-height: 120px; /* 🔥 确保有足够高度进行居中 */
    width: 32px; /* 🔥 固定容器宽度确保对齐 */
    padding: 4px 1px; /* 🔥 微调内边距，增加顶部底部间距 */
    background: rgba(248, 249, 250, 0.3); /* 🔥 微妙背景色突出按钮区域 */
    border-radius: 8px; /* 🔥 圆角让视觉更柔和 */
    border: 1px solid rgba(228, 231, 237, 0.4); /* 🔥 微妙边框定义边界 */
  }
  
  .layer-actions .el-button {
    padding: 0; /* 🔥 清除内边距 */
    width: 30px; /* 🔥 固定宽度 */
    height: 30px; /* 🔥 固定高度 */
    border-radius: 6px; /* 🔥 调整圆角 */
    font-size: 12px; /* 🔥 减小字体 */
    border: 1px solid #e4e7ed;
    background: white;
    transition: all 0.2s ease;
    opacity: 1 !important; /* 🔥 确保按钮可见 */
    visibility: visible !important; /* 🔥 确保按钮可见 */
    display: flex !important; /* 🔥 确保flex布局 */
    align-items: center !important; /* 🔥 图标垂直居中 */
    justify-content: center !important; /* 🔥 图标水平居中 */
    min-width: 30px !important; /* 🔥 强制最小宽度 */
    max-width: 30px !important; /* 🔥 强制最大宽度 */
    min-height: 30px !important; /* 🔥 强制最小高度 */
    max-height: 30px !important; /* 🔥 强制最大高度 */
    flex: none; /* 🔥 防止flex自动调整 */
    margin: 0; /* 🔥 清除外边距 */
    box-sizing: border-box; /* 🔥 确保盒模型一致 */
  }
  
  /* 🔥 手机端按钮特定样式 */
  .layer-actions .action-btn.zoom-btn {
    border-color: #409eff;
    color: #409eff;
  }
  
  .layer-actions .action-btn.style-btn {
    border-color: #67c23a;
    color: #67c23a;
  }
  
  .layer-actions .action-btn.delete-btn {
    border-color: #f56c6c;
    color: #f56c6c;
  }
  
  /* 🔥 SVG图标样式 */
  .layer-actions .el-button svg {
    display: block !important;
    margin: 0 !important;
    flex-shrink: 0;
    width: 16px !important; /* 🔥 固定图标宽度 */
    height: 16px !important; /* 🔥 固定图标高度 */
    position: relative;
    left: 0;
    top: 0;
  }
  
  .layer-actions .el-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  /* 🔥 手机端按钮悬停效果增强 */
  .layer-actions .action-btn.zoom-btn:hover {
    background: #ecf5ff !important;
    border-color: #337ecc !important;
  }
  
  .layer-actions .action-btn.style-btn:hover {
    background: #f0f9ff !important;
    border-color: #5ca632 !important;
  }
  
  .layer-actions .action-btn.delete-btn:hover {
    background: #fef0f0 !important;
    border-color: #dd4a68 !important;
  }
  
  /* 🔥 手机端按钮点击反馈 */
  .layer-actions .el-button:active {
    transform: scale(0.95);
    transition: transform 0.1s ease;
  }
  
  /* 手机端空状态 */
  .mobile-empty {
    padding: 60px 20px;
    text-align: center;
    color: #909399;
  }
  
  .mobile-empty i {
    font-size: 48px;
    margin-bottom: 16px;
    color: #c0c4cc;
  }
  
  .mobile-empty p {
    margin: 0 0 20px 0;
    font-size: 14px;
    color: #909399;
  }
  
  .mobile-empty .el-button {
    border-radius: 20px;
    padding: 10px 20px;
  }
}

/* 🔥 更小屏幕（手机）优化 */
@media (max-width: 480px) {
  .mobile-drawer {
    max-height: 80vh;
  }
  
  .fab-content {
    padding: 12px 18px;
  }
  
  .fab-text {
    font-size: 13px;
  }
  
  .mobile-layer-item,
  .mobile-scene-item {
    padding: 15px 18px;
  }
  
  .mobile-layer-item {
    gap: 10px; /* 🔥 更小屏幕上进一步减小间距 */
    min-height: 100px; /* 🔥 更小屏幕上减小最小高度 */
    padding: 12px 14px; /* 🔥 进一步优化内边距 */
    align-items: center !important; /* 🔥 确保在小屏幕上也居中对齐 */
  }
  
  /* 🔥 更小屏幕上的操作按钮容器 */
  .layer-actions {
    min-height: 90px !important; /* 🔥 减小操作按钮容器高度 */
    gap: 4px !important; /* 🔥 统一按钮间距 */
    width: 30px !important; /* 🔥 调整容器宽度 */
    padding: 3px 1px !important; /* 🔥 调整内边距 */
  }
  
  .layer-actions .el-button {
    width: 28px !important; /* 🔥 更小屏幕上进一步减小 */
    height: 28px !important; /* 🔥 更小屏幕上进一步减小 */
    padding: 0 !important; /* 🔥 清除内边距 */
    min-width: 28px !important;
    max-width: 28px !important;
    min-height: 28px !important;
    max-height: 28px !important;
    flex: none !important; /* 🔥 防止flex自动调整 */
  }
  
  /* 🔥 更小屏幕上的图标尺寸 */
  .layer-actions .el-button svg {
    width: 14px !important;
    height: 14px !important;
  }
  
  .layer-header .layer-name {
    font-size: 15px;
  }
  
  .mobile-scene-item .scene-info h4 {
    font-size: 15px;
  }
}

/* 🔥 触摸设备优化 */
@media (hover: none) and (pointer: coarse) {
  /* 移除hover效果，优化触摸体验 */
  .mobile-layer-item:hover,
  .mobile-scene-item:hover {
    background: white;
  }
  
  .mobile-layer-item.active:hover,
  .mobile-scene-item.active:hover {
    background: linear-gradient(135deg, #ecf5ff, #f0f9ff);
  }
  
  .layer-actions .el-button:hover {
    transform: none;
    box-shadow: none;
  }
  
  .mobile-layer-fab:hover {
    transform: none;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  }
  
  /* 🔥 触摸设备上的拖拽手柄优化 */
  .drawer-handle:hover {
    background: #e4e7ed; /* 🔥 保持基础颜色 */
    opacity: 0.6; /* 🔥 保持基础透明度 */
    cursor: grab;
  }
  
    .drawer-handle:hover::before {
    cursor: grab; /* 🔥 伪元素光标 */
  }
  
  /* 🔥 确保触摸设备上操作按钮始终可见和对齐 */
  .layer-actions {
    opacity: 1 !important;
    display: flex !important;
    align-items: stretch !important;
    justify-content: center !important;
  }
  
  .layer-actions .el-button {
    opacity: 1 !important;
    visibility: visible !important;
    flex: none !important; /* 🔥 防止触摸设备上尺寸变化 */
  }
}
</style> 