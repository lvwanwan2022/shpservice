/**
 * 智能缓存插件 - 前端入口
 * 提供完整的AI驱动缓存解决方案
 */

import CacheManager from './services/CacheManager.js'
import BehaviorTracker from './services/BehaviorTracker.js'
import PredictionEngine from './services/PredictionEngine.js'
import SpatialIndex from './services/SpatialIndex.js'
import CacheStatsPanel from './components/CacheStatsPanel.vue'
import CacheControlPanel from './components/CacheControlPanel.vue'
import cacheConfig from '../config/cache-config.js'

class IntelligentCachePlugin {
  constructor(options = {}) {
    this.name = 'IntelligentCache'
    this.version = '1.0.0'
    this.enabled = options.enabled !== false
    this.config = { ...cacheConfig, ...options.config }
    
    // 核心服务实例
    this.services = {
      cacheManager: null,
      behaviorTracker: null,
      predictionEngine: null,
      spatialIndex: null
    }
    
    // 插件状态
    this.isInitialized = false
    this.isActive = false
    
    // 性能统计
    this.stats = {
      startTime: Date.now(),
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      predictions: 0,
      preloads: 0
    }
  }

  /**
   * 插件安装方法 - Vue插件标准接口
   */
  install(app, options = {}) {
    if (!this.enabled) {
      console.log('🚫 智能缓存插件已禁用')
      return
    }

    // 合并配置
    this.config = { ...this.config, ...options }
    
    // 初始化核心服务
    this.initializeServices()
    
    // 注册全局组件
    app.component('CacheStatsPanel', CacheStatsPanel)
    app.component('CacheControlPanel', CacheControlPanel)
    
    // 注册全局属性
    app.config.globalProperties.$intelligentCache = this
    
    // 提供依赖注入
    app.provide('intelligentCache', this)
    
    console.log('✅ 智能缓存插件安装成功')
  }

  /**
   * 初始化核心服务
   */
  async initializeServices() {
    try {
      // 1. 初始化空间索引
      this.services.spatialIndex = new SpatialIndex(this.config.spatial)
      await this.services.spatialIndex.init()
      
      // 2. 初始化行为追踪器
      this.services.behaviorTracker = new BehaviorTracker(this.config.behavior)
      await this.services.behaviorTracker.init()
      
      // 3. 初始化预测引擎
      this.services.predictionEngine = new PredictionEngine(this.config.prediction)
      await this.services.predictionEngine.init()
      
      // 4. 初始化缓存管理器
      this.services.cacheManager = new CacheManager({
        ...this.config.cache,
        spatialIndex: this.services.spatialIndex,
        behaviorTracker: this.services.behaviorTracker,
        predictionEngine: this.services.predictionEngine
      })
      await this.services.cacheManager.init()
      
      this.isInitialized = true
      this.isActive = true
      
      console.log('✅ 智能缓存服务初始化完成')
      
    } catch (error) {
      console.error('❌ 智能缓存服务初始化失败:', error)
      this.isActive = false
    }
  }

  /**
   * 核心API：智能瓦片获取
   */
  async getTile(layer, z, x, y, options = {}) {
    if (!this.isActive) {
      // 插件未激活时，直接返回传统获取方式
      return this.fallbackGetTile(layer, z, x, y, options)
    }

    try {
      this.stats.totalRequests++
      
      // 使用智能缓存管理器获取瓦片
      const result = await this.services.cacheManager.getTile(layer, z, x, y, options)
      
      // 更新统计
      if (result.fromCache) {
        this.stats.cacheHits++
      } else {
        this.stats.cacheMisses++
      }
      
      return result.data
      
    } catch (error) {
      console.warn('智能缓存获取失败，使用传统方式:', error)
      return this.fallbackGetTile(layer, z, x, y, options)
    }
  }

