# 用户反馈系统

这是一个独立的、通用的用户反馈收集系统，可以轻松移植到任何项目中。

## 功能特性

### 核心功能
- ✅ 反馈创建、编辑、删除
- ✅ 文件上传（图片、文档、压缩包）
- ✅ 屏幕截图和剪贴板粘贴
- ✅ 用户投票（支持/反对）
- ✅ 评论系统
- ✅ 统计信息

### 分类系统
- **反馈类型**: 功能建议 / 问题反馈
- **相关模块**: 前端 / 后端
- **修改类型**: 界面优化 / 代码修改
- **优先级**: 低 / 中 / 高 / 紧急
- **处理状态**: 待处理 / 处理中 / 已解决 / 已关闭

### 筛选功能
- 按分类、模块、类型、状态、优先级筛选
- 关键词搜索
- 个人反馈筛选
- 多种排序方式（时间、支持数、反对数、评论数、浏览数）

## 技术架构

### 后端技术栈
- Python + Flask
- MySQL 数据库
- 雪花算法 ID 生成
- 文件上传处理
- RESTful API 设计

### 前端技术栈
- Vue 3 + Composition API
- Element Plus UI 框架
- Axios HTTP 客户端
- 响应式设计

## 安装配置

### 1. 数据库配置

执行 SQL 脚本创建数据库表：

```sql
-- 执行 db_schema.sql 创建表结构
mysql -u root -p your_database < backend/feedback/db_schema.sql
```

### 2. 后端配置

在主应用中注册反馈系统蓝图：

```python
# app.py
from feedback.feedback_routes import feedback_bp

app.register_blueprint(feedback_bp)
```

### 3. 前端配置

在前端路由中添加反馈页面：

```javascript
// router/index.js
import FeedbackView from '@/feedback/views/FeedbackView.vue'

const routes = [
  {
    path: '/feedback',
    name: 'Feedback',
    component: FeedbackView,
    meta: {
      title: '用户反馈'
    }
  }
]
```

## API 接口

### 反馈管理
- `GET /api/feedback/items` - 获取反馈列表
- `POST /api/feedback/items` - 创建反馈
- `GET /api/feedback/items/:id` - 获取反馈详情
- `DELETE /api/feedback/items/:id` - 删除反馈

### 附件管理
- `POST /api/feedback/items/:id/attachments` - 上传附件
- `GET /api/feedback/attachments/:filename` - 下载附件

### 互动功能
- `POST /api/feedback/items/:id/comments` - 添加评论
- `POST /api/feedback/items/:id/vote` - 投票

### 统计信息
- `GET /api/feedback/stats` - 获取统计数据

## 移植指南

### 1. 用户认证适配

修改 `feedback_routes.py` 中的 `get_current_user()` 函数：

```python
def get_current_user():
    """获取当前用户信息（适配现有认证系统）"""
    # 替换为您的认证系统
    return your_auth_system.get_current_user()
```

### 2. 数据库适配

如果使用不同的数据库系统，修改 `db_schema.sql` 中的语法。

### 3. 文件存储适配

修改 `FeedbackService` 类中的文件上传逻辑，支持云存储等。

### 4. 前端集成

将 `frontend/src/feedback` 文件夹复制到目标项目中，并根据需要调整样式和组件。

## 配置选项

### 后端配置

```python
# feedback_service.py
class FeedbackService:
    def __init__(self, upload_folder='feedback_uploads'):
        self.upload_folder = upload_folder
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        # 可根据需要调整
```

### 前端配置

```javascript
// api/feedbackApi.js
const feedbackApi = createFeedbackApi('/api/feedback', authToken)
```

## 权限控制

### 后端权限
- 只有反馈创建者可以删除自己的反馈
- 管理员可以更新反馈状态（可扩展）
- 所有登录用户可以查看、评论、投票

### 前端权限
- 根据用户 ID 控制编辑/删除按钮显示
- 未登录用户提示登录

## 数据库设计

### 核心表结构
- `feedback_items` - 反馈主表
- `feedback_attachments` - 附件表
- `feedback_votes` - 投票表
- `feedback_comments` - 评论表

### 索引优化
- 按分类、状态、用户等字段建立索引
- 支持高效的筛选和排序查询

## 最佳实践

### 1. 性能优化
- 使用分页查询避免大数据量问题
- 文件上传大小限制
- 数据库查询优化

### 2. 用户体验
- 响应式设计适配移动端
- 实时表单验证
- 友好的错误提示

### 3. 安全考虑
- 文件类型验证
- SQL 注入防护
- 权限验证

## 扩展功能

### 可扩展特性
- [ ] 邮件通知
- [ ] 微信通知
- [ ] 反馈标签系统
- [ ] 工作流状态管理
- [ ] 反馈合并功能
- [ ] 批量操作
- [ ] 导出功能
- [ ] API 接口文档

### 自定义配置
- 反馈分类可自定义
- 状态流转可配置
- 通知方式可扩展

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查上传目录权限
   - 确认文件大小限制
   - 验证文件类型设置

2. **权限错误**
   - 检查用户认证集成
   - 确认 ID 字段类型匹配

3. **数据库连接问题**
   - 验证数据库配置
   - 检查表结构是否正确创建

## 维护指南

### 定期维护
- 清理过期附件文件
- 数据库性能监控
- 日志分析

### 升级注意事项
- 数据库迁移脚本
- API 版本兼容性
- 前端依赖更新

## 许可证

本项目采用 MIT 许可证，可自由使用、修改和分发。

## 技术支持

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 邮件联系
- 在线文档

---

**注意**: 本系统设计为通用组件，在具体项目中使用时需要根据实际需求进行适配和配置。 