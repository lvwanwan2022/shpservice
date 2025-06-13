# GIS数据管理系统

一个基于Flask + Vue的GIS数据管理平台，支持多种GIS数据格式的上传、管理、预览和地图可视化。

## 功能特性

- **多格式支持**: 支持SHP、DEM、DOM、DWG、DXF、GeoJSON等多种GIS数据格式
- **数据管理**: 完整的文件上传、检索、预览、删除功能
- **地图可视化**: 基于Leaflet的交互式地图展示
- **场景管理**: 支持创建多个地图场景，每个场景可包含多个图层
- **图层控制**: 支持图层显隐、顺序调整、样式设置
- **GeoServer集成**: 自动发布数据到GeoServer，支持WMS/WFS服务
- **元数据管理**: 丰富的元数据字段，支持按专业、类型、标签等搜索

## 技术架构

### 后端技术栈
- **Flask**: Python Web框架
- **PostgreSQL + PostGIS**: 空间数据库存储
- **GeoServer**: 地理数据服务
- **Flask-RESTX**: API文档和管理
- **psycopg2**: PostgreSQL数据库连接
- **geopandas**: 空间数据处理和分析
- **SQLAlchemy**: 数据库ORM框架

### 前端技术栈
- **Vue 3**: 前端框架
- **Element Plus**: UI组件库
- **Leaflet**: 地图可视化
- **Axios**: HTTP客户端

## 系统要求

### 基础环境
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- GeoServer 2.20+

### 数据库配置
```sql
-- 创建数据库
CREATE DATABASE Geometry;
-- 创建用户（如果需要）
CREATE USER postgres WITH PASSWORD '123456';
GRANT ALL PRIVILEGES ON DATABASE Geometry TO postgres;
```

### GeoServer配置
- 访问地址: http://localhost:8083/geoserver
- 默认用户名: admin
- 默认密码: geoserver

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd shpservice
```

### 2. 后端设置

#### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

**新增的空间数据处理依赖：**
- `geopandas`: 强大的地理空间数据处理库
- `sqlalchemy`: 数据库ORM框架
- `GeoAlchemy2`: SQLAlchemy的地理空间扩展
- `fiona`: 地理空间文件I/O库
- `shapely`: 几何对象操作库
- `pyproj`: 坐标系统转换库

**重要提示：**
如果在Windows系统上安装geopandas遇到问题，建议：
1. 先安装conda: `conda install geopandas`
2. 或使用预编译包: `pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ geopandas`

#### 配置数据库
编辑 `backend/config.py` 文件，确保数据库连接信息正确：
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'Geometry',
    'user': 'postgres',
    'password': '123456'
}
```

#### 启动后端服务
```bash
# 初始化数据库（首次运行）
python run.py --init-db

# 启动服务
python run.py
```

后端服务将在 http://localhost:5030 启动
API文档地址: http://localhost:5030/swagger/

### 3. 前端设置

#### 安装依赖
```bash
cd frontend
npm install
```

#### 开发模式启动
```bash
npm run dev
```

#### 生产构建
```bash
npm run build
```

## 项目结构

```
shpservice/
├── backend/                 # 后端代码
│   ├── config.py           # 配置文件
│   ├── app.py              # Flask应用入口
│   ├── run.py              # 启动脚本
│   ├── requirements.txt    # Python依赖
│   ├── models/             # 数据模型
│   │   └── db.py          # 数据库操作
│   ├── services/           # 业务服务
│   │   ├── file_service.py    # 文件服务
│   │   ├── scene_service.py   # 场景服务
│   │   └── geoserver_service.py # GeoServer服务
│   └── routes/             # API路由
│       ├── file_routes.py     # 文件管理API
│       ├── scene_routes.py    # 场景管理API
│       ├── layer_routes.py    # 图层管理API
│       └── geoservice_routes.py # GeoServer服务API
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   │   └── UploadView.vue # 数据管理页面
│   │   ├── components/    # 通用组件
│   │   │   ├── SceneManager.vue # 场景管理
│   │   │   └── MapViewer.vue    # 地图查看器
│   │   └── router/        # 路由配置
│   └── package.json       # 前端依赖
├── FilesData/             # 文件存储目录
└── README.md             # 项目文档
```

## API接口

