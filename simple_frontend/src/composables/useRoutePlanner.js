import { ref, watch } from 'vue'
import { Draw, Modify, Snap } from 'ol/interaction'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import LineString from 'ol/geom/LineString'
import Point from 'ol/geom/Point'
import { Style, Stroke, Circle as CircleStyle, Fill } from 'ol/style'
import Overlay from 'ol/Overlay'
import { generateFilletedSegments } from '@/utils/routeGeometry'

/**
 * 路径规划功能 Composable
 * @param {Object} map - OpenLayers 地图实例
 * @param {String} mode - 交互模式 'DRAW' | 'EDIT' | 'NONE'
 * @param {Number} defaultRadius - 默认转弯半径
 */
export function useRoutePlanner(map, mode, defaultRadius) {
  // 路径节点
  const routeNodes = ref([])
  const selectedNodeIndex = ref(null)
  
  // 图层引用
  const controlSource = ref(new VectorSource()) // 控制线
  const arcSource = ref(new VectorSource())     // 圆弧
  const lineSource = ref(new VectorSource())    // 直线
  const pointSource = ref(new VectorSource())   // 控制点
  
  // 交互引用
  const drawInteraction = ref(null)
  const modifyInteraction = ref(null)
  const snapInteraction = ref(null)
  
  // 绘制状态
  const isDrawing = ref(false)
  const sketchFeature = ref(null)
  
  // 距离提示工具
  const tooltipElement = ref(null)
  const tooltipOverlay = ref(null)
  const segments = ref([])
  
  // 样式
  const controlStyle = new Style({
    stroke: new Stroke({
      color: 'rgba(59, 130, 246, 0.3)',
      width: 1,
      lineDash: [5, 5],
    }),
  })
  
  const lineStyle = new Style({
    stroke: new Stroke({
      color: '#2563eb',
      width: 3,
    }),
  })
  
  const arcStyle = new Style({
    stroke: new Stroke({
      color: '#ef4444',
      width: 3,
    }),
  })
  
  const pointStyleFunc = (feature) => {
    const isSelected = feature.get('isSelected')
    return new Style({
      image: new CircleStyle({
        radius: isSelected ? 8 : 5,
        fill: new Fill({ color: isSelected ? '#ef4444' : '#ffffff' }),
        stroke: new Stroke({ color: '#3b82f6', width: 2 }),
      }),
    })
  }
  
  // 初始化图层
  const initLayers = () => {
    if (!map.value) return
    
    const controlLayer = new VectorLayer({
      source: controlSource.value,
      style: controlStyle,
      zIndex: 100
    })
    
    const lineLayer = new VectorLayer({
      source: lineSource.value,
      style: lineStyle,
      zIndex: 101
    })
    
    const arcLayer = new VectorLayer({
      source: arcSource.value,
      style: arcStyle,
      zIndex: 102
    })
    
    const pointLayer = new VectorLayer({
      source: pointSource.value,
      style: pointStyleFunc,
      zIndex: 103
    })
    
    map.value.addLayer(controlLayer)
    map.value.addLayer(lineLayer)
    map.value.addLayer(arcLayer)
    map.value.addLayer(pointLayer)
  }
  
  // 初始化工具提示
  const initTooltip = () => {
    if (!map.value) return
    
    const tooltipEl = document.createElement('div')
    tooltipEl.style.position = 'absolute'
    tooltipEl.style.backgroundColor = 'rgba(0, 0, 0, 0.8)'
    tooltipEl.style.color = 'white'
    tooltipEl.style.padding = '4px 8px'
    tooltipEl.style.borderRadius = '4px'
    tooltipEl.style.fontSize = '12px'
    tooltipEl.style.whiteSpace = 'nowrap'
    tooltipEl.style.pointerEvents = 'none'
    tooltipEl.style.zIndex = '1000'
    tooltipEl.style.display = 'none'
    tooltipElement.value = tooltipEl
    document.body.appendChild(tooltipEl)
    
    const overlay = new Overlay({
      element: tooltipEl,
      offset: [10, 0],
      positioning: 'bottom-left',
      stopEvent: false
    })
    tooltipOverlay.value = overlay
    map.value.addOverlay(overlay)
  }
  
  // 更新路径渲染
  const updateRouteRender = () => {
    // 更新控制线
    const coords = routeNodes.value.map(n => [n.x, n.y])
    const features = controlSource.value.getFeatures()
    
    if (routeNodes.value.length > 1) {
      if (features.length > 0) {
        const geom = features[0].getGeometry()
        if (geom instanceof LineString) {
          geom.setCoordinates(coords)
        }
      } else {
        const feature = new Feature(new LineString(coords))
        controlSource.value.addFeature(feature)
      }
    } else {
      controlSource.value.clear()
    }
    
    // 更新控制点
    pointSource.value.clear()
    routeNodes.value.forEach((node, idx) => {
      const feat = new Feature(new Point([node.x, node.y]))
      feat.set('index', idx)
      feat.set('isSelected', idx === selectedNodeIndex.value)
      pointSource.value.addFeature(feat)
    })
    
    // 生成并渲染路径段
    const generatedSegments = generateFilletedSegments(routeNodes.value)
    segments.value = generatedSegments
    
    arcSource.value.clear()
    lineSource.value.clear()
    
    generatedSegments.forEach(seg => {
      const geom = new LineString(seg.coordinates.map(c => [c.x, c.y]))
      const feat = new Feature(geom)
      if (seg.type === 'arc') {
        arcSource.value.addFeature(feat)
      } else {
        lineSource.value.addFeature(feat)
      }
    })
  }
  
  // 事件处理器引用
  let handleMapClickRef = null
  let handleMapDblClickRef = null
  let handleKeyDownRef = null
  
  // 点击选择节点
  const handleMapClick = (e) => {
    if (mode.value !== 'EDIT') return
    
    const pixel = e.pixel
    const feature = map.value.forEachFeatureAtPixel(pixel, (feat) => feat, {
      layerFilter: (layer) => {
        const source = layer.getSource()
        return source === pointSource.value
      },
      hitTolerance: 10
    })
    
    if (feature) {
      const index = feature.get('index')
      selectedNodeIndex.value = index
      updateRouteRender()
    } else {
      selectedNodeIndex.value = null
      updateRouteRender()
    }
  }
  
  // 双击插入节点
  const handleMapDblClick = (e) => {
    if (mode.value !== 'EDIT') return
    
    const clickCoords = e.coordinate
    const nodes = routeNodes.value
    if (nodes.length < 2) return
    
    const mapResolution = map.value.getView().getResolution() || 1
    const threshold = 10 * mapResolution
    
    let minDistance = Infinity
    let insertIndex = -1
    let insertPoint = { x: 0, y: 0 }
    
    const getClosest = (p, a, b) => {
      const atob = { x: b.x - a.x, y: b.y - a.y }
      const atop = { x: p.x - a.x, y: p.y - a.y }
      const lenSq = atob.x * atob.x + atob.y * atob.y
      if (lenSq === 0) return a
      const dot = atop.x * atob.x + atop.y * atob.y
      const t = Math.max(0, Math.min(1, dot / lenSq))
      return {
        x: a.x + atob.x * t,
        y: a.y + atob.y * t
      }
    }
    
    for (let i = 0; i < nodes.length - 1; i++) {
      const p1 = nodes[i]
      const p2 = nodes[i + 1]
      const closest = getClosest({ x: clickCoords[0], y: clickCoords[1] }, p1, p2)
      const dist = Math.sqrt((closest.x - clickCoords[0]) ** 2 + (closest.y - clickCoords[1]) ** 2)
      
      if (dist < minDistance) {
        minDistance = dist
        insertIndex = i + 1
        insertPoint = closest
      }
    }
    
    if (insertIndex !== -1 && minDistance < threshold) {
      const newNodes = [...nodes]
      newNodes.splice(insertIndex, 0, { ...insertPoint, radius: defaultRadius.value })
      routeNodes.value = newNodes
      e.preventDefault()
      return false
    }
  }
  
  // 键盘事件处理（删除节点）
  const handleKeyDown = (e) => {
    if (mode.value !== 'EDIT' || selectedNodeIndex.value === null) return
    
    if (e.key === 'Delete' || e.key === 'Backspace') {
      const newNodes = [...routeNodes.value]
      newNodes.splice(selectedNodeIndex.value, 1)
      routeNodes.value = newNodes
      selectedNodeIndex.value = null
      e.preventDefault()
    }
  }
  
  // 设置交互
  const setupInteractions = () => {
    if (!map.value) return
    
    // 清除旧交互
    if (drawInteraction.value) map.value.removeInteraction(drawInteraction.value)
    if (modifyInteraction.value) map.value.removeInteraction(modifyInteraction.value)
    if (snapInteraction.value) map.value.removeInteraction(snapInteraction.value)
    
    // 移除旧事件监听
    if (handleMapClickRef) {
      map.value.un('click', handleMapClickRef)
    }
    if (handleMapDblClickRef) {
      map.value.un('dblclick', handleMapDblClickRef)
    }
    if (handleKeyDownRef) {
      window.removeEventListener('keydown', handleKeyDownRef)
    }
    
    const snap = new Snap({ source: controlSource.value })
    const snapPoints = new Snap({ source: pointSource.value })
    
    if (mode.value === 'DRAW') {
      const draw = new Draw({
        source: controlSource.value,
        type: 'LineString',
      })
      
      draw.on('drawstart', (e) => {
        isDrawing.value = true
        sketchFeature.value = e.feature
      })
      
      draw.on('drawend', (e) => {
        isDrawing.value = false
        sketchFeature.value = null
        
        const geom = e.feature.getGeometry()
        if (geom instanceof LineString) {
          const newCoords = geom.getCoordinates().map(c => ({ x: c[0], y: c[1] }))
          let updatedNodes = [...routeNodes.value]
          
          if (updatedNodes.length > 0) {
            const lastNode = updatedNodes[updatedNodes.length - 1]
            const firstNode = updatedNodes[0]
            const newFirst = newCoords[0]
            const newLast = newCoords[newCoords.length - 1]
            
            const dist = (a, b) => Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
            const TOLERANCE = 100
            
            if (dist(lastNode, newFirst) < TOLERANCE) {
              const toAdd = newCoords.slice(1).map(c => ({ ...c, radius: defaultRadius.value }))
              updatedNodes = [...updatedNodes, ...toAdd]
            } else if (dist(firstNode, newLast) < TOLERANCE) {
              const toAdd = newCoords.slice(0, newCoords.length - 1).map(c => ({ ...c, radius: defaultRadius.value }))
              updatedNodes = [...toAdd, ...updatedNodes]
            } else if (dist(lastNode, newLast) < TOLERANCE) {
              const reversed = [...newCoords].reverse()
              const toAdd = reversed.slice(1).map(c => ({ ...c, radius: defaultRadius.value }))
              updatedNodes = [...updatedNodes, ...toAdd]
            } else if (dist(firstNode, newFirst) < TOLERANCE) {
              const reversed = [...newCoords].reverse()
              const toAdd = reversed.slice(0, reversed.length - 1).map(c => ({ ...c, radius: defaultRadius.value }))
              updatedNodes = [...toAdd, ...updatedNodes]
            } else {
              updatedNodes = newCoords.map(c => ({ ...c, radius: defaultRadius.value }))
            }
          } else {
            updatedNodes = newCoords.map(c => ({ ...c, radius: defaultRadius.value }))
          }
          
          routeNodes.value = updatedNodes
          
          setTimeout(() => {
            controlSource.value.clear()
          }, 0)
        }
      })
      
      draw.on('drawabort', () => {
        isDrawing.value = false
        sketchFeature.value = null
      })
      
      map.value.addInteraction(draw)
      drawInteraction.value = draw
    } else if (mode.value === 'EDIT') {
      const modify = new Modify({
        source: pointSource.value,
      })
      
      modify.on('modifyend', () => {
        const features = pointSource.value.getFeatures()
        const newNodes = [...routeNodes.value]
        features.forEach(f => {
          const idx = f.get('index')
          const geom = f.getGeometry()
          if (geom instanceof Point && typeof idx === 'number') {
            const coords = geom.getCoordinates()
            if (newNodes[idx]) {
              newNodes[idx] = { ...newNodes[idx], x: coords[0], y: coords[1] }
            }
          }
        })
        routeNodes.value = newNodes
      })
      
      map.value.addInteraction(modify)
      modifyInteraction.value = modify
    }
    
    map.value.addInteraction(snap)
    map.value.addInteraction(snapPoints)
    snapInteraction.value = snap
    
    // 添加事件监听
    if (mode.value === 'EDIT') {
      handleMapClickRef = handleMapClick
      handleMapDblClickRef = handleMapDblClick
      handleKeyDownRef = handleKeyDown
      map.value.on('click', handleMapClickRef)
      map.value.on('dblclick', handleMapDblClickRef)
      window.addEventListener('keydown', handleKeyDownRef)
    } else {
      handleMapClickRef = null
      handleMapDblClickRef = null
      handleKeyDownRef = null
    }
  }
  
  // 监听节点变化，更新渲染
  watch([routeNodes, selectedNodeIndex], () => {
    updateRouteRender()
  }, { deep: true })
  
  // 监听模式变化，更新交互
  watch(mode, () => {
    setupInteractions()
  })
  
  // 初始化
  const init = () => {
    if (!map.value) return
    initLayers()
    initTooltip()
    setupInteractions()
  }
  
  // 清理
  const cleanup = () => {
    if (tooltipElement.value && tooltipElement.value.parentNode) {
      tooltipElement.value.parentNode.removeChild(tooltipElement.value)
    }
    if (map.value) {
      if (handleMapClickRef) {
        map.value.un('click', handleMapClickRef)
      }
      if (handleMapDblClickRef) {
        map.value.un('dblclick', handleMapDblClickRef)
      }
      if (drawInteraction.value) map.value.removeInteraction(drawInteraction.value)
      if (modifyInteraction.value) map.value.removeInteraction(modifyInteraction.value)
      if (snapInteraction.value) map.value.removeInteraction(snapInteraction.value)
    }
    if (handleKeyDownRef) {
      window.removeEventListener('keydown', handleKeyDownRef)
    }
  }
  
  return {
    routeNodes,
    selectedNodeIndex,
    init,
    cleanup,
    updateRouteRender
  }
}
