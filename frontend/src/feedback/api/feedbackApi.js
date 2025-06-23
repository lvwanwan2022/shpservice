/**
 * 反馈系统API模块
 * 独立可移植的反馈收集系统前端API
 */

import { authHttp } from '@/auth/authService'

// 反馈API基础路径
const FEEDBACK_BASE_PATH = '/feedback'

/**
 * 反馈系统API服务
 */
const feedbackApi = {
  /**
   * 获取反馈列表
   */
  async getFeedbackList(params = {}) {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items`,
      method: 'get',
      params
    })
    return response.data
  },

  /**
   * 创建反馈
   */
  async createFeedback(data) {
    try {
      const response = await authHttp({
        url: `${FEEDBACK_BASE_PATH}/items`,
        method: 'post',
        data
      })
      return response.data
    } catch (error) {
      console.error('创建反馈失败:', error)
      
      // 如果是401错误，不要让authHttp自动登出
      if (error.response?.status === 401) {
        console.error('401错误详情:', {
          url: error.config?.url,
          headers: error.config?.headers,
          data: error.response?.data
        })
        throw new Error('用户认证失败，请重新登录')
      }
      
      // 如果是400错误，显示具体的错误信息
      if (error.response?.status === 400) {
        console.error('400错误详情:', {
          url: error.config?.url,
          data: error.response?.data,
          requestData: error.config?.data
        })
        const errorMessage = error.response?.data?.message || '请求参数错误'
        throw new Error(errorMessage)
      }
      
      throw error
    }
  },

  /**
   * 获取反馈详情
   */
  async getFeedbackDetail(feedbackId) {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items/${feedbackId}`,
      method: 'get'
    })
    return response.data
  },

  /**
   * 删除反馈
   */
  async deleteFeedback(feedbackId) {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items/${feedbackId}`,
      method: 'delete'
    })
    return response.data
  },

  /**
   * 上传附件
   */
  async uploadAttachment(feedbackId, file, isScreenshot = false) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_screenshot', isScreenshot)

    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items/${feedbackId}/attachments`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 添加评论
   */
  async addComment(feedbackId, content, parentId = null) {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items/${feedbackId}/comments`,
      method: 'post',
      data: {
        content,
        parent_id: parentId
      }
    })
    return response.data
  },

  /**
   * 投票
   */
  async voteFeedback(feedbackId, voteType) {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items/${feedbackId}/vote`,
      method: 'post',
      data: {
        vote_type: voteType
      }
    })
    return response.data
  },

  /**
   * 更新反馈状态
   */
  async updateFeedbackStatus(feedbackId, status) {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/items/${feedbackId}/status`,
      method: 'put',
      data: {
        status
      }
    })
    return response.data
  },

  /**
   * 获取统计信息
   */
  async getFeedbackStats() {
    const response = await authHttp({
      url: `${FEEDBACK_BASE_PATH}/stats`,
      method: 'get'
    })
    return response.data
  },

  /**
   * 下载附件
   */
  downloadAttachment(filename) {
    // 对于下载链接，我们直接返回URL，因为浏览器会自动处理认证
    return `${process.env.VUE_APP_BASE_API || '/api'}${FEEDBACK_BASE_PATH}/attachments/${filename}`
  }
}

/**
 * 创建自定义的反馈API实例（可移植性）
 * @param {string} _baseURL 自定义基础URL（已弃用）
 * @param {string} _authToken 自定义认证token（已弃用）
 * @returns {object} 反馈API实例
 */
// eslint-disable-next-line no-unused-vars
export const createFeedbackApi = (_baseURL = '/api/feedback', _authToken = null) => {
  // 如果需要自定义配置，可以创建新的axios实例
  console.warn('createFeedbackApi已弃用，请直接使用feedbackApi默认实例')
  return feedbackApi
}

export default feedbackApi 