# 设置当前图层功能详细说明

## 问题背景

在Leaflet地图中，当使用Canvas渲染方式加载多个图层时（如MVT瓦片图层、WMS图层等），存在一个重要的技术限制：**只有z-index最高（最顶层）的Canvas图层能够响应鼠标事件**。

这导致的问题是：
- 当多个图层叠加时，只有置顶的图层能响应鼠标悬停、点击等交互事件
- 用户无法直接与被覆盖的底层图层进行交互
- 属性弹窗等功能只能在最顶层图层上正常工作

## 技术原理

### Canvas渲染的z-index问题

Leaflet使用以下默认的Pane层级：
```css
.leaflet-map-pane canvas { z-index: 100; }
.leaflet-tile-pane { z-index: 200; }
.leaflet-map-pane svg { z-index: 200; }
.leaflet-overlay-pane { z-index: 400; }
.leaflet-shadow-pane { z-index: 500; }
.leaflet-marker-pane { z-index: 600; }
.leaflet-tooltip-pane { z-index: 650; }
.leaflet-popup-pane { z-index: 700; }
```

当多个Canvas图层都在同一个Pane中时，后添加的图层会覆盖先添加的图层，导致只有顶层图层能响应鼠标事件。

### 解决方案

我们的解决方案是实现一个"当前活动图层"机制：

1. **Pane动态管理**：将需要交互的图层移动到高z-index的Pane（如overlayPane）
2. **事件控制**：禁用非活动图层的鼠标事件响应
3. **视觉反馈**：为用户提供清晰的当前活动图层指示

## 实现逻辑

### 1. 核心置顶函数

```javascript
const bringLayerToTopInternal = (layer) => {
  try {
    // 1. 禁用所有图层的鼠标事件响应
    Object.values(mvtLayers.value).forEach(mvtLayer => {
      mvtLayer._popupEnabled = false
      // 降低其他图层的z-index，使用较低层级的pane
      if (mvtLayer.options && mvtLayer.options.pane !== 'tilePane') {
        mvtLayer.options.pane = 'tilePane' // 降到瓦片层级别
      }
    })
    
    Object.values(mapLayers.value).forEach(wmsLayer => {
      if (wmsLayer.options && wmsLayer.options.pane !== 'tilePane') {
        wmsLayer.options.pane = 'tilePane' // 降到瓦片层级别
      }
    })
    
    // 2. 关闭当前弹窗
    if (map.value) {
      map.value.closePopup()
    }
    
    // 3. 将目标图层置顶并启用事件
    if (layer.service_type === 'martin') {
      const mvtLayer = mvtLayers.value[layer.id]
      if (mvtLayer && map.value) {
        // 重新添加到地图以置顶（先移除再添加）
        if (map.value.hasLayer(mvtLayer)) {
          map.value.removeLayer(mvtLayer)
        }
        
        // 设置为最高级别的pane，确保能响应鼠标事件
        mvtLayer.options.pane = 'overlayPane' // 使用最高层级的overlayPane
        mvtLayer.addTo(map.value)
        
        // 只启用这个图层的弹窗
        mvtLayer._popupEnabled = true
      }
    } else if (layer.service_type === 'geoserver') {
      const wmsLayer = mapLayers.value[layer.id]
      if (wmsLayer && map.value) {
        // 重新添加到地图以置顶
        if (map.value.hasLayer(wmsLayer)) {
          map.value.removeLayer(wmsLayer)
        }
        
        // 设置为最高级别的pane
        if (wmsLayer.options) {
          wmsLayer.options.pane = 'overlayPane'
        }
        wmsLayer.addTo(map.value)
      }
    }
    
    // 4. 提供用户反馈
    ElMessage.success({
      message: `图层"${layer.layer_name}"已置顶，现在可以响应鼠标交互事件`,
      duration: 2000
    })
    
  } catch (error) {
    console.error('图层置顶失败:', error)
    ElMessage.error('图层置顶失败')
  }
}
```

### 2. 状态管理

```javascript
// 获取当前活动图层信息
const getCurrentLayerInfo = () => {
  if (!currentActiveLayer.value) {
    return {
      hasActiveLayer: false,
      message: '当前没有活动图层'
    }
  }
  
  const layer = currentActiveLayer.value
  let layerInstance = null
  let paneInfo = '未知'
  let eventEnabled = false
  
  if (layer.service_type === 'martin') {
    layerInstance = mvtLayers.value[layer.id]
    if (layerInstance) {
      paneInfo = layerInstance.options?.pane || '未设置'
      eventEnabled = layerInstance._popupEnabled === true
    }
  } else if (layer.service_type === 'geoserver') {
    layerInstance = mapLayers.value[layer.id]
    if (layerInstance) {
      paneInfo = layerInstance.options?.pane || '未设置'
      eventEnabled = true // WMS图层始终可以响应事件
    }
  }
  
  return {
    hasActiveLayer: true,
    layerName: layer.layer_name,
    serviceType: layer.service_type,
    pane: paneInfo,
    eventEnabled,
    canInteract: paneInfo === 'overlayPane' && eventEnabled,
    message: `当前活动图层: ${layer.layer_name} (${layer.service_type})`
  }
}
```

### 3. UI交互

#### 图层列表中的视觉标识
- 当前活动图层会显示特殊的图标和样式
- 带有蓝色边框和脉冲动画效果
- 图层名称使用蓝色字体

#### 左侧控制面板
- 显示当前活动图层的详细信息
- 提供快速重置和查看详情功能
- 当没有活动图层时显示使用提示

## 使用方法

### 1. 设置当前图层
在图层列表中点击任意图层，该图层将自动：
- 被置顶显示
- 启用鼠标交互事件
- 成为当前活动图层

### 2. 查看图层状态
- 在左侧控制面板查看当前活动图层信息
- 图层列表中活动图层有明显的视觉标识
- 控制台会输出详细的诊断信息

### 3. 重置图层
点击"重置图层"按钮可以：
- 清除所有图层的活动状态
- 将所有图层回到默认层级
- 禁用所有图层的鼠标事件

## 技术优势

1. **解决核心问题**：完美解决Canvas图层鼠标事件响应问题
2. **用户友好**：提供直观的视觉反馈和操作方式
3. **性能优化**：避免同时启用多个图层的事件处理
4. **可扩展性**：支持Martin MVT和GeoServer WMS等多种服务类型
5. **调试友好**：提供详细的状态诊断功能

## 相关技术参考

- [Leaflet Panes 文档](https://leafletjs.com/reference.html#map-pane)
- [GitHub项目：OverlappingGeoJSON_Panes_Template](https://github.com/DanFinelli/OverlappingGeoJSON_Panes_Template)
- [Leaflet事件转发机制](https://gist.github.com/perliedman/84ce01954a1a43252d1b917ec925b3dd)

## 注意事项

1. **性能考虑**：频繁切换活动图层可能影响性能，建议用户根据需要进行切换
2. **事件冲突**：确保同一时间只有一个图层处于活动状态
3. **兼容性**：该方案适用于Leaflet 1.x版本，其他版本可能需要调整
4. **浏览器支持**：需要现代浏览器支持Canvas和CSS3特性 