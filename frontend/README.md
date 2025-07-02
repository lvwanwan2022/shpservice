# Frontend README

本文件详细介绍了前端应用程序的结构、功能、技术栈和核心实现，旨在帮助开发人员理解和维护代码，并在必要时能够基于此文档重建项目。

## 1. 项目概述

本项目是一个基于 Vue.js 的地理信息展示和管理平台。用户可以上传多种格式的地理空间数据，将其发布为标准的地图服务，并在交互式地图上进行可视化和分析。

## 2. 主要页面及功能

### 2.1. 路由结构

通过 `vue-router` 管理，主要页面如下：

-   `/#/`: **首页 (`Home.vue`)** - 项目的入口页面。
-   `/#/upload`: **数据管理页 (`UploadView.vue`)** - 核心的数据上传和管理模块。
-   `/#/map`: **地图页 (Leaflet) (`MapView.vue`)** - 基于 Leaflet 的二维地图浏览页面。
-   `/#/map-ol`: **地图页 (OpenLayers) (`MapViewOL.vue`)** - 基于 OpenLayers 的二维地图浏览页面，功能更完善。
-   `/#/scene`: **三维场景页 (`SceneView.vue`)** - 用于展示三维模型的页面。

### 2.2. 页面核心功能

-   **`UploadView.vue`**:
    -   **文件上传**: 支持上传多种格式的地理数据文件，如 `SHP`, `GeoJSON`, `DXF`, `DWG`, `DEM`, `DOM` 等。
    -   **数据管理**: 以列表形式展示已上传的文件，包含元数据（文件名、大小、上传者、专业、标签等）。
    -   **服务发布**:
        -   **GeoServer 服务**: 可将支持的文件（如 SHP, GeoJSON）发布为 `WMS` 和 `WFS` 服务。
        -   **Martin 服务**: 可将 `GeoJSON`, `SHP`, `DXF` 等文件发布为 `MVT` (Mapbox Vector Tiles) 矢量切片服务。
    -   **坐标系管理**: 允许用户为上传的数据指定坐标系（如 `EPSG:4326`）。

-   **`MapView.vue` / `MapViewOL.vue`**:
    -   **双地图引擎**: 项目并行实现了两套地图浏览器，分别基于 `Leaflet` 和 `OpenLayers`，开发者可根据需求选择或扩展。
    -   **场景管理**: "场景"是图层的集合。用户可以创建、切换和管理不同的场景，每个场景包含一组特定的地图图层。
    -   **图层管理**: 在地图页面，用户可以从已发布的服务中选择图层，将其添加到当前场景中，并控制图层的可见性、顺序和样式。

## 3. 技术栈

-   **核心框架**: Vue 3 (主要使用 Composition API)
-   **UI 组件库**: Element Plus
-   **地图库**:
    -   OpenLayers (`ol`)
    -   Leaflet
-   **状态管理**: Vuex (用于存储全局状态，如用户信息)
-   **坐标转换**: `proj4` (与 OpenLayers 结合，用于处理非标准投影)
-   **打包工具**: Vite

## 4. 地图功能与数据加载

### 4.1. 技术路线

项目提供了两种主流的WebGIS开源库作为地图渲染引擎：

1.  **OpenLayers (`MapViewOL.vue` & `MapViewerOL.vue`)**:
    -   **优势**: 功能强大，扩展性好，支持广泛的地理数据格式和标准，特别适合需要复杂交互和自定义功能的专业GIS应用。本项目中，OpenLayers 路线的功能实现更为完整。
    -   **实现**: `MapViewOL.vue` 作为容器页，负责UI和场景管理；`MapViewerOL.vue` 是核心地图组件，封装了所有与 OpenLayers 地图交互的逻辑。

2.  **Leaflet (`MapView.vue` & `MapViewer.vue`)**:
    -   **优势**: 轻量、简洁，API易于上手，性能优秀，适合构建快速、移动端友好的地图应用。
    -   **实现**: 结构与 OpenLayers 类似，`MapView.vue` 为容器，`MapViewer.vue` 为核心组件。

