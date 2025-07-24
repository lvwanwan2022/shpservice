import axios from 'axios'
// 登录认证模块 - 一行代码实现带认证的API调用
import { authHttp } from '@/auth/authService'
//const data = await authHttp.get('/api/protected-data')

// 🔥 导入JSONbig处理大整数
//import JSONbig from 'json-bigint'

// 创建axios实例
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API || '/api',
  timeout: 300000,  // 增加超时时间到5分钟，用于处理大文件上传
  withCredentials: false,  // 不发送cookies
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    //console.log('API请求:', config.method?.toUpperCase(), config.url, config.params || config.data)
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
    //console.log('API响应:', response.status, response.config.url)
    const res = response.data
    return res
  },
  error => {
    console.error('API请求错误:', error)
    
    // 网络错误处理
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('网络连接错误，请检查：')
      console.error('1. 后端服务是否启动 (端口5030)')
      console.error('2. 前端代理配置是否正确')
      console.error('3. 防火墙是否阻止连接')
      
      // 尝试检测服务状态
      checkServiceStatus()
    }
    
    // 超时错误处理
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('请求超时，可能是服务器响应过慢')
    }
    
    return Promise.reject(error)
  }
)



// 检测服务状态
async function checkServiceStatus() {
  try {
    // 尝试直接访问后端健康检查端点
    const response = await fetch('/api/health', { 
      method: 'GET',
      timeout: 5000 
    })
    if (response.ok) {
      //console.log('✅ 后端服务正常')
    } else {
      console.error('❌ 后端服务异常:', response.status)
    }
  } catch (error) {
    console.error('❌ 无法连接到后端服务:', error.message)
    console.error('请确保：')
    console.error('- 后端服务已启动 (python app.py)')
    console.error('- 端口5030未被占用')
    console.error('- 前端开发服务器代理配置正确')
  }
}

// 允许的文件类型
const ALLOWED_FILE_TYPES = [
  '.tif', '.tiff', '.mbtiles', '.dwg', '.dxf', '.geojson', '.zip', '.shp', '.dbf', '.shx', '.prj'
]

// 文件大小检查
const checkFileSize = (file, maxSize = 500) => {
  const fileSize = file.size / 1024 / 1024 // 转换为MB
  if (fileSize > maxSize) {
    return {
      valid: false,
      message: `文件大小超过限制，最大允许${maxSize}MB，当前文件${fileSize.toFixed(2)}MB`
    }
  }
  return { valid: true }
}

// 文件类型检查
const checkFileType = (file) => {
  const fileName = file.name.toLowerCase()
  const fileExt = fileName.substring(fileName.lastIndexOf('.'))
  
  if (!ALLOWED_FILE_TYPES.includes(fileExt)) {
    return {
      valid: false,
      message: `不支持的文件类型${fileExt}，允许类型: ${ALLOWED_FILE_TYPES.join(', ')}`
    }
  }
  
  // 如果是zip文件，检查大小限制放宽
  if (fileExt === '.zip') {
    return checkFileSize(file, 500) // 允许500MB的zip文件
  }
  
  return { valid: true }
}

