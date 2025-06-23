<template>
  <div class="feedback-view" v-loading="loading">
    <!-- 页面头部 -->
    <div class="feedback-header">
      <div class="header-title">
        <h1>用户反馈中心</h1>
        <p>帮助我们创造更好的产品体验</p>
      </div>
      <div class="header-actions">        
        
        <el-button 
          type="primary" 
          @click="showCreateDialog = true"
        >
          提交反馈
        </el-button>
        <el-button 
          type="info" 
          @click="showStatsDialog = true"
        >
          统计信息
        </el-button>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="feedback-filters">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable>
            <el-option label="功能建议" value="feature" />
            <el-option label="问题反馈" value="bug" />
            <el-option label="其他" value="othercategory" />
          </el-select>
        </el-form-item>

        <el-form-item label="模块">
          <el-select 
            v-model="filters.module" 
            placeholder="全部模块" 
            clearable
            filterable
            allow-create
            default-first-option
          >
            <el-option label="前端" value="frontend" />
            <el-option label="后端" value="backend" />
            <el-option label="数据库" value="database" />
            <el-option label="API" value="api" />
            <el-option label="部署" value="deployment" />
            <el-option label="文档" value="documentation" />
            <el-option label="其他" value="othermodule" />
          </el-select>
        </el-form-item>

        <el-form-item label="类型">
          <el-select 
            v-model="filters.type" 
            placeholder="全部类型" 
            clearable
            filterable
            allow-create
            default-first-option
          >
            <el-option label="界面优化" value="ui" />
            <el-option label="代码修改" value="code" />
            <el-option label="性能优化" value="performance" />
            <el-option label="功能新增" value="feature" />
            <el-option label="架构调整" value="architecture" />
            <el-option label="安全修复" value="security" />
            <el-option label="其他" value="othertype" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="待处理" value="open" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>

        <el-form-item label="排序">
          <el-select v-model="sortBy" placeholder="排序方式">
            <el-option label="最新创建" value="created_at" />
            <el-option label="最近更新" value="updated_at" />
            <el-option label="最多支持" value="support_count" />
            <el-option label="最多反对" value="oppose_count" />
            <el-option label="最多评论" value="comment_count" />
            <el-option label="最多浏览" value="view_count" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-input 
            v-model="filters.keyword" 
            placeholder="🔍 搜索关键词..."
            clearable
            style="width: 200px"
            @keyup.enter="loadFeedbackList"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="filters.my_feedback">仅显示我的反馈</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadFeedbackList">
            🔍 搜索
          </el-button>
          <el-button @click="resetFilters">
            🔄 重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 反馈列表 -->
    <div class="feedback-list">
      <el-card 
        v-for="item in feedbackList" 
        :key="item.id" 
        class="feedback-card"
        shadow="hover"
      >
        <div class="feedback-item">
          <div class="feedback-title-row">
            <h3 class="feedback-title">
              <a 
                href="javascript:void(0)" 
                class="title-link"
                @click="openFeedbackDetail(item)"
              >
                {{ item.title }}
              </a>
            </h3>
            <div class="feedback-badges">
              <el-tag 
                :type="getCategoryTagType(item.category)" 
                size="small"
              >
                {{ getCategoryLabel(item.category) }}
              </el-tag>
              <el-tag 
                :type="getModuleTagType(item.module)" 
                size="small"
              >
                {{ getModuleLabel(item.module) }}
              </el-tag>
              <el-tag 
                :type="getTypeTagType(item.type)" 
                size="small"
              >
                {{ getTypeLabel(item.type) }}
              </el-tag>
              <el-tag 
                :type="getStatusTagType(item.status)" 
                size="small"
              >
                {{ getStatusLabel(item.status) }}
              </el-tag>
              <el-tag 
                :type="getPriorityTagType(item.priority)" 
                size="small"
              >
                {{ getPriorityLabel(item.priority) }}
              </el-tag>
            </div>
          </div>

          <div class="feedback-description">
            {{ item.description || '暂无详细描述' }}
          </div>

          <div class="feedback-meta">
            <div class="meta-left">
              <span class="meta-item">
                👤 {{ item.username || '匿名用户' }}
              </span>
              <span class="meta-item">
                🕒 {{ formatTime(item.created_at) }}
              </span>
              <span v-if="item.has_attachments" class="meta-item">
                📎 有附件
              </span>
            </div>
            
            <div class="meta-right">
              <!-- 可点击的点赞/反对按钮 -->
              <el-button 
                v-if="currentUser"
                text 
                size="small"
                :type="item.user_vote === 'support' ? 'success' : 'info'"
                @click.stop="voteFeedback(item, 'support')"
                class="vote-btn"
              >
                👍 {{ item.support_count || 0 }}
              </el-button>
              <span v-else class="meta-item support">
                👍 {{ item.support_count || 0 }}
              </span>
              
              <el-button 
                v-if="currentUser"
                text 
                size="small"
                :type="item.user_vote === 'oppose' ? 'danger' : 'info'"
                @click.stop="voteFeedback(item, 'oppose')"
                class="vote-btn"
              >
                👎 {{ item.oppose_count || 0 }}
              </el-button>
              <span v-else class="meta-item oppose">
                👎 {{ item.oppose_count || 0 }}
              </span>
              
              <span class="meta-item comment">
                💬 {{ item.comment_count || 0 }}
              </span>
              <span class="meta-item view">
                👁️ {{ item.view_count || 0 }}
              </span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && feedbackList.length === 0" 
        description="暂无反馈数据"
      >
        <el-button type="primary" @click="showCreateDialog = true">
          提交第一个反馈
        </el-button>
      </el-empty>
    </div>

    <!-- 分页 -->
    <div class="feedback-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadFeedbackList"
        @current-change="loadFeedbackList"
      />
    </div>

    <!-- 创建反馈对话框 -->
    <create-feedback-dialog 
      v-model="showCreateDialog"
      @success="onCreateSuccess"
    />

    <!-- 反馈详情对话框 -->
    <feedback-detail-dialog 
      v-model="showDetailDialog"
      :feedback-id="selectedFeedbackId"
      @refresh="loadFeedbackList"
    />

    <!-- 统计信息对话框 -->
    <feedback-stats-dialog 
      v-model="showStatsDialog"
    />

  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import feedbackApi from '../api/feedbackApi'