### 4.2. 加载各种类型数据的方法

数据加载遵循 "先发布，后加载" 的模式。数据在 `UploadView` 中被发布成服务后，在地图页面进行消费。

-   **加载 GeoServer WMS 服务**:
    -   在 `MapViewerOL.vue` 中，通过创建 `ol/layer/Tile` 和 `ol/source/TileWMS` 来加载。
    -   **核心逻辑**:
        -   后端 API (`gisApi.getLayerCRSInfo`) 会返回图层正确的坐标系（如 `EPSG:2379`）。
        -   前端根据坐标系信息动态设置 WMS 请求参数（`SRS` 或 `CRS`），确保地图客户端能以正确的投影请求和渲染地图。
    -   **对应代码**: `addGeoServerLayer` 方法。

-   **加载 Martin MVT 服务**:
    -   在 `MapViewerOL.vue` 中，通过创建 `ol/layer/VectorTile` 和 `ol/source/VectorTile` (使用 `MVT` 格式) 来加载矢量切片。
    -   **优势**: 矢量切片将矢量数据预处理为瓦片，传输数据量小，客户端渲染性能高，交互体验好。
    -   **对应代码**: `addMartinLayer` 方法。

-   **加载其他矢量数据 (如 GeoJSON)**:
    -   虽然当前主要通过 Martin 服务加载，但 OpenLayers 和 Leaflet 本身也支持直接加载 GeoJSON 文件。在此项目中，推荐将 GeoJSON 文件发布为 Martin 服务以获得更佳性能。

### 4.3. 代码示例

以下是在 OpenLayers 和 Leaflet 中加载不同数据服务的代码样例。

#### 4.3.1. OpenLayers 示例

**加载 GeoServer WMS 服务**

```javascript
import TileLayer from 'ol/layer/Tile';
import { TileWMS } from 'ol/source';

// GeoServer WMS 服务地址
const wmsUrl = 'http://localhost:8080/geoserver/shpservice/wms';

// 创建 WMS 图层
const wmsLayer = new TileLayer({
  source: new TileWMS({
    url: wmsUrl,
    params: {
      'LAYERS': 'shpservice:your_layer_name', // GeoServer中的图层名
      'TILED': true,
      'VERSION': '1.1.1',
      'FORMAT': 'image/png',
      'TRANSPARENT': true
    },
    serverType: 'geoserver',
    transition: 0,
  }),
  // 可以设置图层的透明度
  opacity: 0.8,
});

// 将图层添加到 map 对象
map.addLayer(wmsLayer);
```

**加载 Martin MVT 服务 (带样式)**

```javascript
import VectorTileLayer from 'ol/layer/VectorTile';
import { VectorTile } from 'ol/source';
import { MVT } from 'ol/format';
import { Style, Stroke, Fill, Circle } from 'ol/style';

// Martin MVT 服务地址模板
const mvtUrl = 'http://localhost:3000/vector_table_name/{z}/{x}/{y}';

// 定义样式函数
// 在本项目中，这是一个非常复杂的函数，它会根据要素的 `cad_layer` 属性
// 和从后端获取的样式配置来动态返回样式。
// 以下是一个简化的示例，为不同几何类型设置固定样式。
const styleFunction = (feature) => {
  const geometryType = feature.getGeometry().getType();
  
  switch (geometryType) {
    case 'Point':
    case 'MultiPoint':
      return new Style({
        image: new Circle({
          radius: 5,
          fill: new Fill({ color: 'red' }),
          stroke: new Stroke({ color: 'white', width: 1 }),
        }),
      });
    case 'LineString':
    case 'MultiLineString':
      return new Style({
        stroke: new Stroke({
          color: 'blue',
          width: 2,
        }),
      });
    case 'Polygon':
    case 'MultiPolygon':
      return new Style({
        fill: new Fill({ color: 'rgba(0, 255, 0, 0.4)' }),
        stroke: new Stroke({
          color: 'green',
          width: 1,
        }),
      });
    default:
      return null;
  }
};

// 创建 MVT 图层
const mvtLayer = new VectorTileLayer({
  declutter: true,
  source: new VectorTile({
    format: new MVT(),
    url: mvtUrl,
  }),
  // 应用样式函数
  style: styleFunction,
});

// 将图层添加到 map 对象
map.addLayer(mvtLayer);
```

