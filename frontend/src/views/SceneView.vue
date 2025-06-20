<template>
  <div class="scene-view">
    <div class="scene-header">
      <h1>场景管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建场景
        </el-button>
        <el-button @click="refreshScenes">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="scene-content">
      <!-- 搜索和筛选 -->
      <div class="search-bar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="场景名称">
            <el-input 
              v-model="searchForm.name" 
              placeholder="请输入场景名称"
              @change="searchScenes"
              clearable
            />
          </el-form-item>
          <el-form-item label="创建时间">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="searchScenes"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchScenes">搜索</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 场景列表 -->
      <div class="scenes-grid">
      
        
        <div 
          v-for="scene in filteredScenes" 
          :key="scene.id" 
          class="scene-card"
          @click="viewScene(scene)"
        >
          <div class="scene-card-header">
            <h3>{{ scene.name }}</h3>
            <div class="scene-actions">
              <el-button 
                size="small" 
                type="primary" 
                @click.stop="editScene(scene)"
              >
                编辑
              </el-button>
              <el-button 
                size="small" 
                type="success" 
                @click.stop="viewScene(scene)"
              >
                查看
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click.stop="deleteScene(scene)"
              >
                删除
              </el-button>
            </div>
          </div>
          
          <div class="scene-card-body">
            <p class="scene-description">{{ scene.description || '暂无描述' }}</p>
            
            <div class="scene-info">
              <div class="info-item">
                <span class="label">图层数量</span>
                <span class="value">{{ scene.layer_count || 0 }} 个</span>
              </div>
              <div class="info-item">
                <span class="label">创建者</span>
                <span class="value">{{ scene.creator || '未知' }}</span>
              </div>
              <div class="info-item">
                <span class="label">创建时间</span>
                <span class="value">{{ formatDateShort(scene.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="label">最后修改</span>
                <span class="value">{{ formatDateShort(scene.updated_at) }}</span>
              </div>
            </div>
          </div>

          <div class="scene-card-footer">
            <el-tag v-if="scene.is_default" type="warning" size="small">默认场景</el-tag>
            <el-tag v-if="scene.layer_count > 0" type="success" size="small">
              {{ scene.layer_count }} 个图层
            </el-tag>
            <el-tag v-else type="info" size="small">空场景</el-tag>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredScenes.length === 0" class="empty-state">
          <el-empty description="暂无场景数据">
            <el-button type="primary" @click="showCreateDialog = true">
              创建第一个场景
            </el-button>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 创建/编辑场景对话框 -->
    <el-dialog 
      :title="dialogMode === 'create' ? '创建场景' : '编辑场景'" 
      v-model="showCreateDialog" 
      width="500px"
    >
      <el-form :model="sceneForm" :rules="sceneRules" ref="sceneFormRef" label-width="80px">
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="sceneForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="场景描述" prop="description">
          <el-input 
            v-model="sceneForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入场景描述" 
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="sceneForm.is_default" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveScene" :loading="saving">
            {{ dialogMode === 'create' ? '创建' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 场景详情对话框 -->
    <el-dialog 
      title="场景详情" 
      v-model="showDetailDialog" 
      width="800px"
    >
      <div v-if="currentScene" class="scene-detail">
        <div class="detail-header">
          <h3>{{ currentScene.name }}</h3>
          <p>{{ currentScene.description }}</p>
        </div>
        
        <div class="detail-body">
          <h4>场景图层 ({{ sceneLayers.length }})</h4>
          <el-table :data="sceneLayers" style="width: 100%">
            <el-table-column prop="layer_name" label="图层名称" />
            <el-table-column prop="file_type" label="数据类型" width="100" />
            <el-table-column prop="service_type" label="服务类型" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag v-if="scope.row.is_visible" type="success" size="small">可见</el-tag>
                <el-tag v-else type="info" size="small">隐藏</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" @click="removeLayerFromScene(scope.row)">
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button type="primary" @click="openMapWithScene">在地图中打开</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import gisApi from '@/api/gis'

export default {
  name: 'SceneView',
  components: {
    Plus,
    Refresh
  },
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const scenes = ref([])
    const showCreateDialog = ref(false)
    const showDetailDialog = ref(false)
    const saving = ref(false)
    const dialogMode = ref('create') // 'create' | 'edit'
    const currentScene = ref(null)
    const sceneLayers = ref([])
    const sceneFormRef = ref(null)
    
    // 搜索表单
    const searchForm = reactive({
      name: '',
      dateRange: null
    })
    
    // 场景表单
    const sceneForm = reactive({
      id: null,
      name: '',
      description: '',
      is_default: false
    })
    
    // 表单验证规则
    const sceneRules = {
      name: [
        { required: true, message: '请输入场景名称', trigger: 'blur' },
        { min: 1, max: 50, message: '场景名称长度在 1 到 50 个字符', trigger: 'blur' }
      ]
    }
    
    // 计算属性
    const filteredScenes = computed(() => {
      let result = scenes.value
      
      // 按名称筛选
      if (searchForm.name) {
        result = result.filter(scene => 
          scene.name.toLowerCase().includes(searchForm.name.toLowerCase())
        )
      }
      
      // 按时间范围筛选
      if (searchForm.dateRange && searchForm.dateRange.length === 2) {
        const [startDate, endDate] = searchForm.dateRange
        result = result.filter(scene => {
          const sceneDate = new Date(scene.created_at)
          return sceneDate >= startDate && sceneDate <= endDate
        })
      }
      
      return result
    })
    
    // 方法
    const loadScenes = async () => {
      try {
        
        
        const response = await gisApi.getScenes()
       
        
        if (response && response.data.scenes) {
          scenes.value = response.data.scenes

        } else {
          console.warn('API响应格式异常，使用空数组')
          scenes.value = []
        }
        
        console.log('最终场景数量:', scenes.value.length)
        console.log('filteredScenes数量:', filteredScenes.value.length)
        
      } catch (error) {
        console.error('加载场景列表失败:', error)
        console.error('错误类型:', error.constructor.name)
        console.error('错误信息:', error.message)
        console.error('HTTP状态:', error.response?.status)
        console.error('响应数据:', error.response?.data)
        console.error('请求配置:', error.config)
        
        scenes.value = []
        ElMessage.error('加载场景列表失败: ' + (error.response?.data?.error || error.message))
      }
    }
    
    const refreshScenes = () => {
      loadScenes()
      ElMessage.success('场景列表已刷新')
    }
    
    const searchScenes = () => {
      // 搜索逻辑已在computed中实现
    }
    
    const resetSearch = () => {
      searchForm.name = ''
      searchForm.dateRange = null
    }
    
    const resetSceneForm = () => {
      sceneForm.id = null
      sceneForm.name = ''
      sceneForm.description = ''
      sceneForm.is_default = false
    }
    
    const editScene = (scene) => {
      dialogMode.value = 'edit'
      sceneForm.id = scene.id
      sceneForm.name = scene.name
      sceneForm.description = scene.description || ''
      sceneForm.is_default = scene.is_default || false
      showCreateDialog.value = true
    }
    
    const saveScene = async () => {
      if (!sceneFormRef.value) return
      
      try {
        await sceneFormRef.value.validate()
        saving.value = true
        
        if (dialogMode.value === 'create') {
          await gisApi.createScene(sceneForm)
          ElMessage.success('场景创建成功')
        } else {
          await gisApi.updateScene(sceneForm.id, sceneForm)
          ElMessage.success('场景更新成功')
        }
        
        showCreateDialog.value = false
        resetSceneForm()
        await loadScenes()
        
      } catch (error) {
        console.error('保存场景失败:', error)
        ElMessage.error('保存场景失败')
      } finally {
        saving.value = false
      }
    }
    
    const deleteScene = async (scene) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除场景 "${scene.name}" 吗？此操作不可恢复。`,
          '删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await gisApi.deleteScene(scene.id)
        ElMessage.success('场景删除成功')
        await loadScenes()
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除场景失败:', error)
          ElMessage.error('删除场景失败')
        }
      }
    }
    
    const viewScene = async (scene) => {
      try {
        currentScene.value = scene
        
        // 加载场景的图层信息
        const response = await gisApi.getScene(scene.id)
        sceneLayers.value = response.layers || []
        
        showDetailDialog.value = true
        
      } catch (error) {
        console.error('加载场景详情失败:', error)
        ElMessage.error('加载场景详情失败')
      }
    }
    
    const removeLayerFromScene = async (layer) => {
      try {
        await ElMessageBox.confirm(
          `确定要从场景中移除图层 "${layer.layer_name}" 吗？`,
          '移除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await gisApi.removeLayerFromScene(currentScene.value.id, layer.id)
        ElMessage.success('图层移除成功')
        
        // 重新加载场景详情
        await viewScene(currentScene.value)
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('移除图层失败:', error)
          ElMessage.error('移除图层失败')
        }
      }
    }
    
    const openMapWithScene = () => {
      showDetailDialog.value = false
      router.push({
        name: 'Map',
        query: { sceneId: currentScene.value.id }
      })
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }

    const formatDateShort = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      
      if (days === 0) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      } else if (days < 7) {
        return `${days}天前`
      } else if (days < 30) {
        return `${Math.floor(days / 7)}周前`
      } else {
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
      }
    }
    
    // 生命周期
    onMounted(() => {
      loadScenes()
    })
    
    return {
      // 响应式数据
      scenes,
      filteredScenes,
      showCreateDialog,
      showDetailDialog,
      saving,
      dialogMode,
      currentScene,
      sceneLayers,
      sceneFormRef,
      searchForm,
      sceneForm,
      sceneRules,
      
      // 方法
      loadScenes,
      refreshScenes,
      searchScenes,
      resetSearch,
      resetSceneForm,
      editScene,
      saveScene,
      deleteScene,
      viewScene,
      removeLayerFromScene,
      openMapWithScene,
      formatDate,
      formatDateShort
    }
  }
}
</script>

<style scoped>
.scene-view {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.scene-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.scene-header h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.scene-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-bar {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.scenes-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  padding: 10px;
}

.scene-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  height: fit-content;
  max-height: 280px;
}

.scene-card:hover {
  border-color: #409eff;
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.12);
}

.scene-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.scene-card-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.scene-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
  flex-shrink: 0;
}

.scene-card:hover .scene-actions {
  opacity: 1;
}

.scene-actions .el-button {
  padding: 4px 8px;
  font-size: 12px;
  height: 24px;
}

.scene-card-body {
  margin-bottom: 12px;
}

.scene-description {
  color: #606266;
  margin: 0 0 12px 0;
  line-height: 1.4;
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-height: 36px;
}

.scene-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
  font-size: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-item .label {
  color: #909399;
  font-size: 11px;
}

.info-item .value {
  color: #606266;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scene-card-footer {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.scene-card-footer .el-tag {
  font-size: 11px;
  height: 20px;
  line-height: 18px;
  padding: 0 6px;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.scene-detail {
  padding: 10px 0;
}

.detail-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.detail-header h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 20px;
}

.detail-header p {
  margin: 0;
  color: #606266;
  line-height: 1.5;
}

.detail-body h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 