/**
 * URL处理工具
 * 用于处理服务URL的地址替换和标准化
 */

import { MARTIN_BASE_URL } from '@/config/index.js'

/**
 * 获取配置中的主机地址（不带端口号）
 * @returns {string} 主机地址，格式为 protocol://hostname
 */
export function getConfiguredHost() {
  try {
    const martinUrlObj = new URL(MARTIN_BASE_URL)
    return `${martinUrlObj.protocol}//${martinUrlObj.hostname}`
  } catch (error) {
    console.error('解析MARTIN_BASE_URL失败:', error)
    return 'http://172.16.118.124' // 回退到默认值
  }
}

/**
 * 处理服务URL，将localhost地址替换为配置的地址
 * @param {string} url 原始URL
 * @returns {string} 处理后的URL
 */
export function processServiceUrl(url) {
  if (!url) return url
  
  let processedUrl = url
  const hostWithoutPort = getConfiguredHost()
  
  // 替换各种localhost形式
  const localhostPatterns = [
    'http://localhost:3000',
    'http://localhost:8083',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8083'
  ]
  
  localhostPatterns.forEach(pattern => {
    if (processedUrl.includes(pattern)) {
      processedUrl = processedUrl.replace(pattern, hostWithoutPort)
    }
  })
  
  return processedUrl
}

/**
 * 批量处理多个URL
 * @param {string[]} urls URL数组
 * @returns {string[]} 处理后的URL数组
 */
export function processMultipleUrls(urls) {
  return urls.map(url => processServiceUrl(url))
}

/**
 * 检查URL是否需要处理
 * @param {string} url 要检查的URL
 * @returns {boolean} 是否包含需要替换的localhost地址
 */
export function needsUrlProcessing(url) {
  if (!url) return false
  
  const localhostPatterns = [
    'localhost:3000',
    'localhost:8083',
    '127.0.0.1:3000',
    '127.0.0.1:8083'
  ]
  
  return localhostPatterns.some(pattern => url.includes(pattern))
}

/**
 * 验证URL格式是否正确
 * @param {string} url 要验证的URL
 * @returns {boolean} URL是否有效
 */
export function isValidUrl(url) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export default {
  getConfiguredHost,
  processServiceUrl,
  processMultipleUrls,
  needsUrlProcessing,
  isValidUrl
} 