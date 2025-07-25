<template>
  <el-dialog
    v-model="visible"
    title="TIF文件转换进度"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="canClose"
  >
    <div class="conversion-progress">
      <!-- 文件信息 -->
      <div class="file-info">
        <el-descriptions title="文件信息" :column="2" border>
          <el-descriptions-item label="文件名">{{ fileInfo.name }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ fileInfo.type }}</el-descriptions-item>
          <el-descriptions-item label="缩放级别">{{ minZoom }} - {{ maxZoom }}</el-descriptions-item>
          <el-descriptions-item label="坐标系">{{ coordinateSystem || '自动检测' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 进度显示 -->
      <div class="progress-section">
        <div class="progress-header">
          <h4>转换进度</h4>
          <el-tag :type="getStatusType(progress.status)">{{ getStatusText(progress.status) }}</el-tag>
        </div>
        
        <el-progress
          :percentage="progress.progress"
          :status="getProgressStatus(progress.status)"
          :stroke-width="20"
          text-inside
        />
        
        <div class="progress-message">
          <el-icon><Loading /></el-icon>
          <span>{{ progress.message }}</span>
        </div>
        
        <!-- 当前步骤指示器 -->
        <div class="steps-indicator">
          <el-steps :active="getCurrentStepIndex()" align-center>
            <el-step title="初始化" description="准备转换环境" />
            <el-step title="生成瓦片" description="使用gdal2tiles生成瓦片" />
            <el-step title="打包MBTiles" description="将瓦片打包为MBTiles" />
            <el-step title="发布服务" description="发布为Martin服务" />
            <el-step title="完成" description="转换完成" />
          </el-steps>
        </div>
      </div>

      <!-- 详细信息 -->
      <div class="details-section" v-if="progress.tiles_count">
        <el-descriptions title="详细信息" :column="3" border size="small">
          <el-descriptions-item label="已生成瓦片">{{ progress.tiles_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="当前步骤">{{ getCurrentStepName() }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ getElapsedTime() }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 错误信息 -->
      <div class="error-section" v-if="progress.status === 'error'">
        <el-alert
          title="转换失败"
          :description="progress.message"
          type="error"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 成功信息 -->
      <div class="success-section" v-if="progress.status === 'completed' && result">
        <el-alert
          title="转换成功"
          description="TIF文件已成功转换为MBTiles并发布为Martin服务"
          type="success"
          show-icon
          :closable="false"
        />
        
        <div class="result-info">
          <el-descriptions title="转换结果" :column="2" border size="small">
            <el-descriptions-item label="MBTiles文件">{{ result.mbtiles_filename }}</el-descriptions-item>
            <el-descriptions-item label="服务URL">
              <el-link :href="result.martin_service?.service_url" target="_blank" type="primary">
                {{ result.martin_service?.service_url }}
              </el-link>
            </el-descriptions-item>
            <el-descriptions-item label="瓦片URL">
              <el-link :href="result.martin_service?.mvt_url" target="_blank" type="primary">
                {{ result.martin_service?.mvt_url }}
              </el-link>
            </el-descriptions-item>
            <el-descriptions-item label="TileJSON">
              <el-link :href="result.martin_service?.tilejson_url" target="_blank" type="primary">
                {{ result.martin_service?.tilejson_url }}
              </el-link>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button v-if="canClose" @click="handleClose">关闭</el-button>
        <el-button v-if="progress.status === 'error'" @click="handleRetry" type="primary">重试</el-button>
        <el-button v-if="progress.status === 'completed'" @click="handleViewService" type="primary">查看服务</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  taskId: {
    type: String,
    required: true
  },
  fileInfo: {
    type: Object,
    required: true
  },
  minZoom: {
    type: Number,
    default: 2
  },
  maxZoom: {
    type: Number,
    default: 18
  },
  coordinateSystem: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:visible', 'completed', 'error', 'retry'])

// 响应式数据
const progress = ref({
  status: 'starting',
  progress: 0,
  message: '准备开始...',
  current_step: 'init',
  tiles_count: 0
})

const result = ref(null)
const startTime = ref(Date.now())
let progressTimer = null

// 计算属性
const canClose = computed(() => {
  return progress.value.status === 'completed' || progress.value.status === 'error'
})

// 方法
const getStatusType = (status) => {
  const statusMap = {
    'starting': 'info',
    'processing': 'warning',
    'completed': 'success',
    'error': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'starting': '准备中',
    'processing': '处理中',
    'completed': '已完成',
    'error': '失败'
  }
  return statusMap[status] || '未知'
}

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'error') return 'exception'
  return null
}

const getCurrentStepIndex = () => {
  const stepMap = {
    'init': 0,
    'tiles_generation': 1,
    'mbtiles_packing': 2,
    'martin_publish': 3,
    'completed': 4,
    'error': -1
  }
  return stepMap[progress.value.current_step] || 0
}

const getCurrentStepName = () => {
  const stepMap = {
    'init': '初始化',
    'tiles_generation': '生成瓦片',
    'mbtiles_packing': '打包MBTiles',
    'martin_publish': '发布服务',
    'completed': '完成',
    'error': '错误'
  }
  return stepMap[progress.value.current_step] || '未知'
}

const getElapsedTime = () => {
  const elapsed = Math.floor((Date.now() - startTime.value) / 1000)
  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  return `${minutes}分${seconds}秒`
}

const fetchProgress = async () => {
  try {
    const response = await axios.get(`/api/tif-martin/progress/${props.taskId}`)
    if (response.data.success) {
      const newProgress = response.data.progress
      progress.value = { ...progress.value, ...newProgress }
      
      // 如果完成，获取结果
      if (newProgress.status === 'completed' && newProgress.result) {
        result.value = newProgress.result
        emit('completed', newProgress.result)
        stopProgressPolling()
      } else if (newProgress.status === 'error') {
        emit('error', newProgress.message)
        stopProgressPolling()
      }
    }
  } catch (error) {
    console.error('获取进度失败:', error)
    ElMessage.error('获取进度失败')
  }
}

const startProgressPolling = () => {
  if (progressTimer) return
  
  progressTimer = setInterval(() => {
    if (props.visible && props.taskId) {
      fetchProgress()
    }
  }, 2000) // 每2秒查询一次
}

const stopProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

const handleClose = () => {
  stopProgressPolling()
  emit('update:visible', false)
  
  // 清理进度数据
  if (props.taskId) {
    axios.delete(`/api/tif-martin/cleanup-progress/${props.taskId}`).catch(() => {})
  }
}

const handleRetry = () => {
  emit('retry')
}

const handleViewService = () => {
  if (result.value?.martin_service?.service_url) {
    window.open(result.value.martin_service.service_url, '_blank')
  }
}

// 监听器
watch(() => props.visible, (newVal) => {
  if (newVal && props.taskId) {
    startTime.value = Date.now()
    startProgressPolling()
    fetchProgress() // 立即获取一次进度
  } else {
    stopProgressPolling()
  }
})

// 生命周期
onMounted(() => {
  if (props.visible && props.taskId) {
    startProgressPolling()
  }
})

onUnmounted(() => {
  stopProgressPolling()
})
</script>

<style scoped>
.conversion-progress {
  padding: 20px 0;
}

.file-info {
  margin-bottom: 30px;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.progress-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.progress-message {
  display: flex;
  align-items: center;
  margin: 15px 0;
  color: #666;
  font-size: 14px;
}

.progress-message .el-icon {
  margin-right: 8px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.steps-indicator {
  margin-top: 30px;
}

.details-section {
  margin-bottom: 20px;
}

.error-section {
  margin-bottom: 20px;
}

.success-section {
  margin-bottom: 20px;
}

.result-info {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-progress-bar__inner) {
  transition: width 0.3s ease;
}

:deep(.el-step__title) {
  font-size: 12px;
}

:deep(.el-step__description) {
  font-size: 11px;
}
</style>