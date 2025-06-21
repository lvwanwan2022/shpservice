import defaultDxfStyles from '@/config/defaultDxfStyles.json'
import gisApi from '@/api/gis'

/**
 * DXF样式管理器
 */
export class DxfStyleManager {
  constructor() {
    this.defaultStyles = defaultDxfStyles.defaultDxfStyles
    this.layerGroups = defaultDxfStyles.layerGroups
  }

  /**
   * 获取默认DXF样式
   * @returns {object} 默认样式配置
   */
  getDefaultStyles() {
    return this.defaultStyles
  }

  /**
   * 获取图层分组信息
   * @returns {object} 图层分组配置
   */
  getLayerGroups() {
    return this.layerGroups
  }

  /**
   * 从Martin服务获取图层列表
   * @param {string} tableName - 表名
   * @returns {Promise<Array>} 图层名称列表
   */
  async getLayersFromMartinService(tableName) {
    try {
      const response = await gisApi.getMartinServiceLayers(tableName)
      console.log('Martin API 原始响应:', response)
      
      // 处理不同的响应格式
      if (response?.success && response.data?.layers) {
        // 新格式：已处理的图层列表
        return response.data.layers
      } else if (response?.vector_layers) {
        // TileJSON 格式：直接从 vector_layers 提取
        console.log('从 TileJSON vector_layers 提取图层:', response.vector_layers)
        return response.vector_layers.map(layer => layer.id)
      } else if (response?.data?.vector_layers) {
        // TileJSON 格式：从 data.vector_layers 提取
        console.log('从 data.vector_layers 提取图层:', response.data.vector_layers)
        return response.data.vector_layers.map(layer => layer.id)
      } else {
        // 如果没有 vector_layers，使用表名作为默认图层
        console.warn('未找到 vector_layers，使用表名作为默认图层:', tableName)
        return [tableName]
      }
    } catch (error) {
      console.error('获取Martin服务图层失败:', error)
      console.error('错误详情:', error.response?.data || error.message)
      // 返回表名作为默认图层
      return [tableName]
    }
  }

  /**
   * 获取Martin服务的样式配置
   * @param {number} martinServiceId - Martin服务ID
   * @returns {Promise<object>} 样式配置
   */
  async getMartinServiceStyle(martinServiceId) {
    try {
      //console.log('=== getMartinServiceStyle 调用 ===')
      //console.log('传入的 martinServiceId:', martinServiceId)
      //console.log('martinServiceId 类型:', typeof martinServiceId)
      //console.log('martinServiceId 值:', JSON.stringify(martinServiceId))
      
      const response = await gisApi.getMartinServiceStyle(martinServiceId)
      //console.log('API响应:', response)
      
      if (response?.success && response.data?.style_config) {
        //console.log('找到 style_config:', response.data.style_config)
        // 返回style_config字段（从后端API）
        return response.data.style_config
      }
      
      // 向后兼容：如果没有style_config，尝试style字段
      if (response?.success && response.data?.style) {
        console.log('找到 style 字段:', response.data.style)
        if (typeof response.data.style === 'string') {
          return JSON.parse(response.data.style)
        }
        return response.data.style
      }
      
      console.log('未找到样式配置，返回null')
      return null
    } catch (error) {
      console.error('获取Martin服务样式失败:', error)
      console.error('错误详情:', error.message)
      console.error('错误响应:', error.response?.data)
      return null
    }
  }

  /**
   * 保存Martin服务的样式配置
   * @param {number|string} martinServiceId - Martin服务ID
   * @param {object} styleConfig - 样式配置
   * @returns {Promise<boolean>} 是否保存成功
   */
  async saveMartinServiceStyle(martinServiceId, styleConfig) {
    try {
      console.log('=== saveMartinServiceStyle 调用 ===')
      console.log('传入的 martinServiceId:', martinServiceId)
      console.log('martinServiceId 类型:', typeof martinServiceId)
      console.log('传入的 styleConfig:', styleConfig)
      
      const response = await gisApi.updateMartinServiceStyle(martinServiceId, styleConfig)
      console.log('保存样式 API响应:', response)
      
      if (response?.success) {
        console.log('样式保存成功')
        return true
      } else {
        console.error('样式保存失败:', response?.error || '未知错误')
        return false
      }
    } catch (error) {
      console.error('保存Martin服务样式失败:', error)
      console.error('错误详情:', error.message)
      console.error('错误响应:', error.response?.data)
      return false
    }
  }

  /**
   * 创建新图层样式
   * @param {string} layerName - 图层名称
   * @param {object} baseStyle - 基础样式（可选）
   * @returns {object} 新图层样式
   */
  createNewLayerStyle(layerName, baseStyle = null) {
    if (baseStyle) {
      return {
        ...baseStyle,
        name: layerName,
        description: `自定义图层：${layerName}`
      }
    }

    // 使用默认样式模板
    return {
      weight: 1.5,
      color: '#666666',
      opacity: 0.8,
      fillColor: '#CCCCCC',
      fill: false,
      fillOpacity: 0.3,
      radius: 4,
      name: layerName,
      description: `自定义图层：${layerName}`,
      visible: true,
      zIndex: 1
    }
  }

