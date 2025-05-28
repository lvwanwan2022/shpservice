# Martin 瓦片服务集成指南

## 概述

Martin 是一个高性能的 MVT (Mapbox Vector Tiles) 瓦片服务器，用 Rust 编写，原生支持 PostGIS 数据源。相比传统的 GeoServer，Martin 具有以下优势：

- **高性能**: Rust 编写，内存占用小，并发性能强
- **简单配置**: 相比 GeoServer 复杂的配置，Martin 配置更加简洁
- **现代标准**: 原生支持 Mapbox Vector Tiles (MVT) 格式
- **云原生**: 支持容器化部署，易于扩展

## Martin 安装

### Windows 系统

#### 方法1: 通过 Rust Cargo 安装 (推荐)

1. **安装 Rust**
   ```powershell
   # 下载并安装 Rust
   # 访问 https://rustup.rs/ 下载安装程序
   # 或使用 winget
   winget install Rustlang.Rustup
   ```

2. **安装 Martin**
   ```powershell
   cargo install martin
   ```

#### 方法2: 下载预编译二进制文件

1. 访问 [Martin Releases](https://github.com/maplibre/martin/releases)
2. 下载适用于 Windows 的二进制文件
3. 将可执行文件放到 PATH 目录中

#### 方法3: 使用 Docker

```powershell
# 拉取 Martin 镜像
docker pull ghcr.io/maplibre/martin

# 运行 Martin 容器
docker run -p 3000:3000 -e DATABASE_URL="postgresql://postgres:123456@host.docker.internal:5432/Geometry" ghcr.io/maplibre/martin
```

### Linux/macOS 系统

```bash
# 通过 Cargo 安装
cargo install martin

# 或使用包管理器（如果可用）
# Ubuntu/Debian
sudo apt install martin

# macOS
brew install martin
```

## 集成到现有项目

### 1. 启动 Martin 服务

在项目后端启动后，Martin 会自动启动并连接到你的 PostGIS 数据库：

```python
# 启动你的 Flask 应用
python backend/run.py

# Martin 服务会自动在 http://localhost:3000 启动
```

### 2. API 接口

Martin 集成提供了以下 API 接口：

#### 服务管理
- `GET /api/martin/status` - 获取服务状态
- `POST /api/martin/start` - 启动服务
- `POST /api/martin/stop` - 停止服务
- `POST /api/martin/restart` - 重启服务
- `POST /api/martin/refresh` - 刷新表配置

#### 数据管理
- `GET /api/martin/tables` - 获取 PostGIS 空间表列表
- `GET /api/martin/catalog` - 获取服务目录
- `GET /api/martin/table/<table_id>` - 获取表的 TileJSON 信息
- `GET /api/martin/mvt/<table_id>` - 获取 MVT 瓦片 URL

#### 配置管理
- `GET /api/martin/config` - 获取当前配置

### 3. 前端地图集成

Martin 生成的 MVT 瓦片可以直接在现代地图库中使用：

#### Leaflet 集成示例

```javascript
// 1. 获取 MVT URL
const response = await fetch('/api/martin/mvt/public.your_table');
const { mvt_url, tilejson_url } = await response.json();

// 2. 使用 Leaflet.VectorGrid 加载 MVT
import L from 'leaflet';
import 'leaflet.vectorgrid';

const map = L.map('map').setView([39.9, 116.4], 10);

// 添加 MVT 图层
const mvtLayer = L.vectorGrid.protobuf(mvt_url, {
    vectorTileLayerStyles: {
        'your_layer_name': {
            weight: 2,
            color: '#ff0000',
            fillColor: '#00ff00',
            fillOpacity: 0.5
        }
    }
}).addTo(map);
```

#### MapLibre GL JS 集成示例

```javascript
// 获取 TileJSON URL
const response = await fetch('/api/martin/table/public.your_table');
const tileJson = await response.json();

// 使用 MapLibre GL JS
import maplibregl from 'maplibre-gl';

const map = new maplibregl.Map({
    container: 'map',
    style: {
        version: 8,
        sources: {
            'your-source': {
                type: 'vector',
                url: tileJson.tilejson
            }
        },
        layers: [{
            id: 'your-layer',
            source: 'your-source',
            'source-layer': 'your_table',
            type: 'fill',
            paint: {
                'fill-color': '#00ff00',
                'fill-opacity': 0.5
            }
        }]
    }
});
```

## 配置说明

### 数据库配置

Martin 使用以下配置连接到你的 PostGIS 数据库：

```python
# backend/config.py
MARTIN_CONFIG = {
    'enabled': True,  # 是否启用 Martin 服务
    'port': 3000,     # Martin 服务端口
    'host': '0.0.0.0', # 监听地址
    'postgres_connection': 'postgresql://postgres:123456@localhost:5432/Geometry',
    'auto_publish_tables': True,  # 自动发现 PostGIS 表
    'cors_enabled': True,         # 启用 CORS
    'cache_size': 512,           # 缓存大小 (MB)
    'pool_size': 20,             # 连接池大小
}
```

### 自动表发现

Martin 会自动发现 PostGIS 数据库中的所有空间表，包括：
- 通过 `geometry_columns` 视图发现的表
- 包含 `geometry` 或 `geography` 列的表
- 你上传的 GeoJSON 数据转换后的表

## 性能优化

### 1. 数据库优化

```sql
-- 为几何列创建空间索引
CREATE INDEX idx_table_geom ON your_table USING GIST (geom);

-- 创建属性索引（用于过滤）
CREATE INDEX idx_table_category ON your_table (category);

-- 更新表统计信息
ANALYZE your_table;
```

### 2. Martin 配置优化

```yaml
# martin_config.yaml
listen_addresses: 0.0.0.0:3000
worker_processes: auto
cache_size_mb: 1024  # 增加缓存大小
postgres:
  connection_string: postgresql://postgres:123456@localhost:5432/Geometry
  pool_size: 50      # 增加连接池大小
  max_feature_count: 10000  # 限制要素数量
```

## 监控和调试

### 查看服务状态

```bash
# 检查 Martin 服务状态
curl http://localhost:3000/health

# 查看可用表
curl http://localhost:3000/catalog

# 获取表的 TileJSON
curl http://localhost:3000/public.your_table
```

### 日志监控

Martin 服务的日志可以通过 Flask 应用的日志系统查看：

```python
import logging
logger = logging.getLogger('martin_service')
logger.info("Martin 服务状态检查")
```

## 与 GeoServer 对比

| 特性 | Martin | GeoServer |
|------|--------|-----------|
| 性能 | 非常高 | 中等 |
| 内存占用 | 很低 | 较高 |
| 配置复杂度 | 简单 | 复杂 |
| 瓦片格式 | MVT (矢量) | 多种 |
| WMS 支持 | 无 | 支持 |
| 样式定义 | 客户端 | 服务端 |
| 部署难度 | 简单 | 中等 |

## 故障排除

### 常见问题

1. **Martin 安装失败**
   ```bash
   # 检查 Rust 是否正确安装
   rustc --version
   cargo --version
   
   # 重新安装
   cargo install martin --force
   ```

2. **数据库连接失败**
   - 检查 PostgreSQL 服务是否运行
   - 验证数据库连接参数
   - 确保 PostGIS 扩展已安装

3. **表未显示**
   ```sql
   -- 检查表是否有几何列
   SELECT * FROM geometry_columns WHERE f_table_name = 'your_table';
   
   -- 检查表权限
   GRANT SELECT ON your_table TO postgres;
   ```

4. **瓦片无法加载**
   - 检查 CORS 设置
   - 验证瓦片 URL 格式
   - 查看浏览器网络面板的错误信息

### 获取帮助

- Martin 官方文档: https://maplibre.org/martin/
- GitHub 仓库: https://github.com/maplibre/martin
- PostGIS 文档: https://postgis.net/docs/

## 总结

Martin 为你的 GIS 数据管理系统提供了现代化的矢量瓦片服务能力，相比传统的 GeoServer 方案：

- ✅ **性能更优**: 处理大数据量时响应更快
- ✅ **配置更简**: 自动发现数据库表，无需复杂配置
- ✅ **集成更易**: 原生支持现代前端地图库
- ✅ **维护更少**: 资源占用小，稳定性高

通过 Martin，你可以将存储在 PostGIS 中的 GeoJSON 数据高效地发布为现代化的矢量瓦片服务，为前端地图应用提供流畅的用户体验。 