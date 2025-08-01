# GIS数据管理系统

一个基于Flask + Vue的GIS数据管理平台，支持多种GIS数据格式的上传、管理、预览和地图可视化。
项目旨在提供一个灵活、易用的GIS数据管理解决方案，适用于科研、教育及商业领域。计划开源

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


### GeoServer配置
- 访问地址: http://localhost:8083/geoserver

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

### 登录及权限设置逻辑
1.增加登录页面，登录后，记录用户信息，并设置cookie；
2.在前端，根据cookie中的用户信息判断是否登录；
3.所有前端请求的接口均需要把用户信息作为参数传递，后端根据用户信息进行权限判断；
4.后端接口增加用户信息参数，并根据该参数进行权限判断；
5.数据库表中已有用户信息；
6.数据上传页获取的文件信息应该仅为该用户的文件和其他用户上传的文件类型为公开的文件；
7.场景管理中，用户只能看到自己创建的场景和其他用户设置为公开的场景；
8.地图浏览（leaflet和Openlayers）中，场景下拉框中仅显示自己创建的场景和其他用户设置为公开的场景；
9.地图浏览页（leaflet和Openlayers）的图层添加对话框中，仅显示自己创建的图层和其他用户设置为公开的图层；
10.后端数据库表可能需要对应字段，用以标识文件、场景和图层的创建人id和公开/私有状态；
11.后端接口增加用户信息参数，并根据该参数进行权限判断；

### 地图通过AI预测实现地图切片数据缓存预加载实现逻辑
1.前端
1）使用IndexDB缓存切片数据，https://juejin.cn/post/7395487322958446619
@https://juejin.cn/post/7026900352968425486 

缓存管理
充分浏览F:\PluginDevelopment\shpservice\frontend\src\services\tileCache文件夹下写好的函数，文件夹下主要列出IndexDB的操作函数，地图的Adapter是否主要就是写一个tileLoadFunction函数呢，不要examples.js
帮我重新调整该文件夹下的文件：文件夹下的文件尽量少，操作IndexDB的弄成一个文件，tile相关的计算弄成一个文件，自定义的tileLoadFunction做成一个文件就比较好


缓存管理页面-每个图层的操作栏帮我都做成缓存、可视化、和删除，没有这几个button的实现逻辑现在都不对：
①点击缓存：
弹出地图对话框
在地图上弹出该图层的边界框+高德底图信息，信息展示当前的缩放级别供用户参考，
可以在地图上框选一个范围，或者使用默认的边界框范围；
用户可以输入需要缓存的起始和终止缩放级别，默认的起始缩放级别为边界框当前的缩放级别；
根据以上用户输入信息，将相应图层数据缓存到IndexDB
仅缓存本图层的数据到IndexDB

②点击可视化
弹出地图对话框
显示高德底图及该图层的边界框
在地图上显示缓存的每个瓦片，每个瓦片之间要有格线显示，每个瓦片上显示z、x、y

③删除缓存
删除数据库中本图层的所有缓存

