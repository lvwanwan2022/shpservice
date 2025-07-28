<template>
  <div class="map-container">
    <!-- Deck.gl 地图容器 -->
    <div ref="mapContainer" class="deckgl-map"></div>
    
    <!-- 地图控制器 - 参考OpenLayers的实现 -->
    <div class="map-controls">
      <!-- 底图切换器 -->
      <BaseMapSwitcherDeckGL 
        :current-base-map="currentBaseMap"
        @base-map-change="onBaseMapChange"
      />
      
      <!-- 刷新按钮 - 参考OpenLayers的刷新按钮 -->
      <el-tooltip content="刷新图层" placement="left" :show-after="500" :hide-after="1000">
        <el-button 
          type="success" 
          circle 
          size="small" 
          @click="refreshMap"
          :loading="refreshing"
          class="refresh-button"
        >
          <svg t="1752031016790" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="5670" width="16" height="16">
            <path d="M1023.99872 479.424681V25.601248l-133.119834 129.919838A520.639349 520.639349 0 0 0 518.591352 0.00128C232.12771 0.00128 0 229.312993 0 512.00064s232.12771 511.99936 518.655352 511.99936c198.783752 0 371.199536-110.399862 458.367427-272.25566h-193.791758a359.87155 359.87155 0 0 1-264.575669 114.687857c-198.271752 0-359.039551-158.719802-359.039552-354.431557 0-195.775755 160.767799-354.431557 359.039552-354.431557 101.567873 0 193.279758 41.727948 258.559676 108.607864L558.655302 479.424681H1023.99872z" fill="#2c2c2c" p-id="5671"></path>
          </svg>
        </el-button>
      </el-tooltip>
      
      <!-- 缓存控制按钮 - 参考OpenLayers的缓存按钮 -->
      <el-tooltip :content="layersCacheEnabled ? '关闭缓存' : '开启缓存'" placement="left" :show-after="500" :hide-after="1000">
        <el-button 
          :type="layersCacheEnabled ? 'warning' : 'info'" 
          circle 
          size="small" 
          @click="toggleLayersCache"
          class="cache-toggle-button"
        >
          <svg :class="layersCacheEnabled ? 'el-icon-folder-opened' : 'el-icon-folder'" t="1752031063403" class="icon" viewBox="0 0 1026 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="7600" width="16" height="16">
            <path d="M767.66305 531.384715l-236.251012 236.251011h-36.395426l-236.251012-236.251011L340.176422 449.973893 449.107294 559.47943V257.780503h127.703249v301.698927l109.505537-109.505537z m159.629062 279.542413l-92.137895-92.137894a395.880074 395.880074 0 1 0-204.325199 157.011145l99.161573 99.161573a511.834624 511.834624 0 1 1 197.429224-164.034824z" p-id="7601"></path>
          </svg>
        </el-button>
      </el-tooltip>
      
      <!-- 用户定位按钮 - 参考OpenLayers的定位按钮 -->
      <el-tooltip :content="userLocationVisible ? '关闭定位' : '我的位置'" placement="left" :show-after="500" :hide-after="1000">
        <el-button 
          :type="userLocationVisible ? 'primary' : 'info'" 
          circle 
          size="small" 
          @click="toggleUserLocation"
          :loading="locationLoading"
          class="location-button"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M3.05,13H1V11H3.05C3.5,6.83 6.83,3.5 11,3.05V1H13V3.05C17.17,3.5 20.5,6.83 20.95,11H23V13H20.95C20.5,17.17 17.17,20.5 13,20.95V23H11V20.95C6.83,20.5 3.5,17.17 3.05,13M12,5A7,7 0 0,0 5,12A7,7 0 0,0 12,19A7,7 0 0,0 19,12A7,7 0 0,0 12,5Z"/>
          </svg>
        </el-button>
      </el-tooltip>
    </div>
    
    <!-- 右下角信息面板 - 参考OpenLayers的信息面板 -->
    <div class="map-info-panel">
      <!-- 坐标信息 -->
      <div class="coordinate-info" v-if="mouseCoordinates">
        <span class="coordinate-text">{{ mouseCoordinates.lon }}°, {{ mouseCoordinates.lat }}°</span>
      </div>
      
      <!-- 版权信息 -->
      <div class="copyright-info">
        <span v-if="currentBaseMapAttribution" v-html="currentBaseMapAttribution"></span>
        <span v-else>© Deck.gl</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Deck } from '@deck.gl/core'
import { TileLayer } from '@deck.gl/geo-layers'
import { BitmapLayer } from '@deck.gl/layers'
// 导入MVT支持
import { MVTLayer } from '@deck.gl/geo-layers'
// 导入地形支持
import { TerrainLayer } from '@deck.gl/geo-layers'
// 导入TerrainExtension用于将2D图层贴合到3D地形
import { _TerrainExtension as TerrainExtension } from '@deck.gl/extensions'
// 导入ScatterplotLayer用于用户位置标记
import { ScatterplotLayer } from '@deck.gl/layers'
import BaseMapSwitcherDeckGL from './BaseMapSwitcherDeckGL.vue'
// 导入Martin配置 - 参考OpenLayers的配置导入
import { MARTIN_BASE_URL } from '@/config/index'
// 导入DXF样式配置 - 参考OpenLayers的DXF样式实现
import defaultDxfStylesConfig from '@/config/defaultDxfStyles.json'

