/**
 * 地图诊断工具
 */

import L from 'leaflet'
import axios from 'axios'

export class MapDiagnostics {
  constructor() {
    this.results = []
  }

  // 添加诊断结果
  addResult(test, status, message, details = null) {
    this.results.push({
      test,
      status, // 'success', 'warning', 'error'
      message,
      details,
      timestamp: new Date().toISOString()
    })
  }

  // 检查Leaflet库
  checkLeafletLibrary() {
    try {
      if (typeof L === 'undefined') {
        this.addResult('Leaflet库检查', 'error', 'Leaflet库未加载')
        return false
      }

      this.addResult('Leaflet库检查', 'success', `Leaflet版本: ${L.version}`)
      
      // 检查关键组件
      const components = ['Map', 'TileLayer', 'Marker', 'Icon']
      for (const component of components) {
        if (L[component]) {
          this.addResult(`Leaflet.${component}`, 'success', '组件可用')
        } else {
          this.addResult(`Leaflet.${component}`, 'error', '组件不可用')
        }
      }

      return true
    } catch (error) {
      this.addResult('Leaflet库检查', 'error', '检查Leaflet库时出错', error.message)
      return false
    }
  }

  // 检查CSS加载
  checkLeafletCSS() {
    try {
      // 检查是否有leaflet相关的CSS规则
      const stylesheets = Array.from(document.styleSheets)
      let leafletCSSFound = false

      for (const stylesheet of stylesheets) {
        try {
          if (stylesheet.href && stylesheet.href.includes('leaflet')) {
            leafletCSSFound = true
            this.addResult('Leaflet CSS', 'success', `CSS文件已加载: ${stylesheet.href}`)
            break
          }
        } catch (e) {
          // 跨域CSS无法访问，忽略
        }
      }

      if (!leafletCSSFound) {
        this.addResult('Leaflet CSS', 'warning', '未检测到Leaflet CSS文件')
      }

      // 检查关键CSS类
      const testElement = document.createElement('div')
      testElement.className = 'leaflet-container'
      document.body.appendChild(testElement)
      
      const computedStyle = window.getComputedStyle(testElement)
      if (computedStyle.position === 'relative') {
        this.addResult('Leaflet CSS类', 'success', 'leaflet-container样式正确')
      } else {
        this.addResult('Leaflet CSS类', 'error', 'leaflet-container样式不正确')
      }
      
      document.body.removeChild(testElement)
      return true
    } catch (error) {
      this.addResult('Leaflet CSS检查', 'error', '检查CSS时出错', error.message)
      return false
    }
  }

  // 检查网络连接
  async checkNetworkConnectivity() {
    // 测试多个可靠的地图服务连通性
    const testUrls = [
      'https://webrd01.is.autonavi.com/appmaptile?x=0&y=0&z=0&lang=zh_cn&size=1&scale=1&style=7',
      'https://webst01.is.autonavi.com/appmaptile?style=6&x=0&y=0&z=0'
    ]

    for (const url of testUrls) {
      try {
        const response = await fetch(url, { 
          method: 'HEAD',
          mode: 'no-cors',
          cache: 'no-cache'
        })
        this.addResult('网络连接', 'success', `可以访问: ${url}`)
      } catch (error) {
        this.addResult('网络连接', 'warning', `无法访问: ${url}`, error.message)
      }
    }
  }

  // 检查后端API连接
  async checkBackendAPI() {
    try {
      const response = await axios.get('/api/scenes', { timeout: 5000 })
      this.addResult('后端API', 'success', '后端API连接正常')
      return true
    } catch (error) {
      // 如果404，尝试检查健康端点
      try {
        const healthResponse = await axios.get('/api/health', { timeout: 5000 })
        this.addResult('后端API', 'success', '后端服务运行正常')
        this.addResult('场景API', 'warning', '场景接口可能未配置', error.message)
        return true
      } catch (healthError) {
        this.addResult('后端API', 'error', '后端API连接失败', error.message)
        return false
      }
    }
  }

  // 检查GeoServer连接
  async checkGeoServerConnection() {
    try {
      // 通过代理访问GeoServer（使用相对路径，避免CORS问题）
      const response = await axios.get('/geoserver/web/', { timeout: 5000 })
      this.addResult('GeoServer连接', 'success', 'GeoServer连接正常')
      return true
    } catch (error) {
      this.addResult('GeoServer连接', 'error', 'GeoServer连接失败', error.message)
      
      // 尝试测试WMS服务
      try {
        const wmsResponse = await axios.get('/geoserver/wms?service=WMS&version=1.1.1&request=GetCapabilities', { timeout: 5000 })
        this.addResult('GeoServer WMS', 'success', 'GeoServer WMS服务可访问')
        return true
      } catch (wmsError) {
        this.addResult('GeoServer WMS', 'error', 'GeoServer WMS服务不可访问', wmsError.message)
        return false
      }
    }
  }

