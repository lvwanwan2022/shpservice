<template>
  <div class="base-map-switcher">
    <el-tooltip content="切换底图" placement="left" :show-after="500">
      <el-dropdown @command="switchBaseMap" trigger="click">
        <el-button type="primary" circle size="small">
          <i class="el-icon-map-location"></i>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="gaode" :class="{ active: currentBaseMap === 'gaode' }">
              高德地图
            </el-dropdown-item>
            <el-dropdown-item command="gaodeSatellite" :class="{ active: currentBaseMap === 'gaodeSatellite' }">
              高德卫星图
            </el-dropdown-item>
            <el-dropdown-item command="osm" :class="{ active: currentBaseMap === 'osm' }">
              OpenStreetMap
            </el-dropdown-item>
            <el-dropdown-item command="esriSatellite" :class="{ active: currentBaseMap === 'esriSatellite' }">
              Esri 世界影像
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-tooltip>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import L from 'leaflet'

export default {
  name: 'BaseMapSwitcherLF',
  props: {
    map: { type: Object, required: true }
  },
  emits: ['base-map-changed'],
  setup(props, { emit }) {
    const currentBaseMap = ref('gaode')
    const currentLayer = ref(null)
    
    // 创建不同的底图图层
    const createBaseMapLayer = (type) => {
      const subdomains = ['01', '02', '03', '04']
      let url = ''
      let attribution = ''
      let options = {}
      
      switch (type) {
        case 'gaode':
          url = 'https://webrd{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
          attribution = '© 高德地图'
          options = {
            subdomains: subdomains,
            attribution,
            minZoom: 3,     // 最小缩放级别
            maxNativeZoom: 18,  // 原生瓦片最大级别
            maxZoom: 23,    // 允许过采样到更高级别
            detectRetina: true,
            // 错误瓦片处理
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            // 当瓦片加载失败时的处理
            bounds: [[-85.051128779807, -180], [85.051128779807, 180]]
          }
          break
        case 'gaodeSatellite':
          url = 'https://webst{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
          attribution = '© 高德地图'
          options = {
            subdomains: subdomains,
            attribution,
            minZoom: 3,
            maxNativeZoom: 18,  // 原生瓦片最大级别
            maxZoom: 23,    // 允许过采样到更高级别
            detectRetina: true,
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            bounds: [[-85.051128779807, -180], [85.051128779807, 180]]
          }
          break
        case 'osm':
          url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
          attribution = '© OpenStreetMap contributors'
          options = {
            subdomains: ['a', 'b', 'c'],
            attribution,
            minZoom: 1,
            maxNativeZoom: 19,  // 原生瓦片最大级别
            maxZoom: 23,    // 允许过采样到更高级别
            detectRetina: true,
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
          }
          break
        case 'esriSatellite':
          url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
          attribution = '© Esri'
          options = {
            attribution,
            minZoom: 1,
            maxNativeZoom: 21,  // 原生瓦片最大级别（Esri支持到21级）
            maxZoom: 23,    // 允许过采样到更高级别
            detectRetina: true,
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
          }
          break
        default:
          return null
      }
      
      const layer = L.tileLayer(url, options)
      
      // 添加瓦片加载错误处理和过采样逻辑
      layer.on('tileerror', function(error) {
        console.warn(`底图瓦片加载失败: ${type}`, error)
        // 可以在这里添加备用URL或降级处理
      })
      
      // 添加瓦片加载成功的监听，用于调试过采样
      layer.on('tileload', function(event) {
        const tile = event.tile
        const coords = event.coords
        
        // 检查是否是过采样瓦片（缩放级别超过原生级别）
        if (coords.z > options.maxNativeZoom) {
          // 为过采样瓦片添加视觉标识（可选，用于调试）
          if (tile && tile.style) {
            tile.style.filter = 'contrast(0.9) brightness(0.95)'
            tile.title = `过采样瓦片 (${coords.z}/${options.maxNativeZoom})`
          }
        }
      })
      
      return layer
    }
    
    const switchBaseMap = (command) => {
      if (!props.map) return
      
      // 获取当前缩放级别
      const currentZoom = props.map.getZoom()
      
      // 移除当前底图
      if (currentLayer.value) {
        props.map.removeLayer(currentLayer.value)
      }
      
      // 创建新底图
      const newLayer = createBaseMapLayer(command)
      if (newLayer) {
        // 设置底图的z-index确保在最底层
        newLayer.setZIndex(0)
        newLayer.addTo(props.map)
        currentLayer.value = newLayer
        currentBaseMap.value = command
        
        // 检查当前缩放级别是否在新底图的支持范围内
        const layerMaxZoom = newLayer.options.maxZoom || 18
        const layerMinZoom = newLayer.options.minZoom || 1
        
        // 如果当前缩放级别超出新底图支持范围，自动调整
        if (currentZoom > layerMaxZoom) {
          console.warn(`当前缩放级别(${currentZoom})超出${command}底图最大级别(${layerMaxZoom})，自动调整到最大级别`)
          props.map.setZoom(layerMaxZoom)
        } else if (currentZoom < layerMinZoom) {
          console.warn(`当前缩放级别(${currentZoom})低于${command}底图最小级别(${layerMinZoom})，自动调整到最小级别`)
          props.map.setZoom(layerMinZoom)
        }
        
        // 延迟触发重新排序，确保底图完全加载后执行
        setTimeout(() => {
          refreshLayerOrder()
        }, 200)
        
        // 发出底图切换事件
        emit('base-map-changed', command)
      }
    }
    
    // 刷新图层顺序，确保底图在最底层
    const refreshLayerOrder = () => {
      if (!props.map || !currentLayer.value) return
      
      try {
        // 确保底图的z-index为0（最底层）
        currentLayer.value.setZIndex(0)
        
        // 收集所有非底图图层
        const otherLayers = []
        props.map.eachLayer((layer) => {
          // 跳过底图和默认的缩放控件等
          if (layer !== currentLayer.value && 
              layer.setZIndex && 
              !layer.options.attribution &&
              layer._url !== currentLayer.value._url) {
            otherLayers.push(layer)
          }
        })
        
        // 为其他图层设置更高的z-index
        otherLayers.forEach((layer, index) => {
          if (layer.setZIndex) {
            layer.setZIndex(100 + index)
          }
        })
        
        console.log(`底图z-index: 0, 其他图层数量: ${otherLayers.length}`)
        
      } catch (error) {
        console.error('刷新图层顺序失败:', error)
      }
    }
    
    // 初始化默认底图
    onMounted(() => {
      if (props.map) {
        const defaultLayer = createBaseMapLayer('gaode')
        if (defaultLayer) {
          // 确保初始底图也在最底层
          defaultLayer.setZIndex(0)
          defaultLayer.addTo(props.map)
          currentLayer.value = defaultLayer
        }
      }
    })
    
    return {
      currentBaseMap,
      switchBaseMap
    }
  }
}
</script>

<style scoped>
.base-map-switcher {
  /* 移除绝对定位，现在由父容器 .map-controls 管理位置 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.active {
  background-color: #409EFF;
  color: white;
}
</style> 