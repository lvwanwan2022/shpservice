/**
 * MVT图层工具类 - 基于test_martin_mvt.html成功实现
 * 使用与HTML示例完全相同的逻辑来确保兼容性
 */

import L from 'leaflet'
import 'leaflet.vectorgrid'

/**
 * 检查MVT支持
 */
export function checkMVTSupport() {
  const hasSupport = !!(L.vectorGrid && L.vectorGrid.protobuf)
  //console.log('MVT支持检查:', hasSupport)
  return hasSupport
}

/**
 * 创建样式函数 - 与HTML示例保持一致
 * @param {Object} userStyle - 用户样式配置
 * @returns {Function} 样式函数
 */
function createStyleFunction(userStyle = {}) {
  return function(properties, zoom, geometryDimension) {
    //console.log('样式函数调用:', { properties, zoom, geometryDimension })
    
    // 点样式 (geometryDimension === 1)
    if (geometryDimension === 1) {
      const pointStyle = userStyle.point || {}
      return {
        weight: 2,
        color: pointStyle.color || '#FF0000',
        opacity: 1,
        fillColor: pointStyle.color || '#FF0000',
        fill: true,
        radius: pointStyle.size || 6,
        fillOpacity: pointStyle.opacity || 0.8
      }
    }
    
    // 线样式 (geometryDimension === 2)
    if (geometryDimension === 2) {
      const lineStyle = userStyle.line || {}
      const style = {
        weight: lineStyle.width || 2,
        color: lineStyle.color || '#0000FF',
        opacity: lineStyle.opacity || 1
      }
      
      // 线型样式
      if (lineStyle.style === 'dashed') {
        style.dashArray = '8,4'
      } else if (lineStyle.style === 'dotted') {
        style.dashArray = '2,4'
      }
      
      return style
    }
    
    // 面样式 (geometryDimension === 3)
    if (geometryDimension === 3) {
      const polygonStyle = userStyle.polygon || {}
      return {
        weight: polygonStyle.outlineWidth || 1,
        color: polygonStyle.outlineColor || '#0000FF',
        opacity: polygonStyle.opacity || 1,
        fillColor: polygonStyle.fillColor || '#00FF00',
        fill: true,
        fillOpacity: polygonStyle.fillOpacity || 0.6
      }
    }
    
    // 默认样式
    return {
      weight: 2,
      color: '#3388ff',
      opacity: 1,
      fillColor: '#3388ff',
      fill: true,
      fillOpacity: 0.6
    }
  }
}

/**
 * 创建MVT图层 - 完全基于test_martin_mvt.html的成功实现
 * @param {Object} layerConfig - 图层配置
 * @param {string} layerConfig.mvt_url - MVT瓦片URL模板
 * @param {string} layerConfig.tilejson_url - TileJSON URL
 * @param {string} layerConfig.layer_name - 图层名称
 * @param {Object} layerConfig.style - 图层样式
 * @returns {Promise<L.Layer>} Leaflet图层对象
 */
