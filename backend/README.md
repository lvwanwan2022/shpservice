# Backend README

本文件详细介绍了后端服务的架构、核心功能、数据处理流程和数据库结构，旨在帮助开发人员理解和维护代码，并在必要时能够基于此文档重建项目。

## 1. 项目概述

本项目是一个基于 Python (Flask) 的后端 API 服务，为地理信息展示和管理平台提供支持。它的核心职责包括：

-   管理用户、文件和元数据。
-   提供文件上传和下载接口。
-   编排和管理两种主流地图服务发布流程：GeoServer 和 Martin。
-   管理 "场景"（图层的有序集合）的配置。
-   提供 GIS 相关的工具函数 API（如坐标系查询）。

## 2. 主要服务和路由

后端采用服务-路由分离的结构，逻辑清晰。

-   **`app.py`**: 项目入口，创建 Flask 应用实例，注册蓝图。
-   **`config.py`**: 存储数据库、GeoServer 等服务的连接配置。

### 2.1. 核心模块

| 模块/文件 | 职责 |
| :--- | :--- |
| **文件管理** | |
| `routes/file_routes.py` | 提供文件上传、下载、列表查询、删除等 API 接口。 |
| `services/file_service.py` | 处理文件存储、数据库记录等核心业务逻辑。 |
| **GeoServer** | |
| `routes/geoservice_routes.py`| 提供发布文件到 GeoServer 的 API 接口。 |
| `services/geoserver_service.py`| **核心服务**。封装对 GeoServer REST API 的所有调用，处理工作区、数据存储、图层、样式等的创建和管理。 |
| **Martin** | |
| `routes/*_martin_*.py` | 提供发布 SHP, GeoJSON, DXF 等到 Martin 的 API 接口。 |
| `services/*_martin_*.py` | **核心服务**。处理数据转换，使用 `ogr2ogr` 等工具将源文件导入 PostGIS，并记录服务信息。 |
| `services/dxf_*.py` | 专门用于处理和解析 DXF 文件的服务，提取图层信息。 |
| **场景管理** | |
| `routes/scene_routes.py` | 提供场景的增删改查 API。 |
| `services/scene_service.py` | 实现场景和场景图层管理的业务逻辑。 |
| **样式管理** | |
| `services/style_service.py` | 管理与样式相关的逻辑，特别是 Martin 服务的 DXF 样式（JSON格式）。 |
| `services/sld_template_service.py`| 用于生成 GeoServer 的 SLD (Styled Layer Descriptor) 样式文件。 |
| **数据库** | |
| `models/db.py` | 封装了所有数据库操作，通过原生 `psycopg2` 执行 SQL，并包含 `init_database` 函数用于创建所有表结构。 |
| `services/postgis_service.py`| 封装了对 PostGIS 数据库的特定操作。 |

## 3. 地图服务发布逻辑

项目最核心的功能之一是双轨制的地图服务发布流程。

### 3.1. 通过 GeoServer 发布服务 (WMS/WFS)

此流程主要由 `geoserver_service.py` 驱动，它通过调用 GeoServer 的原生 REST API 来完成。

**逻辑步骤与关键 REST API**:

1.  **接收请求**: 前端在 "数据管理" 页面点击发布 GeoServer 服务。

2.  **创建工作区 (Workspace)**: 确保存在一个用于组织数据的独立工作区（例如 `shpservice`）。
    -   **API**: `POST /rest/workspaces`
    -   **Payload**: `{"workspace": {"name": "shpservice"}}`

3.  **创建数据存储 (DataStore) / 覆盖存储 (CoverageStore)**:
    -   **对于 Shapefile**:
        -   **1. 上传 `.zip` 文件**:
            -   **API**: `PUT /rest/workspaces/{ws}/datastores/{store_name}/file.shp`
            -   **Headers**: `Content-type: application/zip`
            -   **说明**: 这是最直接的方式，GeoServer 会自动解压并创建一个与 `store_name` 对应的 Shapefile 数据存储。
    -   **对于 PostGIS**:
        -   **API**: `POST /rest/workspaces/{ws}/datastores`
        -   **Payload**: 包含数据库连接详情的 JSON，如主机、端口、数据库名、用户名、密码等。
    -   **对于 GeoTIFF**:
        -   **API**: `PUT /rest/workspaces/{ws}/coveragestores/{store_name}/file.geotiff`
        -   **Headers**: `Content-type: image/tiff`
        -   **说明**: 将 GeoTIFF 文件内容作为请求体上传，GeoServer 会创建相应的覆盖存储。

4.  **创建要素类型 (FeatureType) / 覆盖 (Coverage)**:
    -   **自动化**: 在上一步成功创建数据存储后，GeoServer 通常会自动发现并注册数据源中的要素类型（矢量）或覆盖（栅格）。
    -   **手动触发 (如 PostGIS)**: 如果需要手动从一个已存在的 PostGIS 数据存储中发布特定表：
        -   **API**: `POST /rest/workspaces/{ws}/datastores/{store_name}/featuretypes`
        -   **Payload**: `{"featureType": {"name": "table_name_in_db"}}`

