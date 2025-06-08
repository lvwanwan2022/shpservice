import L from 'leaflet'
import 'leaflet.vectorgrid'
import { 
  getAllLayerStyles, 
  getDynamicLayerStyle, 
  getLayerGroups,
  isLayerVisible
} from '../utils/dxfLayerStyleUtils'

/**
 * 创建带有DXF图层样式的Vector Grid图层
 * @param {string} tileUrl - 瓦片服务URL
 * @param {object} options - 额外配置选项
 * @returns {L.VectorGrid.Protobuf} Leaflet VectorGrid图层
 */
export function createDXFVectorTileLayer(tileUrl, options = {}) {
  const defaultOptions = {
    vectorTileLayerStyles: getAllLayerStyles(),
    interactive: true,
    getFeatureId: function(f) {
      return f.properties.id || f.properties.fid || f.id
    }
  }

  const mergedOptions = { ...defaultOptions, ...options }

  return L.vectorGrid.protobuf(tileUrl, mergedOptions)
}

/**
 * 创建带有动态样式的Vector Grid图层
 * @param {string} tileUrl - 瓦片服务URL
 * @param {L.Map} map - Leaflet地图实例
 * @param {object} options - 额外配置选项
 * @returns {L.VectorGrid.Protobuf} Leaflet VectorGrid图层
 */
export function createDynamicDXFVectorTileLayer(tileUrl, map, options = {}) {
  const layerStyles = {}
  const allStyles = getAllLayerStyles()

  // 为每个图层创建动态样式函数
  Object.keys(allStyles).forEach(layerName => {
    layerStyles[layerName] = function(properties, zoom) {
      return getDynamicLayerStyle(layerName, zoom, properties)
    }
  })

  const defaultOptions = {
    vectorTileLayerStyles: layerStyles,
    interactive: true,
    getFeatureId: function(f) {
      return f.properties.id || f.properties.fid || f.id
    }
  }

  const mergedOptions = { ...defaultOptions, ...options }
  const vectorLayer = L.vectorGrid.protobuf(tileUrl, mergedOptions)

  // 监听地图缩放事件，重新渲染图层
  map.on('zoomend', function() {
    vectorLayer.redraw()
  })

  return vectorLayer
}

/**
 * 创建图层控制器
 * @param {object} vectorLayers - 图层对象集合
 * @returns {L.Control.Layers} Leaflet图层控制器
 */
export function createLayerControl(vectorLayers = {}) {
  const layerGroups = getLayerGroups()
  const groupedLayers = {}

  Object.entries(layerGroups).forEach(([groupName, layerNames]) => {
    groupedLayers[groupName] = L.layerGroup()
    
    layerNames.forEach(layerName => {
      if (vectorLayers[layerName]) {
        groupedLayers[groupName].addLayer(vectorLayers[layerName])
      }
    })
  })

  return L.control.layers(null, groupedLayers, {
    collapsed: false,
    position: 'topright'
  })
}

/**
 * 初始化完整的DXF地图
 * @param {string} containerId - 地图容器ID
 * @param {object} config - 地图配置
 * @returns {object} 地图和图层的引用对象
 */
export function initializeDXFMap(containerId, config = {}) {
  const defaultConfig = {
    center: [39.9042, 116.4074], // 北京坐标
    zoom: 13,
    minZoom: 8,
    maxZoom: 18,
    tileUrl: 'https://your-tile-server/{z}/{x}/{y}.pbf'
  }

  const mapConfig = { ...defaultConfig, ...config }

  // 创建地图
  const map = L.map(containerId, {
    center: mapConfig.center,
    zoom: mapConfig.zoom,
    minZoom: mapConfig.minZoom,
    maxZoom: mapConfig.maxZoom
  })

  // 添加底图
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map)

  // 创建DXF图层
  const dxfLayer = createDynamicDXFVectorTileLayer(mapConfig.tileUrl, map, {
    // 添加点击事件
    onclick: function(e) {
      //console.log('要素点击事件:', e.layer.properties)
      
      // 显示要素信息弹窗
      if (e.layer.properties) {
        const popup = L.popup()
          .setLatLng(e.latlng)
          .setContent(`
            <div>
              <h4>要素信息</h4>
              <p><strong>图层:</strong> ${e.sourceTarget.layer}</p>
              <p><strong>属性:</strong></p>
              <pre>${JSON.stringify(e.layer.properties, null, 2)}</pre>
            </div>
          `)
          .openOn(map)
      }
    },
    
    // 添加鼠标悬停事件
    onmouseover: function(e) {
      const layer = e.layer
      if (layer.feature && layer.feature.geometry.type !== 'Point') {
        layer.setStyle({
          weight: 5,
          opacity: 0.8,
          fillOpacity: 0.7
        })
      }
    },
    
    onmouseout: function(e) {
      dxfLayer.resetFeatureStyle(e.layer.feature.id)
    }
  })

  dxfLayer.addTo(map)

  // 创建图层控制器
  const layerControl = L.control.layers(null, {
    'DXF图层': dxfLayer
  }, {
    collapsed: false,
    position: 'topright'
  })
  layerControl.addTo(map)

  // 添加比例尺
  L.control.scale({
    position: 'bottomleft',
    metric: true,
    imperial: false
  }).addTo(map)

  return {
    map,
    dxfLayer,
    layerControl
  }
}

/**
 * 切换图层可见性
 * @param {L.VectorGrid} vectorLayer - Vector Grid图层
 * @param {string} layerName - 图层名称
 * @param {boolean} visible - 是否可见
 */
export function toggleLayerVisibility(vectorLayer, layerName, visible) {
  const currentStyle = vectorLayer.options.vectorTileLayerStyles[layerName]
  
  if (typeof currentStyle === 'function') {
    vectorLayer.options.vectorTileLayerStyles[layerName] = function(properties, zoom) {
      const style = getDynamicLayerStyle(layerName, zoom, properties)
      style.opacity = visible ? style.opacity : 0
      style.fillOpacity = visible ? style.fillOpacity : 0
      return style
    }
  } else {
    vectorLayer.options.vectorTileLayerStyles[layerName] = {
      ...currentStyle,
      opacity: visible ? currentStyle.opacity : 0,
      fillOpacity: visible ? currentStyle.fillOpacity : 0
    }
  }
  
  vectorLayer.redraw()
}

export default {
  createDXFVectorTileLayer,
  createDynamicDXFVectorTileLayer,
  createLayerControl,
  initializeDXFMap,
  toggleLayerVisibility
} 