<template>
  <div class="map-viewer">
    <div class="map-container" ref="mapContainer"></div>
    
    <!-- 高德底图切换器 -->
    <BaseMapSwitcher 
      v-if="map" 
      :map="map" 
      @base-map-changed="onBaseMapChanged" 
    />
    
    
    
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
                <el-tag v-if="scope.row.geoserver_service && scope.row.geoserver_service.is_published" type="success" size="small">
                  GeoServer已发布
                </el-tag>
                <el-tag v-if="scope.row.martin_service && scope.row.martin_service.is_published" type="primary" size="small">
                  Martin已发布
                </el-tag>
                <el-tag v-if="!hasAnyPublishedService(scope.row)" type="warning" size="small">
                  未发布
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <div class="layer-actions">
                <el-button 
                  v-if="scope.row.geoserver_service && scope.row.geoserver_service.is_published"
                  size="small" 
                  type="primary" 
                  @click="addLayerToScene(scope.row, 'geoserver')"
                  :disabled="isLayerInScene(scope.row.id, 'geoserver')"
                >
                  {{ isLayerInScene(scope.row.id, 'geoserver') ? '已添加' : '添加GeoServer' }}
                </el-button>
                <el-button 
                  v-if="scope.row.martin_service && scope.row.martin_service.is_published"
                  size="small" 
                  type="success" 
                  @click="addLayerToScene(scope.row, 'martin')"
                  :disabled="isLayerInScene(scope.row.id, 'martin')"
                >
                  {{ isLayerInScene(scope.row.id, 'martin') ? '已添加' : '添加Martin' }}
                </el-button>
                <div v-if="!hasAnyPublishedService(scope.row)" class="no-service">
                  <span class="no-service-text">无可用服务</span>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    
    <!-- 图层样式设置对话框 -->
    <el-dialog title="图层样式设置" v-model="styleDialogVisible" width="800px" :close-on-click-modal="false">
      <div class="style-dialog-content" v-if="currentStyleLayer">
        <!-- 选项卡 -->
        <el-tabs v-model="activeStyleTab">
          <!-- 基础样式选项卡 -->
          <el-tab-pane label="基础样式" name="basic">
            <el-form :model="styleForm" label-width="100px">
              <template v-if="isVectorLayer">
                <!-- 矢量图层样式设置 -->
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
                  <el-form-item label="线型">
                    <el-select v-model="styleForm.line.style">
                      <el-option label="实线" value="solid"></el-option>
                      <el-option label="虚线" value="dashed"></el-option>
                      <el-option label="点线" value="dotted"></el-option>
                    </el-select>
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
                  <el-form-item label="边框宽度">
                    <el-slider v-model="styleForm.polygon.outlineWidth" :min="0" :max="5" :step="0.5"></el-slider>
                  </el-form-item>
                  <el-form-item label="透明度">
                    <el-slider v-model="styleForm.polygon.opacity" :min="0" :max="1" :step="0.1"></el-slider>
                  </el-form-item>
                </template>
              </template>
              <template v-else>
                <!-- 栅格图层样式设置 -->
                <el-form-item label="透明度">
                  <el-slider v-model="styleForm.raster.opacity" :min="0" :max="1" :step="0.1"></el-slider>
                </el-form-item>
                <template v-if="currentStyleLayer.file_type === 'dem'">
                  <el-form-item label="色带">
                    <el-select v-model="styleForm.raster.palette">
                      <el-option label="高程" value="elevation"></el-option>
                      <el-option label="彩虹" value="rainbow"></el-option>
                      <el-option label="地形" value="terrain"></el-option>
                      <el-option label="灰度" value="grayscale"></el-option>
                    </el-select>
                  </el-form-item>
                </template>
              </template>
            </el-form>
          </el-tab-pane>

          <!-- Martin(DXF)样式选项卡 - 只有Martin服务的DXF图层才显示 -->
          <el-tab-pane 
            v-if="isDxfMartinLayer" 
            label="Martin(DXF)" 
            name="dxf"
          >
            <DxfStyleEditor 
              v-if="currentStyleLayer && currentStyleLayer.martin_service_id"
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
          <el-button 
            v-if="activeStyleTab === 'basic'" 
            type="primary" 
            @click="applyStyle"
          >
            应用样式
          </el-button>
          <el-button 
            v-if="activeStyleTab === 'dxf' && isDxfMartinLayer" 
            type="primary" 
            @click="applyAndSaveDxfStyles"
            :loading="savingDxfStyles"
          >
            保存样式到数据库
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import gisApi from '@/api/gis'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
// 导入VectorGrid插件
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

// 🌍 定义EPSG:404000坐标系
// 参考: https://github.com/openlayers/openlayers/issues/11958
// 这是一个自定义坐标系，可能是都江堰地区的专用投影坐标系
if (typeof window !== 'undefined' && window.proj4) {
  // 如果有proj4库，定义投影参数
  // 注意：这里需要根据实际的投影参数进行调整
  // 这是一个示例定义，实际参数需要从GeoServer或相关文档获取
  window.proj4.defs('EPSG:404000', '+proj=tmerc +lat_0=0 +lon_0=114 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs')
  
  console.log('✅ EPSG:404000坐标系已定义')
} else {
  console.warn('⚠️ proj4库未加载，EPSG:404000坐标系可能无法正确处理')
}

