import dxfLayerStyles from '../config/dxfLayerStyles.json'

/**
 * 获取指定图层的样式配置
 * @param {string} layerName - 图层名称
 * @returns {object} 图层样式配置对象
 */
export function getLayerStyle(layerName) {
  return dxfLayerStyles.vectorTileLayerStyles[layerName] || dxfLayerStyles.defaultStyle
}

/**
 * 获取指定图层的配置信息
 * @param {string} layerName - 图层名称
 * @returns {object} 图层配置信息
 */
export function getLayerConfig(layerName) {
  return dxfLayerStyles.layerConfig[layerName] || {
    name: layerName,
    description: '未知图层',
    visible: true,
    zIndex: 1
  }
}

/**
 * 获取所有图层的样式配置
 * @returns {object} 所有图层的样式配置
 */
export function getAllLayerStyles() {
  return dxfLayerStyles.vectorTileLayerStyles
}

/**
 * 获取所有图层的配置信息
 * @returns {object} 所有图层的配置信息
 */
export function getAllLayerConfigs() {
  return dxfLayerStyles.layerConfig
}

/**
 * 根据图层类型动态调整样式
 * @param {string} layerName - 图层名称
 * @param {number} zoom - 缩放级别
 * @param {object} properties - 要素属性
 * @returns {object} 调整后的样式配置
 */
export function getDynamicLayerStyle(layerName, zoom, properties = {}) {
  const baseStyle = getLayerStyle(layerName)
  const adjustedStyle = { ...baseStyle }

  // 根据缩放级别调整样式
  if (zoom < 10) {
    // 小比例尺时减少细节
    adjustedStyle.weight = Math.max(adjustedStyle.weight - 0.5, 0.5)
    adjustedStyle.opacity = Math.max(adjustedStyle.opacity - 0.2, 0.3)
  } else if (zoom > 15) {
    // 大比例尺时增加细节
    adjustedStyle.weight = adjustedStyle.weight + 0.5
    adjustedStyle.opacity = Math.min(adjustedStyle.opacity + 0.1, 1)
  }

  // 特殊图层的缩放处理
  if (layerName === 'sqx' && zoom < 14) {
    // 1米等高线在小比例尺时隐藏
    adjustedStyle.opacity = 0
  }

  if (layerName === 'jqx' && zoom < 12) {
    // 5米等高线在小比例尺时减少透明度
    adjustedStyle.opacity = Math.max(adjustedStyle.opacity - 0.3, 0.2)
  }

  return adjustedStyle
}

/**
 * 获取图层的显示优先级
 * @param {string} layerName - 图层名称
 * @returns {number} 显示优先级（zIndex）
 */
export function getLayerZIndex(layerName) {
  const config = getLayerConfig(layerName)
  return config.zIndex
}

/**
 * 检查图层是否默认可见
 * @param {string} layerName - 图层名称
 * @returns {boolean} 是否可见
 */
export function isLayerVisible(layerName) {
  const config = getLayerConfig(layerName)
  return config.visible
}

/**
 * 获取图层分组信息
 * @returns {object} 按类型分组的图层信息
 */
export function getLayerGroups() {
  return {
    '地形相关': ['DMTZ', 'DGX', 'GCD', 'jqx', 'sqx'],
    '水系设施': ['SXSS'],
    '道路交通': ['DLSS'],
    '建筑居住': ['JMD', 'DLDW'],
    '植被绿化': ['ZBTZ'],
    '管线设施': ['GXYZ'],
    '边界控制': ['JJ', 'KZD', 'JZD', 'TK'],
    '辅助图层': ['ASSIST']
  }
}

export default {
  getLayerStyle,
  getLayerConfig,
  getAllLayerStyles,
  getAllLayerConfigs,
  getDynamicLayerStyle,
  getLayerZIndex,
  isLayerVisible,
  getLayerGroups
} 