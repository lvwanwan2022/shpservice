/**
 * 中国地图服务配置
 */

export const MAP_SERVICES = {
  // 高德地图
  AMAP: {
    name: '高德地图',
    url: 'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
    options: {
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      maxZoom: 20,
      minZoom: 1,
      subdomains: ['1', '2', '3', '4'],
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    }
  },
  
  // 高德卫星图
  AMAP_SATELLITE: {
    name: '高德卫星图',
    url: 'https://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
    options: {
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      maxZoom: 20,
      minZoom: 1,
      subdomains: ['1', '2', '3', '4'],
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    }
  },
  
  // OpenStreetMap
  OSM: {
    name: 'OpenStreetMap',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: {
      attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
      maxZoom: 19,
      minZoom: 1,
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    }
  },
  
  // Esri 世界影像
  ESRI_WORLD_IMAGERY: {
    name: 'Esri 世界影像',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    options: {
      attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, DigitalGlobe, GeoEye, i-cubed, USDA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community',
      maxZoom: 19,
      minZoom: 1,
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    }
  },
  
  // 腾讯地图
  TENCENT: {
    name: '腾讯地图',
    url: 'https://rt{s}.map.gtimg.com/realtimerender?z={z}&x={x}&y={y}&type=vector&style=0',
    options: {
      attribution: '&copy; <a href="https://map.qq.com/">腾讯地图</a>',
      maxZoom: 20,
      minZoom: 1,
      subdomains: ['0', '1', '2', '3'],
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    }
  },
  
  // 天地图矢量 (需要申请密钥)
  TIANDITU_VEC: {
    name: '天地图矢量',
    url: 'https://t{s}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={apikey}',
    options: {
      attribution: '&copy; <a href="https://www.tianditu.gov.cn/">天地图</a>',
      maxZoom: 20,
      minZoom: 1,
      subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    },
    requiresApiKey: true
  },
  
  // 天地图卫星 (需要申请密钥)
  TIANDITU_IMG: {
    name: '天地图卫星',
    url: 'https://t{s}.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={apikey}',
    options: {
      attribution: '&copy; <a href="https://www.tianditu.gov.cn/">天地图</a>',
      maxZoom: 20,
      minZoom: 1,
      subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
      crossOrigin: true,
      detectRetina: true,
      tileSize: 256,
      zoomOffset: 0
    },
    requiresApiKey: true
  },
  
  // 开源和公共服务
  FREE_SERVICES: {
    name: '免费地图服务',
    services: {}
  }
}

// 服务优先级（按可靠性和速度排序）
export const SERVICE_PRIORITY = [
  'AMAP',              // 高德地图 - 首选
  'AMAP_SATELLITE',    // 高德卫星图 - 备选1
  'OSM',               // OpenStreetMap - 备选2
  'ESRI_WORLD_IMAGERY', // Esri世界影像 - 备选3
  'TENCENT'            // 腾讯地图 - 备选4
]

// 获取地图服务配置
export function getMapService(serviceKey, apiKey = null) {
  const service = MAP_SERVICES[serviceKey]
  if (!service) {
    throw new Error(`未知的地图服务: ${serviceKey}`)
  }
  
  // 如果需要API密钥但未提供
  if (service.requiresApiKey && !apiKey) {
    console.warn(`地图服务 ${service.name} 需要API密钥`)
    return null
  }
  
  // 替换API密钥
  let url = service.url
  if (apiKey) {
    url = url.replace('{apikey}', apiKey)
  }
  
  return {
    ...service,
    url
  }
}

// 创建地图图层
export function createMapLayer(serviceKey, apiKey = null) {
  const service = getMapService(serviceKey, apiKey)
  if (!service) {
    return null
  }
  
  const L = require('leaflet')
  return L.tileLayer(service.url, service.options)
}

// 创建带故障转移的地图图层
export function createMapLayerWithFallback(serviceKeys = SERVICE_PRIORITY, apiKey = null) {
  for (const serviceKey of serviceKeys) {
    try {
      const layer = createMapLayer(serviceKey, apiKey)
      if (layer) {
        //console.log(`使用地图服务: ${MAP_SERVICES[serviceKey].name}`)
        return layer
      }
    } catch (error) {
      console.warn(`地图服务 ${serviceKey} 创建失败:`, error)
    }
  }
  
  throw new Error('所有地图服务都不可用')
} 