  /**
   * 传统瓦片获取方式（备用）
   */
  async fallbackGetTile(layer, z, x, y, options = {}) {
    const url = this.buildTileUrl(layer, z, x, y)
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`瓦片获取失败: ${response.status}`)
    }
    
    return await response.arrayBuffer()
  }

  /**
   * 预测性预加载
   */
  async triggerPredictiveLoading(layer, z, x, y) {
    if (!this.isActive || !this.services.cacheManager) {
      return
    }

    try {
      const predictions = await this.services.predictionEngine.predict({
        current: { layer, z, x, y },
        context: await this.getCurrentContext()
      })
      
      this.stats.predictions += predictions.length
      
      // 异步预加载高概率瓦片
      const preloadPromises = predictions
        .filter(p => p.probability > this.config.prediction.threshold)
        .slice(0, this.config.prediction.maxPreloads)
        .map(p => this.preloadTile(p.layer, p.z, p.x, p.y, p.probability))
      
      await Promise.allSettled(preloadPromises)
      
    } catch (error) {
      console.warn('预测性加载失败:', error)
    }
  }

  /**
   * 预加载单个瓦片
   */
  async preloadTile(layer, z, x, y, probability) {
    try {
      await this.services.cacheManager.preloadTile(layer, z, x, y, probability)
      this.stats.preloads++
    } catch (error) {
      console.debug(`预加载失败 ${layer}/${z}/${x}/${y}:`, error.message)
    }
  }

  /**
   * 记录用户行为
   */
  recordBehavior(action, data) {
    if (!this.isActive || !this.services.behaviorTracker) {
      return
    }

    this.services.behaviorTracker.record(action, data)
  }

  /**
   * 获取缓存统计信息
   */
  async getStats() {
    const baseStats = { ...this.stats }
    
    if (this.isActive && this.services.cacheManager) {
      const cacheStats = await this.services.cacheManager.getStats()
      return {
        ...baseStats,
        ...cacheStats,
        hitRate: this.stats.totalRequests > 0 ? 
          Math.round((this.stats.cacheHits / this.stats.totalRequests) * 100) / 100 : 0,
        uptime: Date.now() - this.stats.startTime,
        isActive: this.isActive
      }
    }
    
    return baseStats
  }

  /**
   * 清理缓存
   */
  async clearCache() {
    if (this.isActive && this.services.cacheManager) {
      await this.services.cacheManager.clearCache()
      this.resetStats()
    }
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      startTime: Date.now(),
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      predictions: 0,
      preloads: 0
    }
  }

  /**
   * 启用插件
   */
  async enable() {
    if (!this.isInitialized) {
      await this.initializeServices()
    }
    this.isActive = true
    console.log('✅ 智能缓存插件已启用')
  }

  /**
   * 禁用插件
   */
  disable() {
    this.isActive = false
    console.log('🚫 智能缓存插件已禁用')
  }

  /**
   * 卸载插件
   */
  async uninstall() {
    try {
      // 清理缓存数据
      if (this.services.cacheManager) {
        await this.services.cacheManager.destroy()
      }
      
      // 停止行为追踪
      if (this.services.behaviorTracker) {
        await this.services.behaviorTracker.destroy()
      }
      
      // 清理预测引擎
      if (this.services.predictionEngine) {
        await this.services.predictionEngine.destroy()
      }
      
      // 清理空间索引
      if (this.services.spatialIndex) {
        await this.services.spatialIndex.destroy()
      }
      
      this.isInitialized = false
      this.isActive = false
      
      console.log('✅ 智能缓存插件卸载完成')
      
    } catch (error) {
      console.error('❌ 插件卸载失败:', error)
    }
  }

  // ============ 辅助方法 ============

  buildTileUrl(layer, z, x, y) {
    // 根据配置构建瓦片URL
    const baseUrl = this.config.tileService.baseUrl || '/api/tiles'
    return `${baseUrl}/${layer}/${z}/${x}/${y}`
  }

  async getCurrentContext() {
    return {
      timestamp: Date.now(),
      hour: new Date().getHours(),
      dayOfWeek: new Date().getDay(),
      stats: await this.getStats()
    }
  }

  // ============ 静态方法 ============

  /**
   * 检查浏览器兼容性
   */
  static checkCompatibility() {
    const requirements = {
      indexedDB: 'indexedDB' in window,
      webWorkers: 'Worker' in window,
      arrayBuffer: 'ArrayBuffer' in window,
      fetch: 'fetch' in window
    }
    
    const compatible = Object.values(requirements).every(Boolean)
    
    return {
      compatible,
      requirements,
      missing: Object.keys(requirements).filter(key => !requirements[key])
    }
  }

  /**
   * 获取插件信息
   */
  static getInfo() {
    return {
      name: 'IntelligentCache',
      version: '1.0.0',
      description: 'AI-powered intelligent caching system for WebGIS',
      author: 'Your Name',
      features: [
        'AI behavior prediction',
        'Intelligent cache management',
        'Spatial indexing',
        'Performance monitoring',
        'Predictive preloading'
      ]
    }
  }
}

// ============ 导出 ============

// Vue插件格式导出
export default IntelligentCachePlugin

// 命名导出核心服务
export {
  CacheManager,
  BehaviorTracker,
  PredictionEngine,
  SpatialIndex,
  CacheStatsPanel,
  CacheControlPanel
}

// 全局安装方法（用于CDN引入）
if (typeof window !== 'undefined' && window.Vue) {
  window.IntelligentCachePlugin = IntelligentCachePlugin
} 