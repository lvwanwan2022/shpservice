<template>
  <div class="map-viewer">
    <div class="map-container" ref="mapContainer"></div>
    
    <BaseMapSwitcher v-if="map" :map="map" @base-map-changed="onBaseMapChanged" />
    
    <!-- 添加图层对话框 -->
    <el-dialog title="添加图层" v-model="addLayerDialogVisible" width="800px">
      <div class="dialog-content">
        <el-form :inline="true" :model="layerSearchForm" class="search-form">
          <el-form-item label="服务类型">
            <el-select v-model="layerSearchForm.service_type" placeholder="请选择服务类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="GeoServer服务" value="geoserver" />
              <el-option label="Martin服务" value="martin" />
            </el-select>
          </el-form-item>
          <el-form-item label="专业">
            <el-select v-model="layerSearchForm.discipline" placeholder="请选择专业" clearable>
              <el-option v-for="item in disciplines" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="数据类型">
            <el-select v-model="layerSearchForm.file_type" placeholder="请选择数据类型" clearable>
              <el-option v-for="item in fileTypes" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchLayers">搜索</el-button>
          </el-form-item>
        </el-form>
        
        <el-table :data="availableLayers" style="width: 100%" max-height="400">
          <el-table-column prop="layer_name" label="图层名称" min-width="150" />
          <el-table-column prop="file_type" label="数据类型" width="100" />
          <el-table-column prop="discipline" label="专业" width="100" />
          <el-table-column label="服务状态" width="120">
            <template #default="scope">
              <div class="service-status">
                <el-tag v-if="scope.row.geoserver_service?.is_published" type="success" size="small">GeoServer已发布</el-tag>
                <el-tag v-if="scope.row.martin_service?.is_published" type="primary" size="small">Martin已发布</el-tag>
                <el-tag v-if="!hasAnyPublishedService(scope.row)" type="warning" size="small">未发布</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <div class="layer-actions">
                <el-button 
                  v-if="scope.row.geoserver_service?.is_published"
                  size="small" 
                  type="primary" 
                  @click="addLayerToScene(scope.row, 'geoserver')"
                  :disabled="isLayerInScene(scope.row.id, 'geoserver')"
                >
                  {{ isLayerInScene(scope.row.id, 'geoserver') ? '已添加' : '添加GeoServer' }}
                </el-button>
                <el-button 
                  v-if="scope.row.martin_service?.is_published"
                  size="small" 
                  type="success" 
                  @click="addLayerToScene(scope.row, 'martin')"
                  :disabled="isLayerInScene(scope.row.id, 'martin')"
                >
                  {{ isLayerInScene(scope.row.id, 'martin') ? '已添加' : '添加Martin' }}
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    
    <!-- 图层样式设置对话框 -->
    <el-dialog title="图层样式设置" v-model="styleDialogVisible" width="800px" :close-on-click-modal="false">
      <div class="style-dialog-content" v-if="currentStyleLayer">
        <el-tabs v-model="activeStyleTab">
          <el-tab-pane label="基础样式" name="basic">
            <el-form :model="styleForm" label-width="100px">
              <template v-if="isVectorLayer">
                <template v-if="hasPointGeometry">
                  <h4>点样式</h4>
                  <el-form-item label="大小">
                    <el-slider v-model="styleForm.point.size" :min="1" :max="15" :step="1"></el-slider>
                  </el-form-item>
                  <el-form-item label="颜色">
                    <el-color-picker v-model="styleForm.point.color"></el-color-picker>
                  </el-form-item>
                </template>
                
                <template v-if="hasLineGeometry">
                  <h4>线样式</h4>
                  <el-form-item label="线宽">
                    <el-slider v-model="styleForm.line.width" :min="1" :max="8" :step="1"></el-slider>
                  </el-form-item>
                  <el-form-item label="颜色">
                    <el-color-picker v-model="styleForm.line.color"></el-color-picker>
                  </el-form-item>
                </template>
                
                <template v-if="hasPolygonGeometry">
                  <h4>面样式</h4>
                  <el-form-item label="填充颜色">
                    <el-color-picker v-model="styleForm.polygon.fillColor"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="边框颜色">
                    <el-color-picker v-model="styleForm.polygon.outlineColor"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="透明度">
                    <el-slider v-model="styleForm.polygon.opacity" :min="0" :max="1" :step="0.1"></el-slider>
                  </el-form-item>
                </template>
              </template>
              <template v-else>
                <el-form-item label="透明度">
                  <el-slider v-model="styleForm.raster.opacity" :min="0" :max="1" :step="0.1"></el-slider>
                </el-form-item>
              </template>
            </el-form>
          </el-tab-pane>

          <el-tab-pane v-if="isDxfMartinLayer" label="Martin(DXF)" name="dxf">
            <DxfStyleEditor 
              v-if="currentStyleLayer?.martin_service_id"
              :layer-data="currentStyleLayer" 
              :martin-service-id="currentStyleLayer.martin_service_id"
              @styles-updated="onDxfStylesUpdated"
              @popup-control-changed="onPopupControlChanged"
              ref="dxfStyleEditorRef"
            />
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="styleDialogVisible = false">取消</el-button>
          <el-button v-if="activeStyleTab === 'basic'" type="primary" @click="applyStyle">应用样式</el-button>
          <el-button v-if="activeStyleTab === 'dxf' && isDxfMartinLayer" type="primary" @click="applyAndSaveDxfStyles" :loading="savingDxfStyles">保存样式到数据库</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import gisApi from '@/api/gis'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.vectorgrid'