  // 测试地图容器
  testMapContainer(containerElement) {
    if (!containerElement) {
      this.addResult('地图容器', 'error', '容器元素不存在')
      return false
    }

    // 检查是否是DOM元素
    if (!(containerElement instanceof HTMLElement)) {
      this.addResult('地图容器', 'error', '提供的容器不是有效的DOM元素', `类型: ${typeof containerElement}`)
      return false
    }

    // 检查元素是否在DOM树中
    if (!containerElement.isConnected) {
      this.addResult('地图容器', 'error', '容器元素未添加到DOM树中')
      return false
    }

    try {
      const rect = containerElement.getBoundingClientRect()
      
      if (rect.width === 0 || rect.height === 0) {
        this.addResult('地图容器', 'error', `容器尺寸无效: ${rect.width}x${rect.height}`)
        return false
      }

      this.addResult('地图容器', 'success', `容器尺寸: ${rect.width}x${rect.height}`)

      // 检查容器样式
      const computedStyle = window.getComputedStyle(containerElement)
      const position = computedStyle.position
      const display = computedStyle.display

      if (display === 'none') {
        this.addResult('容器样式', 'error', '容器被隐藏 (display: none)')
        return false
      }

      this.addResult('容器样式', 'success', `position: ${position}, display: ${display}`)
      return true
    } catch (error) {
      this.addResult('地图容器', 'error', 'getBoundingClientRect调用失败', error.message)
      return false
    }
  }

  // 测试基础地图创建
  testBasicMapCreation(containerElement) {
    if (!this.testMapContainer(containerElement)) {
      return false
    }

    try {
      const testMap = L.map(containerElement, {
        center: [0, 0],
        zoom: 1
      })

      this.addResult('地图创建', 'success', '地图实例创建成功')

      // 测试地图基础功能（无需底图）
      testMap.setZoom(2)
      testMap.setView([39.9042, 116.4074], 10)
      
      this.addResult('地图操作', 'success', '地图缩放和视图设置成功')

      // 清理测试地图
      setTimeout(() => {
        testMap.remove()
      }, 1000)

      return true
    } catch (error) {
      this.addResult('地图创建', 'error', '地图创建失败', error.message)
      return false
    }
  }

  // 测试基础地图功能
  async testBasicMapFunctions() {
    const L = await import('leaflet')
    
    const results = []
    
    // 测试地图创建
    try {
      const testDiv = document.createElement('div')
      testDiv.style.width = '100px'
      testDiv.style.height = '100px'
      document.body.appendChild(testDiv)
      
      const testMap = L.map(testDiv, { center: [0, 0], zoom: 1 })
      
      // 不添加底图，只测试地图实例
      results.push({
        test: '地图实例创建',
        status: 'success',
        message: '地图实例创建成功'
      })
      
      testMap.remove()
      document.body.removeChild(testDiv)
      
    } catch (error) {
      results.push({
        test: '地图实例创建',
        status: 'error',
        message: error.message
      })
    }
    
    return results
  }

  // 运行完整诊断
  async runFullDiagnostics(containerElement = null) {
    this.results = []
    
    //console.log('开始运行地图诊断...')

    // 1. 检查Leaflet库
    this.checkLeafletLibrary()

    // 2. 检查CSS
    this.checkLeafletCSS()

    // 3. 检查网络连接
    await this.checkNetworkConnectivity()

    // 4. 检查后端API
    await this.checkBackendAPI()

    // 5. 检查GeoServer
    await this.checkGeoServerConnection()

    // 6. 如果提供了容器，测试地图创建
    if (containerElement) {
      this.testBasicMapCreation(containerElement)
    }

    //console.log('诊断完成，结果:', this.results)
    return this.results
  }

  // 获取诊断报告
  getReport() {
    const report = {
      summary: {
        total: this.results.length,
        success: this.results.filter(r => r.status === 'success').length,
        warning: this.results.filter(r => r.status === 'warning').length,
        error: this.results.filter(r => r.status === 'error').length
      },
      details: this.results
    }

    return report
  }

  // 打印报告到控制台
  printReport() {
    const report = this.getReport()
    
    console.group('🔍 地图诊断报告')
    //console.log(`总计: ${report.summary.total} 项检查`)
    //console.log(`✅ 成功: ${report.summary.success}`)
    //console.log(`⚠️ 警告: ${report.summary.warning}`)
    //console.log(`❌ 错误: ${report.summary.error}`)
    
    console.group('详细结果:')
    for (const result of report.details) {
      const icon = result.status === 'success' ? '✅' : 
                   result.status === 'warning' ? '⚠️' : '❌'
      //console.log(`${icon} ${result.test}: ${result.message}`)
      if (result.details) {
        //console.log(`   详情: ${result.details}`)
      }
    }
    console.groupEnd()
    console.groupEnd()

    return report
  }
}

// 创建全局诊断实例
export const mapDiagnostics = new MapDiagnostics()

// 便捷函数
export async function runMapDiagnostics(containerElement = null) {
  const diagnostics = new MapDiagnostics()
  await diagnostics.runFullDiagnostics(containerElement)
  return diagnostics.printReport()
} 