export async function createMVTLayer(layerConfig) {
  //console.log('🎯 开始创建MVT图层:', layerConfig)
  
  // 参数验证
  if (!layerConfig || !layerConfig.mvt_url) {
    const error = new Error('MVT URL不能为空')
    console.error('参数验证失败:', error.message)
    throw error
  }
  
  if (!checkMVTSupport()) {
    const error = new Error('浏览器不支持MVT瓦片，请安装Leaflet.VectorGrid插件')
    console.error('MVT支持检查失败:', error.message)
    throw error
  }
  
  try {
    // 处理URL格式 - 确保与HTML示例一致（不带.pbf后缀）
    let mvtUrl = layerConfig.mvt_url
    
    // 移除.pbf后缀（如果存在）
    if (mvtUrl.includes('.pbf')) {
      mvtUrl = mvtUrl.replace('.pbf', '')
      //console.log('移除.pbf后缀，新URL:', mvtUrl)
    }
    
    // 验证URL格式
    if (!mvtUrl.includes('{z}') || !mvtUrl.includes('{x}') || !mvtUrl.includes('{y}')) {
      console.warn('⚠️ MVT URL格式可能不正确，缺少{z},{x},{y}参数:', mvtUrl)
    }
    
    //console.log('MVT URL:', mvtUrl)
    //console.log('TileJSON URL:', layerConfig.tilejson_url)
    
    // 创建样式函数
    const styleFunction = createStyleFunction(layerConfig.style)
    
    // VectorGrid选项 - 完全按照HTML示例配置
    const vectorTileOptions = {
      layerURL: mvtUrl,  // 兼容旧版API
      rendererFactory: L.canvas.tile,  // 使用Canvas渲染
      vectorTileLayerStyles: {},  // 将动态设置
      interactive: true,  // 重新启用交互以支持click事件
      maxZoom: 22,
      attribution: `MVT: ${layerConfig.layer_name}`,
      getFeatureId: function(f) {
        return f.properties.id || f.properties.fid || f.properties.gid || 
               f.properties.osm_id || f.properties.objectid || Math.random()
      },
      // 添加错误处理选项
      pane: 'overlayPane',
      tolerance: 0  // 减少tolerance以避免坐标计算问题
    }
    
    //console.log('正在获取TileJSON确定图层名称...')
    
    // 返回Promise，按HTML示例的逻辑处理
    return new Promise((resolve, reject) => {
      // 首先获取TileJSON来确定图层名称 - 与HTML示例完全一致
      if (layerConfig.tilejson_url) {
        fetch(layerConfig.tilejson_url)
          .then(response => {
            if (!response.ok) {
              throw new Error(`TileJSON请求失败: ${response.status} ${response.statusText}`)
            }
            return response.json()
          })
          .then(tilejsonData => {
            //console.log('TileJSON数据:', tilejsonData)
            
            // 获取图层名称 - 与HTML示例一致
            let layerNames = ['default']  // 默认图层名
            if (tilejsonData.vector_layers && Array.isArray(tilejsonData.vector_layers)) {
              layerNames = tilejsonData.vector_layers.map(layer => layer.id)
            }
            
            //console.log('检测到的图层名称:', layerNames)
            
            // 为每个图层设置样式 - 与HTML示例一致
            layerNames.forEach(layerName => {
              vectorTileOptions.vectorTileLayerStyles[layerName] = styleFunction
            })
            
            //console.log('VectorGrid选项:', vectorTileOptions)
            
            // 创建MVT图层 - 使用与HTML示例完全相同的方式
            const mvtLayer = L.vectorGrid.protobuf(mvtUrl, vectorTileOptions)
            
            if (!mvtLayer) {
              throw new Error('VectorGrid图层创建失败')
            }
            
            // 添加事件处理 - 与HTML示例保持一致
            addEventListeners(mvtLayer, layerConfig.layer_name)
            
            //console.log('✅ MVT图层创建成功')
            resolve(mvtLayer)
          })
          .catch(error => {
            console.error('TileJSON获取失败:', error)
            //console.log('尝试使用默认图层名直接加载...')
            
            // 如果TileJSON获取失败，使用默认配置 - 与HTML示例一致
            vectorTileOptions.vectorTileLayerStyles['default'] = styleFunction
            
            try {
              const mvtLayer = L.vectorGrid.protobuf(mvtUrl, vectorTileOptions)
              addEventListeners(mvtLayer, layerConfig.layer_name)
              //console.log('✅ 使用默认配置创建MVT图层成功')
              resolve(mvtLayer)
            } catch (directError) {
              console.error('直接加载也失败:', directError)
              reject(new Error(`图层加载完全失败: ${directError.message}`))
            }
          })
      } else {
        // 没有TileJSON URL，直接使用默认配置
        //console.log('没有TileJSON URL，使用默认图层名')
        vectorTileOptions.vectorTileLayerStyles['default'] = styleFunction
        
        try {
          const mvtLayer = L.vectorGrid.protobuf(mvtUrl, vectorTileOptions)
          addEventListeners(mvtLayer, layerConfig.layer_name)
          //console.log('✅ 使用默认配置创建MVT图层成功')
          resolve(mvtLayer)
        } catch (error) {
          console.error('默认配置加载失败:', error)
          reject(error)
        }
      }
    })
    
  } catch (error) {
    console.error('❌ 创建MVT图层失败:', error)
    throw error
  }
}

/**
 * 添加事件监听器 - 与HTML示例保持一致
 * @param {L.Layer} mvtLayer - MVT图层
 * @param {string} layerName - 图层名称
 */
function addEventListeners(mvtLayer, layerName) {
  // click事件 - 显示属性弹窗
  mvtLayer.on('mouseover', function(e) {
    //console.log('mouseover事件:', e)
    // 添加click事件来显示属性弹窗
    if (e.layer && e.layer.properties) {
      const properties = e.layer.properties
      const content = Object.entries(properties)
        .filter(([, value]) => value != null && value !== 'NULL' && value !== '')
        .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
        .join('<br/>')
      
      // 检查地图和坐标是否有效
      if (e.target._map && e.latlng && e.latlng.lat !== undefined && e.latlng.lng !== undefined) {
        L.popup()
          .setContent(`
            <div style="max-width: 300px;">
              <h4 style="margin: 0 0 10px 0; color: #333;">要素属性</h4>
              ${content || '无属性信息'}
            </div>
          `)
          .setLatLng(e.latlng)
          .openOn(e.target._map)
        
        //console.log('✅ 已显示要素属性弹窗')
      }
    }
  })
  
  
  mvtLayer.on('mouseout', function(/* e */) {
    mvtLayer.unbindTooltip()
  })
  
  // 加载事件
  mvtLayer.on('loading', () => {
    //console.log(`图层 "${layerName}" 开始加载`)
  })
  
  mvtLayer.on('load', () => {
    //console.log(`✅ 图层 "${layerName}" 加载完成`)
  })
  
  mvtLayer.on('tileerror', (e) => {
    console.error(`瓦片加载错误 "${layerName}":`, e)
  })
  
  mvtLayer.on('error', (e) => {
    console.error(`图层错误 "${layerName}":`, e)
  })
}

/**
 * 从Martin服务信息创建MVT图层
 * @param {Object} martinLayer - Martin图层信息
 * @returns {Promise<L.Layer>} 图层对象
 */
export async function createMVTLayerFromMartin(martinLayer) {
  //console.log('🔧 从Martin服务创建MVT图层:', martinLayer)
  
  const layerConfig = {
    mvt_url: martinLayer.mvt_url,
    tilejson_url: martinLayer.tilejson_url,
    layer_name: martinLayer.layer_name || martinLayer.title,
    style: martinLayer.style || {}
  }
  
  //console.log('构建的图层配置:', layerConfig)
  
  return createMVTLayer(layerConfig)
} 