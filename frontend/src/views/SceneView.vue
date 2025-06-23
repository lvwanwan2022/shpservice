<template>
  <div class="scene-view">
    <div class="scene-header">
      <h1>场景管理</h1>
      <div style="display: flex; gap: 10px; align-items: center;">
        <!-- 🔥 临时测试按钮 -->
        <el-button size="small" type="warning" @click="clearUserCache">清除缓存</el-button>
        <el-button size="small" type="info" @click="testPermissionCheck">测试权限</el-button>
        
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
                :disabled="!canEditScene(scene)"
                @click.stop="editScene(scene)"
                :title="canEditScene(scene) ? '编辑场景' : '只有创建者可以编辑'"
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
                :disabled="!canDeleteScene(scene)"
                @click.stop="deleteScene(scene)"
                :title="canDeleteScene(scene) ? '删除场景' : '只有创建者可以删除'"
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
            <el-tag v-if="scene.is_public" type="success" size="small">公开</el-tag>
            <el-tag v-else type="warning" size="small">私有</el-tag>
            <el-tag v-if="scene.layer_count > 0" type="info" size="small">
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
        <el-form-item label="访问权限">
          <el-switch 
            v-model="sceneForm.is_public" 
            active-text="公开"
            inactive-text="私有"
            :active-value="true"
            :inactive-value="false"
          />
          <div class="form-hint">
            <span style="font-size: 12px; color: #909399;">
              公开场景所有用户可见，私有场景仅创建者可见
            </span>
          </div>
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
      @close="handleDetailDialogClose"
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
            <el-table-column label="状态" width="120">
              <template #default="scope">
                <el-switch
                  v-model="scope.row.visibility"
                  active-text="显"
                  inactive-text="隐"
                  :loading="scope.row.updating || false"
                  @change="toggleLayerVisibility(scope.row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button 
                  size="small" 
                  :disabled="!canEditScene(currentScene)"
                  @click="removeLayerFromScene(scope.row)"
                  :title="canEditScene(currentScene) ? '移除图层' : '只有创建者可以移除图层'"
                >
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
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import gisApi from '@/api/gis'
import authService from '@/auth/authService'

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
    
    // 获取当前用户信息
    const currentUser = ref(null)
    
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
      is_public: true
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
    
    // 检查用户是否有场景操作权限
    const canEditScene = (scene) => {
      if (!currentUser.value) {
        console.log('权限检查失败: 用户未登录')
        return false
      }
      
      if (!scene) {
        console.log('权限检查失败: 场景信息为空')
        return false
      }
      
      // 转换为字符串进行比较
      const currentUserIdStr = String(currentUser.value.id)
      const sceneUserIdStr = String(scene.user_id)
      
      const hasPermission = currentUserIdStr === sceneUserIdStr
      console.log(`权限检查: 用户ID=${currentUserIdStr}, 场景创建者ID=${sceneUserIdStr}, 结果=${hasPermission ? '有权限' : '无权限'}`)
      
      return hasPermission
    }
    
    const canDeleteScene = (scene) => {
      return canEditScene(scene)
    }
    
    // 🔥 临时方法：清除用户信息缓存
    const clearUserCache = () => {
      console.log('清除用户信息缓存...')
      localStorage.removeItem('user_info')
      localStorage.removeItem('auth_token')
      ElMessage.success('缓存已清除，请重新登录')
      window.location.href = '/login'
    }
    
    // 🔥 临时方法：测试权限检查
    const testPermissionCheck = () => {
      console.log('=== 权限检查测试 ===')
      console.log('当前用户:', currentUser.value)
      console.log('场景列表:', scenes.value.map(s => ({
        id: s.id,
        name: s.name,
        user_id: s.user_id,
        creator: s.creator
      })))
      
      if (scenes.value.length > 0) {
        const firstScene = scenes.value[0]
        console.log('测试第一个场景的权限:', canEditScene(firstScene))
      }
    }
    
    // 方法
    const loadScenes = async () => {
      try {
        console.log('开始加载场景列表...')
        
        const response = await gisApi.getScenes()
        
        console.log('API响应:', response)
        
        if (response && response.data.scenes) {
          scenes.value = response.data.scenes
          console.log('加载的场景数量:', scenes.value.length)
          console.log('场景详情:', scenes.value.map(s => ({
            id: s.id,
            name: s.name,
            is_public: s.is_public,
            creator: s.creator,
            user_id: s.user_id
          })))
        } else {
          console.warn('API响应格式异常，使用空数组')
          scenes.value = []
        }
        
      } catch (error) {
        console.error('加载场景列表失败:', error)
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
      sceneForm.is_public = true
    }
    
    const editScene = (scene) => {
      // 权限检查
      if (!canEditScene(scene)) {
        ElMessage.warning('只有场景创建者可以编辑场景')
        return
      }
      
      dialogMode.value = 'edit'
      sceneForm.id = scene.id
      sceneForm.name = scene.name
      sceneForm.description = scene.description || ''
      sceneForm.is_public = scene.is_public || false
      showCreateDialog.value = true
    }
    
    const saveScene = async () => {
      if (!sceneFormRef.value) return
      
      try {
        await sceneFormRef.value.validate()
        saving.value = true
        
        // 调试日志
        console.log('保存场景数据:', sceneForm)
        
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
      // 权限检查
      if (!canDeleteScene(scene)) {
        ElMessage.warning('只有场景创建者可以删除场景')
        return
      }
      
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
          if (error.response?.status === 403) {
            ElMessage.error('权限不足：只有场景创建者可以删除场景')
          } else {
            ElMessage.error('删除场景失败')
          }
        }
      }
    }
    
    const viewScene = async (scene) => {
      try {
        currentScene.value = scene
        
        // 先关闭对话框，确保状态重置
        showDetailDialog.value = false
        
        // 清空之前的图层数据
        sceneLayers.value = []
        
        // 使用 nextTick 确保 DOM 更新完成
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // 加载场景的图层信息
        const response = await gisApi.getScene(scene.id)
        
        if (response && response.data && response.data.layers) {
          sceneLayers.value = response.data.layers.map(layer => ({
            ...layer,
            // 确保 visibility 是布尔值
            visibility: Boolean(layer.visibility || layer.visible),
            // 初始化updating状态
            updating: false
          }))
        } else {
          sceneLayers.value = []
        }
        
        // 延迟显示对话框，避免 ResizeObserver 错误
        await new Promise(resolve => setTimeout(resolve, 50))
        showDetailDialog.value = true
        
      } catch (error) {
        console.error('加载场景详情失败:', error)
        ElMessage.error('加载场景详情失败')
        showDetailDialog.value = false
      }
    }
    
    const removeLayerFromScene = async (layer) => {
      // 权限检查
      if (!canEditScene(currentScene.value)) {
        ElMessage.warning('只有场景创建者可以移除图层')
        return
      }
      
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
        
        await gisApi.removeLayerFromScene(currentScene.value.id, layer.layer_id)
        ElMessage.success('图层移除成功')
        
        // 重新加载场景详情，使用现有的viewScene方法
        await viewScene(currentScene.value)
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('移除图层失败:', error)
          if (error.response?.status === 403) {
            ElMessage.error('权限不足：只有场景创建者可以移除图层')
          } else {
            ElMessage.error('移除图层失败')
          }
        }
      }
    }
    
    const toggleLayerVisibility = async (layer) => {
      const originalVisibility = layer.visibility
      
      // 设置loading状态
      layer.updating = true
      
      try {
        // 调用API更新图层可见性
        await gisApi.updateSceneLayer(currentScene.value.id, layer.id, { 
          visible: layer.visibility 
        })
        
        const statusText = layer.visibility ? '可见' : '隐藏'
        ElMessage({
          message: `图层 "${layer.layer_name}" 已设置为${statusText}`,
          type: 'success',
          duration: 2000
        })
        
      } catch (error) {
        console.error('更新图层可见性失败:', error)
        
        // 如果更新失败，恢复开关状态
        layer.visibility = originalVisibility
        
        ElMessage({
          message: `更新图层可见性失败: ${error.response?.data?.error || error.message}`,
          type: 'error',
          duration: 3000
        })
      } finally {
        // 清除loading状态
        layer.updating = false
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
    
    const handleDetailDialogClose = () => {
      currentScene.value = null
      sceneLayers.value = []
    }
    
    // 生命周期
    onMounted(async () => {
      // 🔥 清除可能被截断的用户信息缓存，重新获取最新的用户信息
      try {
        console.log('重新获取用户信息以确保ID字段正确...')
        const freshUser = await authService.getCurrentUser()
        if (freshUser) {
          currentUser.value = freshUser
          console.log('最新用户信息:', freshUser)
        } else {
          // 如果无法获取最新信息，使用本地缓存但确保ID为字符串
          const cachedUser = authService.getUser()
          if (cachedUser) {
            currentUser.value = cachedUser
            console.log('使用缓存用户信息:', cachedUser)
          }
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 回退到本地缓存
        currentUser.value = authService.getUser()
      }
      
      // 加载场景列表
      loadScenes()
      
      // 抑制 ResizeObserver 错误（这是一个无害的警告）
      const resizeObserverError = (e) => {
        if (e.message === 'ResizeObserver loop completed with undelivered notifications.') {
          e.stopImmediatePropagation()
          return false
        }
      }
      window.addEventListener('error', resizeObserverError)
      
      // 存储清理函数的引用
      window.resizeObserverErrorHandler = resizeObserverError
    })
    
    onUnmounted(() => {
      // 组件卸载时清理事件监听器
      if (window.resizeObserverErrorHandler) {
        window.removeEventListener('error', window.resizeObserverErrorHandler)
        delete window.resizeObserverErrorHandler
      }
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
      toggleLayerVisibility,
      openMapWithScene,
      formatDate,
      formatDateShort,
      handleDetailDialogClose,
      canEditScene,
      canDeleteScene,
      clearUserCache,
      testPermissionCheck
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
  text-align: right;
}

.form-hint {
  margin-top: 5px;
}

.form-hint span {
  display: block;
  line-height: 1.2;
}

/* 防止 ResizeObserver 错误 */
.el-dialog {
  contain: layout;
}

.el-dialog__body {
  overflow: hidden;
}

.scene-detail {
  min-height: 200px;
}

.el-table {
  contain: layout;
}

/* 开关样式优化 */
.el-switch {
  --el-switch-on-color: #13ce66;
  --el-switch-off-color: #ff4949;
}

.el-switch .el-switch__label {
  font-size: 12px;
}

/* 🔥 权限受限按钮的特殊样式 */
.scene-actions .el-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #f5f7fa !important;
  border-color: #dcdfe6 !important;
  color: #c0c4cc !important;
}

.scene-actions .el-button:disabled:hover {
  transform: none !important;
  box-shadow: none !important;
}

/* 鼠标悬停提示样式优化 */
.scene-actions .el-button[title] {
  position: relative;
}

.scene-actions .el-button:disabled[title]:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 1000;
  margin-bottom: 5px;
}

.scene-actions .el-button:disabled[title]:hover::before {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.8);
  z-index: 1000;
}

/* 权限受限状态的图层操作按钮 */
.el-table .el-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #f5f7fa !important;
  border-color: #dcdfe6 !important;
  color: #c0c4cc !important;
}

.el-table .el-button:disabled:hover {
  transform: none !important;
  box-shadow: none !important;
}
</style> 