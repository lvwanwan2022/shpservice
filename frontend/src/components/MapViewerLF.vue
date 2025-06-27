<template>
  <div class="map-viewer">
    <div class="map-container" ref="mapContainer"></div>
    
    <!-- 右上角地图控件 -->
    <div class="map-controls">
      <BaseMapSwitcherLF v-if="map" :map="map" @base-map-changed="onBaseMapChanged" />
      <el-tooltip content="刷新图层" placement="left" :show-after="500">
        <el-button 
          v-if="map" 
          type="success" 
          circle 
          size="small" 
          @click="refreshAllLayers"
          :loading="refreshing"
          class="refresh-button"
        >
          <i class="el-icon-refresh"></i>
        </el-button>
      </el-tooltip>
    </div>
    
    <!-- 右下角坐标信息 -->
    <div class="coordinate-info" v-if="mouseCoordinates">
      <span class="coordinate-text">{{ mouseCoordinates }}</span>
    </div>
    
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
      <div class="style-dialog-content" v-if="styleDialogVisible && currentStyleLayer && activeStyleTab">
        <el-tabs v-model="activeStyleTab" :key="`style-tabs-${currentStyleLayer.id || 'unknown'}-${activeStyleTab}`">
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

          <el-tab-pane v-if="isDxfMartinLayer === true" label="Martin(DXF)" name="dxf">
            <div v-if="currentStyleLayer && currentStyleLayer.martin_service_id">
              <DxfStyleEditor 
                :key="`dxf-editor-${currentStyleLayer.martin_service_id}`"
                :layer-data="currentStyleLayer" 
                :martin-service-id="currentStyleLayer.martin_service_id"
                @styles-updated="onDxfStylesUpdated"
                @popup-control-changed="onPopupControlChanged"
                ref="dxfStyleEditorRef"
              />
            </div>
            <div v-else class="loading-placeholder">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在加载样式编辑器...</span>
              <div style="margin-top: 10px; font-size: 12px; color: #999;">
                调试信息: martin_service_id = {{ currentStyleLayer?.martin_service_id }} ({{ typeof currentStyleLayer?.martin_service_id }})
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div v-else class="dialog-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在初始化对话框...</span>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="styleDialogVisible = false">取消</el-button>
          <el-button v-if="activeStyleTab === 'basic'" type="primary" @click="applyStyle">应用样式</el-button>
          <el-button v-if="activeStyleTab === 'dxf' && isDxfMartinLayer === true" type="primary" @click="applyAndSaveDxfStyles" :loading="savingDxfStyles">保存样式到数据库</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick, toRaw } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import gisApi from '@/api/gis'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.vectorgrid'
import { createMapLayerWithFallback } from '@/utils/mapServices'
import { checkMVTSupport } from '@/utils/mvtLayerUtils'
import BaseMapSwitcherLF from './BaseMapSwitcherLF.vue'
import DxfStyleEditor from './DxfStyleEditor.vue'
import defaultDxfStylesConfig from '@/config/defaultDxfStyles.json'
import { MARTIN_BASE_URL } from '@/config/index'
import { getRecommendedPreloadLevel, getRecommendedCacheSize, getDeviceType } from '@/utils/deviceUtils'

// 修复Leaflet图标问题
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png')
})

