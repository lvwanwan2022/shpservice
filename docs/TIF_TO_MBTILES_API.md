# TIF转MBTiles并发布Martin服务 API文档

本文档介绍如何使用TIF转MBTiles API将TIF文件转换为MBTiles格式并发布为Martin瓦片服务。

## 🎯 功能概述

该API提供以下功能：
- 将已上传的TIF文件转换为MBTiles格式
- 自动发布为Martin瓦片服务
- 支持批量转换
- 提供转换状态查询
- 支持自定义最大缩放级别（1-25级）

## 📋 前置条件

1. **GDAL工具链**：确保系统已安装GDAL工具
   - `gdal_translate`
   - `gdalwarp`
   - `gdalinfo`
   - `gdal2tiles.py`（可选，如无则使用替代方法）

2. **Martin服务**：确保Martin服务正常运行

3. **文件上传**：TIF文件需要先通过文件上传接口上传到系统

## 🔗 API接口

### 1. 转换单个TIF文件

**接口地址**：`POST /api/tif-martin/convert-and-publish/{file_id}`

**请求参数**：
- `file_id`：已上传TIF文件的ID（路径参数）
- `max_zoom`：最大缩放级别，默认20（请求体参数，可选）

**请求示例**：
```bash
POST /api/tif-martin/convert-and-publish/338963489316016128
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "max_zoom": 18
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "TIF文件成功转换为MBTiles并发布为Martin服务",
  "data": {
    "original_file": {
      "id": "338963489316016128",
      "name": "DOM_sample.tif",
      "type": "dom.tif"
    },
    "conversion": {
      "mbtiles_filename": "a1b2c3d4.mbtiles",
      "max_zoom": 18,
      "tif_info": {
        "width": 8192,
        "height": 6144,
        "band_count": 3,
        "data_type": "Byte"
      },
      "mbtiles_info": {
        "tile_count": 1024,
        "min_zoom": 0,
        "max_zoom": 18,
        "file_size": 52428800
      },
      "stats": {
        "file_size_mb": 50.0,
        "tile_count": 1024,
        "zoom_levels": "0-18"
      }
    },
    "martin_service": {
      "success": true,
      "service_url": "http://localhost:3000/a1b2c3d4",
      "mvt_url": "http://localhost:3000/a1b2c3d4/{z}/{x}/{y}",
      "tilejson_url": "http://localhost:3000/a1b2c3d4"
    }
  }
}
```

### 2. 批量转换TIF文件

**接口地址**：`POST /api/tif-martin/batch-convert`

**请求参数**：
```json
{
  "file_ids": ["file_id1", "file_id2", "file_id3"],
  "max_zoom": 20
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量处理完成: 成功 2 个, 失败 1 个",
  "summary": {
    "total": 3,
    "success_count": 2,
    "error_count": 1,
    "max_zoom": 20
  },
  "results": [
    {
      "file_id": "123",
      "file_name": "sample1.tif",
      "success": true,
      "mbtiles_filename": "uuid1.mbtiles",
      "martin_service": {...}
    },
    {
      "file_id": "124",
      "file_name": "sample2.tif",
      "success": true,
      "mbtiles_filename": "uuid2.mbtiles",
      "martin_service": {...}
    },
    {
      "file_id": "125",
      "file_name": "invalid.txt",
      "success": false,
      "error": "不是TIF文件"
    }
  ]
}
```

### 3. 查询转换状态

**接口地址**：`GET /api/tif-martin/conversion-status/{file_id}`

**响应示例**：
```json
{
  "file_id": "338963489316016128",
  "file_name": "DOM_sample.tif",
  "file_type": "dom.tif",
  "converted": true,
  "services": [
    {
      "service_id": "338967150872104960",
      "service_url": "http://localhost:3000/a1b2c3d4",
      "mvt_url": "http://localhost:3000/a1b2c3d4/{z}/{x}/{y}",
      "tilejson_url": "http://localhost:3000/a1b2c3d4",
      "vector_type": "raster_mbtiles",
      "created_at": "2025-07-24T16:54:26"
    }
  ]
}
```

### 4. 列出所有转换记录

**接口地址**：`GET /api/tif-martin/list-conversions`

**查询参数**：
- `page`：页码，默认1
- `per_page`：每页数量，默认20

**响应示例**：
```json
{
  "success": true,
  "conversions": [
    {
      "service_id": "338967150872104960",
      "file_id": "338963489316016128",
      "original_filename": "DOM_sample_mbtiles",
      "file_name": "DOM_sample.tif",
      "file_type": "dom.tif",
      "file_size": 157286400,
      "service_url": "http://localhost:3000/a1b2c3d4",
      "mvt_url": "http://localhost:3000/a1b2c3d4/{z}/{x}/{y}",
      "tilejson_url": "http://localhost:3000/a1b2c3d4",
      "vector_type": "raster_mbtiles",
      "user_id": "326548821884669952",
      "created_at": "2025-07-24T16:54:26"
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
}
```

## ⚙️ 转换流程

1. **文件验证**：使用`gdalinfo`验证TIF文件格式和地理参考信息
2. **预处理**：如需要，将TIF文件转换为Web Mercator投影（EPSG:3857）
3. **瓦片生成**：
   - 优先使用`gdal2tiles.py`生成瓦片
   - 如不可用，则使用`gdalwarp`逐个生成瓦片
4. **MBTiles打包**：将瓦片目录打包为SQLite格式的MBTiles文件
5. **Martin发布**：调用RasterMartinService发布为Martin瓦片服务

## 🔧 配置要求

### GDAL安装（Windows）
```bash
# 使用conda安装
conda install -c conda-forge gdal

# 或下载OSGeo4W
# https://trac.osgeo.org/osgeo4w/
```

### GDAL安装（Linux）
```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin python3-gdal

# CentOS/RHEL
sudo yum install gdal gdal-python3
```

### Martin配置
确保`martin_config.yaml`中配置了正确的mbtiles路径：
```yaml
mbtiles:
  paths:
    - F:/PluginDevelopment/shpservice/FilesData/mbtiles
```

## 📊 性能参考

| 文件大小 | 最大缩放级别 | 预估时间 | MBTiles大小 |
|---------|-------------|----------|-------------|
| 10MB    | 15          | 1-2分钟   | 5-20MB      |
| 50MB    | 18          | 3-8分钟   | 20-100MB    |
| 200MB   | 20          | 10-30分钟 | 50-500MB    |
| 1GB     | 22          | 30-120分钟| 200MB-2GB   |

## ⚠️ 注意事项

1. **缩放级别**：级别越高，生成的瓦片数量呈指数增长，建议根据实际需要设置
2. **存储空间**：确保有足够的磁盘空间存储MBTiles文件
3. **内存使用**：大文件转换时可能占用较多内存
4. **并发限制**：批量转换最多支持10个文件
5. **GDAL版本**：建议使用GDAL 3.0+以获得最佳性能

## 🐛 常见错误

### GDAL工具不可用
```json
{
  "error": "GDAL工具不可用，请确保已安装GDAL并添加到PATH"
}
```
**解决方案**：安装GDAL并确保可执行文件在系统PATH中

### 文件验证失败
```json
{
  "error": "TIF文件验证失败: gdalinfo执行失败"
}
```
**解决方案**：检查TIF文件是否损坏或格式不正确

### 转换失败
```json
{
  "error": "TIF转MBTiles失败: 瓦片生成失败"
}
```
**解决方案**：检查TIF文件投影信息和地理边界是否正确 