import CreateFeedbackDialog from '../components/CreateFeedbackDialog.vue'
import FeedbackDetailDialog from '../components/FeedbackDetailDialog.vue'
import FeedbackStatsDialog from '../components/FeedbackStatsDialog.vue'

export default {
  name: 'FeedbackView',
  components: {
    CreateFeedbackDialog,
    FeedbackDetailDialog,
    FeedbackStatsDialog
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const feedbackList = ref([])
    const showCreateDialog = ref(false)
    const showDetailDialog = ref(false)
    const showStatsDialog = ref(false)
    const selectedFeedbackId = ref(null)
    const sortBy = ref('created_at')

    // 筛选条件
    const filters = reactive({
      category: '',
      module: '',
      type: '',
      status: '',
      priority: '',
      keyword: '',
      my_feedback: false
    })

    // 分页信息
    const pagination = reactive({
      page: 1,
      page_size: 20,
      total: 0
    })

    // 当前用户信息
    const currentUser = computed(() => {
      try {
        // 按优先级尝试不同的key，user_info是authService中使用的key
        const userStr = localStorage.getItem('user_info') ||
                       localStorage.getItem('user') ||
                       localStorage.getItem('currentUser') ||
                       localStorage.getItem('userInfo')
        
        return userStr ? JSON.parse(userStr) : null
      } catch (error) {
        console.error('解析用户信息失败:', error)
        return null
      }
    })

    // 判断是否为管理员
    const isAdmin = computed(() => {
      if (!currentUser.value) {
        return false
      }
      
      const user = currentUser.value
      return (
        user.username === 'admin' || 
        user.role === 'admin' ||
        user.is_admin === true ||
        user.is_admin === 'true' ||
        String(user.username).toLowerCase() === 'admin'
      )
    })

    // 加载反馈列表
    const loadFeedbackList = async () => {
      try {
        loading.value = true
        
        const params = {
          page: pagination.page,
          page_size: pagination.page_size,
          sort_by: sortBy.value,
          sort_order: 'desc',
          ...filters
        }

        // 清理空值参数
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null || params[key] === undefined) {
            delete params[key]
          }
        })

        const response = await feedbackApi.getFeedbackList(params)
        
        if (response.code === 200) {
          const items = response.data.items || []
          // 为每个反馈项初始化投票状态
          feedbackList.value = items.map(item => ({
            ...item,
            user_vote: item.user_vote || null // 用户投票状态
          }))
          pagination.total = response.data.pagination?.total || 0
        } else {
          throw new Error(response.message || '获取数据失败')
        }
      } catch (error) {
        console.error('加载反馈列表失败:', error)
        ElMessage.error(error.message || '加载数据失败')
        feedbackList.value = []
      } finally {
        loading.value = false
      }
    }

    // 重置筛选条件
    const resetFilters = () => {
      Object.keys(filters).forEach(key => {
        if (typeof filters[key] === 'boolean') {
          filters[key] = false
        } else {
          filters[key] = ''
        }
      })
      sortBy.value = 'created_at'
      pagination.page = 1
      loadFeedbackList()
    }

    // 打开反馈详情
    const openFeedbackDetail = (item) => {
      selectedFeedbackId.value = item.id
      showDetailDialog.value = true
    }





    // 投票功能
    const voteFeedback = async (item, voteType) => {
      if (!currentUser.value) {
        ElMessage.warning('请先登录')
        return
      }

      try {
        const response = await feedbackApi.voteFeedback(item.id, voteType)
        
        if (response.code === 200) {
          ElMessage.success(response.message)
          // 重新加载列表以更新投票数据
          loadFeedbackList()
        } else {
          throw new Error(response.message || '投票失败')
        }
      } catch (error) {
        console.error('投票失败:', error)
        ElMessage.error(error.message || '投票失败')
      }
    }

    // 创建成功回调
    const onCreateSuccess = () => {
      loadFeedbackList()
    }



    // 标签样式辅助函数
    const getCategoryTagType = (category) => {
      const types = { feature: 'success', bug: 'danger', othercategory: 'info' }
      return types[category] || 'info'
    }

    const getModuleTagType = (module) => {
      const types = { 
        frontend: 'primary', 
        backend: 'warning', 
        database: 'success',
        api: 'info',
        deployment: 'danger',
        documentation: 'purple',
        othermodule: 'info'
      }
      return types[module] || 'info'
    }

    const getTypeTagType = (type) => {
      const types = { 
        ui: 'primary', 
        code: 'warning',
        performance: 'success',
        feature: 'primary',
        architecture: 'info',
        security: 'danger',
        othertype: 'info'
      }
      return types[type] || 'info'
    }

    const getStatusTagType = (status) => {
      const types = { 
        open: 'info', 
        in_progress: 'warning', 
        resolved: 'success', 
        closed: 'info' 
      }
      return types[status] || 'info'
    }

    const getPriorityTagType = (priority) => {
      const types = { 
        low: 'info', 
        medium: 'warning', 
        high: 'danger', 
        urgent: 'danger' 
      }
      return types[priority] || 'info'
    }

    // 标签文本辅助函数
    const getCategoryLabel = (category) => {
      const labels = { feature: '功能建议', bug: '问题反馈', othercategory: '其他' }
      return labels[category] || category
    }

    const getModuleLabel = (module) => {
      const labels = { 
        frontend: '前端', 
        backend: '后端',
        database: '数据库',
        api: 'API',
        deployment: '部署',
        documentation: '文档',
        othermodule: '其他'
      }
      return labels[module] || module
    }

    const getTypeLabel = (type) => {
      const labels = { 
        ui: '界面优化', 
        code: '代码修改',
        performance: '性能优化',
        feature: '功能新增',
        architecture: '架构调整',
        security: '安全修复',
        othertype: '其他'
      }
      return labels[type] || type
    }

    const getStatusLabel = (status) => {
      const labels = { 
        open: '待处理', 
        in_progress: '处理中', 
        resolved: '已解决', 
        closed: '已关闭' 
      }
      return labels[status] || status
    }

    const getPriorityLabel = (priority) => {
      const labels = { 
        low: '低', 
        medium: '中', 
        high: '高', 
        urgent: '紧急' 
      }
      return labels[priority] || priority
    }

    // 时间格式化
    const formatTime = (timeStr) => {
      if (!timeStr) return ''
      const date = new Date(timeStr)
      const now = new Date()
      const diff = now - date
      
      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
      
      return date.toLocaleDateString()
    }

    // 生命周期
    onMounted(() => {
      loadFeedbackList()
    })

    return {
      // 数据
      loading,
      feedbackList,
      showCreateDialog,
      showDetailDialog,
      showStatsDialog,
      selectedFeedbackId,
      filters,
      pagination,
      sortBy,
      currentUser,
      isAdmin,

      // 方法
      loadFeedbackList,
      resetFilters,
      openFeedbackDetail,
      voteFeedback,
      onCreateSuccess,

      // 辅助函数
      getCategoryTagType,
      getModuleTagType,
      getTypeTagType,
      getStatusTagType,
      getPriorityTagType,
      getCategoryLabel,
      getModuleLabel,
      getTypeLabel,
      getStatusLabel,
      getPriorityLabel,
      formatTime
    }
  }
}
</script>

