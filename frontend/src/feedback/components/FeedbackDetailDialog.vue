<template>
  <el-dialog
    v-model="visible"
    title="反馈详情"
    width="900px"
    :before-close="handleClose"
    class="feedback-detail-dialog"
  >
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="feedback" class="feedback-detail">
      <!-- 反馈头部信息 -->
      <div class="feedback-header">
        <div class="header-main">
          <h2 class="feedback-title">{{ feedback.title }}</h2>
          <div class="feedback-badges">
            <el-tag :type="getCategoryTagType(feedback.category)" size="default">
              {{ getCategoryLabel(feedback.category) }}
            </el-tag>
            <el-tag :type="getModuleTagType(feedback.module)" size="default">
              {{ getModuleLabel(feedback.module) }}
            </el-tag>
            <el-tag :type="getTypeTagType(feedback.type)" size="default">
              {{ getTypeLabel(feedback.type) }}
            </el-tag>
            <el-tag :type="getStatusTagType(feedback.status)" size="default">
              {{ getStatusLabel(feedback.status) }}
            </el-tag>
            <el-tag :type="getPriorityTagType(feedback.priority)" size="default">
              {{ getPriorityLabel(feedback.priority) }}
            </el-tag>
          </div>
        </div>
        
        <div class="header-actions">
          <el-button-group>
            <el-button
              :type="feedback.user_vote === 'support' ? 'success' : 'default'"
              :icon="Like"
              @click="voteFeedback('support')"
            >
              {{ feedback.support_count || 0 }}
            </el-button>
            <el-button
              :type="feedback.user_vote === 'oppose' ? 'danger' : 'default'"
              :icon="DisLike"
              @click="voteFeedback('oppose')"
            >
              {{ feedback.oppose_count || 0 }}
            </el-button>
          </el-button-group>
        </div>
      </div>

      <!-- 反馈元信息 -->
      <div class="feedback-meta">
        <div class="meta-item">
          <el-icon><User /></el-icon>
          <span>{{ feedback.username || '匿名用户' }}</span>
        </div>
        <div class="meta-item">
          <el-icon><Clock /></el-icon>
          <span>{{ formatTime(feedback.created_at) }}</span>
        </div>
        <div class="meta-item">
          <el-icon><View /></el-icon>
          <span>{{ feedback.view_count || 0 }} 次浏览</span>
        </div>
        <div class="meta-item">
          <el-icon><ChatDotRound /></el-icon>
          <span>{{ feedback.comment_count || 0 }} 条评论</span>
        </div>
      </div>

      <!-- 反馈内容 -->
      <div class="feedback-content">
        <h3>详细描述</h3>
        <div class="description-content">
          {{ feedback.description || '暂无详细描述' }}
        </div>
      </div>

      <!-- 附件列表 -->
      <div v-if="feedback.attachments && feedback.attachments.length > 0" class="feedback-attachments">
        <h3>附件</h3>
        <div class="attachment-list">
          <div
            v-for="attachment in feedback.attachments"
            :key="attachment.id"
            class="attachment-item"
            @click="downloadAttachment(attachment)"
          >
            <el-icon class="attachment-icon">
              <Picture v-if="attachment.file_type === 'image'" />
              <Document v-else-if="attachment.file_type === 'document'" />
              <Folder v-else />
            </el-icon>
            <div class="attachment-info">
              <div class="attachment-name">{{ attachment.original_name }}</div>
              <div class="attachment-meta">
                {{ formatFileSize(attachment.file_size) }}
                <span v-if="attachment.is_screenshot" class="screenshot-badge">截图</span>
              </div>
            </div>
            <el-icon class="download-icon"><Download /></el-icon>
          </div>
        </div>
      </div>

      <!-- 评论区域 -->
      <div class="feedback-comments">
        <div class="comments-header">
          <h3>评论 ({{ feedback.comments?.length || 0 }})</h3>
          <el-button type="primary" size="small" @click="showCommentForm = !showCommentForm">
            <el-icon><ChatDotRound /></el-icon>
            添加评论
          </el-button>
        </div>

        <!-- 添加评论表单 -->
        <div v-if="showCommentForm" class="comment-form">
          <el-input
            v-model="newComment"
            type="textarea"
            placeholder="写下您的评论..."
            :rows="3"
            maxlength="500"
            show-word-limit
          />
          <div class="comment-actions">
            <el-button @click="cancelComment">取消</el-button>
            <el-button
              type="primary"
              :loading="commentSubmitting"
              @click="submitComment"
            >
              发表评论
            </el-button>
          </div>
        </div>

        <!-- 评论列表 -->
        <div v-if="feedback.comments && feedback.comments.length > 0" class="comment-list">
          <div
            v-for="comment in feedback.comments"
            :key="comment.id"
            class="comment-item"
          >
            <div class="comment-avatar">
              <el-avatar :size="32">
                {{ (comment.username || '匿名')[0] }}
              </el-avatar>
            </div>
            <div class="comment-content">
              <div class="comment-header">
                <span class="comment-author">{{ comment.username || '匿名用户' }}</span>
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
              </div>
              <div class="comment-text">{{ comment.content }}</div>
            </div>
          </div>
        </div>

        <el-empty v-else-if="!showCommentForm" description="暂无评论">
          <el-button type="primary" @click="showCommentForm = true">
            发表第一条评论
          </el-button>
        </el-empty>
      </div>
    </div>

    <div v-else class="error-container">
      <el-empty description="反馈不存在或已被删除" />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button
          v-if="canDeleteFeedback"
          type="danger"
          @click="deleteFeedback"
        >
          删除反馈
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Clock, View, ChatDotRound,
  Picture, Document, Folder, Download
} from '@element-plus/icons-vue'
import feedbackApi from '../api/feedbackApi'

