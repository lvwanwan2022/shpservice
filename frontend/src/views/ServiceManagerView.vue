<template>
  <div class="service-manager">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>我的服务管理</h1>
      <p class="page-description">管理您的Geoserver和Martin服务实例</p>
    </div>

    <!-- 资源使用概览 -->
    <el-card class="resource-overview" v-if="resourceUsage">
      <template #header>
        <div class="card-header">
          <span>资源使用概览</span>
          <el-button 
            type="primary" 
            size="small" 
            @click="showCreateDialog = true"
            :disabled="!canCreateService"
          >
            <el-icon><Plus /></el-icon>
            新建服务
          </el-button>
        </div>
      </template>
      
      <div class="resource-stats">
        <div class="stat-item">
          <div class="stat-label">GeoServer服务</div>
          <div class="stat-value">
            {{ resourceUsage.usage.used_geoserver }} / {{ resourceUsage.quota.max_geoserver_services }}
          </div>
          <el-progress 
            :percentage="(resourceUsage.usage.used_geoserver / resourceUsage.quota.max_geoserver_services * 100)" 
            :stroke-width="6"
            :show-text="false"
          />
        </div>
        
        <div class="stat-item">
          <div class="stat-label">Martin服务</div>
          <div class="stat-value">
            {{ resourceUsage.usage.used_martin }} / {{ resourceUsage.quota.max_martin_services }}
          </div>
          <el-progress 
            :percentage="(resourceUsage.usage.used_martin / resourceUsage.quota.max_martin_services * 100)" 
            :stroke-width="6"
            :show-text="false"
          />
        </div>
        
        <div class="stat-item">
          <div class="stat-label">运行中服务</div>
          <div class="stat-value">{{ resourceUsage.usage.running_services }}</div>
        </div>
        
        <div class="stat-item">
          <div class="stat-label">配额类型</div>
          <div class="stat-value">
            <el-tag :type="getQuotaTagType(resourceUsage.quota.quota_type)">
              {{ getQuotaTypeName(resourceUsage.quota.quota_type) }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 服务列表 -->
    <el-card class="service-list">
      <template #header>
        <div class="card-header">
          <span>服务列表</span>
          <div class="filters">
            <el-select v-model="filterType" placeholder="服务类型" clearable size="small" style="width: 120px">
              <el-option label="全部" value=""></el-option>
              <el-option label="GeoServer" value="geoserver"></el-option>
              <el-option label="Martin" value="martin"></el-option>
            </el-select>
            
            <el-select v-model="filterStatus" placeholder="状态" clearable size="small" style="width: 100px">
              <el-option label="全部" value=""></el-option>
              <el-option label="运行中" value="running"></el-option>
              <el-option label="已停止" value="stopped"></el-option>
              <el-option label="错误" value="error"></el-option>
            </el-select>
            
            <el-button @click="loadServices" size="small">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <div v-if="services.length === 0" class="empty-state">
          <el-empty description="暂无服务">
            <el-button type="primary" @click="showCreateDialog = true">创建第一个服务</el-button>
          </el-empty>
        </div>

        <div v-else class="service-grid">
          <div 
            v-for="service in filteredServices" 
            :key="service.id" 
            class="service-card"
          >
            <div class="service-header">
              <div class="service-title">
                <h3>{{ service.service_name }}</h3>
                <el-tag 
                  :type="getServiceTypeTagType(service.service_type)" 
                  size="small"
                >
                  {{ getServiceTypeName(service.service_type) }}
                </el-tag>
              </div>
              
              <el-dropdown @command="handleServiceAction" trigger="click">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', service}">编辑</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'logs', service}">查看日志</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'delete', service}" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="service-status">
              <div class="status-indicator">
                <el-tag 
                  :type="getStatusTagType(service.service_status)" 
                  effect="dark"
                  size="small"
                >
                  <el-icon><component :is="getStatusIcon(service.service_status)" /></el-icon>
                  {{ getStatusText(service.service_status) }}
                </el-tag>
              </div>
              
              <div class="service-info">
                <div class="info-item">
                  <span class="label">端口:</span>
                  <span class="value">{{ service.port_number || 'N/A' }}</span>
                </div>
                <div class="info-item" v-if="service.created_at">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDate(service.created_at) }}</span>
                </div>
              </div>
            </div>

            <div class="service-description" v-if="service.description">
              <p>{{ service.description }}</p>
            </div>

            <div class="service-actions">
              <el-button-group>
                <el-button 
                  :type="service.service_status === 'running' ? 'danger' : 'success'"
                  size="small"
                  @click="toggleService(service)"
                  :loading="service.actionLoading"
                >
                  <template v-if="service.service_status === 'running'">
                    <el-icon><VideoPlay /></el-icon>
                    停止
                  </template>
                  <template v-else>
                    <el-icon><VideoPause /></el-icon>
                    启动
                  </template>
                </el-button>
                
                <el-button 
                  size="small" 
                  @click="restartService(service)"
                  :loading="service.actionLoading"
                  :disabled="service.service_status === 'stopped'"
                >
                  <el-icon><Refresh /></el-icon>
                  重启
                </el-button>
                
                <el-button 
                  size="small" 
                  @click="checkServiceStatus(service)"
                >
                  <el-icon><View /></el-icon>
                  状态
                </el-button>
              </el-button-group>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建服务对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="创建新服务" 
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="createFormRef" 
        :model="createForm" 
        :rules="createRules" 
        label-width="100px"
      >
        <el-form-item label="服务名称" prop="service_name">
          <el-input 
            v-model="createForm.service_name" 
            placeholder="请输入服务名称"
          />
        </el-form-item>
        
        <el-form-item label="服务类型" prop="service_type">
          <el-radio-group v-model="createForm.service_type">
            <el-radio label="geoserver">GeoServer</el-radio>
            <el-radio label="martin">Martin</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="createForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入服务描述"
          />
        </el-form-item>
        
        <el-form-item label="自动启动">
          <el-switch v-model="createForm.auto_start" />
        </el-form-item>
        
        <el-form-item label="设为默认">
          <el-switch v-model="createForm.is_default" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createService" :loading="createLoading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 服务日志对话框 -->
    <el-dialog 
      v-model="showLogsDialog" 
      :title="`服务日志 - ${currentService?.service_name}`"
      width="800px"
    >
      <div class="logs-content">
        <div class="logs-filters">
          <el-date-picker
            v-model="logDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            size="small"
            style="margin-right: 10px"
          />
          
          <el-select v-model="logOperationType" placeholder="操作类型" clearable size="small" style="width: 120px">
            <el-option label="全部" value=""></el-option>
            <el-option label="启动" value="start"></el-option>
            <el-option label="停止" value="stop"></el-option>
            <el-option label="重启" value="restart"></el-option>
            <el-option label="创建" value="create"></el-option>
            <el-option label="更新" value="config_update"></el-option>
          </el-select>
          
          <el-button @click="loadServiceLogs" size="small" style="margin-left: 10px">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
        </div>
        
        <div class="logs-list" v-loading="logsLoading">
          <div v-if="serviceLogs.length === 0" class="empty-logs">
            <el-empty description="暂无日志记录" />
          </div>
          
          <div v-else class="log-items">
            <div 
              v-for="log in serviceLogs" 
              :key="log.id" 
              class="log-item"
              :class="{'log-error': log.operation_status === 'failed'}"
            >
              <div class="log-header">
                <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
                <el-tag 
                  :type="log.operation_status === 'success' ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ log.operation_type }}
                </el-tag>
              </div>
              <div class="log-message">{{ log.log_message }}</div>
              <div v-if="log.error_details" class="log-error-details">
                <el-text type="danger" size="small">{{ log.error_details }}</el-text>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, MoreFilled, VideoPlay, VideoPause, 
  View, Search, CircleCheck, CircleClose, Warning 
} from '@element-plus/icons-vue'
import authService from '@/auth/authService'