5.  **创建/配置图层 (Layer)**:
    -   **自动化**: 创建要素类型或覆盖时，GeoServer 会自动创建一个同名图层，并关联默认样式。
    -   **更新样式**: 如需将特定样式应用到图层：
        -   **API**: `PUT /rest/layers/{layer_name}`
        -   **Payload**: `{"layer": {"defaultStyle": {"name": "style_name"}}}`

6.  **记录元数据**: 将创建的工作区、存储、图层等信息记录到后端自身的 PostgreSQL 数据库的 `geoserver_*` 相关表中，用于后续管理和查询。

7.  **返回服务地址**: 将生成的 WMS、WFS 等服务地址返回给前端。

### 3.2. 通过 Martin 发布服务 (MVT)

此流程利用了 Martin 的 **自动发布 (Auto-Publishing)** 功能，并与一个专用的 PostGIS 数据库紧密集成。

**配置文件**: `martin_config.yaml`

```yaml
postgres:
  connection_string: postgresql://user:pass@host/Geometry
  auto_publish:
    tables:
      from_schemas: ["public"]
      id_regex: "^vector_.*"
```

**逻辑步骤**:

1.  **接收请求**: 前端在 "数据管理" 页面点击发布 Martin 服务。
2.  **数据转换与导入 (核心)**:
    -   后端服务（例如 `shp_martin_service.py`）调用系统命令 `ogr2ogr`。
    -   `ogr2ogr` 是一个强大的地理数据转换工具，它会将用户上传的源文件（如 `data.shp`）转换为 PostGIS SQL 格式并导入到 `martin_config.yaml` 中指定的 `Geometry` 数据库。
3.  **表命名**:
    -   在导入时，服务会为新表生成一个符合 `id_regex` 规则的唯一名称，例如 `vector_shp_xxxxxx`。这是触发自动发布的关键。
4.  **Martin 自动发布**:
    -   Martin 服务在运行时会持续监控 `Geometry` 数据库。
    -   当它检测到一个名为 `vector_...` 的新表出现时，会自动将其发布为 MVT 服务。
    -   服务的 URL 格式为 `http://<martin_host>:3000/{table_name}/{z}/{x}/{y}`。
5.  **记录元数据**: 后端服务将 PostGIS 中的表名、生成的服务 URL、文件 ID 等信息记录到 `vector_martin_services` 表中。对于 DXF 文件，还会将提取或用户定义的样式（JSON 格式）一并存入此表的 `style` 字段。
6.  **返回服务地址**: 将 TileJSON 地址和 MVT 模板地址返回给前端。

## 4. 数据库主要数据表结构

项目使用两个 PostgreSQL 数据库。

### 4.1. 应用数据库 (在 `config.py` 中配置)

用于存储应用自身的状态和元数据。表结构在 `models/db.py` 的 `init_database` 函数中定义。

-   **`files`**: 核心文件信息表。记录所有上传文件的元数据，如文件名、路径、大小、坐标系、专业、维度等。
-   **`users`**: 用户信息表。
-   **`scenes`**: 场景定义表。
-   **`scene_layers`**: **场景-图层关联表**。记录了哪个场景包含了哪个图层，以及在该场景下图层的特定属性（顺序、可见性、透明度、自定义样式等）。这是实现场景功能的关键。
-   **`geoserver_*` 系列表**: (`geoserver_workspaces`, `geoserver_stores`, `geoserver_layers` 等)
    -   这些表作为 GeoServer 配置的一个镜像或本地缓存。当通过本系统发布一个 GeoServer 图层时，相关的信息会被记录在这里，方便管理，而不是每次都去查询 GeoServer API。
-   **`vector_martin_services`**:
    -   **Martin 服务的核心记录表**。它建立了上传文件 (`file_id`) 和 PostGIS 中实际数据表 (`table_name`) 之间的映射关系。
    -   存储了 Martin 服务的 URL (`mvt_url`, `tilejson_url`)。
    -   `style` 字段 (JSONB 类型) 用于存储 DXF 图层的自定义样式配置，这是前端实现 DXF 数据驱动样式的后端基础。

### 4.2. Martin 数据源数据库 (`Geometry`)

-   **用途**: 此数据库是 Martin 服务的**唯一数据源**。
-   **配置**: 在 `martin_config.yaml` 中定义连接字符串。
-   **内容**: 只包含由后端服务通过 `ogr2ogr` 从用户上传的 `SHP`, `GeoJSON`, `DXF` 等文件转换而来的地理数据表。表的名称都以 `vector_` 开头，以被 Martin 自动识别和发布。
-   **注意**: 此数据库不包含应用逻辑相关的表，纯粹作为地理数据的仓库。 