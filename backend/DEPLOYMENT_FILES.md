# 🚀 SHP Service 部署文件说明

## 📁 当前部署文件结构

### 🔥 核心部署文件（推荐使用）

#### 1. **生产环境部署**
- `deploy_production.bat` - **主要部署脚本**，支持4种部署模式选择
- `start_production_simple.bat` - 快速启动高性能单实例
- `waitress_production.py` - 高性能Waitress服务器（核心）

#### 2. **企业级功能**
- `windows_service.py` - Windows系统服务管理
- `multi_instance_launcher.py` - 多实例负载均衡集群
- `performance_monitor.py` - 实时性能监控工具

#### 3. **负载均衡配置**
- `nginx_loadbalancer.conf` - Nginx负载均衡配置文件

#### 4. **基础配置**
- `wsgi.py` - WSGI应用入口点
- `config.py` - 应用配置文件

## 🎯 推荐使用方式

### 快速开始（单实例）
```bash
# 方式1: 使用快速启动脚本
start_production_simple.bat

# 方式2: 直接运行Python脚本
python waitress_production.py
```

### 完整生产环境（推荐）
```bash
# 运行部署向导，选择部署模式
deploy_production.bat
```

### 高并发场景（负载均衡）
```bash
# 1. 启动多实例集群
python multi_instance_launcher.py

# 2. 配置Nginx（使用nginx_loadbalancer.conf）
```

### Windows服务模式（企业环境）
```bash
# 安装服务
python windows_service.py install

# 启动服务  
python windows_service.py start

# 管理服务
python windows_service.py status|stop|restart
```

## 📊 性能监控
```bash
# 实时监控仪表板
python performance_monitor.py

# 自定义监控端口
python performance_monitor.py --ports 5030 5031 5032 5033
```

## 🗑️ 已清理的过时文件

以下文件已被删除，因为它们功能重复或者不适合Windows环境：

### 删除的启动脚本
- ~~`start_gunicorn.bat`~~ - Gunicorn Windows兼容性差
- ~~`start_production.bat`~~ - 简单配置，已被新方案替代
- ~~`start_uvicorn_advanced.bat`~~ - Uvicorn不如Waitress适合Windows
- ~~`start_uvicorn_dev.bat`~~ - 开发环境配置，已过时
- ~~`start_uvicorn.bat`~~ - 基础配置，已过时
- ~~`start_waitress.bat`~~ - 简单配置，已被高性能版本替代
- ~~`start_windows.bat`~~ - 功能有限的兼容性配置

### 删除的配置文件
- ~~`gunicorn.conf.py`~~ - Gunicorn配置，Windows兼容性差
- ~~`uvicorn.conf.py`~~ - Uvicorn配置，已不需要
- ~~`waitress_server.py`~~ - 简单Waitress配置，已被高性能版本替代

### 删除的文档
- ~~`UVICORN_DEPLOYMENT.md`~~ - Uvicorn部署文档，已不适用

## 🌟 新方案优势

1. **高性能**: Waitress + 多线程 + 连接池
2. **高可用**: 自动重启 + 负载均衡 + 健康检查  
3. **易管理**: Windows服务 + 性能监控 + 一键部署
4. **生产就绪**: 完整的企业级部署解决方案

## 📝 注意事项

- 所有新的部署方案都经过Windows Server优化
- 推荐使用 `deploy_production.bat` 进行首次部署
- 生产环境建议配合Nginx负载均衡使用
- 定期运行性能监控工具检查系统状态

---
*最后更新: 2025-01-29*
*版本: 2.0 (Windows Server 优化版)*