export default {
  name: 'ServiceManagerView',
  components: {
    Plus, Refresh, MoreFilled, VideoPlay, VideoPause, View, Search
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const createLoading = ref(false)
    const logsLoading = ref(false)
    const services = ref([])
    const resourceUsage = ref(null)
    const serviceLogs = ref([])
    
    // 过滤条件
    const filterType = ref('')
    const filterStatus = ref('')
    
    // 对话框控制
    const showCreateDialog = ref(false)
    const showLogsDialog = ref(false)
    const currentService = ref(null)
    
    // 日志查询条件
    const logDateRange = ref(null)
    const logOperationType = ref('')
    
    // 创建表单
    const createForm = reactive({
      service_name: '',
      service_type: 'geoserver',
      description: '',
      auto_start: false,
      is_default: false,
      config_data: {}
    })
    
    const createFormRef = ref(null)
    
    // 表单验证规则
    const createRules = {
      service_name: [
        { required: true, message: '请输入服务名称', trigger: 'blur' },
        { min: 2, max: 50, message: '服务名称长度应为2-50个字符', trigger: 'blur' }
      ],
      service_type: [
        { required: true, message: '请选择服务类型', trigger: 'change' }
      ]
    }
    
    // 计算属性
    const filteredServices = computed(() => {
      return services.value.filter(service => {
        const typeMatch = !filterType.value || service.service_type === filterType.value
        const statusMatch = !filterStatus.value || service.service_status === filterStatus.value
        return typeMatch && statusMatch
      })
    })
    
    const canCreateService = computed(() => {
      if (!resourceUsage.value) return false
      
      const quota = resourceUsage.value.quota
      const usage = resourceUsage.value.usage
      
      return usage.used_geoserver < quota.max_geoserver_services || 
             usage.used_martin < quota.max_martin_services
    })
    
    // API请求方法
    const apiRequest = async (url, options = {}) => {
      const token = authService.getToken()
      const defaultOptions = {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }
      
      const response = await fetch(url, { ...defaultOptions, ...options })
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || '请求失败')
      }
      
      return data
    }
    
    // 加载服务列表
    const loadServices = async () => {
      try {
        loading.value = true
        const data = await apiRequest('/api/user-services')
        services.value = data.data.services.map(service => ({
          ...service,
          actionLoading: false
        }))
      } catch (error) {
        ElMessage.error('加载服务列表失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 加载资源使用情况
    const loadResourceUsage = async () => {
      try {
        const data = await apiRequest('/api/user-services/resource-usage')
        resourceUsage.value = data.data
      } catch (error) {
        console.error('加载资源使用情况失败:', error.message)
      }
    }
    
    // 创建服务
    const createService = async () => {
      try {
        await createFormRef.value.validate()
        createLoading.value = true
        
        // 根据服务类型设置默认配置
        const defaultConfig = createForm.service_type === 'geoserver' ? {
          workspace: 'default',
          datastore: 'default'
        } : {
          database_url: 'postgresql://user:pass@localhost/geometry'
        }
        
        await apiRequest('/api/user-services', {
          method: 'POST',
          body: JSON.stringify({
            ...createForm,
            config_data: defaultConfig
          })
        })
        
        ElMessage.success('服务创建成功')
        showCreateDialog.value = false
        resetCreateForm()
        loadServices()
        loadResourceUsage()
      } catch (error) {
        ElMessage.error('创建服务失败: ' + error.message)
      } finally {
        createLoading.value = false
      }
    }
    
    // 重置创建表单
    const resetCreateForm = () => {
      Object.assign(createForm, {
        service_name: '',
        service_type: 'geoserver',
        description: '',
        auto_start: false,
        is_default: false,
        config_data: {}
      })
      createFormRef.value?.resetFields()
    }
    
    // 切换服务状态
    const toggleService = async (service) => {
      const action = service.service_status === 'running' ? 'stop' : 'start'
      const actionText = action === 'start' ? '启动' : '停止'
      
      try {
        service.actionLoading = true
        await apiRequest(`/api/user-services/${service.id}/${action}`, {
          method: 'POST'
        })
        
        ElMessage.success(`服务${actionText}成功`)
        loadServices()
      } catch (error) {
        ElMessage.error(`服务${actionText}失败: ` + error.message)
      } finally {
        service.actionLoading = false
      }
    }
    
    // 重启服务
    const restartService = async (service) => {
      try {
        service.actionLoading = true
        await apiRequest(`/api/user-services/${service.id}/restart`, {
          method: 'POST'
        })
        
        ElMessage.success('服务重启成功')
        loadServices()
      } catch (error) {
        ElMessage.error('服务重启失败: ' + error.message)
      } finally {
        service.actionLoading = false
      }
    }
    
    // 检查服务状态
    const checkServiceStatus = async (service) => {
      try {
        const data = await apiRequest(`/api/user-services/${service.id}/status`)
        const status = data.data
        
        ElMessageBox.alert(
          `
          <div style="text-align: left;">
            <p><strong>服务名称:</strong> ${status.service_name}</p>
            <p><strong>服务类型:</strong> ${getServiceTypeName(status.service_type)}</p>
            <p><strong>当前状态:</strong> ${getStatusText(status.status)}</p>
            <p><strong>监听端口:</strong> ${status.port || 'N/A'}</p>
            <p><strong>最后启动:</strong> ${status.last_started_at ? formatDateTime(status.last_started_at) : 'N/A'}</p>
            <p><strong>最后停止:</strong> ${status.last_stopped_at ? formatDateTime(status.last_stopped_at) : 'N/A'}</p>
          </div>
          `,
          '服务状态详情',
          {
            dangerouslyUseHTMLString: true,
            type: 'info'
          }
        )
      } catch (error) {
        ElMessage.error('获取服务状态失败: ' + error.message)
      }
    }
    
    // 处理服务操作
    const handleServiceAction = ({ action, service }) => {
      switch (action) {
        case 'edit':
          editService(service)
          break
        case 'logs':
          showServiceLogs(service)
          break
        case 'delete':
          deleteService(service)
          break
      }
    }
    
    // 编辑服务
    const editService = (service) => {
      ElMessage.info('编辑功能开发中...')
    }
    
    // 显示服务日志
    const showServiceLogs = (service) => {
      currentService.value = service
      showLogsDialog.value = true
      loadServiceLogs()
    }
    
    // 加载服务日志
    const loadServiceLogs = async () => {
      if (!currentService.value) return
      
      try {
        logsLoading.value = true
        let url = `/api/user-services/${currentService.value.id}/logs?limit=50`
        
        if (logDateRange.value) {
          const [startTime, endTime] = logDateRange.value
          url += `&start_time=${startTime.toISOString()}&end_time=${endTime.toISOString()}`
        }
        
        if (logOperationType.value) {
          url += `&operation_type=${logOperationType.value}`
        }
        
        const data = await apiRequest(url)
        serviceLogs.value = data.data
      } catch (error) {
        ElMessage.error('加载服务日志失败: ' + error.message)
      } finally {
        logsLoading.value = false
      }
    }
    
    // 删除服务
    const deleteService = async (service) => {
      try {
        await ElMessageBox.confirm(
          `确认删除服务 "${service.service_name}" 吗？此操作不可恢复。`,
          '删除确认',
          {
            confirmButtonText: '确认删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        await apiRequest(`/api/user-services/${service.id}`, {
          method: 'DELETE'
        })
        
        ElMessage.success('服务删除成功')
        loadServices()
        loadResourceUsage()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除服务失败: ' + error.message)
        }
      }
    }
    
    // 工具方法
    const getServiceTypeName = (type) => {
      const map = {
        'geoserver': 'GeoServer',
        'martin': 'Martin'
      }
      return map[type] || type
    }
    
    const getServiceTypeTagType = (type) => {
      const map = {
        'geoserver': 'primary',
        'martin': 'success'
      }
      return map[type] || 'info'
    }
    
    const getStatusText = (status) => {
      const map = {
        'running': '运行中',
        'stopped': '已停止',
        'starting': '启动中',
        'stopping': '停止中',
        'error': '错误'
      }
      return map[status] || status
    }
    
    const getStatusTagType = (status) => {
      const map = {
        'running': 'success',
        'stopped': 'info',
        'starting': 'warning',
        'stopping': 'warning',
        'error': 'danger'
      }
      return map[status] || 'info'
    }
    
    const getStatusIcon = (status) => {
      const map = {
        'running': 'CircleCheck',
        'stopped': 'CircleClose',
        'starting': 'Warning',
        'stopping': 'Warning',
        'error': 'Warning'
      }
      return map[status] || 'Warning'
    }
    
    const getQuotaTypeName = (type) => {
      const map = {
        'basic': '基础版',
        'standard': '标准版',
        'premium': '高级版'
      }
      return map[type] || type
    }
    
    const getQuotaTagType = (type) => {
      const map = {
        'basic': 'info',
        'standard': 'success',
        'premium': 'warning'
      }
      return map[type] || 'info'
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('zh-CN')
    }
    
    const formatDateTime = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    // 初始化
    onMounted(() => {
      loadServices()
      loadResourceUsage()
    })
    
    return {
      // 响应式数据
      loading,
      createLoading,
      logsLoading,
      services,
      resourceUsage,
      serviceLogs,
      
      // 过滤条件
      filterType,
      filterStatus,
      filteredServices,
      
      // 对话框控制
      showCreateDialog,
      showLogsDialog,
      currentService,
      
      // 日志查询
      logDateRange,
      logOperationType,
      
      // 表单
      createForm,
      createFormRef,
      createRules,
      
      // 计算属性
      canCreateService,
      
      // 方法
      loadServices,
      loadResourceUsage,
      createService,
      resetCreateForm,
      toggleService,
      restartService,
      checkServiceStatus,
      handleServiceAction,
      showServiceLogs,
      loadServiceLogs,
      deleteService,
      
      // 工具方法
      getServiceTypeName,
      getServiceTypeTagType,
      getStatusText,
      getStatusTagType,
      getStatusIcon,
      getQuotaTypeName,
      getQuotaTagType,
      formatDate,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.service-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.page-description {
  color: #909399;
  margin: 5px 0 0 0;
}

.resource-overview {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.service-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.3s;
}

.service-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.service-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.service-title h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #303133;
}

.service-status {
  margin-bottom: 12px;
}

.status-indicator {
  margin-bottom: 8px;
}

.service-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-item .label {
  color: #909399;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.service-description {
  margin-bottom: 16px;
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.service-actions {
  display: flex;
  justify-content: center;
}

.logs-content {
  max-height: 500px;
}

.logs-filters {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.logs-list {
  max-height: 400px;
  overflow-y: auto;
}

.empty-logs {
  text-align: center;
  padding: 40px 0;
}

.log-items {
  space: 8px 0;
}

.log-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
  background: #fafafa;
}

.log-item.log-error {
  border-color: #f89898;
  background: #fef0f0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-message {
  font-size: 14px;
  color: #303133;
  line-height: 1.4;
}

.log-error-details {
  margin-top: 8px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #f89898;
}

@media (max-width: 768px) {
  .service-manager {
    padding: 10px;
  }
  
  .resource-stats {
    grid-template-columns: 1fr;
  }
  
  .service-grid {
    grid-template-columns: 1fr;
  }
  
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .logs-filters {
    flex-direction: column;
    align-items: stretch;
  }
}
</style> 