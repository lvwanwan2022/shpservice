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
                  'dragging': draggingLayerId === layer.id,
                  'settings-open': expandedSettings.has(layer.id)
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
                    <span class="layer-name" :title="layer.layer_name">{{ layer.layer_name }}</span>
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

                    <!-- 设置按钮 -->
                    <el-button 
                      link 
                      @click.stop="toggleLayerSettings(layer)"
                      class="settings-btn"
                      :class="{ 'active': expandedSettings.has(layer.id) }"
                      title="图层设置"
                    >
                      <i class="el-icon-setting"></i>
                    </el-button>
                  </div>
                </div>

                <!-- 设置展开面板 -->
                <div class="layer-settings-panel" v-if="expandedSettings.has(layer.id)" @click.stop>
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
                  
                  <!-- 透明度控制 -->
                  <div 
                    class="layer-opacity-control" 
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
                        class="opacity-slider"
                      />
                      <span class="opacity-value">{{ Math.round((layer.opacity || 1) * 100) }}%</span>
                    </div>
                  </div>

                  <!-- 图层顺序控制 -->
                  <div class="layer-order-control">
                    <span class="control-label">图层顺序</span>
                    <div class="order-buttons">
                      <el-button 
                        size="small" 
                        icon="el-icon-top" 
                        @click="moveLayerUp(layersList.findIndex(l => l.id === layer.id))"
                        :disabled="index === 0"
                      >上移</el-button>
                      <el-button 
                        size="small" 
                        icon="el-icon-bottom" 
                        @click="moveLayerDown(layersList.findIndex(l => l.id === layer.id))"
                        :disabled="index === sortedLayersList.length - 1"
                      >下移</el-button>
                    </div>
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
    
    // 🔥 图层设置面板展开状态
    const expandedSettings = reactive(new Set())
    
    // 切换图层设置面板
    const toggleLayerSettings = (layer) => {
      if (expandedSettings.has(layer.id)) {
        expandedSettings.delete(layer.id)
      } else {
        expandedSettings.add(layer.id)
      }
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
    
    // 上移图层 (index in sortedLayersList)
    const moveLayerUp = async (index) => {
      if (index === 0) return
      
      try {
        const newOrders = calculateNewLayersOrder(index, index - 1)
        await updateLayersOrder(newOrders)
        ElMessage.success('图层上移成功')
        await refreshLayersAfterReorder()
      } catch (error) {
        console.error('图层上移失败', error)
        ElMessage.error('图层上移失败')
      }
    }
    
    // 下移图层 (index in sortedLayersList)
    const moveLayerDown = async (index) => {
      if (index === sortedLayersList.value.length - 1) return
      
      try {
        const newOrders = calculateNewLayersOrder(index, index + 1)
        await updateLayersOrder(newOrders)
        ElMessage.success('图层下移成功')
        await refreshLayersAfterReorder()
      } catch (error) {
        console.error('图层下移失败', error)
        ElMessage.error('图层下移失败')
      }
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
      handleDrawerDragStart,
      
      // 🔥 图层设置相关
      expandedSettings,
      toggleLayerSettings
    }
  }
}
</script>

<style scoped src="./MapViewOL.css"></style>
