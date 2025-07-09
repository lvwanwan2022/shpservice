<template>
  <div class="base-map-switcher">
    <el-tooltip content="切换底图" placement="left" :show-after="500">
      <el-dropdown @command="switchBaseMap" trigger="click">
        <el-button type="primary" circle size="small">
          <svg t="1752030794383" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4606" width="16" height="16"><path d="M950.9888 514.59072l-189.0816 80.64 189.0816 97.4848a30.16704 30.16704 0 0 1 0 42.88512L540.0576 953.37472c-11.9296 11.84768-44.0832 11.84768-56.0128 0L72.73472 735.60064a30.16704 30.16704 0 0 1 0-42.88512l189.06112-97.4848-189.06112-80.64a30.16704 30.16704 0 0 1 0-42.88512l203.0592-97.4848L72.74496 279.552c-11.9296-11.83744-11.9296-45.03552 0-56.89344L484.0448 71.07584c11.9296-11.84768 44.0832-11.84768 56.0128 0L950.9888 222.6688c11.9296 11.85792 11.9296 45.056 0 56.89344l-203.08992 94.65856 203.08992 97.4848a30.16704 30.16704 0 0 1 0 42.88512zM185.10848 701.21472c-11.9296 11.84768-7.08608 2.23232 4.84352 14.08l294.0928 154.05056c11.93984 11.84768 44.09344 11.84768 56.02304 0l285.82912-146.67776c11.9296-11.84768 26.90048-5.16096 14.98112-17.00864l-135.4752-63.55968-165.33504 73.19552c-11.9296 11.84768-44.0832 11.84768-56.0128 0L315.99616 641.024l-130.88768 60.19072zM834.17088 253.1328c11.9296-11.84768 4.62848-5.67296-7.29088-17.5104L540.0576 127.0784c-11.9296-11.84768-44.0832-11.84768-56.0128 0L189.952 239.12448c-11.93984 11.85792-11.93984 2.16064 0 14.00832L484.0448 379.1872c11.9296 11.84768 44.0832 11.84768 56.0128 0L834.17088 253.1328z m0 224.08192l-156.7744-70.12352-137.3184 70.12352c-11.93984 11.84768-44.09344 11.84768-56.02304 0l-140.05248-71.20896-154.05056 71.20896c-11.9296 11.84768-11.9296 2.1504 0 13.99808l294.0928 140.05248c11.93984 11.84768 44.09344 11.84768 56.02304 0L834.17088 491.2128c11.9296-11.84768 11.9296-2.1504 0-13.99808z" fill="#000000" p-id="4607"></path></svg>
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
import { getRecommendedPreloadLevel, getRecommendedCacheSize, getDeviceType } from '@/utils/deviceUtils'

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
      // 获取设备特定的预加载配置
      const preloadLevel = getRecommendedPreloadLevel()
      const cacheSize = getRecommendedCacheSize()
      const deviceType = getDeviceType()
      
      //console.log(`🚀 Leaflet地图预加载配置 - 设备类型: ${deviceType}, 预加载级别: ${preloadLevel}, 缓存大小: ${cacheSize}`)
      
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
            // Leaflet预加载和缓存配置
            keepBuffer: preloadLevel,     // 预加载级别（桌面3级，移动2级）
            updateWhenZooming: false,     // 缩放时不立即更新，优化性能
            updateWhenIdle: true,         // 空闲时更新
            tileCacheSize: cacheSize,     // 瓦片缓存大小
            maxConcurrentRequests: deviceType === 'mobile' ? 4 : 6,  // 最大并发请求数
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
            // Leaflet预加载和缓存配置
            keepBuffer: preloadLevel,     // 预加载级别（桌面3级，移动2级）
            updateWhenZooming: false,     // 缩放时不立即更新，优化性能
            updateWhenIdle: true,         // 空闲时更新
            tileCacheSize: cacheSize,     // 瓦片缓存大小
            maxConcurrentRequests: deviceType === 'mobile' ? 4 : 6,  // 最大并发请求数
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
            // Leaflet预加载和缓存配置
            keepBuffer: preloadLevel,     // 预加载级别（桌面3级，移动2级）
            updateWhenZooming: false,     // 缩放时不立即更新，优化性能
            updateWhenIdle: true,         // 空闲时更新
            tileCacheSize: cacheSize,     // 瓦片缓存大小
            maxConcurrentRequests: deviceType === 'mobile' ? 4 : 6,  // 最大并发请求数
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
            // Leaflet预加载和缓存配置
            keepBuffer: preloadLevel,     // 预加载级别（桌面3级，移动2级）
            updateWhenZooming: false,     // 缩放时不立即更新，优化性能
            updateWhenIdle: true,         // 空闲时更新
            tileCacheSize: cacheSize,     // 瓦片缓存大小
            maxConcurrentRequests: deviceType === 'mobile' ? 4 : 6,  // 最大并发请求数
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
        
        //console.log(`底图z-index: 0, 其他图层数量: ${otherLayers.length}`)
        
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

.base-map-switcher .el-button.is-circle {
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
.active {
  background-color: #409EFF;
  color: white;
}
</style> 