<template>
  <div class="sld-style-manager">
    <div class="sld-style-header">
      <h3>SLD样式管理</h3>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传SLD样式
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <div class="sld-style-filter">
      <el-select v-model="filterGeometryType" placeholder="选择几何类型" clearable @change="loadSldStyles">
        <el-option label="点图层" value="point" />
        <el-option label="线图层" value="line" />
        <el-option label="面图层" value="polygon" />
      </el-select>
    </div>

    <!-- SLD样式列表 -->
    <div class="sld-style-list">
      <el-table :data="sldStyles" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="样式名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="geometry_type" label="几何类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getGeometryTypeTagType(row.geometry_type)">
              {{ getGeometryTypeLabel(row.geometry_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="downloadSldFile(row.id)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button size="small" type="danger" @click="deleteSldStyle(row.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传SLD样式文件"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="样式名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入样式名称" />
        </el-form-item>
        <el-form-item label="样式描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入样式描述"
          />
        </el-form-item>
        <el-form-item label="几何类型" prop="geometry_type">
          <el-select v-model="uploadForm.geometry_type" placeholder="请选择几何类型" style="width: 100%">
            <el-option label="点图层" value="point" />
            <el-option label="线图层" value="line" />
            <el-option label="面图层" value="polygon" />
          </el-select>
        </el-form-item>
        <el-form-item label="SLD文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".sld"
            :limit="1"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                只能上传.sld文件，且不超过10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="uploadSldFile" :loading="uploading">
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Delete } from '@element-plus/icons-vue'
import { sldStyleApi } from '@/api/sldStyle'

export default {
  name: 'SldStyleManager',
  components: {
    Upload,
    Download,
    Delete
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const uploading = ref(false)
    const showUploadDialog = ref(false)
    const sldStyles = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const filterGeometryType = ref('')
    const fileList = ref([])

    // 上传表单
    const uploadForm = reactive({
      name: '',
      description: '',
      geometry_type: '',
      file: null
    })

    // 表单验证规则
    const uploadRules = {
      name: [
        { required: true, message: '请输入样式名称', trigger: 'blur' }
      ],
      geometry_type: [
        { required: true, message: '请选择几何类型', trigger: 'change' }
      ],
      file: [
        { required: true, message: '请选择SLD文件', trigger: 'change' }
      ]
    }

    const uploadFormRef = ref()
    const uploadRef = ref()

    // 加载SLD样式列表
    const loadSldStyles = async () => {
      try {
        loading.value = true
        const params = {
          page: currentPage.value,
          page_size: pageSize.value
        }
        
        if (filterGeometryType.value) {
          params.geometry_type = filterGeometryType.value
        }

        const response = await sldStyleApi.getSldStyles(params)
        sldStyles.value = response.styles || []
        total.value = response.total || 0
      } catch (error) {
        console.error('加载SLD样式列表失败:', error)
        ElMessage.error('加载SLD样式列表失败')
      } finally {
        loading.value = false
      }
    }

    // 上传SLD文件
    const uploadSldFile = async () => {
      try {
        await uploadFormRef.value.validate()
        
        if (!uploadForm.file) {
          ElMessage.error('请选择SLD文件')
          return
        }

        uploading.value = true
        
        const formData = new FormData()
        formData.append('name', uploadForm.name)
        formData.append('description', uploadForm.description)
        formData.append('geometry_type', uploadForm.geometry_type)
        formData.append('file', uploadForm.file)

        await sldStyleApi.uploadSldFile(formData)
        
        ElMessage.success('SLD文件上传成功')
        showUploadDialog.value = false
        resetUploadForm()
        loadSldStyles()
      } catch (error) {
        console.error('上传SLD文件失败:', error)
        ElMessage.error(error.response?.data?.error || '上传SLD文件失败')
      } finally {
        uploading.value = false
      }
    }

    // 下载SLD文件
    const downloadSldFile = async (styleId) => {
      try {
        const response = await sldStyleApi.downloadSldFile(styleId)
        
        // 创建下载链接
        const blob = new Blob([response], { type: 'application/xml' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `style_${styleId}.sld`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('文件下载成功')
      } catch (error) {
        console.error('下载SLD文件失败:', error)
        ElMessage.error('下载SLD文件失败')
      }
    }

    // 删除SLD样式
    const deleteSldStyle = async (styleId) => {
      try {
        await ElMessageBox.confirm('确定要删除这个SLD样式吗？', '确认删除', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        await sldStyleApi.deleteSldStyle(styleId)
        ElMessage.success('SLD样式删除成功')
        loadSldStyles()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除SLD样式失败:', error)
          ElMessage.error('删除SLD样式失败')
        }
      }
    }

    // 文件选择处理
    const handleFileChange = (file) => {
      uploadForm.file = file.raw
    }

    // 重置上传表单
    const resetUploadForm = () => {
      uploadForm.name = ''
      uploadForm.description = ''
      uploadForm.geometry_type = ''
      uploadForm.file = null
      fileList.value = []
      uploadFormRef.value?.resetFields()
    }

    // 分页处理
    const handleSizeChange = (val) => {
      pageSize.value = val
      currentPage.value = 1
      loadSldStyles()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadSldStyles()
    }

    // 工具函数
    const getGeometryTypeLabel = (type) => {
      const labels = {
        point: '点图层',
        line: '线图层',
        polygon: '面图层'
      }
      return labels[type] || type
    }

    const getGeometryTypeTagType = (type) => {
      const types = {
        point: 'success',
        line: 'warning',
        polygon: 'info'
      }
      return types[type] || 'default'
    }

    const formatFileSize = (bytes) => {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleString()
    }

    // 初始化
    onMounted(() => {
      loadSldStyles()
    })

    return {
      loading,
      uploading,
      showUploadDialog,
      sldStyles,
      total,
      currentPage,
      pageSize,
      filterGeometryType,
      fileList,
      uploadForm,
      uploadRules,
      uploadFormRef,
      uploadRef,
      loadSldStyles,
      uploadSldFile,
      downloadSldFile,
      deleteSldStyle,
      handleFileChange,
      handleSizeChange,
      handleCurrentChange,
      getGeometryTypeLabel,
      getGeometryTypeTagType,
      formatFileSize,
      formatDate
    }
  }
}
</script>

<style scoped>
.sld-style-manager {
  padding: 20px;
}

.sld-style-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sld-style-header h3 {
  margin: 0;
  color: #303133;
}

.sld-style-filter {
  margin-bottom: 20px;
}

.sld-style-filter .el-select {
  width: 200px;
}

.sld-style-list {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.el-upload__tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}
</style>