export default {
  name: 'MapViewer',
  components: {
    BaseMapSwitcher,
    DxfStyleEditor
  },
  props: {
    sceneId: {
      type: [Number, String],
      default: null
    },
    readonly: {
      type: Boolean,
      default: false
    }
  },
  emits: ['layerAdded', 'layer-selected'],
  setup(props, { emit }) {
    const route = useRoute()
    const mapContainer = ref(null)
    const map = ref(null)
    const mapLayers = ref({}) // GeoServer图层
    const mvtLayers = ref({}) // Martin MVT图层
    const currentScene = ref(null)
    const layersList = ref([])
    const currentActiveLayer = ref(null) // 当前激活的图层
    
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
      line: { width: 2, color: '#0000FF', style: 'solid' },
      polygon: { fillColor: '#00FF00', outlineColor: '#000000', outlineWidth: 1, opacity: 0.5 },
      raster: { opacity: 1, palette: 'elevation' }
    })
    
    const disciplines = ref([
      '综合', '测绘', '地勘', '水文', '水工', '施工',
      '建筑', '金结', '电一', '电二', '消防', '暖通',
      '给排水', '环水', '移民', '其他'
    ])
    const fileTypes = ref(['shp', 'dem', 'dom', 'dwg', 'dxf', 'geojson'])
    
    // 判断图层类型
    const isVectorLayer = computed(() => {
      if (!currentStyleLayer.value) return false
      return ['shp', 'dwg', 'dxf', 'geojson'].includes(currentStyleLayer.value.file_type)
    })
    
    const hasPointGeometry = computed(() => isVectorLayer.value)
    const hasLineGeometry = computed(() => isVectorLayer.value)
    const hasPolygonGeometry = computed(() => isVectorLayer.value)

    // 判断是否为DXF Martin图层
    const isDxfMartinLayer = computed(() => {
      if (!currentStyleLayer.value) return false
      return currentStyleLayer.value.service_type === 'martin' && 
             currentStyleLayer.value.file_type === 'dxf' &&
             currentStyleLayer.value.martin_service_id
    })
    
    // 初始化地图
    const initMap = () => {
      try {
        // 如果已经有地图实例，先安全地销毁它
        if (map.value) {
          try {
            map.value.off() // 移除所有事件监听器
            map.value.remove() // 销毁地图实例
          } catch (destroyError) {
            console.warn('销毁旧地图实例时出现警告:', destroyError)
          } finally {
            map.value = null
          }
        }
        
        // 确保容器存在且已挂载到DOM
        if (!mapContainer.value) {
          console.error('地图容器引用不存在')
          ElMessage.error('地图容器不存在')
          return
        }
        
        // 检查容器是否在DOM中
        if (!mapContainer.value.parentNode) {
          console.error('地图容器未挂载到DOM')
          ElMessage.error('地图容器未正确挂载')
          return
        }
        
        // 清理容器内容，确保干净的状态
        if (mapContainer.value.innerHTML.trim() !== '') {
          mapContainer.value.innerHTML = ''
        }
        
        // 统一使用EPSG:3857坐标系 - 这是Web地图的标准配置
        map.value = L.map(mapContainer.value, {
          center: [35.0, 105.0],
          zoom: 5,
          maxZoom: 22,
          minZoom: 1,
          zoomControl: true,
          attributionControl: true,
          crs: L.CRS.EPSG3857, // Web Mercator坐标系，与网络地图服务兼容
          zoomSnap: 0.25, // 允许更精细的缩放控制
          zoomDelta: 0.25, // 缩放步长
          wheelPxPerZoomLevel: 120, // 鼠标滚轮缩放速度
          preferCanvas: true, // 在支持的情况下使用Canvas渲染，提高性能
          // 添加错误恢复选项
          fadeAnimation: false, // 禁用可能导致DOM访问问题的动画
          zoomAnimation: true,
          markerZoomAnimation: true
        })
        
        // 验证地图实例创建成功
        if (!map.value) {
          throw new Error('Leaflet地图实例创建失败')
        }
        
        // 添加错误处理的事件监听器
        map.value.on('error', (e) => {
          console.error('Leaflet地图错误:', e)
          ElMessage.error('地图运行时错误: ' + (e.message || '未知错误'))
        })
        
        // 添加缩放事件处理（带错误保护）
        map.value.on("zoom", function () {
          try {
            if (map.value && map.value.closePopup) {
              map.value.closePopup()
            }
          } catch (zoomError) {
            console.warn('缩放事件处理时出现警告:', zoomError)
          }
        })
        
        // 添加底图
        const baseLayer = createMapLayerWithFallback()
        if (baseLayer) {
          baseLayer.addTo(map.value)
        }
        
        // 添加比例尺
        L.control.scale({ imperial: false }).addTo(map.value)
        
        // 延迟刷新地图尺寸，确保DOM完全准备就绪
        setTimeout(() => {
          try {
            if (map.value && map.value.getContainer() && map.value.getContainer().parentNode) {
              map.value.invalidateSize()
              console.log('✅ 地图尺寸已刷新')
            }
          } catch (resizeError) {
            console.warn('刷新地图尺寸时出现警告:', resizeError)
          }
        }, 100)
        
        // ElMessage.success('地图初始化完成') // 移除弹窗，避免干扰
        console.log('✅ Leaflet地图初始化成功')
        
      } catch (error) {
        console.error('❌ 地图初始化失败:', error)
        ElMessage.error('地图初始化失败: ' + error.message)
        
        // 清理失败的状态
        if (map.value) {
          try {
            map.value.remove()
          } catch (cleanupError) {
            console.warn('清理失败地图实例时出现警告:', cleanupError)
          } finally {
            map.value = null
          }
        }
      }
    }
    
    // 加载场景
    const loadScene = async (sceneId) => {
      try {
        console.log('🚀 开始加载场景:', sceneId)
        
        // 验证地图对象是否已初始化
        if (!map.value) {
          console.warn('⚠️ 地图对象未初始化，等待地图初始化完成...')
          // 等待地图初始化
          let retryCount = 0
          const maxRetries = 10
          while (!map.value && retryCount < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 100))
            retryCount++
          }
          
          if (!map.value) {
            console.error('❌ 地图初始化超时，无法加载场景')
            ElMessage.error('地图初始化失败，无法加载场景')
            return
          }
        }
        
        const response = await gisApi.getScene(sceneId)
        currentScene.value = response.scene
        layersList.value = response.layers
        
        console.log('📋 场景信息:', currentScene.value)
        console.log('📊 图层列表:', layersList.value)
        
        // 输出所有MVT和TileJSON URL格式以便调试
        layersList.value.forEach((layer, index) => {
          if (layer.service_type === 'martin') {
            console.log(`🔍 Martin图层${index + 1} [${layer.layer_name}]:`)
            console.log('  - MVT URL:', layer.mvt_url)
            console.log('  - TileJSON URL:', layer.tilejson_url)
            console.log('  - Martin Service ID:', layer.martin_service_id)
          }
        })
        
        clearAllLayers()
        
        if (!layersList.value || layersList.value.length === 0) {
          ElMessage.info('当前场景没有图层')
          return
        }
        
        // 加载场景图层
        for (const layer of layersList.value) {
          console.log(`🔄 准备加载图层: ${layer.layer_name} (${layer.service_type})`)
          if (layer.service_type === 'martin') {
            await addMartinLayer(layer)
          } else {
            await addGeoServerLayer(layer)
          }
        }
        
        console.log('✅ 场景加载完成')
      } catch (error) {
        console.error('❌ 加载场景失败:', error)
        ElMessage.error('加载场景失败: ' + error.message)
      }
    }
    
    // 添加Martin图层 - 改进版本
    const addMartinLayer = async (layer) => {
      console.log('🔧 开始添加Martin图层:', layer)
      
      try {
        // 首先验证地图对象是否已初始化
        if (!map.value) {
          console.error('❌ 地图对象未初始化，无法添加Martin图层:', layer.layer_name)
          ElMessage.error(`无法添加图层"${layer.layer_name}"：地图未初始化`)
          return
        }
        
        if (!layer.mvt_url) {
          console.warn('Martin图层缺少MVT URL:', layer)
          ElMessage.warning(`Martin图层"${layer.layer_name}"缺少MVT服务URL`)
          return
        }
        
        if (!checkMVTSupport()) {
          console.error('浏览器不支持MVT瓦片')
          ElMessage.error('浏览器不支持MVT瓦片')
          return
        }
        
        // 处理URL格式 - 修复代理问题
        let mvtUrl = layer.mvt_url
        
        console.log('🔍 原始MVT URL:', mvtUrl)
        
        // 检查是否需要代理
        if (mvtUrl.includes('localhost:3000') ) {
          // 正确解析Martin MVT URL格式
          // 例如: http://localhost:3000/table_name/{z}/{x}/{y}
          const urlPattern = /^https?:\/\/[^/]+\/([^/{]+)/
          const match = mvtUrl.match(urlPattern)
          
          if (match && match[1]) {
            const tableName = match[1]
            // 临时使用直接URL而不是代理路径，不添加.pbf后缀
            mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
            console.log('🔄 表名:', tableName)
            console.log('🔄 直接使用Martin URL:', mvtUrl)
          } else {
            console.warn('⚠️ 无法解析MVT URL格式:', mvtUrl)
            // 尝试备用解析方法
            const urlParts = mvtUrl.split('/')
            let tableName = 'unknown'
            for (let i = urlParts.length - 1; i >= 0; i--) {
              if (urlParts[i] && !urlParts[i].includes('{') && !urlParts[i].includes('.pbf')) {
                tableName = urlParts[i]
                break
              }
            }
            mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
            console.log('🔄 备用解析 - 表名:', tableName)
            console.log('🔄 备用解析 - 直接URL:', mvtUrl)
          }
        } else {
          // 非本地服务，移除.pbf后缀（如果存在）
          if (mvtUrl.endsWith('.pbf')) {
            mvtUrl = mvtUrl.replace('.pbf', '')
            console.log('🔧 移除远程MVT URL的.pbf后缀:', mvtUrl)
          }
        }
        
        console.log('📍 MVT URL:', mvtUrl)
        
        // 获取图层配置信息
        let vectorTileOptions = {
          rendererFactory: L.canvas.tile,
          vectorTileLayerStyles: {},
          interactive: true,
          maxNativeZoom: 20, // 提高到20级以获得更清晰的瓦片
          maxZoom: 22,
          minZoom: 1,
          zoomOffset: 0,
          detectRetina: true, // 启用高DPI屏幕支持
          attribution: `MVT: ${layer.layer_name}`,
          pane: 'overlayPane'
        }
        
        // 如果有TileJSON URL，获取图层信息
        if (layer.tilejson_url) {
          try {
            console.log('🔍 获取TileJSON:', layer.tilejson_url)
            
            // 处理TileJSON代理路径
            let tilejsonUrl = layer.tilejson_url
            console.log('🔍 原始TileJSON URL:', tilejsonUrl)
            
            if (tilejsonUrl.includes('localhost:3000')) {
              // Martin的TileJSON格式: http://localhost:3000/table_name （不需要/tilejson.json后缀）
              const urlPattern = /^https?:\/\/[^/]+\/([^/]+)(?:\/tilejson\.json)?$/
              const match = tilejsonUrl.match(urlPattern)
              
              if (match && match[1]) {
                const tableName = match[1]
                // 临时使用直接URL而不是代理路径
                tilejsonUrl = `http://localhost:3000/${tableName}`
                console.log('🔄 TileJSON表名:', tableName)
                console.log('🔄 直接使用Martin服务URL:', tilejsonUrl)
              } else {
                console.warn('⚠️ 无法解析TileJSON URL格式:', tilejsonUrl)
                // 备用解析 - 先移除协议和域名部分，再提取表名
                const pathOnly = tilejsonUrl.replace(/^https?:\/\/[^/]+\//, '').replace('/tilejson.json', '')
                const tableName = pathOnly || 'unknown'
                tilejsonUrl = `http://localhost:3000/${tableName}`
                console.log('🔄 TileJSON备用解析 - 表名:', tableName)
                console.log('🔄 直接使用Martin服务URL:', tilejsonUrl)
              }
            } else {
              console.log('✅ 使用原始TileJSON URL（非本地服务）:', tilejsonUrl)
            }
            
            // 测试Martin服务连接
            console.log('🧪 测试Martin服务连接...')
            console.log('🧪 即将请求TileJSON:', tilejsonUrl)
            
            const response = await fetch(tilejsonUrl)
            if (response.ok) {
              const tilejsonData = await response.json()
              console.log('📊 TileJSON数据:', tilejsonData)
              
              // 更新MVT URL
              if (tilejsonData.tiles && tilejsonData.tiles.length > 0) {
                mvtUrl = tilejsonData.tiles[0]
                
                // 移除.pbf后缀（如果存在），因为Leaflet VectorGrid不需要
                if (mvtUrl.endsWith('.pbf')) {
                  mvtUrl = mvtUrl.replace('.pbf', '')
                  console.log('🔧 移除MVT URL的.pbf后缀:', mvtUrl)
                }
                
                // 如果是本地服务，转换为直接URL
                if (mvtUrl.includes('localhost:3000') || mvtUrl.includes('localhost:8084')) {
                  const urlPattern = /^https?:\/\/[^/]+\/([^/{]+)/
                  const match = mvtUrl.match(urlPattern)
                  
                  if (match && match[1]) {
                    const tableName = match[1]
                    // 临时使用直接URL，不添加.pbf后缀
                    mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
                    console.log('🔄 TileJSON中的表名:', tableName)
                    console.log('🔄 直接使用Martin瓦片URL:', mvtUrl)
                  }
                }
                
                console.log('🔄 从TileJSON更新MVT URL:', mvtUrl)
              }
              
              // 获取图层名称
              let layerNames = ['default']
              if (tilejsonData.vector_layers && Array.isArray(tilejsonData.vector_layers)) {
                layerNames = tilejsonData.vector_layers.map(layer => layer.id)
              }
              
              console.log('🎯 检测到的图层名称:', layerNames)
              
              // 创建基于DXF样式配置的样式函数
              const createDxfStyleFunction = () => {
                // 获取默认DXF样式配置
                const defaultDxfStyles = defaultDxfStylesConfig.defaultDxfStyles
                console.log('🎨 加载默认DXF样式配置:', Object.keys(defaultDxfStyles))
                
                return function(properties, zoom) {
                  const layerName = properties.layer || properties.Layer || 'default'
                  
                  // 获取预定义的图层样式
                  const layerStyle = defaultDxfStyles[layerName]
                  
                  // 基础样式配置
                  let style = {
                    weight: 2,
                    color: '#0066cc',
                    opacity: 0.8,
                    fillColor: '#66ccff',
                    fillOpacity: 0.3,
                    radius: 4,
                    fill: true
                  }
                  
                  // 如果找到预定义样式，使用它
                  if (layerStyle) {
                    style = {
                      weight: layerStyle.weight || 2,
                      color: layerStyle.color || '#0066cc',
                      opacity: layerStyle.opacity || 0.8,
                      fillColor: layerStyle.fillColor || layerStyle.color || '#66ccff',
                      fillOpacity: layerStyle.fillOpacity || 0.3,
                      radius: layerStyle.radius || 4,
                      fill: layerStyle.fill !== false,
                      dashArray: layerStyle.dashArray || null,
                      lineCap: layerStyle.lineCap || 'round',
                      lineJoin: layerStyle.lineJoin || 'round'
                    }
                    
                    console.log(`🎨 图层 "${layerName}" 使用预定义样式:`, layerStyle.name, style.color)
                  } else {
                    console.log(`🎨 图层 "${layerName}" 使用默认样式`)
                  }
                  
                  // 根据缩放级别调整样式
                  if (zoom < 10) {
                    style.weight = Math.max(style.weight - 0.5, 0.5)
                    style.opacity = Math.max(style.opacity - 0.2, 0.3)
                    if (style.radius) style.radius = Math.max(2, style.radius - 1)
                  } else if (zoom > 15) {
                    style.weight = style.weight + 0.5
                    style.opacity = Math.min(style.opacity + 0.1, 1)
                    if (style.radius) style.radius = style.radius + 1
                  }
                  
                  // 特殊图层处理 - 根据可见性设置
                  if (layerStyle && layerStyle.visible === false) {
                    style.opacity = 0
                    style.fillOpacity = 0
                  }
                  
                  // 特殊缩放级别处理
                  if (layerName === 'sqx' && zoom < 14) {
                    style.opacity = 0  // 1米等高线在小比例尺下隐藏
                  }
                  
                  if (layerName === 'jqx' && zoom < 12) {
                    style.opacity = Math.max(style.opacity - 0.3, 0.2)  // 5米等高线淡化
                  }
                  
                  return style
                }
              }
              
              // 检查是否为DXF文件类型
              const isDxfLayer = layer.file_type === 'dxf'
              
              // 创建样式函数
              const styleFunction = isDxfLayer 
                ? createDxfStyleFunction(layer.file_type)
                : (properties, zoom) => {
                    // 非DXF图层使用默认样式
                    let style = {
                      weight: 2,
                      color: '#0066cc',
                      opacity: 0.8,
                      fillColor: '#66ccff',
                      fillOpacity: 0.3,
                      radius: 4
                    }
                    
                    // 根据缩放级别调整样式
                    if (zoom < 10) {
                      style.weight = Math.max(style.weight - 0.5, 0.5)
                      style.opacity = Math.max(style.opacity - 0.2, 0.3)
                      if (style.radius) style.radius = Math.max(2, style.radius - 1)
                    } else if (zoom > 15) {
                      style.weight = style.weight + 0.5
                      style.opacity = Math.min(style.opacity + 0.1, 1)
                      if (style.radius) style.radius = style.radius + 1
                    }
                    
                    return style
                  }
              
              // 为每个图层设置样式
                layerNames.forEach(layerName => {
                  vectorTileOptions.vectorTileLayerStyles[layerName] = styleFunction
                })
                
              // 设置边界
              if (tilejsonData.bounds) {
                vectorTileOptions.bounds = L.latLngBounds(
                  [tilejsonData.bounds[1], tilejsonData.bounds[0]],
                  [tilejsonData.bounds[3], tilejsonData.bounds[2]]
                )
              }
              
            } else {
              console.warn('TileJSON获取失败，使用默认配置')
              vectorTileOptions.vectorTileLayerStyles['default'] = () => ({
                weight: 2,
                color: '#0066cc',
                opacity: 0.8,
                fillColor: '#66ccff',
                fillOpacity: 0.3
              })
            }
          } catch (error) {
            console.warn('TileJSON解析失败，使用默认配置:', error)
            vectorTileOptions.vectorTileLayerStyles['default'] = () => ({
              weight: 2,
              color: '#0066cc',
              opacity: 0.8,
              fillColor: '#66ccff',
              fillOpacity: 0.3
            })
          }
        } else {
          // 没有TileJSON，使用默认配置
          vectorTileOptions.vectorTileLayerStyles['default'] = () => ({
                      weight: 2,
                      color: '#0066cc',
                      opacity: 0.8,
                      fillColor: '#66ccff',
            fillOpacity: 0.3
          })
        }
        
        console.log('🔧 VectorGrid配置:', vectorTileOptions)
        
        // 创建MVT图层
        const mvtLayer = L.vectorGrid.protobuf(mvtUrl, vectorTileOptions)
        
        if (!mvtLayer) {
          throw new Error('VectorGrid图层创建失败')
        }
        
        // 为MVT图层添加事件监听 - 使用更安全的事件处理方式
        mvtLayer.on('loading', () => {
          console.log(`🔄 图层 "${layer.layer_name}" 开始加载`)
        })
        
        mvtLayer.on('load', () => {
          console.log(`✅ 图层 "${layer.layer_name}" 加载完成`)
          // ElMessage.success(`Martin图层"${layer.layer_name}"加载成功`) // 移除弹窗，避免干扰
        })
        
        mvtLayer.on('tileerror', (e) => {
          console.error(`❌ 瓦片加载错误 "${layer.layer_name}":`, e)
          console.log('错误详情:', e.error)
          ElMessage.error(`图层"${layer.layer_name}"瓦片加载失败`)
        })
        
        // 使用click事件而不是mouseover来避免坐标错误问题
        mvtLayer.on('click', (e) => {
          console.log('MVT图层点击事件:', e)
          
          // 基本验证
          if (!e || !e.layer || !e.layer.properties) {
            console.warn('MVT点击事件数据无效:', e)
            return
          }
          
          // 设置为当前活动图层
          currentActiveLayer.value = layer
          emit('layer-selected', layer)
          
          // 只有启用弹窗的图层才显示弹窗
          if (mvtLayer._popupEnabled !== false) {
            const properties = e.layer.properties
            const content = Object.entries(properties)
              .filter(([, value]) => value != null && value !== 'NULL' && value !== '')
              .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
              .join('<br/>')
            
            // 验证坐标有效性
            if (e.latlng && typeof e.latlng.lat === 'number' && typeof e.latlng.lng === 'number') {
              try {
                L.popup({
                  className: 'mvt-popup-click',
                  maxWidth: 300,
                  offset: [0, -10],
                  closeButton: true,
                  autoClose: false,
                  closeOnEscapeKey: true
                })
                  .setContent(`
                    <div style="max-width: 300px;">
                      <h4 style="margin: 0 0 10px 0; color: #333;">要素属性 - ${layer.layer_name}</h4>
                      ${content || '无属性信息'}
                    </div>
                  `)
                  .setLatLng(e.latlng)
                  .openOn(map.value)
              } catch (popupError) {
                console.warn('创建MVT弹窗失败:', popupError)
              }
            } else {
              console.warn('MVT点击事件坐标无效:', e.latlng)
            }
          }
        })
        
        // 标记事件已绑定
        mvtLayer._popupEventsBound = true
        mvtLayer._popupEnabled = true // 默认启用弹窗
        
        mvtLayers.value[layer.id] = mvtLayer
        
        // 根据可见性添加到地图
        if (layer.visibility === true) {
          mvtLayer.addTo(map.value)
        }
        
        console.log('🎉 Martin图层添加完成')
      } catch (error) {
        console.error('❌ 添加Martin图层失败:', error)
        ElMessage.error(`添加Martin图层"${layer.layer_name}"失败: ${error.message}`)
      }
    }
    
    // 添加GeoServer图层 - 基于数据库坐标系信息的智能加载
    const addGeoServerLayer = async (layer) => {
      try {
        // 首先验证地图对象是否已初始化
        if (!map.value) {
          console.error('❌ 地图对象未初始化，无法添加图层:', layer.layer_name)
          ElMessage.error(`无法添加图层"${layer.layer_name}"：地图未初始化`)
          return
        }
        
        if (!layer.wms_url || !layer.geoserver_layer) {
          ElMessage.warning(`图层"${layer.layer_name}"尚未发布到GeoServer`)
          return
        }
        
        console.log('🔍 开始智能加载GeoServer图层:', layer)
        
        // 🎯 Step 1: 从数据库获取图层的坐标系信息
        console.log('📡 正在从数据库获取坐标系信息...')
        let crsInfo = null
        let selectedCRS = 'EPSG:3857' // 默认坐标系
        let wmsVersion = '1.1.1' // 默认版本
        let centerCoords = null
        let zoomLevel = 10
        
        try {
          const crsResponse = await gisApi.getLayerCRSInfo(layer.id)
          if (crsResponse && crsResponse.success && crsResponse.data) {
            crsInfo = crsResponse.data
            selectedCRS = crsInfo.srs || 'EPSG:3857'
            wmsVersion = crsInfo.wms_version || '1.1.1'
            centerCoords = crsInfo.center_coords
            zoomLevel = crsInfo.zoom_level || 10
            
            console.log('✅ 成功获取坐标系信息:', {
              srs: selectedCRS,
              version: wmsVersion,
              found_in_db: crsInfo.found_in_db,
              center: centerCoords,
              zoom: zoomLevel
            })
            
            if (crsInfo.found_in_db) {
              console.log(`✅ 已从数据库获取图层"${layer.layer_name}"的坐标系信息: ${selectedCRS}`)
              // ElMessage.success({
              //   message: `已从数据库获取图层"${layer.layer_name}"的坐标系信息: ${selectedCRS}`,
              //   duration: 3000
              // }) // 移除弹窗，避免干扰
            } else {
              console.log(`ℹ️ 图层"${layer.layer_name}"使用默认坐标系配置: ${selectedCRS}`)
              // ElMessage.info({
              //   message: `图层"${layer.layer_name}"使用默认坐标系配置: ${selectedCRS}`,
              //   duration: 3000
              // }) // 移除弹窗，避免干扰
            }
          } else {
            console.warn('⚠️ 获取坐标系信息失败，使用智能检测')
            throw new Error('API返回数据格式错误')
          }
        } catch (crsError) {
          console.warn('⚠️ 无法获取数据库坐标系信息，回退到智能检测:', crsError.message)
          
          
        }
        
        // 修复URL处理 - 清理所有参数，只保留基础URL
        let wmsUrl = layer.wms_url
        
        console.log('🔍 原始WMS URL:', wmsUrl)
        
        // 🔧 重要修复：处理包含GetCapabilities的错误URL格式
        if (wmsUrl.includes('GetCapabilities')) {
          console.warn('⚠️ 检测到URL包含GetCapabilities，这是错误的格式，正在修复...')
          // 移除从?开始的所有参数
          if (wmsUrl.includes('?')) {
            wmsUrl = wmsUrl.split('?')[0]
          }
          console.log('🔧 移除GetCapabilities参数后:', wmsUrl)
        } else if (wmsUrl.includes('?')) {
          // 移除其他所有参数，只保留基础URL
          wmsUrl = wmsUrl.split('?')[0]
          console.log('🔧 移除其他参数后:', wmsUrl)
        }
        
        // 如果URL包含localhost:8083，使用代理路径
        if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
          wmsUrl = '/geoserver/wms'
          console.log('🔄 使用GeoServer代理路径:', wmsUrl)
        }
        
        // 确保URL不以?结尾
        wmsUrl = wmsUrl.replace(/\?$/, '')
        
        console.log('📍 清理后的WMS URL:', wmsUrl)
        console.log('📍 图层名称:', layer.geoserver_layer)
        
        // 使用原始的图层名称，不进行修改
        let layerName = layer.geoserver_layer
        
        // 🔧 重要修复：确保图层名称包含工作空间前缀
        if (layerName && !layerName.includes(':')) {
          // 如果图层名称不包含工作空间前缀，添加默认的shpservice前缀
          layerName = `shpservice:${layerName}`
          console.log('🔧 添加工作空间前缀后的图层名称:', layerName)
        } else {
          console.log('✅ 图层名称已包含工作空间前缀或为空:', layerName)
        }
        
        console.log('📍 最终使用的图层名称:', layerName)
        console.log(`🌍 确定的坐标系: ${selectedCRS}`)
        console.log(`🔧 WMS版本: ${wmsVersion}`)
        
        // 🧪 测试WMS URL是否可用
        console.log('🧪 测试WMS服务可用性...')
        const testParams = new URLSearchParams({
          service: 'WMS',
          version: wmsVersion,
          request: 'GetMap',
          layers: layerName,
          styles: '',
          format: 'image/png',
          transparent: 'true',
          width: '256',
          height: '256',
          })
        
        const testUrl = `${wmsUrl}?${testParams.toString()}`
        console.log('🧪 测试URL:', testUrl)
        
        // 异步测试URL（不阻塞图层创建）
        setTimeout(async () => {
          try {
            const response = await fetch(testUrl)
            const contentType = response.headers.get('content-type')
            if (response.ok && contentType && contentType.includes('image')) {
              console.log('✅ WMS URL测试成功，图层应该可以正常显示')
            } else {
              console.warn('⚠️ WMS URL测试失败:', response.status, contentType)
              const text = await response.text()
              console.log('错误响应:', text.substring(0, 300))
            }
          } catch (error) {
            console.warn('⚠️ WMS URL测试异常:', error.message)
          }
        }, 100)
        
        // 🎯 Step 2: 根据坐标系信息创建WMS图层
        const wmsLayer = L.tileLayer.wms(wmsUrl, {
          layers: layerName,
          format: 'image/png',
          transparent: true,
          version: wmsVersion,
          attribution: `GeoServer (${selectedCRS})`,
          // 🔧 关键修复：使用数据库中的真实坐标系
          srs: selectedCRS,
          // 添加容错参数
          exceptions: 'application/vnd.ogc.se_inimage',
          // 提高图像质量
          dpi: 96
        })
        
        console.log('🔧 WMS图层对象创建完成')
        
        // 添加基本的事件监听
        wmsLayer.on('loading', function() {
          console.log(`🔄 WMS图层"${layer.layer_name}"开始加载`)
        })
        
        wmsLayer.on('load', function() {
          console.log(`✅ WMS图层"${layer.layer_name}"加载完成`)
          // ElMessage.success(`图层"${layer.layer_name}"加载成功 (${selectedCRS})`) // 移除弹窗，避免干扰
        })
        
        wmsLayer.on('tileerror', function(e) {
          console.error(`❌ WMS图层"${layer.layer_name}"瓦片加载失败:`, e)
          if (e.tile && e.tile.src) {
            console.log('失败的瓦片URL:', e.tile.src)
            
            // 分析URL问题
            const url = e.tile.src
            if (url.includes('GetCapabilities') && url.includes('GetMap')) {
              console.error('❌ 瓦片URL包含冲突的request参数!')
            }
            if ((url.match(/service=WMS/g) || []).length > 1) {
              console.error('❌ 瓦片URL包含重复的service参数!')
            }
            if ((url.match(/version=/g) || []).length > 1) {
              console.error('❌ 瓦片URL包含重复的version参数!')
            }
            if ((url.match(/layers=/g) || []).length > 1) {
              console.error('❌ 瓦片URL包含重复的layers参数!')
            }
            
            // 如果使用了数据库坐标系信息还是失败，尝试其他坐标系
            if (crsInfo && crsInfo.found_in_db) {
              console.warn('🔄 数据库坐标系失败，尝试备用坐标系...')
              
              // 启动多坐标系测试
              setTimeout(() => {
                testMultipleCRS(url, layerName, wmsUrl, layer)
              }, 1000)
            } else {
              // 启动多坐标系测试
              setTimeout(() => {
                testMultipleCRS(url, layerName, wmsUrl, layer)
              }, 1000)
            }
          }
          
          ElMessage.error({
            message: `图层"${layer.layer_name}"加载失败`,
            duration: 5000,
            showClose: true
          })
        })
        
        // 为WMS图层添加点击事件
        wmsLayer.on('click', function(e) {
          console.log('WMS图层点击事件:', e)
          currentActiveLayer.value = layer
          emit('layer-selected', layer)
        })
        
        // 保存图层引用
        mapLayers.value[layer.id] = wmsLayer
        
        // 按照示例的方式添加到地图：使用map.addLayer方法
        if (layer.visibility === true) {
          console.log(`🗺️ 添加WMS图层到地图: ${layer.layer_name}`)
          map.value.addLayer(wmsLayer)
        }
        
        // 🎯 Step 3: 如果有坐标信息，自动调整地图视图
        if (centerCoords && centerCoords.length >= 2) {
          setTimeout(() => {
            try {
              // 多重检查确保地图状态正常
              if (!map.value) {
                console.warn('⚠️ 地图对象为空，跳过自动视图调整')
                return
              }
              
              // 检查地图是否已完全初始化
              const container = map.value.getContainer()
              if (!container || !container.parentNode) {
                console.warn('⚠️ 地图容器未准备就绪，跳过自动视图调整')
                return
              }
              
              // 检查地图尺寸
              const size = map.value.getSize()
              if (!size || size.x === 0 || size.y === 0) {
                console.warn('⚠️ 地图尺寸无效，跳过自动视图调整')
                return
              }
              
              // 检查地图的坐标系是否正常
              if (!map.value.options.crs || !map.value.options.crs.project) {
                console.warn('⚠️ 地图坐标系未就绪，跳过自动视图调整')
                return
              }
              
              // 安全地设置视图
              console.log(`🎯 基于数据库坐标系信息调整地图视图: [${centerCoords[0].toFixed(4)}, ${centerCoords[1].toFixed(4)}] zoom=${zoomLevel}`)
              
              map.value.setView(centerCoords, zoomLevel, {
                animate: false, // 禁用动画避免可能的冲突
                duration: 0
              })
              
              console.log(`🎯 地图视图已调整到图层范围 (${selectedCRS})`)
              ElMessage.info(`地图视图已自动定位到"${layer.layer_name}"图层范围`)
              
            } catch (viewError) {
              console.error('❌ 自动调整地图视图时出错:', viewError)
              // 不显示错误消息，因为这是自动调整，失败了用户可以手动调整
            }
          }, 1500)
        }
        
        console.log('🎉 GeoServer WMS图层添加完成')
        
      } catch (error) {
        console.error('❌ 添加GeoServer图层失败:', error)
        ElMessage.error(`添加图层"${layer.layer_name}"失败: ${error.message}`)
      }
    }
    
    // 多坐标系测试函数
    const testMultipleCRS = (originalUrl, layerName, wmsUrl, layer) => {
      try {
        const urlObj = new URL(originalUrl)
        console.log('原始参数:', Object.fromEntries(urlObj.searchParams))
        
        // 🌍 尝试多种坐标系配置进行修复
        const crsToTry = [
          'EPSG:404000', // 都江堰地区专用坐标系（根据GeoServer预览链接）
          'EPSG:4326',   // WGS84地理坐标系
          'EPSG:4490',   // CGCS2000
          'EPSG:4214',   // Beijing 1954  
          'EPSG:3857',   // Web Mercator
          'EPSG:2383',   // Gauss Kruger CM 114E
          'EPSG:2384'    // Gauss Kruger CM 120E
        ]
        
        console.log('🔄 开始测试多种坐标系配置...')
        
        // 串行测试每种坐标系
        let testIndex = 0
        const testNextCRS = () => {
          if (testIndex >= crsToTry.length) {
            console.error('❌ 所有坐标系测试都失败')
            ElMessage.error({
              message: `图层"${layer.layer_name}"在所有测试的坐标系下都无法加载。请检查数据源和坐标系配置。`,
              duration: 8000,
              showClose: true
            })
            return
          }
          
          const testCRS = crsToTry[testIndex]
          const testVersion = testCRS === 'EPSG:404000' ? '1.1.0' : '1.1.1'
          
          // 清理并重建参数
          const cleanParams = new URLSearchParams()
          cleanParams.set('service', 'WMS')
          cleanParams.set('version', testVersion)
          cleanParams.set('request', 'GetMap')
          cleanParams.set('layers', layerName)
          cleanParams.set('styles', '')
          cleanParams.set('format', 'image/png')
          cleanParams.set('transparent', 'true')
          cleanParams.set('width', '256')
          cleanParams.set('height', '256')
          cleanParams.set('srs', testCRS)
          
          // 保留bbox参数（如果有）
          if (urlObj.searchParams.get('bbox')) {
            cleanParams.set('bbox', urlObj.searchParams.get('bbox'))
          }
          
          const testUrl = `${urlObj.origin}${urlObj.pathname}?${cleanParams.toString()}`
          console.log(`🧪 测试坐标系 ${testCRS} (${testIndex + 1}/${crsToTry.length}):`)
          console.log(`   URL: ${testUrl}`)
          
          // 测试这个坐标系
          fetch(testUrl)
            .then(response => {
              if (response.ok && response.headers.get('content-type')?.includes('image')) {
                console.log(`✅ 坐标系 ${testCRS} 测试成功! 状态: ${response.status}`)
                console.log(`   内容类型: ${response.headers.get('content-type')}`)
                
                // 成功找到可用的坐标系
                ElMessage.success({
                  message: `发现图层"${layer.layer_name}"在坐标系 ${testCRS} 下可以正常加载！建议更新图层配置。`,
                  duration: 8000,
                  showClose: true
                })
                
                // 如果是第一个成功的坐标系，提供重新加载选项
                if (testIndex === 0) {
                  ElMessageBox.confirm(
                    `检测到图层"${layer.layer_name}"在坐标系 ${testCRS} 下可以正常显示。是否要使用此坐标系重新加载图层？`,
                    '坐标系修复',
                    {
                      confirmButtonText: '重新加载',
                      cancelButtonText: '取消',
                      type: 'success'
                    }
                  ).then(() => {
                    // 用户确认重新加载，更新图层配置
                    console.log(`🔄 使用坐标系 ${testCRS} 重新创建图层...`)
                    
                    // 移除当前图层
                    const currentLayer = mapLayers.value[layer.id]
                    if (currentLayer && map.value.hasLayer(currentLayer)) {
                      map.value.removeLayer(currentLayer)
                    }
                    
                    // 使用新坐标系创建图层
                    const newWmsLayer = L.tileLayer.wms(wmsUrl, {
                      layers: layerName,
                      format: 'image/png',
                      transparent: true,
                      version: testVersion,
                      attribution: `GeoServer (${testCRS})`,
                      srs: testCRS,
                      exceptions: 'application/vnd.ogc.se_inimage',
                      dpi: 96,
                      styles: ''
                    })
                    
                    // 更新图层引用
                    mapLayers.value[layer.id] = newWmsLayer
                    
                    // 添加到地图
                    if (layer.visibility === true) {
                      newWmsLayer.addTo(map.value)
                    }
                    
                    // 如果是都江堰地区且使用支持的坐标系，调整视图
                    if ((testCRS === 'EPSG:404000' || testCRS === 'EPSG:4326') && layer.layer_name.includes('都江堰')) {
                      setTimeout(() => {
                        try {
                          // 多重检查确保地图状态正常
                          if (!map.value) {
                            console.warn('⚠️ 地图对象为空，跳过视图调整')
                            return
                          }
                          
                          // 检查地图是否已完全初始化
                          if (!map.value.getContainer() || !map.value.getSize()) {
                            console.warn('⚠️ 地图容器未准备就绪，跳过视图调整')
                            return
                          }
                          
                          // 检查地图的坐标系是否正常
                          if (!map.value.options.crs || !map.value.options.crs.project) {
                            console.warn('⚠️ 地图坐标系未就绪，跳过视图调整')
                            return
                          }
                          
                          // 安全地设置视图 - 根据坐标系选择合适的坐标
                          let targetCoords, zoomLevel
                          if (testCRS === 'EPSG:404000') {
                            // 使用GeoServer预览链接的bbox中心点
                            const centerLng = (103.44123417062076 + 105.62364387846247) / 2
                            const centerLat = (29.463131839962728 + 31.460939144026554) / 2
                            targetCoords = [centerLat, centerLng]
                            zoomLevel = 10
                          } else {
                            // EPSG:4326的备用坐标
                            targetCoords = [30.9, 103.6]
                            zoomLevel = 11
                          }
                          
                          map.value.setView(targetCoords, zoomLevel, {
                            animate: false, // 禁用动画避免可能的冲突
                            duration: 0
                          })
                          
                          console.log(`🎯 地图视图已调整到都江堰地区 (${testCRS}): [${targetCoords[0].toFixed(4)}, ${targetCoords[1].toFixed(4)}]`)
                          ElMessage.info(`地图视图已调整到都江堰地区 (${testCRS})`)
                        } catch (viewError) {
                          console.error('❌ 错误恢复时调整地图视图失败:', viewError)
                          // 不显示错误消息，因为这是错误恢复过程中的次要操作
                        }
                      }, 1500)
                    }
                    
                    console.log(`✅ 图层"${layer.layer_name}"已使用坐标系 ${testCRS} 重新加载`)
                  }).catch(() => {
                    console.log('用户取消了图层重新加载')
                  })
                }
                
                return // 成功，停止测试
              } else {
                console.log(`❌ 坐标系 ${testCRS} 测试失败: ${response.status}`)
                console.log(`   内容类型: ${response.headers.get('content-type')}`)
                
                // 如果不是图像内容，打印一些响应信息
                if (!response.headers.get('content-type')?.includes('image')) {
                  response.text().then(text => {
                    console.log(`   错误响应内容: ${text.substring(0, 200)}...`)
                  }).catch(() => {})
                }
                
                testIndex++
                setTimeout(testNextCRS, 300) // 延迟300ms后测试下一个
              }
            })
            .catch(testError => {
              console.log(`❌ 坐标系 ${testCRS} 测试异常: ${testError.message}`)
              testIndex++
              setTimeout(testNextCRS, 300) // 延迟300ms后测试下一个
            })
        }
        
        // 开始测试
        testNextCRS()
        
      } catch (urlError) {
        console.error('URL解析失败:', urlError)
        ElMessage.error(`图层"${layer.layer_name}"URL解析失败`)
      }
    }
    
    // 清除所有图层
    const clearAllLayers = () => {
      Object.values(mapLayers.value).forEach(layer => {
        if (map.value && map.value.hasLayer(layer)) {
          map.value.removeLayer(layer)
        }
      })
      Object.values(mvtLayers.value).forEach(layer => {
        if (map.value && map.value.hasLayer(layer)) {
          map.value.removeLayer(layer)
        }
      })
      mapLayers.value = {}
      mvtLayers.value = {}
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = (layer) => {
      try {
        const targetLayer = layer.service_type === 'martin' 
          ? mvtLayers.value[layer.id] 
          : mapLayers.value[layer.id]
          
        if (!targetLayer) {
          ElMessage.warning(`图层"${layer.layer_name}"未找到，请重新加载场景`)
          return
        }
        
        if (layer.visibility) {
          // 显示图层 - 使用map.addLayer方法（与示例一致）
          if (!map.value.hasLayer(targetLayer)) {
            console.log(`🗺️ 显示图层: ${layer.layer_name}`)
            map.value.addLayer(targetLayer)
          }
        } else {
          // 隐藏图层 - 使用map.removeLayer方法
          if (map.value.hasLayer(targetLayer)) {
            console.log(`🗺️ 隐藏图层: ${layer.layer_name}`)
            map.value.removeLayer(targetLayer)
          }
        }
        
        // 更新服务器状态
        updateLayerVisibility(layer.id, layer.visibility)
        
        const statusText = layer.visibility ? '显示' : '隐藏'
        const serviceText = layer.service_type === 'martin' ? 'Martin' : 'GeoServer'
        // ElMessage.success(`${serviceText}图层"${layer.layer_name}"${statusText}`) // 移除弹窗，避免干扰
        console.log(`✅ ${serviceText}图层"${layer.layer_name}"${statusText}`)
      } catch (error) {
        console.error('切换图层可见性失败', error)
        ElMessage.error('切换图层可见性失败')
        layer.visibility = !layer.visibility // 回滚状态
      }
    }
    
    // 更新图层可见性到服务
    const updateLayerVisibility = async (layerId, visibility) => {
      if (props.readonly) return
      
      try {
        await gisApi.updateSceneLayer(props.sceneId, layerId, { visibility })
      } catch (error) {
        console.error('更新图层可见性失败', error)
      }
    }
    
    // 显示样式设置对话框
    const showStyleDialog = async (layer) => {
      // 发射事件通知父组件设置当前图层
      emit('layer-selected', layer)
      
      currentStyleLayer.value = layer
      
      // 判断是否为DXF Martin图层，设置对应的选项卡
      if (layer.service_type === 'martin' && layer.file_type === 'dxf' && layer.martin_service_id) {
        activeStyleTab.value = 'dxf'
      } else {
        activeStyleTab.value = 'basic'
      }
      
      try {
        let response
        
        // 获取样式配置
        if (layer.service_type === 'martin' && layer.martin_service_id) {
          response = await gisApi.getMartinServiceStyle(layer.martin_service_id)
        } else {
          response = await gisApi.getLayerStyle(layer.id)
        }
        
        // 重置为默认值
        styleForm.point = { color: '#FF0000', size: 6, shape: 'circle', opacity: 1 }
        styleForm.line = { color: '#0000FF', width: 2, style: 'solid', opacity: 1 }
        styleForm.polygon = { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000', outlineWidth: 1, opacity: 1 }
        styleForm.raster = { opacity: 1, palette: 'default' }
        
        // 应用获取到的样式配置
        if (response?.success && response.data?.style_config) {
          const { style_config, file_type } = response.data
          const layerFileType = file_type || layer.file_type
          
          if (['shp', 'dwg', 'dxf', 'geojson'].includes(layerFileType)) {
            if (style_config.point) styleForm.point = { ...styleForm.point, ...style_config.point }
            if (style_config.line) styleForm.line = { ...styleForm.line, ...style_config.line }
            if (style_config.polygon) styleForm.polygon = { ...styleForm.polygon, ...style_config.polygon }
          } else {
            if (style_config.raster) styleForm.raster = { ...styleForm.raster, ...style_config.raster }
          }
        }
        
        styleDialogVisible.value = true
      } catch (error) {
        console.error('获取图层样式配置失败:', error)
        // 使用默认样式显示对话框
        styleDialogVisible.value = true
        ElMessage.warning('获取样式配置失败，已加载默认配置')
      }
    }
    
    // 应用样式
    const applyStyle = async () => {
      if (!currentStyleLayer.value) return
      
      // 准备样式配置
      let styleConfig = {}
      if (['shp', 'dwg', 'dxf', 'geojson'].includes(currentStyleLayer.value.file_type)) {
        styleConfig = {
          point: { ...styleForm.point },
          line: { ...styleForm.line },
          polygon: { ...styleForm.polygon }
        }
      } else {
        styleConfig = { raster: { ...styleForm.raster } }
      }
      
      try {
        // 更新后端样式
        if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
          await gisApi.updateMartinServiceStyle(currentStyleLayer.value.martin_service_id, styleConfig)
        } else {
          await gisApi.updateLayerStyle(currentStyleLayer.value.id, styleConfig)
        }
        
        // 更新本地样式配置
        const layerIndex = layersList.value.findIndex(layer => layer.id === currentStyleLayer.value.id)
        if (layerIndex !== -1) {
          layersList.value[layerIndex].style_config = styleConfig
        }
        currentStyleLayer.value.style_config = styleConfig
        
        // 重新加载图层
        if (currentStyleLayer.value.service_type === 'martin') {
          const mvtLayer = mvtLayers.value[currentStyleLayer.value.id]
          if (mvtLayer && map.value.hasLayer(mvtLayer)) {
            map.value.removeLayer(mvtLayer)
          }
          delete mvtLayers.value[currentStyleLayer.value.id]
          await addMartinLayer(currentStyleLayer.value)
        } else {
          const wmsLayer = mapLayers.value[currentStyleLayer.value.id]
          if (wmsLayer && map.value.hasLayer(wmsLayer)) {
            map.value.removeLayer(wmsLayer)
          }
          delete mapLayers.value[currentStyleLayer.value.id]
          await addGeoServerLayer(currentStyleLayer.value)
        }
        
        styleDialogVisible.value = false
        ElMessage.success('样式应用成功，图层已更新')
      } catch (error) {
        console.error('更新图层样式失败:', error)
        ElMessage.error('更新图层样式失败')
      }
    }
    
    // 显示添加图层对话框
    const showAddLayerDialog = async () => {
      if (!props.sceneId) {
        ElMessage.warning('请先选择一个场景')
        return
      }
      addLayerDialogVisible.value = true
      await fetchAvailableLayers()
    }
    
    // 获取可用图层
    const fetchAvailableLayers = async () => {
      try {
        const params = { ...layerSearchForm }
        Object.keys(params).forEach(key => {
          if (params[key] === '') delete params[key]
        })

        const response = await gisApi.getFiles(params)
        let filteredFiles = response.files || []

        if (layerSearchForm.service_type) {
          filteredFiles = filteredFiles.filter(file => {
            if (layerSearchForm.service_type === 'geoserver') {
              return file.geoserver_service && file.geoserver_service.is_published
            } else if (layerSearchForm.service_type === 'martin') {
              return file.martin_service && file.martin_service.is_published
            }
            return false
          })
        }

        // 确保每个文件对象都有layer_name属性
        filteredFiles = filteredFiles.map(file => ({
          ...file,
          layer_name: file.layer_name || file.file_name || file.original_name || '未命名图层'
        }))

        availableLayers.value = filteredFiles
      } catch (error) {
        console.error('获取可用图层失败', error)
        ElMessage.error('获取可用图层失败')
      }
    }
    
    // 搜索图层
    const searchLayers = () => {
      fetchAvailableLayers()
    }
    
    // 检查图层是否已在场景中
    const isLayerInScene = (fileId, serviceType) => {
      return layersList.value.some(layer => layer.file_id === fileId && layer.service_type === serviceType)
    }
    
    // 检查文件是否有任何已发布的服务
    const hasAnyPublishedService = (file) => {
      const hasGeoServer = file.geoserver_service && file.geoserver_service.is_published
      const hasMartin = file.martin_service && file.martin_service.is_published
      return hasGeoServer || hasMartin
    }
    
    // 添加图层到场景
    const addLayerToScene = async (file, serviceType) => {
      try {
        // 检查服务是否已发布
        let serviceInfo
        if (serviceType === 'martin') {
          serviceInfo = file.martin_service
          if (!serviceInfo || !serviceInfo.is_published) {
            ElMessage.error('该文件尚未发布Martin服务')
            return
          }
        } else if (serviceType === 'geoserver') {
          serviceInfo = file.geoserver_service
          if (!serviceInfo || !serviceInfo.is_published) {
            ElMessage.error('该文件尚未发布GeoServer服务')
            return
          }
        } else {
          ElMessage.error('不支持的服务类型')
          return
        }
        
        // 构建图层数据
        let layerData = {
          layer_name: file.file_name,
          visible: true,
          service_type: serviceType,
          file_id: file.id,
          file_type: file.file_type,
          discipline: file.discipline
        }
        
        if (serviceType === 'martin') {
          // Martin服务处理
          const martinServices = await gisApi.searchMartinServices({ file_id: serviceInfo.file_id })
          const martinService = martinServices.services.find(service => service.file_id === serviceInfo.file_id)
          
          if (!martinService) {
            ElMessage.error('找不到对应的Martin服务')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: file.id,
            martin_service_id: martinService.database_record_id || martinService.id,
            mvt_url: serviceInfo.mvt_url,
            tilejson_url: serviceInfo.tilejson_url
          }
        } else {
          // GeoServer服务处理
          layerData = {
            ...layerData,
            layer_id: serviceInfo.layer_id || file.id,
            geoserver_layer_name: serviceInfo.layer_name,
            wms_url: serviceInfo.wms_url,
            wfs_url: serviceInfo.wfs_url
          }
        }
        
        await gisApi.addLayerToScene(props.sceneId, layerData)
        addLayerDialogVisible.value = false
        ElMessage.success('图层添加成功')
        
        // 重新加载场景
        await loadScene(props.sceneId)
        emit('layerAdded', { sceneId: props.sceneId, layerData })
      } catch (error) {
        console.error('添加图层失败', error)
        ElMessage.error('添加图层失败')
      }
    }
    
    // 移除图层
    const removeLayer = (layer) => {
      ElMessageBox.confirm(`确认从场景中移除图层"${layer.layer_name}"？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await gisApi.removeLayerFromScene(props.sceneId, layer.id)
          
          // 从地图移除
          const targetLayer = layer.service_type === 'martin' 
            ? mvtLayers.value[layer.id] 
            : mapLayers.value[layer.id]
            
          if (targetLayer) {
            map.value.removeLayer(targetLayer)
            if (layer.service_type === 'martin') {
              delete mvtLayers.value[layer.id]
            } else {
              delete mapLayers.value[layer.id]
            }
          }
          
          // 从列表移除
          layersList.value = layersList.value.filter(item => item.id !== layer.id)
          ElMessage.success('图层移除成功')
        } catch (error) {
          console.error('移除图层失败', error)
          ElMessage.error('移除图层失败')
        }
      }).catch(() => {})
    }
    
    // 底图切换事件处理
    const onBaseMapChanged = (/* layerInfo */) => { // 注释掉未使用的参数
      //console.log('底图已切换', layerInfo)
    }
    
    // 获取图层状态
    const getLayerStatusText = (layer) => {
      if (layer.service_type === 'martin') return '已发布'
      return (!layer.geoserver_layer || !layer.wms_url) ? '未发布' : '已发布'
    }
    
    const getLayerStatusClass = (layer) => {
      if (layer.service_type === 'martin') return 'status-published'
      return (!layer.geoserver_layer || !layer.wms_url) ? 'status-unpublished' : 'status-published'
    }
    
    // 面板收起/展开状态
    const panelCollapsed = ref(false)
    const togglePanel = () => {
      panelCollapsed.value = !panelCollapsed.value
      setTimeout(() => {
        if (map.value) map.value.invalidateSize()
      }, 300)
    }
    
    // 监听sceneId变化
    watch(() => props.sceneId, (newValue, oldValue) => {
      if (newValue && newValue !== oldValue && map.value) {
        setTimeout(() => {
          if (props.sceneId === newValue) {
            loadScene(newValue)
          }
        }, 100)
      }
    })
    
    // 处理DXF样式更新
    const onDxfStylesUpdated = async (updateData) => {
      const { layerName, style, allStyles } = updateData
      console.log('DXF样式已更新:', { layerName, style, allStyles })
      
      // 如果有MVT图层需要重新渲染
      if (currentStyleLayer.value && mvtLayers.value[currentStyleLayer.value.id]) {
        try {
          const mvtLayer = mvtLayers.value[currentStyleLayer.value.id]
          
          // 方法1: 尝试重新创建样式函数并重新渲染
          if (mvtLayer.options && mvtLayer.options.vectorTileLayerStyles) {
            // 导入dxfStyleManager来创建新的样式函数
            // const { dxfStyleManager } = await import('@/utils/dxfStyleManager') // 注释掉未使用的变量
            
            // 创建新的样式函数
            const createDxfStyleFunction = () => {
              // 获取默认DXF样式配置
              const defaultDxfStyles = defaultDxfStylesConfig.defaultDxfStyles
              console.log('🎨 加载默认DXF样式配置:', Object.keys(defaultDxfStyles))
              
              return function(properties, zoom) {
                const layerName = properties.layer || properties.Layer || 'default'
                
                // 获取预定义的图层样式
                const layerStyle = defaultDxfStyles[layerName]
                
                // 基础样式配置
                let style = {
                  weight: 2,
                  color: '#0066cc',
                  opacity: 0.8,
                  fillColor: '#66ccff',
                  fillOpacity: 0.3,
                  radius: 4,
                  fill: true
                }
                
                // 如果找到预定义样式，使用它
                if (layerStyle) {
                  style = {
                    weight: layerStyle.weight || 2,
                    color: layerStyle.color || '#0066cc',
                    opacity: layerStyle.opacity || 0.8,
                    fillColor: layerStyle.fillColor || layerStyle.color || '#66ccff',
                    fillOpacity: layerStyle.fillOpacity || 0.3,
                    radius: layerStyle.radius || 4,
                    fill: layerStyle.fill !== false,
                    dashArray: layerStyle.dashArray || null,
                    lineCap: layerStyle.lineCap || 'round',
                    lineJoin: layerStyle.lineJoin || 'round'
                  }
                  
                  console.log(`🎨 图层 "${layerName}" 使用预定义样式:`, layerStyle.name, style.color)
                } else {
                  console.log(`🎨 图层 "${layerName}" 使用默认样式`)
                }
                
                // 根据缩放级别调整样式
                if (zoom < 10) {
                  style.weight = Math.max(style.weight - 0.5, 0.5)
                  style.opacity = Math.max(style.opacity - 0.2, 0.3)
                  if (style.radius) style.radius = Math.max(2, style.radius - 1)
                } else if (zoom > 15) {
                  style.weight = style.weight + 0.5
                  style.opacity = Math.min(style.opacity + 0.1, 1)
                  if (style.radius) style.radius = style.radius + 1
                }
                
                // 特殊图层处理 - 根据可见性设置
                if (layerStyle && layerStyle.visible === false) {
                  style.opacity = 0
                  style.fillOpacity = 0
                }
                
                // 特殊缩放级别处理
                if (layerName === 'sqx' && zoom < 14) {
                  style.opacity = 0  // 1米等高线在小比例尺下隐藏
                }
                
                if (layerName === 'jqx' && zoom < 12) {
                  style.opacity = Math.max(style.opacity - 0.3, 0.2)  // 5米等高线淡化
                }
                
                return style
              }
            }
            
            // 更新样式函数
            const styleFunction = createDxfStyleFunction()
            
            // 获取表名
            // const tableName = currentStyleLayer.value.martin_service?.postgis_table || 'default' // 注释掉未使用的变量
            
            // 更新所有相关图层的样式函数
            Object.keys(mvtLayer.options.vectorTileLayerStyles).forEach(layerKey => {
              mvtLayer.options.vectorTileLayerStyles[layerKey] = styleFunction
            })
            
            // 触发重新渲染
            if (mvtLayer.redraw) {
              mvtLayer.redraw()
              console.log('✅ DXF图层样式已实时更新')
            }
          }
        } catch (error) {
          console.error('实时更新DXF样式失败:', error)
          console.log('将在保存时重新加载图层')
        }
      }
    }
    
    // 应用并保存DXF样式
    const applyAndSaveDxfStyles = async () => {
      if (!dxfStyleEditorRef.value) {
        ElMessage.warning('DXF样式编辑器未准备就绪')
        return
      }

      try {
        savingDxfStyles.value = true
        const success = await dxfStyleEditorRef.value.saveStylesToDatabase()
        
        if (success) {
          // 样式更改是实时的，无需重新加载图层
          // 只需要关闭对话框并显示成功消息
          styleDialogVisible.value = false
          ElMessage.success('DXF样式已保存到数据库')
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
      const { enabled, martinServiceId, layerId } = controlData
      console.log('属性弹窗控制变更:', { enabled, martinServiceId, layerId })
      
      // 查找对应的MVT图层
      const mvtLayer = mvtLayers.value[layerId]
      if (!mvtLayer) {
        console.warn('未找到对应的MVT图层:', layerId)
        return
      }
      
      // 控制弹窗启用状态
      if (enabled) {
        // 开启属性弹窗
        mvtLayer._popupEnabled = true
        console.log('✅ 已启用MVT图层属性弹窗')
      } else {
        // 关闭属性弹窗
        mvtLayer._popupEnabled = false
        
        // 关闭当前显示的弹窗
        if (map.value) {
          map.value.closePopup()
        }
        
        console.log('✅ 已关闭MVT图层属性弹窗')
      }
    }
    
    // 设置当前活动图层
    const setActiveLayer = (layer) => {
      console.log('设置当前活动图层:', layer.layer_name)
      currentActiveLayer.value = layer
      
      // 发射事件通知父组件
      emit('layer-selected', layer)
    }
    
    // 内部置顶函数（不设置活动图层）
    const bringLayerToTopInternal = (layer) => {
      console.log('将图层置顶（内部）:', layer.layer_name)
      
      try {
        // 1. 禁用所有图层的鼠标事件响应
        Object.values(mvtLayers.value).forEach(mvtLayer => {
          mvtLayer._popupEnabled = false
          // 降低其他图层的z-index，使用较低层级的pane
          if (mvtLayer.options && mvtLayer.options.pane !== 'tilePane') {
            mvtLayer.options.pane = 'tilePane' // 降到瓦片层级别
          }
        })
        
        Object.values(mapLayers.value).forEach(wmsLayer => {
          if (wmsLayer.options && wmsLayer.options.pane !== 'tilePane') {
            wmsLayer.options.pane = 'tilePane' // 降到瓦片层级别
          }
        })
        
        // 2. 关闭当前弹窗
        if (map.value) {
          map.value.closePopup()
        }
        
        // 3. 将目标图层置顶并启用事件
        if (layer.service_type === 'martin') {
          const mvtLayer = mvtLayers.value[layer.id]
          if (mvtLayer && map.value) {
            // 重新添加到地图以置顶（先移除再添加）
            if (map.value.hasLayer(mvtLayer)) {
              map.value.removeLayer(mvtLayer)
            }
            
            // 设置为最高级别的pane，确保能响应鼠标事件
            mvtLayer.options.pane = 'overlayPane' // 使用最高层级的overlayPane
            mvtLayer.addTo(map.value)
            
            // 只启用这个图层的弹窗
            mvtLayer._popupEnabled = true
            
            console.log('✅ Martin图层已置顶并启用弹窗:', layer.layer_name)
            console.log('   - 当前pane:', mvtLayer.options.pane)
            console.log('   - 弹窗状态:', mvtLayer._popupEnabled)
          }
        } else if (layer.service_type === 'geoserver') {
          const wmsLayer = mapLayers.value[layer.id]
          if (wmsLayer && map.value) {
            // 重新添加到地图以置顶
            if (map.value.hasLayer(wmsLayer)) {
              map.value.removeLayer(wmsLayer)
            }
            
            // 设置为最高级别的pane
            if (wmsLayer.options) {
              wmsLayer.options.pane = 'overlayPane'
            }
            wmsLayer.addTo(map.value)
            
            console.log('✅ GeoServer图层已置顶:', layer.layer_name)
            console.log('   - 当前pane:', wmsLayer.options.pane)
          }
        }
        
        // 4. 提供用户反馈
        ElMessage.success({
          message: `图层"${layer.layer_name}"已置顶，现在可以响应鼠标交互事件`,
          duration: 2000
        })
        
      } catch (error) {
        console.error('图层置顶失败:', error)
        ElMessage.error('图层置顶失败')
      }
    }
    
    // 将图层置顶（公共接口）
    const bringLayerToTop = (layer) => {
      console.log('将图层置顶:', layer.layer_name)
      
      // 设置为当前活动图层
      currentActiveLayer.value = layer
      
      // 发射事件通知父组件
      emit('layer-selected', layer)
      
      // 执行置顶操作
      bringLayerToTopInternal(layer)
    }
    
    // 诊断地图和图层状态
    const diagnoseMapLayers = async () => {
      console.log('🔍 开始诊断地图状态...')
      
      if (!map.value) {
        console.error('❌ 地图对象不存在')
        return
      }
      
      console.log('📍 地图基本信息:')
      console.log('  - 中心点:', map.value.getCenter())
      console.log('  - 缩放级别:', map.value.getZoom())
      console.log('  - 坐标系:', map.value.options.crs.code)
      console.log('  - 地图尺寸:', map.value.getSize())
      
      console.log('📊 当前图层状态:')
      console.log('  - GeoServer图层数量:', Object.keys(mapLayers.value).length)
      console.log('  - Martin图层数量:', Object.keys(mvtLayers.value).length)
      console.log('  - 场景图层列表:', layersList.value.length)
      console.log('  - 当前活动图层:', currentActiveLayer.value?.layer_name || '无')
      
      // 🎯 新增：诊断数据库坐标系信息
      console.log('🗄️ 开始诊断数据库坐标系信息...')
      
      for (const layer of layersList.value) {
        const isActive = currentActiveLayer.value?.id === layer.id
        console.log(`  - 图层${layersList.value.indexOf(layer) + 1}: ${layer.layer_name} ${isActive ? '🔥(当前活动)' : ''}`)
        console.log(`    类型: ${layer.service_type}`)
        console.log(`    可见: ${layer.visibility}`)
        
        // 如果是GeoServer图层，查询数据库坐标系信息
        if (layer.service_type === 'geoserver') {
          try {
            console.log(`    📡 查询数据库坐标系信息...`)
            const crsResponse = await gisApi.getLayerCRSInfo(layer.id)
            
            if (crsResponse && crsResponse.success && crsResponse.data) {
              const crsInfo = crsResponse.data
              console.log(`    ✅ 数据库坐标系信息:`)
              console.log(`       - 坐标系: ${crsInfo.srs}`)
              console.log(`       - WMS版本: ${crsInfo.wms_version}`)
              console.log(`       - 在数据库中找到: ${crsInfo.found_in_db}`)
              console.log(`       - 工作空间: ${crsInfo.workspace_name || '未知'}`)
              console.log(`       - 存储名称: ${crsInfo.store_name || '未知'}`)
              console.log(`       - 图层名称: ${crsInfo.layer_name || '未知'}`)
              if (crsInfo.center_coords) {
                console.log(`       - 推荐中心点: [${crsInfo.center_coords[0].toFixed(4)}, ${crsInfo.center_coords[1].toFixed(4)}]`)
                console.log(`       - 推荐缩放级别: ${crsInfo.zoom_level}`)
              }
              if (crsInfo.native_bbox) {
                console.log(`       - 原始边界框:`, crsInfo.native_bbox)
              }
              if (crsInfo.lat_lon_bbox) {
                console.log(`       - 经纬度边界框:`, crsInfo.lat_lon_bbox)
              }
            } else {
              console.log(`    ❌ 获取坐标系信息失败`)
            }
          } catch (crsError) {
            console.log(`    ❌ 查询坐标系信息异常: ${crsError.message}`)
          }
        }
        
        if (layer.service_type === 'martin') {
          const mvtLayer = mvtLayers.value[layer.id]
          console.log(`    MVT图层存在: ${!!mvtLayer}`)
          if (mvtLayer) {
            console.log(`    已添加到地图: ${map.value.hasLayer(mvtLayer)}`)
            console.log(`    当前pane: ${mvtLayer.options?.pane || '未设置'}`)
            console.log(`    弹窗启用: ${mvtLayer._popupEnabled}`)
          }
        } else {
          const wmsLayer = mapLayers.value[layer.id]
          console.log(`    WMS图层存在: ${!!wmsLayer}`)
          if (wmsLayer) {
            console.log(`    已添加到地图: ${map.value.hasLayer(wmsLayer)}`)
            console.log(`    当前pane: ${wmsLayer.options?.pane || '未设置'}`)
            console.log(`    WMS配置: ${JSON.stringify(wmsLayer.wmsParams)}`)
          }
        }
      }
      
      // 诊断Pane的z-index情况
      console.log('📊 地图Pane层级诊断:')
      const panes = map.value.getPanes()
      Object.entries(panes).forEach(([paneName, paneElement]) => {
        const zIndex = window.getComputedStyle(paneElement).zIndex
        console.log(`  - ${paneName}: z-index = ${zIndex}`)
      })
      
      // 🌍 坐标系诊断功能
      console.log('🌍 坐标系诊断:')
      
      // 测试都江堰地区的WMS图层
      const dujiangyanLayer = layersList.value.find(layer => 
        layer.layer_name && (
          layer.layer_name.includes('都江堰') || 
          layer.layer_name.includes('灌区') ||
          layer.layer_name.includes('范围')
        ) && layer.service_type === 'geoserver'
      )
      
      if (dujiangyanLayer) {
        console.log('🎯 发现都江堰图层，开始坐标系测试:', dujiangyanLayer.layer_name)
        
        // 首先尝试从数据库获取坐标系信息进行测试
        try {
          const crsResponse = await gisApi.getLayerCRSInfo(dujiangyanLayer.id)
          if (crsResponse && crsResponse.success && crsResponse.data && crsResponse.data.found_in_db) {
            const dbCRS = crsResponse.data.srs
            console.log(`🗄️ 数据库中的坐标系: ${dbCRS}`)
            
            // 使用数据库坐标系进行优先测试
            await testDatabaseCRS(dujiangyanLayer, dbCRS, crsResponse.data.wms_version)
          } else {
            console.log('⚠️ 数据库中未找到坐标系信息，使用默认测试')
            // 回退到原有的测试方法
            await testCoordinateSystems(dujiangyanLayer)
          }
        } catch (error) {
          console.log('❌ 获取数据库坐标系信息失败，使用默认测试:', error.message)
          await testCoordinateSystems(dujiangyanLayer)
        }
      } else {
        console.log('⚠️ 未找到都江堰图层，跳过坐标系测试')
      }
      
      // 测试简单底图
      console.log('🧪 测试基础底图加载...')
      const testLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '测试图层',
        opacity: 0.5
      })
      testLayer.addTo(map.value)
      
      // 测试GeoServer服务
      console.log('🧪 测试GeoServer服务连接...')
      fetch('/geoserver/web/')
        .then(response => {
          if (response.ok) {
            console.log('✅ GeoServer Web界面可访问')
          } else {
            console.error('❌ GeoServer Web界面返回错误状态:', response.status)
          }
        })
        .catch(error => {
          console.error('❌ GeoServer Web界面连接失败:', error)
        })
      
      // 测试GeoServer WMS服务
      fetch('/geoserver/wms?service=WMS&version=1.1.1&request=GetCapabilities')
        .then(response => {
          if (response.ok) {
            console.log('✅ GeoServer WMS服务可访问')
            return response.text()
          } else {
            console.error('❌ GeoServer WMS服务返回错误状态:', response.status)
            throw new Error(`GeoServer WMS状态: ${response.status}`)
          }
        })
        .then(data => {
          console.log('📄 GeoServer WMS Capabilities长度:', data.length)
          // 检查是否包含我们的图层
          if (data.includes('shpservice:')) {
            console.log('✅ 在Capabilities中找到shpservice图层')
          } else {
            console.warn('⚠️ 在Capabilities中未找到shpservice图层')
          }
        })
        .catch(error => {
          console.error('❌ GeoServer WMS服务连接失败:', error)
          ElMessage.error('GeoServer WMS服务不可用')
        })
      
      setTimeout(() => {
        console.log('✅ 测试图层已添加，如果能看到半透明的OpenStreetMap，说明基础地图功能正常')
        setTimeout(() => {
          map.value.removeLayer(testLayer)
          console.log('🧹 测试图层已移除')
        }, 3000)
      }, 1000)
    }
    
    // 使用数据库坐标系进行测试
    const testDatabaseCRS = async (layer, dbCRS, dbVersion) => {
      console.log(`🗄️ 使用数据库坐标系信息进行测试: ${dbCRS} (版本: ${dbVersion})`)
      
      let wmsUrl = layer.wms_url
      if (wmsUrl.includes('?')) {
        wmsUrl = wmsUrl.split('?')[0]
      }
      if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
        wmsUrl = '/geoserver/wms'
      }
      
      const layerName = layer.geoserver_layer
      
      const testParams = new URLSearchParams({
        service: 'WMS',
        version: dbVersion,
        request: 'GetMap',
        layers: layerName,
        styles: '',
        format: 'image/png',
        transparent: 'true',
        width: '256',
        height: '256',
        srs: dbCRS,
        // 使用默认bbox进行测试
        bbox: dbCRS === 'EPSG:404000' ? 
          '103.44123417062076,29.463131839962728,105.62364387846247,31.460939144026554' : 
          (dbCRS === 'EPSG:4326' ? '103.4,30.7,103.8,31.1' : '11508000,3599000,11552000,3643000')
      })
      
      const testUrl = `${wmsUrl}?${testParams.toString()}`
      
      try {
        console.log(`🧪 测试数据库坐标系 ${dbCRS}...`)
        console.log(`   测试URL: ${testUrl}`)
        
        const response = await fetch(testUrl)
        
        if (response.ok) {
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('image')) {
            console.log(`✅ 数据库坐标系 ${dbCRS} 测试成功! (${response.status}) - ${contentType}`)
            
            // 获取图像大小信息
            const contentLength = response.headers.get('content-length')
            if (contentLength) {
              console.log(`   图像大小: ${Math.round(contentLength / 1024)}KB`)
            }
            
            // ElMessage.success({
            //   message: `数据库坐标系 ${dbCRS} 验证成功！图层配置正确。`,
            //   duration: 5000
            // }) // 移除弹窗，避免诊断时干扰
          } else {
            console.log(`⚠️ 数据库坐标系 ${dbCRS} 响应成功但不是图像 - ${contentType}`)
            const text = await response.text()
            console.log(`   响应内容: ${text.substring(0, 200)}...`)
            
            ElMessage.warning({
              message: `数据库坐标系 ${dbCRS} 测试异常：响应格式不正确`,
              duration: 5000
            })
          }
        } else {
          console.log(`❌ 数据库坐标系 ${dbCRS} 测试失败: (${response.status})`)
          const text = await response.text()
          console.log(`   错误信息: ${text.substring(0, 200)}...`)
          
          ElMessage.error({
            message: `数据库坐标系 ${dbCRS} 验证失败 (${response.status})`,
            duration: 5000
          })
          
          // 回退到多坐标系测试
          console.log('🔄 回退到多坐标系测试...')
          await testCoordinateSystems(layer)
        }
      } catch (error) {
        console.log(`❌ 数据库坐标系 ${dbCRS} 测试异常: ${error.message}`)
        ElMessage.error({
          message: `数据库坐标系 ${dbCRS} 测试异常: ${error.message}`,
          duration: 5000
        })
        
        // 回退到多坐标系测试
        console.log('🔄 回退到多坐标系测试...')
        await testCoordinateSystems(layer)
      }
    }
    
    // 多坐标系测试函数（原有功能）
    const testCoordinateSystems = async (dujiangyanLayer) => {
      const crsToTest = [
        'EPSG:404000', // 都江堰地区专用坐标系（根据GeoServer预览链接）
        'EPSG:4326',   // WGS84
        'EPSG:4490',   // CGCS2000
        'EPSG:3857',   // Web Mercator
        'EPSG:4214',   // Beijing 1954
        'EPSG:4610'    // Xian 1980
      ]
      
      let wmsUrl = dujiangyanLayer.wms_url
      if (wmsUrl.includes('?')) {
        wmsUrl = wmsUrl.split('?')[0]
      }
      if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
        wmsUrl = '/geoserver/wms'
      }
      
      const layerName = dujiangyanLayer.geoserver_layer
      
      console.log('🧪 开始坐标系兼容性测试...')
      
      for (const crs of crsToTest) {
        const testParams = new URLSearchParams({
          service: 'WMS',
          version: crs === 'EPSG:404000' ? '1.1.0' : '1.1.1', // 根据坐标系选择版本
          request: 'GetMap',
          layers: layerName,
          styles: '',
          format: 'image/png',
          transparent: 'true',
          width: '256',
          height: '256',
          srs: crs,
          // 根据GeoServer预览链接使用实际的bbox坐标
          bbox: crs === 'EPSG:404000' ? 
            '103.44123417062076,29.463131839962728,105.62364387846247,31.460939144026554' : 
            (crs === 'EPSG:4326' ? '103.4,30.7,103.8,31.1' : '11508000,3599000,11552000,3643000')
        })
        
        const testUrl = `${wmsUrl}?${testParams.toString()}`
        
        try {
          console.log(`🔍 测试 ${crs}...`)
          const response = await fetch(testUrl)
          
          if (response.ok) {
            const contentType = response.headers.get('content-type')
            if (contentType && contentType.includes('image')) {
              console.log(`✅ ${crs}: 成功 (${response.status}) - ${contentType}`)
              
              // 获取图像大小信息
              const contentLength = response.headers.get('content-length')
              if (contentLength) {
                console.log(`   图像大小: ${Math.round(contentLength / 1024)}KB`)
              }
            } else {
              console.log(`⚠️ ${crs}: 响应成功但不是图像 - ${contentType}`)
              const text = await response.text()
              console.log(`   响应内容: ${text.substring(0, 100)}...`)
            }
          } else {
            console.log(`❌ ${crs}: 失败 (${response.status})`)
            const text = await response.text()
            console.log(`   错误信息: ${text.substring(0, 100)}...`)
          }
        } catch (error) {
          console.log(`❌ ${crs}: 网络错误 - ${error.message}`)
        }
        
        // 避免请求过于频繁
        await new Promise(resolve => setTimeout(resolve, 200))
      }
      
      console.log('🧪 坐标系兼容性测试完成')
    }
    
    onMounted(() => {
      console.log('🚀 MapViewer组件挂载完成，开始初始化...')
      
      // 使用nextTick确保DOM完全渲染
      nextTick(() => {
        // 延迟一小段时间确保容器完全准备就绪
        setTimeout(() => {
          try {
            initMap()
            
            // 等待地图初始化完成后再加载场景
            const sceneId = props.sceneId || route.query.scene_id
            if (sceneId) {
              // 再次延迟确保地图完全准备就绪
              setTimeout(() => {
                if (map.value && map.value.getContainer()) {
                  loadScene(sceneId)
                } else {
                  console.warn('⚠️ 地图初始化未完成，延迟加载场景')
                  setTimeout(() => {
                    if (map.value && map.value.getContainer()) {
                      loadScene(sceneId)
                    } else {
                      console.error('❌ 地图初始化失败，无法加载场景')
                      ElMessage.error('地图初始化失败，请刷新页面重试')
                    }
                  }, 1000)
                }
              }, 500)
            }
          } catch (initError) {
            console.error('❌ 组件初始化过程中出错:', initError)
            ElMessage.error('组件初始化失败: ' + initError.message)
          }
        }, 100)
      })
    })
    
    onUnmounted(() => {
      console.log('🧹 开始清理MapViewer组件...')
      
      // 清理所有图层
      try {
        clearAllLayers()
      } catch (layerError) {
        console.warn('清理图层时出现警告:', layerError)
      }
      
      // 安全地销毁地图实例
      if (map.value) {
        try {
          // 移除所有事件监听器
          map.value.off()
          
          // 检查地图容器是否仍然存在
          const container = map.value.getContainer()
          if (container && container.parentNode) {
            // 容器仍在DOM中，安全销毁
            map.value.remove()
            console.log('✅ 地图实例已安全销毁')
          } else {
            // 容器已被移除，只清理引用
            console.log('⚠️ 地图容器已被移除，仅清理引用')
          }
        } catch (destroyError) {
          console.warn('销毁地图实例时出现警告:', destroyError)
          // 即使出错也要清理引用
        } finally {
          map.value = null
        }
      }
      
      // 清理其他引用
      mapLayers.value = {}
      mvtLayers.value = {}
      
      console.log('✅ MapViewer组件清理完成')
    })
    
    // 获取当前活动图层信息
    const getCurrentLayerInfo = () => {
      if (!currentActiveLayer.value) {
        return {
          hasActiveLayer: false,
          message: '当前没有活动图层'
        }
      }
      
      const layer = currentActiveLayer.value
      let layerInstance = null
      let paneInfo = '未知'
      let eventEnabled = false
      
      if (layer.service_type === 'martin') {
        layerInstance = mvtLayers.value[layer.id]
        if (layerInstance) {
          paneInfo = layerInstance.options?.pane || '未设置'
          eventEnabled = layerInstance._popupEnabled === true
        }
      } else if (layer.service_type === 'geoserver') {
        layerInstance = mapLayers.value[layer.id]
        if (layerInstance) {
          paneInfo = layerInstance.options?.pane || '未设置'
          eventEnabled = true // WMS图层始终可以响应事件
        }
      }
      
      return {
        hasActiveLayer: true,
        layerName: layer.layer_name,
        serviceType: layer.service_type,
        pane: paneInfo,
        eventEnabled,
        canInteract: paneInfo === 'overlayPane' && eventEnabled,
        message: `当前活动图层: ${layer.layer_name} (${layer.service_type})`
      }
    }
    
    // 重置所有图层到默认状态
    const resetAllLayersToDefault = () => {
      console.log('🔄 重置所有图层到默认状态...')
      
      try {
        // 重置所有MVT图层
        Object.values(mvtLayers.value).forEach(mvtLayer => {
          mvtLayer._popupEnabled = false
          if (mvtLayer.options) {
            mvtLayer.options.pane = 'tilePane'
          }
        })
        
        // 重置所有WMS图层
        Object.values(mapLayers.value).forEach(wmsLayer => {
          if (wmsLayer.options) {
            wmsLayer.options.pane = 'tilePane'
          }
        })
        
        // 清除当前活动图层
        currentActiveLayer.value = null
        
        // 关闭弹窗
        if (map.value) {
          map.value.closePopup()
        }
        
        console.log('✅ 所有图层已重置到默认状态')
        ElMessage.info('所有图层已重置，请重新选择需要交互的图层')
        
      } catch (error) {
        console.error('重置图层状态失败:', error)
        ElMessage.error('重置图层状态失败')
      }
    }
    
    // 快速修复都江堰图层坐标系问题 - 现在基于数据库信息
    const fixDujiangyanCRS = async () => {
      console.log('🔧 开始智能修复图层坐标系问题...')
      
      // 首先检查地图是否已初始化
      if (!map.value) {
        ElMessage.error('地图未初始化，请等待地图加载完成后再试')
        return
      }
      
      // 查找都江堰图层
      const dujiangyanLayer = layersList.value.find(layer => 
        layer.layer_name && (
          layer.layer_name.includes('都江堰') || 
          layer.layer_name.includes('灌区') ||
          layer.layer_name.includes('范围')
        ) && layer.service_type === 'geoserver'
      )
      
      if (!dujiangyanLayer) {
        ElMessage.warning('未找到都江堰相关的GeoServer图层')
        return
      }
      
      console.log('🎯 找到目标图层:', dujiangyanLayer.layer_name)
      
      try {
        // 🗄️ 首先从数据库获取坐标系信息
        console.log('📡 从数据库获取图层坐标系信息...')
        let dbCRS = null
        let dbVersion = null
        let centerCoords = null
        let zoomLevel = 10
        
        try {
          const crsResponse = await gisApi.getLayerCRSInfo(dujiangyanLayer.id)
          if (crsResponse && crsResponse.success && crsResponse.data && crsResponse.data.found_in_db) {
            dbCRS = crsResponse.data.srs
            dbVersion = crsResponse.data.wms_version
            centerCoords = crsResponse.data.center_coords
            zoomLevel = crsResponse.data.zoom_level || 10
            
            console.log('✅ 成功获取数据库坐标系信息:', {
              srs: dbCRS,
              version: dbVersion,
              center: centerCoords,
              zoom: zoomLevel
            })
            
            // ElMessage.success({
            //   message: `从数据库获取到坐标系信息: ${dbCRS}，正在重新加载图层...`,
            //   duration: 3000
            // }) // 移除弹窗，避免干扰
            console.log(`✅ 从数据库获取到坐标系信息: ${dbCRS}，正在重新加载图层...`)
          } else {
            console.log('⚠️ 数据库中未找到坐标系信息，使用默认EPSG:404000')
            dbCRS = 'EPSG:404000'
            dbVersion = '1.1.0'
          }
        } catch (dbError) {
          console.warn('⚠️ 获取数据库坐标系信息失败，使用默认配置:', dbError.message)
          dbCRS = 'EPSG:404000'
          dbVersion = '1.1.0'
        }
        
        // 移除当前图层
        const currentLayer = mapLayers.value[dujiangyanLayer.id]
        if (currentLayer && map.value.hasLayer(currentLayer)) {
          map.value.removeLayer(currentLayer)
          console.log('🗑️ 已移除当前图层')
        }
        
        // 准备WMS URL
        let wmsUrl = dujiangyanLayer.wms_url
        if (wmsUrl.includes('?')) {
          wmsUrl = wmsUrl.split('?')[0]
        }
        if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
          wmsUrl = '/geoserver/wms'
        }
        
        const layerName = dujiangyanLayer.geoserver_layer
        
        // 使用数据库坐标系创建新图层
        console.log(`🔄 使用数据库坐标系 ${dbCRS} 重新创建图层...`)
        const newWmsLayer = L.tileLayer.wms(wmsUrl, {
          layers: layerName,
          format: 'image/png',
          transparent: true,
          version: dbVersion,
          attribution: `GeoServer (${dbCRS} - 来自数据库)`,
          srs: dbCRS,
          exceptions: 'application/vnd.ogc.se_inimage',
          dpi: 96,
          styles: ''
        })
        
        // 添加事件监听
        newWmsLayer.on('load', () => {
          console.log(`✅ 都江堰图层使用数据库坐标系 ${dbCRS} 加载成功`)
          // ElMessage.success(`图层"${dujiangyanLayer.layer_name}"已使用数据库坐标系 ${dbCRS} 重新加载`) // 移除弹窗，避免干扰
          console.log(`✅ 图层"${dujiangyanLayer.layer_name}"已使用数据库坐标系 ${dbCRS} 重新加载`)
        })
        
        newWmsLayer.on('tileerror', (e) => {
          console.error(`❌ 数据库坐标系 ${dbCRS} 加载也失败:`, e)
          ElMessage.error(`使用数据库坐标系 ${dbCRS} 仍然无法加载图层，可能需要检查数据源`)
        })
        
        // 更新图层引用
        mapLayers.value[dujiangyanLayer.id] = newWmsLayer
        
        // 添加到地图
        if (dujiangyanLayer.visibility !== false) {
          newWmsLayer.addTo(map.value)
        }
        
        // 🔧 如果有数据库中心坐标，自动调整地图视图
        if (centerCoords && centerCoords.length >= 2) {
          setTimeout(() => {
            try {
              // 多重检查确保地图状态正常
              if (!map.value) {
                console.warn('⚠️ 地图对象为空，跳过视图调整')
                return
              }
              
              // 检查地图是否已完全初始化
              if (!map.value.getContainer() || !map.value.getSize()) {
                console.warn('⚠️ 地图容器未准备就绪，跳过视图调整')
                return
              }
              
              // 检查地图的坐标系是否正常
              if (!map.value.options.crs || !map.value.options.crs.project) {
                console.warn('⚠️ 地图坐标系未就绪，跳过视图调整')
                return
              }
              
              // 安全地设置视图
              console.log(`🎯 基于数据库中心坐标调整地图视图: [${centerCoords[0].toFixed(4)}, ${centerCoords[1].toFixed(4)}] zoom=${zoomLevel}`)
              
              map.value.setView(centerCoords, zoomLevel, {
                animate: false, // 禁用动画避免可能的冲突
                duration: 0
              })
              
              console.log(`🎯 地图视图已调整到数据库定义的图层范围 (${dbCRS})`)
              ElMessage.info(`地图视图已自动定位到"${dujiangyanLayer.layer_name}"图层范围（基于数据库信息）`)
              
            } catch (viewError) {
              console.error('❌ 设置地图视图时出错:', viewError)
              ElMessage.warning('图层已加载，但自动定位失败。请手动调整地图位置。')
            }
          }, 2000) // 增加延迟时间确保稳定性
        } else {
          // 如果没有数据库中心坐标，使用默认的都江堰坐标
          setTimeout(() => {
            try {
              if (!map.value) return
              
              // 使用GeoServer预览链接的bbox中心点作为备用
              const centerLng = (103.44123417062076 + 105.62364387846247) / 2
              const centerLat = (29.463131839962728 + 31.460939144026554) / 2
              const targetLatLng = [centerLat, centerLng]
              const targetZoom = 10
              
              map.value.setView(targetLatLng, targetZoom, {
                animate: false,
                duration: 0
              })
              
              console.log(`🎯 使用默认都江堰坐标调整地图视图: [${centerLat.toFixed(4)}, ${centerLng.toFixed(4)}]`)
              ElMessage.info('地图视图已调整到都江堰灌区范围（使用默认坐标）')
              
            } catch (viewError) {
              console.error('❌ 设置默认地图视图时出错:', viewError)
            }
          }, 2000)
        }
        
        console.log(`✅ 正在使用${dbCRS === 'EPSG:404000' ? '默认' : '数据库'}坐标系 ${dbCRS} 重新加载"${dujiangyanLayer.layer_name}"`)
        
      } catch (error) {
        console.error('❌ 智能修复失败:', error)
        ElMessage.error('智能修复失败: ' + error.message)
      }
    }
    
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
      panelCollapsed,
      togglePanel,
      getLayerStatusText,
      getLayerStatusClass,
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
      diagnoseMapLayers,
      getCurrentLayerInfo,
      resetAllLayersToDefault,
      fixDujiangyanCRS,
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
  min-height: 400px; /* 确保最小高度 */
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px; /* 确保最小高度 */
}

.layer-control-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 300px;
  max-height: calc(100% - 20px);
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  transition: all 0.3s ease;
}

.layer-control-panel.collapsed {
  width: 0;
  overflow: hidden;
}

.panel-toggle {
  position: absolute;
  top: 50%;
  left: -15px;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #dcdfe6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  z-index: 1002;
}

.panel-toggle:hover {
  background: #f5f7fa;
  box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.2);
  transform: scale(1.1);
}

.panel-toggle i {
  color: #606266;
  font-size: 14px;
}

.panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-header {
  padding: 15px;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.layer-list {
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}

.layer-item {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  transition: all 0.3s;
  cursor: pointer; /* 添加指针样式 */
  border: 2px solid transparent; /* 为活动状态预留边框 */
}

.layer-item:hover {
  background-color: #e6f1fc;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.layer-item.active {
  background-color: #e6f7ff;
  border-color: #1890ff;
  box-shadow: 0 2px 12px rgba(24, 144, 255, 0.2);
}

.layer-item.active .layer-name {
  color: #1890ff;
  font-weight: 600;
}

.layer-header {
  display: flex;
  align-items: center;
}

.layer-drag-handle {
  cursor: move;
  margin-right: 5px;
  color: #909399;
}

.layer-name {
  margin-left: 5px;
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layer-actions {
  display: flex;
}

.layer-info {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
}

.tag {
  font-size: 12px;
  background-color: #ecf5ff;
  color: #409eff;
  padding: 2px 6px;
  border-radius: 2px;
  margin-right: 5px;
  margin-bottom: 5px;
}

.tag.status-published {
  background-color: #f0f9ff;
  color: #67c23a;
}

.tag.status-unpublished {
  background-color: #fef0f0;
  color: #f56c6c;
}

.empty-layers {
  padding: 30px;
  text-align: center;
  color: #909399;
}

.empty-layers i {
  font-size: 40px;
  margin-bottom: 10px;
}

.dialog-content {
  min-height: 300px;
}

.style-dialog-content h4 {
  margin: 15px 0 10px;
  color: #606266;
}

.base-map-section {
  border-top: 1px solid #dcdfe6;
  padding: 10px;
  flex-shrink: 0;
}

/* 右上角球形展开按钮样式 */
.floating-panel-toggle {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px 0 rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
  backdrop-filter: blur(5px);
}

.floating-panel-toggle:hover {
  background: rgba(64, 158, 255, 0.1);
  box-shadow: 0 6px 20px 0 rgba(64, 158, 255, 0.4);
  transform: scale(1.1);
  border-color: #66b1ff;
}

.floating-panel-toggle .panel-ball {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px 0 rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;
}

.floating-panel-toggle:hover .panel-ball {
  background: linear-gradient(135deg, #66b1ff, #409eff);
  transform: rotate(180deg);
}

.floating-panel-toggle .panel-ball i {
  color: #fff;
  font-size: 16px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 添加图层对话框样式 */
.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.service-types {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.service-tag {
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 2px;
  line-height: 1.2;
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

.no-service {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
}

.no-service-text {
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

/* MVT图层弹窗样式 */
:deep(.mvt-popup-click .leaflet-popup-content-wrapper) {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #007bff;
}

:deep(.mvt-popup-click .leaflet-popup-content) {
  margin: 12px 16px;
  max-width: 300px;
  font-size: 13px;
  line-height: 1.4;
}

/* WMS图层弹窗样式 */
:deep(.wms-popup .leaflet-popup-content-wrapper) {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #52c41a;
}

:deep(.wms-popup .leaflet-popup-content) {
  margin: 12px 16px;
  max-width: 300px;
  font-size: 13px;
  line-height: 1.4;
}

:deep(.mvt-popup-click h4), :deep(.wms-popup h4) {
  color: #333 !important;
  margin: 0 0 8px 0 !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}

:deep(.mvt-popup-click strong), :deep(.wms-popup strong) {
  color: #666;
  font-weight: 500;
}

/* 确保Leaflet弹窗层级 */
:deep(.leaflet-popup-pane) {
  z-index: 1100 !important;
}

/* 诊断按钮样式 */
.map-diagnostic-button {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  padding: 5px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.debug-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  padding: 5px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.debug-panel .el-button-group {
  display: flex;
  gap: 5px;
}

.debug-panel .el-button {
  padding: 5px 10px;
  font-size: 12px;
}
</style>