export default {
  name: 'MapViewerDeckGL',
  components: {
    BaseMapSwitcherDeckGL
  },
  props: {
    layers: {
      type: Array,
      default: () => []
    },
    initialView: {
      type: Object,
      default: () => ({
        //[104.0667, 30.6667]), // 成都坐标
        longitude: 104.0667,
        latitude: 30.6667,
        zoom: 10
      })
    }
  },
  emits: ['map-ready', 'layer-click', 'view-change'],
  setup(props, { emit }) {
    const mapContainer = ref(null)
    const deckgl = ref(null)
    const refreshing = ref(false)
    const locating = ref(false)
    
    // 新增响应式变量 - 参考OpenLayers的实现
    const layersCacheEnabled = ref(false) // 缓存状态
    const locationLoading = ref(false) // 定位加载状态
    const userLocationVisible = ref(false) // 用户位置可见状态
    const currentBaseMapAttribution = ref('') // 底图版权信息
    const userLocationCoords = ref(null) // 用户位置坐标
    
    // 鼠标坐标
    const mouseCoordinates = reactive({
      lon: 0,
      lat: 0
    })
    
    // 自定义tooltip状态
    const tooltipState = ref({
      visible: false,
      content: '',
      x: 0,
      y: 0,
      timeout: null
    })
    
    // 当前底图 - 参考OpenLayers的配置，支持三维模式
    const currentBaseMap = ref({
      key: 'gaode',
      name: '高德地图',
      url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
      attribution: '© 高德地图',
      is3D: false
    })
    


    // 初始化Deck.gl地图
    const initDeckGL = () => {
      if (!mapContainer.value) return

      try {
        // 确保容器样式正确
        mapContainer.value.style.position = 'relative'
        mapContainer.value.style.width = '100%'
        mapContainer.value.style.height = '100%'
        mapContainer.value.style.overflow = 'hidden'
        console.log('容器尺寸:', mapContainer.value.getBoundingClientRect())
        
        deckgl.value = new Deck({
          container: mapContainer.value,
          width: mapContainer.value.clientWidth,
          height: mapContainer.value.clientHeight,
          style: {
            position: 'relative',
            width: '100%',
            height: '100%'
          },
          initialViewState: {
            longitude: props.initialView.longitude,
            latitude: props.initialView.latitude,
            zoom: props.initialView.zoom,
            pitch: 0,
            bearing: 0
          },
          // 完全启用控制器，允许所有交互
          controller: {
            inertia: true,
            scrollZoom: true,
            dragPan: true,
            dragRotate: true,
            doubleClickZoom: true,
            touchZoom: true,
            touchRotate: true,
            keyboard: true
          },
          layers: [createBaseMapLayer()],
          onViewStateChange: ({ viewState }) => {
            emit('view-change', viewState)
          },
          onHover: (info) => {
            try {
              updateMouseCoordinates(info)
              
              // 清除之前的定时器
              if (tooltipState.value.timeout) {
                clearTimeout(tooltipState.value.timeout)
                tooltipState.value.timeout = null
              }
              
              if (info.object && info.object.properties) {
                // 有要素时显示手型指针
                document.body.style.cursor = 'pointer'
                
                // 构建tooltip内容
                const layerInfo = info.object.layerInfo || {}
                const properties = info.object.properties
                
                // 过滤有效的属性
                const filteredProperties = Object.entries(properties)
                  .filter(([key, value]) => {
                    if (key === 'geometry' || key === 'geom') return false
                    if (value == null || value === 'NULL' || value === '') return false
                    if (typeof value === 'object') return false
                    return true
                  })
                  .slice(0, 6)
                
                let content = `<div style="max-width: 300px; font-family: 'Microsoft YaHei', sans-serif;">
                  <div style="margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.3);">
                    <strong style="color: #fff;">${layerInfo.layerName || '图层'}</strong>
                    <small style="background: rgba(255,255,255,0.2); padding: 1px 4px; border-radius: 2px; font-size: 10px; margin-left: 4px;">
                      ${layerInfo.fileType?.toUpperCase() || 'MVT'}
                    </small>
                  </div>`
                
                if (filteredProperties.length === 0) {
                  content += '<div style="color: rgba(255,255,255,0.7); font-style: italic; font-size: 12px;">暂无属性信息</div>'
                } else {
                  filteredProperties.forEach(([key, value]) => {
                    let displayKey = key.length > 12 ? key.substring(0, 12) + '...' : key
                    let displayValue = String(value).length > 20 ? String(value).substring(0, 20) + '...' : value
                    
                    if (typeof value === 'number' && value % 1 !== 0) {
                      displayValue = Number(value).toFixed(3)
                    }
                    
                    content += `
                      <div style="margin-bottom: 4px; font-size: 12px; display: flex;">
                        <span style="color: rgba(255,255,255,0.8); margin-right: 8px; min-width: 60px; font-weight: 500;">${displayKey}：</span>
                        <span style="color: #fff; flex: 1;">${displayValue}</span>
                      </div>
                    `
                  })
                  
                  const totalProperties = Object.keys(properties).length - 2
                  if (totalProperties > 6) {
                    content += `<div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.3); color: rgba(255,255,255,0.6); font-style: italic; font-size: 10px; text-align: center;">共 ${totalProperties} 个属性</div>`
                  }
                }
                
                content += '</div>'
                
                // 设置tooltip位置（靠近鼠标）
                tooltipState.value = {
                  visible: true,
                  content: content,
                  x: info.x + 15, // 向右偏移15px
                  y: info.y - 10, // 向上偏移10px
                  timeout: null
                }
                
                // 设置3秒后自动隐藏
                tooltipState.value.timeout = setTimeout(() => {
                  tooltipState.value.visible = false
                }, 3000)
                
              } else {
                // 无要素时恢复默认指针并隐藏tooltip
                document.body.style.cursor = 'default'
                tooltipState.value.visible = false
              }
            } catch (error) {
              console.warn('鼠标悬停处理出错，已忽略:', error)
              // 不抛出错误，避免视口锁定
            }
          },
          onClick: (info) => {
            try {
              handleMapClick(info)
            } catch (error) {
              console.warn('地图点击处理出错，已忽略:', error)
              // 不抛出错误，避免视口锁定
            }
          },
          getTooltip: ({ object }) => {
            if (!object || !object.properties) return null
            
            // 获取图层信息
            const layerInfo = object.layerInfo || {}
            const properties = object.properties
            
            // 过滤有效的属性
            const filteredProperties = Object.entries(properties)
              .filter(([key, value]) => {
                // 排除几何相关和内部属性
                if (key === 'geometry' || key === 'geom') return false
                if (value == null || value === 'NULL' || value === '') return false
                if (typeof value === 'object') return false
                return true
              })
              .slice(0, 6) // 限制显示前6个属性
            
            // 构建tooltip内容
            let content = `<div style="max-width: 300px; font-family: 'Microsoft YaHei', sans-serif;">
              <div style="margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.3);">
                <strong style="color: #fff;">${layerInfo.layerName || '图层'}</strong>
                <small style="background: rgba(255,255,255,0.2); padding: 1px 4px; border-radius: 2px; font-size: 10px; margin-left: 4px;">
                  ${layerInfo.fileType?.toUpperCase() || 'MVT'}
                </small>
              </div>`
            
            if (filteredProperties.length === 0) {
              content += '<div style="color: rgba(255,255,255,0.7); font-style: italic; font-size: 12px;">暂无属性信息</div>'
            } else {
              filteredProperties.forEach(([key, value]) => {
                // 格式化属性名和值
                let displayKey = key.length > 12 ? key.substring(0, 12) + '...' : key
                let displayValue = String(value).length > 20 ? String(value).substring(0, 20) + '...' : value
                
                // 特殊格式化数字
                if (typeof value === 'number' && value % 1 !== 0) {
                  displayValue = Number(value).toFixed(3)
                }
                
                content += `
                  <div style="margin-bottom: 4px; font-size: 12px; display: flex;">
                    <span style="color: rgba(255,255,255,0.8); margin-right: 8px; min-width: 60px; font-weight: 500;">${displayKey}：</span>
                    <span style="color: #fff; flex: 1;">${displayValue}</span>
                  </div>
                `
              })
              
              const totalProperties = Object.keys(properties).length - 2 // 排除geometry等
              if (totalProperties > 6) {
                content += `<div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.3); color: rgba(255,255,255,0.6); font-style: italic; font-size: 10px; text-align: center;">共 ${totalProperties} 个属性</div>`
              }
            }
            
            content += '</div>'
            
            return {
              html: content,
              style: {
                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                color: 'white',
                padding: '10px',
                borderRadius: '6px',
                fontSize: '12px',
                lineHeight: '1.4',
                maxWidth: '320px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.1)'
              },
              // 设置tooltip位置偏移，让弹出框更靠近鼠标
              offset: [10, 10],
              // 设置tooltip停留时间（毫秒）
              timeout: 3000
            }
          }
        })

        console.log('Deck.gl地图初始化成功')
        
        // 设置初始底图版权信息
        updateBaseMapAttribution(currentBaseMap.value.key)
        
        // 初始化完成后，如果有图层数据，立即更新 - 参考OpenLayers的图层加载逻辑
        if (props.layers && props.layers.length > 0) {
          console.log('🎯 地图初始化完成，开始加载图层，数量:', props.layers.length)
          console.log('图层数据样例:', props.layers[0])
          updateMapLayers(props.layers)
        } else {
          console.log('🎯 地图初始化完成，没有图层数据，仅显示底图')
        }
        
        // 强制修复canvas定位问题
        const fixCanvasPosition = () => {
          // 查找所有canvas元素
          const allCanvases = document.querySelectorAll('canvas')
          console.log('页面上的所有canvas:', allCanvases)
          
          // 查找deckgl相关的canvas
          let deckglCanvas = null
          allCanvases.forEach(canvas => {
            if (canvas.id.includes('deckgl') || canvas.id.includes('overlay')) {
              deckglCanvas = canvas
            }
          })
          
          if (deckglCanvas) {
            console.log('找到deckgl canvas:', deckglCanvas)
            console.log('当前父容器:', deckglCanvas.parentElement)
            console.log('期望的父容器:', mapContainer.value)
            
            // 确保canvas在正确的容器中
            if (deckglCanvas.parentElement !== mapContainer.value) {
              console.log('移动canvas到正确位置')
              mapContainer.value.appendChild(deckglCanvas)
            }
            
            // 修复样式
            deckglCanvas.style.position = 'relative'
            deckglCanvas.style.top = '0'
            deckglCanvas.style.left = '0'
            deckglCanvas.style.width = '100%'
            deckglCanvas.style.height = '100%'
            deckglCanvas.style.maxWidth = '100%'
            deckglCanvas.style.maxHeight = '100%'
            deckglCanvas.style.display = 'block'
            deckglCanvas.style.zIndex = '1'
            
            console.log('Canvas样式已修复，位置:', deckglCanvas.getBoundingClientRect())
          } else {
            console.log('未找到deckgl canvas')
          }
        }
        
        setTimeout(fixCanvasPosition, 100)
        
        // 设置一个观察器来持续监控canvas样式
        const observer = new MutationObserver(() => {
          fixCanvasPosition()
        })
        
        observer.observe(mapContainer.value, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ['style']
        })
        
        emit('map-ready', deckgl.value)
        
      } catch (error) {
        console.error('Deck.gl地图初始化失败:', error)
        ElMessage.error('地图初始化失败: ' + error.message)
      }
    }

    // 创建底图图层
    const createBaseMapLayer = () => {
      return new TileLayer({
        id: 'base-map',
        data: currentBaseMap.value.url,
        minZoom: 0,
        maxZoom: 19,
        tileSize: 256,
        renderSubLayers: props => {
          const {
            bbox: { west, south, east, north }
          } = props.tile
          
          return new BitmapLayer(props, {
            data: null,
            image: props.data,
            bounds: [west, south, east, north]
          })
        }
      })
    }
    
    // 创建三维地形图层 - 直接在TerrainLayer上设置底图纹理
    const create3DTerrainLayers = () => {
      const layers = []
      
      // 🔑 简化方案：在TerrainLayer上直接设置底图作为纹理
      const terrainLayer = new TerrainLayer({
        id: 'terrain-layer',
        // AWS Terrain Tiles (免费) - Terrarium格式
        elevationData: 'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png',
        // 🎯 关键：直接使用当前底图作为地形纹理
        texture: currentBaseMap.value.url,
        // Terrarium格式的高程解码器
        elevationDecoder: {
          rScaler: 256,
          gScaler: 1,
          bScaler: 1 / 256,
          offset: -32768
        },
        // 🎯 关键设置：operation为'terrain+draw'，既显示地形纹理又为其他图层提供3D表面
        operation: 'terrain+draw',
        // 地形材质设置 - 显示底图纹理
        material: {
          ambient: 0.64,    // 环境光
          diffuse: 0.6,     // 漫反射
          shininess: 32,    // 高光
          specularColor: [51, 51, 51]  // 镜面反射
        },
        // 地形渲染参数
        wireframe: false,
        opacity: 1.0,       // 完全不透明
        // 瓦片参数
        minZoom: 0,
        maxZoom: 15,
        tileSize: 256,
        // 地形夸张系数
        elevationScale: 2.0,
        // 更新触发器
        updateTriggers: {
          elevationData: Date.now(),
          texture: currentBaseMap.value.url  // 底图变化时更新
        }
      })
      
      layers.push(terrainLayer)
      
      console.log('🏔️ 已创建三维地形图层，直接使用底图作为纹理')
      console.log('🔧 地形图层配置:', {
        elevationData: 'AWS Terrain Tiles',
        texture: currentBaseMap.value.name,
        elevationScale: 2.0,
        opacity: 1.0,
        operation: 'terrain+draw'
      })
      return layers
    }
    
    // 三维模式下不需要单独的底图图层，TerrainLayer已经包含纹理
    // 这个函数现在返回空，因为底图已经直接设置在TerrainLayer的texture属性上
    const create3DBaseMapLayer = () => {
      // 在简化的三维方案中，不需要额外的底图图层
      // 底图已经作为TerrainLayer的纹理显示
      return null
    }
    


    // 更新鼠标坐标
    const updateMouseCoordinates = (info) => {
      if (info.coordinate) {
        mouseCoordinates.lon = info.coordinate[0].toFixed(6)
        mouseCoordinates.lat = info.coordinate[1].toFixed(6)
      }
    }

    // 处理地图点击
    const handleMapClick = (info) => {
      if (info.layer && info.object) {
        emit('layer-click', {
          layer: info.layer,
          feature: info.object,
          coordinate: info.coordinate
        })
      }
    }

    // 三维模式状态
    const is3DModeEnabled = ref(false)
    
    // 创建用户位置标记图层
    const createUserLocationLayer = () => {
      if (!userLocationCoords.value || !userLocationVisible.value) return null
      
      const layerConfig = {
        id: 'user-location',
        data: [{ position: userLocationCoords.value, name: '我的位置' }],
        pickable: true,
        opacity: 0.9,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 10,
        radiusMaxPixels: 25,
        lineWidthMinPixels: 3,
        getPosition: d => d.position,
        getRadius: 15,
        getFillColor: [64, 158, 255, 200], // 蓝色填充
        getLineColor: [255, 255, 255, 255], // 白色边框
        // 确保在最上层显示
        renderOrder: 1000
      }
      
      // 在三维模式下贴合地形
      if (is3DModeEnabled.value) {
        layerConfig.extensions = [new TerrainExtension()]
        layerConfig.terrainDrawMode = 'drape'
        console.log('📍 用户位置标记已启用三维地形贴合')
      }
      
      return new ScatterplotLayer(layerConfig)
    }
    
    // 底图切换 - 参考OpenLayers的实现，支持三维模式
    const onBaseMapChange = (baseMap) => {
      console.log('切换底图:', baseMap)
      
      // 简化的三维切换逻辑
      if (baseMap.is3D) {
        // 点击三维模式：保持当前底图，切换到三维
        enable3DMode()
      } else {
        // 点击任何其他底图：切换底图，并退出三维模式
        currentBaseMap.value = baseMap
        
        if (is3DModeEnabled.value) {
          // 如果当前在三维模式，先退出三维再切换底图
          disable3DMode()
          // 延迟更新底图，确保三维模式完全退出
          setTimeout(() => {
            updateBaseMapLayer()
          }, 200)
        } else {
          // 普通二维模式，直接更新底图
          updateBaseMapLayer()
        }
      }
      
      // 更新版权信息
      updateBaseMapAttribution(baseMap.key)
    }

    // 更新底图图层
    const updateBaseMapLayer = () => {
      if (!deckgl.value) return
      
      const currentLayers = deckgl.value.props.layers || []
      const otherLayers = currentLayers.filter(layer => layer.id !== 'base-map')
      const newBaseLayer = createBaseMapLayer()
      
      deckgl.value.setProps({
        layers: [newBaseLayer, ...otherLayers]
      })
    }

    // 监听图层变化
    watch(() => props.layers, (newLayers) => {
      updateMapLayers(newLayers)
    }, { deep: true })

    // 更新地图图层
    const updateMapLayers = async (layers) => {
      console.log('updateMapLayers被调用, deckgl实例:', deckgl.value, '图层数量:', layers?.length)
      
      if (!deckgl.value) {
        console.warn('Deck.gl实例不存在，无法更新图层')
        return
      }
      
      if (!layers || layers.length === 0) {
        console.log('没有图层数据，只显示底图')
        
        let layersToShow = []
        if (is3DModeEnabled.value) {
          // 三维模式：只显示地形（包含底图纹理）
          const terrainLayers = create3DTerrainLayers()
          layersToShow = [...terrainLayers]
          console.log('三维模式无数据：显示地形（含底图纹理）')
        } else {
          // 二维模式：只显示底图
          const baseLayer = createBaseMapLayer()
          layersToShow = [baseLayer]
          console.log('二维模式无数据：只显示底图')
        }
        
        // 添加用户位置图层（如果存在）
        const userLocationLayer = createUserLocationLayer()
        if (userLocationLayer) {
          layersToShow.push(userLocationLayer)
          console.log('📍 已添加用户位置标记图层（无数据模式）')
        }
        
        deckgl.value.setProps({
          layers: layersToShow
        })
        return
      }

      try {
        // 创建数据图层
        const dataLayers = await createDataLayers(layers)
        
        let allLayers = []
        
        if (is3DModeEnabled.value) {
          // 三维模式：地形（含底图纹理） + 数据图层
          console.log('🏔️ 三维模式下更新图层')
          const terrainLayers = create3DTerrainLayers()
          allLayers = [...terrainLayers, ...dataLayers]
          console.log('三维模式图层结构: 地形（含纹理）(1) + 数据(' + dataLayers.length + ') = ' + allLayers.length)
        } else {
          // 二维模式：底图 + 数据图层
          console.log('🗺️ 二维模式下更新图层')
          const baseLayer = createBaseMapLayer()
          allLayers = [baseLayer, ...dataLayers]
          console.log('二维模式图层结构: 底图(1) + 数据(' + dataLayers.length + ') = ' + allLayers.length)
        }
        
        // 添加用户位置图层（如果存在）
        const userLocationLayer = createUserLocationLayer()
        if (userLocationLayer) {
          allLayers.push(userLocationLayer)
          console.log('📍 已添加用户位置标记图层')
        }
        
        deckgl.value.setProps({
          layers: allLayers
        })
        
        console.log('✅ 图层更新完成，当前模式:', is3DModeEnabled.value ? '三维' : '二维')
        
      } catch (error) {
        console.error('❌ 更新图层失败:', error)
      }
    }

    // 创建数据图层
    const createDataLayers = async (layers) => {
      const deckLayers = []
      
      console.log('开始创建数据图层，总数:', layers.length)
      
      for (const layer of layers) {
        // 检查图层可见性（兼容visibility和visible字段）
        const isVisible = layer.visibility !== false && layer.visible !== false
        console.log(`图层 ${layer.layer_name}: 可见性=${isVisible}, service_type=${layer.service_type}, file_type=${layer.file_type}`)
        
        if (!isVisible) {
          console.log(`跳过隐藏图层: ${layer.layer_name}`)
          continue
        }
        
        try {
          let deckLayer = null
          
          // 图层类型判断 - 参考OpenLayers的图层类型判断逻辑
          if (layer.service_type === 'martin') {
            // Martin矢量瓦片图层 - 参考OpenLayers的addMartinLayer
           
            if(layer.martin_service_type==='raster.mbtiles'){
                console.log(`创建栅格瓦片图层: ${layer.layer_name} (${layer.file_type})`)
                deckLayer = createTileLayer(layer)
              }else{
                console.log(`创建栅格文件图层: ${layer.layer_name} (${layer.file_type})`)
                deckLayer = createMVTLayer(layer)
              }

          } else if (layer.service_type === 'geoserver') {
            // GeoServer WMS图层 - 参考OpenLayers的addGeoServerLayer
            console.log(`创建GeoServer WMS图层: ${layer.layer_name}`)
            deckLayer = createWMSLayer(layer)
          } else {
            // 根据文件类型推断 - 参考OpenLayers的文件类型判断
            if (layer.file_type === 'geojson' || layer.file_type === 'shp' || layer.file_type === 'dxf') {
              console.log(`创建矢量文件图层: ${layer.layer_name} (${layer.file_type})`)
              deckLayer = createMVTLayer(layer)
            } else if (layer.file_type === 'tif' || layer.file_type === 'tiff') {
              if(layer.martin_service_type==='raster.mbtiles'){
                console.log(`创建栅格瓦片图层: ${layer.layer_name} (${layer.file_type})`)
                deckLayer = createTileLayer(layer)
              }else{
                console.log(`创建栅格文件图层: ${layer.layer_name} (${layer.file_type})`)
                deckLayer = createMVTLayer(layer)
              }
            } else if (layer.file_type === 'mbtiles') {
              console.log(`创建MBTiles图层: ${layer.layer_name}`)
              deckLayer = createMVTLayer(layer)
            } else {
              console.log(`尝试创建通用图层: ${layer.layer_name}`)
              // 根据URL内容判断
              if (layer.mvt_url || (layer.url && (layer.url.includes('pbf') || layer.url.includes('mvt')))) {
                deckLayer = createMVTLayer(layer)
              } else if (layer.wms_url || (layer.url && layer.url.includes('wms'))) {
                deckLayer = createWMSLayer(layer)
              }
            }
          }
          
          if (deckLayer) {
            deckLayers.push(deckLayer)
            console.log(`成功创建图层: ${layer.layer_name}`)
          } else {
            console.warn(`无法确定图层类型: ${layer.layer_name}`)
          }
        } catch (error) {
          console.error(`创建图层 ${layer.layer_name} 失败:`, error)
        }
      }
      
      console.log(`共创建了 ${deckLayers.length} 个Deck.gl图层`)
      return deckLayers
    }

    // 创建栅格瓦片图层 - 用于raster.mbtiles
    const createTileLayer = (layer) => {
      console.log(`创建栅格瓦片图层，图层信息:`, layer)
      
      // 检查MVT URL是否存在 - 参考OpenLayers的验证逻辑
      if (!layer.mvt_url) {
        console.warn('栅格瓦片URL不存在，跳过图层:', layer.layer_name)
        return null
      }
      
      // 从配置中获取Martin基础URL - 参考OpenLayers的配置使用
      const baseUrl = MARTIN_BASE_URL
      
      // 构建栅格瓦片URL - 参考OpenLayers的URL处理逻辑
      let tileUrl = layer.mvt_url
      
      if (tileUrl.includes('localhost:3000')) {
        // 检查是否是MBTiles服务 - 参考OpenLayers的处理
        if (layer.file_type === 'mbtiles' || layer.file_type === 'raster.mbtiles' || tileUrl.includes('/mbtiles/')) {
          const mbtilesMatch = tileUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
          const fileName = mbtilesMatch[1] || 'default'
          tileUrl = `${baseUrl}/${fileName}/{z}/{x}/{y}`
        } else {
          // 提取表名 - 参考OpenLayers的表名提取逻辑
          const tableName = tileUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
          tileUrl = `${baseUrl}/${tableName}/{z}/{x}/{y}`
        }
      }
      
      console.log(`栅格瓦片图层URL: ${tileUrl}`)
      
      const tileLayerConfig = {
        id: `tile-${layer.scene_layer_id || layer.layer_id || layer.id}`,
        data: tileUrl,
        minZoom: layer.min_zoom || 0,
        maxZoom: layer.max_zoom || 22,
        opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
        visible: (layer.visibility !== false && layer.visible !== false),
        tileSize: 256,
        renderSubLayers: props => {
          const {
            bbox: { west, south, east, north }
          } = props.tile
          
          return new BitmapLayer(props, {
            data: null,
            image: props.data,
            bounds: [west, south, east, north]
          })
        },
        // 启用拾取
        pickable: true,
        // 图层信息 - 便于调试
        layerInfo: {
          layerName: layer.layer_name,
          fileType: layer.file_type,
          serviceType: layer.service_type
        }
      }
      
      // 🔑 混合方案：在三维模式下，数据图层使用TerrainExtension贴合地形
      if (is3DModeEnabled.value) {
        tileLayerConfig.extensions = [new TerrainExtension()]
        // drape模式：将栅格数据作为纹理覆盖在地形表面
        tileLayerConfig.terrainDrawMode = 'drape'
        console.log(`🏔️ 栅格瓦片图层 ${layer.layer_name} 已启用TerrainExtension (drape模式)`)
      }
      
      return new TileLayer(tileLayerConfig)
    }

    // 创建MVT矢量瓦片图层 - 参考OpenLayers的实现
    const createMVTLayer = (layer) => {
      console.log(`创建MVT图层，图层信息:`, layer)
      
      // 检查MVT URL是否存在 - 参考OpenLayers的验证逻辑
      if (!layer.mvt_url) {
        console.warn('MVT URL不存在，跳过图层:', layer.layer_name)
        return null
      }
      
      // 从配置中获取Martin基础URL - 参考OpenLayers的配置使用
      const baseUrl = MARTIN_BASE_URL
      
      // 构建MVT URL - 参考OpenLayers的URL处理逻辑
      let mvtUrl = layer.mvt_url
      
      if (mvtUrl.includes('localhost:3000')) {
        // 检查是否是MBTiles服务 - 参考OpenLayers的处理
        if (layer.file_type === 'mbtiles' || mvtUrl.includes('/mbtiles/')) {
          const mbtilesMatch = mvtUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
          const fileName = mbtilesMatch[1] || 'default'
          mvtUrl = `${baseUrl}/${fileName}/{z}/{x}/{y}`
        } else {
          // 提取表名 - 参考OpenLayers的表名提取逻辑
          const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
          mvtUrl = `${baseUrl}/${tableName}/{z}/{x}/{y}`
        }
      }
      
      console.log(`MVT图层URL: ${mvtUrl}`)
      
      // 如果是DXF文件，输出样式调试信息
      if (layer.file_type === 'dxf') {
        console.log(`🎨 为DXF文件创建样式函数: ${layer.layer_name}`)
        console.log('可用的默认样式图层:', Object.keys(defaultDxfStylesConfig.defaultDxfStyles))
      }
      
      // 创建DXF样式函数 - 参考OpenLayers的样式实现
      const createDxfStyleFunctions = (layer) => {
        const isDxf = layer.file_type === 'dxf'
        const defaultStyles = isDxf ? defaultDxfStylesConfig.defaultDxfStyles : {}
        
        // 样式缓存，提高性能 (暂时未使用，保留以备后续优化)
        // const styleCache = {}
        
        return {
          // 填充颜色函数 - 参考OpenLayers的填充样式
          getFillColor: (feature) => {
            const properties = feature.properties || {}
            const geometryType = feature.geometry?.type
            
            // 获取DXF图层名称 - 参考OpenLayers的图层名称提取
            let dxfLayerName = null
            if (properties.cad_layer && typeof properties.cad_layer === 'string') {
              dxfLayerName = properties.cad_layer.trim()
            } else if (isDxf) {
              // 备用字段
              const fallbackFields = ['layer_name', 'dxf_layer', 'subclasses', 'layername', 'entity_layer']
              for (const fieldName of fallbackFields) {
                const fieldValue = properties[fieldName]
                if (fieldValue && typeof fieldValue === 'string' && fieldValue.trim() !== '') {
                  dxfLayerName = fieldValue.trim()
                  break
                }
              }
            }
            
                         // 获取样式配置 - 参考OpenLayers的样式选择逻辑
             let styleConfig = {}
             if (isDxf && dxfLayerName && defaultStyles[dxfLayerName]) {
               styleConfig = defaultStyles[dxfLayerName]
               console.log(`🎨 找到DXF图层样式: ${dxfLayerName}`, styleConfig)
             } else {
               // 默认样式
               styleConfig = {
                 fillColor: '#CCCCCC',
                 fillOpacity: 0.3,
                 visible: true
               }
               if (isDxf && dxfLayerName) {
                 console.log(`⚠️ 未找到DXF图层样式: ${dxfLayerName}，使用默认样式`)
               }
             }
            
            // 如果图层不可见，返回透明
            if (styleConfig.visible === false) {
              return [0, 0, 0, 0]
            }
            
            // 处理填充颜色 - 参考OpenLayers的颜色转换
            if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
              const fillColor = styleConfig.fillColor || '#CCCCCC'
              const fillOpacity = styleConfig.fillOpacity !== undefined ? styleConfig.fillOpacity : 0.3
              
              if (fillColor.startsWith('#')) {
                const r = parseInt(fillColor.slice(1, 3), 16)
                const g = parseInt(fillColor.slice(3, 5), 16)
                const b = parseInt(fillColor.slice(5, 7), 16)
                const a = Math.round(fillOpacity * 255)
                return [r, g, b, a]
              }
            }
            
            // 默认填充颜色
            return [200, 200, 200, 80]
          },
          
          // 线条颜色函数 - 参考OpenLayers的线条样式
          getLineColor: (feature) => {
            const properties = feature.properties || {}
            
            // 获取DXF图层名称
            let dxfLayerName = null
            if (properties.cad_layer && typeof properties.cad_layer === 'string') {
              dxfLayerName = properties.cad_layer.trim()
            }
            
            // 获取样式配置
            let styleConfig = {}
            if (isDxf && dxfLayerName && defaultStyles[dxfLayerName]) {
              styleConfig = defaultStyles[dxfLayerName]
            } else {
              styleConfig = { color: '#000000', opacity: 0.8, visible: true }
            }
            
            // 如果图层不可见，返回透明
            if (styleConfig.visible === false) {
              return [0, 0, 0, 0]
            }
            
            // 处理线条颜色
            const color = styleConfig.color || '#000000'
            const opacity = styleConfig.opacity !== undefined ? styleConfig.opacity : 0.8
            
            if (color.startsWith('#')) {
              const r = parseInt(color.slice(1, 3), 16)
              const g = parseInt(color.slice(3, 5), 16)
              const b = parseInt(color.slice(5, 7), 16)
              const a = Math.round(opacity * 255)
              return [r, g, b, a]
            }
            
            // 默认线条颜色
            return [0, 0, 0, 200]
          },
          
          // 线宽函数 - 参考OpenLayers的线宽设置
          getLineWidth: (feature) => {
            const properties = feature.properties || {}
            
            // 获取DXF图层名称
            let dxfLayerName = null
            if (properties.cad_layer && typeof properties.cad_layer === 'string') {
              dxfLayerName = properties.cad_layer.trim()
            }
            
            // 获取样式配置
            let styleConfig = {}
            if (isDxf && dxfLayerName && defaultStyles[dxfLayerName]) {
              styleConfig = defaultStyles[dxfLayerName]
            } else {
              styleConfig = { weight: 1, visible: true }
            }
            
            // 如果图层不可见，返回0宽度
            if (styleConfig.visible === false) {
              return 0
            }
            
            return styleConfig.weight || 1
          },
          
          // 点半径函数 - 参考OpenLayers的点样式
          getPointRadius: (feature) => {
            const properties = feature.properties || {}
            
            // 获取DXF图层名称
            let dxfLayerName = null
            if (properties.cad_layer && typeof properties.cad_layer === 'string') {
              dxfLayerName = properties.cad_layer.trim()
            }
            
            // 获取样式配置
            let styleConfig = {}
            if (isDxf && dxfLayerName && defaultStyles[dxfLayerName]) {
              styleConfig = defaultStyles[dxfLayerName]
            } else {
              styleConfig = { radius: 3, visible: true }
            }
            
            // 如果图层不可见，返回0半径
            if (styleConfig.visible === false) {
              return 0
            }
            
            return styleConfig.radius || 3
          }
        }
      }
      
      // 获取样式函数
      const styleFunctions = createDxfStyleFunctions(layer)
      
      const mvtLayerConfig = {
        id: `mvt-${layer.scene_layer_id || layer.layer_id || layer.id}`,
        data: mvtUrl,
        minZoom: layer.min_zoom || 0,
        maxZoom: layer.max_zoom || 22, // 参考OpenLayers的最大缩放级别
        opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
        visible: (layer.visibility !== false && layer.visible !== false),
        // 设置渲染顺序 - 参考OpenLayers的zIndex
        renderOrder: layer.layer_order || 1,
        // DXF样式配置 - 参考OpenLayers的样式函数
        getFillColor: styleFunctions.getFillColor,
        getLineColor: styleFunctions.getLineColor,
        getLineWidth: styleFunctions.getLineWidth,
        getPointRadius: styleFunctions.getPointRadius,
        lineWidthMinPixels: 1,
        pointRadiusMinPixels: 2,
        // 启用拾取
        pickable: true,
        // 自动高亮
        autoHighlight: true,
        // 图层信息 - 便于调试
        layerInfo: {
          layerName: layer.layer_name,
          fileType: layer.file_type,
          serviceType: layer.service_type
        }
      }
      
      // 🔑 混合方案：在三维模式下，数据图层使用TerrainExtension贴合地形
      if (is3DModeEnabled.value) {
        mvtLayerConfig.extensions = [new TerrainExtension()]
        // drape模式：将矢量数据作为纹理覆盖在地形表面
        mvtLayerConfig.terrainDrawMode = 'drape'
        // 🔧 修复拾取问题：在三维模式下禁用拾取功能
        mvtLayerConfig.pickable = false
        mvtLayerConfig.autoHighlight = false
        console.log(`🏔️ MVT图层 ${layer.layer_name} 已启用TerrainExtension (drape模式，禁用拾取)`)
      }
      
      return new MVTLayer(mvtLayerConfig)
    }

    // 创建WMS栅格图层 - 参考OpenLayers的实现
    const createWMSLayer = (layer) => {
      // 检查必要的WMS参数 - 参考OpenLayers的验证逻辑
      if (!layer.wms_url || !layer.geoserver_layer) {
        console.warn('WMS URL或图层名称不存在，跳过图层:', layer.layer_name)
        return null
      }
      
      // 处理WMS URL - 参考OpenLayers的URL处理
      let wmsUrl = layer.wms_url.split('?')[0]
      if (wmsUrl.includes('localhost:8083/geoserver') || wmsUrl.includes('localhost:8080/geoserver')) {
        wmsUrl = '/geoserver/wms'
      }
      
      console.log('创建WMS图层:', layer.layer_name, 'URL:', wmsUrl)
      
      // 获取图层坐标系信息 - 参考OpenLayers的坐标系处理
      let layerCRS = 'EPSG:4326' // 默认坐标系
      let wmsVersion = '1.1.1' // 默认版本
      let crsParam = 'SRS' // 默认使用SRS参数
      
      // 根据坐标系调整WMS参数 - 参考OpenLayers的参数设置
      if (layerCRS.startsWith('EPSG:')) {
        if (!layerCRS.includes('4326') && !layerCRS.includes('3857')) {
          wmsVersion = '1.1.0'
          crsParam = 'SRS'
        } else {
          wmsVersion = '1.1.1'
          crsParam = 'SRS'
        }
      }
      
      // 构建WMS参数 - 参考OpenLayers的参数构建
      const wmsParams = {
        'LAYERS': layer.geoserver_layer,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true',
        'VERSION': wmsVersion,
        'STYLES': '',
        'TILED': 'true'
      }
      
      // 设置坐标系参数 - 使用Web Mercator以匹配Deck.gl
      wmsParams[crsParam] = 'EPSG:3857' // Deck.gl使用Web Mercator坐标系
      
      // 构建完整的WMS瓦片URL
      const paramsString = Object.entries(wmsParams)
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&')
      
      const wmsTileUrl = `${wmsUrl}?SERVICE=WMS&REQUEST=GetMap&${paramsString}&BBOX={bbox}&WIDTH=256&HEIGHT=256`
      
      console.log(`WMS图层URL: ${wmsTileUrl}`)
      
      const wmsLayerConfig = {
        id: `wms-${layer.scene_layer_id || layer.layer_id || layer.id}`,
        // 移除data属性，只使用getTileData
        minZoom: layer.min_zoom || 0,
        maxZoom: layer.max_zoom || 23, // 参考OpenLayers的最大缩放级别
        opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
        visible: (layer.visibility !== false && layer.visible !== false),
        // 设置渲染顺序 - 参考OpenLayers的zIndex
        renderOrder: layer.layer_order || 1,
        tileSize: 256,
        // 修复WMS瓦片加载 - 使用getTileData获取图像URL
        getTileData: ({ index: { x, y, z } }) => {
          // 计算Web Mercator瓦片边界框（米为单位）
          const tileSize = 256
          const resolution = (20037508.34 * 2) / (tileSize * Math.pow(2, z))
          const originX = -20037508.34
          const originY = 20037508.34
          
          const west = originX + x * tileSize * resolution
          const east = originX + (x + 1) * tileSize * resolution
          const north = originY - y * tileSize * resolution
          const south = originY - (y + 1) * tileSize * resolution
          
          // 构建实际的WMS请求URL
          const actualUrl = wmsTileUrl.replace('{bbox}', `${west},${south},${east},${north}`)
          
          console.log(`WMS瓦片请求: z=${z}, x=${x}, y=${y}, bbox=${west.toFixed(2)},${south.toFixed(2)},${east.toFixed(2)},${north.toFixed(2)}`)
          
          // 返回图像URL，Deck.gl会自动加载这个图像
          return actualUrl
        },
        renderSubLayers: props => {
          if (!props.data) return null
          
          const {
            bbox: { west, south, east, north }
          } = props.tile
          
          const bitmapConfig = {
            data: null,
            image: props.data,
            bounds: [west, south, east, north]
          }
          
          // 🔑 混合方案：在三维模式下，WMS子图层使用TerrainExtension贴合地形
          if (is3DModeEnabled.value) {
            bitmapConfig.extensions = [new TerrainExtension()]
            bitmapConfig.terrainDrawMode = 'drape'
          }
          
          return new BitmapLayer(props, bitmapConfig)
        }
      }
      
      // 🔑 混合方案：在三维模式下，WMS图层使用TerrainExtension贴合地形
      if (is3DModeEnabled.value) {
        wmsLayerConfig.extensions = [new TerrainExtension()]
        // drape模式：将栅格数据作为纹理覆盖在地形表面
        wmsLayerConfig.terrainDrawMode = 'drape'
        // 🔧 修复拾取问题：在三维模式下禁用拾取功能
        wmsLayerConfig.pickable = false
        console.log(`🏔️ WMS图层 ${layer.layer_name} 已启用TerrainExtension (drape模式，禁用拾取)`)
      }
      
      return new TileLayer(wmsLayerConfig)
    }

    // 刷新地图 - 增强版，支持三维模式，包含错误恢复
    const refreshMap = () => {
      refreshing.value = true
      console.log('🔄 开始刷新地图，当前模式:', is3DModeEnabled.value ? '三维' : '二维')
      
      try {
        if (deckgl.value) {
          // 🔧 清除任何可能的错误状态
          try {
            deckgl.value.setProps({
              onError: (error) => {
                console.warn('Deck.gl错误已捕获:', error)
                return true // 阻止错误传播
              }
            })
          } catch (e) {
            console.warn('设置错误处理器失败，忽略:', e)
          }
          
          // 1. 强制重新渲染Deck.gl
          deckgl.value.redraw()
          
          // 2. 重新加载所有图层（特别重要用于三维模式）
          if (props.layers && props.layers.length > 0) {
            console.log('🔄 重新加载业务图层，数量:', props.layers.length)
            setTimeout(() => {
              updateMapLayers(props.layers)
            }, 100)
          }
          
          // 3. 如果是三维模式，确保深度测试启用
          if (is3DModeEnabled.value) {
            console.log('🏔️ 三维模式刷新：确保WebGL参数正确')
            setTimeout(() => {
              deckgl.value.setProps({
                parameters: {
                  depthTest: true,
                  depthMask: true
                }
              })
            }, 200)
          }
          
          // 4. 强制释放viewState控制，确保交互可用
          setTimeout(() => {
            if (deckgl.value) {
              deckgl.value.setProps({
                viewState: undefined
              })
              console.log('🔓 已确保视口控制释放')
            }
          }, 1000)
          
          ElMessage.success(is3DModeEnabled.value ? '三维地图刷新成功' : '地图刷新成功')
        }
      } catch (error) {
        console.error('❌ 地图刷新失败:', error)
        ElMessage.error('地图刷新失败，尝试重置地图')
        
        // 🆘 紧急重置：如果刷新失败，尝试重新初始化
        setTimeout(() => {
          try {
            if (is3DModeEnabled.value) {
              is3DModeEnabled.value = false
              console.log('🆘 已强制退出三维模式进行重置')
            }
            initDeckGL()
          } catch (resetError) {
            console.error('❌ 重置也失败了:', resetError)
          }
        }, 1000)
      } finally {
        setTimeout(() => {
          refreshing.value = false
          console.log('✅ 地图刷新完成')
        }, 500)
      }
    }

    // 用户定位 - 参考OpenLayers的实现
    const showUserLocation = async () => {
      locationLoading.value = true
      
      try {
        if (!navigator.geolocation) {
          ElMessage.error('浏览器不支持定位功能')
          return
        }
        
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
          })
        })
        
        const { longitude, latitude } = position.coords
        console.log('🔥 用户定位坐标:', { longitude, latitude })
        
        // 保存用户位置坐标
        userLocationCoords.value = [longitude, latitude]
        
        if (deckgl.value) {
          // 获取当前视图状态并保持三维模式的pitch
          const currentViewState = deckgl.value.viewState
          console.log('🔥 当前视图状态:', currentViewState)
          
          const pitch = is3DModeEnabled.value ? (currentViewState.pitch || 45) : 0
          
          // 使用控制器的animateToViewState方法，避免锁定视口
          const targetViewState = {
            longitude,
            latitude,
            zoom: 15,
            pitch,
            bearing: currentViewState.bearing || 0,
            transitionDuration: 1500,
            transitionInterpolator: null
          }
          
          console.log('🔥 目标视图状态:', targetViewState)
          
          // 先更新图层以显示位置标记
          updateMapLayers(props.layers || [])
          
          // 使用控制器的过渡方法而不是直接设置viewState
          deckgl.value.setProps({
            initialViewState: targetViewState,
            viewState: targetViewState
          })
          
          // 短暂延迟后释放viewState控制，保持位置标记显示
          setTimeout(() => {
            if (deckgl.value) {
              console.log('🔥 定位动画完成，释放视图状态控制，保持位置标记')
              // 移除viewState控制，让控制器接管，但保持位置坐标
              deckgl.value.setProps({
                viewState: undefined
              })
            }
          }, 1600) // 等待动画完成
          
          userLocationVisible.value = true
          ElMessage.success('定位成功')
        }
      } catch (error) {
        console.error('定位失败:', error)
        if (error.code === 1) {
          ElMessage.error('定位权限被拒绝，请允许位置访问')
        } else if (error.code === 2) {
          ElMessage.error('无法获取位置信息')
        } else if (error.code === 3) {
          ElMessage.error('定位超时，请重试')
        } else {
          ElMessage.error('定位失败，请检查网络连接')
        }
      } finally {
        locationLoading.value = false
      }
    }
    
    // 隐藏用户位置
    const hideUserLocation = () => {
      userLocationVisible.value = false
      userLocationCoords.value = null // 清除位置坐标
      // 更新图层以移除位置标记
      updateMapLayers(props.layers || [])
      ElMessage.info('已关闭位置显示')
    }
    
    // 切换用户位置显示 - 参考OpenLayers的实现
    const toggleUserLocation = async () => {
      if (userLocationVisible.value) {
        hideUserLocation()
      } else {
        await showUserLocation()
      }
    }
    
    // 切换图层缓存 - 参考OpenLayers的实现
    const toggleLayersCache = () => {
      layersCacheEnabled.value = !layersCacheEnabled.value
      ElMessage.info(`图层缓存已${layersCacheEnabled.value ? '开启' : '关闭'}`)
      console.log('图层缓存状态已切换:', layersCacheEnabled.value ? '开启' : '关闭')
    }
    
    // 更新底图版权信息 - 参考OpenLayers的实现
    const updateBaseMapAttribution = (baseMapType) => {
      const attributions = {
        'gaode': '© 高德地图',
        'gaodeSatellite': '© 高德地图',
        'osm': '© OpenStreetMap contributors',
        'esriSatellite': '© Esri, Maxar, Earthstar Geographics',
        'terrain': '© Esri',
        '3d': '© Deck.gl 三维渲染'
      }
      
      currentBaseMapAttribution.value = attributions[baseMapType] || ''
    }
    
        // 启用三维模式 - Deck.gl特有功能  
    const enable3DMode = () => {
      if (!deckgl.value) return
      
      console.log('🌍 启用三维模式，保持当前底图:', currentBaseMap.value.name)
      is3DModeEnabled.value = true
      
      // 获取当前视图状态
      const currentViewState = deckgl.value.viewState
      
      // 创建三维地形图层（地形基础）
      const terrainLayers = create3DTerrainLayers()
      
      // 创建当前底图的三维版本（覆盖在地形上）
      const baseMapLayer = create3DBaseMapLayer()
      
      // 获取当前的数据图层（非底图）
      const dataLayers = deckgl.value.props.layers?.filter(layer => !layer.id?.includes('base-map')) || []
      
      console.log('🎯 三维模式图层顺序:')
      console.log('1. 地形基础 (TerrainLayer)')
      console.log('2. 底图覆盖:', currentBaseMap.value.name)
      console.log('3. 数据图层:', dataLayers.length, '个')
      
      // 图层顺序：地形（底） -> 底图（中） -> 数据图层（上） -> 用户位置（最上）
      let allLayers = [...terrainLayers, baseMapLayer, ...dataLayers]
      
      // 添加用户位置图层（如果存在）
      const userLocationLayer = createUserLocationLayer()
      if (userLocationLayer) {
        allLayers.push(userLocationLayer)
        console.log('📍 已添加用户位置标记图层（三维模式）')
      }
      
      // 设置三维视图，确保控制器完全启用
      deckgl.value.setProps({
        // 只设置一次视图状态用于过渡，不锁定视口
        viewState: {
          longitude: currentViewState.longitude,
          latitude: currentViewState.latitude,
          zoom: currentViewState.zoom, // 保持当前缩放级别
          pitch: 45, // 设置三维倾斜角
          bearing: currentViewState.bearing || 0, // 保持当前方位角
          transitionDuration: 1500
        },
        // 确保控制器完全启用，允许所有交互
        controller: {
          inertia: true,
          scrollZoom: true,
          dragPan: true,
          dragRotate: true,
          doubleClickZoom: true,
          touchZoom: true,
          touchRotate: true,
          keyboard: true
        },
        // 使用分层结构：地形基础 + 贴合地形的底图 + 贴合地形的数据图层
        layers: allLayers,
        // 不再需要全局terrain配置，使用TerrainExtension实现更精确的图层控制
        parameters: {
          depthTest: true,
          depthMask: true
        }
      })
      
      // 等待过渡动画完成后释放viewState控制，避免锁定视口
      setTimeout(() => {
        if (deckgl.value && is3DModeEnabled.value) {
          deckgl.value.setProps({
            viewState: undefined // 移除viewState控制，完全交给用户
          })
          console.log('✅ 三维模式过渡完成，视口控制已释放')
        }
      }, 1600) // 稍晚于动画完成时间
      
      // 设置三维背景色
      if (deckgl.value.canvas) {
        deckgl.value.canvas.style.backgroundColor = '#0c1445'
      }
      
      // 🔄 强制重新加载所有图层，确保在三维模式下正确显示
      setTimeout(() => {
        console.log('🔄 三维模式启用后，强制刷新图层')
        
        // 如果有props.layers，重新应用它们
        if (props.layers && props.layers.length > 0) {
          console.log('📊 重新加载业务图层，数量:', props.layers.length)
          updateMapLayers(props.layers)
        }
        
        // 不再强制设置viewState，避免锁定视口
        console.log('✅ 三维模式图层刷新完成')
      }, 500) // 等待地形图层完全加载后再刷新
      
      ElMessage.success(`🌍 三维模式已启用：地形(${currentBaseMap.value.name}纹理) + ${dataLayers.length}个数据图层(TerrainExtension)`)
    }
    
    // 禁用三维模式 - 恢复二维视图
    const disable3DMode = () => {
      if (!deckgl.value) return
      
      console.log('🗺️ 恢复二维模式，当前底图:', currentBaseMap.value.name)
      is3DModeEnabled.value = false
      
      // 获取当前视图状态
      const currentViewState = deckgl.value.viewState
      
      // 获取当前的数据图层（排除地形和三维底图）
      const dataLayers = deckgl.value.props.layers?.filter(layer => 
        !layer.id?.includes('base-map') && !layer.id?.includes('terrain-layer')
      ) || []
      
      // 创建普通底图图层
      const baseLayer = createBaseMapLayer()
      
      // 图层顺序：底图 + 数据图层 + 用户位置
      let allLayers = [baseLayer, ...dataLayers]
      
      // 添加用户位置图层（如果存在）
      const userLocationLayer = createUserLocationLayer()
      if (userLocationLayer) {
        allLayers.push(userLocationLayer)
        console.log('📍 已添加用户位置标记图层（二维模式）')
      }
      
      console.log('🎯 二维模式图层顺序:')
      console.log('1. 底图:', currentBaseMap.value.name)
      console.log('2. 数据图层:', dataLayers.length, '个')
      
      // 恢复二维视图，确保不锁定视口
      deckgl.value.setProps({
        // 只设置一次视图状态用于过渡，不锁定视口
        viewState: {
          longitude: currentViewState.longitude,
          latitude: currentViewState.latitude,
          zoom: currentViewState.zoom,
          pitch: 0, // 恢复平视角度
          bearing: currentViewState.bearing || 0, // 保持方位角
          transitionDuration: 1000
        },
        // 确保控制器完全启用，允许所有交互
        controller: {
          inertia: true,
          scrollZoom: true,
          dragPan: true,
          dragRotate: true,
          doubleClickZoom: true,
          touchZoom: true,
          touchRotate: true,
          keyboard: true
        },
        // 恢复普通图层结构：普通底图 + 普通数据图层（无TerrainExtension）
        layers: allLayers,
        // 重置WebGL参数
        parameters: {
          depthTest: false,
          depthMask: false
        }
      })
      
      // 等待过渡动画完成后释放viewState控制，避免锁定视口
      setTimeout(() => {
        if (deckgl.value && !is3DModeEnabled.value) {
          deckgl.value.setProps({
            viewState: undefined // 移除viewState控制，完全交给用户
          })
          console.log('✅ 二维模式过渡完成，视口控制已释放')
        }
      }, 1100) // 稍晚于动画完成时间
      
      // 恢复背景色
      if (deckgl.value.canvas) {
        deckgl.value.canvas.style.backgroundColor = 'transparent'
      }
      
      console.log('✅ 二维模式已恢复')
    }

    // 组件挂载
    onMounted(async () => {
      await nextTick()
      initDeckGL()
    })

    // 组件卸载
    onUnmounted(() => {
      if (deckgl.value) {
        deckgl.value.finalize()
        deckgl.value = null
      }
    })

    return {
      mapContainer,
      mouseCoordinates,
      currentBaseMap,
      refreshing,
      locating,
      deckgl,
      // 新增返回值 - 参考OpenLayers的实现
      layersCacheEnabled,
      locationLoading,
      userLocationVisible,
      currentBaseMapAttribution,
      // 方法
      onBaseMapChange,
      refreshMap,
      toggleUserLocation,
      toggleLayersCache,
      updateBaseMapAttribution
    }
  }
}
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1; /* 确保不会覆盖其他UI元素 */
}

