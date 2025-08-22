# SLD样式管理功能说明

## 功能概述

为simple_frontend项目添加了SLD样式文件管理功能，允许用户上传、管理和应用SLD样式文件到GeoServer图层。

## 功能特性

### 1. SLD样式文件管理
- **上传SLD文件**：支持上传.sld格式的样式文件
- **样式分类**：按几何类型分类（点图层、线图层、面图层）
- **样式验证**：验证SLD文件格式和几何类型匹配
- **文件下载**：支持下载已上传的SLD文件
- **样式删除**：软删除样式文件

### 2. 图层样式应用
- **样式选择**：根据图层几何类型选择合适的SLD样式
- **样式应用**：一键将SLD样式应用到GeoServer图层
- **样式移除**：移除已应用的样式，恢复默认样式
- **实时预览**：应用样式后立即刷新地图显示

### 3. 用户界面
- **样式管理页面**：独立的SLD样式管理界面
- **图层样式设置**：在图层样式设置对话框中添加SLD样式选项卡
- **响应式设计**：支持桌面端和移动端

## 技术实现

### 后端实现

#### 1. 数据库设计
- **sld_styles表**：存储SLD样式文件信息
  - id: 主键
  - name: 样式名称
  - description: 样式描述
  - geometry_type: 几何类型（point/line/polygon）
  - file_path: 文件存储路径
  - file_size: 文件大小
  - content: SLD文件内容
  - created_by: 创建用户
  - created_at/updated_at: 时间戳
  - is_active: 是否激活

- **layer_sld_mapping表**：图层与SLD样式的映射关系
  - id: 主键
  - layer_id: 图层ID
  - sld_style_id: SLD样式ID
  - applied_at: 应用时间
  - applied_by: 应用用户
  - is_active: 是否激活

#### 2. 核心服务
- **SLDStyleModel**：数据库操作模型
- **SLDStyleService**：业务逻辑服务
- **SLD样式路由**：RESTful API接口

#### 3. API接口
```
POST /api/sld-styles/initialize     # 初始化数据库
POST /api/sld-styles/upload         # 上传SLD文件
GET  /api/sld-styles               # 获取样式列表
GET  /api/sld-styles/{id}          # 获取样式详情
GET  /api/sld-styles/{id}/download # 下载SLD文件
DELETE /api/sld-styles/{id}        # 删除样式
POST /api/sld-styles/apply         # 应用样式到图层
GET  /api/sld-styles/layer/{id}    # 获取图层当前样式
POST /api/sld-styles/layer/{id}/remove # 移除图层样式
```

### 前端实现

#### 1. 组件结构
- **SldStyleManager.vue**：SLD样式管理主组件
- **SldStyleSelector.vue**：图层样式选择器组件
- **sldStyle.js**：API服务模块

#### 2. 集成方式
- 在图层样式设置对话框中添加"SLD样式"选项卡
- 支持在样式管理页面独立管理所有SLD样式
- 实时同步样式应用状态

## 使用说明

### 1. 初始化数据库
```bash
cd backend
python init_sld_database.py
```

### 2. 启动服务
```bash
# 启动后端服务
cd backend
python app.py

# 启动前端服务
cd simple_frontend
npm run serve
```

### 3. 使用流程

#### 上传SLD样式
1. 进入图层样式设置对话框
2. 选择"SLD样式"选项卡
3. 选择图层几何类型
4. 点击"上传新样式"按钮
5. 填写样式信息并选择.sld文件
6. 点击"上传"完成上传

#### 应用样式到图层
1. 在SLD样式选项卡中选择图层几何类型
2. 从可用样式列表中选择合适的样式
3. 点击"应用"按钮
4. 样式将立即应用到GeoServer图层
5. 地图将自动刷新显示新样式

#### 管理样式文件
1. 访问样式管理页面
2. 可以查看、下载、删除已上传的样式
3. 支持按几何类型筛选样式
4. 支持分页浏览大量样式文件

## 文件结构

```
backend/
├── models/
│   └── sld_styles.py              # SLD样式数据模型
├── services/
│   └── sld_style_service.py       # SLD样式业务服务
├── routes/
│   └── sld_style_routes.py        # SLD样式API路由
├── app.py                         # 主应用（已注册路由）
└── init_sld_database.py           # 数据库初始化脚本

simple_frontend/
├── src/
│   ├── api/
│   │   └── sldStyle.js            # SLD样式API服务
│   └── components/
│       ├── SldStyleManager.vue    # SLD样式管理组件
│       ├── SldStyleSelector.vue   # SLD样式选择器组件
│       └── MapViewerOL.vue        # 地图组件（已集成）
```

## 注意事项

1. **文件格式**：只支持.sld格式的样式文件
2. **几何类型匹配**：SLD样式必须与图层几何类型匹配
3. **文件大小**：建议SLD文件不超过10MB
4. **权限要求**：需要GeoServer管理员权限来应用样式
5. **数据库依赖**：需要PostgreSQL数据库支持

## 扩展功能

1. **样式预览**：添加样式效果预览功能
2. **样式模板**：提供常用样式模板
3. **批量操作**：支持批量应用样式到多个图层
4. **样式版本管理**：支持样式版本控制和回滚
5. **样式分享**：支持样式文件分享和导入导出

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置
   - 确保PostgreSQL服务运行正常

2. **文件上传失败**
   - 检查文件格式是否为.sld
   - 确认文件大小不超过限制
   - 验证SLD文件格式是否正确

3. **样式应用失败**
   - 检查GeoServer连接
   - 确认图层存在且可访问
   - 验证样式几何类型与图层匹配

4. **前端编译错误**
   - 检查依赖包是否安装完整
   - 确认API路径配置正确

### 日志查看

- 后端日志：查看控制台输出或日志文件
- 前端日志：打开浏览器开发者工具查看控制台
- 网络请求：使用浏览器网络面板检查API调用