### 文件管理
- `POST /api/file/upload` - 文件上传
- `GET /api/file/list` - 文件列表
- `GET /api/file/<id>` - 文件详情
- `DELETE /api/file/<id>` - 删除文件
- `GET /api/file/users` - 用户列表

### 场景管理
- `POST /api/scene` - 创建场景
- `GET /api/scene` - 场景列表
- `GET /api/scene/<id>` - 场景详情
- `PUT /api/scene/<id>` - 更新场景
- `DELETE /api/scene/<id>` - 删除场景

### 图层管理
- `POST /api/scene/<id>/layers` - 添加图层
- `PUT /api/scene/<id>/layers/<layer_id>` - 更新图层
- `DELETE /api/scene/<id>/layers/<layer_id>` - 删除图层
- `POST /api/scene/<id>/layers/reorder` - 重排图层

### GeoServer服务
- `GET /api/geoservice/layers` - 图层列表
- `GET /api/geoservice/layer_info/<name>` - 图层信息
- `GET /api/geoservice/layer_preview/<name>` - 图层预览

## 配置说明

### 后端配置 (backend/config.py)
```python
# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'Geometry',
    'user': 'postgres',
    'password': '123456'
}

# GeoServer配置
GEOSERVER_CONFIG = {
    'url': 'http://localhost:8083/geoserver',
    'user': 'admin',
    'password': 'geoserver',
    'workspace': 'shpservice'
}

# 文件存储配置
FILE_STORAGE = {
    'upload_folder': '../FilesData',
    'allowed_extensions': ['tif', 'mbtiles', 'dwg', 'dxf', 'geojson', 'zip'],
    'max_file_size': 500 * 1024 * 1024  # 500MB
}
```

## 部署指南

### 生产环境部署

#### 1. 使用Gunicorn部署后端
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 2. 使用Nginx代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否启动
   - 验证数据库连接信息
   - 确保数据库用户有足够权限

2. **GeoServer连接失败**
   - 检查GeoServer服务状态
   - 验证GeoServer访问地址和端口
   - 确认用户名密码正确

3. **文件上传失败**
   - 检查文件存储目录权限
   - 验证文件格式是否支持
   - 确认文件大小未超过限制

4. **前端编译错误**
   - 更新Node.js到最新LTS版本
   - 清除node_modules重新安装依赖
   - 检查包管理器版本

## 开发指南

### 添加新的文件类型支持
1. 在 `config.py` 的 `allowed_extensions` 中添加扩展名
2. 在 `geoserver_service.py` 中添加对应的发布方法
3. 在前端 `fileTypes` 数组中添加类型选项

### 自定义样式配置
在 `MapViewer.vue` 的样式设置部分添加新的样式选项和参数。

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者 

# SHP Service

## 数据上传与服务发布

### 工作流程

本系统将数据上传和服务发布分为两个独立的步骤：

#### 1. 数据上传
- 用户通过"数据上传"功能上传文件（支持 shp、geojson、tif、dem、dom、dwg、dxf 等格式）
- 系统仅保存文件到服务器，记录元数据信息
- **不会自动发布为GeoServer服务**

#### 2. 服务发布
- 数据上传成功后，在文件列表中会显示"未发布"状态
- 用户可以根据需要点击"发布服务"按钮
- 系统将文件发布到GeoServer，生成WMS/WFS服务
- 发布成功后状态变为"已发布"，显示服务地址

### 优势
- **按需发布**：只有需要的数据才发布为服务，节省服务器资源
- **灵活控制**：用户可以控制何时发布服务
- **错误隔离**：上传失败不影响数据保存，发布失败不影响数据存储
- **资源管理**：避免不必要的服务占用GeoServer资源

### 支持的文件类型
- **可发布服务**：shp、geojson、tif、dem、dom、mbtiles
- **仅存储**：dwg、dxf（现已支持自动发布）

### 操作说明
1. 点击"数据上传"按钮上传文件
2. 填写文件信息（名称、专业、类型等）
3. 点击"上传"完成数据保存
4. 在文件列表中找到上传的文件
5. 点击"发布服务"按钮发布为GeoServer服务
6. 发布成功后可复制WMS/WFS服务地址使用

### 故障排除

#### 图层配置错误问题
如果遇到"图层名称配置错误"的问题，可以使用以下方法排查：