// 瓦片加载事件（用于底图缓存）
            const wmtsTileLoadFunction = function(imageTile, src) {
                const image = imageTile.getImage();
                
                // 从URL中提取瓦片坐标信息用于缓存
                const urlPattern = /x=(\d+).*y=(\d+).*z=(\d+)/;
                const match = src.match(urlPattern);
                let layerId = 'basemap_gaode';
                let z, x, y;
                
                if (match) {
                    x = parseInt(match[1]);
                    y = parseInt(match[2]);
                    z = parseInt(match[3]);
                } else {
                    // 如果无法解析坐标，直接加载
                    fetch(src).then(response => response.blob())
                        .then(blob => {
                            const imageUrl = URL.createObjectURL(blob);
                            image.src = imageUrl;
                        })
                        .catch(() => imageTile.setState(3));
                    return;
                }

                // 检查缓存中是否已经存在该瓦片
                if (tileCacheService) {
                    tileCacheService.getTile(layerId, z, x, y).then((tileCache) => {
                        if (tileCache != null && tileCache.data) {
                            // 如果已经存在，直接使用缓存的瓦片替换图片瓦片
                            let imageUrl;
                            if (tileCache.data instanceof Blob) {
                                imageUrl = URL.createObjectURL(tileCache.data);
                            } else if (typeof tileCache.data === 'string') {
                                // 如果是base64字符串
                                imageUrl = 'data:image/png;base64,' + tileCache.data;
                            } else {
                                // 如果是ArrayBuffer
                                const blob = new Blob([tileCache.data], { type: 'image/png' });
                                imageUrl = URL.createObjectURL(blob);
                            }
                            image.src = imageUrl;
                            console.log(`命中底图瓦片缓存: ${z}/${x}/${y}`);
                            return;
                        } else {
                            // 缓存中没有，从网络加载
                            fetch(src, {
                                method: 'GET',
                                keepalive: true,
                                cache: "force-cache"
                            }).then((response) => {
                                if (retryCodes.includes(response.status)) {
                                    retries[src] = (retries[src] || 0) + 1;
                                    if (retries[src] < 3) {
                                        console.log("请求瓦片失败，重新尝试次数：" + retries[src]);
                                        setTimeout(() => imageTile.load(), retries[src] * 250);
                                    }
                                    return Promise.reject();
                                }
                                return response.blob();
                            })
                            .then((blob) => {
                                const imageUrl = URL.createObjectURL(blob);
                                image.src = imageUrl;
                                
                                // 缓存瓦片到IndexedDB
                                if (tileCacheService) {
                                    const tileData = {
                                        id: `${layerId}_${z}_${x}_${y}`,
                                        layerId: layerId,
                                        zoomLevel: z,
                                        tileX: x,
                                        tileY: y,
                                        data: blob,
                                        size: blob.size,
                                        contentType: 'image/png',
                                        timestamp: Date.now(),
                                        url: src
                                    };
                                    
                                    tileCacheService.saveTile(tileData).then(() => {
                                        console.log(`底图瓦片已缓存: ${z}/${x}/${y}`);
                                    }).catch(error => {
                                        console.error('缓存底图瓦片失败:', error);
                                    });
                                }
                            })
                            .catch(() => imageTile.setState(3)); // error
                        }
                    }).catch(error => {
                        console.error('检查瓦片缓存失败:', error);
                        // 缓存检查失败，直接从网络加载
                        fetch(src).then(response => response.blob())
                            .then(blob => {
                                const imageUrl = URL.createObjectURL(blob);
                                image.src = imageUrl;
                            })
                            .catch(() => imageTile.setState(3));
                    });
                } else {
                    // 缓存服务未初始化，直接从网络加载
                    fetch(src).then(response => response.blob())
                        .then(blob => {
                            const imageUrl = URL.createObjectURL(blob);
                            image.src = imageUrl;
                        })
                        .catch(() => imageTile.setState(3));
                }
            };

            // 创建高德地图底图源
            const gaodeSource = new ol.source.XYZ({
                url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                crossOrigin: 'anonymous',
                maxZoom: 18,
                minZoom: 3
            });

            // 设置自定义瓦片加载函数
            gaodeSource.setTileLoadFunction(wmtsTileLoadFunction);

            // 创建底图
            const baseLayer = new ol.layer.Tile({
                source: gaodeSource
            });

            //瓦片加载事件（用于MVT缓存）
            const mvtTileLoadFunction = function(tile, url) {
                // 对于 VectorTile，我们需要设置 loader 而不是直接操作 image
                tile.setLoader(function(extent, resolution, projection) {
                    // 从URL中提取瓦片坐标
                    const match = url.match(/\/(\d+)\/(\d+)\/(\d+)$/);
                    if (!match) {
                        console.warn('无法解析瓦片坐标:', url);
                        tile.setFeatures([]);
                        return;
                    }
                    
                    const [z, x, y] = [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
                    console.log(`MVT瓦片请求: ${z}/${x}/${y} - ${url}`);
                    
                    // 从网络获取MVT数据
                    fetch(url)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}`);
                            }
                            return response.arrayBuffer();
                        })
                        .then(arrayBuffer => {
                            // 解析MVT数据
                            const mvtFormat = new ol.format.MVT();
                            const features = mvtFormat.readFeatures(arrayBuffer, {
                                extent: extent,
                                featureProjection: projection
                            });
                            
                            console.log(`MVT瓦片 ${z}/${x}/${y} 加载成功，包含 ${features.length} 个要素`);
                            tile.setFeatures(features);
                        })
                        .catch(error => {
                            console.error(`MVT瓦片 ${z}/${x}/${y} 加载失败:`, error);
                            tile.setFeatures([]);
                        });
                });
            };
            //创建MVT源
            const mvtSource = new ol.source.VectorTile({
                url: 'http://192.168.1.17:3000/vector_8aa2a0aa/{z}/{x}/{y}',
                format: new ol.format.MVT(),
                tileLoadFunction: mvtTileLoadFunction
            });
            //创建MVT图层
            const mvtLayer = new ol.layer.VectorTile({
                source: mvtSource,
                // 添加样式以便能看到矢量数据
                style: new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: '#FF0000',
                        width: 2
                    }),
                    fill: new ol.style.Fill({
                        color: 'rgba(255, 0, 0, 0.3)'
                    }),
                    image: new ol.style.Circle({
                        radius: 5,
                        fill: new ol.style.Fill({
                            color: '#FF0000'
                        })
                    })
                })
            });

            


openlayers从IndexDB加载缓存
https://openlayers.org/en/latest/apidoc/module-ol_source_XYZ-XYZ.html#tileLoadFunction
2）用户不同的操作行为触发不同的缓存加载策略：
   ①登录时，加载scenes数据，根据不同的scenes下的layers，加载不同layers的bounds，根据bounds加载范围内固定缩放级别的地图切片数据、加载图层切片数据；
   ②场景切换时，预加载该场景下的所有图层bounds和范围内的一定缩放级别范围内的切片数据
   ③缩放图层时，预加载当前缩放级别范围内的切片数据；
3）相关因素
   ①用户ID、场景ID、图层ID、bounds、缩放级别、tile_X\tile_Y
   ②常用场景、常用图层、常用bounds、常用缩放级别。
2.后端

缓存管理页面-在刷新、清空、导出、导入几个button前增加一个从后端更新场景和图层信息button-本页面用到的需要到后端请求的数据全部都缓存到IndexDB中，页面加载时不从后端获取数据，全部从IndexDB中获取，只有点击后端更新场景和图层信息这个button时，才会从后端获取信息，然后更新IndexDB中相应数据，每次更新都打上时间戳，加载页面时检查时间戳，超过一天再重新更新一次，不超一天就从IndexDB加载页面数据