<style scoped>
.feedback-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.header-title h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.header-title p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
}

.feedback-filters {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-form .el-form-item {
  margin-bottom: 0;
  margin-right: 20px;
}

.filter-form .el-form-item:last-child {
  margin-right: 0;
}

.filter-form .el-form-item .el-form-item__label {
  font-weight: 500;
  color: #606266;
  width: auto !important;
  margin-right: 8px;
}

/* 筛选控件宽度设置 */
.filter-form .el-select {
  width: 150px;
  min-width: 120px;
}

.filter-form .el-input {
  width: 200px;
  min-width: 160px;
}

/* 支持自定义输入的选择框样式 */
.filter-form .el-select.is-filterable .el-input .el-input__wrapper {
  border-color: #dcdfe6;
  transition: border-color 0.2s ease;
}

.filter-form .el-select.is-filterable:hover .el-input .el-input__wrapper {
  border-color: #c0c4cc;
}

.filter-form .el-select.is-filterable.is-focus .el-input .el-input__wrapper {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 排序选择框需要更宽一点 */
.filter-form .el-form-item:nth-child(5) .el-select {
  width: 180px;
}

/* 搜索输入框特殊宽度 */
.filter-form .el-input[placeholder*="搜索"] {
  width: 240px;
  min-width: 200px;
}

/* 表单项间距已在上面定义 */

.feedback-list {
  margin-bottom: 24px;
}

.feedback-card {
  margin-bottom: 16px;
  cursor: default;
  transition: all 0.3s ease;
}

.feedback-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.feedback-item {
  display: block;
  width: 100%;
}

.feedback-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.feedback-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  flex: 1;
  margin-right: 16px;
}

.title-link {
  color: #303133;
  text-decoration: none;
  transition: color 0.3s ease;
}

.title-link:hover {
  color: #409eff;
  text-decoration: underline;
}

.feedback-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.feedback-description {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.feedback-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.meta-left,
.meta-right {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item.support {
  color: #67c23a;
}

.meta-item.oppose {
  color: #f56c6c;
}

.meta-item.comment {
  color: #409eff;
}

.meta-item.view {
  color: #909399;
}



.vote-btn {
  font-size: 12px;
  padding: 0 4px;
  height: auto;
  margin: 0 2px;
}

.vote-btn:hover {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}

.vote-btn.is-type-success {
  color: #67c23a;
}

.vote-btn.is-type-danger {
  color: #f56c6c;
}

.feedback-pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .feedback-view {
    padding: 16px;
  }
  
  .feedback-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .filter-form {
    flex-direction: column;
  }
  
  /* 移动端控件宽度调整 */
  .filter-form .el-select,
  .filter-form .el-input {
    width: 100% !important;
    max-width: 300px;
  }
  
  .feedback-title-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .feedback-badges {
    align-self: flex-start;
  }
  
  .feedback-meta {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .feedback-item {
    display: block;
  }
}
</style> 