1. **使用调试功能**：在文件列表中点击"调试"按钮，查看详细的诊断信息
2. **检查图层名称**：确保GeoServer中的图层名称与数据库记录一致
3. **验证服务可用性**：确认WMS/WFS服务地址可以正常访问

#### 常见问题解决方案

**问题1：服务发布成功但图层无法显示**
- 原因：图层名称不匹配或GeoServer配置问题
- 解决：使用调试功能检查图层状态，重新发布服务

**问题2：WMS瓦片加载失败**
- 原因：代理配置问题或图层数据范围问题
- 解决：检查nginx代理配置，确认数据坐标系正确

**问题3：Shapefile发布后图层名称错误**
- 原因：ZIP包内文件名与预期不符
- 解决：系统已自动修复，会获取实际的图层名称

#### 测试工具
项目提供了测试脚本来验证GeoServer配置：

```bash
# 运行GeoServer基础测试
python test_geoserver.py

# 运行服务发布功能测试
python test_publish_service.py

# 测试特定文件的发布（替换8为实际文件ID）
python test_publish_service.py 8
```

这些脚本会检查：
- GeoServer连接状态
- 工作空间配置
- WMS服务可用性
- 已发布图层状态
- 图层验证功能
- 实际图层名称获取

#### 最新修复 (v2.0)

**修复内容：**
1. **改进图层名称获取**：增加了从ZIP文件中提取实际SHP文件名的功能
2. **宽松验证模式**：不再因为图层验证失败而阻止发布，改为警告提示
3. **多重验证机制**：使用图层信息、WMS Capabilities、WMS GetMap等多种方式验证
4. **详细日志输出**：增加了详细的调试日志，便于问题排查
5. **重试机制**：增加了等待时间，让GeoServer有时间处理发布请求

**使用建议：**
- 如果发布后显示警告，请等待几秒钟后使用"调试"功能检查
- 对于Shapefile，系统会自动提取ZIP包内的实际文件名作为图层名
- 如果遇到问题，可以运行测试脚本进行诊断 

## MBTiles 支持

系统现已支持 MBTiles 文件的发布和管理，提供以下功能：

1. **MBTiles 文件上传**：支持上传 MBTiles 格式的瓦片数据
2. **自动发布为 Martin 服务**：上传后可一键发布为 Martin 瓦片服务
3. **专用 API 接口**：提供 `/api/mbtiles/` 系列接口管理 MBTiles 服务
4. **服务管理**：支持查看、删除 MBTiles 服务

### MBTiles 服务使用方法

1. **上传 MBTiles 文件**：通过文件上传功能上传 .mbtiles 文件
2. **发布服务**：在文件列表中找到上传的 MBTiles 文件，点击"发布服务"按钮
3. **使用服务**：发布成功后可获取服务地址，格式为 `http://localhost:3000/mbtiles/{文件名}/{z}/{x}/{y}`

### MBTiles API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/mbtiles/services/list` | GET | 获取所有 MBTiles 服务列表 |
| `/api/mbtiles/services/{service_id}` | GET | 获取指定 MBTiles 服务详情 |
| `/api/mbtiles/services/{service_id}` | DELETE | 删除指定 MBTiles 服务 |
| `/api/mbtiles/publish/{file_id}` | POST | 发布 MBTiles 文件为服务 |
| `/api/mbtiles/unpublish/{file_id}` | DELETE | 取消发布 MBTiles 服务 |

GeoServer概念          →  数据库表                →  说明
─────────────────────────────────────────────────────────────
工作空间(Workspace)    →  geoserver_workspaces   →  命名空间管理
存储仓库(Store)        →  geoserver_stores       →  数据源连接
要素类型(FeatureType)  →  geoserver_featuretypes →  矢量数据结构
覆盖范围(Coverage)     →  geoserver_coverages    →  栅格数据结构  
图层(Layer)           →  geoserver_layers       →  发布的服务
图层组(LayerGroup)    →  geoserver_layergroups  →  图层组合
样式(Style)           →  geoserver_styles       →  渲染样式

业务流程                →  涉及的表
────────────────────────────────────────────
文件上传               →  files
GeoServer发布          →  geoserver_* 系列表
场景管理               →  scenes, scene_layers
地图浏览               →  所有表的联合查询

