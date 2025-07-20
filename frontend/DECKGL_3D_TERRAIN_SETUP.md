# Deck.gl 三维地形上二维图层叠加解决方案

## 问题描述

在Deck.gl三维模式下，二维地图（底图和数据图层）无法正确显示在三维地形表面上，导致图层不可见或显示异常。

## 解决方案

使用Deck.gl官方的 **TerrainExtension** 来实现二维图层与三维地形的完美结合。

### 核心概念

根据 [Deck.gl官方文档](https://deck.gl/docs/api-reference/extensions/terrain-extension)，TerrainExtension 可以将2D数据渲染到3D地形表面上。

#### 1. 地形源（Terrain Source）
- 使用 `TerrainLayer` 创建地形基础
- 设置 `operation: 'terrain'` 将其定义为地形源
- 该图层为其他图层提供3D表面，自身设为透明

#### 2. 图层扩展（Layer Extensions）
- 为需要贴合地形的图层添加 `TerrainExtension`
- 设置 `terrainDrawMode: 'drape'` 将图层作为纹理覆盖在地形表面

## 具体实现

### 1. 导入依赖

```javascript
import { _TerrainExtension as TerrainExtension } from '@deck.gl/extensions'
```

### 2. 创建地形基础图层

```javascript
const terrainLayer = new TerrainLayer({
  id: 'terrain-layer',
  elevationData: 'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png',
  texture: null, // 不设置纹理，仅提供高程
  operation: 'terrain', // 🔑 关键：定义为地形源
  elevationDecoder: {
    rScaler: 256,
    gScaler: 1,
    bScaler: 1 / 256,
    offset: -32768
  },
  opacity: 0, // 完全透明，仅提供地形表面
  elevationScale: 2.0
})
```

### 3. 为底图添加TerrainExtension

```javascript
const baseMapLayer = new TileLayer({
  id: 'base-map-3d',
  data: baseMapUrl,
  extensions: [new TerrainExtension()], // 🔑 添加地形扩展
  terrainDrawMode: 'drape', // 🔑 设置为覆盖模式
  // ... 其他配置
})
```

### 4. 为数据图层添加TerrainExtension

```javascript
// MVT矢量图层
const mvtLayer = new MVTLayer({
  id: 'mvt-layer',
  data: mvtUrl,
  extensions: [new TerrainExtension()], // 🔑 添加地形扩展
  terrainDrawMode: 'drape', // 🔑 设置为覆盖模式
  // ... 其他配置
})

// WMS栅格图层
const wmsLayer = new TileLayer({
  id: 'wms-layer',
  extensions: [new TerrainExtension()], // 🔑 添加地形扩展
  terrainDrawMode: 'drape', // 🔑 设置为覆盖模式
  // renderSubLayers中的BitmapLayer也需要添加扩展
  renderSubLayers: props => {
    return new BitmapLayer(props, {
      extensions: [new TerrainExtension()],
      terrainDrawMode: 'drape'
    })
  }
})
```

### 5. 图层顺序

正确的图层顺序：
1. **地形基础图层** (TerrainLayer with operation: 'terrain') - 最底层
2. **底图图层** (TileLayer with TerrainExtension) - 中间层
3. **数据图层** (MVTLayer/WMS with TerrainExtension) - 最上层

## 关键技术点

### terrainDrawMode 模式

- **`drape`**: 将图层作为纹理覆盖在地形表面（推荐用于底图和平面数据）
- **`offset`**: 将对象沿高程方向偏移（适用于3D对象）

### 数据源兼容性

- ✅ **底图瓦片**: OSM、高德、Esri等
- ✅ **MVT矢量瓦片**: Martin服务、MBTiles
- ✅ **WMS栅格**: GeoServer WMS服务
- ✅ **GeoJSON**: 矢量要素数据

### 性能优化

1. 地形基础图层设置为透明 (`opacity: 0`)
2. 合理设置 `elevationScale` 控制地形夸张程度
3. 限制地形图层的 `maxZoom` 以控制性能

## 测试验证

启用三维模式后，应能看到：
1. 🏔️ **地形起伏**: 明显的三维地形效果
2. 🗺️ **底图贴合**: 底图完美贴合地形表面
3. 📊 **数据可见**: MVT/WMS数据图层正确显示在地形上
4. 🎮 **交互正常**: 可以自由旋转、缩放、平移

## 参考资料

- [Deck.gl TerrainExtension官方文档](https://deck.gl/docs/api-reference/extensions/terrain-extension)
- [Deck.gl TerrainLayer示例](https://deck.gl/examples/terrain-layer)
- [GitHub: photorealistic-3d-deckgl](https://github.com/cheeaun/photorealistic-3d-deckgl) 