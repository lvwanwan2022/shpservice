/**
 * 坐标工具函数
 * 提供安全的坐标检查和处理功能
 */

/**
 * 检查坐标对象是否有效
 * @param {Object} latlng - 坐标对象，应包含lat和lng属性
 * @returns {boolean} 是否为有效坐标
 */
export function isValidLatLng(latlng) {
  if (!latlng || typeof latlng !== 'object') {
    return false
  }
  
  const { lat, lng } = latlng
  
  // 检查是否为数字
  if (typeof lat !== 'number' || typeof lng !== 'number') {
    return false
  }
  
  // 检查是否为有限数
  if (!isFinite(lat) || !isFinite(lng)) {
    return false
  }
  
  // 检查坐标范围
  if (Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    return false
  }
  
  return true
}

/**
 * 安全获取坐标字符串
 * @param {Object} latlng - 坐标对象
 * @param {number} precision - 精度（小数位数），默认6位
 * @returns {string|null} 坐标字符串或null
 */
export function safeGetCoordinateString(latlng, precision = 6) {
  if (!isValidLatLng(latlng)) {
    return null
  }
  
  try {
    const lat = latlng.lat.toFixed(precision)
    const lng = latlng.lng.toFixed(precision)
    return `${lat}, ${lng}`
  } catch (error) {
    console.warn('坐标字符串转换错误:', error)
    return null
  }
}

/**
 * 安全处理地图事件
 * @param {Function} handler - 事件处理函数
 * @returns {Function} 包装后的安全事件处理函数
 */
export function safeEventHandler(handler) {
  return function(e) {
    try {
      // 检查事件对象
      if (!e || typeof e !== 'object') {
        console.warn('无效的事件对象:', e)
        return
      }
      
      // 如果事件包含坐标信息，进行检查
      if (e.latlng) {
        if (!isValidLatLng(e.latlng)) {
          console.warn('事件包含无效坐标:', e.latlng)
          return
        }
      }
      
      // 调用原始处理函数
      return handler.call(this, e)
    } catch (error) {
      console.error('事件处理错误:', error)
    }
  }
}

/**
 * 创建安全的坐标显示更新函数
 * @param {Function} updateFunction - 坐标更新函数
 * @returns {Function} 安全的坐标更新函数
 */
export function createSafeCoordinateUpdater(updateFunction) {
  return safeEventHandler((e) => {
    const coordString = safeGetCoordinateString(e.latlng)
    if (coordString) {
      updateFunction(coordString)
    }
  })
}

/**
 * 验证并规范化坐标对象
 * @param {Object} latlng - 原始坐标对象
 * @returns {Object|null} 规范化的坐标对象或null
 */
export function normalizeLatLng(latlng) {
  if (!isValidLatLng(latlng)) {
    return null
  }
  
  return {
    lat: Number(latlng.lat),
    lng: Number(latlng.lng)
  }
}

/**
 * 创建安全的弹窗显示函数
 * @param {Object} L - Leaflet对象
 * @param {Object} map - 地图实例
 * @returns {Function} 安全的弹窗显示函数
 */
export function createSafePopupHandler(L, map) {
  return function(latlng, content) {
    try {
      const validLatLng = normalizeLatLng(latlng)
      if (!validLatLng) {
        console.warn('无法显示弹窗，坐标无效:', latlng)
        return
      }
      
      L.popup()
        .setLatLng(validLatLng)
        .setContent(content)
        .openOn(map)
    } catch (error) {
      console.error('弹窗显示错误:', error)
    }
  }
}

export default {
  isValidLatLng,
  safeGetCoordinateString,
  safeEventHandler,
  createSafeCoordinateUpdater,
  normalizeLatLng,
  createSafePopupHandler
} 