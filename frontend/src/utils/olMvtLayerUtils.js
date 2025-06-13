/**
 * OpenLayers MVT图层工具类
 * 基于 Leaflet 版本改写为 OpenLayers 实现
 */

import VectorTileLayer from 'ol/layer/VectorTile'
import VectorTile from 'ol/source/VectorTile'
import { MVT } from 'ol/format'
import { Style, Fill, Stroke, Circle } from 'ol/style'

/**
 * 检查OpenLayers MVT支持
 */
export function checkOpenLayersMVTSupport() {
  try {
    const hasSupport = !!(VectorTileLayer && VectorTile && MVT)
    //console.log('OpenLayers MVT支持检查:', hasSupport)
    return hasSupport
  } catch (error) {
    console.error('OpenLayers MVT支持检查失败:', error)
    return false
  }
}

/**
 * 创建样式函数 - OpenLayers版本
 * @param {Object} styleConfig - 样式配置对象
 * @param {boolean} isDxf - 是否为DXF类型
 * @returns {Function} OpenLayers样式函数
 */
export function createOpenLayersStyleFunction(styleConfig = {}, isDxf = false) {
  return (feature, resolution) => {
    const properties = feature.getProperties()
    const layerName = properties.layer || properties.Layer || 'default'
    const layerStyle = styleConfig[layerName] || {}
    
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
            width: layerStyle.strokeWidth || 1
          })
        })
      })
    } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
      // 线样式 - 对应Leaflet的weight
      style = new Style({
        stroke: new Stroke({
          color: layerStyle.color || '#0066cc',
          width: layerStyle.weight || 2,
          lineDash: layerStyle.dashArray || undefined,
          opacity: layerStyle.opacity || 0.8
        })
      })
    } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
      // 面样式 - 对应Leaflet的fillColor和fillOpacity
      const fillColor = layerStyle.fillColor || layerStyle.color || '#66ccff'
      const fillOpacity = layerStyle.fillOpacity || 0.3
      
      // 转换颜色和透明度
      let finalFillColor = fillColor
      if (fillOpacity !== 1) {
        if (fillColor.startsWith('#')) {
          // 将十六进制颜色转换为rgba
          const r = parseInt(fillColor.slice(1, 3), 16)
          const g = parseInt(fillColor.slice(3, 5), 16)
          const b = parseInt(fillColor.slice(5, 7), 16)
          finalFillColor = `rgba(${r}, ${g}, ${b}, ${fillOpacity})`
        }
      }
      
      style = new Style({
        stroke: new Stroke({
          color: layerStyle.color || '#0066cc',
          width: layerStyle.weight || 1
        }),
        fill: new Fill({
          color: finalFillColor
        })
      })
    } else {
      // 默认混合样式
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
    
    // 处理图层可见性 - 对应Leaflet的opacity控制
    if (layerStyle.visible === false || layerStyle.opacity === 0) {
      return new Style({}) // 返回空样式以隐藏
    }
    
    return style
  }
}

/**
 * 创建OpenLayers MVT图层 - 完全对应Leaflet版本
 * @param {Object} layerConfig - 图层配置
 * @param {string} layerConfig.mvt_url - MVT瓦片URL模板
 * @param {string} layerConfig.tilejson_url - TileJSON URL
 * @param {string} layerConfig.layer_name - 图层名称
 * @param {Object} layerConfig.style - 图层样式
 * @param {Object} options - 额外选项
 * @returns {Promise<VectorTileLayer>} OpenLayers图层对象
 */
