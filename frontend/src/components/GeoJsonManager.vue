<template>
  <div class="geojson-manager">
    <div class="header">
      <h2>GeoJSON 文件管理</h2>
      <p class="description">直接上传GeoJSON文件，无需通过GeoServer，前端使用Leaflet直接加载显示</p>
    </div>

    <!-- 文件上传区域 -->
    <div class="upload-section">
      <div class="upload-card">
        <h3>上传 GeoJSON 文件</h3>
        
        <div class="upload-area" 
             :class="{ 'dragging': isDragging }"
             @drop="handleDrop"
             @dragover="handleDragOver"
             @dragenter="handleDragEnter"
             @dragleave="handleDragLeave">
          
          <div v-if="!uploading" class="upload-content">
            <i class="upload-icon">📁</i>
            <p>拖拽 GeoJSON 文件到这里，或者<br>
              <button class="upload-btn" @click="selectFile">点击选择文件</button>
            </p>
            <p class="file-hint">支持 .geojson 和 .json 文件格式</p>
          </div>
          
          <div v-else class="uploading">
            <div class="spinner"></div>
            <p>正在上传处理文件...</p>
          </div>
        </div>
        
        <input 
          ref="fileInput" 
          type="file" 
          accept=".geojson,.json" 
          @change="handleFileSelect" 
          style="display: none;">
      </div>
    </div>

    <!-- 成功上传提示 -->
    <div v-if="uploadResult" class="result-section">
      <div class="result-card success">
        <h3>✅ 上传成功！</h3>
        
        <div class="file-info">
          <p><strong>文件名：</strong>{{ uploadResult.original_filename }}</p>
          <p><strong>文件ID：</strong>{{ uploadResult.file_id }}</p>
          <p><strong>要素数量：</strong>{{ uploadResult.analysis.feature_count }}</p>
          <p><strong>几何类型：</strong>{{ uploadResult.analysis.geometry_types.join(', ') }}</p>
          <p><strong>属性字段：</strong>{{ uploadResult.analysis.property_fields.join(', ') }}</p>
        </div>
        
        <div class="action-buttons">
          <button class="btn preview-btn" @click="previewOnMap(uploadResult)">
            🗺️ 在地图上预览
          </button>
          <button class="btn copy-btn" @click="copyAccessUrl(uploadResult.access_url)">
            📋 复制访问URL
          </button>
          <button class="btn download-btn" @click="downloadFile(uploadResult.download_url)">
            ⬇️ 下载文件
          </button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="result-section">
      <div class="result-card error">
        <h3>❌ 上传失败</h3>
        <p>{{ errorMessage }}</p>
        <button class="btn" @click="clearError">确定</button>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="files-section">
      <div class="section-header">
        <h3>已上传的文件</h3>
        <button class="btn refresh-btn" @click="loadFileList">🔄 刷新</button>
      </div>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="files.length === 0" class="empty-state">
        <p>暂无文件</p>
      </div>
      
      <div v-else class="files-grid">
        <div v-for="file in files" :key="file.file_id" class="file-card">
          <div class="file-header">
            <h4>{{ file.original_filename }}</h4>
            <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
          </div>
          
          <div class="file-info">
            <div class="info-row">
              <span class="label">要素数量：</span>
              <span class="value">{{ file.feature_count }}</span>
            </div>
            <div class="info-row">
              <span class="label">几何类型：</span>
              <span class="value">{{ file.geometry_types.join(', ') }}</span>
            </div>
            <div class="info-row">
              <span class="label">上传时间：</span>
              <span class="value">{{ formatDate(file.upload_time) }}</span>
            </div>
            <div class="info-row">
              <span class="label">访问次数：</span>
              <span class="value">{{ file.access_count }}</span>
            </div>
          </div>
          
          <div class="file-actions">
            <button class="btn small preview-btn" @click="previewOnMap(file)">
              🗺️ 预览
            </button>
            <button class="btn small copy-btn" @click="copyAccessUrl(file.access_url)">
              📋 复制URL
            </button>
            <button class="btn small download-btn" @click="downloadFile(file.download_url)">
              ⬇️ 下载
            </button>
            <button class="btn small delete-btn" @click="deleteFile(file.file_id)">
              🗑️ 删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 地图预览弹窗 -->
    <div v-if="showMapPreview" class="map-modal" @click="closeMapPreview">
      <div class="map-container" @click.stop>
        <div class="map-header">
          <h3>地图预览: {{ previewFile?.original_filename }}</h3>
          <button class="close-btn" @click="closeMapPreview">✕</button>
        </div>
        <div id="previewMap" class="map-content"></div>
        <div class="map-footer">
          <div class="map-info">
            <span>要素数量: {{ previewFile?.feature_count || previewFile?.analysis?.feature_count }}</span>
            <span>几何类型: {{ getGeometryTypes(previewFile) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '@/api/index.js'

export default {
  name: 'GeoJsonManager',
  data() {
    return {
      // 上传状态
      uploading: false,
      isDragging: false,
      uploadResult: null,
      errorMessage: null,
      
      // 文件列表
      files: [],
      loading: false,
      
      // 地图预览
      showMapPreview: false,
      previewFile: null,
      map: null
    }
  },
  
  mounted() {
    this.loadFileList()
  },
  
  beforeUnmount() {
    if (this.map) {
      this.map.remove()
    }
  },
  
  methods: {
    // === 文件上传相关 ===
    selectFile() {
      this.$refs.fileInput.click()
    },
    
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        this.uploadFile(file)
      }
    },
    
    handleDragEnter(e) {
      e.preventDefault()
      this.isDragging = true
    },
    
    handleDragOver(e) {
      e.preventDefault()
    },
    
    handleDragLeave(e) {
      e.preventDefault()
      this.isDragging = false
    },
    
    handleDrop(e) {
      e.preventDefault()
      this.isDragging = false
      
      const files = e.dataTransfer.files
      if (files.length > 0) {
        this.uploadFile(files[0])
      }
    },
    
    async uploadFile(file) {
      if (!this.validateFile(file)) {
        return
      }
      
      this.uploading = true
      this.uploadResult = null
      this.errorMessage = null
      
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        //console.log('开始上传文件:', file.name)
        
        const response = await api.post('/geojson/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        //console.log('上传成功:', response.data)
        this.uploadResult = response.data
        
        // 刷新文件列表
        this.loadFileList()
        
        // 清空文件输入
        this.$refs.fileInput.value = ''
        
      } catch (error) {
        console.error('上传失败:', error)
        this.errorMessage = error.response?.data?.error || error.message || '上传失败'
      } finally {
        this.uploading = false
      }
    },
    
    validateFile(file) {
      const validTypes = ['.geojson', '.json']
      const fileName = file.name.toLowerCase()
      
      if (!validTypes.some(type => fileName.endsWith(type))) {
        this.errorMessage = '只支持 .geojson 和 .json 文件格式'
        return false
      }
      
      if (file.size > 50 * 1024 * 1024) { // 50MB
        this.errorMessage = '文件大小不能超过50MB'
        return false
      }
      
      return true
    },
    
    // === 文件列表相关 ===
    async loadFileList() {
      this.loading = true
      
      try {
        const response = await api.get('/geojson/files')
        this.files = response.data.files || []
        //console.log('文件列表加载成功:', this.files.length, '个文件')
      } catch (error) {
        console.error('加载文件列表失败:', error)
        this.errorMessage = '加载文件列表失败'
      } finally {
        this.loading = false
      }
    },
    
    async deleteFile(fileId) {
      if (!confirm('确定要删除这个文件吗？')) {
        return
      }
      
      try {
        await api.delete(`/geojson/files/${fileId}`)
        //console.log('文件删除成功:', fileId)
        
        // 移除本地列表中的文件
        this.files = this.files.filter(f => f.file_id !== fileId)
        
        // 如果删除的是当前预览的文件，关闭预览
        if (this.previewFile?.file_id === fileId) {
          this.closeMapPreview()
        }
        
      } catch (error) {
        console.error('删除文件失败:', error)
        this.errorMessage = error.response?.data?.error || '删除失败'
      }
    },
    
    // === 地图预览相关 ===
    async previewOnMap(file) {
      this.previewFile = file
      this.showMapPreview = true
      
      // 等待DOM更新
      await this.$nextTick()
      
      this.initMap(file)
    },
    
    async initMap(file) {
      try {
        // 如果已有地图，先销毁
        if (this.map) {
          this.map.remove()
        }
        
        // 动态导入Leaflet
        const L = await this.loadLeaflet()
        
        // 创建地图
        this.map = L.map('previewMap').setView([39.9042, 116.4074], 10)
        
        // 添加底图
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors'
        }).addTo(this.map)
        
        // 获取并加载GeoJSON数据
        const accessUrl = file.access_url || `/api/geojson/files/${file.file_id}`
        //console.log('加载GeoJSON数据:', accessUrl)
        
        const response = await api.get(accessUrl)
        const geojsonData = response.data
        
        //console.log('GeoJSON数据加载成功:', geojsonData)
        
        // 添加GeoJSON图层
        const geojsonLayer = L.geoJSON(geojsonData, {
          style: {
            color: '#3388ff',
            weight: 2,
            opacity: 0.8,
            fillOpacity: 0.3
          },
          pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng, {
              radius: 6,
              fillColor: '#3388ff',
              color: '#000',
              weight: 1,
              opacity: 1,
              fillOpacity: 0.8
            })
          },
          onEachFeature: function (feature, layer) {
            if (feature.properties) {
              const props = feature.properties
              let popupContent = '<div class="popup-content">'
              
              for (const [key, value] of Object.entries(props)) {
                if (value !== null && value !== undefined && value !== '') {
                  popupContent += `<div><strong>${key}:</strong> ${value}</div>`
                }
              }
              
              popupContent += '</div>'
              layer.bindPopup(popupContent)
            }
          }
        }).addTo(this.map)
        
        // 缩放到数据范围
        if (geojsonLayer.getBounds().isValid()) {
          this.map.fitBounds(geojsonLayer.getBounds(), { padding: [20, 20] })
        }
        
      } catch (error) {
        console.error('地图预览失败:', error)
        this.errorMessage = '地图预览失败: ' + (error.message || '未知错误')
        this.closeMapPreview()
      }
    },
    
    async loadLeaflet() {
      // 检查是否已加载
      if (window.L) {
        return window.L
      }
      
      // 动态加载CSS
      if (!document.querySelector('link[href*="leaflet"]')) {
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
        document.head.appendChild(link)
      }
      
      // 动态加载JS
      return new Promise((resolve, reject) => {
        if (window.L) {
          resolve(window.L)
          return
        }
        
        const script = document.createElement('script')
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
        script.onload = () => resolve(window.L)
        script.onerror = reject
        document.head.appendChild(script)
      })
    },
    
    closeMapPreview() {
      this.showMapPreview = false
      this.previewFile = null
      
      if (this.map) {
        this.map.remove()
        this.map = null
      }
    },
    
    // === 工具方法 ===
    async copyAccessUrl(url) {
      try {
        const fullUrl = window.location.origin + url
        await navigator.clipboard.writeText(fullUrl)
        //console.log('URL已复制到剪贴板:', fullUrl)
        
        // 可以添加一个临时提示
        this.showToast('URL已复制到剪贴板')
      } catch (error) {
        console.error('复制失败:', error)
        
        // 降级方案
        const textArea = document.createElement('textarea')
        textArea.value = window.location.origin + url
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        
        this.showToast('URL已复制到剪贴板')
      }
    },
    
    downloadFile(url) {
      const fullUrl = window.location.origin + url
      window.open(fullUrl, '_blank')
    },
    
    clearError() {
      this.errorMessage = null
      this.uploadResult = null
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    },
    
    getGeometryTypes(file) {
      if (file?.geometry_types) {
        return file.geometry_types.join(', ')
      }
      if (file?.analysis?.geometry_types) {
        return file.analysis.geometry_types.join(', ')
      }
      return '未知'
    },
    
    showToast(message) {
      // 简单的提示实现
      const toast = document.createElement('div')
      toast.className = 'toast'
      toast.textContent = message
      toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 10000;
        animation: fadeInOut 2s ease-in-out;
      `
      
      document.body.appendChild(toast)
      
      setTimeout(() => {
        document.body.removeChild(toast)
      }, 2000)
    }
  }
}
</script>

<style scoped>
.geojson-manager {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.description {
  color: #7f8c8d;
  font-size: 14px;
}

/* 上传区域 */
.upload-section {
  margin-bottom: 30px;
}

.upload-card {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.upload-card h3 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.upload-area {
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover,
.upload-area.dragging {
  border-color: #3498db;
  background: #e3f2fd;
}

.upload-content .upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.upload-btn {
  color: #3498db;
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.file-hint {
  color: #7f8c8d;
  font-size: 12px;
  margin-top: 8px;
}

.uploading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 结果区域 */
.result-section {
  margin-bottom: 30px;
}

.result-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.result-card.success {
  border-left: 4px solid #27ae60;
}

.result-card.error {
  border-left: 4px solid #e74c3c;
}

.file-info {
  margin: 16px 0;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 4px;
}

.file-info p {
  margin: 8px 0;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 文件列表 */
.files-section {
  margin-top: 40px;
}

.section-header {
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  color: #2c3e50;
}

.loading {
  text-align: center;
  padding: 40px;
}

.loading .spinner {
  margin: 0 auto 16px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.file-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.file-card:hover {
  transform: translateY(-2px);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.file-header h4 {
  color: #2c3e50;
  margin: 0;
  word-break: break-all;
  flex: 1;
}

.file-size {
  color: #7f8c8d;
  font-size: 12px;
  white-space: nowrap;
  margin-left: 12px;
}

.file-info {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-row .label {
  color: #7f8c8d;
  flex-shrink: 0;
}

.info-row .value {
  color: #2c3e50;
  text-align: right;
  word-break: break-all;
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn.small {
  padding: 6px 12px;
  font-size: 12px;
}

.btn:hover {
  opacity: 0.8;
}

.preview-btn {
  background: #3498db;
  color: white;
}

.copy-btn {
  background: #95a5a6;
  color: white;
}

.download-btn {
  background: #27ae60;
  color: white;
}

.delete-btn {
  background: #e74c3c;
  color: white;
}

.refresh-btn {
  background: #f39c12;
  color: white;
}

/* 地图预览弹窗 */
.map-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.map-container {
  background: white;
  border-radius: 8px;
  width: 90%;
  height: 80%;
  max-width: 1000px;
  max-height: 700px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.map-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-content {
  flex: 1;
  position: relative;
}

.map-footer {
  padding: 12px 20px;
  background: #f8f9fa;
  border-top: 1px solid #eee;
}

.map-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #7f8c8d;
}

/* 弹出框内容样式 */
:global(.popup-content) {
  max-width: 200px;
}

:global(.popup-content div) {
  margin-bottom: 4px;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .geojson-manager {
    padding: 10px;
  }
  
  .upload-card {
    padding: 20px;
  }
  
  .upload-area {
    padding: 20px;
  }
  
  .files-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .file-actions {
    flex-direction: column;
  }
  
  .map-container {
    width: 95%;
    height: 90%;
  }
  
  .map-info {
    flex-direction: column;
    gap: 8px;
  }
}

/* Toast 动画 */
@keyframes fadeInOut {
  0% { opacity: 0; transform: translateY(-20px); }
  20% { opacity: 1; transform: translateY(0); }
  80% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-20px); }
}
</style> 