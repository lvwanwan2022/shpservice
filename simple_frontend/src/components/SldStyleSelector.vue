<template>
  <div class="sld-style-selector">
    <div class="sld-style-selector-header">
      <h4>SLD样式设置</h4>
      <el-button size="small" @click="refreshStyles">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 当前应用的样式 -->
    <div v-if="currentStyle" class="current-style-info">
      <el-alert
        title="当前应用的样式"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="current-style-details">
            <p><strong>样式名称：</strong>{{ currentStyle.name }}</p>
            <p><strong>几何类型：</strong>{{ getGeometryTypeLabel(currentStyle.geometry_type) }}</p>
            <p><strong>应用时间：</strong>{{ formatDate(currentStyle.applied_at) }}</p>
          </div>
          <div class="current-style-actions">
            <el-button size="small" @click="removeCurrentStyle" type="danger">
              移除样式
            </el-button>
          </div>
        </template>
      </el-alert>
    </div>

    <!-- 图层几何类型选择 -->
    <div class="geometry-type-selector">
      <el-form-item label="图层几何类型" required>
        <el-radio-group v-model="selectedGeometryType" @change="onGeometryTypeChange">
          <el-radio label="point">点图层</el-radio>
          <el-radio label="line">线图层</el-radio>
          <el-radio label="polygon">面图层</el-radio>
        </el-radio-group>
      </el-form-item>
    </div>

    <!-- SLD样式列表 -->
    <div v-if="selectedGeometryType" class="sld-style-list">
      <div class="style-list-header">
        <h5>可用的{{ getGeometryTypeLabel(selectedGeometryType) }}样式</h5>
        <el-button size="small" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传新样式
        </el-button>
      </div>

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="filteredStyles.length === 0" class="empty-container">
        <el-empty description="暂无可用的样式">
          <el-button type="primary" @click="showUploadDialog = true">
            上传样式
          </el-button>
        </el-empty>
      </div>

      <!-- 电脑端：使用表格列表展示 -->
      <div v-else-if="isDesktop" class="style-table-container">
        <el-table 
          :data="filteredStyles" 
          v-loading="loading"
          style="width: 100%"
          :row-class-name="getRowClassName"
          @row-click="handleRowClick"
          highlight-current-row
        >
          <el-table-column prop="name" label="样式名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="geometry_type" label="几何类型" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="getGeometryTypeTagType(row.geometry_type)">
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
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click.stop="editStyle(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" @click.stop="downloadStyle(row.id)">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button
                size="small"
                type="primary"
                @click.stop="applyStyle(row)"
                :loading="applyingStyleId === row.id"
              >
                应用
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click.stop="deleteStyle(row.id)"
                :loading="deletingStyleId === row.id"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 移动端：使用卡片网格展示 -->
      <div v-else class="style-grid">
        <div
          v-for="style in filteredStyles"
          :key="style.id"
          class="style-card"
          :class="{ 'selected': selectedStyleId === style.id }"
          @click="selectStyle(style)"
        >
          <div class="style-card-header">
            <h6>{{ style.name }}</h6>
            <el-tag size="small" :type="getGeometryTypeTagType(style.geometry_type)">
              {{ getGeometryTypeLabel(style.geometry_type) }}
            </el-tag>
          </div>
          <div class="style-card-content">
            <p class="style-description">{{ style.description || '暂无描述' }}</p>
            <p class="style-info">
              <small>文件大小: {{ formatFileSize(style.file_size) }}</small>
              <br>
              <small>创建时间: {{ formatDate(style.created_at) }}</small>
            </p>
          </div>
          <div class="style-card-actions">
            <el-button size="small" @click.stop="editStyle(style)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button size="small" @click.stop="downloadStyle(style.id)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click.stop="applyStyle(style)"
              :loading="applyingStyleId === style.id"
            >
              应用
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click.stop="deleteStyle(style.id)"
              :loading="deletingStyleId === style.id"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
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
        <el-form-item v-if="!selectedGeometryType" label="几何类型">
          <el-alert
            type="warning"
            :closable="false"
            show-icon
          >
            <template #default>
              请先在主界面选择图层几何类型
            </template>
          </el-alert>
        </el-form-item>
        <el-form-item v-else label="几何类型">
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              {{ getGeometryTypeLabel(selectedGeometryType) }}（将使用主界面选择的几何类型）
            </template>
          </el-alert>
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
          <el-button 
            type="primary" 
            @click="uploadSldFile" 
            :loading="uploading"
            :disabled="!selectedGeometryType"
          >
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑样式对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑SLD样式"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="editingStyle" v-loading="loadingContent">
        <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
          <el-form-item label="样式名称" prop="name">
            <el-input v-model="editForm.name" placeholder="请输入样式名称" />
          </el-form-item>
          <el-form-item label="样式描述" prop="description">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入样式描述"
            />
          </el-form-item>
          <el-form-item label="几何类型" prop="geometry_type">
            <el-select v-model="editForm.geometry_type" placeholder="请选择几何类型" style="width: 100%">
              <el-option label="点图层" value="point" />
              <el-option label="线图层" value="line" />
              <el-option label="面图层" value="polygon" />
            </el-select>
          </el-form-item>
          
          <!-- SLD内容编辑 -->
          <el-form-item label="SLD内容" prop="content">
            <el-input
              v-model="editForm.content"
              type="textarea"
              :rows="15"
              placeholder="请输入SLD文件内容"
              class="sld-content-editor"
            />
            <div class="editor-tips">
              <p><small>提示：</small></p>
              <p><small>• 请确保SLD内容格式正确</small></p>
              <p><small>• SLD内容应包含与所选几何类型匹配的符号化器</small></p>
              <p><small>• 可以参考现有的SLD文件格式进行编写</small></p>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveEditedStyle" :loading="saving">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Upload, Download, Loading, Edit, Delete } from '@element-plus/icons-vue'
