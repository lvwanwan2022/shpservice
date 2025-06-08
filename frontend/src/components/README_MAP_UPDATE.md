# OpenLayers 地图底图更新说明

## 更新内容

本次更新对 OpenLayers 地图浏览页的底图配置进行了以下修改：

### 🔄 底图变更
- **移除**: 天地图、百度地图
- **保留**: 高德地图
- **新增**: 高德卫星地图、OpenStreetMap、Esri世界影像

### 📁 修改的文件

#### 1. `frontend/src/components/MapViewerOL.vue`
- 更新底图图层配置
- 新增高德卫星地图、OpenStreetMap和Esri世界影像图层
- 移除天地图和百度地图图层
- 更新 `map.baseLayers` 引用

#### 2. `frontend/src/components/BaseMapSwitcherOL.vue`
- 更新底图切换器选项
- 新增"高德卫星图"、"OpenStreetMap"和"Esri世界影像"选项
- 移除"天地图"和"百度地图"选项
- 更新切换逻辑

#### 3. `frontend/src/utils/mapServices.js`
- 新增OpenStreetMap和Esri世界影像地图服务配置
- 移除百度地图服务配置
- 更新服务优先级列表

#### 4. `frontend/src/examples/wms_openlayers_demo.html`
- 同步更新演示页面的底图配置
- 保持与主地图组件的一致性

### 🗺️ 新的底图配置

#### 高德地图（普通）
```javascript
url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
```

#### 高德卫星地图
```javascript
url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
```

#### OpenStreetMap
```javascript
url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
```

#### Esri 世界影像
```javascript
url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
```

### 🎯 使用方法

用户现在可以通过右上角的底图切换器在以下四种底图之间切换：
1. **高德地图** - 标准矢量地图（默认）
2. **高德卫星图** - 卫星影像地图（国内）
3. **OpenStreetMap** - 开源矢量地图
4. **Esri世界影像** - 全球高清卫星影像

### ⚠️ 注意事项

1. **坐标系兼容性**: 所有底图都使用Web墨卡托投影（EPSG:3857），与OpenLayers默认配置兼容
2. **服务稳定性**: 高德地图服务相对稳定，OpenStreetMap和Esri作为备选方案
3. **加载性能**: 卫星地图瓦片较大，加载可能稍慢；海外服务器可能在国内访问稍慢
4. **跨域配置**: 所有服务已配置 `crossOrigin: 'anonymous'`
5. **开源优势**: OpenStreetMap完全开源免费，Esri世界影像提供高质量全球卫星图像
6. **影像质量**: Esri世界影像提供高分辨率卫星图像，适合详细查看地物

### 🔧 技术细节

- 使用OpenLayers的 `TileLayer` + `XYZ` 源
- 支持动态切换，无需刷新页面
- 保持图层状态和用户交互不变
- 向下兼容现有的图层加载逻辑
- 所有底图支持最高19级缩放，适合大比例尺查看
- Esri世界影像使用标准的ArcGIS REST服务

---

*更新时间: 2024年6月*
*影响范围: OpenLayers地图浏览器组件* 