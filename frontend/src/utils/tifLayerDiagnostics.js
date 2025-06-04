/*
 * TIF图层诊断工具
 * 用于检测和处理TIF图层的加载问题
 */

import L from 'leaflet'

/**
 * 诊断TIF图层
 * @param {Object} layerInfo - 图层信息
 * @param {L.Map} map - Leaflet地图实例
 * @returns {Promise<Object>} 诊断结果
 */
export const diagnoseTifLayer = async (layerInfo, /* map */) => {
  const result = {
    layerId: layerInfo.id,
    layerName: layerInfo.layer_name,
    success: false,
    errors: [],
    warnings: [],
    suggestions: []
  }

  try {
    // 检查图层基本信息
    if (!layerInfo.wms_url) {
      result.errors.push('缺少WMS URL')
      return result
    }

    if (!layerInfo.layer_name) {
      result.errors.push('缺少图层名称')
      return result
    }

    // 检查WMS服务可访问性
    const capabilitiesUrl = `${layerInfo.wms_url}?service=WMS&request=GetCapabilities&version=1.1.1`
    
    try {
      const response = await fetch(capabilitiesUrl, { 
        method: 'GET',
        timeout: 10000 
      })
      
      if (!response.ok) {
        result.errors.push(`WMS服务不可访问: HTTP ${response.status}`)
        return result
      }

      const capabilitiesText = await response.text()
      
      // 检查是否包含图层
      if (!capabilitiesText.toLowerCase().includes(layerInfo.layer_name.toLowerCase())) {
        result.warnings.push('在WMS Capabilities中未找到指定图层名称')
        result.suggestions.push('检查图层名称是否正确')
      }

    } catch (networkError) {
      result.errors.push(`网络错误: ${networkError.message}`)
      result.suggestions.push('检查网络连接和服务器状态')
    }

    // 检查坐标系
    if (!layerInfo.crs && !layerInfo.srs) {
      result.warnings.push('未指定坐标参考系统')
      result.suggestions.push('建议明确指定CRS参数')
    }

    // 如果没有严重错误，标记为成功
    if (result.errors.length === 0) {
      result.success = true
    }

  } catch (error) {
    result.errors.push(`诊断过程异常: ${error.message}`)
  }

  return result
}

/**
 * 创建改进的WMS图层
 * @param {Object} layerInfo - 图层信息
 * @param {Object} options - 额外选项
 * @returns {L.TileLayer.WMS} WMS图层实例
 */
export const createImprovedWmsLayer = (layerInfo, options = {}) => {
  const defaultOptions = {
    layers: layerInfo.layer_name,
    format: 'image/png',
    transparent: true,
    attribution: '© GeoServer',
    maxZoom: 22,
    minZoom: 1,
    tileSize: 256,
    zoomOffset: 0,
    detectRetina: true,
    crs: L.CRS.EPSG3857,
    ...options
  }

  // 处理坐标系
  if (layerInfo.crs) {
    defaultOptions.crs = layerInfo.crs
  }
  if (layerInfo.srs) {
    defaultOptions.srs = layerInfo.srs
  }

  // 创建WMS图层
  const wmsLayer = L.tileLayer.wms(layerInfo.wms_url, defaultOptions)

  // 添加错误处理
  wmsLayer.on('tileerror', function(error) {
    console.warn('TIF图层瓦片加载错误:', error)
  })

  // 添加加载完成事件
  wmsLayer.on('load', function() {
    console.log('TIF图层加载完成:', layerInfo.layer_name)
  })

  return wmsLayer
}

/**
 * 获取图层边界框
 * @param {Object} layerInfo - 图层信息
 * @returns {Promise<L.LatLngBounds|null>} 图层边界框
 */
export const getLayerBounds = async (layerInfo) => {
  try {
    if (layerInfo.bbox) {
      const bbox = layerInfo.bbox
      if (Array.isArray(bbox) && bbox.length === 4) {
        return L.latLngBounds(
          [bbox[1], bbox[0]], // sw
          [bbox[3], bbox[2]]  // ne
        )
      }
    }

    // 尝试从WMS Capabilities获取边界框
    const capabilitiesUrl = `${layerInfo.wms_url}?service=WMS&request=GetCapabilities&version=1.1.1`
    const response = await fetch(capabilitiesUrl)
    
    if (response.ok) {
      const capabilitiesText = await response.text()
      const parser = new DOMParser()
      const xmlDoc = parser.parseFromString(capabilitiesText, 'text/xml')
      
      // 查找图层的边界框信息
      const layers = xmlDoc.getElementsByTagName('Layer')
      for (let layer of layers) {
        const nameElement = layer.getElementsByTagName('Name')[0]
        if (nameElement && nameElement.textContent === layerInfo.layer_name) {
          const bboxElement = layer.getElementsByTagName('BoundingBox')[0]
          if (bboxElement) {
            const minx = parseFloat(bboxElement.getAttribute('minx'))
            const miny = parseFloat(bboxElement.getAttribute('miny'))
            const maxx = parseFloat(bboxElement.getAttribute('maxx'))
            const maxy = parseFloat(bboxElement.getAttribute('maxy'))
            
            return L.latLngBounds([miny, minx], [maxy, maxx])
          }
        }
      }
    }
  } catch (error) {
    console.warn('获取图层边界框失败:', error)
  }
  
  return null
}

/**
 * 检查TIF图层支持的格式
 * @param {string} wmsUrl - WMS服务URL
 * @returns {Promise<Array>} 支持的格式列表
 */
export const checkSupportedFormats = async (wmsUrl) => {
  const formats = ['image/png', 'image/jpeg', 'image/tiff', 'image/geotiff']
  const supportedFormats = []
  
  for (const format of formats) {
    try {
      const testUrl = `${wmsUrl}?service=WMS&version=1.1.1&request=GetMap&layers=test&format=${format}&width=1&height=1&bbox=0,0,1,1&srs=EPSG:4326`
      const response = await fetch(testUrl, { method: 'HEAD' })
      
      if (response.ok || response.status === 400) {
        // 400错误通常表示参数错误，但格式是支持的
        supportedFormats.push(format)
      }
    } catch (error) {
      // 忽略网络错误
    }
  }
  
  return supportedFormats
} 