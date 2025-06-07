<template>
  <div class="map-view">
    <!-- 主要内容区域 -->
    <div class="map-content">
      <!-- 左侧图层面板 -->
      <div class="layer-panel" :class="{ 'collapsed': layerPanelCollapsed }">
        <div class="panel-content" v-show="!layerPanelCollapsed">
          <div class="panel-header">
            <h3>图层管理</h3>
            <div class="header-right">
              <span class="layer-count">{{ layersList.length }} 个图层</span>
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
            <div class="layer-cards" v-if="layersList.length > 0">
              <div 
                v-for="layer in layersList" 
                :key="layer.id" 
                class="layer-card"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.id === layer.id,
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
                    <i v-if="currentActiveLayer && currentActiveLayer.id === layer.id" 
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
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M15.5 14h-.79l-.28-.27A6.5 6.5 0 1 0 13 15.5l.27.28v.79l5 4.99L19.49 20l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/>
                        <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
                      </svg>
                    </el-button>
                    
                    <!-- 样式设置 -->
                    <el-button 
                      link 
                      @click.stop="showStyleDialog(layer)"
                      class="style-btn"
                      title="样式设置"
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
                      </svg>
                    </el-button>
                    
                    <!-- 删除图层 -->
                    <el-button 
                      link 
                      @click.stop="removeLayer(layer)" 
                      class="remove-btn"
                      title="删除图层"
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                        <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
                      </svg>
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
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
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
      description: ''
    })
    
    // 响应式数据
    const sceneList = ref([])
    const selectedSceneId = ref(null)
    const layersList = ref([])
    const loading = ref(false)
    const layerInfoDialogVisible = ref(false)
    const currentLayerInfo = ref(null)
    const currentActiveLayer = ref(null)
    
    // 获取场景列表
    const fetchSceneList = async () => {
      try {
        const response = await gisApi.getScenes()
        sceneList.value = response.scenes
        
        // 如果URL中有scene_id参数，设置为当前选中的场景
        const sceneIdFromQuery = route.query.scene_id
        if (sceneIdFromQuery) {
          selectedSceneId.value = parseInt(sceneIdFromQuery)
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
    /* const selectScene = async (sceneId) => {
      if (selectedSceneId.value === sceneId) return
      
      selectedSceneId.value = sceneId
      
      try {
        const response = await gisApi.getScene(sceneId)
        layersList.value = response.layers || []
      } catch (error) {
        console.error('加载场景详情失败:', error)
        ElMessage.error('加载场景详情失败')
      }
    } */
    
    // 显示创建场景对话框
    const showCreateSceneDialog = () => {
      editingScene.value = null
      sceneForm.name = ''
      sceneForm.description = ''
      sceneDialogVisible.value = true
    }
    
    // 编辑场景
    const editScene = (scene) => {
      editingScene.value = scene
      sceneForm.name = scene.name
      sceneForm.description = scene.description || ''
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
          //const response = await gisApi.createScene(sceneForm)
          ElMessage.success('场景创建成功')
          //currentSceneId.value = response.scene.id
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
        layersList.value = response.layers
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
          const response = await gisApi.getLayerBounds(layer.id)
          if (response?.success && response.data?.bbox) {
            bbox = response.data.bbox
            // coordinate_system字段仅用于显示原始坐标系，bbox已经是EPSG:4326坐标
            originalCRS = response.data.coordinate_system || 'EPSG:4326'
            console.log('从图层边界API获取到边界:', bbox, '(已转换为EPSG:4326), 原始坐标系:', originalCRS)
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
        
        // 4. 验证边界框数据并转换格式
        let minx, miny, maxx, maxy
        
        if (bbox.minx !== undefined) {
          // 对象格式 {minx, miny, maxx, maxy}
          minx = parseFloat(bbox.minx)
          miny = parseFloat(bbox.miny)
          maxx = parseFloat(bbox.maxx)
          maxy = parseFloat(bbox.maxy)
        } else if (Array.isArray(bbox) && bbox.length === 4) {
          // 数组格式 [minx, miny, maxx, maxy]
          minx = parseFloat(bbox[0])
          miny = parseFloat(bbox[1])
          maxx = parseFloat(bbox[2])
          maxy = parseFloat(bbox[3])
        } else {
          ElMessage.warning('边界框数据格式不正确')
          return
        }
        
        if (isNaN(minx) || isNaN(miny) || isNaN(maxx) || isNaN(maxy)) {
          ElMessage.warning('边界框数据格式错误')
          return
        }
        
        // 5. 构建范围并进行坐标转换
        const originalExtent = [minx, miny, maxx, maxy]
        console.log(`边界框坐标 (后端已转换为EPSG:4326):`, originalExtent, `原始坐标系: ${originalCRS}`)
        
        let transformedExtent
        try {
          // 由于后端返回的bbox已经是EPSG:4326坐标，直接从EPSG:4326转换到EPSG:3857
          if (mapViewerRef.value.transformCoordinates) {
            transformedExtent = mapViewerRef.value.transformCoordinates(originalExtent, 'EPSG:4326', 'EPSG:3857')
          } else {
            // 备用方案：直接使用OpenLayers的transformExtent
            transformedExtent = ol.proj.transformExtent(originalExtent, 'EPSG:4326', 'EPSG:3857')
          }
          console.log(`转换后边界 (EPSG:3857):`, transformedExtent)
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
        
        ElMessage.success(`已缩放到图层"${layer.layer_name}"范围 (${originalCRS})`)
        
      } catch (error) {
        console.error('缩放到图层失败:', error)
        ElMessage.error(`缩放到图层失败: ${error.message}`)
      }
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
    const showAddLayerDialog = () => {
      
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
      console.log('选择图层:', layer.layer_name)
      currentActiveLayer.value = layer
      
      // 通知MapViewerOL组件将该图层置顶
      if (mapViewerRef.value) {
        mapViewerRef.value.bringLayerToTop(layer)
      }
      
      ElMessage.success(`已选中图层: ${layer.layer_name}，该图层已置顶并启用属性弹窗`)
    }
    
    // 处理图层选择事件
    const onLayerSelected = (layer) => {
      console.log('收到图层选择事件:', layer)
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
    
    // 图层数量计算属性
    const layerCount = computed(() => {
      return layersList.value ? layersList.value.length : 0
    })
    
    // 获取图层数量文本
    const getLayerCountText = () => {
      const count = layerCount.value
      return count === 0 ? '暂无图层' : `${count} 个图层`
    }
    
    return {
      sceneList,
      selectedSceneId,
      layersList,
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
      moveLayerUp,
      moveLayerDown,
      handleLayerAction,
      zoomToLayer,
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
      getLayerCountText
    }
  }
}
</script>

<style scoped>
.map-view {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.map-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  height: 100%;
  overflow: hidden;
}

.layer-panel {
  width: 350px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0; /* 防止面板被压缩 */
}

.layer-panel.collapsed {
  width: 50px;
}

.map-container-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background-color: #f0f0f0; /* 临时背景色便于调试 */
  min-height: 0; /* 防止flex容器高度计算问题 */
  contain: layout style; /* CSS containment 优化 */
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
  height: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
  transition: all 0.3s ease;
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

/* 图层卡片样式 */
.layer-cards {
  padding: 0;
}

.layer-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.layer-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-color: #c6e2ff;
}

.layer-card.active {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.layer-card.invisible {
  opacity: 0.6;
}

.layer-card-header {
  padding: 12px 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.layer-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.layer-name {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.active-indicator {
  color: #409eff;
  font-size: 16px;
  margin-right: 4px;
}

.layer-drag-handle {
  color: #c0c4cc;
  cursor: grab;
  margin-right: 8px;
}

.layer-drag-handle:hover {
  color: #909399;
}

.layer-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.layer-card:hover .layer-actions {
  opacity: 1;
}

.layer-actions .el-button {
  padding: 4px;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #606266;
  transition: all 0.2s;
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
  padding: 0 15px 12px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  border-radius: 12px;
  background: #f4f4f5;
  color: #909399;
  border: 1px solid transparent;
  line-height: 1.2;
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
  padding: 0 15px 15px;
}

.layer-count {
  font-size: 12px;
  color: #909399;
  margin-right: 10px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.panel-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style> 