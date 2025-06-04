# DXF Vector Tile 样式配置系统

基于 Martin Vector Tile 服务的 DXF 图层样式配置和应用系统。

## 📁 文件结构

```
frontend/src/
├── config/
│   ├── dxfLayerStyles.json          # DXF图层样式配置文件
│   ├── martinConfig.js              # Martin服务配置
│   └── README_DXF_STYLES.md         # 本文档
├── utils/
│   └── dxfLayerStyleUtils.js        # 样式工具函数
├── components/
│   └── MartinVectorMap.vue          # Vue地图组件
├── examples/
│   └── leafletVectorTileExample.js  # Leaflet集成示例
└── public/
    └── martin-vector-demo.html      # 独立HTML演示页面
```

## 🚀 快速开始

### 1. 数据库表结构

确保您的 PostGIS 表包含以下字段：

```sql
CREATE TABLE IF NOT EXISTS public.vector_05492e03 (
    gid integer NOT NULL DEFAULT nextval('vector_05492e03_gid_seq'::regclass),
    layer character varying,          -- 重要：DXF图层名称字段
    paperspace boolean,
    subclasses character varying,
    linetype character varying,
    entityhandle character varying,
    text character varying,
    rawcodevalues character varying[],
    geom geometry(Geometry,3857),
    CONSTRAINT vector_05492e03_pkey PRIMARY KEY (gid)
);
```

### 2. Martin 服务配置

启动 Martin 服务，确保它能访问您的 PostGIS 数据库：

```bash
# martin配置示例
martin --config martin_config.yaml
```

martin_config.yaml 示例：
```yaml
pg:
  connection_string: "postgresql://user:password@localhost/database"
  
auto_publish:
  tables:
    - public.vector_05492e03

listen_addresses: "0.0.0.0:3000"
```

### 3. 使用方式

#### 方式一：Vue 组件

```vue
<template>
  <MartinVectorMap 
    :martin-url="'http://localhost:3000'"
    :table-name="'vector_05492e03'"
    :center="[39.9042, 116.4074]"
    :zoom="13"
    @service-error="handleServiceError"
  />
</template>

<script>
import MartinVectorMap from '@/components/MartinVectorMap.vue'

export default {
  components: {
    MartinVectorMap
  },
  methods: {
    handleServiceError(error) {
      console.error('Martin服务错误:', error)
    }
  }
}
</script>
```

#### 方式二：纯 JavaScript

```javascript
import { 
  getAllLayerStyles, 
  createUniversalStyleFunction 
} from '@/utils/dxfLayerStyleUtils'
import { getMartinTileUrl } from '@/config/martinConfig'

// 创建地图
const map = L.map('map').setView([39.9042, 116.4074], 13)

// 添加底图
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)

// 创建Martin vector tile图层
const tileUrl = getMartinTileUrl('vector_05492e03', 'http://localhost:3000')
const styleFunction = createUniversalStyleFunction(getAllLayerStyles(), 'layer')

const vectorLayer = L.vectorGrid.protobuf(tileUrl, {
  vectorTileLayerStyles: styleFunction,
  interactive: true
})

vectorLayer.addTo(map)
```

#### 方式三：独立 HTML 页面

直接访问 `frontend/public/martin-vector-demo.html`，这是一个完整的独立演示页面。

## 🎨 图层样式配置

### 支持的图层类型

| 图层代码 | 中文名称 | 样式特色 | 应用场景 |
|---------|---------|---------|---------|
| DMTZ | 地貌图层 | 棕色/土色系 | 地形特征表示 |
| SXSS | 水系设施 | 蓝色系 | 河流、湖泊等水体 |
| DLSS | 道路设施 | 深灰色，粗线条 | 道路网络 |
| ASSIST | 骨架线 | 虚线，低透明度 | 辅助参考线 |
| DLDW | 独立地物 | 紫色系 | 建筑、构筑物 |
| KZD | 控制点 | 红色，高亮显示 | 测量控制点 |
| ZBTZ | 植被图层 | 绿色系 | 植被覆盖 |
| DGX | 等高线 | 灰色，虚线 | 地形等高线 |
| GCD | 高程点 | 灰色点 | 高程标注点 |
| GXYZ | 管线设施 | 紫色，虚线 | 地下管线 |
| JJ | 境界线 | 黑色，粗线 | 行政边界 |
| JMD | 居民地 | 橙色系 | 居住区域 |
| JZD | 界址点 | 深红色点 | 地籍界址点 |
| TK | 图廓 | 黑色，粗边框 | 地图边框 |
| jqx | 5米等高线 | 中灰色，细虚线 | 5米间距等高线 |
| sqx | 1米等高线 | 浅灰色，极细虚线 | 1米间距等高线 |

