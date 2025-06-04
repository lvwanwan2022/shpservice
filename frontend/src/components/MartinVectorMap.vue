<template>
  <div class="martin-vector-map">
    <div id="map" ref="mapContainer" class="map-container"></div>
    
    <!-- 图层控制面板 -->
    <div class="layer-control-panel">
      <div class="panel-header">
        <h3>图层控制</h3>
        <button @click="togglePanel" class="toggle-btn">
          {{ panelVisible ? '隐藏' : '显示' }}
        </button>
      </div>
      
      <div v-show="panelVisible" class="panel-content">
        <div v-for="(groupLayers, groupName) in layerGroups" :key="groupName" class="layer-group">
          <h4 @click="toggleGroup(groupName)" class="group-title">
            {{ groupName }}
            <span class="group-toggle">{{ groupExpanded[groupName] ? '▼' : '▶' }}</span>
          </h4>
          
          <div v-show="groupExpanded[groupName]" class="group-layers">
            <label v-for="layerName in groupLayers" :key="layerName" class="layer-item">
              <input 
                type="checkbox" 
                :checked="layerVisibility[layerName]"
                @change="toggleLayerVisibility(layerName, $event.target.checked)"
              />
              <span class="layer-name">{{ getLayerDisplayName(layerName) }}</span>
              <div class="layer-preview" :style="getLayerPreviewStyle(layerName)"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.vectorgrid'
import { 
  getAllLayerStyles, 
  getDynamicLayerStyle, 
  getLayerGroups,
  getLayerConfig,
  isLayerVisible
} from '../utils/dxfLayerStyleUtils'
import { 
  getMartinTileUrl, 
  getTableMetadata,
  createUniversalStyleFunction,
  checkMartinService
} from '../config/martinConfig'

