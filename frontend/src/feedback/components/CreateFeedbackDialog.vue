<template>
  <el-dialog
    v-model="visible"
    title="提交反馈"
    width="800px"
    :before-close="handleClose"
    class="create-feedback-dialog"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      class="feedback-form"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h3>基本信息</h3>
        
        <el-form-item label="反馈标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请简洁明了地描述您的反馈..."
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请详细描述您遇到的问题或建议..."
            :rows="6"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
      </div>

      <!-- 分类信息 -->
      <div class="form-section">
        <h3>分类信息</h3>
        
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="反馈分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择">
                <el-option
                  label="功能建议"
                  value="feature"
                >
                  <div class="option-detail">
                    <div class="option-title">功能建议</div>
                    <div class="option-desc">新功能需求或功能改进建议</div>
                  </div>
                </el-option>
                <el-option
                  label="问题反馈"
                  value="bug"
                >
                  <div class="option-detail">
                    <div class="option-title">问题反馈</div>
                    <div class="option-desc">发现的bug或异常问题</div>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="相关模块" prop="module">
              <el-select 
                v-model="form.module" 
                placeholder="请选择或输入模块"
                filterable
                allow-create
                default-first-option
              >
                <el-option
                  label="前端"
                  value="frontend"
                >
                  <div class="option-detail">
                    <div class="option-title">前端</div>
                    <div class="option-desc">用户界面、交互体验相关</div>
                  </div>
                </el-option>
                <el-option
                  label="后端"
                  value="backend"
                >
                  <div class="option-detail">
                    <div class="option-title">后端</div>
                    <div class="option-desc">服务器、数据处理相关</div>
                  </div>
                </el-option>
                <el-option
                  label="数据库"
                  value="database"
                >
                  <div class="option-detail">
                    <div class="option-title">数据库</div>
                    <div class="option-desc">数据存储、查询相关</div>
                  </div>
                </el-option>
                <el-option
                  label="API"
                  value="api"
                >
                  <div class="option-detail">
                    <div class="option-title">API</div>
                    <div class="option-desc">接口设计、调用相关</div>
                  </div>
                </el-option>
                <el-option
                  label="部署"
                  value="deployment"
                >
                  <div class="option-detail">
                    <div class="option-title">部署</div>
                    <div class="option-desc">发布、运维相关</div>
                  </div>
                </el-option>
                <el-option
                  label="文档"
                  value="documentation"
                >
                  <div class="option-detail">
                    <div class="option-title">文档</div>
                    <div class="option-desc">说明文档、帮助相关</div>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="修改类型" prop="type">
              <el-select 
                v-model="form.type" 
                placeholder="请选择或输入类型"
                filterable
                allow-create
                default-first-option
              >
                <el-option
                  label="界面优化"
                  value="ui"
                >
                  <div class="option-detail">
                    <div class="option-title">界面优化</div>
                    <div class="option-desc">UI设计、布局、样式相关</div>
                  </div>
                </el-option>
                <el-option
                  label="代码修改"
                  value="code"
                >
                  <div class="option-detail">
                    <div class="option-title">代码修改</div>
                    <div class="option-desc">功能逻辑、性能优化相关</div>
                  </div>
                </el-option>
                <el-option
                  label="性能优化"
                  value="performance"
                >
                  <div class="option-detail">
                    <div class="option-title">性能优化</div>
                    <div class="option-desc">响应速度、资源占用相关</div>
                  </div>
                </el-option>
                <el-option
                  label="功能新增"
                  value="feature"
                >
                  <div class="option-detail">
                    <div class="option-title">功能新增</div>
                    <div class="option-desc">新特性、新模块相关</div>
                  </div>
                </el-option>
                <el-option
                  label="架构调整"
                  value="architecture"
                >
                  <div class="option-detail">
                    <div class="option-title">架构调整</div>
                    <div class="option-desc">系统结构、技术栈相关</div>
                  </div>
                </el-option>
                <el-option
                  label="安全修复"
                  value="security"
                >
                  <div class="option-detail">
                    <div class="option-title">安全修复</div>
                    <div class="option-desc">安全漏洞、权限控制相关</div>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="form.priority">
            <el-radio-button label="low">低</el-radio-button>
            <el-radio-button label="medium">中</el-radio-button>
            <el-radio-button label="high">高</el-radio-button>
            <el-radio-button label="urgent">紧急</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </div>

      <!-- 附件上传 -->
      <div class="form-section">
        <h3>附件上传</h3>
        
        <el-form-item label="文件附件">
          <div class="upload-area">
            <el-upload
              ref="uploadRef"
              :file-list="fileList"
              :auto-upload="false"
              :multiple="true"
              :limit="5"
              :accept="acceptTypes"
              :before-upload="beforeUpload"
              @change="onFileChange"
              @remove="onFileRemove"
              drag
              class="upload-dragger"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 jpg/png/gif 图片，pdf/doc/txt 文档，zip/rar 压缩包，单个文件不超过 10MB
                </div>
              </template>
            </el-upload>

            <!-- 截图工具 -->
            <div class="screenshot-tools">
              <el-button
                type="primary"
                icon="Camera"
                @click="captureScreenshot"
                :disabled="!isScreenCaptureSupported"
              >
                截图
              </el-button>
              <el-button
                type="info"
                icon="Picture"
                @click="pasteFromClipboard"
              >
                从剪贴板粘贴
              </el-button>
            </div>
          </div>
        </el-form-item>

        <!-- 文件预览 -->
        <div v-if="fileList.length > 0" class="file-preview">
          <h4>已选择的文件：</h4>
          <div class="file-list">
            <div
              v-for="file in fileList"
              :key="file.uid"
              class="file-item"
            >
              <el-icon class="file-icon">
                <Document v-if="isDocument(file)" />
                <Picture v-else-if="isImage(file)" />
                <Folder v-else />
              </el-icon>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
              <el-button
                type="danger"
                size="small"
                icon="Delete"
                @click="removeFile(file)"
                circle
              />
            </div>
          </div>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="submitFeedback"
        >
          {{ submitting ? '提交中...' : '提交反馈' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  Picture,
  Document,
  Folder
} from '@element-plus/icons-vue'
import feedbackApi from '../api/feedbackApi'

export default {
  name: 'CreateFeedbackDialog',
  components: {
    UploadFilled,
    Picture,
    Document,
    Folder
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'success'],
  setup(props, { emit }) {
    const formRef = ref()
    const uploadRef = ref()
    const submitting = ref(false)
    const fileList = ref([])

    // 表单数据
    const form = reactive({
      title: '',
      description: '',
      category: '',
      module: '',
      type: '',
      priority: 'medium'
    })

    // 表单验证规则
    const rules = {
      title: [
        { required: true, message: '请输入反馈标题', trigger: 'blur' },
        { min: 5, max: 200, message: '标题长度应在 5 到 200 个字符', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入详细描述', trigger: 'blur' },
        { min: 10, message: '描述至少需要 10 个字符', trigger: 'blur' }
      ],
      category: [
        { required: true, message: '请选择反馈分类', trigger: 'change' }
      ],
      module: [
        { required: true, message: '请选择相关模块', trigger: 'change' }
      ],
      type: [
        { required: true, message: '请选择修改类型', trigger: 'change' }
      ]
    }

    // 对话框可见性
    const visible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    // 支持的文件类型
    const acceptTypes = '.jpg,.jpeg,.png,.gif,.bmp,.webp,.pdf,.doc,.docx,.txt,.md,.zip,.rar,.7z'

    // 检查是否支持屏幕截图
    const isScreenCaptureSupported = computed(() => {
      return navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia
    })

    // 文件类型判断
    const isImage = (file) => {
      return file.type?.startsWith('image/') || /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(file.name)
    }

    const isDocument = (file) => {
      return /\.(pdf|doc|docx|txt|md)$/i.test(file.name)
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

    // 文件上传前检查
    const beforeUpload = (file) => {
      const isValidType = acceptTypes.split(',').some(type => 
        file.name.toLowerCase().endsWith(type.trim().substring(1))
      )
      
      if (!isValidType) {
        ElMessage.error('不支持的文件类型')
        return false
      }

      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        ElMessage.error('文件大小不能超过 10MB')
        return false
      }

      return true
    }

    // 文件变化处理
    const onFileChange = (file, files) => {
      fileList.value = files
    }

    // 移除文件
    const onFileRemove = (file, files) => {
      fileList.value = files
    }

    const removeFile = (file) => {
      const index = fileList.value.findIndex(f => f.uid === file.uid)
      if (index > -1) {
        fileList.value.splice(index, 1)
      }
    }

    // 截图功能
    const captureScreenshot = async () => {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: true
        })
        
        const video = document.createElement('video')
        video.srcObject = stream
        video.play()

        video.addEventListener('loadedmetadata', () => {
          const canvas = document.createElement('canvas')
          canvas.width = video.videoWidth
          canvas.height = video.videoHeight
          
          const ctx = canvas.getContext('2d')
          ctx.drawImage(video, 0, 0)
          
          canvas.toBlob((blob) => {
            const file = new File([blob], `screenshot-${Date.now()}.png`, {
              type: 'image/png'
            })
            
            // 添加到文件列表
            const fileObj = {
              uid: Date.now(),
              name: file.name,
              size: file.size,
              type: file.type,
              raw: file,
              status: 'ready'
            }
            
            fileList.value.push(fileObj)
            ElMessage.success('截图成功')
          })
          
          // 停止屏幕共享
          stream.getTracks().forEach(track => track.stop())
        })
      } catch (error) {
        console.error('截图失败:', error)
        ElMessage.error('截图失败，请检查浏览器权限')
      }
    }

    // 从剪贴板粘贴
    const pasteFromClipboard = async () => {
      try {
        const clipboardItems = await navigator.clipboard.read()
        
        for (const clipboardItem of clipboardItems) {
          for (const type of clipboardItem.types) {
            if (type.startsWith('image/')) {
              const blob = await clipboardItem.getType(type)
              const file = new File([blob], `clipboard-${Date.now()}.png`, {
                type: blob.type
              })
              
              const fileObj = {
                uid: Date.now(),
                name: file.name,
                size: file.size,
                type: file.type,
                raw: file,
                status: 'ready'
              }
              
              fileList.value.push(fileObj)
              ElMessage.success('粘贴成功')
              return
            }
          }
        }
        
        ElMessage.warning('剪贴板中没有图片')
      } catch (error) {
        console.error('粘贴失败:', error)
        ElMessage.error('粘贴失败，请检查浏览器权限')
      }
    }

    // 提交反馈
    const submitFeedback = async () => {
      try {
        // 表单验证
        await formRef.value.validate()
        
        submitting.value = true

        // 创建反馈
        const response = await feedbackApi.createFeedback(form)
        
        if (response.code !== 201) {
          throw new Error(response.message || '提交失败')
        }

        const feedbackId = response.data.feedback_id

        // 上传附件
        if (fileList.value.length > 0) {
          for (const file of fileList.value) {
            if (file.raw) {
              try {
                await feedbackApi.uploadAttachment(
                  feedbackId, 
                  file.raw, 
                  file.name.includes('screenshot') || file.name.includes('clipboard')
                )
              } catch (uploadError) {
                console.error('文件上传失败:', uploadError)
                ElMessage.warning(`文件 "${file.name}" 上传失败`)
              }
            }
          }
        }

        ElMessage.success('反馈提交成功')
        emit('success')
        handleClose()
        
      } catch (error) {
        console.error('提交反馈失败:', error)
        ElMessage.error(error.message || '提交失败')
      } finally {
        submitting.value = false
      }
    }

    // 关闭对话框
    const handleClose = () => {
      // 重置表单
      formRef.value?.resetFields()
      fileList.value = []
      Object.keys(form).forEach(key => {
        if (key === 'priority') {
          form[key] = 'medium'
        } else {
          form[key] = ''
        }
      })
      
      visible.value = false
    }

    return {
      formRef,
      uploadRef,
      submitting,
      form,
      rules,
      visible,
      fileList,
      acceptTypes,
      isScreenCaptureSupported,

      // 方法
      beforeUpload,
      onFileChange,
      onFileRemove,
      removeFile,
      captureScreenshot,
      pasteFromClipboard,
      submitFeedback,
      handleClose,

      // 辅助函数
      isImage,
      isDocument,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.create-feedback-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #ebeef5;
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.form-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.option-detail {
  padding: 4px 0;
}

.option-title {
  font-weight: 600;
  color: #303133;
}

.option-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* 支持自定义输入的选择框样式 */
.feedback-form .el-select.is-filterable .el-input .el-input__wrapper {
  border-color: #dcdfe6;
  transition: border-color 0.2s ease;
}

.feedback-form .el-select.is-filterable:hover .el-input .el-input__wrapper {
  border-color: #c0c4cc;
}

.feedback-form .el-select.is-filterable.is-focus .el-input .el-input__wrapper {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 选择框的自定义提示样式 */
.el-select-dropdown .el-select-dropdown__empty {
  color: #909399;
  font-size: 13px;
}

.el-select-dropdown .el-select-dropdown__empty::before {
  content: "💡 ";
}

.upload-area {
  width: 100%;
}

.upload-dragger {
  width: 100%;
}

.screenshot-tools {
  margin-top: 12px;
  display: flex;
  gap: 12px;
}

.file-preview {
  margin-top: 20px;
}

.file-preview h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
}

.file-icon {
  font-size: 16px;
  color: #409eff;
}

.file-name {
  flex: 1;
  color: #303133;
}

.file-size {
  color: #909399;
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .create-feedback-dialog :deep(.el-dialog) {
    width: 95vw;
    margin: 5vh auto;
  }
  
  .form-section {
    margin-bottom: 24px;
    padding-bottom: 16px;
  }
  
  .screenshot-tools {
    flex-direction: column;
  }
  
  .file-item {
    flex-wrap: wrap;
  }
  
  .file-name {
    word-break: break-all;
  }
}
</style> 