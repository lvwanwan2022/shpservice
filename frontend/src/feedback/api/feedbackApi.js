/**
 * 反馈系统API模块
 * 独立可移植的反馈收集系统前端API
 */

import axios from 'axios'

// 创建专用的axios实例
const createFeedbackApi = (baseURL = '/api/feedback', authToken = null) => {
  const instance = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // 请求拦截器 - 自动添加token
  instance.interceptors.request.use(
    config => {
      // 优先使用传入的token，否则从localStorage获取
      const token = authToken || localStorage.getItem('auth_token')
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
      return config
    },
    error => Promise.reject(error)
  )

  // 响应拦截器 - 统一处理响应格式
  instance.interceptors.response.use(
    response => {
      // 如果后端返回标准格式，直接返回data部分
      if (response.data && typeof response.data.code !== 'undefined') {
        return response.data
      }
      return response.data
    },
    error => {
      // 统一错误处理
      const errorMessage = error.response?.data?.message || error.message || '网络错误'
      return Promise.reject(new Error(errorMessage))
    }
  )

  return {
    /**
     * 获取反馈列表
     */
    getFeedbackList(params = {}) {
      return instance.get('/items', { params })
    },

    /**
     * 创建反馈
     */
    createFeedback(data) {
      return instance.post('/items', data)
    },

    /**
     * 获取反馈详情
     */
    getFeedbackDetail(feedbackId) {
      return instance.get(`/items/${feedbackId}`)
    },

    /**
     * 删除反馈
     */
    deleteFeedback(feedbackId) {
      return instance.delete(`/items/${feedbackId}`)
    },

    /**
     * 上传附件
     */
    uploadAttachment(feedbackId, file, isScreenshot = false) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('is_screenshot', isScreenshot)

      return instance.post(`/items/${feedbackId}/attachments`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    },

    /**
     * 添加评论
     */
    addComment(feedbackId, content, parentId = null) {
      return instance.post(`/items/${feedbackId}/comments`, {
        content,
        parent_id: parentId
      })
    },

    /**
     * 投票
     */
    voteFeedback(feedbackId, voteType) {
      return instance.post(`/items/${feedbackId}/vote`, {
        vote_type: voteType
      })
    },

    /**
     * 更新反馈状态
     */
    updateFeedbackStatus(feedbackId, status) {
      return instance.put(`/items/${feedbackId}/status`, {
        status
      })
    },

    /**
     * 获取统计信息
     */
    getFeedbackStats() {
      return instance.get('/stats')
    },

    /**
     * 下载附件
     */
    downloadAttachment(filename) {
      return `${baseURL}/attachments/${filename}`
    }
  }
}

// 默认实例
const feedbackApi = createFeedbackApi()

export { createFeedbackApi }
export default feedbackApi 