export default {
  name: 'MartinVectorMap',
  props: {
    martinUrl: {
      type: String,
      default: 'http://localhost:3000' // martin服务默认地址
    },
    tableName: {
      type: String,
      default: 'vector_05492e03' // 您的表名
    },
    center: {
      type: Array,
      default: () => [39.9042, 116.4074] // 默认中心点
    },
    zoom: {
      type: Number,
      default: 13
    }
  },
  
  data() {
    return {
      map: null,
      vectorLayer: null,
      layerGroups: {},
      layerVisibility: {},
      groupExpanded: {},
      panelVisible: true
    }
  },
  
  mounted() {
    this.initMap()
    this.initLayerControls()
  },
  
  beforeUnmount() {
    if (this.map) {
      this.map.remove()
    }
  },
  
  methods: {
    initMap() {
      // 创建地图
      this.map = L.map(this.$refs.mapContainer, {
        center: this.center,
        zoom: this.zoom,
        minZoom: 8,
        maxZoom: 20
      })
      
      // 添加底图 - 使用天地图作为底图
      const baseLayer = L.tileLayer(
        'http://t{s}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=您的天地图key', 
        {
          subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
          attribution: '© 天地图'
        }
      )
      
      // 如果没有天地图key，使用OpenStreetMap
      const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      })
      
      osmLayer.addTo(this.map)
      
      // 创建martin vector tile图层
      this.createMartinVectorLayer()
      
      // 添加比例尺
      L.control.scale({
        position: 'bottomleft',
        metric: true,
        imperial: false
      }).addTo(this.map)
    },
    
    createMartinVectorLayer() {
      // martin服务的vector tile URL格式
      const tileUrl = getMartinTileUrl(this.tableName, this.martinUrl)
      const tableMetadata = getTableMetadata(this.tableName)
      
      console.log('Martin Tile URL:', tileUrl)
      console.log('Table Metadata:', tableMetadata)
      
      // 使用通用样式函数，根据layer字段动态应用样式
      const layerStyles = createUniversalStyleFunction(
        getAllLayerStyles(), 
        tableMetadata.layerField
      )
      
      console.log('Applied Styles:', layerStyles)
      
      // 创建vector grid图层
      this.vectorLayer = L.vectorGrid.protobuf(tileUrl, {
        vectorTileLayerStyles: layerStyles,
        interactive: true,
        getFeatureId: (f) => {
          return f.properties.gid || f.properties.id || f.id
        },
        
        // 鼠标点击事件
        onclick: (e) => {
          console.log('要素点击:', e.layer.properties)
          this.showFeaturePopup(e)
        },
        
        // 鼠标悬停事件
        onmouseover: (e) => {
          this.highlightFeature(e)
        },
        
        onmouseout: (e) => {
          this.resetFeatureHighlight(e)
        }
      })
      
      this.vectorLayer.addTo(this.map)
      
      // 监听缩放事件
      this.map.on('zoomend', () => {
        this.vectorLayer.redraw()
      })
      
      // 检查Martin服务状态
      this.checkServiceStatus()
    },
    
    async checkServiceStatus() {
      const isAvailable = await checkMartinService(this.martinUrl)
      if (!isAvailable) {
        console.warn('Martin服务可能未启动或无法连接:', this.martinUrl)
        this.$emit('service-error', {
          message: 'Martin服务连接失败',
          url: this.martinUrl
        })
      }
    },
    
    initLayerControls() {
      this.layerGroups = getLayerGroups()
      
      // 初始化图层可见性
      Object.values(this.layerGroups).flat().forEach(layerName => {
        this.layerVisibility[layerName] = isLayerVisible(layerName)
      })
      
      // 初始化分组展开状态
      Object.keys(this.layerGroups).forEach(groupName => {
        this.groupExpanded[groupName] = true
      })
    },
    
    toggleLayerVisibility(layerName, visible) {
      this.layerVisibility[layerName] = visible
      
      if (this.vectorLayer) {
        const currentStyle = this.vectorLayer.options.vectorTileLayerStyles[layerName]
        
        if (typeof currentStyle === 'function') {
          this.vectorLayer.options.vectorTileLayerStyles[layerName] = (properties, zoom) => {
            const style = getDynamicLayerStyle(layerName, zoom, properties)
            if (!visible) {
              style.opacity = 0
              style.fillOpacity = 0
            }
            return style
          }
        }
        
        this.vectorLayer.redraw()
      }
    },
    
    toggleGroup(groupName) {
      this.groupExpanded[groupName] = !this.groupExpanded[groupName]
    },
    
    togglePanel() {
      this.panelVisible = !this.panelVisible
    },
    
    getLayerDisplayName(layerName) {
      const config = getLayerConfig(layerName)
      return config.name
    },
    
    getLayerPreviewStyle(layerName) {
      const style = getAllLayerStyles()[layerName]
      if (!style) return {}
      
      return {
        backgroundColor: style.fillColor || style.color || '#666',
        opacity: style.fillOpacity || style.opacity || 0.7,
        width: '20px',
        height: '3px',
        display: 'inline-block',
        marginLeft: '5px'
      }
    },
    
    showFeaturePopup(e) {
      if (!e.layer.properties) return
      
      const props = e.layer.properties
      const layerConfig = getLayerConfig(props.layer)
      
      const popupContent = `
        <div class="feature-popup">
          <h4>${layerConfig.name}</h4>
          <table>
            <tr><td><strong>图层:</strong></td><td>${props.layer || '未知'}</td></tr>
            <tr><td><strong>要素ID:</strong></td><td>${props.gid || props.id || '未知'}</td></tr>
            <tr><td><strong>线型:</strong></td><td>${props.linetype || '未知'}</td></tr>
            <tr><td><strong>文本:</strong></td><td>${props.text || '无'}</td></tr>
            <tr><td><strong>实体句柄:</strong></td><td>${props.entityhandle || '未知'}</td></tr>
          </table>
        </div>
      `
      
      L.popup()
        .setLatLng(e.latlng)
        .setContent(popupContent)
        .openOn(this.map)
    },
    
    highlightFeature(e) {
      const layer = e.layer
      if (layer.feature && layer.feature.geometry.type !== 'Point') {
        layer.setStyle({
          weight: 5,
          opacity: 0.9,
          fillOpacity: 0.8,
          color: '#ff0000'
        })
      }
    },
    
    resetFeatureHighlight(e) {
      if (this.vectorLayer && e.layer.feature) {
        this.vectorLayer.resetFeatureStyle(e.layer.feature.id)
      }
    }
  }
}
</script>

<style scoped>
.martin-vector-map {
  position: relative;
  width: 100%;
  height: 100vh;
}

.map-container {
  width: 100%;
  height: 100%;
}

.layer-control-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 280px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  z-index: 1000;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.toggle-btn {
  padding: 4px 8px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.toggle-btn:hover {
  background: #0056b3;
}

.panel-content {
  max-height: 500px;
  overflow-y: auto;
  padding: 8px;
}

.layer-group {
  margin-bottom: 12px;
}

.group-title {
  padding: 8px 12px;
  background: #f1f3f4;
  margin: 0 0 8px 0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.group-title:hover {
  background: #e8eaed;
}

.group-toggle {
  font-size: 12px;
}

.group-layers {
  padding-left: 8px;
}

.layer-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.layer-item:hover {
  background: #f8f9fa;
}

.layer-name {
  margin-left: 8px;
  flex: 1;
}

/* 弹窗样式 */
:deep(.feature-popup) {
  font-family: 'Microsoft YaHei', sans-serif;
}

:deep(.feature-popup h4) {
  margin: 0 0 10px 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

:deep(.feature-popup table) {
  width: 100%;
  font-size: 12px;
}

:deep(.feature-popup td) {
  padding: 2px 5px;
  vertical-align: top;
}

:deep(.feature-popup td:first-child) {
  font-weight: bold;
  width: 80px;
}
</style> 