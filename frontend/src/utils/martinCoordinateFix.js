/**
 * Martin服务坐标修复工具
 * 专门处理Martin MVT服务中可能出现的坐标问题
 */

import { isValidLatLng } from './coordinateUtils'

/**
 * 修复VectorGrid的缩放动画问题
 * @param {Object} L - Leaflet对象
 */
export function patchVectorGridZoomAnimation(L) {
  if (!L || !L.vectorGrid || !L.vectorGrid.protobuf) {
    console.warn('Leaflet VectorGrid不可用，跳过缩放动画补丁')
    return
  }

  ////console.log('应用VectorGrid缩放动画修复补丁...')

  // 修复VectorGrid的_animateZoom方法，防止_map为null的错误
  const originalVectorGridPrototype = L.VectorGrid.prototype
  if (originalVectorGridPrototype && originalVectorGridPrototype._animateZoom) {
    const original_animateZoom = originalVectorGridPrototype._animateZoom
    originalVectorGridPrototype._animateZoom = function(e) {
      try {
        // 检查地图实例是否存在
        if (!this._map) {
          console.warn('VectorGrid缩放动画：地图实例不存在，跳过动画')
          return
        }

        // 检查地图的_latLngToNewLayerPoint方法是否存在
        if (!this._map._latLngToNewLayerPoint) {
          console.warn('VectorGrid缩放动画：_latLngToNewLayerPoint方法不存在，跳过动画')
          return
        }

        // 调用原始方法
        return original_animateZoom.call(this, e)
      } catch (error) {
        console.error('VectorGrid缩放动画错误:', error)
        // 静默处理错误，不影响地图的其他功能
      }
    }
  }

  // 修复可能的Popup缩放动画问题
  if (L.Popup && L.Popup.prototype._animateZoom) {
    // const originalPopup_animateZoom = L.Popup.prototype._animateZoom // 注释掉未使用的变量
    L.Popup.prototype._animateZoom = function(e) {
      try {
        if (!this._map) {
          console.warn('Popup缩放动画：地图实例不存在，跳过动画')
          return
        }

        if (!this._map._latLngToNewLayerPoint) {
          console.warn('Popup缩放动画：_latLngToNewLayerPoint方法不存在，跳过动画')
          return
        }

        var pos = this._map._latLngToNewLayerPoint(this._latlng, e.zoom, e.center)
        var anchor = this._getAnchor()
        L.DomUtil.setPosition(this._container, pos.add(anchor))
      } catch (error) {
        console.error('Popup缩放动画错误:', error)
        // 静默处理错误
      }
    }
  }

  // 修复Marker的缩放动画问题
  if (L.Marker && L.Marker.prototype._animateZoom) {
    const originalMarker_animateZoom = L.Marker.prototype._animateZoom
    L.Marker.prototype._animateZoom = function(e) {
      try {
        if (!this._map) {
          console.warn('Marker缩放动画：地图实例不存在，跳过动画')
          return
        }

        if (!this._map._latLngToNewLayerPoint) {
          console.warn('Marker缩放动画：_latLngToNewLayerPoint方法不存在，跳过动画')
          return
        }

        return originalMarker_animateZoom.call(this, e)
      } catch (error) {
        console.error('Marker缩放动画错误:', error)
        // 静默处理错误
      }
    }
  }
}

/**
 * 为VectorGrid添加坐标安全检查补丁
 * @param {Object} L - Leaflet对象
 */
