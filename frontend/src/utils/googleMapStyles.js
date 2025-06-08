/**
 * Google Maps 风格的现代化配色方案
 * 参考Google官方设计指南和Material Design
 */

// Google官方色彩palette
export const GoogleColors = {
  // 主色调
  primary: {
    blue: '#4285F4',      // Google蓝
    green: '#0F9D58',     // Google绿
    yellow: '#FBBB05',    // Google黄
    red: '#E94335'        // Google红
  },
  
  // 辅助色调
  secondary: {
    grey600: '#757575',   // 深灰
    grey500: '#9E9E9E',   // 中灰
    grey400: '#BDBDBD',   // 浅灰
    white: '#FFFFFF'      // 白色
  },
  
  // 地图专用色彩
  maps: {
    // 地形颜色（来自Google Maps Light主题）
    terrain: {
      forest: '#C2E4CB',      // 森林绿
      desert: '#FEE193',      // 沙漠黄
      mountain: '#F2F3F5',    // 山地灰
      water: '#9CC0FA',       // 水体蓝
      park: '#A8DAB5'         // 公园绿
    },
    
    // 道路颜色
    roads: {
      highway: '#FFFFFF',     // 高速公路-白色
      arterial: '#FEFEFE',    // 主干道-浅白
      local: '#F8F8F8',       // 地方道路-米白
      pedestrian: '#FAFAFA'   // 步行道-极浅灰
    },
    
    // 兴趣点颜色
    poi: {
      business: '#4285F4',    // 商业-蓝色
      education: '#0F9D58',   // 教育-绿色
      medical: '#E94335',     // 医疗-红色
      recreation: '#FBBB05',  // 娱乐-黄色
      transport: '#9E9E9E'    // 交通-灰色
    }
  }
}

// 现代化MVT样式配置
export const ModernMVTStyles = {
  /**
   * 点要素样式
   */
  point: {
    default: {
      color: GoogleColors.primary.blue,
      fillColor: GoogleColors.primary.blue,
      radius: 4,
      fill: true,
      fillOpacity: 0.8,
      weight: 2,
      opacity: 1,
      // CSS过渡动画
      className: 'mvt-point-default'
    },
    
    // 不同类型的点样式
    business: {
      color: GoogleColors.primary.blue,
      fillColor: GoogleColors.primary.blue,
      radius: 4,
      fill: true,
      fillOpacity: 0.85,
      weight: 1,
      opacity: 1,
      className: 'mvt-point-business'
    },
    
    landmark: {
      color: GoogleColors.primary.red,
      fillColor: GoogleColors.primary.red,
      radius: 5,
      fill: true,
      fillOpacity: 0.9,
      weight: 2,
      opacity: 1,
      className: 'mvt-point-landmark'
    },
    
    transit: {
      color: GoogleColors.secondary.grey600,
      fillColor: GoogleColors.secondary.grey600,
      radius: 3,
      fill: true,
      fillOpacity: 0.8,
      weight: 1,
      opacity: 1,
      className: 'mvt-point-transit'
    }
  },

  /**
   * 线要素样式
   */
  line: {
    default: {
      color: GoogleColors.secondary.grey600,
      weight: 2,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-default'
    },
    
    // 不同类型的线样式
    highway: {
      color: GoogleColors.primary.blue,
      weight: 4,
      opacity: 0.9,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-highway'
    },
    
    arterial: {
      color: GoogleColors.secondary.grey600,
      weight: 3,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-arterial'
    },
    
    local: {
      color: GoogleColors.secondary.grey500,
      weight: 2,
      opacity: 0.7,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-local'
    },
    
    waterway: {
      color: GoogleColors.maps.terrain.water,
      weight: 2,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-waterway'
    }
  },

  /**
   * 面要素样式
   */
  polygon: {
    default: {
      fillColor: GoogleColors.maps.terrain.park,
      color: GoogleColors.secondary.grey500,
      weight: 1,
      fill: true,
      fillOpacity: 0.3,
      opacity: 0.6,
      className: 'mvt-polygon-default'
    },
    
    // 不同类型的面样式
    building: {
      fillColor: GoogleColors.secondary.grey400,
      color: GoogleColors.secondary.grey600,
      weight: 1,
      fill: true,
      fillOpacity: 0.4,
      opacity: 0.8,
      className: 'mvt-polygon-building'
    },
    
    park: {
      fillColor: GoogleColors.maps.terrain.park,
      color: GoogleColors.primary.green,
      weight: 1,
      fill: true,
      fillOpacity: 0.4,
      opacity: 0.7,
      className: 'mvt-polygon-park'
    },
    
    water: {
      fillColor: GoogleColors.maps.terrain.water,
      color: GoogleColors.primary.blue,
      weight: 1,
      fill: true,
      fillOpacity: 0.5,
      opacity: 0.8,
      className: 'mvt-polygon-water'
    },
    
    forest: {
      fillColor: GoogleColors.maps.terrain.forest,
      color: GoogleColors.primary.green,
      weight: 1,
      fill: true,
      fillOpacity: 0.3,
      opacity: 0.6,
      className: 'mvt-polygon-forest'
    }
  },

  /**
   * 悬停状态样式
   */
  hover: {
    point: {
      color: GoogleColors.primary.red,
      fillColor: GoogleColors.primary.red,
      radius: 6,
      fill: true,
      fillOpacity: 0.9,
      weight: 3,
      opacity: 1,
      className: 'mvt-point-hover'
    },
    
    line: {
      color: GoogleColors.primary.blue,
      weight: 4,
      opacity: 1,
      className: 'mvt-line-hover'
    },
    
    polygon: {
      fillColor: GoogleColors.primary.yellow,
      color: GoogleColors.primary.blue,
      weight: 2,
      fill: true,
      fillOpacity: 0.6,
      opacity: 1,
      className: 'mvt-polygon-hover'
    }
  }
}