.deckgl-map {
  width: 100%;
  height: 100%;
  position: relative;
}
.el-button+.el-button {
    margin-left: 0px;
}
/* 确保Deck.gl生成的canvas元素正确定位在容器内 */
.map-container canvas {
  position: relative !important;
  max-width: 100% !important;
  max-height: 100% !important;
  display: block !important;
}

/* 特别针对deckgl-overlay的样式重写 */
.map-container #deckgl-overlay {
  position: relative !important;
  width: 100% !important;
  height: 100% !important;
  max-width: 100% !important;
  max-height: 100% !important;
  top: auto !important;
  left: auto !important;
}

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center; /* 参考OpenLayers确保所有按钮居中对齐 */
  gap: 8px;
}

/* 右下角信息面板 - 参考OpenLayers的实现 */
.map-info-panel {
  position: absolute;
  bottom: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
}

.coordinate-info {
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  pointer-events: auto;
}

.coordinate-text {
  font-family: monospace;
  font-size: 11px;
  color: #333;
}

.copyright-info {
  background: rgba(255, 255, 255, 0.7);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  color: #666;
  max-width: 200px;
  text-align: right;
  pointer-events: auto;
}

/* 按钮样式 - 参考OpenLayers的按钮样式 */
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

.location-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid #409EFF;
}

.location-button:hover {
  background-color: #3a8ee6;
  border-color: #3a8ee6;
}

.location-button.is-loading {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.cache-toggle-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 移动端适配 - 参考OpenLayers的移动端样式 */
@media (max-width: 768px) {
  .map-controls {
    top: 8px;
    right: 8px;
    gap: 6px;
  }
  
  /* 确保所有圆形按钮在手机端保持正确的圆形形状 */
  .map-controls .el-button.is-circle {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
  }
  
  /* 确保图标在按钮中居中 */
  .map-controls .el-button.is-circle i {
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
  }
  
  /* 针对具体按钮的额外修复 */
  .map-controls .refresh-button,
  .map-controls .cache-toggle-button,
  .map-controls .location-button,
  .map-controls .base-map-switcher {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
  }
  
  /* 确保所有按钮容器对齐 */
  .map-controls > * {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
  }
  
  .coordinate-info {
    font-size: 10px;
    padding: 3px 6px;
  }
  
  .map-info-panel {
    bottom: 8px;
    right: 8px;
  }
}
</style> 