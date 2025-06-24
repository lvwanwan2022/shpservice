/**
 * 地图缩放级别管理工具
 * 处理不同底图服务的缩放级别限制和错误处理
 */

// 不同底图服务的缩放级别配置
export const BASE_MAP_ZOOM_CONFIG = {
  gaode: {
    name: '高德地图',
    maxZoom: 18,
    minZoom: 3,
    maxNativeZoom: 18,      // 原生瓦片最大级别
    maxOversampleZoom: 23,  // 允许过采样的最大级别
    description: '高德地图标准版，支持3-18级缩放，可过采样到23级'
  },
  gaodeSatellite: {
    name: '高德卫星图',
    maxZoom: 18,
    minZoom: 3,
    maxNativeZoom: 18,
    maxOversampleZoom: 23,
    description: '高德卫星影像，支持3-18级缩放，可过采样到23级'
  },
  osm: {
    name: 'OpenStreetMap',
    maxZoom: 19,
    minZoom: 1,
    maxNativeZoom: 19,
    maxOversampleZoom: 23,
    description: 'OpenStreetMap开源地图，支持1-19级缩放，可过采样到23级'
  },
  esriSatellite: {
    name: 'Esri世界影像',
    maxZoom: 21,
    minZoom: 1,
    maxNativeZoom: 21,      // Esri原生支持21级
    maxOversampleZoom: 23,  // 允许过采样到更高级别
    description: 'Esri全球卫星影像，原生支持1-21级缩放，可过采样到23级'
  }
}

/**
 * 获取底图的缩放级别配置
 * @param {string} baseMapType 底图类型
 * @returns {object} 缩放级别配置
 */
export function getBaseMapZoomConfig(baseMapType) {
  return BASE_MAP_ZOOM_CONFIG[baseMapType] || {
    name: '未知底图',
    maxZoom: 18,
    minZoom: 1,
    description: '默认缩放级别配置'
  }
}

/**
 * 检查缩放级别是否在底图支持范围内
 * @param {number} zoom 当前缩放级别
 * @param {string} baseMapType 底图类型
 * @returns {object} 检查结果
 */
export function validateZoomLevel(zoom, baseMapType) {
  const config = getBaseMapZoomConfig(baseMapType)
  
  return {
    isValid: zoom >= config.minZoom && zoom <= config.maxOversampleZoom,
    isNative: zoom >= config.minZoom && zoom <= config.maxNativeZoom,
    isOversampled: zoom > config.maxNativeZoom && zoom <= config.maxOversampleZoom,
    tooHigh: zoom > config.maxOversampleZoom,
    tooLow: zoom < config.minZoom,
    maxZoom: config.maxZoom,
    minZoom: config.minZoom,
    maxNativeZoom: config.maxNativeZoom,
    maxOversampleZoom: config.maxOversampleZoom,
    suggestedZoom: zoom > config.maxOversampleZoom ? config.maxOversampleZoom : 
                   zoom < config.minZoom ? config.minZoom : zoom
  }
}

/**
 * 检查当前缩放级别是否需要过采样
 * @param {number} zoom 当前缩放级别
 * @param {string} baseMapType 底图类型
 * @returns {object} 过采样检查结果
 */
export function checkOversamplingStatus(zoom, baseMapType) {
  const config = getBaseMapZoomConfig(baseMapType)
  const validation = validateZoomLevel(zoom, baseMapType)
  
  return {
    needsOversampling: validation.isOversampled,
    oversampleLevel: validation.isOversampled ? zoom - config.maxNativeZoom : 0,
    sourceZoom: validation.isOversampled ? config.maxNativeZoom : zoom,
    targetZoom: zoom,
    scaleFactor: validation.isOversampled ? Math.pow(2, zoom - config.maxNativeZoom) : 1,
    qualityWarning: validation.isOversampled ? '使用低级别瓦片放大显示，图像质量可能降低' : null
  }
}

/**
 * 自动调整缩放级别到底图支持范围内
 * @param {object} map 地图实例（Leaflet或OpenLayers）
 * @param {string} baseMapType 底图类型
 * @param {string} mapType 地图库类型 ('leaflet' | 'openlayers')
 */
export function adjustZoomToBaseMapRange(map, baseMapType, mapType = 'leaflet') {
  if (!map) return
  
  const currentZoom = mapType === 'leaflet' ? map.getZoom() : map.getView().getZoom()
  const validation = validateZoomLevel(currentZoom, baseMapType)
  
  if (!validation.isValid) {
    console.warn(`缩放级别调整: ${currentZoom} -> ${validation.suggestedZoom} (${baseMapType})`)
    
    if (mapType === 'leaflet') {
      map.setZoom(validation.suggestedZoom)
    } else {
      map.getView().setZoom(validation.suggestedZoom)
    }
    
    return {
      adjusted: true,
      oldZoom: currentZoom,
      newZoom: validation.suggestedZoom,
      reason: validation.tooHigh ? '超出最大级别' : '低于最小级别'
    }
  }
  
  return { adjusted: false }
}

/**
 * 创建缩放级别监听器（Leaflet版本）
 * @param {object} map Leaflet地图实例
 * @param {function} getCurrentBaseMapType 获取当前底图类型的函数
 */