export function patchVectorGridCoordinates(L) {
  if (!L || !L.vectorGrid || !L.vectorGrid.protobuf) {
    console.warn('Leaflet VectorGrid不可用，跳过坐标补丁')
    return
  }

  ////console.log('应用VectorGrid坐标安全补丁...')

  const originalProtobuf = L.vectorGrid.protobuf

  L.vectorGrid.protobuf = function(url, options) {
    const layer = originalProtobuf.call(this, url, options)
    
    // 修复点要素的坐标问题 (来自 GitHub issue #267)
    if (layer._createLayer) {
      const original_createLayer = layer._createLayer
      layer._createLayer = function(feat, pxPerExtent, layerStyle) {
        let vectorLayer = original_createLayer.call(this, feat, pxPerExtent, layerStyle)
        
        // 对于点要素 (feat.type === 1)，清除getLatLng方法以避免坐标错误
        if (feat.type === 1 && vectorLayer) {
          vectorLayer.getLatLng = null
        }
        
        return vectorLayer
      }
    }
    
    // 需要拦截的所有鼠标事件类型
    const mouseEvents = ['click', 'mouseover', 'mouseout', 'mousemove', 'mousedown', 'mouseup', 'dblclick', 'contextmenu']
    
    // 包装原始的_fireDOMEvent方法
    if (layer._fireDOMEvent) {
      const originalFireDOMEvent = layer._fireDOMEvent
      layer._fireDOMEvent = function(e, type, propagate) {
        try {
          // 检查是否是鼠标事件且包含坐标信息
          if (mouseEvents.includes(type) && e && e.latlng) {
            // 验证坐标的有效性
            if (!isValidLatLng(e.latlng)) {
              console.warn(`VectorGrid鼠标事件"${type}"包含无效坐标，已跳过:`, e.latlng)
              return this
            }
          }
          
          return originalFireDOMEvent.call(this, e, type, propagate)
        } catch (error) {
          console.error(`VectorGrid事件"${type}"处理错误:`, error)
          return this
        }
      }
    }

    // 包装原始的fire方法
    if (layer.fire) {
      const originalFire = layer.fire
      layer.fire = function(type, data, propagate) {
        try {
          // 如果事件数据包含坐标信息，进行验证
          if (data && data.latlng && mouseEvents.includes(type)) {
            if (!isValidLatLng(data.latlng)) {
              console.warn(`VectorGrid fire事件"${type}"包含无效坐标，已跳过:`, data.latlng)
              return this
            }
          }
          
          return originalFire.call(this, type, data, propagate)
        } catch (error) {
          console.error(`VectorGrid fire事件"${type}"处理错误:`, error)
          return this
        }
      }
    }

    // 包装图层的所有鼠标事件监听器
    const originalOn = layer.on
    if (originalOn) {
      layer.on = function(type, fn, context) {
        if (mouseEvents.includes(type)) {
          // 创建安全的事件处理器包装器
          const safeFn = function(e) {
            try {
              if (e && e.latlng && !isValidLatLng(e.latlng)) {
                console.warn(`图层事件"${type}"包含无效坐标，已跳过:`, e.latlng)
                return
              }
              return fn.call(this, e)
            } catch (error) {
              console.error(`图层事件"${type}"处理错误:`, error)
            }
          }
          return originalOn.call(this, type, safeFn, context)
        }
        return originalOn.call(this, type, fn, context)
      }
    }

    return layer
  }

  // 复制原始方法的属性
  Object.setPrototypeOf(L.vectorGrid.protobuf, originalProtobuf)
  Object.assign(L.vectorGrid.protobuf, originalProtobuf)
}

/**
 * 应用Martin服务坐标修复补丁
 * @param {Object} L - Leaflet对象
 */
export function applyMartinCoordinateFixes(L) {
  ////console.log('应用Martin服务坐标修复补丁...')
  
  try {
    // 应用VectorGrid坐标补丁
    patchVectorGridCoordinates(L)
    
    // 应用VectorGrid缩放动画修复补丁
    patchVectorGridZoomAnimation(L)
    
    ////console.log('Martin服务坐标修复补丁应用完成')
  } catch (error) {
    console.error('应用坐标修复补丁失败:', error)
  }
}

export default {
  patchVectorGridCoordinates,
  patchVectorGridZoomAnimation,
  applyMartinCoordinateFixes
} 