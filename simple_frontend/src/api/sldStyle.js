import axios from 'axios'

// 创建axios实例
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API || '/api',
  timeout: 300000,
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// SLD样式管理API
export const sldStyleApi = {
  // 初始化数据库
  initializeDatabase() {
    return service({
      url: '/sld-styles/initialize',
      method: 'post'
    })
  },

  // 上传SLD文件
  uploadSldFile(data) {
    return service({
      url: '/sld-styles/upload',
      method: 'post',
      data,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取SLD样式列表
  getSldStyles(params) {
    return service({
      url: '/sld-styles',
      method: 'get',
      params
    })
  },

  // 获取SLD样式详情
  getSldStyle(styleId) {
    return service({
      url: `/sld-styles/${styleId}`,
      method: 'get'
    })
  },

  // 获取SLD样式文件内容
  getSldStyleContent(styleId) {
    return service({
      url: `/sld-styles/${styleId}/content`,
      method: 'get'
    })
  },

  // 更新SLD样式文件内容
  updateSldStyleContent(styleId, data) {
    return service({
      url: `/sld-styles/${styleId}/content`,
      method: 'put',
      data
    })
  },

  // 下载SLD文件
  downloadSldFile(styleId) {
    return service({
      url: `/sld-styles/${styleId}/download`,
      method: 'get',
      responseType: 'blob'
    })
  },

  // 删除SLD样式
  deleteSldStyle(styleId) {
    return service({
      url: `/sld-styles/${styleId}`,
      method: 'delete'
    })
  },

  // 更新SLD样式
  updateSldStyle(styleId, data) {
    return service({
      url: `/sld-styles/${styleId}`,
      method: 'put',
      data
    })
  },

  // 应用SLD样式到图层
  applySldStyleToLayer(data) {
    return service({
      url: '/sld-styles/apply',
      method: 'post',
      data
    })
  },

  // 获取图层的当前SLD样式
  getLayerSldStyle(layerId) {
    return service({
      url: `/sld-styles/layer/${layerId}`,
      method: 'get'
    })
  },

  // 移除图层的SLD样式
  removeLayerSldStyle(layerId) {
    return service({
      url: `/sld-styles/layer/${layerId}/remove`,
      method: 'post'
    })
  }
}
