<template>
  <div class="map-viewer">
    <div class="map-container" ref="mapContainer"></div>
    
    <BaseMapSwitcherOL v-if="map" :map="map" @base-map-changed="onBaseMapChanged" />
    
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

    <!-- OpenLayers 弹窗 -->
    <div id="popup" class="ol-popup">
      <a href="#" id="popup-closer" class="ol-popup-closer"></a>
      <div id="popup-content"></div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import gisApi from '@/api/gis'
// OpenLayers 相关导入
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorTileLayer from 'ol/layer/VectorTile'
import { OSM, TileWMS, VectorTile } from 'ol/source'
import { fromLonLat } from 'ol/proj'
//import { defaults as defaultControls, ScaleLine } from 'ol/control'
//import Overlay from 'ol/Overlay'
import { Style, Fill, Stroke, Circle } from 'ol/style'
import { MVT } from 'ol/format'
import BaseMapSwitcherOL from './BaseMapSwitcherOL.vue'
import DxfStyleEditor from './DxfStyleEditor.vue'
import defaultDxfStylesConfig from '@/config/defaultDxfStyles.json'

export default {
  name: 'MapViewerOL',
  components: { BaseMapSwitcherOL, DxfStyleEditor },
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
    const popup = ref(null)
    
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
      console.log('=== 开始地图初始化 ===')
      
      // 1. 清理现有地图
      if (map.value) {
        map.value.setTarget(null)
        map.value = null
      }
      
      // 2. 检查容器
      if (!mapContainer.value) {
        console.error('❌ 地图容器未找到')
        return
      }
      console.log('✅ 地图容器已找到:', mapContainer.value)
      
      // 3. 检查OpenLayers导入
      if (!Map || !View || !TileLayer || !OSM) {
        console.error('❌ OpenLayers模块导入失败')
        console.log('Map:', Map, 'View:', View, 'TileLayer:', TileLayer, 'OSM:', OSM)
        return
      }
      console.log('✅ OpenLayers模块导入正常')
      
      try {
        // 4. 创建最简单的OSM底图
        console.log('创建OSM图层...')
        const osmLayer = new TileLayer({
          source: new OSM()
        })
        console.log('✅ OSM图层创建成功')
        
        // 5. 创建地图实例 - 最基本配置
        console.log('创建地图实例...')
        map.value = new Map({
          target: mapContainer.value,
          layers: [osmLayer],
          view: new View({
            center: fromLonLat([116.4, 39.9]), // 北京坐标
            zoom: 10
          })
        })
        console.log('✅ 地图实例创建成功')
        
        // 6. 监听地图渲染
        map.value.once('rendercomplete', () => {
          console.log('🎉 地图首次渲染完成！')
        })
        
        // 7. 延迟强制更新尺寸
        setTimeout(() => {
          if (map.value) {
            console.log('强制更新地图尺寸...')
            map.value.updateSize()
          }
        }, 200)
        
        console.log('=== 地图初始化完成 ===')
        
      } catch (error) {
        console.error('❌ 地图初始化失败:', error)
        console.error('错误堆栈:', error.stack)
      }
    }
    
    // 加载场景
    const loadScene = async (sceneId) => {
      if (!sceneId) {
        console.warn('场景ID为空，跳过加载')
        return
      }
      
      // 检查地图实例是否存在
      if (!map.value) {
        console.warn('地图实例不存在，延迟加载场景:', sceneId)
        // 延迟重试
        setTimeout(() => {
          if (map.value) {
            loadScene(sceneId)
          } else {
            console.error('地图初始化超时，无法加载场景:', sceneId)
          }
        }, 1000)
        return
      }
      
      try {
        console.log('开始加载场景:', sceneId)
        const response = await gisApi.getScene(sceneId)
        currentScene.value = response.scene
        layersList.value = response.layers
        
        console.log('场景数据加载完成，图层数量:', layersList.value.length)
        
        // 清除现有图层
        clearAllLayers()
        
        // 添加新图层
        for (const layer of layersList.value) {
          if (layer.service_type === 'martin') {
            await addMartinLayer(layer)
          } else {
            await addGeoServerLayer(layer)
          }
        }
        
        console.log('✅ 场景加载完成:', response.scene?.name)
        
      } catch (error) {
        console.error('加载场景失败:', error)
        ElMessage.error(`加载场景失败: ${error.message}`)
      }
    }
    
    // 添加Martin图层 - 改进版本
    const addMartinLayer = async (layer) => {
      if (!layer.mvt_url) {
        console.warn('MVT URL不存在，跳过图层:', layer.layer_name)
        return
      }
      
      let mvtUrl = layer.mvt_url
      
      // 处理localhost URL格式
      if (mvtUrl.includes('localhost:3000')) {
        const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
        mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
      }
      
      // 移除.pbf后缀（如果存在）- 与Leaflet版本保持一致
      if (mvtUrl.includes('.pbf')) {
        mvtUrl = mvtUrl.replace('.pbf', '')
        console.log('移除.pbf后缀，新URL:', mvtUrl)
      }
      
      console.log('创建MVT图层:', layer.layer_name, 'URL:', mvtUrl)
      
      // 创建样式函数 - 改进版本
      const createStyleFunction = () => {
        const isDxf = layer.file_type === 'dxf'
        const defaultStyles = isDxf ? defaultDxfStylesConfig.defaultDxfStyles : {}
        
        return (feature) => {
          const properties = feature.getProperties()
          const layerName = properties.layer || properties.Layer || 'default'
          const layerStyle = defaultStyles[layerName] || {}
          
          // 根据几何类型创建不同样式
          const geometryType = feature.getGeometry().getType()
          
          let style
          if (geometryType === 'Point' || geometryType === 'MultiPoint') {
            // 点样式
            style = new Style({
              image: new Circle({
                radius: layerStyle.radius || 4,
                fill: new Fill({
                  color: layerStyle.fillColor || layerStyle.color || '#66ccff'
                }),
                stroke: new Stroke({
                  color: layerStyle.color || '#0066cc',
                  width: 1
                })
              })
            })
          } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
            // 线样式
            style = new Style({
              stroke: new Stroke({
                color: layerStyle.color || '#0066cc',
                width: layerStyle.weight || 2,
                lineDash: layerStyle.dashArray || undefined
              })
            })
          } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
            // 面样式
            style = new Style({
              stroke: new Stroke({
                color: layerStyle.color || '#0066cc',
                width: layerStyle.weight || 1
              }),
              fill: new Fill({
                color: layerStyle.fillColor || (layerStyle.color + '4D') || '#66ccff4D' // 添加透明度
              })
            })
          } else {
            // 默认样式
            style = new Style({
              stroke: new Stroke({
                color: layerStyle.color || '#0066cc',
                width: layerStyle.weight || 2
              }),
              fill: new Fill({
                color: layerStyle.fillColor || layerStyle.color || '#66ccff'
              }),
              image: new Circle({
                radius: layerStyle.radius || 4,
                fill: new Fill({
                  color: layerStyle.fillColor || layerStyle.color || '#66ccff'
                }),
                stroke: new Stroke({
                  color: layerStyle.color || '#0066cc',
                  width: 1
                })
              })
            })
          }
          
          // 处理图层可见性
          if (layerStyle.visible === false) {
            return new Style({}) // 返回空样式以隐藏
          }
          
          return style
        }
      }
      
      try {
        // 创建矢量切片图层 - 完整配置
        const mvtLayer = new VectorTileLayer({
          source: new VectorTile({
            format: new MVT(),
            url: mvtUrl,
            maxZoom: 22,
            wrapX: false // 防止世界重复
          }),
          style: createStyleFunction(),
          opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
          visible: layer.visibility !== false,
          // 添加图层标识
          properties: {
            layerId: layer.id,
            layerName: layer.layer_name,
            serviceType: 'martin'
          }
        })
        
        // 启用弹窗交互
        mvtLayer._popupEnabled = true
        mvtLayer._layerInfo = layer
        
        // 存储图层引用
        mvtLayers.value[layer.id] = mvtLayer
        
        // 添加到地图（如果图层可见）
        if (layer.visibility !== false && map.value) {
          map.value.addLayer(mvtLayer)
          console.log('✅ MVT图层添加成功:', layer.layer_name)
        }
        
        // 添加图层事件监听
        mvtLayer.getSource().on('tileloaderror', (evt) => {
          console.warn('MVT瓦片加载失败:', evt.tile.src_)
        })
        
        mvtLayer.getSource().on('tileloadend', (evt) => {
          console.log('MVT瓦片加载完成:', evt.tile.src_)
        })
        
      } catch (error) {
        console.error('创建MVT图层失败:', error)
        ElMessage.error(`MVT图层创建失败: ${layer.layer_name}`)
      }
    }
    
    // 添加GeoServer图层
    const addGeoServerLayer = async (layer) => {
      if (!layer.wms_url || !layer.geoserver_layer) {
        console.warn('WMS URL或图层名称不存在，跳过图层:', layer.layer_name)
        return
      }
      
      // 检查地图实例是否存在
      if (!map.value) {
        console.error('地图实例不存在，无法添加GeoServer图层:', layer.layer_name)
        return
      }
      
      let wmsUrl = layer.wms_url.split('?')[0]
      if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
        wmsUrl = '/geoserver/wms'
      }
      
      console.log('创建WMS图层:', layer.layer_name, 'URL:', wmsUrl)
      
      try {
        const wmsLayer = new TileLayer({
          source: new TileWMS({
            url: wmsUrl,
            params: {
              'LAYERS': layer.geoserver_layer,
              'FORMAT': 'image/png',
              'TRANSPARENT': true,
              'VERSION': '1.1.1',
              'SRS': 'EPSG:4326'
            },
            serverType: 'geoserver'
          }),
          opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
          visible: layer.visibility !== false,
          // 添加图层标识
          properties: {
            layerId: layer.id,
            layerName: layer.layer_name,
            serviceType: 'geoserver'
          }
        })
        
        // 存储图层引用
        mapLayers.value[layer.id] = wmsLayer
        
        // 添加到地图（如果图层可见）
        if (layer.visibility !== false) {
          map.value.addLayer(wmsLayer)
          console.log('✅ WMS图层添加成功:', layer.layer_name)
        }
        
      } catch (error) {
        console.error('创建WMS图层失败:', error)
        ElMessage.error(`WMS图层创建失败: ${layer.layer_name}`)
      }
    }
    
    // 清除所有图层
    const clearAllLayers = () => {
      if (!map.value) {
        console.warn('地图实例不存在，无法清除图层')
        // 清空图层引用即可
        mapLayers.value = {}
        mvtLayers.value = {}
        return
      }
      
      try {
        Object.values(mapLayers.value).forEach(layer => {
          if (layer && map.value) {
            map.value.removeLayer(layer)
          }
        })
        Object.values(mvtLayers.value).forEach(layer => {
          if (layer && map.value) {
            map.value.removeLayer(layer)
          }
        })
        
        // 清空图层引用
        mapLayers.value = {}
        mvtLayers.value = {}
        
        console.log('✅ 所有图层已清除')
      } catch (error) {
        console.error('清除图层时出错:', error)
        // 强制清空引用
        mapLayers.value = {}
        mvtLayers.value = {}
      }
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = (layer) => {
      const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
      if (!targetLayer) return
      
      if (layer.visibility) {
        map.value.addLayer(targetLayer)
      } else {
        map.value.removeLayer(targetLayer)
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
        if (mvtLayer) {
          map.value.removeLayer(mvtLayer)
          delete mvtLayers.value[currentStyleLayer.value.id]
          await addMartinLayer(currentStyleLayer.value)
        }
      } else {
        const wmsLayer = mapLayers.value[currentStyleLayer.value.id]
        if (wmsLayer) {
          map.value.removeLayer(wmsLayer)
          delete mapLayers.value[currentStyleLayer.value.id]
          await addGeoServerLayer(currentStyleLayer.value)
        }
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
      try {
        if (!props.sceneId) {
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
          const martinService = martinServices.services.find(service => service.file_id === serviceInfo.file_id)
          
          if (!martinService) {
            ElMessage.error('未找到对应的Martin服务')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: -(martinService.database_record_id || martinService.id),
            martin_service_id: martinService.database_record_id || martinService.id,
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
            layer_id: geoserverLayerId,
            geoserver_layer_name: serviceInfo.layer_name,
            wms_url: serviceInfo.wms_url,
            wfs_url: serviceInfo.wfs_url
          }
        }
        
        await gisApi.addLayerToScene(props.sceneId, layerData)
        
        ElMessage.success(`图层 "${file.file_name}" 添加成功`)
        
        addLayerDialogVisible.value = false
        await loadScene(props.sceneId)
        emit('layerAdded', { sceneId: props.sceneId, layerData })
        
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || '添加图层失败'
        ElMessage.error(`添加图层失败: ${errorMessage}`)
      }
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
      
      if (layer.service_type === 'martin') {
        const mvtLayer = mvtLayers.value[layer.id]
        if (mvtLayer) {
          map.value.removeLayer(mvtLayer)
          map.value.addLayer(mvtLayer)
          mvtLayer._popupEnabled = true
        }
      } else {
        const wmsLayer = mapLayers.value[layer.id]
        if (wmsLayer) {
          map.value.removeLayer(wmsLayer)
          map.value.addLayer(wmsLayer)
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
        if (!enabled && popup.value) {
          popup.value.setPosition(undefined)
        }
      }
    }

    /* // 添加地图点击事件处理
    const setupMapClickEvents = () => {
      map.value.on('singleclick', (evt) => {
        const coordinate = evt.coordinate
        const pixel = evt.pixel

        // 检查是否点击了MVT图层
        map.value.forEachFeatureAtPixel(pixel, (feature, layer) => {
          // 找到对应的图层数据
          const layerData = Object.values(mvtLayers.value).find(mvtLayer => mvtLayer === layer)
          if (layerData && layerData._popupEnabled) {
            const layerInfo = layersList.value.find(l => mvtLayers.value[l.id] === layer)
            if (layerInfo) {
              currentActiveLayer.value = layerInfo
              emit('layer-selected', layerInfo)
              
              const properties = feature.getProperties()
              const content = Object.entries(properties)
                .filter(([, value]) => value != null && value !== 'NULL' && value !== '')
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br/>')
              
              const popupContent = `<h4>${layerInfo.layer_name}</h4>${content || '无属性信息'}`
              document.getElementById('popup-content').innerHTML = popupContent
              popup.value.setPosition(coordinate)
              
              return true // 停止进一步检查
            }
          }
        })
      })
    } */
    
    // 监听sceneId变化
    watch(() => props.sceneId, (newValue, oldValue) => {
      if (newValue && newValue !== oldValue && map.value) {
        setTimeout(() => loadScene(newValue), 100)
      }
    })
    
    onMounted(() => {
      nextTick(() => {
        // 增加一个小延迟确保DOM完全渲染
        setTimeout(() => {
          console.log('DOM准备就绪，开始初始化地图...')
          initMap()
          const sceneId = props.sceneId || route.query.scene_id
          if (sceneId) {
            setTimeout(() => loadScene(sceneId), 200)
          }
        }, 50)
      })
    })
    
    onUnmounted(() => {
      clearAllLayers()
      if (map.value) {
        map.value.setTarget(null)
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
  background-color: #e0e0e0; /* 调试背景色 */
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  background-color: #f5f5f5; /* 添加背景色以便调试 */
  border: 2px solid #409eff; /* 临时添加边框以便调试 */
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

/* OpenLayers popup styles */
.ol-popup {
  position: absolute;
  background-color: white;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  padding: 15px;
  border-radius: 10px;
  border: 1px solid #cccccc;
  bottom: 12px;
  left: -50px;
  min-width: 280px;
}
.ol-popup:after, .ol-popup:before {
  top: 100%;
  border: solid transparent;
  content: " ";
  height: 0;
  width: 0;
  position: absolute;
  pointer-events: none;
}
.ol-popup:after {
  border-top-color: white;
  border-width: 10px;
  left: 48px;
  margin-left: -10px;
}
.ol-popup:before {
  border-top-color: #cccccc;
  border-width: 11px;
  left: 48px;
  margin-left: -11px;
}
.ol-popup-closer {
  text-decoration: none;
  position: absolute;
  top: 2px;
  right: 8px;
}
.ol-popup-closer:after {
  content: "✖";
}
</style> 