<template>
  <div class="leaflet-map-container">
    <div class="map-header">
      <h3>GeoJSON 地图显示</h3>
      <div class="map-controls">
        <button class="control-btn" @click="loadGeoJsonData">📊 加载数据</button>
        <button class="control-btn" @click="clearAllLayers">🗑️ 清除图层</button>
        <button class="control-btn" @click="toggleLayerPanel">📋 图层管理</button>
        <button class="control-btn" @click="fitBounds">🎯 适合范围</button>
      </div>
    </div>
    
    <div class="map-content">
      <!-- 地图容器 -->
      <div id="mainMap" class="map-wrapper"></div>
      
      <!-- 图层管理面板 -->
      <div v-if="showLayerPanel" class="layer-panel">
        <div class="panel-header">
          <h4>图层管理</h4>
          <button class="close-btn" @click="toggleLayerPanel">×</button>
        </div>
        
        <div class="layer-list">
          <div v-if="layers.length === 0" class="empty-layers">
            没有已加载的图层
          </div>
          
          <div v-for="layer in layers" :key="layer.id" class="layer-item">
            <div class="layer-info">
              <div class="layer-name">{{ layer.name }}</div>
              <div class="layer-details">
                要素: {{ layer.featureCount }} | 类型: {{ layer.geometryType }}
              </div>
            </div>
            
            <div class="layer-controls">
              <button 
                class="toggle-btn" 
                :class="{ active: layer.visible }"
                @click="toggleLayerVisibility(layer.id)">
                {{ layer.visible ? '👁️' : '🙈' }}
              </button>
              <button class="zoom-btn" @click="zoomToLayer(layer.id)">🎯</button>
              <button class="remove-btn" @click="removeLayer(layer.id)">🗑️</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- GeoJSON数据选择面板 -->
      <div v-if="showDataPanel" class="data-panel">
        <div class="panel-header">
          <h4>选择GeoJSON数据</h4>
          <button class="close-btn" @click="showDataPanel = false">×</button>
        </div>
        
        <div class="data-options">
          <div class="option-section">
            <h5>从文件列表加载</h5>
            <div v-if="loadingFiles" class="loading">
              <div class="spinner"></div>
              <span>加载文件列表...</span>
            </div>
            <div v-else class="file-list">
              <div 
                v-for="file in availableFiles" 
                :key="file.file_id" 
                class="file-option">
                <div class="file-name">{{ file.original_filename }}</div>
                <div class="file-info">
                  {{ file.feature_count }} 要素 | {{ file.geometry_types.join(', ') }}
                </div>
                <div class="file-actions">
                  <button 
                    class="action-btn" 
                    @click="loadFileData(file)"
                    :disabled="loading || file.publishing"
                  >
                    加载显示
                  </button>
                  <button 
                    class="action-btn publish-btn" 
                    @click="publishFileService(file)"
                    :disabled="loading || file.publishing"
                  >
                    {{ file.publishing ? '发布中...' : '服务发布' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="option-section">
            <h5>从URL加载</h5>
            <div class="url-input">
              <input 
                v-model="customUrl" 
                type="url" 
                placeholder="输入GeoJSON文件的URL"
                @keyup.enter="loadUrlData">
              <button @click="loadUrlData">加载</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 状态信息 -->
    <div class="status-bar">
      <div class="status-info">
        <span>图层数: {{ layers.length }}</span>
        <span>总要素: {{ totalFeatures }}</span>
        <span v-if="loading">⏳ 正在加载...</span>
      </div>
      
      <div class="coordinates" v-if="mouseCoordinates">
        {{ mouseCoordinates }}
      </div>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-toast">
      {{ errorMessage }}
      <button @click="errorMessage = null">×</button>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/index.js'

export default {
  name: 'LeafletMap',
  props: {
    // 初始要加载的GeoJSON文件ID
    initialFileId: {
      type: String,
      default: null
    },
    // 地图配置
    mapConfig: {
      type: Object,
      default: () => ({
        center: [39.9042, 116.4074],
        zoom: 10,
        maxZoom: 18,
        minZoom: 3
      })
    }
  },
  
  data() {
    return {
      // 地图相关
      map: null,
      layers: [],
      layerIdCounter: 1,
      
      // 面板显示
      showLayerPanel: false,
      showDataPanel: false,
      
      // 数据加载
      loading: false,
      loadingFiles: false,
      availableFiles: [],
      customUrl: '',
      
      // 状态
      errorMessage: null,
      mouseCoordinates: null
    }
  },
  
  computed: {
    totalFeatures() {
      return this.layers.reduce((total, layer) => total + (layer.featureCount || 0), 0)
    }
  },
  
  mounted() {
    this.initMap()
    this.loadAvailableFiles()
    
    // 如果有初始文件ID，自动加载
    if (this.initialFileId) {
      this.loadFileById(this.initialFileId)
    }
  },
  
  beforeUnmount() {
    if (this.map) {
      this.map.remove()
    }
  },
  
  methods: {
    // === 地图初始化 ===
    async initMap() {
      try {
        // 动态加载Leaflet
        const L = await this.loadLeaflet()
        
        ////console.log('创建Leaflet地图...')
        
        // 创建地图但不添加任何底图
        this.map = L.map(this.$refs.mapContainer, {
          center: [39.9042, 116.4074], // 北京
          zoom: 10,
          zoomControl: true,
          attributionControl: true
        })
        
        ////console.log('Leaflet地图创建成功（无底图模式）')
        
        // 添加鼠标坐标显示
        this.map.on('mousemove', (e) => {
          if (e.latlng && e.latlng.lat !== undefined && e.latlng.lng !== undefined) {
            const lat = e.latlng.lat.toFixed(6)
            const lng = e.latlng.lng.toFixed(6)
            this.mouseCoordinates = `${lat}, ${lng}`
          }
        })
        
        // 添加右键菜单（可选）
        this.map.on('contextmenu', (e) => {
          if (e.latlng && e.latlng.lat !== undefined && e.latlng.lng !== undefined) {
            const lat = e.latlng.lat.toFixed(6)
            const lng = e.latlng.lng.toFixed(6)
            ////console.log('右键点击坐标:', lat, lng)
          }
        })
        
        ////console.log('地图初始化成功')
        
      } catch (error) {
        console.error('地图初始化失败:', error)
        this.errorMessage = '地图初始化失败: ' + error.message
      }
    },
    
    async loadLeaflet() {
      // 检查是否已加载
      if (window.L) {
        return window.L
      }
      
      // 动态加载CSS
      if (!document.querySelector('link[href*="leaflet"]')) {
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
        document.head.appendChild(link)
      }
      
      // 动态加载JS
      return new Promise((resolve, reject) => {
        if (window.L) {
          resolve(window.L)
          return
        }
        
        const script = document.createElement('script')
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
        script.onload = () => resolve(window.L)
        script.onerror = reject
        document.head.appendChild(script)
      })
    },
    
    // === 数据加载 ===
    async loadAvailableFiles() {
      this.loadingFiles = true
      
      try {
        const response = await api.get('/geojson/files')
        this.availableFiles = response.data.files || []
        ////console.log('可用文件列表加载成功:', this.availableFiles.length)
      } catch (error) {
        console.error('加载文件列表失败:', error)
        this.errorMessage = '加载文件列表失败'
      } finally {
        this.loadingFiles = false
      }
    },
    
    async loadFileById(fileId) {
      try {
        this.loading = true
        
        // 获取文件信息
        const fileInfo = this.availableFiles.find(f => f.file_id === fileId)
        if (!fileInfo) {
          throw new Error('文件不存在')
        }
        
        // 加载GeoJSON数据
        const dataUrl = `/api/geojson/files/${fileId}`
        const response = await api.get(dataUrl)
        const geojsonData = response.data
        
        // 添加到地图
        this.addGeoJsonLayer(geojsonData, {
          name: fileInfo.original_filename,
          source: 'file',
          fileId: fileId
        })
        
        ////console.log('文件数据加载成功:', fileId)
        
      } catch (error) {
        console.error('加载文件数据失败:', error)
        this.errorMessage = '加载数据失败: ' + error.message
      } finally {
        this.loading = false
      }
    },
    
    async loadFileData(file) {
      this.showDataPanel = false
      await this.loadFileById(file.file_id)
    },
    
    async publishFileService(file) {
      try {
        // 设置发布中状态
        file.publishing = true
        this.loading = true
        this.showDataPanel = false
        
        // 显示提示
        this.errorMessage = `正在发布服务，请稍候...`
        
        // 调用发布服务API
        const response = await api.publishService(file.file_id)
        
        ////console.log('服务发布成功:', response.data)
        
        // 显示成功提示，包含服务URL
        this.errorMessage = `服务发布成功！
          图层名称: ${response.data.layer_name}
          WMS服务: ${response.data.wms_url}
          WFS服务: ${response.data.wfs_url}`
        
        // 3秒后自动关闭提示
        setTimeout(() => {
          if (this.errorMessage && this.errorMessage.includes('服务发布成功')) {
            this.errorMessage = null
          }
        }, 5000)
        
      } catch (error) {
        console.error('发布服务失败:', error)
        this.errorMessage = '发布服务失败: ' + (error.response?.data?.error || error.message)
      } finally {
        // 清除状态
        file.publishing = false
        this.loading = false
      }
    },
    
    async loadUrlData() {
      if (!this.customUrl.trim()) {
        this.errorMessage = '请输入有效的URL'
        return
      }
      
      try {
        this.loading = true
        
        // 直接请求URL
        const response = await fetch(this.customUrl)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const geojsonData = await response.json()
        
        // 添加到地图
        this.addGeoJsonLayer(geojsonData, {
          name: `URL数据 (${new URL(this.customUrl).pathname.split('/').pop()})`,
          source: 'url',
          url: this.customUrl
        })
        
        this.customUrl = ''
        this.showDataPanel = false
        
        ////console.log('URL数据加载成功')
        
      } catch (error) {
        console.error('加载URL数据失败:', error)
        this.errorMessage = 'URL数据加载失败: ' + error.message
      } finally {
        this.loading = false
      }
    },
    
    // === 图层管理 ===
    addGeoJsonLayer(geojsonData, options = {}) {
      if (!this.map) {
        throw new Error('地图未初始化')
      }
      
      const L = window.L
      
      // 分析数据
      const analysis = this.analyzeGeoJson(geojsonData)
      
      // 创建图层
      const geojsonLayer = L.geoJSON(geojsonData, {
        style: (feature) => {
          return {
            color: this.getRandomColor(),
            weight: 2,
            opacity: 0.8,
            fillOpacity: 0.3
          }
        },
        pointToLayer: (feature, latlng) => {
          return L.circleMarker(latlng, {
            radius: 6,
            fillColor: this.getRandomColor(),
            color: '#000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
          })
        },
        onEachFeature: (feature, layer) => {
          if (feature.properties) {
            this.bindFeaturePopup(feature, layer)
          }
        }
      })
      
      // 添加到地图
      geojsonLayer.addTo(this.map)
      
      // 记录图层信息
      const layerInfo = {
        id: this.layerIdCounter++,
        name: options.name || `图层 ${this.layers.length + 1}`,
        layer: geojsonLayer,
        visible: true,
        featureCount: analysis.featureCount,
        geometryType: analysis.geometryTypes.join(', '),
        bounds: geojsonLayer.getBounds(),
        source: options.source || 'unknown',
        ...options
      }
      
      this.layers.push(layerInfo)
      
      // 自动缩放到新图层
      if (layerInfo.bounds.isValid()) {
        this.map.fitBounds(layerInfo.bounds, { padding: [20, 20] })
      }
      
      ////console.log('图层添加成功:', layerInfo)
      
      return layerInfo
    },
    
    analyzeGeoJson(geojsonData) {
      const analysis = {
        featureCount: 0,
        geometryTypes: new Set()
      }
      
      if (geojsonData.type === 'FeatureCollection') {
        analysis.featureCount = geojsonData.features.length
        geojsonData.features.forEach(feature => {
          if (feature.geometry && feature.geometry.type) {
            analysis.geometryTypes.add(feature.geometry.type)
          }
        })
      } else if (geojsonData.type === 'Feature') {
        analysis.featureCount = 1
        if (geojsonData.geometry && geojsonData.geometry.type) {
          analysis.geometryTypes.add(geojsonData.geometry.type)
        }
      }
      
      analysis.geometryTypes = Array.from(analysis.geometryTypes)
      
      return analysis
    },
    
    bindFeaturePopup(feature, layer) {
      const props = feature.properties
      let popupContent = '<div class="feature-popup">'
      
      // 添加几何类型信息
      if (feature.geometry && feature.geometry.type) {
        popupContent += `<div class="popup-header">类型: ${feature.geometry.type}</div>`
      }
      
      // 添加属性信息
      popupContent += '<div class="popup-properties">'
      
      for (const [key, value] of Object.entries(props)) {
        if (value !== null && value !== undefined && value !== '') {
          const displayValue = typeof value === 'object' ? JSON.stringify(value) : value
          popupContent += `<div class="property-row">
            <strong>${key}:</strong> <span>${displayValue}</span>
          </div>`
        }
      }
      
      popupContent += '</div></div>'
      
      layer.bindPopup(popupContent, {
        maxWidth: 300,
        className: 'custom-popup'
      })
    },
    
    toggleLayerVisibility(layerId) {
      const layerInfo = this.layers.find(l => l.id === layerId)
      if (!layerInfo) return
      
      if (layerInfo.visible) {
        this.map.removeLayer(layerInfo.layer)
        layerInfo.visible = false
      } else {
        this.map.addLayer(layerInfo.layer)
        layerInfo.visible = true
      }
    },
    
    zoomToLayer(layerId) {
      const layerInfo = this.layers.find(l => l.id === layerId)
      if (!layerInfo || !layerInfo.bounds.isValid()) return
      
      this.map.fitBounds(layerInfo.bounds, { padding: [20, 20] })
    },
    
    removeLayer(layerId) {
      const index = this.layers.findIndex(l => l.id === layerId)
      if (index === -1) return
      
      const layerInfo = this.layers[index]
      
      // 从地图移除
      this.map.removeLayer(layerInfo.layer)
      
      // 从列表移除
      this.layers.splice(index, 1)
      
      ////console.log('图层已移除:', layerInfo.name)
    },
    
    clearAllLayers() {
      if (this.layers.length === 0) return
      
      if (!confirm('确定要清除所有图层吗？')) return
      
      this.layers.forEach(layerInfo => {
        this.map.removeLayer(layerInfo.layer)
      })
      
      this.layers = []
      ////console.log('所有图层已清除')
    },
    
    fitBounds() {
      if (this.layers.length === 0) {
        this.errorMessage = '没有可用的图层'
        return
      }
      
      const group = window.L.featureGroup(
        this.layers
          .filter(l => l.visible && l.bounds.isValid())
          .map(l => l.layer)
      )
      
      if (group.getLayers().length > 0) {
        this.map.fitBounds(group.getBounds(), { padding: [20, 20] })
      }
    },
    
    // === 界面控制 ===
    loadGeoJsonData() {
      this.showDataPanel = true
    },
    
    toggleLayerPanel() {
      this.showLayerPanel = !this.showLayerPanel
    },
    
    // === 工具方法 ===
    getRandomColor() {
      const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
      ]
      return colors[Math.floor(Math.random() * colors.length)]
    }
  }
}
</script>

<style scoped>
.leaflet-map-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.map-header {
  background: white;
  padding: 16px 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.map-header h3 {
  margin: 0;
  color: #2c3e50;
}

.map-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
  padding: 8px 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.control-btn:hover {
  background: #2980b9;
}

.map-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-wrapper {
  width: 100%;
  height: 100%;
}

/* 图层管理面板 */
.layer-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 320px;
  max-height: 70%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  display: flex;
  flex-direction: column;
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

.panel-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
}

.close-btn {
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.layer-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-layers {
  text-align: center;
  color: #7f8c8d;
  padding: 20px;
  font-style: italic;
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin: 4px 0;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.layer-info {
  flex: 1;
  min-width: 0;
}

.layer-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
  word-break: break-all;
}

.layer-details {
  font-size: 12px;
  color: #7f8c8d;
}

.layer-controls {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.toggle-btn, .zoom-btn, .remove-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  min-width: 28px;
  height: 28px;
}

.toggle-btn {
  background: #95a5a6;
  color: white;
}

.toggle-btn.active {
  background: #27ae60;
}

.zoom-btn {
  background: #3498db;
  color: white;
}

.remove-btn {
  background: #e74c3c;
  color: white;
}

/* 数据选择面板 */
.data-panel {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 500px;
  max-width: 90vw;
  max-height: 80vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  z-index: 1001;
  display: flex;
  flex-direction: column;
}

.data-options {
  padding: 16px;
  overflow-y: auto;
}

.option-section {
  margin-bottom: 24px;
}

.option-section h5 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 4px;
}

.file-option {
  padding: 12px;
  border-bottom: 1px solid #f8f9fa;
  cursor: pointer;
  transition: background 0.2s;
}

.file-option:hover {
  background: #f8f9fa;
}

.file-option:last-child {
  border-bottom: none;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.file-info {
  font-size: 12px;
  color: #7f8c8d;
}

.file-actions {
  display: flex;
  gap: 5px;
  margin-top: 5px;
}

.action-btn {
  padding: 3px 8px;
  font-size: 12px;
  background-color: #4c8bf5;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.action-btn:hover {
  background-color: #3a7ce0;
}

.publish-btn {
  background-color: #28a745;
}

.publish-btn:hover {
  background-color: #218838;
}

.url-input {
  display: flex;
  gap: 8px;
}

.url-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.url-input button {
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 状态栏 */
.status-bar {
  background: white;
  padding: 8px 20px;
  box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  flex-shrink: 0;
}

.status-info {
  display: flex;
  gap: 16px;
  color: #7f8c8d;
}

.coordinates {
  color: #2c3e50;
  font-family: monospace;
}

/* 加载状态 */
.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  padding: 20px;
  color: #7f8c8d;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误提示 */
.error-toast {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #e74c3c;
  color: white;
  padding: 12px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1002;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 80%;
}

.error-toast button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  width: 20px;
  height: 20px;
}

/* 弹出框样式 */
:global(.custom-popup .leaflet-popup-content) {
  margin: 0;
  line-height: 1.4;
}

:global(.feature-popup) {
  font-size: 14px;
}

:global(.popup-header) {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

:global(.popup-properties) {
  max-height: 200px;
  overflow-y: auto;
}

:global(.property-row) {
  margin-bottom: 6px;
  display: flex;
  gap: 8px;
}

:global(.property-row strong) {
  color: #34495e;
  flex-shrink: 0;
  min-width: 80px;
}

:global(.property-row span) {
  color: #2c3e50;
  word-break: break-all;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .map-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .map-controls {
    width: 100%;
    justify-content: space-around;
  }
  
  .layer-panel {
    width: calc(100vw - 20px);
    right: 10px;
    left: 10px;
  }
  
  .data-panel {
    width: calc(100vw - 20px);
  }
  
  .status-bar {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .layer-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .layer-controls {
    width: 100%;
    justify-content: space-around;
  }
}
</style> 