/**
 * CSS动画类
 */
export const MVTAnimationCSS = `
/* 基础过渡动画 */
.mvt-point-default,
.mvt-point-business,
.mvt-point-landmark,
.mvt-point-transit {
  transition: all 0.2s ease-in-out !important;
  transform-origin: center !important;
}

.mvt-line-default,
.mvt-line-highway,
.mvt-line-arterial,
.mvt-line-local,
.mvt-line-waterway {
  transition: all 0.2s ease-in-out !important;
}

.mvt-polygon-default,
.mvt-polygon-building,
.mvt-polygon-park,
.mvt-polygon-water,
.mvt-polygon-forest {
  transition: all 0.25s ease-in-out !important;
}

/* 悬停动画效果 */
.mvt-point-hover {
  animation: pulse 1.5s infinite ease-in-out !important;
  transform: scale(1.2) !important;
  transition: all 0.15s ease-out !important;
}

.mvt-line-hover {
  animation: lineGlow 2s infinite ease-in-out !important;
  transition: all 0.2s ease-out !important;
}

.mvt-polygon-hover {
  animation: polygonGlow 2s infinite ease-in-out !important;
  transition: all 0.25s ease-out !important;
}

/* 关键帧动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 0.8;
    transform: scale(1.2);
  }
  50% {
    opacity: 1;
    transform: scale(1.4);
  }
}

@keyframes lineGlow {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

@keyframes polygonGlow {
  0%, 100% {
    fill-opacity: 0.6;
  }
  50% {
    fill-opacity: 0.8;
  }
}

/* 加载动画 */
.mvt-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 平滑缩放过渡 */
.leaflet-zoom-anim .mvt-point-default,
.leaflet-zoom-anim .mvt-point-business,
.leaflet-zoom-anim .mvt-point-landmark,
.leaflet-zoom-anim .mvt-point-transit {
  transition: none !important;
}

/* 弹窗样式增强 */
.mvt-popup {
  position: relative;
}

.mvt-popup-timer {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #4285F4, #0F9D58);
  transition: width 0.1s linear;
  border-radius: 0 0 4px 4px;
}

.mvt-popup-timer.warning {
  background: linear-gradient(90deg, #E94335, #FBBB05);
}

.leaflet-popup-content-wrapper {
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

.leaflet-popup-content {
  margin: 12px 16px !important;
  line-height: 1.4 !important;
}

.leaflet-popup:hover .mvt-popup-timer {
  display: none;
}
`

/**
 * 根据要素类型和属性获取样式
 * @param {string} geometryType - 几何类型
 * @param {Object} properties - 要素属性
 * @param {boolean} isHover - 是否悬停状态
 * @returns {Object} 样式对象
 */