### 动态样式特性

- **缩放自适应**：根据地图缩放级别自动调整线宽和透明度
- **图层分级**：不同重要性的图层在不同缩放级别显示
- **性能优化**：小比例尺时自动隐藏细节图层（如1米等高线）

### 自定义样式

修改 `frontend/src/config/dxfLayerStyles.json` 文件：

```json
{
  "vectorTileLayerStyles": {
    "YOUR_LAYER": {
      "weight": 2,
      "color": "#your-color",
      "opacity": 0.8,
      "fillColor": "#your-fill-color",
      "fill": true,
      "fillOpacity": 0.4,
      "radius": 5
    }
  }
}
```

## 🔧 配置选项

### Martin 配置

修改 `frontend/src/config/martinConfig.js`：

```javascript
export const martinConfig = {
  baseUrl: 'http://your-martin-server:3000',
  tables: {
    'your_table_name': {
      name: '您的表显示名称',
      layerField: 'layer',  // 图层字段名
      geometryField: 'geom',
      srid: 3857
    }
  }
}
```

### 地图配置

```javascript
const mapOptions = {
  center: [纬度, 经度],
  zoom: 13,
  minZoom: 8,
  maxZoom: 20
}
```

## 🛠️ 工具函数

### 样式管理

```javascript
import { 
  getLayerStyle,           // 获取指定图层样式
  getAllLayerStyles,       // 获取所有图层样式
  getDynamicLayerStyle,    // 获取动态调整的样式
  getLayerGroups          // 获取图层分组信息
} from '@/utils/dxfLayerStyleUtils'
```

### Martin 服务

```javascript
import { 
  getMartinTileUrl,        // 获取tile URL
  checkMartinService,      // 检查服务状态
  getMartinCatalog        // 获取数据目录
} from '@/config/martinConfig'
```

## 🔍 调试指南

### 1. 检查 Martin 服务

```bash
# 检查服务状态
curl http://localhost:3000/catalog

# 检查特定表
curl http://localhost:3000/vector_05492e03.json
```

### 2. 图层不显示问题

1. **检查数据库连接**：确保 Martin 能访问 PostGIS
2. **检查图层字段**：确保 `layer` 字段包含正确的图层名称
3. **检查样式配置**：确保样式配置中的图层名称与数据匹配
4. **检查缩放级别**：某些图层在特定缩放级别可能被隐藏

### 3. 样式不生效问题

1. **检查字段映射**：确保 `layerField` 配置正确
2. **检查样式函数**：在浏览器控制台查看样式函数返回值
3. **清除缓存**：Vector tile 可能被浏览器缓存

## 📊 性能优化

### 1. 数据库优化

```sql
-- 为layer字段创建索引
CREATE INDEX idx_vector_layer ON public.vector_05492e03(layer);

-- 为几何字段创建空间索引
CREATE INDEX idx_vector_geom ON public.vector_05492e03 USING GIST(geom);
```

### 2. Martin 配置优化

```yaml
# martin_config.yaml
cache_size_mb: 512
max_feature_count: 1000
```

### 3. 前端优化

- 合理设置缩放级别范围
- 使用图层分组管理
- 实现按需加载

## 🔗 相关链接

- [Martin Vector Tile Server](https://github.com/maplibre/martin)
- [Leaflet VectorGrid 插件](https://github.com/Leaflet/Leaflet.VectorGrid)
- [参考博客文章](https://blog.csdn.net/weixin_40184249/article/details/86374647)

## 📄 许可证

本配置系统遵循项目主许可证。 