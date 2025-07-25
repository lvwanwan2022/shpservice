# GDAL2Tiles Profile 详细说明

## 概述

GDAL2Tiles 支持三种不同的 profile（瓦片方案），每种都有特定的使用场景和坐标系要求。

## Profile 类型

### 1. Mercator Profile (`--profile=mercator`)

**适用坐标系：**
- EPSG:3857 (Web Mercator)
- EPSG:900913 (Google Mercator，旧版本)

**特点：**
- 使用球形墨卡托投影
- 全球覆盖，但高纬度地区变形严重
- 与 Google Maps、OpenStreetMap 等主流 Web 地图服务兼容
- 瓦片坐标系统：TMS (Tile Map Service)

**使用场景：**
- 全球或大区域的地图服务
- 需要与主流 Web 地图叠加显示
- 商业地图应用

**瓦片坐标范围：**
- X: 0 到 2^zoom - 1
- Y: 0 到 2^zoom - 1
- 原点在左上角

### 2. Geodetic Profile (`--profile=geodetic`)

**适用坐标系：**
- EPSG:4326 (WGS84 地理坐标系)
- EPSG:4490 (CGCS2000 地理坐标系)
- EPSG:4214 (北京54 地理坐标系)
- EPSG:4610 (西安80 地理坐标系)

**特点：**
- 使用地理坐标系（经纬度）
- 保持真实的地理形状和比例
- 适合高纬度地区
- 与 Google Earth 兼容

**使用场景：**
- 需要保持真实地理形状的应用
- 高纬度地区的数据
- 科学研究和专业 GIS 应用
- 与 Google Earth 集成

**瓦片坐标范围：**
- 基于实际地理范围计算
- 不固定为正方形网格

### 3. Raster Profile (`--profile=raster`)

**适用坐标系：**
- 任何坐标系
- 保持原始投影

**特点：**
- 保持原始文件的坐标系和投影
- 不进行坐标系转换
- 瓦片基于原始像素坐标
- 适合专业 GIS 应用

**使用场景：**
- 需要保持原始精度的专业应用
- 特定投影的数据（如 UTM、国家坐标系等）
- 科学研究和工程应用
- 数据精度要求高的场景

**瓦片坐标范围：**
- 基于原始文件的像素坐标
- 保持原始投影的坐标系统

## 坐标系转换策略

### 智能坐标系处理逻辑

我们的系统实现了智能坐标系处理，根据以下优先级决定处理策略：

1. **数据库坐标系优先**：如果 files 表中有 coordinate_system 字段，优先使用
2. **文件坐标系**：如果数据库没有，使用文件自身的坐标系
3. **默认坐标系**：如果都没有，使用 EPSG:4326 (WGS84)

### 转换决策矩阵

| 目标坐标系 | Profile | 是否需要转换 | 说明 |
|-----------|---------|-------------|------|
| EPSG:4326 | geodetic | 否 | 直接使用地理坐标系 |
| EPSG:3857 | mercator | 是 | 转换为 Web Mercator |
| EPSG:4490 | geodetic | 否 | 直接使用地理坐标系 |
| EPSG:4214 | geodetic | 否 | 直接使用地理坐标系 |
| EPSG:4610 | geodetic | 否 | 直接使用地理坐标系 |
| 其他坐标系 | raster | 否 | 保持原始投影 |

### 支持的坐标系列表

```python
supported_coordinates = {
    'EPSG:4326': 'geodetic',  # WGS84地理坐标系
    'EPSG:3857': 'mercator',   # Web Mercator投影
    'EPSG:900913': 'mercator', # Google Mercator (旧版本)
    'EPSG:4490': 'geodetic',   # CGCS2000地理坐标系
    'EPSG:4214': 'geodetic',   # 北京54地理坐标系
    'EPSG:4610': 'geodetic',   # 西安80地理坐标系
}
```

## 使用建议

### 1. Web 地图应用
- **推荐 Profile**: mercator
- **目标坐标系**: EPSG:3857
- **原因**: 与主流 Web 地图服务兼容

### 2. 专业 GIS 应用
- **推荐 Profile**: geodetic 或 raster
- **目标坐标系**: 根据数据源确定
- **原因**: 保持数据精度和真实地理形状

### 3. 中国地区应用
- **推荐 Profile**: geodetic
- **目标坐标系**: EPSG:4490 (CGCS2000)
- **原因**: 符合中国测绘标准

### 4. 高精度工程应用
- **推荐 Profile**: raster
- **目标坐标系**: 保持原始坐标系
- **原因**: 避免坐标系转换带来的精度损失

## 性能考虑

### 转换开销
- **mercator**: 需要投影转换，计算开销较大
- **geodetic**: 地理坐标系，转换开销较小
- **raster**: 无坐标系转换，性能最佳

### 存储空间
- **mercator**: 全球覆盖，瓦片数量固定
- **geodetic**: 基于实际范围，瓦片数量可变
- **raster**: 基于原始像素，瓦片数量最少

## 兼容性

### Web 地图库兼容性
- **mercator**: 完全兼容 Leaflet、OpenLayers、Mapbox 等
- **geodetic**: 兼容 OpenLayers，部分兼容其他库
- **raster**: 需要自定义投影支持

### 数据格式兼容性
- **mercator**: 标准 Web 瓦片格式
- **geodetic**: 支持 KML 输出
- **raster**: 自定义瓦片格式

## 总结

选择合适的 Profile 应该基于：
1. **应用场景**：Web 应用 vs 专业 GIS
2. **数据精度要求**：是否需要保持原始精度
3. **兼容性需求**：是否需要与特定地图服务集成
4. **性能要求**：处理速度和存储空间限制

我们的智能坐标系处理系统会自动分析这些因素，选择最合适的 Profile 和坐标系转换策略。 