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
/* eslint-disable */
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import gisApi from '@/api/gis'
// OpenLayers 相关导入
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorTileLayer from 'ol/layer/VectorTile'
import { TileWMS, VectorTile, XYZ } from 'ol/source'
import { fromLonLat, transformExtent, transform } from 'ol/proj'
import * as projlv from 'ol/proj'
import Overlay from 'ol/Overlay'
import { Style, Fill, Stroke, Circle } from 'ol/style'
import { MVT } from 'ol/format'
import BaseMapSwitcherOL from './BaseMapSwitcherOL.vue'
import DxfStyleEditor from './DxfStyleEditor.vue'
import defaultDxfStylesConfig from '@/config/defaultDxfStyles.json'
// 引入proj4库用于坐标系转换
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'
// 引入ol-proj-ch库中的GCJ02坐标系
import  gcj02Mecator  from '@/utils/GCJ02'

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
    
    // 坐标系初始化状态
    const projectionsInitialized = ref(false)
    
    // 异步初始化坐标系
    const initializeProjections = async () => {
      if (!projectionsInitialized.value) {
        await initProjections()
        projectionsInitialized.value = true
      }
    }
    
    // 初始化坐标系
    const initProjections = async () => {
      try {
        //console.log('🔄 开始从后端获取坐标系定义...')
        
        // 从后端获取常用坐标系的proj4定义
        const response = await gisApi.getProj4Definitions()
        
        if (response.success && response.proj4_definitions) {
          // 注册投影定义
          Object.entries(response.proj4_definitions).forEach(([epsgCode, info]) => {
            if (info.proj4) {
              proj4.defs(epsgCode, info.proj4)
              //console.log(`✅ 注册坐标系: ${epsgCode} - ${info.name || '未知'}`)
            }
          })
          
          // 注册到OpenLayers
          register(proj4)
         
          //console.log(`✅ 坐标系初始化完成，共注册${Object.keys(response.proj4_definitions).length}个坐标系`)
          return true
        } else {
          throw new Error(response.message || '获取坐标系定义失败')
        }
        
      } catch (error) {
        console.warn('⚠️ 从后端获取坐标系定义失败，使用备用定义:', error.message)
        
        // 备用方案：使用硬编码的常用坐标系定义
        const fallbackProjections = {
          'EPSG:2379': '+proj=tmerc +lat_0=0 +lon_0=102 +k=1 +x_0=500000 +y_0=0 +ellps=IAU76 +towgs84=24,-123,-94,0,0,0,0 +units=m +no_defs +type=crs',
          'EPSG:2343': '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=15.8,-154.4,-82.3,0,0,0,0 +units=m +no_defs',
          'EPSG:2431': '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +datum=WGS84 +units=m +no_defs',
          'EPSG:4545': '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=15.8,-154.4,-82.3,0,0,0,0 +units=m +no_defs',
          'EPSG:4547': '+proj=tmerc +lat_0=0 +lon_0=102 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=15.8,-154.4,-82.3,0,0,0,0 +units=m +no_defs'
        }
        
        // 注册备用投影定义
        Object.entries(fallbackProjections).forEach(([code, def]) => {
          proj4.defs(code, def)
          //console.log(`⚠️ 备用注册坐标系: ${code}`)
        })
        
        // 注册到OpenLayers
        register(proj4)
        
        //console.log('⚠️ 坐标系初始化完成（使用备用定义）')
        return false
      }
    }
    
    // 动态注册单个坐标系
    const registerProjection = async (epsgCode) => {
      try {
        // 检查是否已经注册
        if (proj4.defs(epsgCode)) {
          //console.log(`✅ 坐标系 ${epsgCode} 已注册`)
          return true
        }
        
        //console.log(`🔄 动态获取坐标系定义: ${epsgCode}`)
        const response = await gisApi.getSingleProj4Definition(epsgCode)
        
        if (response.success && response.crs_info && response.crs_info.proj4_definition) {
          proj4.defs(epsgCode, response.crs_info.proj4_definition)
          register(proj4)
          //console.log(`✅ 动态注册坐标系: ${epsgCode} - ${response.crs_info.name || '未知'}`)
          return true
        } else {
          console.warn(`⚠️ 无法获取 ${epsgCode} 的proj4定义`)
          return false
        }
        
      } catch (error) {
        console.error(`❌ 动态注册坐标系 ${epsgCode} 失败:`, error.message)
        return false
      }
    }
    
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
    
    // 图层样式缓存
    const layerStyleCache = reactive({})
    
    // 初始化地图
    const initMap = () => {
      //console.log('=== 开始地图初始化 ===')
      
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
      //console.log('✅ 地图容器已找到:', mapContainer.value)
      
      // 3. 检查OpenLayers导入
      if (!Map || !View || !TileLayer || !XYZ) {
        console.error('❌ OpenLayers模块导入失败')
        //console.log('Map:', Map, 'View:', View, 'TileLayer:', TileLayer, 'XYZ:', XYZ)
        return
      }
      //console.log('✅ OpenLayers模块导入正常')
      
      try {
        // 4. 创建底图图层
        //console.log('创建底图图层...')
        // 创建GCJ02坐标系,对高德地图进行纠偏
        // const gcj02Extent = [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244];
        //   const gcjMecator = new projlv.Projection({
        //     code: "GCJ-02",
        //     extent: gcj02Extent,
        //     units: "m"
        //   });
        //   projlv.addProjection(gcjMecator);
 // 设置GCJ02的有效范围（基于中国区域）
        

        // 高德地图 - 使用GCJ02坐标系修正偏移
        const gaodeLayer = new TileLayer({
          source: new XYZ({
            url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            crossOrigin: 'anonymous',
            projection:  gcj02Mecator // 使用GCJ02坐标系
          }),
          visible: true
        })
        
        // 高德卫星地图 - 使用GCJ02坐标系修正偏移
        const gaodeSatelliteLayer = new TileLayer({
          source: new XYZ({
            url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
            crossOrigin: 'anonymous',
            projection: gcj02Mecator // 使用GCJ02坐标系
          }),
          visible: false
        })
        
        // OpenStreetMap
        const osmLayer = new TileLayer({
          source: new XYZ({
            url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            crossOrigin: 'anonymous'
          }),
          visible: false
        })
        
        // Esri 世界影像（卫星图）
        const esriSatelliteLayer = new TileLayer({
          source: new XYZ({
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            crossOrigin: 'anonymous'
          }),
          visible: false
        })
        
        //console.log('✅ 底图图层创建成功')
        
        // 5. 创建地图实例
        //console.log('创建地图实例...')
        map.value = new Map({
          target: mapContainer.value,
          layers: [gaodeLayer, gaodeSatelliteLayer, osmLayer, esriSatelliteLayer],
          view: new View({
            center: fromLonLat([104.0667, 30.6667]), // 成都坐标
            zoom: 10
          })
        })
        
        // 6. 设置底图引用供切换器使用
        map.value.baseLayers = {
          gaode: gaodeLayer,
          gaodeSatellite: gaodeSatelliteLayer,
          osm: osmLayer,
          esriSatellite: esriSatelliteLayer
        }
        
        //console.log('✅ 地图实例创建成功')
        
        // 7. 监听地图渲染
        map.value.once('rendercomplete', () => {
          //console.log('🎉 地图首次渲染完成！')
        })
        
        // 8. 延迟强制更新尺寸
        setTimeout(() => {
          if (map.value) {
            //console.log('强制更新地图尺寸...')
            map.value.updateSize()
          }
        }, 200)
        
        // 9. 初始化弹窗
        initializePopup()
        
        //console.log('=== 地图初始化完成 ===')
        
      } catch (error) {
        console.error('❌ 地图初始化失败:', error)
        console.error('错误堆栈:', error.stack)
      }
    }
    
    // 初始化弹窗 - 简化版本
    const initializePopup = () => {
      if (!map.value) return
      
      // 获取弹窗元素
      const container = document.getElementById('popup')
      const content = document.getElementById('popup-content')
      const closer = document.getElementById('popup-closer')
      
      if (!container || !content || !closer) {
        console.error('❌ 弹窗元素未找到')
        return
      }
      
      // 创建弹窗覆盖物
      popup.value = new Overlay({
        element: container,
        autoPan: {
          animation: {
            duration: 250,
          },
        },
      })
      
      // 添加到地图
      map.value.addOverlay(popup.value)
      
      // 关闭按钮事件
      closer.onclick = function () {
        popup.value.setPosition(undefined)
        closer.blur()
        return false
      }
      
      // 地图点击事件
      map.value.on('click', function (evt) {
        const coordinate = evt.coordinate
        const pixel = evt.pixel
        
        // 检查点击位置是否有要素
        const features = map.value.getFeaturesAtPixel(pixel)
        ////console.log('features',features)
        if (features && features.length > 0) {
          // 找到第一个要素
          const feature = features[0]
          
          // 找到要素所属的图层
          const targetLayer = map.value.forEachFeatureAtPixel(pixel, (feat, layer) => {
             if (feat === feature && layer && mvtLayers.value && Object.values(mvtLayers.value).includes(layer)) {
              //console.log('lv-targetLayer:', layer)
               return layer
             }
            
            return null
          })
          
          if (targetLayer) {
            // 显示弹窗
            showPopup(feature, targetLayer, coordinate, content)
          }
        } else {
          // 点击空白处，隐藏弹窗
          popup.value.setPosition(undefined)
        }
      })
      
      // 鼠标移动事件 - 改变鼠标样式
      map.value.on('pointermove', function (evt) {
        if (evt.dragging) return
        
        const pixel = evt.pixel
        const hasFeature = map.value.hasFeatureAtPixel(pixel, {
          layerFilter: (layer) => {
            // 只对MVT图层启用手型cursor
            return mvtLayers.value && Object.values(mvtLayers.value).includes(layer)
          }
        })
        
        // 改变鼠标样式
        map.value.getTargetElement().style.cursor = hasFeature ? 'pointer' : ''
      })
      
      //console.log('✅ 弹窗初始化完成')
    }
    
    // 显示弹窗 - 简化版本
    const showPopup = (feature, layer, coordinate, contentElement) => {
      if (!popup.value || !feature) return
      
      // 获取要素属性
      const properties = feature.getProperties()
      
      // 找到对应的图层信息
      const layerInfo = layer._layerInfo
      //console.log('lv-layer:', layer)
      //if (!layerInfo) return
      //console.log('layerInfo:', layerInfo)
      // 构建弹窗内容
      let content = `<div style="padding: 10px;">
        <h4 style="margin: 0 0 10px 0; color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px;">
          ${layerInfo.layer_name}
          <small style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 5px;">
            ${layerInfo.file_type?.toUpperCase() || 'MVT'}
          </small>
        </h4>`
      
      // 处理属性
      const filteredProperties = Object.entries(properties)
        .filter(([key, value]) => {
          // 排除几何相关和内部属性
          if (key === 'geometry' || key === 'geom') return false
          if (value == null || value === 'NULL' || value === '') return false
          if (typeof value === 'object') return false
          return true
        })
        //.slice(0, 6) // 限制为6个属性
      
      if (filteredProperties.length === 0) {
        content += '<div style="color: #999; font-style: italic;">暂无属性信息</div>'
      } else {
        filteredProperties.forEach(([key, value]) => {
          // 格式化属性名和值
          let displayKey = key.length > 15 ? key.substring(0, 15) + '...' : key
          let displayValue = String(value).length > 30 ? String(value).substring(0, 30) + '...' : value
          
          // 特殊格式化数字
          if (typeof value === 'number' && value % 1 !== 0) {
            displayValue = Number(value).toFixed(3)
          }
          
          content += `
            <div style="margin-bottom: 8px; display: flex;">
              <span style="color: #666; margin-right: 10px; min-width: 80px; font-weight: 500;">${displayKey}：</span>
              <span style="color: #333; flex: 1;">${displayValue}</span>
            </div>
          `
        })
        
        const totalProperties = Object.keys(properties).length - 2 // 排除geometry等
        if (totalProperties > 6) {
          content += `<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; color: #999; font-style: italic; font-size: 12px; text-align: center;">共 ${totalProperties} 个属性</div>`
        }
      }
      
      content += '</div>'
      
      // 设置内容和位置
      contentElement.innerHTML = content
      popup.value.setPosition(coordinate)
      
      //console.log('🎯 显示弹窗:', layerInfo.layer_name)
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
        //console.log('开始加载场景:', sceneId)
        const response = await gisApi.getScene(sceneId)
        currentScene.value = response.scene
        layersList.value = response.layers
        
        //console.log('场景数据加载完成，图层数量:', layersList.value.length)
        
        // 清除现有图层
        clearAllLayers()
        
        // 添加新图层
        for (const layer of layersList.value) {
          //console.log('lvlayertype:', layer)
          if (layer.service_type === 'martin') {
            
            await addMartinLayer(layer)
          } else {
            await addGeoServerLayer(layer)
          }
        }
        
        //console.log('✅ 场景加载完成:', response.scene?.name)
        
      } catch (error) {
        console.error('加载场景失败:', error)
        ElMessage.error(`加载场景失败: ${error.message}`)
      }
    }
    
    // 添加Martin图层
    const addMartinLayer = async (layer) => {
      
      if (!layer.mvt_url) {
        console.warn('MVT URL不存在，跳过图层:', layer.layer_name)
        return
      }
      
      // 检查地图实例是否存在
      if (!map.value) {
        console.error('地图实例不存在，无法添加Martin图层:', layer.layer_name)
        return
      }

      let mvtUrl = layer.mvt_url
      if (mvtUrl.includes('localhost:3000')) {
        // 检查是否是 MBTiles 服务
        if (layer.file_type === 'mbtiles' || mvtUrl.includes('/mbtiles/')) {
          // MBTiles 服务格式：http://localhost:3000/mbtiles/{文件名}/{z}/{x}/{y}
          const mbtilesMatch = mvtUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
          const fileName = mbtilesMatch[1] || 'default'
          mvtUrl = `http://localhost:3000/${fileName}/{z}/{x}/{y}`
        } else {
          // 普通 Martin 服务格式：http://localhost:3000/{tableName}/{z}/{x}/{y}
          const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
          mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
        }
      }

     
      let layerStyleConfig = layerStyleCache[layer.id] || {}
      
      // 如果是DXF文件且没有缓存样式，使用默认DXF样式
      if (layer.file_type === 'dxf' && Object.keys(layerStyleConfig).length === 0) {
        //console.log('使用默认DXF样式配置')
        layerStyleConfig = defaultDxfStylesConfig.defaultDxfStyles
      }
            

      // 创建样式函数 - 重新设计的版本
      const createStyleFunction = () => {
        const isDxf = layer.file_type === 'dxf'
        const defaultStyles = isDxf ? defaultDxfStylesConfig.defaultDxfStyles : {}
        
        // 样式缓存，提高性能
        const styleCache = {}
        
        return (feature) => {
          const properties = feature.getProperties()
          ////console.log('properties',properties)
          const geometryType = feature.getGeometry().getType()
          
          // 🔧 解决MVT layer属性冲突问题 - 后端方案
          // 现在在后端ogr2ogr导入时已将DXF的layer字段重命名为cad_layer字段
          // 这样避免了与MVT规范的layer属性（表名）冲突
          
          let dxfLayerName = null
          let useLayerBasedStyle = false
          
          // 查找DXF图层名称 - 现在使用专门的cad_layer字段
          const isDxf = layer.file_type === 'dxf'
          
          // 优先查找cad_layer字段（后端已重命名）
          if (properties.cad_layer && 
              typeof properties.cad_layer === 'string' && 
              properties.cad_layer.trim() !== '') {
            dxfLayerName = properties.cad_layer.trim()
            useLayerBasedStyle = true
            //console.log(`✅ 找到CAD图层名称: "${dxfLayerName}" (来源: cad_layer字段)`)
          }
          // 备用：检查其他可能的字段名（兼容旧数据）
          else if (isDxf) {
            const fallbackFields = ['layer_name', 'dxf_layer', 'subclasses', 'layername', 'entity_layer']
            
            for (const fieldName of fallbackFields) {
              const fieldValue = properties[fieldName]
              
              if (fieldValue && 
                  typeof fieldValue === 'string' && 
                  fieldValue.trim() !== '' &&
                  !fieldValue.includes('vector_') && 
                  !fieldValue.includes('table_') &&
                  !fieldValue.match(/^[a-f0-9]{8,}$/)) {
                    
                dxfLayerName = fieldValue.trim()
                useLayerBasedStyle = true
                //console.log(`⚠️ 使用备用字段获取图层名称: "${dxfLayerName}" (来源: ${fieldName}字段)`)
                break
              }
            }
          }
          
         
          
          // 样式策略1：DXF图层 - 根据是否找到图层名称决定样式方式
          if (isDxf) {
            if (dxfLayerName) {
              // 找到了DXF图层名称，使用图层匹配样式
              const cacheKey = `dxf_layer_${dxfLayerName}_${geometryType}`
              if (styleCache[cacheKey]) {
                return styleCache[cacheKey]
              }
              
              // 获取图层特定样式：优先使用用户自定义样式，其次使用默认样式
              const layerSpecificStyle = layerStyleConfig[dxfLayerName] || defaultStyles[dxfLayerName] || {}
              
              // 如果没有找到匹配的样式配置，使用通用默认样式
              const finalStyle = Object.keys(layerSpecificStyle).length > 0 ? layerSpecificStyle : {
                weight: 1,
                color: '#666666',
                opacity: 0.8,
                fillColor: '#CCCCCC',
                fill: false,
                fillOpacity: 0.3,
                radius: 3,
                visible: true
              }
              
              //console.log(`🎨 使用DXF图层样式: ${dxfLayerName} (${geometryType})`, finalStyle)
              
              let style = createStyleFromConfig(finalStyle, geometryType)
              
              // 处理图层可见性
              if (finalStyle.visible === false) {
                style = new Style({}) // 返回空样式以隐藏
              }
              
              // 缓存样式
              styleCache[cacheKey] = style
              return style
            } else {
              // 没有找到DXF图层名称，使用DXF通用默认样式
              const cacheKey = `dxf_default_${geometryType}`
              if (styleCache[cacheKey]) {
                return styleCache[cacheKey]
              }
              
              // 使用DXF通用默认样式
              const defaultStyle = {
                weight: 1,
                color: '#888888',
                opacity: 0.8,
                fillColor: '#DDDDDD',
                fill: false,
                fillOpacity: 0.3,
                radius: 3,
                visible: true
              }
              
              //console.log(`🎨 使用DXF通用默认样式 (${geometryType})`, defaultStyle)
              
              let style = createStyleFromConfig(defaultStyle, geometryType)
              styleCache[cacheKey] = style
              return style
            }
          }
          
          // 样式策略2：非DXF图层但有图层字段的矢量切片图层 - 使用layer字段匹配样式
          else if (useLayerBasedStyle && dxfLayerName) {
            // 创建缓存键
            const cacheKey = `layer_${dxfLayerName}_${geometryType}`
            if (styleCache[cacheKey]) {
              return styleCache[cacheKey]
            }
            
            // 获取图层特定样式：优先使用用户自定义样式，其次使用默认样式
            const layerSpecificStyle = layerStyleConfig[dxfLayerName] || defaultStyles[dxfLayerName] || {}
            
            // 如果没有找到匹配的样式配置，使用通用默认样式
            const finalStyle = Object.keys(layerSpecificStyle).length > 0 ? layerSpecificStyle : {
              weight: 1,
              color: '#666666',
              opacity: 0.8,
              fillColor: '#CCCCCC',
              fill: false,
              fillOpacity: 0.3,
              radius: 3,
              visible: true
            }
            
            //console.log(`🎨 使用layer字段样式: ${dxfLayerName} (${geometryType})`, finalStyle)
            
            let style = createStyleFromConfig(finalStyle, geometryType)
            
            // 处理图层可见性
            if (finalStyle.visible === false) {
              style = new Style({}) // 返回空样式以隐藏
            }
            
            // 缓存样式
            styleCache[cacheKey] = style
            return style
          }
          
          // 样式策略3：没有layer字段的图层 - 使用基础点线面样式
          else {
            // 创建缓存键
            const cacheKey = `basic_${geometryType}`
            if (styleCache[cacheKey]) {
              return styleCache[cacheKey]
            }
            
            // 获取基础样式配置（从样式面板的表单配置）
            const basicStyles = {
              point: styleForm.point || { color: '#FF0000', size: 6 },
              line: styleForm.line || { color: '#0000FF', width: 2 },
              polygon: styleForm.polygon || { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
            }
            
            //console.log(`🎨 使用基础几何样式: ${geometryType}`, basicStyles)
            
            let style
            if (geometryType === 'Point' || geometryType === 'MultiPoint') {
              style = new Style({
                image: new Circle({
                  radius: basicStyles.point.size || 6,
                  fill: new Fill({
                    color: basicStyles.point.color || '#FF0000'
                  }),
                  stroke: new Stroke({
                    color: '#FFFFFF',
                    width: 1
                  })
                })
              })
            } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
              style = new Style({
                stroke: new Stroke({
                  color: basicStyles.line.color || '#0000FF',
                  width: basicStyles.line.width || 2
                })
              })
            } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
              const fillColor = basicStyles.polygon.fillColor || '#00FF00'
              const fillOpacity = basicStyles.polygon.fillOpacity !== undefined ? basicStyles.polygon.fillOpacity : 0.3
              
              // 转换颜色和透明度
              let finalFillColor = fillColor
              if (fillOpacity !== 1 && fillColor.startsWith('#')) {
                const r = parseInt(fillColor.slice(1, 3), 16)
                const g = parseInt(fillColor.slice(3, 5), 16)
                const b = parseInt(fillColor.slice(5, 7), 16)
                finalFillColor = `rgba(${r}, ${g}, ${b}, ${fillOpacity})`
              }
              
              style = new Style({
                stroke: new Stroke({
                  color: basicStyles.polygon.outlineColor || '#000000',
                  width: 1
                }),
                fill: new Fill({
                  color: finalFillColor
                })
              })
            } else {
              // 默认样式
              style = new Style({
                stroke: new Stroke({
                  color: '#0066cc',
                  width: 2
                }),
                fill: new Fill({
                  color: 'rgba(102, 204, 255, 0.3)'
                }),
                image: new Circle({
                  radius: 4,
                  fill: new Fill({
                    color: '#66ccff'
                  }),
                  stroke: new Stroke({
                    color: '#0066cc',
                    width: 1
                  })
                })
              })
            }
            
            // 缓存样式
            styleCache[cacheKey] = style
            return style
          }
        }
      }
      
      // 样式配置转换为OpenLayers样式的辅助函数
      const createStyleFromConfig = (styleConfig, geometryType) => {
        if (geometryType === 'Point' || geometryType === 'MultiPoint') {
          // 点样式
          return new Style({
            image: new Circle({
              radius: styleConfig.radius || 4,
              fill: new Fill({
                color: styleConfig.fillColor || styleConfig.color || '#66ccff'
              }),
              stroke: new Stroke({
                color: styleConfig.color || '#0066cc',
                width: 1
              })
            })
          })
        } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
          // 线样式
          const dashArray = styleConfig.dashArray
          return new Style({
            stroke: new Stroke({
              color: styleConfig.color || '#0066cc',
              width: styleConfig.weight || 2,
              lineDash: dashArray ? dashArray.split(',').map(Number) : undefined
            })
          })
        } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
          // 面样式
          const fillColor = styleConfig.fillColor || styleConfig.color || '#66ccff'
          const fillOpacity = styleConfig.fillOpacity !== undefined ? styleConfig.fillOpacity : 0.3
          
          // 转换颜色和透明度
          let finalFillColor = fillColor
          if (fillOpacity !== 1 && fillColor.startsWith('#')) {
            const r = parseInt(fillColor.slice(1, 3), 16)
            const g = parseInt(fillColor.slice(3, 5), 16)
            const b = parseInt(fillColor.slice(5, 7), 16)
            finalFillColor = `rgba(${r}, ${g}, ${b}, ${fillOpacity})`
          }
          
          return new Style({
            stroke: new Stroke({
              color: styleConfig.color || '#0066cc',
              width: styleConfig.weight || 1
            }),
            fill: styleConfig.fill !== false ? new Fill({
              color: finalFillColor
            }) : undefined
          })
        } else {
          // 默认样式
          return new Style({
            stroke: new Stroke({
              color: styleConfig.color || '#0066cc',
              width: styleConfig.weight || 2
            }),
            fill: new Fill({
              color: styleConfig.fillColor || styleConfig.color || '#66ccff'
            }),
            image: new Circle({
              radius: styleConfig.radius || 4,
              fill: new Fill({
                color: styleConfig.fillColor || styleConfig.color || '#66ccff'
              }),
              stroke: new Stroke({
                color: styleConfig.color || '#0066cc',
                width: 1
              })
            })
          })
        }
      }
      
      try {
        // 检查是否为栅格mbtiles
        const isRasterMbtiles = layer.file_type === 'raster.mbtiles';
        
        let olLayer;
        
        if (isRasterMbtiles) {
          // 创建栅格XYZ图层 - 用于栅格mbtiles
          olLayer = new TileLayer({
            source: new XYZ({
              url: mvtUrl,
              maxZoom: 22,
              minZoom: 0,
              wrapX: false,
              transition: 0,
              attributions: layer.attribution || [],
              cacheSize: 256
            }),
            opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
            visible: layer.visibility !== false,
            zIndex: layer.zIndex || 1,
            properties: {
              layerId: layer.id,
              layerName: layer.layer_name,
              serviceType: 'martin',
              fileType: layer.file_type
            }
          });
          
          console.log('创建栅格MBTiles图层:', layer.layer_name);
        } else {

          
          // 创建矢量切片图层 - 用于矢量mbtiles和其他矢量数据
          olLayer = new VectorTileLayer({
            declutter: true, // 启用标注防冲突
            source: new VectorTile({
              format: new MVT(),
              url: mvtUrl,
              maxZoom: 22, // 最大缩放级别
              minZoom: 0,  // 最小缩放级别
              wrapX: false, // 防止世界重复
              transition: 0, // 禁用过渡动画，提高性能
              // 添加属性信息
              attributions: layer.attribution || [],
              // 设置瓦片缓存大小
              cacheSize: 128
            }),
            style: createStyleFunction(),
            opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
            visible: layer.visibility !== false,
            // 设置渲染顺序
            zIndex: layer.zIndex || 1,
            // 添加图层标识
            properties: {
              layerId: layer.id,
              layerName: layer.layer_name,
              serviceType: 'martin',
              fileType: layer.file_type
            }
          });
          
          console.log('创建矢量MBTiles图层:', layer.layer_name);
        }
        
        // 使用统一变量名
        const mvtLayer = olLayer;
        
        // 启用弹窗交互
        mvtLayer._popupEnabled = true
        mvtLayer._layerInfo = layer
        
        // 存储图层引用
        mvtLayers.value[layer.id] = mvtLayer
        
        // 添加到地图（如果图层可见）
        if (layer.visibility !== false && map.value) {
          map.value.addLayer(mvtLayer)
          //console.log('✅ MVT图层添加成功:', layer.layer_name)
        }
        
        // 添加图层事件监听 - 改进版本
        const source = mvtLayer.getSource()
        
        // 瓦片加载错误处理
        source.on('tileloaderror', (evt) => {
          console.warn('MVT瓦片加载失败:', evt.tile.src_)
          console.warn('错误详情:', evt)
          
          // 可以在这里添加重试逻辑
          if (evt.tile.getState() === 3) { // ERROR state
            setTimeout(() => {
              //console.log('重试加载MVT瓦片:', evt.tile.src_)
              evt.tile.load()
            }, 1000)
          }
        })
        
        // 瓦片加载成功
        source.on('tileloadend', (evt) => {
          //console.log('MVT瓦片加载完成:', evt.tile.src_)
        })
        
        // 瓦片开始加载
        source.on('tileloadstart', (evt) => {
          console.debug('MVT瓦片开始加载:', evt.tile.src_)
        })
        
        // 监听源变化
        source.on('change', () => {
          console.debug('MVT源状态变化:', source.getState())
        })
        
        return mvtLayer
        
      } catch (error) {
        console.error('创建MVT图层失败:', error)
        console.error('错误详情:', {
          layerName: layer.layer_name,
          mvtUrl: mvtUrl,
          error: error.message,
          stack: error.stack
        })
        ElMessage.error(`MVT图层创建失败: ${layer.layer_name} - ${error.message}`)
        throw error
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
      
      //console.log('创建WMS图层:', layer.layer_name, 'URL:', wmsUrl)
      
      // 获取图层坐标系信息
      let layerCRS = 'EPSG:4326' // 默认坐标系
      let wmsVersion = '1.1.1' // 默认版本
      let crsParam = 'SRS' // 默认使用SRS参数
      
      try {
        // 确保坐标系已初始化
        //await initializeProjections()
        // 尝试获取图层的坐标系信息
        if (layer.layer_id) {
          const response = await gisApi.getLayerCRSInfo(layer.layer_id)
          if (response.success && response.crs_info) {
            layerCRS = response.crs_info.epsg_code || layerCRS
            //console.log(`✅ 获取到图层坐标系: ${layerCRS}`)
            
            // 动态注册坐标系（如果需要）
            if (response.crs_info.proj4_definition) {
              //console.log(`🔄 动态注册坐标系: ${layerCRS}`)
              proj4.defs(layerCRS, response.crs_info.proj4_definition)
              register(proj4)
              //console.log(`✅ 坐标系注册完成: ${layerCRS}`)
            }
            
            // 使用推荐的WMS版本
            wmsVersion = response.crs_info.recommended_wms_version || wmsVersion
          }
        }
        
        // 根据坐标系调整WMS参数
        if (layerCRS.startsWith('EPSG:')) {
          // 对于投影坐标系，使用WMS 1.1.0和SRS参数
          if (!layerCRS.includes('4326') && !layerCRS.includes('3857')) {
            wmsVersion = '1.1.0'
            crsParam = 'SRS'
          } else {
            // 对于地理坐标系，使用WMS 1.1.1和SRS参数
            wmsVersion = '1.1.1'
            crsParam = 'SRS'
          }
        }
        
      } catch (error) {
        console.warn('获取图层坐标系失败，使用默认值:', error.message)
      }
      
      try {
        // 构建WMS参数
        const wmsParams = {
          'LAYERS': layer.geoserver_layer,
          'FORMAT': 'image/png',
          'TRANSPARENT': true,
          'VERSION': wmsVersion,
          'STYLES': '',
          'TILED': true
        }
        
        // 设置坐标系参数
        wmsParams[crsParam] = layerCRS
        //console.log('lv-projection:', wmsParams)
        const wmsLayer = new TileLayer({
          source: new TileWMS({
            url: wmsUrl,
            params: wmsParams,
            projection: layerCRS, // 明确指定WMS源数据的投影
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
          //console.log(`✅ WMS图层添加成功: ${layer.layer_name} (坐标系: ${layerCRS})`)
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
        
        //console.log('✅ 所有图层已清除')
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
      
      // 如果是DXF Martin图层，在对话框打开后应用一次面板样式
      if (isDxfMartinLayer.value && layer.martin_service_id) {
        await nextTick() // 等待DOM更新
        
        // 等待DxfStyleEditor组件加载完成
        // 由于DxfStyleEditor在初始化时会自动触发styles-updated事件
        // 这里不需要手动获取和应用样式，让组件自己处理
        //console.log('DXF样式对话框已打开，等待DxfStyleEditor组件初始化...')
      }
    }
    
    // 应用样式
    const applyStyle = async () => {
      if (!currentStyleLayer.value) return
      
      const styleConfig = isVectorLayer.value 
        ? { point: { ...styleForm.point }, line: { ...styleForm.line }, polygon: { ...styleForm.polygon } }
        : { raster: { ...styleForm.raster } }
      
      // 将样式配置保存到缓存中，供重新加载图层时使用
      layerStyleCache[currentStyleLayer.value.id] = styleConfig
      
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
            layer_id: martinService.database_record_id || martinService.id,
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
    
    // 底图切换处理
    const onBaseMapChanged = (baseMapType) => {
      //console.log('切换底图到:', baseMapType)
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
    const onDxfStylesUpdated = async (styleData) => {
      //console.log('接收到DXF样式更新:', styleData)
      
      if (!currentStyleLayer.value || currentStyleLayer.value.service_type !== 'martin') {
        console.warn('当前图层不是Martin图层，无法应用DXF样式')
        return
      }
      
      // 动态应用样式到图层
      await applyDxfStylesToLayer(currentStyleLayer.value, styleData.allStyles || { [styleData.layerName]: styleData.style })
    }
    
    // 应用DXF样式到图层
    const applyDxfStylesToLayer = async (layer, styleConfig) => {
      if (!layer || !layer.martin_service_id || !styleConfig) {
        console.warn('参数不完整，无法应用DXF样式')
        return
      }
      
      try {
        //console.log('应用DXF样式到图层:', layer.layer_name, styleConfig)
        
        // 获取现有的MVT图层
        const existingMvtLayer = mvtLayers.value[layer.id]
        
        if (existingMvtLayer) {
          // 移除现有图层
          map.value.removeLayer(existingMvtLayer)
          delete mvtLayers.value[layer.id]
          
          // 缓存样式配置
          layerStyleCache[layer.id] = styleConfig
          
          // 重新创建并添加图层
          await addMartinLayer(layer)
          
          //console.log('DXF样式已应用到图层:', layer.layer_name)
        } else {
          console.warn('未找到要更新样式的MVT图层:', layer.layer_name)
        }
      } catch (error) {
        console.error('应用DXF样式失败:', error)
        ElMessage.error('应用DXF样式失败: ' + error.message)
      }
    }
    
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
    
    // 获取图层坐标系信息
    const getLayerCRSInfo = async (layer) => {
      try {
        if (layer.file_id) {
          const response = await gisApi.getLayerCRSInfo(layer.file_id)
          if (response.success && response.crs_info) {
            return {
              epsgCode: response.crs_info.epsg_code || 'EPSG:4326',
              proj4Def: response.crs_info.proj4_definition || null,
              name: response.crs_info.name || '未知坐标系'
            }
          }
        }
        
        // 从图层属性中获取
        const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
        if (targetLayer && targetLayer.get('properties')) {
          const props = targetLayer.get('properties')
          return {
            epsgCode: props.originalCRS || 'EPSG:4326',
            proj4Def: null,
            name: props.originalCRS || 'EPSG:4326'
          }
        }
        
        return {
          epsgCode: 'EPSG:4326',
          proj4Def: null,
          name: 'WGS84'
        }
      } catch (error) {
        console.warn('获取图层坐标系信息失败:', error.message)
        return {
          epsgCode: 'EPSG:4326',
          proj4Def: null,
          name: 'WGS84 (默认)'
        }
      }
    }
    
    // 坐标转换辅助函数
    const transformCoordinates = (coordinates, fromCRS, toCRS) => {
      try {
        if (fromCRS === toCRS) {
          return coordinates
        }
        
        // 如果是范围（4个数值），使用transformExtent
        if (Array.isArray(coordinates) && coordinates.length === 4) {
          return transformExtent(coordinates, fromCRS, toCRS)
        }
        
        // 如果是点坐标（2个数值），使用transform
        if (Array.isArray(coordinates) && coordinates.length === 2) {
          return transform(coordinates, fromCRS, toCRS)
        }
        
        return coordinates
      } catch (error) {
        console.error(`坐标转换失败: ${fromCRS} -> ${toCRS}`, error)
        return coordinates
      }
    }
    
    onMounted(() => {
      nextTick(async () => {
        // 增加一个小延迟确保DOM完全渲染
        setTimeout(async () => {
          //console.log('DOM准备就绪，开始初始化...')
          
          try {
            // 首先初始化坐标系
            await initializeProjections()
            
            // 然后初始化地图
            initMap()
            
            // 强制更新地图尺寸
            if (map.value) {
              // 使用requestAnimationFrame确保DOM完全渲染后再更新尺寸
              requestAnimationFrame(() => {
                setTimeout(() => {
                  if (map.value) {
                    map.value.updateSize()
                    //console.log('地图尺寸已更新')
                  }
                }, 100)
              })
            }
            
            const sceneId = props.sceneId || route.query.scene_id
            if (sceneId) {
              setTimeout(() => loadScene(sceneId), 300)
            }
          } catch (error) {
            console.error('地图初始化过程中出错:', error)
          }
        }, 100) // 增加延迟时间
      })
    })
    
    onUnmounted(() => {
      // 清理弹窗
      if (popup.value) {
        map.value?.removeOverlay(popup.value)
      }
      
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
      bringLayerToTop,
      getLayerCRSInfo,
      transformCoordinates,
      initializeProjections,
      registerProjection,
      projectionsInitialized,
      layerStyleCache,
      applyDxfStylesToLayer,
      popup
    }
  },
  expose: ['showStyleDialog', 'showAddLayerDialog', 'toggleLayerVisibility', 'map', 'bringLayerToTop', 'setActiveLayer', 'currentActiveLayer', 'getLayerCRSInfo', 'transformCoordinates', 'initializeProjections', 'registerProjection', 'projectionsInitialized', 'applyDxfStylesToLayer']
}
</script>

<style scoped>
.map-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #e0e0e0; /* 调试背景色 */
  overflow: hidden;
  contain: layout style; /* CSS containment 优化 */
}

.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  background-color: #f5f5f5; /* 添加背景色以便调试 */
  min-height: 0; /* 防止flex容器高度计算问题 */
  contain: layout style; /* CSS containment 优化 */
  border: none; /* 移除调试边框 */
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
  max-width: 400px;
}

.ol-popup:after, 
.ol-popup:before {
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
  color: #333;
  font-size: 16px;
  font-weight: bold;
}

.ol-popup-closer:after {
  content: "✖";
}

.ol-popup-closer:hover {
  color: #666;
}

#popup-content {
  max-height: 300px;
  overflow-y: auto;
}
</style> 