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
                    
                    <!-- 删除图层 -->
                    <el-button 
                      link 
                      @click.stop="removeLayer(layer)" 
                      class="remove-btn"
                      title="删除图层"
                    >
                      <i class="el-icon-delete"></i>
                    </el-button>
                  </div>
                </div>
                
                <!-- 图层详细信息 -->
                <div class="layer-card-body">
                  <div class="layer-meta">
                    <span class="layer-type">{{ getLayerTypeText(layer) }}</span>
                    <span class="layer-service">{{ layer.service_type || layer.file_type }}</span>
                  </div>
                  
                  <!-- 透明度控制 -->
                  <div class="layer-opacity">
                    <label class="opacity-label">透明度: {{ Math.round((layer.opacity || 1) * 100) }}%</label>
                    <el-slider
                      :model-value="layer.opacity || 1"
                      @update:model-value="val => { layer.opacity = val; updateLayerOpacity(layer); }"
                      :min="0"
                      :max="1"
                      :step="0.1"
                      size="small"
                      class="opacity-slider"
                    />
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
        
        <!-- 收起状态的展开按钮 -->
        <div v-show="layerPanelCollapsed" class="collapsed-toggle">
          <el-button 
            link 
            size="small" 
            @click="toggleLayerPanel"
            class="expand-btn"
            title="展开图层面板"
          >
            <span class="toggle-icon">》</span>
          </el-button>
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
        
        <!-- 移动端图层管理按钮 -->
        <div class="mobile-layer-toggle mobile-only">
          <el-button 
            type="primary" 
            circle 
            size="large"
            @click="showMobileLayerPanel"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M3,2H21V2H21V4H20V3H4V20H3V2M5,6V18H19V8H21V18A2,2 0 0,1 19,20H5A2,2 0 0,1 3,18V6A2,2 0 0,1 5,4H19A2,2 0 0,1 21,6H5M6,9H18V11H6V9M6,12H16V14H6V12M6,15H14V17H6V15Z"/>
            </svg>
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 移动端图层面板抽屉 -->
    <el-drawer
      v-model="mobileLayerPanelVisible"
      direction="ltr"
      :size="280"
      :show-close="false"
      class="mobile-layer-drawer"
    >
      <template #header>
        <div class="drawer-header">
          <h4>图层管理</h4>
          <el-button size="small" @click="showAddLayerDialog">
            <i class="el-icon-plus"></i> 添加
          </el-button>
        </div>
      </template>
      
      <!-- 场景选择 -->
      <div class="scene-selector mobile">
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
      
      <!-- 图层列表 - 移动端版本 -->
      <div class="mobile-layer-list">
        <div 
          v-for="layer in sortedLayersList" 
          :key="layer.id" 
          class="mobile-layer-item"
        >
          <div class="layer-header">
            <div class="layer-info">
              <div class="layer-name">{{ layer.name || '未命名图层' }}</div>
              <div class="layer-type">{{ getLayerTypeText(layer) }}</div>
            </div>
            <el-switch
              v-model="layer.visible"
              size="small"
              @change="toggleLayerVisibility(layer)"
            />
          </div>
          
          <div v-if="layer.visible" class="layer-controls">
            <div class="opacity-control">
              <span>透明度:</span>
              <el-slider
                v-model="layer.opacity"
                :min="0"
                :max="100"
                :step="10"
                size="small"
                @change="updateLayerOpacity(layer)"
              />
            </div>
            <div class="layer-actions">
              <el-button size="small" @click="zoomToLayer(layer)">定位</el-button>
              <el-button size="small" type="danger" @click="removeLayer(layer)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
    
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
            @click="selectLayer(layer)"
            :class="{ 'selected': selectedLayers.includes(layer.id) }"
          >
            <div class="layer-preview">
              <div class="preview-placeholder">
                {{ getLayerIcon(layer) }}
              </div>
            </div>
            <div class="layer-details">
              <div class="layer-name">{{ layer.name }}</div>
              <div class="layer-description">{{ layer.description || getLayerTypeText(layer) }}</div>
              <div class="layer-meta">
                <span class="meta-item">{{ layer.file_type?.toUpperCase() }}</span>
                <span class="meta-item">{{ layer.service_type }}</span>
              </div>
            </div>
            <div class="layer-actions">
              <el-checkbox 
                :model-value="selectedLayers.includes(layer.id)"
                @change="toggleLayerSelection(layer)"
              />
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
    const mobileLayerPanelVisible = ref(false)
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
    const showMobileLayerPanel = () => {
      mobileLayerPanelVisible.value = true
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
    const updateLayerOpacity = (layer) => {
      console.log(`更新图层 ${layer.layer_name} 透明度: ${Math.round(layer.opacity * 100)}%`)
      
      // 确保透明度在有效范围内
      layer.opacity = Math.max(0, Math.min(1, parseFloat(layer.opacity) || 1.0))
      
      // 通知地图组件更新
      if (mapViewer.value) {
        // 触发图层列表的响应式更新
        layersList.value = [...layersList.value]
      }
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
        // 这里调用实际的API
        const response = await fetch('/api/layers/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            ...layerSearchForm,
            page: currentPage.value,
            pageSize: pageSize.value
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          availableLayers.value = data.layers || []
          totalLayers.value = data.total || 0
        } else {
          ElMessage.error('加载图层列表失败')
        }
      } catch (error) {
        console.error('加载图层失败:', error)
        // 使用模拟数据
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
    
    // 添加选中图层
    const addSelectedLayers = () => {
      const layersToAdd = availableLayers.value.filter(layer => 
        selectedLayers.value.includes(layer.id)
      )
      
      layersToAdd.forEach(layer => {
        // 检查图层是否已存在
        if (!layersList.value.find(l => l.id === layer.id)) {
          layersList.value.push({
            ...layer,
            visible: true,
            opacity: 100,
            zIndex: layersList.value.length
          })
        }
      })
      
      selectedLayers.value = []
      addLayerDialogVisible.value = false
      ElMessage.success(`已添加 ${layersToAdd.length} 个图层`)
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
      mobileLayerPanelVisible,
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
      showMobileLayerPanel,
      toggleLayerVisibility,
      updateLayerOpacity,
      zoomToLayer,
      removeLayer,
      getLayerTypeText,
      getLayerIcon,
      showAddLayerDialog,
      searchLayers,
      resetSearch,
      
      toggleLayerSelection,
      addSelectedLayers,
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
  width: 320px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  transition: all 0.3s ease;
  z-index: 1000;
  position: relative;
}

.layer-panel.collapsed {
  width: 0;
  border-right: none;
}

.panel-content {
  width: 320px;
  height: 100%;
  display: flex;
  flex-direction: column;
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
  color: #909399;
}

.panel-toggle-btn {
  padding: 4px 8px;
  min-height: auto;
}

.toggle-icon {
  font-size: 12px;
  font-weight: bold;
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
  gap: 8px;
}

.layer-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  transition: all 0.2s ease;
  cursor: pointer;
  margin-bottom: 8px;
}

.layer-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.layer-card.active {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  background: linear-gradient(135deg, #ecf5ff, #f0f9ff);
}

.layer-card.invisible {
  opacity: 0.6;
}

.layer-card-header {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
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

/* 收起状态 */
.collapsed-toggle {
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  z-index: 1001;
}

.expand-btn {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  padding: 8px 4px;
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

/* 移动端图层按钮 */
.mobile-layer-toggle {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
}

/* 移动端图层抽屉 */
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-header h4 {
  margin: 0;
  font-size: 16px;
}

.scene-selector.mobile {
  margin: 16px 0;
}

.mobile-layer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-layer-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
}

.layer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.layer-name {
  font-weight: 500;
  font-size: 14px;
}

.layer-type {
  font-size: 12px;
  color: #909399;
}

.layer-controls {
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
}

.opacity-control {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.opacity-control span {
  font-size: 12px;
  min-width: 50px;
}

.layer-actions {
  display: flex;
  gap: 8px;
}

/* 添加图层对话框 */
.layer-search-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.available-layers {
  max-height: 400px;
  overflow-y: auto;
}

.available-layer-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.available-layer-item:hover {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.available-layer-item.selected {
  border-color: #409eff;
  background-color: #e1f3ff;
}

.layer-preview {
  width: 40px;
  height: 40px;
  margin-right: 12px;
  flex-shrink: 0;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.layer-details {
  flex: 1;
  min-width: 0;
}

.layer-details .layer-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.layer-description {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.layer-meta {
  display: flex;
  gap: 8px;
}

.meta-item {
  background: #f0f2f5;
  color: #606266;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }
  
  .mobile-only {
    display: block !important;
  }
}

@media (min-width: 769px) {
  .desktop-only {
    display: block !important;
  }
  
  .mobile-only {
    display: none !important;
  }
}
</style> 