export default {
  name: 'MapViewer',
  components: { BaseMapSwitcherLF, DxfStyleEditor, Loading },
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
    const isDxfMartinLayer = computed(() => {
      return currentStyleLayer.value?.service_type === 'martin' && 
             currentStyleLayer.value?.file_type === 'dxf' && 
             Boolean(currentStyleLayer.value?.martin_service_id)
    })
    
    // 全局变量，用于跟踪地图状态
    const mapState = reactive({
      isAnimating: false,
      isZooming: false,
      popupsEnabled: true
    })
    
    // 鼠标坐标信息
    const mouseCoordinates = ref(null)
    
    // 当前底图版权信息
    const currentBaseMapAttribution = ref('')
    
    // 刷新状态
    const refreshing = ref(false)
    
    // 安全地显示弹窗的辅助函数
    const safeShowPopup = (latlng, content) => {
      if (!map.value || !latlng || mapState.isAnimating || mapState.isZooming || !mapState.popupsEnabled) {
        return null
      }
      
      try {
        // 获取原始地图对象，避免 Vue 响应式代理
        const rawMap = toRaw(map.value)
        // 获取原始坐标，避免 Vue 响应式代理
        const rawLatLng = toRaw(latlng)
        
        // 确保先关闭所有现有弹窗
        rawMap.closePopup()
        
        // 创建新弹窗，禁用关闭按钮
        const popup = L.popup({          
          className: 'no-close-button-popup', // 添加自定义类名，以便于样式控制
          autoClose: true, // 点击地图其他位置时自动关闭
          closeOnEscapeKey: true // 按ESC键可关闭
        })
          .setContent(content)
          .setLatLng(rawLatLng)
        
        // 添加到地图
        popup.openOn(rawMap)
        return popup
      } catch (error) {
        console.error('显示弹窗时出错:', error)
        return null
      }
    }
    
    // 初始化地图
    const initMap = () => {
      if (map.value) {
        map.value.remove()
        map.value = null
      }
      
      map.value = L.map(mapContainer.value, {
        center: [35.0, 105.0],
        zoom: 5,
        crs: L.CRS.EPSG3857,
        maxZoom: 23,  // 全局最大缩放级别（适配所有底图）
        minZoom: 1    // 全局最小缩放级别
      })
      
      // 底图将由BaseMapSwitcherLF组件管理，不在这里添加默认底图
      
      L.control.scale({ imperial: false }).addTo(map.value)
      
      // 添加鼠标坐标跟踪
      initializeCoordinateTracking()
      
      // 设置默认底图版权信息
      updateBaseMapAttribution('gaode')
      
      // 添加地图事件监听器，在可能导致弹窗位置错误的操作前关闭所有弹窗
      map.value.on('zoomstart', () => {
        if (map.value) {
          // 获取原始地图对象，避免 Vue 响应式代理
          const rawMap = toRaw(map.value)
          
          // 更新地图状态
          mapState.isZooming = true
          mapState.popupsEnabled = false
          
          // 关闭所有弹窗
          rawMap.closePopup()
          
          // 临时禁用所有图层的弹窗功能
          Object.values(mvtLayers.value).forEach(layer => {
            if (layer) {
              // 获取原始图层对象，避免 Vue 响应式代理
              const rawLayer = toRaw(layer)
              rawLayer._popupEnabled = false
            }
          })
          
          // 移除地图上可能存在的弹窗元素
          const popups = document.querySelectorAll('.leaflet-popup')
          popups.forEach(popup => {
            popup.remove()
          })
          
          // 清除可能存在的弹窗相关引用
          if (rawMap._popup) {
            rawMap._popup = null
          }
        }
      })
      
      // 缩放结束后重新启用弹窗功能
      map.value.on('zoomend', () => {
        // 延迟一点重新启用弹窗功能，确保缩放动画完全结束
        setTimeout(() => {
          mapState.isZooming = false
          mapState.popupsEnabled = true
          
          Object.values(mvtLayers.value).forEach(layer => {
            if (layer) {
              // 获取原始图层对象，避免 Vue 响应式代理
              const rawLayer = toRaw(layer)
              rawLayer._popupEnabled = true
            }
          })
        }, 100)
      })
      
      map.value.on('dragstart', () => {
        if (map.value) {
          // 获取原始地图对象，避免 Vue 响应式代理
          const rawMap = toRaw(map.value)
          
          // 更新地图状态
          mapState.isAnimating = true
          mapState.popupsEnabled = false
          
          // 关闭所有弹窗
          rawMap.closePopup()
        }
      })
      
      map.value.on('dragend', () => {
        // 延迟一点重新启用弹窗功能，确保拖动动画完全结束
        setTimeout(() => {
          mapState.isAnimating = false
          mapState.popupsEnabled = true
        }, 100)
      })
    }
    
    // 加载场景
    const loadScene = async (sceneId) => {
      try {
        // 确保地图实例已经初始化
        if (!map.value) {
          console.warn('地图尚未初始化，等待初始化完成后再加载场景')
          return
        }

        const response = await gisApi.getScene(sceneId)
        //console.log('Leaflet场景API响应:', response)
        
        currentScene.value = response.data.scene
        
        // 🔥 确保layers是数组
        if (response.data.layers && Array.isArray(response.data.layers)) {
          layersList.value = response.data.layers
        } else {
          //console.log('场景图层数据:', response.data.layers)
          console.warn('场景图层数据不是数组，使用空数组:', response.data.layers)
          layersList.value = []
        }
        
        clearAllLayers()
        
        // 确保layersList是数组再进行迭代
        if (layersList.value && Array.isArray(layersList.value)) {
          for (const layer of layersList.value) {
            //console.log('Leaflet处理图层:', layer.layer_name, '服务类型:', layer.service_type)
            if (layer.service_type === 'martin') {
              await addMartinLayer(layer)
            } else {
              await addGeoServerLayer(layer)
            }
          }
        } else {
          console.warn('layersList.value不是数组，跳过图层加载:', layersList.value)
        }
      } catch (error) {
        console.error('加载场景失败:', error)
      }
    }
    
    // 添加Martin图层
    const addMartinLayer = async (layer) => {
      if (!layer.mvt_url || !checkMVTSupport()) return
      
      // 确保地图实例已经初始化
      if (!map.value) {
        console.warn('地图尚未初始化，无法添加Martin图层')
        return
      }
      
      //console.log(`🎨 开始加载Martin图层: ${layer.layer_name}, 文件类型: ${layer.file_type}, Martin服务ID: ${layer.martin_service_id}`)
      
      let mvtUrl = layer.mvt_url
      if (mvtUrl.includes('localhost:3000')) {
        // 检查是否是 MBTiles 服务
        if (layer.file_type === 'mbtiles' || mvtUrl.includes('/mbtiles/')) {
          const mbtilesMatch = mvtUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
          const fileName = mbtilesMatch[1] || 'default'

          mvtUrl = `${MARTIN_BASE_URL}/mbtiles/${fileName}/{z}/{x}/{y}`
        } else {

          const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'

          mvtUrl = `${MARTIN_BASE_URL}/${tableName}/{z}/{x}/{y}`
        }
      }
      
      // 调试：获取Martin服务的TileJSON信息
      try {
        const tileJsonUrl = layer.tilejson_url || mvtUrl.replace('/{z}/{x}/{y}', '.json')
        //console.log('🎨 TileJSON URL:', tileJsonUrl)
        // 请修改常量赋值错误修改
        const tileJsonUrl_re=tileJsonUrl.replace('http://localhost:3000',MARTIN_BASE_URL)
        //console.log('tileJsonUrl',tileJsonUrl_re)
        const response = await fetch(tileJsonUrl_re)
        if (response.ok) {
          const tileJson = await response.json()
          //console.log('🎨 TileJSON内容:', tileJson)
          //console.log('🎨 可用图层:', tileJson.vector_layers)
        } else {
          console.warn('🎨 无法获取TileJSON:', response.status)
        }
      } catch (error) {
        console.warn('🎨 获取TileJSON失败:', error)
      }
      
      // DXF样式函数 - 实现README中的样式映射逻辑
      const createLocalStyleFunction = async () => {
        // 使用新的独立样式函数创建方法
        return await createDxfStyleFunction(layer)
      }

      // 创建样式函数
      const styleFunction = await createLocalStyleFunction()
      
      //console.log('🎨 创建MVT图层，URL:', mvtUrl)
      
      // 尝试从URL提取表名作为图层名
      let tableName = 'default'
      if (layer.file_type === 'mbtiles' || layer.file_type === 'vector.mbtiles' || layer.file_type === 'raster.mbtiles' || mvtUrl.includes('/mbtiles/')) {
        // 从 MBTiles URL 提取文件名
        const mbtilesMatch = mvtUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
        tableName = mbtilesMatch[1] || 'default'
      } else {
        // 从普通 Martin URL 提取表名
        tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
      }
      //console.log('🎨 提取的表名/图层名:', tableName)
      
      let mvtLayer;
      
      // 检查是否为栅格mbtiles
      if (layer.file_type === 'raster.mbtiles') {
        //console.log('创建栅格MBTiles图层:', layer.layer_name);
        // 使用普通瓦片图层加载栅格mbtiles
        mvtLayer = L.tileLayer(mvtUrl, {
          maxZoom: 22,
          attribution: `MBTiles: ${layer.layer_name}`
        });
      } else {
        // 使用矢量瓦片加载矢量mbtiles和其他矢量数据
        mvtLayer = L.vectorGrid.protobuf(mvtUrl, {
          vectorTileLayerStyles: { 
            // 使用多种可能的图层名称
            [tableName]: styleFunction,
            'default': styleFunction,
            // 有时Martin使用完整的表名
            [`public.${tableName}`]: styleFunction
          },
          interactive: true,
          maxZoom: 22,
          // 移除调试代码，避免性能问题
          getFeatureId: function(feature) {
            return feature.properties?.gid || feature.id;
          }
        });
        //console.log('创建矢量MBTiles图层:', layer.layer_name);
      }
      
      // 根据图层类型添加不同的事件监听器
      if (layer.file_type === 'raster.mbtiles') {
        // 栅格图层事件
        mvtLayer.on('error', (e) => {
          console.error('🎨 栅格MBTiles瓦片加载错误:', e)
        })
        
        mvtLayer.on('click', (e) => {
          // 如果地图状态不允许显示弹窗，直接返回
          if (mapState.isAnimating || mapState.isZooming || !mapState.popupsEnabled) return
          
          currentActiveLayer.value = layer
          emit('layer-selected', layer)
          
          // 栅格图层点击时只显示基本信息
          safeShowPopup(e.latlng, `<h4>${layer.layer_name}</h4><p>栅格MBTiles图层</p>`)
        })
      } else {
        // 矢量图层事件
        mvtLayer.on('tileerror', (e) => {
          console.error('🎨 MVT瓦片加载错误:', e)
        })
        
        mvtLayer.on('click', (e) => {
          // 如果图层禁用了弹窗或地图状态不允许显示弹窗，直接返回
          if (!e?.layer?.properties || !mvtLayer._popupEnabled || 
              mapState.isAnimating || mapState.isZooming || !mapState.popupsEnabled) return
          
          currentActiveLayer.value = layer
          emit('layer-selected', layer)
          
          const properties = e.layer.properties
          
          // 构建属性信息显示内容
          const content = Object.entries(properties)
            .filter(([, value]) => value != null && value !== 'NULL' && value !== '')
            .map(([key, value]) => {
              // 特殊处理CAD图层信息
              if (key === 'cad_layer') {
                return `<strong>CAD图层:</strong> ${value}`
              }
              return `<strong>${key}:</strong> ${value}`
            })
            .join('<br/>')
          
          if (e.latlng) {
            // 显示图层名称和CAD图层信息
            const title = layer.layer_name
            const cadLayer = properties.cad_layer ? ` (${properties.cad_layer})` : ''
            
            // 使用安全弹窗辅助函数
            safeShowPopup(e.latlng, `<h4>${title}${cadLayer}</h4>${content || '无属性信息'}`)
          }
        })
      }
      
      // 为所有类型的图层设置通用属性
      mvtLayer._popupEnabled = true
      mvtLayers.value[layer.id] = mvtLayer
      
      if (layer.visibility) {
        // 确保地图状态稳定后再添加图层
        if (map.value && !map.value._animating && !map.value._zooming) {
          // 获取原始地图对象和图层，避免 Vue 响应式代理
          const rawMap = toRaw(map.value)
          const rawLayer = toRaw(mvtLayer)
          
          // 设置业务图层的z-index确保在底图之上
          if (rawLayer.setZIndex) {
            const zIndex = 100 + Object.keys(mvtLayers.value).length
            rawLayer.setZIndex(zIndex)
          }
          
          rawLayer.addTo(rawMap)
        } else {
          // 如果地图正在动画，等待动画完成
          const addWhenReady = () => {
            if (map.value && !map.value._animating && !map.value._zooming) {
              // 获取原始地图对象和图层，避免 Vue 响应式代理
              const rawMap = toRaw(map.value)
              const rawLayer = toRaw(mvtLayer)
              
              // 设置业务图层的z-index确保在底图之上
              if (rawLayer.setZIndex) {
                const zIndex = 100 + Object.keys(mvtLayers.value).length
                rawLayer.setZIndex(zIndex)
              }
              
              rawLayer.addTo(rawMap)
            } else {
              setTimeout(addWhenReady, 50)
            }
          }
          addWhenReady()
        }
      }
    }
    
    // 添加GeoServer图层
    const addGeoServerLayer = async (layer) => {
      if (!layer.wms_url || !layer.geoserver_layer) return
      
      // 确保地图实例已经初始化
      if (!map.value) {
        console.warn('地图尚未初始化，无法添加GeoServer图层')
        return
      }
      
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
      
      if (layer.visibility && map.value) {
        // 获取原始地图对象和图层，避免 Vue 响应式代理
        const rawMap = toRaw(map.value)
        const rawLayer = toRaw(wmsLayer)
        
        // 设置WMS图层的z-index确保在底图之上
        if (rawLayer.setZIndex) {
          const zIndex = 200 + Object.keys(mapLayers.value).length
          rawLayer.setZIndex(zIndex)
        }
        
        rawLayer.addTo(rawMap)
      }
    }
    
    // 清除所有图层
    const clearAllLayers = () => {
      // 如果地图未初始化，直接返回
      if (!map.value) {
        mvtLayers.value = {}
        mapLayers.value = {}
        return
      }
      
      // 获取原始地图对象，避免 Vue 响应式代理
      const rawMap = toRaw(map.value)
      
      // 清理MVT图层
      Object.entries(mvtLayers.value).forEach(([layerId, layer]) => {
        try {
          const rawLayer = toRaw(layer)
          if (rawMap && rawMap.hasLayer(rawLayer)) {
            rawMap.removeLayer(rawLayer)
          }
          // 清理事件监听器
          if (rawLayer.off) {
            rawLayer.off()
          }
        } catch (error) {
          console.warn(`清理MVT图层 ${layerId} 时出错:`, error)
        }
      })
      
      // 清理WMS图层
      Object.entries(mapLayers.value).forEach(([layerId, layer]) => {
        try {
          const rawLayer = toRaw(layer)
          if (rawMap && rawMap.hasLayer(rawLayer)) {
            rawMap.removeLayer(rawLayer)
          }
          // 清理事件监听器
          if (rawLayer.off) {
            rawLayer.off()
          }
        } catch (error) {
          console.warn(`清理WMS图层 ${layerId} 时出错:`, error)
        }
      })
      
      mapLayers.value = {}
      mvtLayers.value = {}
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = (layer) => {
      const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
      if (!targetLayer || !map.value) return
      
      // 获取原始地图对象和图层，避免 Vue 响应式代理
      const rawMap = toRaw(map.value)
      const rawLayer = toRaw(targetLayer)
      
      if (layer.visibility) {
        if (!rawMap.hasLayer(rawLayer)) {
          // 重新显示图层时设置正确的z-index
          if (rawLayer.setZIndex) {
            if (layer.service_type === 'martin') {
              const zIndex = 100 + Object.keys(mvtLayers.value).length
              rawLayer.setZIndex(zIndex)
            } else {
              const zIndex = 200 + Object.keys(mapLayers.value).length
              rawLayer.setZIndex(zIndex)
            }
          }
          rawMap.addLayer(rawLayer)
        }
      } else {
        if (rawMap.hasLayer(rawLayer)) rawMap.removeLayer(rawLayer)
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
      // console.log('=== showStyleDialog 被调用 ===')
      // console.log('传入的 layer 参数:', layer)
      // console.log('layer 完整对象:', JSON.stringify(layer, null, 2))
      
      emit('layer-selected', layer)
      currentStyleLayer.value = layer
      activeStyleTab.value = isDxfMartinLayer.value ? 'dxf' : 'basic'
      
      // console.log('设置后的状态:')
      // console.log('currentStyleLayer.value:', currentStyleLayer.value)
      // console.log('activeStyleTab.value:', activeStyleTab.value)
      // console.log('isDxfMartinLayer.value:', isDxfMartinLayer.value)
      
      // 重置样式表单
      styleForm.point = { color: '#FF0000', size: 6 }
      styleForm.line = { color: '#0000FF', width: 2 }
      styleForm.polygon = { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
      styleForm.raster = { opacity: 1 }
      
      styleDialogVisible.value = true
      // console.log('styleDialogVisible 设置为 true')
      // console.log('================================')
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
        //console.log('🔍 添加图层到场景 - 开始:', { file, serviceType, sceneId: props.sceneId })
        
        if (!props.sceneId) {
          console.error('❌ 缺少场景ID')
          ElMessage.error('缺少场景ID，无法添加图层')
          return
        }
        
        const serviceInfo = serviceType === 'martin' ? file.martin_service : file.geoserver_service
        //console.log('🔍 服务信息:', serviceInfo)
        
        if (!serviceInfo?.is_published) {
          console.error('❌ 服务未发布或不存在:', serviceInfo)
          ElMessage.error('服务未发布或不存在')
          return
        }
        
        // 基础图层数据，注意添加layer_id字段
        let layerData = {
          layer_name: file.file_name,
          visible: true,
          service_type: serviceType,
          file_id: file.id,
          file_type: file.file_type,
          discipline: file.discipline
        }
        
        //console.log('🔍 基础图层数据:', layerData)
        
        if (serviceType === 'martin') {
          //console.log('🔍 处理Martin服务...')
          const martinServices = await gisApi.searchMartinServices({ file_id: serviceInfo.file_id })
          //console.log('🔍 Martin服务搜索结果:', martinServices)
          
          const martinService = martinServices.services.find(service => service.file_id === serviceInfo.file_id)
          //console.log('🔍 找到的Martin服务:', martinService)
          
          if (!martinService) {
            console.error('❌ 未找到对应的Martin服务')
            ElMessage.error('未找到对应的Martin服务')
            return
          }
          
          layerData = {
            ...layerData,
            // 对于Martin服务，使用martin_service_id作为layer_id
            layer_id: martinService.database_record_id || martinService.id,
            martin_service_id: String(martinService.database_record_id || martinService.id),  // 确保为字符串
            mvt_url: serviceInfo.mvt_url,
            tilejson_url: serviceInfo.tilejson_url
          }
        } else {
          //console.log('🔍 处理GeoServer服务...')
          // 对于GeoServer服务，layer_id应该是geoserver_layers表中的实际ID
          // 这里需要从serviceInfo中获取实际的layer_id
          const geoserverLayerId = serviceInfo.layer_id
          if (!geoserverLayerId) {
            console.error('❌ GeoServer服务缺少图层ID:', serviceInfo)
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
        
        //console.log('🔍 最终图层数据:', layerData)
        //console.log('🔍 调用API添加图层到场景...')
        
        await gisApi.addLayerToScene(props.sceneId, layerData)
        
        //console.log('✅ 图层添加成功')
        ElMessage.success(`图层 "${file.file_name}" 添加成功`)
        
        addLayerDialogVisible.value = false
        await loadScene(props.sceneId)
        emit('layerAdded', { sceneId: props.sceneId, layerData })
        
      } catch (error) {
        console.error('❌ 添加图层到场景失败:', error)
        console.error('错误详情:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        
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
    const onBaseMapChanged = (baseMapType) => {
      //console.log(`底图切换到: ${baseMapType}`)
      updateBaseMapAttribution(baseMapType)
      
      // 修复图层显示顺序问题
      setTimeout(() => {
        refreshLayersOrder()
      }, 100)
    }
    
    // 刷新图层显示顺序
    const refreshLayersOrder = () => {
      if (!map.value) return
      
      //console.log('刷新图层显示顺序...')
      
      try {
        // 1. 重新设置所有图层的z-index
        let mvtIndex = 0
        let wmsIndex = 0
        
        // 设置MVT图层的z-index
        Object.values(mvtLayers.value).forEach(mvtLayer => {
          if (mvtLayer && map.value.hasLayer(mvtLayer) && mvtLayer.setZIndex) {
            mvtLayer.setZIndex(100 + mvtIndex++)
          }
        })
        
        // 设置WMS图层的z-index
        Object.values(mapLayers.value).forEach(wmsLayer => {
          if (wmsLayer && map.value.hasLayer(wmsLayer) && wmsLayer.setZIndex) {
            wmsLayer.setZIndex(200 + wmsIndex++)
          }
        })
        
        // 2. 强制重新渲染地图
        setTimeout(() => {
          if (map.value) {
            map.value.invalidateSize()
            // 触发地图重绘
            map.value.fire('layerChange')
          }
        }, 50)
        
        //console.log(`已刷新图层z-index: MVT图层${mvtIndex}个, WMS图层${wmsIndex}个`)
        
      } catch (error) {
        console.error('刷新图层顺序失败:', error)
      }
    }
    
    // 初始化坐标跟踪
    const initializeCoordinateTracking = () => {
      if (!map.value) return
      
      map.value.on('mousemove', (e) => {
        if (e.latlng) {
          const lat = e.latlng.lat.toFixed(6)
          const lng = e.latlng.lng.toFixed(6)
          mouseCoordinates.value = `${lng}°, ${lat}°`
        }
      })
      
      map.value.on('mouseout', () => {
        mouseCoordinates.value = null
      })
    }
    
    // 更新底图版权信息
    const updateBaseMapAttribution = (baseMapType) => {
      const attributions = {
        'gaode': '© 高德',
        'gaodeSatellite': '© 高德',
        'osm': '© OpenStreetMap',
        'esriSatellite': '© Esri',
        'google': '© Google',
        'tianditu': '© 天地图'
      }
      
      currentBaseMapAttribution.value = attributions[baseMapType] || '© Leaflet'
    }
    
    // 刷新所有图层
    const refreshAllLayers = async () => {
      if (!map.value || refreshing.value) return
      
      refreshing.value = true
      
      try {
        //console.log('开始刷新所有图层...')
        
        // 获取当前场景ID
        const currentSceneId = props.sceneId || route.query.scene_id
        
        if (currentSceneId) {
          // 重新加载场景图层
          await loadScene(currentSceneId)
          //console.log('图层刷新完成')
        } else {
          console.warn('没有场景ID，无法刷新图层')
        }
        
      } catch (error) {
        console.error('刷新图层失败:', error)
      } finally {
        refreshing.value = false
      }
    }
    
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
    const onDxfStylesUpdated = async (eventData = {}) => {
      // 实时更新DXF样式 - 直接重新加载图层（更安全可靠）
      if (currentStyleLayer.value && currentStyleLayer.value.service_type === 'martin') {
        try {
          const { layerName, style, allStyles } = eventData
          
          //console.log('🎨 收到DXF样式更新事件:', eventData)
          
          // 检查地图是否正在动画中
          if (map.value && (map.value._animating || map.value._zooming)) {
            //console.log('🎨 地图正在动画中，延迟样式更新...')
            setTimeout(() => onDxfStylesUpdated(eventData), 100)
            return
          }
          
          // 安全地移除图层
          const mvtLayer = mvtLayers.value[currentStyleLayer.value.id]
          if (mvtLayer) {
            try {
              if (map.value && map.value.hasLayer(mvtLayer)) {
                map.value.removeLayer(mvtLayer)
              }
              // 清理事件监听器
              if (mvtLayer.off) {
                mvtLayer.off()
              }
            } catch (removeError) {
              console.warn('移除图层时出错:', removeError)
            }
            delete mvtLayers.value[currentStyleLayer.value.id]
          }
          
          // 重新添加图层
          await addMartinLayer(currentStyleLayer.value)
          
          if (layerName) {
            //console.log(`🎨 DXF图层 "${layerName}" 样式已更新`)
          } else {
            //console.log('🎨 DXF样式已更新')
          }
          
        } catch (error) {
          console.error('更新DXF样式失败:', error)
          ElMessage.error('更新DXF样式失败')
        }
      }
    }
    
    // 强制刷新Martin图层样式
    const refreshMartinLayerStyle = async (layer) => {
      if (!layer || layer.service_type !== 'martin') return
      
      try {
        // 安全地移除当前图层
        const mvtLayer = mvtLayers.value[layer.id]
        if (mvtLayer) {
          try {
            if (map.value && map.value.hasLayer(mvtLayer)) {
              map.value.removeLayer(mvtLayer)
            }
            // 清理事件监听器
            if (mvtLayer.off) {
              mvtLayer.off()
            }
          } catch (removeError) {
            console.warn('移除图层时出错:', removeError)
          }
          delete mvtLayers.value[layer.id]
        }
        
        // 重新添加图层（会自动应用最新样式）
        await addMartinLayer(layer)
        
        //console.log(`图层 "${layer.layer_name}" 样式已刷新`)
      } catch (error) {
        console.error('刷新图层样式失败:', error)
        throw error
      }
    }

    // 应用并保存DXF样式
    const applyAndSaveDxfStyles = async () => {
      if (!dxfStyleEditorRef.value) return
      
      savingDxfStyles.value = true
      try {
        const success = await dxfStyleEditorRef.value.saveStylesToDatabase()
        
        if (success) {
          // 保存成功后，刷新图层样式
          if (currentStyleLayer.value) {
            await refreshMartinLayerStyle(currentStyleLayer.value)
          }
          
          styleDialogVisible.value = false
          ElMessage.success('DXF样式已保存并应用到地图')
        }
      } catch (error) {
        console.error('保存DXF样式失败:', error)
        ElMessage.error('保存DXF样式失败')
      } finally {
        savingDxfStyles.value = false
      }
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
    
    // 强制更新MVT图层样式（不重新加载图层）
    const updateMvtLayerStyles = async (layer) => {
      if (!layer || layer.service_type !== 'martin') return
      
      const mvtLayer = mvtLayers.value[layer.id]
      if (!mvtLayer || !map.value) return
      
      try {
        //console.log('🎨 开始更新MVT图层样式...')
        
        // 检查地图是否正在动画中，如果是则等待动画完成
        if (map.value._animating || map.value._zooming) {
          //console.log('🎨 地图正在动画中，等待动画完成...')
          await new Promise(resolve => {
            const checkAnimation = () => {
              if (!map.value._animating && !map.value._zooming) {
                resolve()
              } else {
                setTimeout(checkAnimation, 50)
              }
            }
            checkAnimation()
          })
        }
        
        // 获取最新的样式函数
        const styleFunction = await createDxfStyleFunction(layer)
        if (!styleFunction) {
          throw new Error('无法创建样式函数')
        }
        
        // 强制重新设置样式
        const tableName = layer.mvt_url?.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
        
        // 更新vectorTileLayerStyles
        mvtLayer.options.vectorTileLayerStyles = {
          [tableName]: styleFunction,
          'default': styleFunction,
          [`public.${tableName}`]: styleFunction
        }
        
        // 安全地强制重新渲染图层
        if (mvtLayer._map && map.value.hasLayer(mvtLayer)) {
          // 确保地图状态稳定后再操作
          setTimeout(() => {
            try {
              if (map.value && mvtLayer._map && map.value.hasLayer(mvtLayer)) {
                // 临时移除并重新添加图层
                map.value.removeLayer(mvtLayer)
                // 使用 nextTick 确保 DOM 更新完成
                setTimeout(() => {
                  if (map.value && !map.value._animating && !map.value._zooming) {
                    map.value.addLayer(mvtLayer)
                  }
                }, 10)
              }
            } catch (reRenderError) {
              console.warn('🎨 重新渲染图层时出错:', reRenderError)
            }
          }, 10)
        }
        
        //console.log('🎨 MVT图层样式更新完成')
      } catch (error) {
        console.error('更新MVT图层样式失败:', error)
        throw error
      }
    }
    
    // 创建样式函数（提取为独立方法以便重用）
    const createDxfStyleFunction = async (layerData = null) => {
      const targetLayer = layerData || currentStyleLayer.value
      if (!targetLayer) return null
      
      const isDxf = targetLayer.file_type === 'dxf'
      //console.log('🎨 创建样式函数，isDxf:', isDxf)
      
      if (!isDxf) {
        // 非DXF文件使用默认样式
        return (properties, zoom, geometryDimension) => ({
          weight: 2,
          color: '#0066cc',
          opacity: 0.8,
          fillColor: '#66ccff',
          fillOpacity: 0.3,
          radius: 4
        })
      }

      // DXF默认样式配置（中等优先级）
      const defaultDxfStyles = defaultDxfStylesConfig.defaultDxfStyles || {}
      
      // 系统通用默认样式（最低优先级）
      const systemDefaultStyle = {
        weight: 1.5,
        color: '#666666',
        opacity: 0.8,
        fillColor: '#CCCCCC',
        fill: false,
        fillOpacity: 0.3,
        radius: 4,
        visible: true
      }

      return (properties, zoom, geometryDimension) => {
        // 1. 从MVT要素的properties.cad_layer字段读取图层名称
        const cadLayerName = properties?.cad_layer || properties?.layer || properties?.Layer
        
        if (!cadLayerName) {
          // 如果没有图层名称，使用系统默认样式
          return {
            weight: systemDefaultStyle.weight,
            color: systemDefaultStyle.color,
            opacity: systemDefaultStyle.opacity,
            fillColor: systemDefaultStyle.fillColor,
            fillOpacity: systemDefaultStyle.fillOpacity,
            radius: systemDefaultStyle.radius
          }
        }

        // 2. 实时获取用户自定义样式（最高优先级）
        let userCustomStyles = {}
        if (dxfStyleEditorRef.value && typeof dxfStyleEditorRef.value.getStyles === 'function') {
          try {
            userCustomStyles = dxfStyleEditorRef.value.getStyles() || {}
          } catch (error) {
            console.warn('获取实时样式失败:', error)
          }
        }

        // 3. 样式优先级查找
        let layerStyle = null

        // 最高优先级：用户自定义样式（实时获取）
        if (userCustomStyles[cadLayerName]) {
          layerStyle = userCustomStyles[cadLayerName]
        }
        // 中等优先级：DXF默认样式配置
        else if (defaultDxfStyles[cadLayerName]) {
          layerStyle = defaultDxfStyles[cadLayerName]
        }
        // 最低优先级：系统通用默认样式
        else {
          layerStyle = systemDefaultStyle
        }

        // 4. 构建Leaflet样式对象
        const style = {
          weight: layerStyle.weight || systemDefaultStyle.weight,
          color: layerStyle.color || systemDefaultStyle.color,
          opacity: layerStyle.opacity || systemDefaultStyle.opacity,
          fillColor: layerStyle.fillColor || layerStyle.color || systemDefaultStyle.fillColor,
          fillOpacity: layerStyle.fillOpacity || systemDefaultStyle.fillOpacity,
          radius: layerStyle.radius || systemDefaultStyle.radius
        }

        // 处理线型样式
        if (layerStyle.dashArray) {
          style.dashArray = layerStyle.dashArray
        }

        // 处理线端点和连接样式
        if (layerStyle.lineCap) {
          style.lineCap = layerStyle.lineCap
        }
        if (layerStyle.lineJoin) {
          style.lineJoin = layerStyle.lineJoin
        }

        // 处理填充
        if (layerStyle.fill !== undefined) {
          if (!layerStyle.fill) {
            style.fillOpacity = 0
          }
        }

        // 处理图层可见性
        if (layerStyle.visible === false) {
          style.opacity = 0
          style.fillOpacity = 0
        }

        return style
      }
    }
    
    // 监听sceneId变化
    watch(() => props.sceneId, (newValue, oldValue) => {
      if (newValue && newValue !== oldValue) {
        // 确保地图已经初始化并加载完成
        if (map.value && map.value._loaded) {
          loadScene(newValue)
        } else {
          console.warn('地图尚未初始化完成，等待初始化后再加载场景')
          // 等待地图初始化完成后再加载场景
          const loadSceneWhenReady = () => {
            if (map.value && map.value._loaded) {
              loadScene(newValue)
            } else {
              // 如果地图尚未加载完成，等待一段时间后再次检查
              setTimeout(loadSceneWhenReady, 100)
            }
          }
          setTimeout(loadSceneWhenReady, 200)
        }
      }
    })
    
    
    onMounted(() => {
      nextTick(() => {
        // 初始化地图
        initMap()
        
        // 使用地图的 'load' 事件确保地图完全初始化后再加载场景
        const sceneId = props.sceneId || route.query.scene_id
        if (sceneId && map.value) {
          // 使用一次性事件监听器确保地图准备就绪后加载场景
          const loadSceneWhenReady = () => {
            if (map.value && map.value._loaded) {
              loadScene(sceneId)
            } else {
              // 如果地图尚未加载完成，等待一段时间后再次检查
              setTimeout(loadSceneWhenReady, 100)
            }
          }
          
          // 延迟执行以确保地图有足够时间初始化
          setTimeout(loadSceneWhenReady, 500)
        }
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
      bringLayerToTop,
      refreshMartinLayerStyle,
      updateMvtLayerStyles,
      mouseCoordinates,
      currentBaseMapAttribution,
      initializeCoordinateTracking,
      updateBaseMapAttribution,
      refreshing,
      refreshAllLayers,
      refreshLayersOrder
    }
  },
  expose: ['showStyleDialog', 'showAddLayerDialog', 'toggleLayerVisibility', 'map', 'bringLayerToTop', 'setActiveLayer', 'currentActiveLayer', 'refreshMartinLayerStyle', 'updateMvtLayerStyles']
}
</script>

<style scoped>
.map-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
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

/* 搜索表单控件宽度设置 */
.search-form .el-form-item {
  margin-bottom: 0;
  margin-right: 20px;
}

.search-form .el-form-item:last-child {
  margin-right: 0;
}

.search-form .el-form-item .el-form-item__label {
  font-weight: 500;
  color: #606266;
  width: auto !important;
  margin-right: 8px;
}

.search-form .el-select {
  width: 160px;
  min-width: 140px;
}

/* 服务类型选择框稍微宽一点 */
.search-form .el-form-item:first-child .el-select {
  width: 180px;
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

/* 自定义弹窗样式 */
:global(.no-close-button-popup) {
  margin: 0;
  padding: 0;
}

:global(.no-close-button-popup .leaflet-popup-content-wrapper) {
  border-radius: 8px;
  box-shadow: 0 3px 14px rgba(0,0,0,0.2);
}

:global(.no-close-button-popup .leaflet-popup-content) {
  margin: 13px 19px;
  line-height: 1.4;
}

:global(.no-close-button-popup .leaflet-popup-tip-container) {
  margin: 0 auto;
  width: 40px;
  height: 20px;
  position: relative;
  overflow: hidden;
}

.loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
}

.loading-placeholder .el-icon {
  margin-bottom: 10px;
}

.dialog-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.dialog-loading .el-icon {
  margin-bottom: 10px;
  font-size: 24px;
}

/* 地图控件组样式 */
.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.refresh-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid #67c23a;
}

.refresh-button:hover {
  background-color: #5daf34;
  border-color: #5daf34;
}

.refresh-button.is-loading {
  background-color: #85ce61;
  border-color: #85ce61;
}

/* 坐标信息样式 - 匹配Leaflet自带版权信息的样式 */
.coordinate-info {
  position: absolute;
  bottom: 0px; /* 与Leaflet版权信息同一位置 */
  right: 150px; /* 增加距离，确保不遮挡版权信息 */
  z-index: 999; /* 降低层级，确保不遮挡Leaflet版权 */
  background: rgba(255, 255, 255, 0.8); /* 匹配Leaflet版权的透明度 */
  padding: 0px 5px; /* 匹配Leaflet版权的内边距 */
  font-size: 11px; /* 匹配Leaflet版权的字体大小 */
  font-family: 'Helvetica Neue', Arial, Helvetica, sans-serif; /* 匹配Leaflet默认字体 */
  line-height: 1.5; /* 匹配Leaflet版权的行高 */
  color: #333; /* 匹配Leaflet版权的文字颜色 */
  white-space: nowrap;
  pointer-events: none; /* 允许鼠标事件穿透到地图 */
  border-radius: 0; /* 移除圆角，匹配Leaflet样式 */
  box-shadow: none; /* 移除阴影，匹配Leaflet样式 */
  border: none; /* 移除边框，匹配Leaflet样式 */
}

.coordinate-text {
  /* 继承父容器的样式，与Leaflet版权信息保持一致 */
}



/* 响应式调整 */
@media (max-width: 768px) {
  .coordinate-info {
    bottom: 0px; /* 移动端与版权信息同一位置 */
    right: 60px; /* 移动端版权信息较短，调整位置 */
    padding: 0px 3px; /* 移动端保持相同的内边距比例 */
    font-size: 10px; /* 移动端稍微减小字体 */
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-form {
    padding: 12px;
  }
  
  .search-form .el-form-item {
    margin-right: 0;
    margin-bottom: 12px;
    width: 100%;
  }
  
  .search-form .el-form-item:last-child {
    margin-bottom: 0;
  }
  
  .search-form .el-select {
    width: 100% !important;
    max-width: 300px;
  }
}
</style>
