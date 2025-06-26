/**
 * Leaflet VectorGrid 兼容性修复
 * 解决 Leaflet 1.8+ 版本中 L.DomEvent.fakeStop 不存在的问题
 */

import L from 'leaflet'

/**
 * 修复 VectorGrid 与 Leaflet 1.8+ 的兼容性问题
 * 方案1：为 Canvas.Tile 添加修复的 _onClick 方法
 * 方案3：添加 fakeStop polyfill
 */
export function fixVectorGridCompatibility() {
  //console.log('应用 VectorGrid 兼容性修复...')
  
  // 方案3：添加 fakeStop polyfill（最直接的修复）
  if (!L.DomEvent.fakeStop) {
    //console.log('添加 L.DomEvent.fakeStop polyfill')
    L.DomEvent.fakeStop = function(e) {
      // 改进的 polyfill，只阻止默认行为，不阻止事件传播
      if (e && e.preventDefault) {
        e.preventDefault()
      }
      if (e) {
        e._stopped = true
      }
      return false
    }
  }
  
  // 检查是否需要修复
  if (L.Canvas && L.Canvas.Tile) {
    //console.log('检测到 Leaflet 1.8+，应用 VectorGrid 兼容性修复')
    
    // 方案1：重写 Canvas.Tile 的 _onClick 方法（改进版）
    L.Canvas.Tile.include({
      _onClick: function (e) {
        var point = this._map.mouseEventToLayerPoint(e).subtract(this.getOffset())
        var layer
        var clickedLayer
        
        for (var id in this._layers) {
          layer = this._layers[id]
          if (
            layer.options.interactive &&
            layer._containsPoint(point) &&
            !this._map._draggableMoved(layer)
          ) {
            clickedLayer = layer
          }
        }
        
        if (clickedLayer) {
          // 不调用 fakeStop，让事件正常传播
          // 直接触发图层事件，保留原始事件信息
          var layerPoint = this._map.mouseEventToLayerPoint(e)
          var latlng = this._map.layerPointToLatLng(layerPoint)
          
          clickedLayer.fireEvent('click', {
            latlng: latlng,
            layerPoint: layerPoint,
            containerPoint: this._map.latLngToContainerPoint(latlng),
            originalEvent: e,
            layer: clickedLayer,
            target: this,
            type: 'click'
          }, true)
        }
      }
    })
    
    //console.log('VectorGrid 兼容性修复已应用')
  } else {
    console.warn('无法识别的 Leaflet 版本或 VectorGrid 未加载')
  }
}

/**
 * 方案2：使用 SVG 渲染器（备选方案）
 * 如果方案1不工作，可以尝试强制使用 SVG 渲染器
 */
export function getCompatibleRendererFactory() {
  // SVG 渲染器不受此问题影响
  return L.svg.tile
}

/**
 * 检查 VectorGrid 兼容性
 */
export function checkVectorGridCompatibility() {
  const issues = []
  
  if (!L.vectorGrid) {
    issues.push('VectorGrid 插件未加载')
  }
  
  if (!L.DomEvent.fakeStop && L.Canvas && L.Canvas.Tile) {
    issues.push('检测到 Leaflet 1.8+ 兼容性问题，需要修复')
  }
  
  return {
    isCompatible: issues.length === 0,
    issues: issues,
    leafletVersion: L.version || '未知'
  }
} 