import { sldStyleApi } from '@/api/sldStyle'
import { getDeviceType } from '@/utils/deviceUtils'

export default {
  name: 'SldStyleSelector',
  components: {
    Refresh,
    Upload,
    Download,
    Loading,
    Edit,
    Delete
  },
  props: {
    layerId: {
      type: [Number, String],
      required: true
    },
    layerGeometryType: {
      type: String,
      default: ''
    }
  },
  emits: ['style-applied', 'style-removed'],
  setup(props, { emit }) {
    // 响应式数据
    const loading = ref(false)
    const uploading = ref(false)
    const showUploadDialog = ref(false)
    const sldStyles = ref([])
    const currentStyle = ref(null)
    const selectedGeometryType = ref('')
    const selectedStyleId = ref(null)
    const applyingStyleId = ref(null)
    const deletingStyleId = ref(null)
    const fileList = ref([])
    
    // 设备类型检测
    const isDesktop = ref(getDeviceType() === 'desktop')
    
    // 监听窗口大小变化，更新设备类型
    const handleResize = () => {
      isDesktop.value = getDeviceType() === 'desktop'
    }
    
    // 编辑相关状态
    const showEditDialog = ref(false)
    const editingStyle = ref(null)
    const saving = ref(false)
    const loadingContent = ref(false)
    const editFormRef = ref()
    
    // 编辑表单
    const editForm = reactive({
      name: '',
      description: '',
      geometry_type: '',
      content: ''
    })
    
    // 编辑表单验证规则
    const editRules = {
      name: [
        { required: true, message: '请输入样式名称', trigger: 'blur' }
      ],
      geometry_type: [
        { required: true, message: '请选择几何类型', trigger: 'change' }
      ],
      content: [
        { required: true, message: '请输入SLD内容', trigger: 'blur' }
      ]
    }

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
      file: [
        { required: true, message: '请选择SLD文件', trigger: 'change' }
      ]
    }

    const uploadFormRef = ref()
    const uploadRef = ref()

    // 计算属性
    const filteredStyles = computed(() => {
      if (!selectedGeometryType.value) return []
      return sldStyles.value.filter(style => style.geometry_type === selectedGeometryType.value)
    })

    // 加载SLD样式列表
    const loadSldStyles = async () => {
      try {
        loading.value = true
        const response = await sldStyleApi.getSldStyles()
        sldStyles.value = response.styles || []
      } catch (error) {
        console.error('加载SLD样式列表失败:', error)
        ElMessage.error('加载SLD样式列表失败')
      } finally {
        loading.value = false
      }
    }

    // 加载当前图层的SLD样式
    const loadCurrentLayerStyle = async () => {
      try {
        const response = await sldStyleApi.getLayerSldStyle(props.layerId)
        currentStyle.value = response.data || null
        if (currentStyle.value) {
          selectedGeometryType.value = currentStyle.value.geometry_type
          selectedStyleId.value = currentStyle.value.sld_style_id
        }
      } catch (error) {
        if (error.response?.status !== 404) {
          console.error('加载图层当前样式失败:', error)
          ElMessage.error('加载图层当前样式失败')
        }
        currentStyle.value = null
      }
    }

    // 刷新样式
    const refreshStyles = async () => {
      await Promise.all([
        loadSldStyles(),
        loadCurrentLayerStyle()
      ])
    }

    // 几何类型变化处理
    const onGeometryTypeChange = () => {
      selectedStyleId.value = null
    }

    // 选择样式
    const selectStyle = (style) => {
      selectedStyleId.value = style.id
    }

    // 应用样式
    const applyStyle = async (style) => {
      try {
        applyingStyleId.value = style.id
        
        await sldStyleApi.applySldStyleToLayer({
          layer_id: props.layerId,
          sld_style_id: style.id
        })
        
        ElMessage.success('SLD样式应用成功')
        currentStyle.value = {
          ...style,
          sld_style_id: style.id,
          applied_at: new Date().toISOString()
        }
        selectedStyleId.value = style.id
        
        emit('style-applied', style)
      } catch (error) {
        console.error('应用SLD样式失败:', error)
        ElMessage.error(error.response?.data?.error || '应用SLD样式失败')
      } finally {
        applyingStyleId.value = null
      }
    }

    // 移除当前样式
    const removeCurrentStyle = async () => {
      try {
        await ElMessageBox.confirm('确定要移除当前应用的SLD样式吗？', '确认移除', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        await sldStyleApi.removeLayerSldStyle(props.layerId)
        
        ElMessage.success('SLD样式移除成功')
        currentStyle.value = null
        selectedStyleId.value = null
        
        emit('style-removed')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('移除SLD样式失败:', error)
          ElMessage.error('移除SLD样式失败')
        }
      }
    }

    // 下载样式
    const downloadStyle = async (styleId) => {
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

    // 删除样式
    const deleteStyle = async (styleId) => {
      try {
        await ElMessageBox.confirm('确定要删除这个SLD样式吗？删除后无法恢复。', '确认删除', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        deletingStyleId.value = styleId
        await sldStyleApi.deleteSldStyle(styleId)
        
        ElMessage.success('SLD样式删除成功')
        
        // 如果删除的是当前选中的样式，清除选中状态
        if (selectedStyleId.value === styleId) {
          selectedStyleId.value = null
        }
        
        // 如果删除的是当前应用的样式，清除当前样式
        if (currentStyle.value && currentStyle.value.sld_style_id === styleId) {
          currentStyle.value = null
        }
        
        // 刷新样式列表
        await loadSldStyles()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除SLD样式失败:', error)
          ElMessage.error('删除SLD样式失败')
        }
      } finally {
        deletingStyleId.value = null
      }
    }

    // 表格行点击处理
    const handleRowClick = (row) => {
      selectStyle(row)
    }

    // 获取表格行类名
    const getRowClassName = ({ row }) => {
      return selectedStyleId.value === row.id ? 'selected-row' : ''
    }

    // 上传SLD文件
    const uploadSldFile = async () => {
      try {
        // 检查是否选择了几何类型
        if (!selectedGeometryType.value) {
          ElMessage.error('请先在主界面选择图层几何类型')
          return
        }
        
        await uploadFormRef.value.validate()
        
        if (!uploadForm.file) {
          ElMessage.error('请选择SLD文件')
          return
        }

        // 验证必填字段
        if (!uploadForm.name) {
          ElMessage.error('样式名称不能为空')
          return
        }

        uploading.value = true
        
        const formData = new FormData()
        formData.append('name', uploadForm.name)
        formData.append('description', uploadForm.description || '')
        // 使用主界面选择的几何类型
        formData.append('geometry_type', selectedGeometryType.value)
        formData.append('file', uploadForm.file)

        // 打印 FormData 内容用于调试
        console.log('FormData 内容:')
        for (let pair of formData.entries()) {
          console.log(pair[0] + ':', pair[1])
        }

        await sldStyleApi.uploadSldFile(formData)
        
        ElMessage.success('SLD文件上传成功')
        showUploadDialog.value = false
        resetUploadForm()
        loadSldStyles()
      } catch (error) {
        console.error('上传SLD文件失败:', error)
        console.error('错误详情:', error.response?.data)
        ElMessage.error(error.response?.data?.error || '上传SLD文件失败')
      } finally {
        uploading.value = false
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
      uploadForm.file = null
      fileList.value = []
      uploadFormRef.value?.resetFields()
    }
    
    // 编辑样式
    const editStyle = async (style) => {
      try {
        editingStyle.value = style
        editForm.name = style.name
        editForm.description = style.description || ''
        editForm.geometry_type = style.geometry_type
        editForm.content = ''
        
        showEditDialog.value = true
        
        // 加载SLD文件内容
        await loadSldContent(style.id)
        
      } catch (error) {
        console.error('打开编辑对话框失败:', error)
        ElMessage.error('打开编辑对话框失败')
      }
    }

    // 加载SLD文件内容
    const loadSldContent = async (styleId) => {
      try {
        loadingContent.value = true
        const response = await sldStyleApi.getSldStyleContent(styleId)
        editForm.content = response.content || ''
      } catch (error) {
        console.error('加载SLD内容失败:', error)
        ElMessage.error('加载SLD内容失败')
      } finally {
        loadingContent.value = false
      }
    }
    
    // 保存编辑的样式
    const saveEditedStyle = async () => {
      try {
        await editFormRef.value.validate()
        
        saving.value = true
        
        // 构建更新数据
        const updateData = {
          name: editForm.name,
          description: editForm.description,
          geometry_type: editForm.geometry_type,
          content: editForm.content
        }
        
        // 调用API更新SLD内容
        await sldStyleApi.updateSldStyleContent(editingStyle.value.id, updateData)
        
        ElMessage.success('SLD样式更新成功')
        showEditDialog.value = false
        editingStyle.value = null
        
        // 刷新样式列表
        await loadSldStyles()
        
      } catch (error) {
        console.error('保存样式失败:', error)
        ElMessage.error(error.response?.data?.error || '保存样式失败')
      } finally {
        saving.value = false
      }
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

    // 监听图层几何类型变化
    watch(() => props.layerGeometryType, (newType) => {
      if (newType) {
        selectedGeometryType.value = newType
      }
    }, { immediate: true })

    // 初始化
    onMounted(() => {
      refreshStyles()
      // 监听窗口大小变化
      window.addEventListener('resize', handleResize)
    })

    // 组件卸载时移除事件监听
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    return {
      loading,
      uploading,
      showUploadDialog,
      sldStyles,
      currentStyle,
      selectedGeometryType,
      selectedStyleId,
      applyingStyleId,
      deletingStyleId,
      isDesktop,
      fileList,
      uploadForm,
      uploadRules,
      uploadFormRef,
      uploadRef,
      filteredStyles,
      loadSldStyles,
      loadCurrentLayerStyle,
      refreshStyles,
      onGeometryTypeChange,
      selectStyle,
      applyStyle,
      removeCurrentStyle,
      downloadStyle,
      deleteStyle,
      handleRowClick,
      getRowClassName,
      uploadSldFile,
      handleFileChange,
      getGeometryTypeLabel,
      getGeometryTypeTagType,
      formatFileSize,
      formatDate,
      // 编辑相关
      showEditDialog,
      editingStyle,
      saving,
      loadingContent,
      editForm,
      editRules,
      editFormRef,
      editStyle,
      loadSldContent,
      saveEditedStyle
    }
  }
}
</script>

<style scoped>
.sld-style-selector {
  padding: 20px;
}

/* 样式预览 */
.style-preview {
  padding: 20px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f5f7fa;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-point {
  display: flex;
  align-items: center;
  justify-content: center;
}

.point-sample {
  border-radius: 50%;
  border: 1px solid #333;
}

.preview-line {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.line-sample {
  width: 100px;
  border-radius: 2px;
}

.preview-polygon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.polygon-sample {
  width: 60px;
  height: 40px;
  border-radius: 4px;
  border-style: solid;
}

.sld-style-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sld-style-selector-header h4 {
  margin: 0;
  color: #303133;
}

.current-style-info {
  margin-bottom: 20px;
}

.current-style-details {
  margin-bottom: 10px;
}

.current-style-details p {
  margin: 5px 0;
}

.current-style-actions {
  margin-top: 10px;
}

.geometry-type-selector {
  margin-bottom: 20px;
}

.sld-style-list {
  margin-top: 20px;
}

.style-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.style-list-header h5 {
  margin: 0;
  color: #606266;
}

.loading-container,
.empty-container {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.loading-container .el-icon {
  font-size: 24px;
  margin-bottom: 10px;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.style-card {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.style-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.style-card.selected {
  border-color: #409eff;
  background: #f0f9ff;
}

.style-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.style-card-header h6 {
  margin: 0;
  color: #303133;
  font-size: 14px;
}

.style-card-content {
  margin-bottom: 15px;
}

.style-description {
  color: #606266;
  font-size: 12px;
  margin: 5px 0;
  line-height: 1.4;
}

.style-info {
  color: #909399;
  font-size: 11px;
  margin: 5px 0;
}

.style-card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
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

/* SLD内容编辑器样式 */
.sld-content-editor {
  font-family: 'Courier New', monospace;
}

.sld-content-editor .el-textarea__inner {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}

.editor-tips {
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.editor-tips p {
  margin: 5px 0;
  color: #606266;
}

.editor-tips p:first-child {
  color: #409eff;
  font-weight: bold;
}

/* 表格样式 */
.style-table-container {
  background: #fff;
  border-radius: 4px;
  padding: 0;
}

.style-table-container :deep(.el-table) {
  border-radius: 4px;
}

.style-table-container :deep(.el-table__row) {
  cursor: pointer;
}

.style-table-container :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.style-table-container :deep(.el-table__row.selected-row) {
  background-color: #f0f9ff;
}

.style-table-container :deep(.el-table__row.selected-row:hover) {
  background-color: #e0f2fe;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .style-table-container {
    display: none;
  }
  
  .style-grid {
    display: block;
  }
  
  .style-card {
    margin-bottom: 15px;
  }
}

/* 电脑端隐藏卡片网格 */
@media (min-width: 769px) {
  .style-grid {
    display: none;
  }
}
</style>