export default {
  name: 'FeedbackDetailDialog',
  components: {
    User, Clock, View, ChatDotRound,
    Picture, Document, Folder, Download
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    feedbackId: {
      type: String,
      default: null
    }
  },
  emits: ['update:modelValue', 'refresh'],
  setup(props, { emit }) {
    const loading = ref(false)
    const feedback = ref(null)
    const showCommentForm = ref(false)
    const newComment = ref('')
    const commentSubmitting = ref(false)

    // 对话框可见性
    const visible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    // 当前用户信息
    const currentUser = computed(() => {
      try {
        const userStr = localStorage.getItem('user')
        return userStr ? JSON.parse(userStr) : null
      } catch {
        return null
      }
    })

    // 判断是否可以删除反馈
    const canDeleteFeedback = computed(() => {
      return currentUser.value && 
             feedback.value &&
             String(currentUser.value.id) === String(feedback.value.user_id)
    })

    // 监听反馈ID变化
    watch(() => props.feedbackId, (newId) => {
      if (newId && visible.value) {
        loadFeedbackDetail()
      }
    })

    // 监听对话框显示
    watch(visible, (newVisible) => {
      if (newVisible && props.feedbackId) {
        loadFeedbackDetail()
      } else if (!newVisible) {
        resetState()
      }
    })

    // 加载反馈详情
    const loadFeedbackDetail = async () => {
      if (!props.feedbackId) return

      try {
        loading.value = true
        const response = await feedbackApi.getFeedbackDetail(props.feedbackId)
        
        if (response.code === 200) {
          feedback.value = response.data
        } else {
          throw new Error(response.message || '获取详情失败')
        }
      } catch (error) {
        console.error('加载反馈详情失败:', error)
        ElMessage.error(error.message || '加载详情失败')
        feedback.value = null
      } finally {
        loading.value = false
      }
    }

    // 投票
    const voteFeedback = async (voteType) => {
      if (!currentUser.value) {
        ElMessage.warning('请先登录')
        return
      }

      try {
        const response = await feedbackApi.voteFeedback(props.feedbackId, voteType)
        
        if (response.code === 200) {
          ElMessage.success(response.message)
          // 重新加载详情
          loadFeedbackDetail()
        } else {
          throw new Error(response.message || '投票失败')
        }
      } catch (error) {
        console.error('投票失败:', error)
        ElMessage.error(error.message || '投票失败')
      }
    }

    // 提交评论
    const submitComment = async () => {
      if (!currentUser.value) {
        ElMessage.warning('请先登录')
        return
      }

      if (!newComment.value.trim()) {
        ElMessage.warning('评论内容不能为空')
        return
      }

      try {
        commentSubmitting.value = true
        const response = await feedbackApi.addComment(
          props.feedbackId,
          newComment.value.trim()
        )
        
        if (response.code === 201) {
          ElMessage.success('评论成功')
          newComment.value = ''
          showCommentForm.value = false
          // 重新加载详情
          loadFeedbackDetail()
        } else {
          throw new Error(response.message || '评论失败')
        }
      } catch (error) {
        console.error('评论失败:', error)
        ElMessage.error(error.message || '评论失败')
      } finally {
        commentSubmitting.value = false
      }
    }

    // 取消评论
    const cancelComment = () => {
      newComment.value = ''
      showCommentForm.value = false
    }

    // 下载附件
    const downloadAttachment = (attachment) => {
      const url = feedbackApi.downloadAttachment(attachment.filename)
      window.open(url, '_blank')
    }

    // 删除反馈
    const deleteFeedback = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要删除反馈"${feedback.value.title}"吗？此操作不可恢复。`,
          '确认删除',
          {
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
          }
        )

        const response = await feedbackApi.deleteFeedback(props.feedbackId)
        
        if (response.code === 200) {
          ElMessage.success('删除成功')
          emit('refresh')
          handleClose()
        } else {
          throw new Error(response.message || '删除失败')
        }
      } catch (error) {
        if (error.message !== 'cancel') {
          console.error('删除反馈失败:', error)
          ElMessage.error(error.message || '删除失败')
        }
      }
    }

    // 重置状态
    const resetState = () => {
      feedback.value = null
      showCommentForm.value = false
      newComment.value = ''
    }

    // 关闭对话框
    const handleClose = () => {
      visible.value = false
    }

    // 标签样式辅助函数
    const getCategoryTagType = (category) => {
      const types = { feature: 'success', bug: 'danger' }
      return types[category] || 'info'
    }

    const getModuleTagType = (module) => {
      const types = { frontend: 'primary', backend: 'warning' }
      return types[module] || 'info'
    }

    const getTypeTagType = (type) => {
      const types = { ui: 'primary', code: 'warning' }
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
      const labels = { feature: '功能建议', bug: '问题反馈' }
      return labels[category] || category
    }

    const getModuleLabel = (module) => {
      const labels = { frontend: '前端', backend: '后端' }
      return labels[module] || module
    }

    const getTypeLabel = (type) => {
      const labels = { ui: '界面', code: '代码' }
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

    // 文件大小格式化
    const formatFileSize = (size) => {
      if (!size) return '0 B'
      const units = ['B', 'KB', 'MB', 'GB']
      let index = 0
      while (size >= 1024 && index < units.length - 1) {
        size /= 1024
        index++
      }
      return `${size.toFixed(1)} ${units[index]}`
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

    return {
      loading,
      feedback,
      visible,
      showCommentForm,
      newComment,
      commentSubmitting,
      currentUser,
      canDeleteFeedback,

      // 方法
      loadFeedbackDetail,
      voteFeedback,
      submitComment,
      cancelComment,
      downloadAttachment,
      deleteFeedback,
      handleClose,

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
      formatFileSize,
      formatTime
    }
  }
}
</script>

<style scoped>
.feedback-detail-dialog :deep(.el-dialog__body) {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.loading-container {
  padding: 20px 0;
}

.error-container {
  padding: 40px 0;
  text-align: center;
}

.feedback-detail {
  font-size: 14px;
  line-height: 1.6;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-main {
  flex: 1;
}

.feedback-title {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.feedback-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.header-actions {
  margin-left: 20px;
}

.feedback-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  color: #909399;
  font-size: 13px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.feedback-content {
  margin-bottom: 32px;
}

.feedback-content h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.description-content {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  white-space: pre-wrap;
  line-height: 1.6;
  color: #303133;
}

.feedback-attachments {
  margin-bottom: 32px;
}

.feedback-attachments h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.attachment-item:hover {
  background: #e8f4ff;
}

.attachment-icon {
  font-size: 20px;
  color: #409eff;
}

.attachment-info {
  flex: 1;
}

.attachment-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.attachment-meta {
  font-size: 12px;
  color: #909399;
}

.screenshot-badge {
  margin-left: 8px;
  padding: 2px 6px;
  background: #e1f3d8;
  color: #67c23a;
  border-radius: 4px;
  font-size: 10px;
}

.download-icon {
  color: #409eff;
}

.feedback-comments h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.comment-form {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-avatar {
  flex-shrink: 0;
}

.comment-content {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.comment-author {
  font-weight: 500;
  color: #303133;
}

.comment-time {
  font-size: 12px;
  color: #909399;
}

.comment-text {
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .feedback-detail-dialog :deep(.el-dialog) {
    width: 95vw;
    margin: 5vh auto;
  }
  
  .feedback-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    margin-left: 0;
    align-self: flex-start;
  }
  
  .feedback-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .attachment-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .comments-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style> 