import { createMapLayerWithFallback } from '@/utils/mapServices'
import { checkMVTSupport } from '@/utils/mvtLayerUtils'
import BaseMapSwitcher from './BaseMapSwitcher.vue'
import DxfStyleEditor from './DxfStyleEditor.vue'
import defaultDxfStylesConfig from '@/config/defaultDxfStyles.json'

// 修复Leaflet图标问题
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png')
})

export default {
  name: 'MapViewer',
  components: { BaseMapSwitcher, DxfStyleEditor },
  props: {
    sceneId: { type: [Number, String], default: null },
    readonly: { type: Boolean, default: false }
  },
  emits: ['layerAdded', 'layer-selected'],
  setup(props, { emit }) {
    const route = useRoute()
    const mapContainer = ref(null)
    const map = ref(null)
    const mapLayers = ref({})
    const mvtLayers = ref({})
    const currentScene = ref(null)
    const layersList = ref([])
    const currentActiveLayer = ref(null)
    
    // 添加图层对话框
    const addLayerDialogVisible = ref(false)
    const availableLayers = ref([])
    const layerSearchForm = reactive({
      service_type: '',
      discipline: '',
      file_type: ''
    })
    
    // 图层样式对话框
    const styleDialogVisible = ref(false)
    const currentStyleLayer = ref(null)
    const activeStyleTab = ref('basic')
    const dxfStyleEditorRef = ref(null)
    const savingDxfStyles = ref(false)
    
    const styleForm = reactive({
      point: { size: 5, color: '#FF0000' },
      line: { width: 2, color: '#0000FF' },
      polygon: { fillColor: '#00FF00', outlineColor: '#000000', opacity: 0.5 },
      raster: { opacity: 1 }
    })
    
    const disciplines = ref(['综合', '测绘', '地勘', '水文', '水工', '施工', '建筑', '金结', '电一', '电二', '消防', '暖通', '给排水', '环水', '移民', '其他'])
    const fileTypes = ref(['shp', 'dem', 'dom', 'dwg', 'dxf', 'geojson'])
    
    const isVectorLayer = computed(() => currentStyleLayer.value && ['shp', 'dwg', 'dxf', 'geojson'].includes(currentStyleLayer.value.file_type))
    const hasPointGeometry = computed(() => isVectorLayer.value)
    const hasLineGeometry = computed(() => isVectorLayer.value)
    const hasPolygonGeometry = computed(() => isVectorLayer.value)
    const isDxfMartinLayer = computed(() => currentStyleLayer.value?.service_type === 'martin' && currentStyleLayer.value?.file_type === 'dxf' && currentStyleLayer.value?.martin_service_id)
    
    // 初始化地图
    const initMap = () => {
      if (map.value) {
        map.value.remove()
        map.value = null
      }
      
      map.value = L.map(mapContainer.value, {
        center: [35.0, 105.0],
        zoom: 5,
        crs: L.CRS.EPSG3857
      })
      
      const baseLayer = createMapLayerWithFallback()
      if (baseLayer) baseLayer.addTo(map.value)
      
      L.control.scale({ imperial: false }).addTo(map.value)
    }
    
    // 加载场景
    const loadScene = async (sceneId) => {
      const response = await gisApi.getScene(sceneId)
      currentScene.value = response.scene
      layersList.value = response.layers
      
      clearAllLayers()
      
      for (const layer of layersList.value) {
        if (layer.service_type === 'martin') {
          await addMartinLayer(layer)
        } else {
          await addGeoServerLayer(layer)
        }
      }
    }
    
    // 添加Martin图层
    const addMartinLayer = async (layer) => {
      if (!layer.mvt_url || !checkMVTSupport()) return
      
      let mvtUrl = layer.mvt_url
      if (mvtUrl.includes('localhost:3000')) {
        const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
        mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
      }
      
      // 默认样式函数
      const createStyleFunction = () => {
        const isDxf = layer.file_type === 'dxf'
        const defaultStyles = isDxf ? defaultDxfStylesConfig.defaultDxfStyles : {}
        
        return (properties) => {
          const layerName = properties.layer || properties.Layer || 'default'
          const layerStyle = defaultStyles[layerName]
          
          const style = {
            weight: layerStyle?.weight || 2,
            color: layerStyle?.color || '#0066cc',
            opacity: layerStyle?.opacity || 0.8,
            fillColor: layerStyle?.fillColor || layerStyle?.color || '#66ccff',
            fillOpacity: layerStyle?.fillOpacity || 0.3,
            radius: layerStyle?.radius || 4
          }
          
          if (layerStyle?.visible === false) {
            style.opacity = 0
            style.fillOpacity = 0
          }
          
          return style
        }
      }
      
      const mvtLayer = L.vectorGrid.protobuf(mvtUrl, {
        vectorTileLayerStyles: { default: createStyleFunction() },
        interactive: true,
        maxZoom: 22
      })
      
      mvtLayer.on('click', (e) => {
        if (!e?.layer?.properties || !mvtLayer._popupEnabled) return
        
        currentActiveLayer.value = layer
        emit('layer-selected', layer)
        
        const properties = e.layer.properties
        const content = Object.entries(properties)
          .filter(([, value]) => value != null && value !== 'NULL' && value !== '')
          .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
          .join('<br/>')
        
        if (e.latlng) {
          L.popup().setContent(`<h4>${layer.layer_name}</h4>${content || '无属性信息'}`).setLatLng(e.latlng).openOn(map.value)
        }
      })
      
      mvtLayer._popupEnabled = true
      mvtLayers.value[layer.id] = mvtLayer
      
      if (layer.visibility) mvtLayer.addTo(map.value)
    }
    
    // 添加GeoServer图层
    const addGeoServerLayer = async (layer) => {
      if (!layer.wms_url || !layer.geoserver_layer) return
      
      let wmsUrl = layer.wms_url.split('?')[0]
      if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
        wmsUrl = '/geoserver/wms'
      }
      
      const wmsLayer = L.tileLayer.wms(wmsUrl, {
        layers: layer.geoserver_layer,
        format: 'image/png',
        transparent: true,
        version: '1.1.1', // 使用更常见的版本
        crs: L.CRS.EPSG4326
      })
      
      wmsLayer.on('click', () => {
        currentActiveLayer.value = layer
        emit('layer-selected', layer)
      })
      
      mapLayers.value[layer.id] = wmsLayer
      
      if (layer.visibility) map.value.addLayer(wmsLayer)
    }
    
    // 清除所有图层
    const clearAllLayers = () => {
      Object.values(mapLayers.value).forEach(layer => map.value.hasLayer(layer) && map.value.removeLayer(layer))
      Object.values(mvtLayers.value).forEach(layer => map.value.hasLayer(layer) && map.value.removeLayer(layer))
      mapLayers.value = {}
      mvtLayers.value = {}
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = (layer) => {
      const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
      if (!targetLayer) return
      
      if (layer.visibility) {
        if (!map.value.hasLayer(targetLayer)) map.value.addLayer(targetLayer)
      } else {
        if (map.value.hasLayer(targetLayer)) map.value.removeLayer(targetLayer)
      }
      
      updateLayerVisibility(layer.id, layer.visibility)
    }
    
    // 更新图层可见性到服务器
    const updateLayerVisibility = async (layerId, visibility) => {
      if (props.readonly) return
      await gisApi.updateSceneLayer(props.sceneId, layerId, { visibility })
    }
    
    // 显示样式设置对话框
    const showStyleDialog = async (layer) => {
      emit('layer-selected', layer)
      currentStyleLayer.value = layer
      activeStyleTab.value = isDxfMartinLayer.value ? 'dxf' : 'basic'
      
      // 重置样式表单
      styleForm.point = { color: '#FF0000', size: 6 }
      styleForm.line = { color: '#0000FF', width: 2 }
      styleForm.polygon = { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
      styleForm.raster = { opacity: 1 }
      
      styleDialogVisible.value = true
    }
    
    // 应用样式
    const applyStyle = async () => {
      if (!currentStyleLayer.value) return
      
      const styleConfig = isVectorLayer.value 
        ? { point: { ...styleForm.point }, line: { ...styleForm.line }, polygon: { ...styleForm.polygon } }
        : { raster: { ...styleForm.raster } }
      
      if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
        await gisApi.updateMartinServiceStyle(currentStyleLayer.value.martin_service_id, styleConfig)
      } else {
        await gisApi.updateLayerStyle(currentStyleLayer.value.id, styleConfig)
      }
      
      // 重新加载图层
      if (currentStyleLayer.value.service_type === 'martin') {
        const mvtLayer = mvtLayers.value[currentStyleLayer.value.id]
        if (mvtLayer && map.value.hasLayer(mvtLayer)) map.value.removeLayer(mvtLayer)
        delete mvtLayers.value[currentStyleLayer.value.id]
        await addMartinLayer(currentStyleLayer.value)
      } else {
        const wmsLayer = mapLayers.value[currentStyleLayer.value.id]
        if (wmsLayer && map.value.hasLayer(wmsLayer)) map.value.removeLayer(wmsLayer)
        delete mapLayers.value[currentStyleLayer.value.id]
        await addGeoServerLayer(currentStyleLayer.value)
      }
      
      styleDialogVisible.value = false
    }
    
    // 显示添加图层对话框
    const showAddLayerDialog = async () => {
      if (!props.sceneId) return
      addLayerDialogVisible.value = true
      await fetchAvailableLayers()
    }
    
    // 获取可用图层
    const fetchAvailableLayers = async () => {
      const params = { ...layerSearchForm }
      Object.keys(params).forEach(key => params[key] === '' && delete params[key])

      const response = await gisApi.getFiles(params)
      let filteredFiles = response.files || []

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
    }
    
    // 搜索图层
    const searchLayers = () => fetchAvailableLayers()
    
    // 检查图层是否已在场景中
    const isLayerInScene = (fileId, serviceType) => layersList.value.some(layer => layer.file_id === fileId && layer.service_type === serviceType)
    
    // 检查文件是否有任何已发布的服务
    const hasAnyPublishedService = (file) => (file.geoserver_service?.is_published) || (file.martin_service?.is_published)
    
    // 添加图层到场景
    const addLayerToScene = async (file, serviceType) => {
      const serviceInfo = serviceType === 'martin' ? file.martin_service : file.geoserver_service
      if (!serviceInfo?.is_published) return
      
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
        const martinService = martinServices.services.find(service => service.file_id === serviceInfo.file_id)
        
        layerData = {
          ...layerData,
          martin_service_id: martinService.database_record_id || martinService.id,
          mvt_url: serviceInfo.mvt_url,
          tilejson_url: serviceInfo.tilejson_url
        }
      } else {
        layerData = {
          ...layerData,
          geoserver_layer_name: serviceInfo.layer_name,
          wms_url: serviceInfo.wms_url,
          wfs_url: serviceInfo.wfs_url
        }
      }
      
      await gisApi.addLayerToScene(props.sceneId, layerData)
      addLayerDialogVisible.value = false
      await loadScene(props.sceneId)
      emit('layerAdded', { sceneId: props.sceneId, layerData })
    }
    
    // 移除图层
    const removeLayer = async (layer) => {
      await gisApi.removeLayerFromScene(props.sceneId, layer.id)
      
      const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
      if (targetLayer) {
        map.value.removeLayer(targetLayer)
        if (layer.service_type === 'martin') {
          delete mvtLayers.value[layer.id]
        } else {
          delete mapLayers.value[layer.id]
        }
      }
      
      layersList.value = layersList.value.filter(item => item.id !== layer.id)
    }
    
    // 底图切换事件处理
    const onBaseMapChanged = () => {}
    
    // 设置当前活动图层
    const setActiveLayer = (layer) => {
      currentActiveLayer.value = layer
      emit('layer-selected', layer)
    }
    
    // 将图层置顶
    const bringLayerToTop = (layer) => {
      currentActiveLayer.value = layer
      emit('layer-selected', layer)
      
      // 禁用所有图层事件
      Object.values(mvtLayers.value).forEach(mvtLayer => mvtLayer._popupEnabled = false)
      
      // 启用目标图层
      if (layer.service_type === 'martin') {
        const mvtLayer = mvtLayers.value[layer.id]
        if (mvtLayer) {
          if (map.value.hasLayer(mvtLayer)) map.value.removeLayer(mvtLayer)
          mvtLayer.addTo(map.value)
          mvtLayer._popupEnabled = true
        }
      } else {
        const wmsLayer = mapLayers.value[layer.id]
        if (wmsLayer) {
          if (map.value.hasLayer(wmsLayer)) map.value.removeLayer(wmsLayer)
          wmsLayer.addTo(map.value)
        }
      }
    }
    
    // DXF样式更新处理
    const onDxfStylesUpdated = () => {}
    
    // 应用并保存DXF样式
    const applyAndSaveDxfStyles = async () => {
      if (!dxfStyleEditorRef.value) return
      
      savingDxfStyles.value = true
      const success = await dxfStyleEditorRef.value.saveStylesToDatabase()
      
      if (success) {
        styleDialogVisible.value = false
        ElMessage.success('DXF样式已保存')
      }
      savingDxfStyles.value = false
    }
    
    // 处理属性弹窗控制
    const onPopupControlChanged = (controlData) => {
      const { enabled, layerId } = controlData
      const mvtLayer = mvtLayers.value[layerId]
      if (mvtLayer) {
        mvtLayer._popupEnabled = enabled
        if (!enabled && map.value) map.value.closePopup()
      }
    }
    
    // 监听sceneId变化
    watch(() => props.sceneId, (newValue, oldValue) => {
      if (newValue && newValue !== oldValue && map.value) {
        setTimeout(() => loadScene(newValue), 100)
      }
    })
    
    onMounted(() => {
      nextTick(() => {
        setTimeout(() => {
          initMap()
          const sceneId = props.sceneId || route.query.scene_id
          if (sceneId) {
            setTimeout(() => loadScene(sceneId), 500)
          }
        }, 100)
      })
    })
    
    onUnmounted(() => {
      clearAllLayers()
      if (map.value) {
        map.value.remove()
        map.value = null
      }
    })
    
    return {
      mapContainer,
      map,
      currentScene,
      layersList,
      currentActiveLayer,
      addLayerDialogVisible,
      availableLayers,
      layerSearchForm,
      disciplines,
      fileTypes,
      styleDialogVisible,
      currentStyleLayer,
      styleForm,
      isVectorLayer,
      hasPointGeometry,
      hasLineGeometry,
      hasPolygonGeometry,
      isDxfMartinLayer,
      toggleLayerVisibility,
      showAddLayerDialog,
      searchLayers,
      addLayerToScene,
      removeLayer,
      showStyleDialog,
      applyStyle,
      onBaseMapChanged,
      isLayerInScene,
      hasAnyPublishedService,
      activeStyleTab,
      dxfStyleEditorRef,
      savingDxfStyles,
      onDxfStylesUpdated,
      applyAndSaveDxfStyles,
      onPopupControlChanged,
      setActiveLayer,
      bringLayerToTop
    }
  },
  expose: ['showStyleDialog', 'showAddLayerDialog', 'toggleLayerVisibility', 'map', 'bringLayerToTop', 'setActiveLayer', 'currentActiveLayer']
}
</script>

<style scoped>
.map-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.dialog-content {
  min-height: 300px;
}

.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.service-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-start;
}

.layer-actions .el-button {
  padding: 4px 8px;
  font-size: 12px;
  min-height: auto;
  line-height: 1.2;
}

.style-dialog-content h4 {
  margin: 15px 0 10px;
  color: #606266;
}
</style>