export function createLeafletZoomListener(map, getCurrentBaseMapType) {
  if (!map) return
  
  map.on('zoomend', () => {
    const currentZoom = map.getZoom()
    const baseMapType = getCurrentBaseMapType()
    const validation = validateZoomLevel(currentZoom, baseMapType)
    const oversamplingStatus = checkOversamplingStatus(currentZoom, baseMapType)
    
    if (validation.tooHigh) {
      console.warn(`缩放级别过高: ${currentZoom}/${validation.maxOversampleZoom} (${baseMapType})`)
    } else if (validation.tooLow) {
      console.warn(`缩放级别过低: ${currentZoom}/${validation.minZoom} (${baseMapType})`)
    } else if (oversamplingStatus.needsOversampling) {
      console.info(`${baseMapType}: 过采样显示 Z${currentZoom} (源瓦片Z${oversamplingStatus.sourceZoom}, 放大${oversamplingStatus.oversampleLevel}级)`)
      if (oversamplingStatus.qualityWarning) {
        console.info(`提示: ${oversamplingStatus.qualityWarning}`)
      }
    }
  })
}

/**
 * 创建缩放级别监听器（OpenLayers版本）
 * @param {object} map OpenLayers地图实例
 * @param {function} getCurrentBaseMapType 获取当前底图类型的函数
 */
export function createOpenLayersZoomListener(map, getCurrentBaseMapType) {
  if (!map) return
  
  map.getView().on('change:resolution', () => {
    const currentZoom = map.getView().getZoom()
    const baseMapType = getCurrentBaseMapType()
    const validation = validateZoomLevel(currentZoom, baseMapType)
    const oversamplingStatus = checkOversamplingStatus(currentZoom, baseMapType)
    
    if (validation.tooHigh) {
      console.warn(`缩放级别过高: ${Math.floor(currentZoom)}/${validation.maxOversampleZoom} (${baseMapType})`)
    } else if (validation.tooLow) {
      console.warn(`缩放级别过低: ${Math.floor(currentZoom)}/${validation.minZoom} (${baseMapType})`)
    } else if (oversamplingStatus.needsOversampling) {
      console.info(`${baseMapType}: 过采样显示 Z${Math.floor(currentZoom)} (源瓦片Z${oversamplingStatus.sourceZoom}, 放大${oversamplingStatus.oversampleLevel}级)`)
      if (oversamplingStatus.qualityWarning) {
        console.info(`提示: ${oversamplingStatus.qualityWarning}`)
      }
    }
  })
}

/**
 * 获取推荐的缩放级别范围提示文本
 * @param {string} baseMapType 底图类型
 * @returns {string} 提示文本
 */
export function getZoomRangeHint(baseMapType) {
  const config = getBaseMapZoomConfig(baseMapType)
  return `${config.name}支持${config.minZoom}-${config.maxNativeZoom}级原生缩放，可过采样到${config.maxOversampleZoom}级`
}

/**
 * 获取当前缩放状态的详细信息
 * @param {number} zoom 当前缩放级别
 * @param {string} baseMapType 底图类型
 * @returns {object} 详细状态信息
 */
export function getZoomStatusInfo(zoom, baseMapType) {
  const config = getBaseMapZoomConfig(baseMapType)
  const validation = validateZoomLevel(zoom, baseMapType)
  const oversamplingStatus = checkOversamplingStatus(zoom, baseMapType)
  
  let status = 'normal'
  let message = '正常显示'
  let color = '#67C23A' // 绿色
  
  if (validation.tooHigh) {
    status = 'too-high'
    message = '缩放级别过高'
    color = '#F56C6C' // 红色
  } else if (validation.tooLow) {
    status = 'too-low'
    message = '缩放级别过低'
    color = '#F56C6C' // 红色
  } else if (oversamplingStatus.needsOversampling) {
    status = 'oversampled'
    message = `过采样显示 (${oversamplingStatus.oversampleLevel}级放大)`
    color = '#E6A23C' // 橙色
  }
  
  return {
    status,
    message,
    color,
    zoom,
    baseMapType,
    baseMapName: config.name,
    isNative: validation.isNative,
    isOversampled: validation.isOversampled,
    nativeRange: `${config.minZoom}-${config.maxNativeZoom}`,
    oversampleRange: `${config.maxNativeZoom + 1}-${config.maxOversampleZoom}`,
    ...oversamplingStatus
  }
}

/**
 * 创建过采样质量评估
 * @param {number} zoom 当前缩放级别
 * @param {string} baseMapType 底图类型
 * @returns {object} 质量评估结果
 */
export function assessOversamplingQuality(zoom, baseMapType) {
  const oversamplingStatus = checkOversamplingStatus(zoom, baseMapType)
  
  if (!oversamplingStatus.needsOversampling) {
    return {
      quality: 'excellent',
      score: 100,
      description: '原生瓦片，质量最佳'
    }
  }
  
  const oversampleLevel = oversamplingStatus.oversampleLevel
  let quality, score, description
  
  if (oversampleLevel <= 1) {
    quality = 'good'
    score = 85
    description = '轻微过采样，质量良好'
  } else if (oversampleLevel <= 2) {
    quality = 'fair'
    score = 70
    description = '中度过采样，质量一般'
  } else {
    quality = 'poor'
    score = 50
    description = '重度过采样，质量较差'
  }
  
  return {
    quality,
    score,
    description,
    oversampleLevel,
    scaleFactor: oversamplingStatus.scaleFactor,
    recommendation: oversampleLevel > 2 ? '建议切换到支持更高级别的底图' : null
  }
} 