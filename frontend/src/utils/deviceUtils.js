/**
 * 设备检测工具
 * 用于判断设备类型和性能，以便优化地图配置
 */

/**
 * 检测是否为移动设备
 * @returns {boolean} 是否为移动设备
 */
export function isMobileDevice() {
  // 检查用户代理字符串
  const userAgent = navigator.userAgent.toLowerCase()
  const mobileKeywords = [
    'mobile', 'android', 'iphone', 'ipad', 'ipod', 
    'blackberry', 'windows phone', 'webos'
  ]
  
  const isMobileUA = mobileKeywords.some(keyword => userAgent.includes(keyword))
  
  // 检查屏幕尺寸
  const isMobileScreen = window.innerWidth <= 768 || window.innerHeight <= 768
  
  // 检查触摸支持
  const hasTouchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  
  return isMobileUA || (isMobileScreen && hasTouchSupport)
}

/**
 * 检测是否为平板设备
 * @returns {boolean} 是否为平板设备
 */
export function isTabletDevice() {
  const userAgent = navigator.userAgent.toLowerCase()
  const isIpad = userAgent.includes('ipad')
  const isAndroidTablet = userAgent.includes('android') && !userAgent.includes('mobile')
  const isTabletScreen = window.innerWidth >= 768 && window.innerWidth <= 1024
  
  return isIpad || isAndroidTablet || isTabletScreen
}

/**
 * 获取设备类型
 * @returns {'mobile'|'tablet'|'desktop'} 设备类型
 */
export function getDeviceType() {
  if (isMobileDevice()) return 'mobile'
  if (isTabletDevice()) return 'tablet'
  return 'desktop'
}

/**
 * 获取网络连接信息
 * @returns {Object} 网络连接信息
 */
export function getNetworkInfo() {
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection
  
  if (!connection) {
    return {
      effectiveType: 'unknown',
      downlink: null,
      rtt: null,
      saveData: false
    }
  }
  
  return {
    effectiveType: connection.effectiveType,
    downlink: connection.downlink,
    rtt: connection.rtt,
    saveData: connection.saveData || false
  }
}

/**
 * 获取建议的地图预加载级别
 * @returns {number} 预加载级别
 */
export function getRecommendedPreloadLevel() {
  const deviceType = getDeviceType()
  const networkInfo = getNetworkInfo()
  
  // 基础预加载级别
  let preloadLevel = 3 // 桌面端默认
  
  // 根据设备类型调整
  if (deviceType === 'mobile') {
    preloadLevel = 2
  } else if (deviceType === 'tablet') {
    preloadLevel = 2
  }
  
  // 根据网络状况调整
  if (networkInfo.saveData) {
    preloadLevel = Math.max(1, preloadLevel - 1)
  }
  
  if (networkInfo.effectiveType === '2g' || networkInfo.effectiveType === 'slow-2g') {
    preloadLevel = 1
  } else if (networkInfo.effectiveType === '3g') {
    preloadLevel = Math.max(2, preloadLevel)
  }
  
  // 根据硬件性能调整
  if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) {
    preloadLevel = Math.max(1, preloadLevel - 1)
  }
  
  return preloadLevel
}

/**
 * 获取建议的瓦片缓存大小
 * @returns {number} 缓存大小
 */
export function getRecommendedCacheSize() {
  const deviceType = getDeviceType()
  const networkInfo = getNetworkInfo()
  
  let cacheSize = 256 // 桌面端默认
  
  if (deviceType === 'mobile') {
    cacheSize = 128
  } else if (deviceType === 'tablet') {
    cacheSize = 192
  }
  
  // 如果启用了数据节省模式
  if (networkInfo.saveData) {
    cacheSize = Math.floor(cacheSize * 0.5)
  }
  
  return cacheSize
}

/**
 * 获取建议的最大并发请求数
 * @returns {number} 最大并发请求数
 */
export function getRecommendedMaxConcurrentRequests() {
  const deviceType = getDeviceType()
  const networkInfo = getNetworkInfo()
  
  let maxRequests = 6 // 桌面端默认
  
  if (deviceType === 'mobile') {
    maxRequests = 4
  } else if (deviceType === 'tablet') {
    maxRequests = 5
  }
  
  // 根据网络状况调整
  if (networkInfo.effectiveType === '2g' || networkInfo.effectiveType === 'slow-2g') {
    maxRequests = 2
  } else if (networkInfo.effectiveType === '3g') {
    maxRequests = 3
  }
  
  return maxRequests
}

/**
 * 检测设备性能级别
 * @returns {'low'|'medium'|'high'} 性能级别
 */
export function getDevicePerformanceLevel() {
  const cores = navigator.hardwareConcurrency || 4
  const memory = navigator.deviceMemory || 4
  const deviceType = getDeviceType()
  
  if (deviceType === 'mobile' && (cores <= 4 || memory <= 2)) {
    return 'low'
  }
  
  if (cores >= 8 && memory >= 8) {
    return 'high'
  }
  
  return 'medium'
}

export default {
  isMobileDevice,
  isTabletDevice,
  getDeviceType,
  getNetworkInfo,
  getRecommendedPreloadLevel,
  getRecommendedCacheSize,
  getRecommendedMaxConcurrentRequests,
  getDevicePerformanceLevel
} 