export function getModernStyle(geometryType, properties = {}, isHover = false) {
  ////console.log('获取样式 - 几何类型:', geometryType, '属性:', properties, '悬停:', isHover)
  
  if (isHover) {
    if (geometryType === 'Point' || geometryType === 'MultiPoint') {
      return { ...ModernMVTStyles.hover.point }
    } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
      return { ...ModernMVTStyles.hover.line }
    } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
      return { ...ModernMVTStyles.hover.polygon }
    }
  }

  // DXF特定的样式分类逻辑
  const style = getDXFSpecificStyle(geometryType, properties)
  if (style) {
    ////console.log('使用DXF特定样式:', style)
    return style
  }

  // 根据几何类型的默认样式
  if (geometryType === 'Point' || geometryType === 'MultiPoint') {
    return { ...ModernMVTStyles.point.default }
  } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
    return { ...ModernMVTStyles.line.default }
  } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
    return { ...ModernMVTStyles.polygon.default }
  }

  // 最终默认样式
  return {
    color: GoogleColors.secondary.grey600,
    fillColor: GoogleColors.secondary.grey400,
    radius: 4,
    weight: 2,
    fill: true,
    fillOpacity: 0.5,
    opacity: 0.8,
    className: 'mvt-default'
  }
}

/**
 * 根据DXF属性获取特定样式
 * @param {string} geometryType - 几何类型
 * @param {Object} properties - 要素属性
 * @returns {Object|null} 样式对象或null
 */
export function getDXFSpecificStyle(geometryType, properties) {
  // 优先使用数据库中的颜色信息
  if (properties.color_rgb && properties.color_rgb !== 'NULL') {
    return createStyleFromColorRGB(geometryType, properties.color_rgb, properties)
  }
  
  if (properties.color_name && properties.color_name !== 'NULL') {
    return createStyleFromColorName(geometryType, properties.color_name, properties)
  }
  
  if (properties.color_index && properties.color_index !== 'NULL') {
    return createStyleFromColorIndex(geometryType, properties.color_index, properties)
  }

  // 根据图层名称分类
  if (properties.layer) {
    return createStyleFromLayer(geometryType, properties.layer, properties)
  }

  // 根据实体类型分类
  if (properties.subclasses) {
    return createStyleFromSubclass(geometryType, properties.subclasses, properties)
  }

  // 根据线型分类
  if (properties.linetype && properties.linetype !== 'ByLayer') {
    return createStyleFromLinetype(geometryType, properties.linetype, properties)
  }

  return null
}

/**
 * 从RGB颜色创建样式
 */
export function createStyleFromColorRGB(geometryType, colorRGB, properties) {
  const color = colorRGB.startsWith('#') ? colorRGB : `#${colorRGB}`
  
  if (geometryType === 'Point' || geometryType === 'MultiPoint') {
    return {
      color: color,
      fillColor: color,
      radius: 3,
      fill: true,
      fillOpacity: 0.8,
      weight: 1,
      opacity: 1,
      className: 'mvt-point-rgb'
    }
  } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
    return {
      color: color,
      weight: 2,
      opacity: 0.9,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-rgb'
    }
  } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
    return {
      fillColor: color,
      color: color,
      weight: 1,
      fill: true,
      fillOpacity: 0.4,
      opacity: 0.8,
      className: 'mvt-polygon-rgb'
    }
  }
}

/**
 * 从颜色名称创建样式
 */
export function createStyleFromColorName(geometryType, colorName, properties) {
  const colorMap = {
    'red': GoogleColors.primary.red,
    'green': GoogleColors.primary.green,
    'blue': GoogleColors.primary.blue,
    'yellow': GoogleColors.primary.yellow,
    'cyan': '#00FFFF',
    'magenta': '#FF00FF',
    'white': '#FFFFFF',
    'black': '#000000'
  }
  
  const color = colorMap[colorName.toLowerCase()] || GoogleColors.secondary.grey600
  return createStyleFromColorRGB(geometryType, color, properties)
}

/**
 * 从颜色索引创建样式
 */
export function createStyleFromColorIndex(geometryType, colorIndex, properties) {
  const indexColorMap = {
    '1': GoogleColors.primary.red,        // 红色
    '2': GoogleColors.primary.yellow,     // 黄色
    '3': GoogleColors.primary.green,      // 绿色
    '4': '#00FFFF',                       // 青色
    '5': GoogleColors.primary.blue,       // 蓝色
    '6': '#FF00FF',                       // 洋红
    '7': '#FFFFFF',                       // 白色
    '8': '#808080',                       // 灰色
    '9': '#C0C0C0'                        // 浅灰
  }
  
  const color = indexColorMap[colorIndex] || GoogleColors.secondary.grey500
  return createStyleFromColorRGB(geometryType, color, properties)
}