#### 4.3.2. Leaflet 示例

**加载 GeoServer WMS 服务**

```javascript
import L from 'leaflet';

// GeoServer WMS 服务地址
const wmsUrl = 'http://localhost:8080/geoserver/shpservice/wms';

// 创建 WMS 图层
const wmsLayer = L.tileLayer.wms(wmsUrl, {
  layers: 'shpservice:your_layer_name', // GeoServer中的图层名
  format: 'image/png',
  transparent: true,
  version: '1.1.1',
  // 可以设置图层的透明度
  opacity: 0.8,
});

// 将图层添加到 map 对象
wmsLayer.addTo(map);
```

**加载 Martin MVT 服务 (带样式)**

```javascript
import L from 'leaflet';
import 'leaflet.vectorgrid'; // 确保已安装和导入

// Martin MVT 服务地址
// 注意: Leaflet.VectorGrid 通常需要 TileJSON 或直接的 URL 模板
const mvtUrl = 'http://localhost:3000/vector_table_name/{z}/{x}/{y}';

// 定义矢量切片样式
// 样式可以是一个对象，也可以是一个函数，以实现数据驱动的样式
const vectorTileOptions = {
  rendererFactory: L.canvas.tile,
  // 样式函数，`properties` 是要素的属性, `zoom` 是当前缩放级别
  vectorTileLayerStyles: {
    // `vector_table_name` 对应 MVT 中的图层名（通常是表名）
    vector_table_name: (properties, zoom) => {
      // 在本项目的实际逻辑中，这里会根据 properties.cad_layer 
      // 和从后端获取的样式配置来返回不同的样式。
      // 以下是一个简化的示例。
      const geometryType = properties.geom_type; // 假设属性中包含几何类型
      
      switch (geometryType) {
        case 'Point':
          return {
            fillColor: 'red',
            fill: true,
            radius: 5,
            color: 'white',
            weight: 1,
          };
        case 'LineString':
          return {
            color: 'blue',
            weight: 2,
          };
        case 'Polygon':
          return {
            fillColor: 'rgba(0, 255, 0, 0.4)',
            fill: true,
            stroke: true,
            color: 'green',
            weight: 1,
          };
      }
    }
  }
};

// 使用 L.vectorGrid.protobuf 创建 MVT 图层
const mvtLayer = L.vectorGrid.protobuf(mvtUrl, vectorTileOptions);

// 将图层添加到 map 对象
mvtLayer.addTo(map);
```

## 5. 核心逻辑：地图样式设置

地图样式的灵活性和动态性是本项目的核心特点之一，尤其是在 OpenLayers 实现中。

### 5.1. 样式设置入口

在 `MapViewOL.vue` 的图层列表中，每个图层卡片都有一个 "样式设置" 按钮，点击后会弹出样式设置对话框 (`styleDialogVisible`)。

### 5.2. 样式逻辑详解

样式的核心逻辑位于 `MapViewerOL.vue` 组件内。

-   **WMS 栅格图层**: 样式相对简单，主要由 GeoServer 控制。前端仅提供**透明度 (`opacity`)** 调整功能。

