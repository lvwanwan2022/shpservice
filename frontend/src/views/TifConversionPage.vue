<template>
  <div class="tif-conversion-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>TIF文件转换为MBTiles服务</span>
        </div>
      </template>

      <div class="conversion-form">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
          <el-form-item label="选择TIF文件" prop="fileId">
            <el-select
              v-model="form.fileId"
              placeholder="请选择TIF文件"
              style="width: 100%"
              filterable
            >
              <el-option
                v-for="file in tifFiles"
                :key="file.id"
                :label="`${file.file_name} (${file.file_type})`"
                :value="file.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="最小缩放级别" prop="minZoom">
            <el-input-number
              v-model="form.minZoom"
              :min="0"
              :max="20"
              placeholder="最小缩放级别"
            />
          </el-form-item>

          <el-form-item label="最大缩放级别" prop="maxZoom">
            <el-input-number
              v-model="form.maxZoom"
              :min="1"
              :max="25"
              placeholder="最大缩放级别"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="startConversion" :loading="converting">
              开始转换
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 转换历史 -->
      <div class="conversion-history">
        <h3>转换历史</h3>
        <el-table :data="conversionHistory" style="width: 100%">
          <el-table-column prop="file_name" label="文件名" />
          <el-table-column prop="vector_type" label="类型" />
          <el-table-column prop="created_at" label="转换时间" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" @click="viewService(scope.row)">查看服务</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 转换进度对话框 -->
    <TifConversionDialog
      v-model:visible="showProgressDialog"
      :task-id="currentTaskId"
      :file-info="currentFileInfo"
      :min-zoom="form.minZoom"
      :max-zoom="form.maxZoom"
      :coordinate-system="currentCoordinateSystem"
      @completed="onConversionCompleted"
      @error="onConversionError"
      @retry="onRetryConversion"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import TifConversionDialog from '@/components/TifConversionDialog.vue'

// 响应式数据
const formRef = ref()
const tifFiles = ref([])
const conversionHistory = ref([])
const converting = ref(false)
const showProgressDialog = ref(false)
const currentTaskId = ref('')
const currentFileInfo = ref({})
const currentCoordinateSystem = ref('')

const form = reactive({
  fileId: '',
  minZoom: 2,
  maxZoom: 18
})

const rules = {
  fileId: [
    { required: true, message: '请选择TIF文件', trigger: 'change' }
  ],
  minZoom: [
    { required: true, message: '请输入最小缩放级别', trigger: 'blur' },
    { type: 'number', min: 0, max: 20, message: '最小缩放级别必须在0-20之间', trigger: 'blur' }
  ],
  maxZoom: [
    { required: true, message: '请输入最大缩放级别', trigger: 'blur' },
    { type: 'number', min: 1, max: 25, message: '最大缩放级别必须在1-25之间', trigger: 'blur' }
  ]
}

// 方法
const loadTifFiles = async () => {
  try {
    const response = await axios.get('/api/files', {
      params: {
        file_type: 'tif,tiff,dem.tif,dom.tif',
        page: 1,
        per_page: 100
      }
    })
    
    if (response.data.success) {
      tifFiles.value = response.data.files
    }
  } catch (error) {
    console.error('加载TIF文件列表失败:', error)
    ElMessage.error('加载文件列表失败')
  }
}

const loadConversionHistory = async () => {
  try {
    const response = await axios.get('/api/tif-martin/list-conversions')
    if (response.data.success) {
      conversionHistory.value = response.data.conversions
    }
  } catch (error) {
    console.error('加载转换历史失败:', error)
  }
}

const startConversion = async () => {
  try {
    await formRef.value.validate()
    
    const selectedFile = tifFiles.value.find(f => f.id === form.fileId)
    if (!selectedFile) {
      ElMessage.error('请选择有效的TIF文件')
      return
    }

    // 检查是否已经转换过
    const statusResponse = await axios.get(`/api/tif-martin/conversion-status/${form.fileId}`)
    if (statusResponse.data.converted) {
      const result = await ElMessageBox.confirm(
        '该文件已经转换过，是否要重新转换？',
        '确认',
        {
          confirmButtonText: '重新转换',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      if (result !== 'confirm') {
        return
      }
    }

    converting.value = true
    currentFileInfo.value = {
      id: selectedFile.id,
      name: selectedFile.file_name,
      type: selectedFile.file_type
    }

    // 启动异步转换
    const response = await axios.post(`/api/tif-martin/convert-async/${form.fileId}`, {
      min_zoom: form.minZoom,
      max_zoom: form.maxZoom
    })

    if (response.data.success) {
      currentTaskId.value = response.data.task_id
      currentCoordinateSystem.value = response.data.coordinate_system || ''
      showProgressDialog.value = true
      ElMessage.success('转换任务已启动')
    } else {
      ElMessage.error(response.data.error || '启动转换失败')
    }

  } catch (error) {
    console.error('启动转换失败:', error)
    ElMessage.error('启动转换失败')
  } finally {
    converting.value = false
  }
}

const onConversionCompleted = (result) => {
  ElMessage.success('TIF文件转换完成！')
  loadConversionHistory() // 刷新转换历史
}

const onConversionError = (error) => {
  ElMessage.error(`转换失败: ${error}`)
}

const onRetryConversion = () => {
  showProgressDialog.value = false
  setTimeout(() => {
    startConversion()
  }, 500)
}

const resetForm = () => {
  formRef.value.resetFields()
}

const viewService = (row) => {
  if (row.service_url) {
    window.open(row.service_url, '_blank')
  }
}

// 生命周期
onMounted(() => {
  loadTifFiles()
  loadConversionHistory()
})
</script>

<style scoped>
.tif-conversion-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conversion-form {
  margin-bottom: 40px;
}

.conversion-history {
  margin-top: 40px;
}

.conversion-history h3 {
  margin-bottom: 20px;
  color: #333;
}
</style>