export async function createOpenLayersMVTLayer(layerConfig, options = {}) {
  //console.log('🎯 开始创建OpenLayers MVT图层:', layerConfig)
  
  // 参数验证
  if (!layerConfig || !layerConfig.mvt_url) {
    const error = new Error('MVT URL不能为空')
    console.error('参数验证失败:', error.message)
    throw error
  }
  
  if (!checkOpenLayersMVTSupport()) {
    const error = new Error('OpenLayers MVT支持检查失败')
    console.error('MVT支持检查失败:', error.message)
    throw error
  }
  
  try {
    // 处理URL格式 - 与Leaflet版本保持一致
    let mvtUrl = layerConfig.mvt_url
    
    // 移除.pbf后缀（如果存在）
    if (mvtUrl.includes('.pbf')) {
      mvtUrl = mvtUrl.replace('.pbf', '')
      //console.log('移除.pbf后缀，新URL:', mvtUrl)
    }
    
    // 处理localhost URL
    if (mvtUrl.includes('localhost:3000')) {
      // 检查是否是 MBTiles 服务
      if (layerConfig.file_type === 'mbtiles' || mvtUrl.includes('/mbtiles/')) {
        // MBTiles 服务格式：http://localhost:3000/mbtiles/{文件名}/{z}/{x}/{y}
        const mbtilesMatch = mvtUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
        const fileName = mbtilesMatch[1] || 'default'
        mvtUrl = `http://localhost:3000/mbtiles/${fileName}/{z}/{x}/{y}`
      } else {
        // 普通 Martin 服务格式：http://localhost:3000/{tableName}/{z}/{x}/{y}
        const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
        mvtUrl = `http://localhost:3000/${tableName}/{z}/{x}/{y}`
      }
    }
    
    // 验证URL格式
    if (!mvtUrl.includes('{z}') || !mvtUrl.includes('{x}') || !mvtUrl.includes('{y}')) {
      console.warn('⚠️ MVT URL格式可能不正确，缺少{z},{x},{y}参数:', mvtUrl)
    }
    
    //console.log('MVT URL:', mvtUrl)
    //console.log('TileJSON URL:', layerConfig.tilejson_url)
    
    // 创建样式函数
    const styleFunction = createOpenLayersStyleFunction(
      layerConfig.style || {}, 
      layerConfig.file_type === 'dxf'
    )
    
    // 默认选项
    const defaultOptions = {
      opacity: layerConfig.opacity || 1.0,
      visible: layerConfig.visibility !== false,
      maxZoom: 22,
      properties: {
        layerId: layerConfig.id,
        layerName: layerConfig.layer_name,
        serviceType: 'martin'
      }
    }
    
    const mergedOptions = { ...defaultOptions, ...options }
    
    // 创建OpenLayers矢量切片图层
    const mvtLayer = new VectorTileLayer({
      source: new VectorTile({
        format: new MVT(),
        url: mvtUrl,
        maxZoom: mergedOptions.maxZoom,
        wrapX: false
      }),
      style: styleFunction,
      opacity: mergedOptions.opacity,
      visible: mergedOptions.visible,
      properties: mergedOptions.properties
    })
    
    // 添加与Leaflet对应的属性
    mvtLayer._popupEnabled = true
    mvtLayer._layerInfo = layerConfig
    
    // 添加事件监听
    mvtLayer.getSource().on('tileloaderror', (evt) => {
      console.warn('MVT瓦片加载失败:', evt.tile.src_ || 'Unknown tile')
    })
    
    mvtLayer.getSource().on('tileloadend', (evt) => {
      //console.log('MVT瓦片加载完成:', evt.tile.src_ || 'Unknown tile')
    })
    
    //console.log('✅ OpenLayers MVT图层创建成功')
    return mvtLayer
    
  } catch (error) {
    console.error('❌ OpenLayers MVT图层创建失败:', error)
    throw error
  }
}

/**
 * 更新MVT图层样式 - OpenLayers版本
 * @param {VectorTileLayer} mvtLayer - OpenLayers图层
 * @param {Object} newStyle - 新样式配置
 * @param {boolean} isDxf - 是否为DXF类型
 */
export function updateOpenLayersMVTLayerStyle(mvtLayer, newStyle, isDxf = false) {
  try {
    const newStyleFunction = createOpenLayersStyleFunction(newStyle, isDxf)
    mvtLayer.setStyle(newStyleFunction)
    //console.log('✅ MVT图层样式更新成功')
  } catch (error) {
    console.error('❌ MVT图层样式更新失败:', error)
    throw error
  }
}

/**
 * 获取MVT图层的瓦片网格信息 - 对应Leaflet的getLayerNames
 * @param {string} tilejsonUrl - TileJSON URL
 * @returns {Promise<Array>} 图层名称数组
 */
export async function getOpenLayersMVTLayerNames(tilejsonUrl) {
  try {
    const response = await fetch(tilejsonUrl)
    if (!response.ok) {
      throw new Error(`TileJSON请求失败: ${response.status} ${response.statusText}`)
    }
    
    const tilejsonData = await response.json()
    //console.log('TileJSON数据:', tilejsonData)
    
    let layerNames = ['default']  // 默认图层名
    if (tilejsonData.vector_layers && Array.isArray(tilejsonData.vector_layers)) {
      layerNames = tilejsonData.vector_layers.map(layer => layer.id)
    }
    
    //console.log('检测到的图层名称:', layerNames)
    return layerNames
    
  } catch (error) {
    console.error('获取MVT图层名称失败:', error)
    return ['default']
  }
}

export default {
  checkOpenLayersMVTSupport,
  createOpenLayersStyleFunction,
  createOpenLayersMVTLayer,
  updateOpenLayersMVTLayerStyle,
  getOpenLayersMVTLayerNames
} 