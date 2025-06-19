/**
 * Martin Vector Tile 服务配置
 */

// Martin服务配置
export const martinConfig = {
  // Martin服务地址
  //baseUrl: 'http://localhost:3000',
  baseUrl: 'http://localhost:3000',
  
  // 数据库表配置
  tables: {
    // DXF矢量数据表
    'vector_05492e03': {
      name: 'DXF矢量图层',
      description: 'DXF文件转换的矢量数据',
      layerField: 'layer', // 图层名称字段
      geometryField: 'geom',
      srid: 3857,
      // 表字段映射
      fields: {
        gid: 'gid',
        layer: 'layer',
        paperspace: 'paperspace', 
        subclasses: 'subclasses',
        linetype: 'linetype',
        entityhandle: 'entityhandle',
        text: 'text',
        rawcodevalues: 'rawcodevalues'
      }
    }
  },
  
  // 默认地图配置
  defaultMapOptions: {
    center: [39.9042, 116.4074],
    zoom: 13,
    minZoom: 8,
    maxZoom: 20,
    crs: 'EPSG:3857'
  }
}

/**
 * 获取指定表的Martin Vector Tile URL
 * @param {string} tableName - 表名
 * @param {string} baseUrl - Martin服务基础URL
 * @returns {string} Vector Tile URL
 */
export function getMartinTileUrl(tableName, baseUrl = martinConfig.baseUrl) {
  return `${baseUrl}/${tableName}/{z}/{x}/{y}.pbf`
}

/**
 * 获取表的元数据信息
 * @param {string} tableName - 表名  
 * @returns {object} 表元数据
 */
export function getTableMetadata(tableName) {
  return martinConfig.tables[tableName] || {
    name: tableName,
    description: '未知表',
    layerField: 'layer',
    geometryField: 'geom',
    srid: 3857,
    fields: {}
  }
}

/**
 * 根据PostGIS表结构创建Martin样式配置
 * 这个函数将DXF图层样式映射到Martin的vector tile格式
 * @param {object} layerStyles - DXF图层样式配置
 * @param {string} layerField - 图层字段名（默认为'layer'）
 * @returns {object} Martin兼容的样式配置
 */
export function createMartinStyleConfig(layerStyles, layerField = 'layer') {
  const martinStyles = {}
  
  // 为每个图层创建样式函数
  Object.keys(layerStyles).forEach(layerName => {
    martinStyles[layerName] = function(properties, zoom) {
      // 检查要素的图层字段是否匹配
      if (properties[layerField] === layerName) {
        const baseStyle = layerStyles[layerName]
        
        // 根据缩放级别动态调整样式
        const adjustedStyle = { ...baseStyle }
        
        // 缩放级别样式调整
        if (zoom < 10) {
          adjustedStyle.weight = Math.max((adjustedStyle.weight || 1) - 0.5, 0.5)
          adjustedStyle.opacity = Math.max((adjustedStyle.opacity || 0.7) - 0.2, 0.3)
        } else if (zoom > 15) {
          adjustedStyle.weight = (adjustedStyle.weight || 1) + 0.5
          adjustedStyle.opacity = Math.min((adjustedStyle.opacity || 0.7) + 0.1, 1)
        }
        
        // 特殊图层处理
        if (layerName === 'sqx' && zoom < 14) {
          adjustedStyle.opacity = 0 // 1米等高线在小比例尺时隐藏
        }
        
        if (layerName === 'jqx' && zoom < 12) {
          adjustedStyle.opacity = Math.max((adjustedStyle.opacity || 0.6) - 0.3, 0.2)
        }
        
        return adjustedStyle
      }
      
      // 如果图层不匹配，返回透明样式
      return {
        opacity: 0,
        fillOpacity: 0
      }
    }
  })
  
  return martinStyles
}

/**
 * 创建用于所有图层的通用样式函数
 * 这个函数会根据要素的layer属性动态选择对应的样式
 * @param {object} allLayerStyles - 所有图层样式配置
 * @param {string} layerField - 图层字段名
 * @returns {object} 包含单个样式函数的配置对象
 */
export function createUniversalStyleFunction(allLayerStyles, layerField = 'layer') {
  return {
    // 使用表名作为key，martin会将此应用到所有要素
    [Object.keys(martinConfig.tables)[0]]: function(properties, zoom) {
      const layerName = properties[layerField]
      
      // 获取对应图层的基础样式
      const baseStyle = allLayerStyles[layerName]
      if (!baseStyle) {
        // 如果没有找到对应样式，使用默认样式
        return {
          weight: 1,
          color: '#666666',
          opacity: 0.7,
          fillColor: '#CCCCCC',
          fill: false,
          fillOpacity: 0.3
        }
      }
      
      // 复制基础样式
      const adjustedStyle = { ...baseStyle }
      
      // 根据缩放级别调整样式
      if (zoom < 10) {
        adjustedStyle.weight = Math.max((adjustedStyle.weight || 1) - 0.5, 0.5)
        adjustedStyle.opacity = Math.max((adjustedStyle.opacity || 0.7) - 0.2, 0.3)
      } else if (zoom > 15) {
        adjustedStyle.weight = (adjustedStyle.weight || 1) + 0.5
        adjustedStyle.opacity = Math.min((adjustedStyle.opacity || 0.7) + 0.1, 1)
      }
      
      // 特殊图层的缩放处理
      if (layerName === 'sqx' && zoom < 14) {
        adjustedStyle.opacity = 0
      }
      
      if (layerName === 'jqx' && zoom < 12) {
        adjustedStyle.opacity = Math.max((adjustedStyle.opacity || 0.6) - 0.3, 0.2)
      }
      
      return adjustedStyle
    }
  }
}

/**
 * 验证Martin服务是否可用
 * @param {string} baseUrl - Martin服务地址
 * @returns {Promise<boolean>} 服务是否可用
 */
export async function checkMartinService(baseUrl = martinConfig.baseUrl) {
  try {
    const response = await fetch(`${baseUrl}/catalog`)
    return response.ok
  } catch (error) {
    console.error('Martin服务连接失败:', error)
    return false
  }
}

/**
 * 获取Martin服务的数据目录
 * @param {string} baseUrl - Martin服务地址
 * @returns {Promise<object>} 数据目录信息
 */
export async function getMartinCatalog(baseUrl = martinConfig.baseUrl) {
  try {
    const response = await fetch(`${baseUrl}/catalog`)
    if (response.ok) {
      return await response.json()
    }
    throw new Error('获取目录失败')
  } catch (error) {
    console.error('获取Martin目录失败:', error)
    return null
  }
}

export default {
  martinConfig,
  getMartinTileUrl,
  getTableMetadata,
  createMartinStyleConfig,
  createUniversalStyleFunction,
  checkMartinService,
  getMartinCatalog
} 