# 安装 Rust (如果还没有)
winget install Rustlang.Rustup

# 安装 Martin
cargo install martin

# 测试集成
cd backend
python test_martin_integration.py


我的martin发布的dxf的样式应该每次加载图层时都从数据库表中获取，后端也写好了相应的接口，如果后端样式为空，才会使用dxf的默认样式：G:\code\shpservice\frontend\src\config\defaultDxfStyles.json
每次调出martin(dxf)选项卡，都会从数据库读取一次样式，每次更改一个样式就会应用到图层样式上，但是不会保存到数据库，帮我检查现在是否是这个逻辑

## DXF图层样式功能

### 功能说明

本系统支持根据PostGIS表中的`cad_layer`字段为DXF图层设置不同的样式，实现与AutoCAD中DXF图层样式的一致性。

### PostGIS表结构支持

对于如下的PostGIS表结构：
```sql
CREATE TABLE IF NOT EXISTS public.vector_05492e03
(
    gid integer NOT NULL DEFAULT nextval('vector_05492e03_gid_seq'::regclass),
    cad_layer character varying COLLATE pg_catalog."default",  -- 关键字段：图层名称
    paperspace boolean,
    subclasses character varying COLLATE pg_catalog."default",
    linetype character varying COLLATE pg_catalog."default",
    entityhandle character varying COLLATE pg_catalog."default",
    text character varying COLLATE pg_catalog."default",
    rawcodevalues character varying[] COLLATE pg_catalog."default",
    geom geometry(Geometry,3857),  -- 几何字段
    CONSTRAINT vector_05492e03_pkey PRIMARY KEY (gid)
)
```

### 样式应用逻辑

1. **MVT要素样式映射**：
   - 系统从MVT要素的`properties.cad_layer`字段读取图层名称
   - 根据图层名称在默认DXF样式配置中查找对应样式
   - 如果找不到匹配样式，使用通用默认样式

2. **样式优先级**：
   - 用户自定义样式（最高优先级）
   - DXF默认样式配置
   - 系统通用默认样式（最低优先级）

### 使用方法
需要修改MapViewer组件中的addMartinLayer方法，实现README中描述的DXF样式逻辑。根据README的描述，需要：
从MVT要素的properties.cad_layer字段读取图层名称
根据图层名称在默认DXF样式配置中查找对应样式
如果找不到匹配样式，使用通用默认样式
支持样式优先级：用户自定义样式 > DXF默认样式配置 > 系统通用默认样式

1. **加载DXF图层**：
   - 上传DXF文件到系统
   - 系统自动转换为PostGIS表
   - 发布为Martin PBF服务
   - 在地图中添加图层

2. **样式设置**：
   - 点击图层的"样式设置"按钮
   - 切换到"Martin(DXF)"选项卡
   - 系统自动应用当前样式配置
   - 修改任何样式属性都会实时更新地图显示
   - **新功能**：支持从MVT要素的`properties.cad_layer`字段自动识别CAD图层
   - **新功能**：实现三级样式优先级：用户自定义 > DXF默认配置 > 系统默认
   - **新功能**：样式修改后自动重新加载图层，无需手动刷新
   - **新功能**：属性弹窗显示CAD图层信息，方便用户识别图层来源

3. **支持的样式属性**：
   - 颜色（color）
   - 线宽（weight）
   - 透明度（opacity）
   - 线型（dashArray）：实线、虚线、点线、点划线
   - 填充（fill）：是否填充
   - 填充颜色（fillColor）
   - 可见性（visible）

### 调试功能

开发者可以在浏览器控制台查看详细的样式应用日志：
- DXF图层信息
- 样式配置内容
- 要素样式处理过程
- 样式应用结果

### 已配置的默认DXF图层样式

系统预配置了常见的DXF图层样式，包括：
- 地形相关：DMTZ、DGX、GCD、jqx、sqx
- 水系设施：SXSS
- 道路交通：DLSS  
- 建筑居住：JMD、DLDW
- 植被绿化：ZBTZ
- 管线设施：GXYZ
- 边界控制：JJ、KZD、JZD、TK
- 辅助图层：ASSIST

更多图层样式可以通过样式编辑器动态添加和配置。