// GIS服务API
export default {
  // ========== 文件管理 ==========
  
  // 上传文件
  uploadFile(formData, onProgress) {
    const file = formData.get('file')
    
    if (file) {
      // 文件类型检查
      const typeCheck = checkFileType(file)
      if (!typeCheck.valid) {
        return Promise.reject(new Error(typeCheck.message))
      }
      
      // 文件大小检查 - 针对不同文件类型设置不同限制
      let maxSize = 100; // 默认100MB
      if (file.name.endsWith('.zip')) {
        maxSize = 500; // ZIP文件500MB
      } else if (file.name.toLowerCase().endsWith('.tif') || file.name.toLowerCase().endsWith('.tiff') || file.name.toLowerCase().endsWith('.mbtiles')) {
        maxSize = 50000; // TIF和MBTiles文件允许50GB
      }
      
      // 检查文件类型与表单选择是否匹配
      const formFileType = formData.get('file_type');
      if (formFileType) {
        if (file.name.toLowerCase().endsWith('.mbtiles') && 
            !['vector.mbtiles', 'raster.mbtiles'].includes(formFileType)) {
          return Promise.reject(new Error('MBTiles文件必须选择正确的类型：vector.mbtiles(矢量瓦片)或raster.mbtiles(栅格瓦片)'))
        }
      }
      
      const sizeCheck = checkFileSize(file, maxSize)
      if (!sizeCheck.valid) {
        return Promise.reject(new Error(sizeCheck.message))
      }
      
      //console.log(`开始上传文件: ${file.name}, 大小: ${(file.size/1024/1024).toFixed(2)}MB`)
      
      // 对于大文件（>500MB）使用分片上传
      const fileSizeMB = file.size / 1024 / 1024
      if (fileSizeMB > 500) {
        //console.log('文件较大，使用分片上传模式')
        return this.uploadFileChunked(formData, onProgress)
      }
    }
    
    // 根据文件大小动态设置超时时间
    const fileSizeMB = file ? file.size / 1024 / 1024 : 0
    let timeout = 600000 // 默认10分钟
    if (fileSizeMB > 1000) { // 大于1GB
      timeout = 1800000 // 30分钟
    } else if (fileSizeMB > 500) { // 大于500MB
      timeout = 1200000 // 20分钟
    }
    
    // 使用带认证的axios实例进行文件上传
    return authHttp({
      url: '/files/upload',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: timeout,
      onUploadProgress: progressEvent => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        //console.log('上传进度:', percentCompleted, '%')
        if (onProgress && typeof onProgress === 'function') {
          onProgress(percentCompleted)
        }
      }
    })
  },
  
  // 分片上传文件
  async uploadFileChunked(formData, onProgress) {
    const file = formData.get('file')
    const chunkSize = 10 * 1024 * 1024 // 10MB每片
    const totalChunks = Math.ceil(file.size / chunkSize)
    const uploadId = Date.now().toString() + '_' + Math.random().toString(36).substr(2, 9)
    
    //console.log(`分片上传开始: ${file.name}, 总大小: ${(file.size/1024/1024).toFixed(2)}MB, 分片数: ${totalChunks}`)
    
    try {
      // 1. 初始化分片上传
      if (onProgress) onProgress(1)
      await this.initChunkedUpload(uploadId, file.name, totalChunks, formData)
      
      // 2. 上传每个分片
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * chunkSize
        const end = Math.min(start + chunkSize, file.size)
        const chunk = file.slice(start, end)
        
        let retryCount = 0
        const maxRetries = 3
        
        while (retryCount < maxRetries) {
          try {
            //console.log(`上传分片 ${chunkIndex + 1}/${totalChunks}, 大小: ${(chunk.size/1024/1024).toFixed(2)}MB`)
            
            await this.uploadChunk(uploadId, chunkIndex, chunk)
            
            // 更新进度 (1% 给初始化，98% 给分片上传，1% 给合并)
            const progress = Math.round(1 + ((chunkIndex + 1) / totalChunks) * 98)
            if (onProgress && typeof onProgress === 'function') {
              onProgress(progress)
            }
            
            break // 成功，跳出重试循环
          } catch (error) {
            retryCount++
            console.warn(`分片 ${chunkIndex + 1} 上传失败，重试 ${retryCount}/${maxRetries}:`, error.message)
            
            if (retryCount >= maxRetries) {
              throw new Error(`分片 ${chunkIndex + 1} 上传失败，已重试 ${maxRetries} 次`)
            }
            
            // 等待后重试
            await new Promise(resolve => setTimeout(resolve, 1000 * retryCount))
          }
        }
      }
      
      // 3. 完成分片上传
      //console.log('所有分片上传完成，正在合并文件...')
      if (onProgress) onProgress(99)
      const result = await this.completeChunkedUpload(uploadId)
      if (onProgress) onProgress(100)
      //console.log('分片上传成功完成')
      return result
      
    } catch (error) {
      console.error('分片上传失败:', error)
      // 清理失败的上传
      try {
        await this.abortChunkedUpload(uploadId)
      } catch (cleanupError) {
        console.warn('清理失败的分片上传时出错:', cleanupError)
      }
      throw error
    }
  },

  // 初始化分片上传
  initChunkedUpload(uploadId, fileName, totalChunks, formData) {
    const metadata = {}
    for (let [key, value] of formData.entries()) {
      if (key !== 'file') {
        metadata[key] = value
      }
    }
    
    // 使用带认证的axios实例进行分片上传初始化
    return authHttp({
      url: '/files/upload/chunked/init',
      method: 'post',
      data: {
        upload_id: uploadId,
        file_name: fileName,
        total_chunks: totalChunks,
        metadata: metadata
      },
      timeout: 30000
    })
  },

  // 上传单个分片
  uploadChunk(uploadId, chunkIndex, chunk) {
    const chunkFormData = new FormData()
    chunkFormData.append('upload_id', uploadId)
    chunkFormData.append('chunk_index', chunkIndex)
    chunkFormData.append('chunk', chunk)
    
    // 使用带认证的axios实例上传分片
    return authHttp({
      url: '/files/upload/chunked/chunk',
      method: 'post',
      data: chunkFormData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000 // 2分钟超时，单个分片不应该太久
    })
  },

  // 完成分片上传
  completeChunkedUpload(uploadId) {
    // 使用带认证的axios实例完成分片上传
    return authHttp({
      url: '/files/upload/chunked/complete',
      method: 'post',
      data: {
        upload_id: uploadId
      },
      timeout: 300000 // 5分钟超时，合并文件可能需要时间
    })
  },

  // 取消分片上传
  abortChunkedUpload(uploadId) {
    // 使用带认证的axios实例取消分片上传
    return authHttp({
      url: '/files/upload/chunked/abort',
      method: 'post',
      data: {
        upload_id: uploadId
      },
      timeout: 30000
    })
  },
  
  // 获取文件列表
  getFiles(params = {}) {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/files/list',
      method: 'get',
      params
    })
  },
  
  // 获取文件详情
  getFile(fileId) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/files/${fileId}`,
      method: 'get'
    })
  },
  
  // 删除文件
  deleteFile(fileId) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/files/${fileId}`,
      method: 'delete'
    })
  },
  
  // 获取用户列表
  getUsers() {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/files/users',
      method: 'get'
    })
  },
  
  // 更新文件
  updateFile(fileId, data) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/files/${fileId}`,
      method: 'put',
      data
    })
  },
  
  // 获取文件统计信息
  getFileStatistics() {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/files/statistics',
      method: 'get'
    })
  },
  
  // 获取学科列表
  getDisciplines() {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/files/disciplines',
      method: 'get'
    })
  },
  
  // 获取文件类型列表
  getFileTypes() {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/files/file-types',
      method: 'get'
    })
  },
  
  // ========== 图层管理 ==========
  
  // 获取图层列表
  getLayers(params = {}) {
    return service({
      url: '/layers',
      method: 'get',
      params
    })
  },
  
  // 获取图层详情
  getLayer(layerId) {
    return service({
      url: `/layers/${layerId}`,
      method: 'get'
    })
  },
  
  // 发布图层服务
  publishLayer(fileId, params = {}) {
    return service({
      url: `/layers/publish/${fileId}`,
      method: 'post',
      data: params
    })
  },
  
  // 更新图层
  updateLayer(layerId, data) {
    return service({
      url: `/layers/${layerId}`,
      method: 'put',
      data
    })
  },
  
  // 删除图层
  deleteLayer(layerId) {
    return service({
      url: `/layers/${layerId}`,
      method: 'delete'
    })
  },
  
  // 获取图层能力信息
  getLayerCapabilities(layerId, serviceType = 'WMS') {
    return service({
      url: `/layers/${layerId}/capabilities`,
      method: 'get',
      params: { service_type: serviceType }
    })
  },
  
  // 获取图层预览
  getLayerPreview(layerId, bbox, width = 512, height = 512, srs = 'EPSG:4326') {
    return service({
      url: `/layers/${layerId}/preview`,
      method: 'get',
      params: { bbox, width, height, srs }
    })
  },
  
  // 获取图层边界信息
  getSceneLayerBounds(scenelayerId) {
    return service({
      url: `/layers/${scenelayerId}/scenelayerbounds`,
      method: 'get'
    })
  },
  
  // 获取文件边界信息
  getFileBounds(fileId) {
    return service({
      url: `/files/${fileId}`,
      method: 'get'
    })
  },
  
  // 获取图层统计信息
  getLayerStatistics() {
    return service({
      url: '/layers/statistics',
      method: 'get'
    })
  },
  
  // ========== 场景管理 ==========
  
  // 获取场景列表
  getScenes(params = {}) {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/scenes',
      method: 'get',
      params
    })
  },
  
  // 获取场景详情
  getScene(sceneId) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${String(sceneId)}`,  // 将sceneId转换为字符串，避免大数值被取整
      method: 'get'
    })
  },
  
  // 创建场景
  createScene(data) {
    return authHttp({  // 🔥 使用带认证的请求
      url: '/scenes',
      method: 'post',
      data
    })
  },
  
  // 更新场景
  updateScene(sceneId, data) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${sceneId}`,
      method: 'put',
      data
    })
  },
  
  // 删除场景
  deleteScene(sceneId) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${sceneId}`,
      method: 'delete'
    })
  },
  
  // 添加图层到场景
  addLayerToScene(sceneId, data) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${sceneId}/layers`,
      method: 'post',
      data
    })
  },
  
  // 更新场景图层
  updateSceneLayer(sceneId, layerId, data) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${sceneId}/layers/${layerId}`,
      method: 'put',
      data
    })
  },
  
  // 从场景删除图层
  removeLayerFromScene(sceneId, layerId) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${sceneId}/layers/${layerId}`,
      method: 'delete'
    })
  },
  
  // 重新排序场景图层
  reorderSceneLayers(sceneId, layerOrders) {
    return authHttp({  // 🔥 使用带认证的请求
      url: `/scenes/${sceneId}/layers/reorder`,
      method: 'post',
      data: { layer_order: layerOrders }
    })
  },

  // 更新单个图层的顺序
  updateLayerOrder(sceneId, layerId, newOrder) {
    return authHttp({
      url: `/scenes/${sceneId}/layers/${layerId}/order`,
      method: 'put',
      data: {
        layer_order: newOrder
      }
    })
  },
  
  // ========== GeoServer 工作空间管理 ==========
  
  // 获取工作空间列表
  getWorkspaces() {
    return service({
      url: '/geoserver/workspaces',
      method: 'get'
    })
  },
  
  // 创建工作空间
  createWorkspace(data) {
    return service({
      url: '/geoserver/workspaces',
      method: 'post',
      data
    })
  },
  
  // ========== GeoServer 存储仓库管理 ==========
  
  // 获取存储仓库列表
  getStores(workspaceId) {
    return service({
      url: `/geoserver/workspaces/${workspaceId}/stores`,
      method: 'get'
    })
  },
  
  // 创建存储仓库
  createStore(workspaceId, data) {
    return service({
      url: `/geoserver/workspaces/${workspaceId}/stores`,
      method: 'post',
      data
    })
  },
  
  // ========== GeoServer 样式管理 ==========
  
  // 获取样式列表
  getStyles(workspaceId = null) {
    const params = {}
    if (workspaceId) {
      params.workspace_id = workspaceId
    }
    return service({
      url: '/geoserver/styles',
      method: 'get',
      params
    })
  },
  
  // 创建样式
  createStyle(data, workspaceId = null) {
    const params = {}
    if (workspaceId) {
      params.workspace_id = workspaceId
    }
    return service({
      url: '/geoserver/styles',
      method: 'post',
      data,
      params
    })
  },
  
  // 更新图层样式（新增方法）
  updateLayerStyle(layerId, styleConfig) {
    return service({
      url: `/layers/${layerId}/style`,
      method: 'put',
      data: {
        style_config: styleConfig
      }
    })
  },
  
  // 获取图层样式配置
  getLayerStyle(layerId) {
    //console.log(`调用API: GET /api/layers/${layerId}/style`)
    
    // 验证layerId
    if (!layerId || layerId === undefined || layerId === null) {
      return Promise.reject(new Error(`无效的图层ID: ${layerId}`))
    }
    
    return service({
      url: `/layers/${layerId}/style`,
      method: 'get'
    }).catch(error => {
      console.error(`获取图层样式API调用失败:`, error)
      console.error('错误详情:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        code: error.code
      })
      
      // 重新抛出错误，保持原有的错误信息结构
      throw error
    })
  },
  
  // ========== WFS/WMS 服务 ==========
  
  // 获取WFS数据 (GeoJSON格式)
  getWfsData(wfsUrl, params = {}) {
    // 默认参数
    const defaultParams = {
      service: 'WFS',
      version: '2.0.0',
      request: 'GetFeature',
      outputFormat: 'application/json',
      srsName: 'EPSG:4326'
    }
    
    // 合并参数
    const mergedParams = { ...defaultParams, ...params }
    
    return axios.get(wfsUrl, { 
      params: mergedParams 
    })
  },
  
  // 获取WMS GetCapabilities
  getWmsCapabilities(wmsUrl) {
    return axios.get(wmsUrl, {
      params: {
        service: 'WMS',
        version: '1.3.0',
        request: 'GetCapabilities'
      }
    })
  },
  
  // 获取WFS GetCapabilities
  getWfsCapabilities(wfsUrl) {
    return axios.get(wfsUrl, {
      params: {
        service: 'WFS',
        version: '2.0.0',
        request: 'GetCapabilities'
      }
    })
  },
  
  // ========== 兼容性方法 (保持向后兼容) ==========
  
  // 健康检查
  getHealth() {
    return service({
      url: '/health',
      method: 'get',
      timeout: 5000
    })
  },
  
  // 上传SHP文件或打包ZIP文件 (兼容旧接口)
  uploadShpFile(formData, onProgress) {
    return this.uploadFile(formData, onProgress)
  },
  
  // 获取服务列表 (兼容旧接口)
  getServices() {
    return this.getLayers()
  },
  
  // 发布WFS服务 (兼容旧接口)
  publishWfsService(fileId, params = {}) {
    return this.publishLayer(fileId, params)
  },

  // ========== 地理服务管理 ==========
  
  // 发布服务
  publishService(fileId, params = {}) {
    return service({
      url: `/geoservice/publish/${fileId}`,
      method: 'post',
      data: params
    })
  },

  // 取消发布服务
  unpublishService(fileId) {
    return service({
      url: `/geoservice/unpublish/${fileId}`,
      method: 'delete'
    })
  },

  // 获取图层调试信息
  getLayerDebugInfo(fileId) {
    return service({
      url: `/geoservice/debug/layer/${fileId}`,
      method: 'get'
    })
  },

  // 获取图层预览
  getLayerPreviewImage(layerName, params = {}) {
    return service({
      url: `/geoservice/layer_preview/${layerName}`,
      method: 'get',
      params
    })
  },

  // ========== Martin服务相关 ==========
  
  // 获取Martin服务健康状态
  getMartinHealth() {
    return service({
      url: '/martin/status',
      method: 'get'
    })
  },

  // 获取Martin服务状态
  getMartinStatus() {
    return service({
      url: '/martin/status',
      method: 'get'
    })
  },

  // 获取Martin服务日志
  getMartinLogs() {
    return service({
      url: '/martin/logs',
      method: 'get'
    })
  },

  // 刷新Martin数据表
  refreshMartinTables() {
    return service({
      url: '/martin/refresh',
      method: 'post'
    })
  },

  // 重新加载Martin配置
  reloadMartinConfig() {
    return service({
      url: '/martin/reload-config',
      method: 'post'
    })
  },

  // 重启Martin服务
  restartMartinService() {
    return service({
      url: '/martin/restart',
      method: 'post'
    })
  },

  // ========== Martin服务发布 ==========
  
  // 发布Martin服务
  publishMartinService(fileId, params = {}) {
    return service({
      url: `/files/${fileId}/publish/martin`,
      method: 'post',
      data: params
    })
  },
  // 发布mbtiles的Martin服务
  publishMbtilesMartinService(fileId, params = {}) {
    return service({
      url: `/files/${fileId}/publish/martin-mbtiles`,
      method: 'post',
      data: params
    })
  },

  // 取消发布Martin服务
  unpublishMartinService(fileId) {
    return service({
      url: `/files/${fileId}/unpublish/martin`,
      method: 'delete'
    })
  },

  // 发布GeoServer服务
  publishGeoServerService(fileId, params = {}) {
    return service({
      url: `/files/${fileId}/publish/geoserver`,
      method: 'post',
      data: params
    })
  },

  // 取消发布GeoServer服务
  unpublishGeoServerService(fileId) {
    return service({
      url: `/files/${fileId}/unpublish/geoserver`,
      method: 'delete'
    })
  },

  // ========== Martin服务查询 ==========
  
  // 获取所有Martin服务
  getAllMartinServices(params = {}) {
    return service({
      url: '/martin-services/list',
      method: 'get',
      params
    })
  },

  // 搜索Martin服务
  searchMartinServices(params = {}) {
    return authHttp({
      url: '/martin-services/search',
      method: 'get',
      params
    })
  },

  // 根据ID获取Martin服务
  getMartinServiceById(serviceId) {
    return service({
      url: `/martin-services/${serviceId}`,
      method: 'get'
    })
  },

  // ========== DXF相关 ==========
  
  // 发布DXF的Martin服务
  publishDxfMartinService(fileId, params = {}) {
    return authHttp({  // 🔥 修复：使用带认证的axios实例
      url: `/dxf/publish-martin-ezdxf/${fileId}`,
      method: 'post',
      data: params
    })
  },
  

  // 分析DXF样式
  analyzeDxfStyles(fileId) {
    return service({
      url: `/dxf/analyze-styles/${fileId}`,
      method: 'get'
    })
  },

  // 获取DXF Martin服务列表
  getDxfMartinServices() {
    return service({
      url: '/dxf/martin-services',
      method: 'get'
    })
  },

  // 删除DXF Martin服务
  deleteDxfMartinService(serviceId) {
    return service({
      url: `/dxf/martin-services/${serviceId}`,
      method: 'delete'
    })
  },

  // 发布DXF到双服务（GeoServer + Martin）
  publishDxfBothServices(fileId, params = {}) {
    return authHttp({  // 🔥 修复：使用带认证的axios实例
      url: `/dxf/publish-both/${fileId}`,
      method: 'post',
      data: params
    })
  },

  // 上传并发布DXF
  uploadAndPublishDxf(formData) {
    return service({
      url: '/dxf/upload-and-publish',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 600000 // 10分钟
    })
  },

  // 获取DXF样式图例
  getDxfStyleLegend(fileId) {
    return service({
      url: `/dxf/style-legend/${fileId}`,
      method: 'get'
    })
  },

  // 验证DXF文件
  validateDxfFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    return service({
      url: '/dxf/validate',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // ========== 服务发布到GeoServer ==========
  
  // 发布服务到GeoServer
  async publishServiceToGeoServer(fileId) {
    try {
      //console.log('开始发布到GeoServer，文件ID:', fileId)
      
      const response = await service({
        url: `/services/geoserver/publish/${fileId}`,
        method: 'post',
        timeout: 300000
      })
      
      //console.log('GeoServer发布响应:', response)
      return response
    } catch (error) {
      console.error('发布到GeoServer失败:', error)
      
      // 处理具体的错误类型
      if (error.response) {
        const { status, data } = error.response
        switch (status) {
          case 400:
            throw new Error(data.error || '请求参数错误')
          case 409:
            throw new Error('图层已存在，请检查工作空间和图层名称')
          case 500:
            throw new Error(data.error || 'GeoServer内部错误')
          default:
            throw new Error(`发布失败: ${data.error || '未知错误'}`)
        }
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('发布超时，请稍后重试')
      } else {
        throw new Error(error.message || '网络连接失败')
      }
    }
  },

  // ========== 坐标系相关 ==========
  
  // 搜索坐标系
  searchCoordinateSystems(keyword, limit = 20) {
    return service({
      url: '/files/coordinate-systems/search',
      method: 'get',
      params: {
        keyword,
        limit
      }
    })
  },

  // 获取常用坐标系
  getCommonCoordinateSystems() {
    return service({
      url: '/files/coordinate-systems/common',
      method: 'get'
    })
  },

  // ========== Martin样式管理 ==========
  
  // 更新Martin服务样式
  updateMartinServiceStyle(serviceId, styleConfig) {
    return service({
      url: `/martin-services/${serviceId}/style`,
      method: 'post',
      data: {
        style_config: styleConfig
      }
    })
  },

  // 应用Martin服务样式（保存并应用）
  applyMartinServiceStyle(serviceId, styleConfig) {
    return service({
      url: `/martin-services/${serviceId}/apply-style`,
      method: 'post',
      data: {
        style_config: styleConfig
      }
    })
  },

  // 获取Martin服务样式
  getMartinServiceStyle(serviceId) {
    return service({
      url: `/martin-services/${serviceId}/style`,
      method: 'get'
    })
  },

  // 获取Martin服务图层列表
  getMartinServiceLayers(tableName) {
    return service({
      url: `/martin/table/${tableName}`,
      method: 'get'
    })
  },

  // 获取Martin服务样式模板
  getMartinServiceStyleTemplates() {
    return service({
      url: '/martin-services/style-templates',
      method: 'get'
    })
  },

  // 获取图层坐标系信息
  getLayerCRSInfo(layerId) {
    return service({
      url: `/gis/layer/${layerId}/crs-info`,
      method: 'get'
    })
  },
  
  // 获取常用坐标系的proj4定义
  getProj4Definitions() {
    return service({
      url: '/gis/coordinate-systems/proj4-definitions',
      method: 'get'
    })
  },
  
  // 获取单个坐标系的proj4定义
  getSingleProj4Definition(epsgCode) {
    return service({
      url: `/gis/coordinate-systems/${epsgCode}/proj4`,
      method: 'get'
    })
  }
}

// 导出service实例供其他地方使用
export { service } 