/**
 * 从图层名称创建样式
 */
export function createStyleFromLayer(geometryType, layerName, properties) {
  // 为不同图层设置不同颜色
  const layerHash = hashString(layerName)
  const colors = [
    GoogleColors.primary.blue,
    GoogleColors.primary.green,
    GoogleColors.primary.red,
    GoogleColors.primary.yellow,
    '#FF6B35',  // 橙色
    '#9B59B6',  // 紫色
    '#1ABC9C',  // 青绿色
    '#E67E22',  // 橙红色
    '#3498DB',  // 天蓝色
    '#2ECC71'   // 翠绿色
  ]
  
  const color = colors[layerHash % colors.length]
  const opacity = 0.7 + (layerHash % 3) * 0.1  // 0.7-0.9的透明度
  
  if (geometryType === 'Point' || geometryType === 'MultiPoint') {
    return {
      color: color,
      fillColor: color,
      radius: 3 + (layerHash % 3),  // 3-5的半径
      fill: true,
      fillOpacity: opacity,
      weight: 1,
      opacity: 1,
      className: 'mvt-point-layer'
    }
  } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
    return {
      color: color,
      weight: 2 + (layerHash % 2),  // 2-3的线宽
      opacity: opacity,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-layer'
    }
  } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
    return {
      fillColor: color,
      color: darkenColor(color, 20),  // 边框颜色更深
      weight: 1,
      fill: true,
      fillOpacity: opacity * 0.6,  // 填充更透明
      opacity: opacity,
      className: 'mvt-polygon-layer'
    }
  }
}

/**
 * 从子类创建样式
 */
export function createStyleFromSubclass(geometryType, subclasses, properties) {
  // 根据不同的实体子类设置样式
  if (subclasses.includes('AcDbLine')) {
    return {
      color: GoogleColors.secondary.grey600,
      weight: 2,
      opacity: 0.8,
      lineCap: 'round',
      className: 'mvt-line-entity'
    }
  } else if (subclasses.includes('AcDbCircle')) {
    return {
      color: GoogleColors.primary.blue,
      fillColor: GoogleColors.primary.blue,
      radius: 4,
      fill: true,
      fillOpacity: 0.6,
      weight: 2,
      opacity: 1,
      className: 'mvt-circle-entity'
    }
  } else if (subclasses.includes('AcDbPolyline')) {
    return {
      color: GoogleColors.primary.green,
      weight: 2,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-polyline-entity'
    }
  } else if (subclasses.includes('AcDbText')) {
    return {
      color: GoogleColors.primary.red,
      fillColor: GoogleColors.primary.red,
      radius: 2,
      fill: true,
      fillOpacity: 0.9,
      weight: 1,
      opacity: 1,
      className: 'mvt-text-entity'
    }
  }
  
  return null
}

/**
 * 从线型创建样式
 */
export function createStyleFromLinetype(geometryType, linetype, properties) {
  const linetypeStyles = {
    'DASHED': {
      dashArray: '10, 5',
      color: GoogleColors.secondary.grey600
    },
    'DOTTED': {
      dashArray: '2, 3',
      color: GoogleColors.secondary.grey500
    },
    'DASHDOT': {
      dashArray: '10, 5, 2, 5',
      color: GoogleColors.secondary.grey600
    }
  }
  
  const lineStyle = linetypeStyles[linetype.toUpperCase()]
  if (lineStyle && (geometryType === 'LineString' || geometryType === 'MultiLineString')) {
    return {
      ...lineStyle,
      weight: 2,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      className: 'mvt-line-styled'
    }
  }
  
  return null
}

/**
 * 字符串哈希函数
 */
export function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // 转换为32位整数
  }
  return Math.abs(hash)
}

/**
 * 颜色加深函数
 */
export function darkenColor(color, percent) {
  // 简单的颜色加深实现
  const num = parseInt(color.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = (num >> 16) - amt
  const G = (num >> 8 & 0x00FF) - amt
  const B = (num & 0x0000FF) - amt
  return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
    (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
    (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1)
}

/**
 * 注入CSS动画样式到页面
 */
export function injectMVTAnimationCSS() {
  // 检查是否已经注入
  if (document.getElementById('mvt-animation-styles')) {
    return
  }

  const style = document.createElement('style')
  style.id = 'mvt-animation-styles'
  style.textContent = MVTAnimationCSS
  document.head.appendChild(style)
  
  ////console.log('MVT动画样式已注入')
} 