-   **MVT 矢量图层 (核心)**:
    -   样式设置是**数据驱动 (Data-Driven Styling)** 的，这意味着要素的显示样式取决于其自身的属性。
    -   核心实现位于 `addMartinLayer` 方法内的 `createStyleFunction` 样式函数中。此函数在渲染每个要素时被调用。

    -   **样式策略**:
        1.  **DXF 文件的特殊处理**:
            -   **背景**: DXF 文件内部包含多个图层（例如，`contour`, `building`, `annotation`）。在发布为 MVT 服务时，这些原始的图层名被保存在每个要素的 `cad_layer` 属性中。
            -   **动态样式**: `createStyleFunction` 会读取每个要素的 `cad_layer` 属性值。
            -   **样式匹配**: 它会根据 `cad_layer` 的值去查找对应的样式配置。样式来源有两个：
                -   **用户自定义样式**: 用户可以通过 `DxfStyleEditor.vue` 组件为每个 `cad_layer` 设置详细的样式（颜色、线宽、可见性等）。这些配置通过 API (`gisApi.updateMartinLayerStyles`) 保存在后端的数据库中，并在加载时获取。
                -   **默认样式**: 如果用户没有定义样式，则会从一个静态的 JSON 文件 (`@/config/defaultDxfStyles.json`) 中读取默认样式作为后备。
            -   **可见性控制**: `DxfStyleEditor.vue` 允许用户设置每个内部图层的可见性，不可见的图层会通过返回一个空样式 (`new Style({})`) 来实现隐藏。

        2.  **通用矢量文件 (SHP, GeoJSON)**:
            -   对于非 DXF 的矢量图层，应用较为简单的基础样式。
            -   样式对话框 (`styleDialogVisible`) 提供基础的点、线、面样式编辑器，允许用户修改颜色、大小、宽度和透明度等。
            -   这些修改后的样式直接应用于图层上。

    -   **性能优化**:
        -   为了避免在渲染每个要素时都重新创建样式对象，代码中使用了 `styleCache`。对于相同类型和图层的要素，其样式对象会被缓存和复用，显著提高了渲染性能。

### 5.3. 核心方法摘要

-   **`MapViewerOL.vue` -> `showStyleDialog(layer)`**:
    -   打开样式对话框的入口方法。

-   **`MapViewerOL.vue` -> `addMartinLayer(layer)`**:
    -   创建 MVT 图层的核心方法。
    -   内部定义并使用了 `createStyleFunction`。

-   **`MapViewerOL.vue` -> `createStyleFunction`**:
    -   **最核心的样式函数**。实现了数据驱动的样式逻辑，处理 DXF 和通用矢量要素的样式匹配与应用。

-   **`MapViewerOL.vue` -> `applyAndSaveDxfStyles()`**:
    -   当用户在 `DxfStyleEditor` 中保存样式时被调用，负责将样式配置通过 API 发送到后端进行持久化存储。

-   **`MapViewerOL.vue` -> `initializeProjections()`**:
    -   在地图初始化时调用，通过 API 从后端获取 `proj4` 坐标系定义，并注册到 OpenLayers 中，使得地图能够支持和正确转换各种非标准的地理坐标系。这是确保从不同数据源获取的 WMS 服务能正确叠加的关键。
### 5.4. openlayers加载高德底图纠偏方法
-   **`坐标转换文件`**
    :\frontend\src\utils\GCJ02.js
    // 高德地图 - 使用GCJ02坐标系修正偏移
        const gaodeLayer = new TileLayer({
          source: new XYZ({
            url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            crossOrigin: 'anonymous',
            projection:  gcj02Mecator // 使用GCJ02坐标系
          }),
          visible: true
        })
        
        // 高德卫星地图 - 使用GCJ02坐标系修正偏移
        const gaodeSatelliteLayer = new TileLayer({
          source: new XYZ({
            url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
            crossOrigin: 'anonymous',
            projection: gcj02Mecator // 使用GCJ02坐标系
          }),
          visible: false
        })

## 6.openlayers从IndexDB加载缓存
https://openlayers.org/en/latest/apidoc/module-ol_source_XYZ-XYZ.html#tileLoadFunction