import { ref, watch } from 'vue'
import { Draw, Modify, Snap } from 'ol/interaction'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import LineString from 'ol/geom/LineString'
import Point from 'ol/geom/Point'
import { Style, Stroke, Circle as CircleStyle, Fill } from 'ol/style'
import Overlay from 'ol/Overlay'
import { generateFilletedSegments, IndustryMode } from '@/utils/routeGeometry'

/**
 * 路径规划功能 Composable
 * @param {Object} map - OpenLayers 地图实例
 * @param {String} mode - 交互模式 'DRAW' | 'EDIT' | 'NONE'
 * @param {Number} defaultRadius - 默认转弯半径
 * @param {String} industryMode - 行业模式 'WATER' | 'HIGHWAY'，默认'WATER'
 * @param {Number} defaultSpiralLen - 默认缓和曲线长度，默认0
 */
export function useRoutePlanner(map, mode, defaultRadius, industryMode = IndustryMode.WATER, defaultSpiralLen = 0) {
  // 路径节点
  const routeNodes = ref([])
  const selectedNodeIndex = ref(null)
  
  // 行业模式和默认缓和曲线长度（如果传入的是ref，直接使用；否则创建ref）
  const industryModeRef = ref(industryMode)
  const defaultSpiralLenRef = ref(defaultSpiralLen)
  
  // 如果传入的是ref，同步更新
  if (industryMode && typeof industryMode === 'object' && 'value' in industryMode) {
    watch(industryMode, (val) => { industryModeRef.value = val }, { immediate: true })
  }
  if (defaultSpiralLen && typeof defaultSpiralLen === 'object' && 'value' in defaultSpiralLen) {
    watch(defaultSpiralLen, (val) => { defaultSpiralLenRef.value = val }, { immediate: true })
  }
  
  // 图层引用
  const controlSource = ref(new VectorSource()) // 控制线
  const arcSource = ref(new VectorSource())     // 圆弧
  const lineSource = ref(new VectorSource())    // 直线
  const spiralSource = ref(new VectorSource())  // 缓和曲线（公路模式）
  const pointSource = ref(new VectorSource())   // 控制点
  
  // 图层对象引用（用于cleanup时移除）
  const controlLayer = ref(null)
  const lineLayer = ref(null)
  const spiralLayer = ref(null)
  const arcLayer = ref(null)
  const pointLayer = ref(null)
  
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
      color: 'rgba(59, 130, 246, 0.6)', // 提高不透明度，从 0.3 改为 0.6
      width: 2, // 加粗线宽，从 1 改为 2
      lineDash: [8, 6], // 调整虚线样式，从 [5, 5] 改为 [8, 6]
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
  
  // 缓和曲线样式（公路模式）
  const spiralStyle = new Style({
    stroke: new Stroke({
      color: '#9333ea', // 紫色
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
    
    // 如果图层已经存在，先移除旧的图层
    if (controlLayer.value) map.value.removeLayer(controlLayer.value)
    if (lineLayer.value) map.value.removeLayer(lineLayer.value)
    if (spiralLayer.value) map.value.removeLayer(spiralLayer.value)
    if (arcLayer.value) map.value.removeLayer(arcLayer.value)
    if (pointLayer.value) map.value.removeLayer(pointLayer.value)
    
    controlLayer.value = new VectorLayer({
      source: controlSource.value,
      style: controlStyle,
      zIndex: 100
    })
    
    lineLayer.value = new VectorLayer({
      source: lineSource.value,
      style: lineStyle,
      zIndex: 101
    })
    
    spiralLayer.value = new VectorLayer({
      source: spiralSource.value,
      style: spiralStyle,
      zIndex: 101.5
    })
    
    arcLayer.value = new VectorLayer({
      source: arcSource.value,
      style: arcStyle,
      zIndex: 102
    })
    
    pointLayer.value = new VectorLayer({
      source: pointSource.value,
      style: pointStyleFunc,
      zIndex: 103
    })
    
    map.value.addLayer(controlLayer.value)
    map.value.addLayer(lineLayer.value)
    map.value.addLayer(spiralLayer.value)
    map.value.addLayer(arcLayer.value)
    map.value.addLayer(pointLayer.value)
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
    const generatedSegments = generateFilletedSegments(
      routeNodes.value, 
      industryModeRef.value || IndustryMode.WATER,
      defaultSpiralLenRef.value || 0
    )
    segments.value = generatedSegments
    
    arcSource.value.clear()
    lineSource.value.clear()
    spiralSource.value.clear()
    
    generatedSegments.forEach(seg => {
      const geom = new LineString(seg.coordinates.map(c => [c.x, c.y]))
      const feat = new Feature(geom)
      if (seg.type === 'arc') {
        arcSource.value.addFeature(feat)
      } else if (seg.type === 'spiral') {
        spiralSource.value.addFeature(feat)
      } else {
        lineSource.value.addFeature(feat)
      }
    })
  }
  
  // 确保所有节点都有radius属性的辅助函数
  const ensureNodesHaveRadius = () => {
    const nodesWithRadius = routeNodes.value.map(node => {
      if (node.radius === undefined || node.radius === null) {
        return { ...node, radius: defaultRadius.value }
      }
      return node
    })
    
    // 检查是否有节点需要更新radius
    const needsUpdate = nodesWithRadius.some((node, idx) => {
      const oldNode = routeNodes.value[idx]
      return !oldNode || node.radius !== oldNode.radius
    })
    
    if (needsUpdate) {
      routeNodes.value = nodesWithRadius
    }
  }
  
  // 事件处理器引用
  let handleMapClickRef = null
  let handleMapDblClickRef = null
  let handleKeyDownRef = null

  // 点击选择节点
  const handleMapClick = (e) => {
    if (mode.value !== 'EDIT') return
    
    const pixel = e.pixel
    // 优先检查是否点击了控制点
    const feature = map.value.forEachFeatureAtPixel(pixel, (feat) => {
      // 只选择控制点图层中的要素
      return feat
    }, {
      layerFilter: (layer) => {
        const source = layer.getSource()
        // 只检查控制点图层
        return source === pointSource.value
      },
      hitTolerance: 10 // 点击容差
    })
    
    if (feature) {
      const index = feature.get('index')
      if (index !== undefined && index !== null) {
        // 更新选中状态
        selectedNodeIndex.value = index
        // 确保节点有radius属性
        const nodes = [...routeNodes.value]
        if (nodes[index] && (nodes[index].radius === undefined || nodes[index].radius === null)) {
          nodes[index] = { ...nodes[index], radius: defaultRadius.value }
          routeNodes.value = nodes
        }
        // 确保节点有spiralLength属性（如果是公路模式）
        if (industryModeRef.value === 'HIGHWAY' && nodes[index] && (nodes[index].spiralLength === undefined || nodes[index].spiralLength === null)) {
          nodes[index] = { ...nodes[index], spiralLength: defaultSpiralLenRef.value || 0 }
          routeNodes.value = nodes
        }
      }
    } else {
      // 点击空白处，取消选择
      selectedNodeIndex.value = null
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
      newNodes.splice(insertIndex, 0, { 
        ...insertPoint, 
        radius: defaultRadius.value,
        spiralLength: defaultSpiralLenRef.value || 0
      })
      routeNodes.value = newNodes
      e.preventDefault()
      return false
    }
  }
  
  // 键盘事件处理（删除节点和ESC撤销）
  const handleKeyDown = (e) => {
    // Delete键删除节点（仅在编辑模式且有选中节点时）
    if (mode.value === 'EDIT' && selectedNodeIndex.value !== null) {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const newNodes = [...routeNodes.value]
        if (newNodes.length > 0 && selectedNodeIndex.value >= 0 && selectedNodeIndex.value < newNodes.length) {
          newNodes.splice(selectedNodeIndex.value, 1)
          routeNodes.value = newNodes
          selectedNodeIndex.value = null
          e.preventDefault()
          e.stopPropagation()
          return false
        }
      }
    }
    
    // ESC键撤销操作
    if (e.key === 'Escape' || e.key === 'Esc') {
      if (mode.value === 'DRAW') {
        e.preventDefault()
        e.stopPropagation()
        if (isDrawing.value && drawInteraction.value) {
          const sketch = sketchFeature.value
          if (sketch) {
            const geom = sketch.getGeometry()
            if (geom instanceof LineString && geom.getCoordinates().length > 2) {
              // 撤销最后一个点
              drawInteraction.value.removeLastPoint()
            } else {
              // 取消绘制
              drawInteraction.value.abortDrawing()
            }
          }
        } else {
          // 如果没有正在绘制，删除最后一个节点
          if (routeNodes.value.length > 0) {
            routeNodes.value = routeNodes.value.slice(0, -1)
          }
        }
        return false
      } else if (mode.value === 'EDIT') {
        // 编辑模式下，ESC取消选择
        if (selectedNodeIndex.value !== null) {
          selectedNodeIndex.value = null
          e.preventDefault()
          e.stopPropagation()
          return false
        }
      }
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
              const toAdd = newCoords.slice(1).map(c => ({ 
                ...c, 
                radius: defaultRadius.value,
                spiralLength: defaultSpiralLenRef.value || 0
              }))
              updatedNodes = [...updatedNodes, ...toAdd]
            } else if (dist(firstNode, newLast) < TOLERANCE) {
              const toAdd = newCoords.slice(0, newCoords.length - 1).map(c => ({ 
                ...c, 
                radius: defaultRadius.value,
                spiralLength: defaultSpiralLenRef.value || 0
              }))
              updatedNodes = [...toAdd, ...updatedNodes]
            } else if (dist(lastNode, newLast) < TOLERANCE) {
              const reversed = [...newCoords].reverse()
              const toAdd = reversed.slice(1).map(c => ({ 
                ...c, 
                radius: defaultRadius.value,
                spiralLength: defaultSpiralLenRef.value || 0
              }))
              updatedNodes = [...updatedNodes, ...toAdd]
            } else if (dist(firstNode, newFirst) < TOLERANCE) {
              const reversed = [...newCoords].reverse()
              const toAdd = reversed.slice(0, reversed.length - 1).map(c => ({ 
                ...c, 
                radius: defaultRadius.value,
                spiralLength: defaultSpiralLenRef.value || 0
              }))
              updatedNodes = [...toAdd, ...updatedNodes]
            } else {
              updatedNodes = newCoords.map(c => ({ 
                ...c, 
                radius: defaultRadius.value,
                spiralLength: defaultSpiralLenRef.value || 0
              }))
            }
          } else {
            updatedNodes = newCoords.map(c => ({ 
              ...c, 
              radius: defaultRadius.value,
              spiralLength: defaultSpiralLenRef.value || 0
            }))
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
      // 配置 Modify 交互 - 参考 openlayers-RouterPlanner 的简单实现
      const modify = new Modify({
        source: pointSource.value,
        pixelTolerance: 10
      })
      
      // 修改结束，更新节点位置
      modify.on('modifyend', () => {
        const features = pointSource.value.getFeatures()
        const newNodes = [...routeNodes.value]
        features.forEach(f => {
          const idx = f.get('index')
          const geom = f.getGeometry()
          if (geom instanceof Point && typeof idx === 'number') {
            const coords = geom.getCoordinates()
            if (newNodes[idx]) {
              // 保持原有的radius和spiralLength属性，如果没有则使用默认值
              const radius = newNodes[idx].radius !== undefined && newNodes[idx].radius !== null 
                ? newNodes[idx].radius 
                : defaultRadius.value
              const spiralLength = newNodes[idx].spiralLength !== undefined && newNodes[idx].spiralLength !== null
                ? newNodes[idx].spiralLength
                : (defaultSpiralLenRef.value || 0)
              newNodes[idx] = { ...newNodes[idx], x: coords[0], y: coords[1], radius, spiralLength }
            }
          }
        })
        routeNodes.value = newNodes
      })
      
      map.value.addInteraction(modify)
      modifyInteraction.value = modify
    }
    
    // 只在DRAW或EDIT模式下添加Snap交互
    if (mode.value === 'DRAW' || mode.value === 'EDIT') {
      map.value.addInteraction(snap)
      map.value.addInteraction(snapPoints)
      snapInteraction.value = snap
    }
    
    // 添加事件监听
    if (mode.value === 'EDIT') {
      handleMapClickRef = handleMapClick
      handleMapDblClickRef = handleMapDblClick
      // 添加点击和双击监听
      map.value.on('click', handleMapClickRef)
      map.value.on('dblclick', handleMapDblClickRef)
    } else {
      handleMapClickRef = null
      handleMapDblClickRef = null
    }
    
    // 键盘事件只在DRAW或EDIT模式下监听
    if (mode.value === 'DRAW' || mode.value === 'EDIT') {
      handleKeyDownRef = handleKeyDown
      window.addEventListener('keydown', handleKeyDownRef, { capture: true })
    } else {
      handleKeyDownRef = null
    }
  }
  
  // 监听节点变化，更新渲染
  watch([routeNodes, selectedNodeIndex, industryModeRef, defaultSpiralLenRef], () => {
    // 确保所有节点都有radius属性
    ensureNodesHaveRadius()
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
      
      // 移除图层
      if (controlLayer.value) map.value.removeLayer(controlLayer.value)
      if (lineLayer.value) map.value.removeLayer(lineLayer.value)
      if (spiralLayer.value) map.value.removeLayer(spiralLayer.value)
      if (arcLayer.value) map.value.removeLayer(arcLayer.value)
      if (pointLayer.value) map.value.removeLayer(pointLayer.value)
    }
    if (handleKeyDownRef) {
      window.removeEventListener('keydown', handleKeyDownRef, { capture: true })
    }
    
    // 清空图层引用
    controlLayer.value = null
    lineLayer.value = null
    spiralLayer.value = null
    arcLayer.value = null
    pointLayer.value = null
  }
  
  return {
    routeNodes,
    selectedNodeIndex,
    init,
    cleanup,
    updateRouteRender
  }
}
