# Martin矢量图层样式问题修复总结

## 问题描述

1. **Martin矢量图层样式对话框问题**：每次点击弹出的dialog中点样式、线样式和面样式没有从后端获取该图层的样式，每次点击弹出的都不是数据库中保存的样式。

2. **Martin图层初始化样式问题**：Martin矢量图层（shp和geojson）初始化的样式也不正确显示，显示的都是默认样式。

3. **GeoServer WMS图层点样式问题**：geoserver加载矢量图层，使用wms加载方法，修改点样式（比如修改颜色），点击应用，点图层就看不到了，但是线图层和面图层都是正确的。

## 修复内容

### 1. 修复样式对话框初始化问题

**文件**: `simple_frontend/src/components/MapViewerOL.vue`

**修改位置**: `showStyleDialog` 方法

**修复内容**:
- 在打开样式对话框时，从后端获取保存的样式配置，而不是使用硬编码的默认值
- 添加了详细的调试日志，帮助诊断样式获取问题
- 正确处理Martin服务和普通图层的样式获取逻辑

**关键代码**:
```javascript
// 从后端获取保存的样式配置
try {
  let savedStyleConfig = null
  
  if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
    // 获取Martin服务样式
    const response = await gisApi.getMartinServiceStyle(currentStyleLayer.value.martin_service_id)
    if (response?.success && response.data?.style_config) {
      savedStyleConfig = response.data.style_config
    }
  } else {
    // 获取普通图层样式
    const response = await gisApi.getLayerStyle(currentStyleLayer.value.id)
    if (response?.success && response.data?.style_config) {
      savedStyleConfig = response.data.style_config
    }
  }
  
  // 如果有保存的样式配置，使用它；否则使用默认值
  if (savedStyleConfig) {
    // 更新样式表单
    styleForm.point = { 
      color: savedStyleConfig.point.color || '#FF0000', 
      size: savedStyleConfig.point.size || 6 
    }
    // ... 其他样式更新
  }
} catch (error) {
  console.error('❌ 获取样式配置失败:', error)
}
```

### 2. 修复图层初始化样式问题

**文件**: `simple_frontend/src/components/MapViewerOL.vue`

**修改位置**: `addMartinLayer` 方法

**修复内容**:
- 在图层初始化时，如果缓存中没有样式配置，尝试从后端获取
- 确保Martin图层在加载时使用正确的样式配置

**关键代码**:
```javascript
let layerStyleConfig = layerStyleCache[layer.id] || {}

// 如果缓存中没有样式配置，尝试从后端获取
if (Object.keys(layerStyleConfig).length === 0) {
  try {
    console.log('🔄 从后端获取图层样式配置...')
    let savedStyleConfig = null
    
    if (layer.service_type === 'martin' && layer.martin_service_id) {
      // 获取Martin服务样式
      const response = await gisApi.getMartinServiceStyle(layer.martin_service_id)
      if (response?.success && response.data?.style_config) {
        savedStyleConfig = response.data.style_config
      }
    } else {
      // 获取普通图层样式
      const response = await gisApi.getLayerStyle(layer.id)
      if (response?.success && response.data?.style_config) {
        savedStyleConfig = response.data.style_config
      }
    }
    
    if (savedStyleConfig) {
      layerStyleConfig = savedStyleConfig
      // 将样式配置保存到缓存中
      layerStyleCache[layer.id] = savedStyleConfig
    }
  } catch (error) {
    console.error('❌ 获取样式配置失败:', error)
  }
}
```

### 3. 修复GeoServer WMS图层点样式问题

**文件**: `simple_frontend/src/components/MapViewerOL.vue`

**修改位置**: `applyStyle` 方法

**修复内容**:
- 对于GeoServer WMS图层，检测是否修改了点样式
- 如果修改了点样式，需要重新加载图层（因为WMS不支持动态点样式）
- 如果只修改了透明度等参数，可以直接更新WMS参数

**关键代码**:
```javascript
// 对于GeoServer WMS图层，需要特殊处理
if (currentStyleLayer.value.service_type === 'geoserver') {
  const wmsLayer = mapLayers.value[currentStyleLayer.value.id]
  if (wmsLayer) {
    // 获取WMS源
    const wmsSource = wmsLayer.getSource()
    if (wmsSource) {
      // 检查是否修改了点样式（这需要SLD支持）
      const hasPointStyleChanges = styleConfig.point && (
        styleConfig.point.color !== undefined || 
        styleConfig.point.size !== undefined
      )
      
      if (hasPointStyleChanges) {
        // 点样式修改需要重新加载图层，因为WMS不支持动态点样式
        console.log('⚠️ 检测到点样式修改，需要重新加载WMS图层')
        map.value.removeLayer(wmsLayer)
        delete mapLayers.value[currentStyleLayer.value.id]
        await addGeoServerLayer(currentStyleLayer.value)
      } else {
        // 其他样式修改（透明度等）可以直接更新
        const currentParams = wmsSource.getParams()
        const newParams = {
          ...currentParams,
          // 添加时间戳参数强制刷新
          '_t': Date.now()
        }
        wmsSource.updateParams(newParams)
        
        // 如果修改了透明度，直接更新图层透明度
        if (styleConfig.raster && styleConfig.raster.opacity !== undefined) {
          wmsLayer.setOpacity(styleConfig.raster.opacity)
        }
      }
    }
  }
}
```

## 测试建议

1. **测试Martin矢量图层样式对话框**:
   - 打开一个Martin矢量图层（shp或geojson）
   - 点击样式设置按钮
   - 验证对话框中的样式值是否是从后端获取的保存值

2. **测试Martin图层初始化样式**:
   - 重新加载页面
   - 添加Martin矢量图层
   - 验证图层是否使用正确的样式显示

3. **测试GeoServer WMS图层点样式**:
   - 打开一个GeoServer WMS图层
   - 修改点样式（颜色或大小）
   - 点击应用，验证图层是否正常显示

## 注意事项

1. **DXF图层样式**：DXF图层的样式处理逻辑保持不变，仍然使用默认的DXF样式配置。

2. **错误处理**：添加了完善的错误处理机制，当样式获取失败时会使用默认值。

3. **调试信息**：添加了详细的调试日志，方便排查问题。

4. **性能优化**：使用样式缓存机制，避免重复获取样式配置。