  /**
   * 合并默认样式和自定义样式
   * @param {Array} availableLayers - 可用图层列表
   * @param {object} customStyles - 自定义样式配置
   * @returns {object} 合并后的样式配置
   */
  mergeStyles(availableLayers, customStyles = {}) {
    const mergedStyles = {}

    // 首先添加所有可用图层
    availableLayers.forEach(layerName => {
      if (customStyles[layerName]) {
        // 使用自定义样式
        mergedStyles[layerName] = { ...customStyles[layerName] }
      } else if (this.defaultStyles[layerName]) {
        // 使用默认样式
        mergedStyles[layerName] = { ...this.defaultStyles[layerName] }
      } else {
        // 创建新样式
        mergedStyles[layerName] = this.createNewLayerStyle(layerName)
      }
    })

    // 添加自定义样式中存在但图层列表中不存在的图层
    Object.keys(customStyles).forEach(layerName => {
      if (!mergedStyles[layerName]) {
        mergedStyles[layerName] = { ...customStyles[layerName] }
      }
    })

    return mergedStyles
  }

  /**
   * 验证样式配置
   * @param {object} styleConfig - 样式配置
   * @returns {object} 验证结果 { valid: boolean, errors: Array }
   */
  validateStyleConfig(styleConfig) {
    const errors = []

    Object.keys(styleConfig).forEach(layerName => {
      const style = styleConfig[layerName]

      // 检查必需字段
      if (!style.color) {
        errors.push(`图层 ${layerName}: 缺少颜色配置`)
      }

      if (typeof style.weight !== 'number' || style.weight < 0) {
        errors.push(`图层 ${layerName}: 线宽配置无效`)
      }

      if (typeof style.opacity !== 'number' || style.opacity < 0 || style.opacity > 1) {
        errors.push(`图层 ${layerName}: 透明度配置无效`)
      }

      // 检查填充样式
      if (style.fill && !style.fillColor) {
        errors.push(`图层 ${layerName}: 启用填充但未设置填充颜色`)
      }

      if (style.fill && (typeof style.fillOpacity !== 'number' || style.fillOpacity < 0 || style.fillOpacity > 1)) {
        errors.push(`图层 ${layerName}: 填充透明度配置无效`)
      }
    })

    return {
      valid: errors.length === 0,
      errors
    }
  }

  /**
   * 将样式配置转换为Leaflet VectorGrid格式
   * @param {object} styleConfig - DXF样式配置
   * @param {string} tableName - 表名
   * @param {string} layerField - 图层字段名
   * @returns {object} VectorGrid样式配置
   */
  convertToVectorGridStyle(styleConfig, tableName, layerField = 'layer') {
    return {
      [tableName]: function(properties, zoom) {
        const layerName = properties[layerField]
        const style = styleConfig[layerName]

        if (!style) {
          return {
            weight: 1,
            color: '#666666',
            opacity: 0.3,
            fillColor: '#CCCCCC',
            fill: false,
            fillOpacity: 0.1
          }
        }

        // 根据缩放级别动态调整样式
        const adjustedStyle = { ...style }

        if (zoom < 10) {
          adjustedStyle.weight = Math.max((adjustedStyle.weight || 1) - 0.5, 0.5)
          adjustedStyle.opacity = Math.max((adjustedStyle.opacity || 0.7) - 0.2, 0.3)
        } else if (zoom > 15) {
          adjustedStyle.weight = (adjustedStyle.weight || 1) + 0.5
          adjustedStyle.opacity = Math.min((adjustedStyle.opacity || 0.7) + 0.1, 1)
        }

        // 特殊图层处理
        if (layerName === 'sqx' && zoom < 14) {
          adjustedStyle.opacity = 0
        }

        if (layerName === 'jqx' && zoom < 12) {
          adjustedStyle.opacity = Math.max((adjustedStyle.opacity || 0.6) - 0.3, 0.2)
        }

        // 可见性控制
        if (style.visible === false) {
          adjustedStyle.opacity = 0
          adjustedStyle.fillOpacity = 0
        }

        return adjustedStyle
      }
    }
  }

  /**
   * 导出样式配置为JSON
   * @param {object} styleConfig - 样式配置
   * @returns {string} JSON字符串
   */
  exportStyleConfig(styleConfig) {
    return JSON.stringify(styleConfig, null, 2)
  }

  /**
   * 从JSON导入样式配置
   * @param {string} jsonString - JSON字符串
   * @returns {object} 样式配置对象
   */
  importStyleConfig(jsonString) {
    try {
      const config = JSON.parse(jsonString)
      const validation = this.validateStyleConfig(config)
      
      if (!validation.valid) {
        throw new Error(`样式配置验证失败: ${validation.errors.join(', ')}`)
      }

      return config
    } catch (error) {
      throw new Error(`导入样式配置失败: ${error.message}`)
    }
  }
}

// 创建全局实例
export const dxfStyleManager = new DxfStyleManager()

export default {
  DxfStyleManager,
  dxfStyleManager
} 