/*
 * TIF图层测试工具
 * 用于快速测试和调试TIF图层的加载
 */

import { diagnoseTifLayer, createImprovedWmsLayer } from './tifLayerDiagnostics'

/**
 * 快速测试TIF图层
 * @param {Object} layerInfo - 图层信息
 * @param {L.Map} map - Leaflet地图实例
 * @returns {Promise<Object>} 测试结果
 */
export const quickTestTifLayer = async (layerInfo, map) => {
  const testResult = {
    success: false,
    loadTime: 0,
    error: null,
    layer: null,
    diagnostics: null
  }

  const startTime = performance.now()

  try {
    // 首先进行诊断
    //console.log('🔍 开始诊断TIF图层:', layerInfo.layer_name)
    testResult.diagnostics = await diagnoseTifLayer(layerInfo, map)
    
    if (!testResult.diagnostics.success) {
      testResult.error = testResult.diagnostics.errors.join(', ')
      return testResult
    }

    // 创建测试图层
    //console.log('🧪 创建测试图层:', layerInfo.layer_name)
    const testLayer = createImprovedWmsLayer(layerInfo, {
      opacity: 0.8,
      format: 'image/png'
    })

    // 添加到地图进行测试
    testLayer.addTo(map)
    
    // 等待图层加载
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('图层加载超时'))
      }, 15000) // 15秒超时

      testLayer.on('load', () => {
        clearTimeout(timeout)
        resolve()
      })

      testLayer.on('tileerror', (error) => {
        clearTimeout(timeout)
        reject(new Error('瓦片加载错误: ' + error.message))
      })

      // 触发加载
      map.invalidateSize()
    })

    testResult.success = true
    testResult.layer = testLayer
    testResult.loadTime = performance.now() - startTime

    //console.log('✅ TIF图层测试成功:', layerInfo.layer_name, `(${testResult.loadTime.toFixed(2)}ms)`)

  } catch (error) {
    testResult.error = error.message
    testResult.loadTime = performance.now() - startTime
    console.error('❌ TIF图层测试失败:', layerInfo.layer_name, error)
    
    // 清理测试图层
    if (testResult.layer) {
      map.removeLayer(testResult.layer)
      testResult.layer = null
    }
  }

  return testResult
}

/**
 * 调试TIF图层
 * @param {Object} layerInfo - 图层信息
 * @param {L.Map} map - Leaflet地图实例
 * @returns {Promise<Object>} 调试信息
 */
export const debugTifLayer = async (layerInfo, map) => {
  const debugInfo = {
    timestamp: new Date().toISOString(),
    layerInfo: { ...layerInfo },
    mapState: {
      center: map.getCenter(),
      zoom: map.getZoom(),
      bounds: map.getBounds()
    },
    wmsRequests: [],
    errors: [],
    performance: {}
  }

  try {
    // 性能测试开始
    const perfStart = performance.now()

    // 测试不同的WMS请求
    const testRequests = [
      { format: 'image/png', transparent: true },
      { format: 'image/jpeg', transparent: false },
      { format: 'image/png', version: '1.3.0' },
      { format: 'image/png', version: '1.1.1' }
    ]

    for (const requestParams of testRequests) {
      try {
        const wmsUrl = buildWmsGetMapUrl(layerInfo, map, requestParams)
        const startTime = performance.now()
        
        const response = await fetch(wmsUrl, { 
          method: 'HEAD',
          timeout: 5000 
        })
        
        const responseTime = performance.now() - startTime
        
        debugInfo.wmsRequests.push({
          params: requestParams,
          url: wmsUrl,
          status: response.status,
          responseTime,
          success: response.ok,
          contentType: response.headers.get('content-type')
        })

      } catch (requestError) {
        debugInfo.wmsRequests.push({
          params: requestParams,
          error: requestError.message,
          success: false
        })
      }
    }

    // 测试GetCapabilities
    try {
      const capabilitiesUrl = `${layerInfo.wms_url}?service=WMS&request=GetCapabilities&version=1.1.1`
      const response = await fetch(capabilitiesUrl)
      
      if (response.ok) {
        const capabilitiesText = await response.text()
        debugInfo.capabilities = {
          available: true,
          size: capabilitiesText.length,
          containsLayer: capabilitiesText.toLowerCase().includes(layerInfo.layer_name.toLowerCase())
        }
      }
    } catch (capError) {
      debugInfo.capabilities = {
        available: false,
        error: capError.message
      }
    }

    debugInfo.performance.totalTime = performance.now() - perfStart

  } catch (error) {
    debugInfo.errors.push({
      type: 'debug_error',
      message: error.message,
      stack: error.stack
    })
  }

  console.group('🐛 TIF图层调试信息:')
  //console.log('图层信息:', debugInfo.layerInfo)
  //console.log('地图状态:', debugInfo.mapState)
  //console.log('WMS请求测试:', debugInfo.wmsRequests)
  //console.log('Capabilities:', debugInfo.capabilities)
  //console.log('性能信息:', debugInfo.performance)
  if (debugInfo.errors.length > 0) {
    console.error('错误信息:', debugInfo.errors)
  }
  console.groupEnd()

  return debugInfo
}

/**
 * 构建WMS GetMap请求URL
 * @param {Object} layerInfo - 图层信息
 * @param {L.Map} map - 地图实例
 * @param {Object} params - 请求参数
 * @returns {string} 完整的WMS URL
 */
const buildWmsGetMapUrl = (layerInfo, map, params = {}) => {
  const bounds = map.getBounds()
  const size = map.getSize()
  
  const defaultParams = {
    service: 'WMS',
    request: 'GetMap',
    version: '1.1.1',
    layers: layerInfo.layer_name,
    format: 'image/png',
    transparent: true,
    width: Math.min(size.x, 256),
    height: Math.min(size.y, 256),
    bbox: `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`,
    srs: 'EPSG:4326',
    ...params
  }

  const urlParams = new URLSearchParams(defaultParams)
  return `${layerInfo.wms_url}?${urlParams.toString()}`
}

/**
 * 批量测试多个TIF图层
 * @param {Array} layerInfos - 图层信息数组
 * @param {L.Map} map - 地图实例
 * @returns {Promise<Array>} 测试结果数组
 */
export const batchTestTifLayers = async (layerInfos, map) => {
  const results = []
  
  //console.log('🧪 开始批量测试TIF图层，总数:', layerInfos.length)
  
  for (let i = 0; i < layerInfos.length; i++) {
    const layerInfo = layerInfos[i]
    //console.log(`正在测试 ${i + 1}/${layerInfos.length}: ${layerInfo.layer_name}`)
    
    try {
      const result = await quickTestTifLayer(layerInfo, map)
      results.push({
        index: i,
        layerInfo,
        ...result
      })
      
      // 清理测试图层
      if (result.layer) {
        map.removeLayer(result.layer)
      }
      
    } catch (error) {
      results.push({
        index: i,
        layerInfo,
        success: false,
        error: error.message
      })
    }
    
    // 短暂延迟，避免并发请求过多
    if (i < layerInfos.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }
  
  // 生成统计报告
  const successCount = results.filter(r => r.success).length
  const failureCount = results.length - successCount
  
  //console.log('📊 批量测试完成:')
  //console.log(`  ✅ 成功: ${successCount}`)
  //console.log(`  ❌ 失败: ${failureCount}`)
  //console.log(`  🎯 成功率: ${((successCount / results.length) * 100).toFixed(1)}%`)
  
  return results
}

/**
 * 测试不同缩放级别下的图层性能
 * @param {Object} layerInfo - 图层信息
 * @param {L.Map} map - 地图实例
 * @param {Array} zoomLevels - 要测试的缩放级别
 * @returns {Promise<Object>} 性能测试结果
 */
export const testLayerPerformanceAtZooms = async (layerInfo, map, zoomLevels = [5, 10, 15, 18]) => {
  const results = {
    layerName: layerInfo.layer_name,
    tests: [],
    summary: {}
  }

  const originalZoom = map.getZoom()
  const originalCenter = map.getCenter()

  try {
    for (const zoom of zoomLevels) {
      //console.log(`测试缩放级别 ${zoom}`)
      
      // 设置缩放级别
      map.setView(originalCenter, zoom)
      
      // 等待地图稳定
      await new Promise(resolve => setTimeout(resolve, 200))
      
      const testResult = await quickTestTifLayer(layerInfo, map)
      
      results.tests.push({
        zoom,
        success: testResult.success,
        loadTime: testResult.loadTime,
        error: testResult.error
      })

      // 清理测试图层
      if (testResult.layer) {
        map.removeLayer(testResult.layer)
      }
    }

    // 计算性能摘要
    const successfulTests = results.tests.filter(t => t.success)
    if (successfulTests.length > 0) {
      const loadTimes = successfulTests.map(t => t.loadTime)
      results.summary = {
        successRate: (successfulTests.length / results.tests.length) * 100,
        avgLoadTime: loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length,
        minLoadTime: Math.min(...loadTimes),
        maxLoadTime: Math.max(...loadTimes)
      }
    }

  } finally {
    // 恢复原始视图
    map.setView(originalCenter, originalZoom)
  }

  return results
} 