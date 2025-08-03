<template>
  <div class="service-connection">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>我的服务连接</h1>
      <p class="page-description">管理您的外部Geoserver和Martin服务连接配置</p>
      
      <!-- 功能说明 -->
      <el-alert
        title="连接测试说明"
        type="info"
        show-icon
        :closable="false"
        class="test-info-alert"
      >
        <div>
          <p><strong>前端测试：</strong>直接从浏览器测试服务连接，无需通过后端。适用于客户端可直接访问Geoserver的场景。</p>
          <p><strong>后端测试：</strong>通过系统后端测试连接，适用于服务器间的网络连接测试。</p>
          <p class="tip">💡 推荐优先使用前端测试，这样即使后端服务器无法访问Geoserver，只要您的浏览器能访问就可以正常使用服务。</p>
        </div>
      </el-alert>
    </div>

    <!-- 服务连接列表 -->
    <el-card class="connection-list">
      <template #header>
        <div class="card-header">
          <span>服务连接列表</span>
          <div class="header-actions">
            <div class="filters">
              <el-select v-model="filterType" placeholder="服务类型" clearable size="small" style="width: 120px">
                <el-option label="全部" value=""></el-option>
                <el-option label="GeoServer" value="geoserver"></el-option>
                <el-option label="Martin" value="martin"></el-option>
              </el-select>
              
              <el-button @click="loadConnections" size="small">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
            
            <el-button 
              type="primary" 
              @click="showCreateDialog = true"
              size="small"
            >
              <el-icon><Plus /></el-icon>
              添加连接
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <div v-if="connections.length === 0" class="empty-state">
          <el-empty description="暂无服务连接">
            <el-button type="primary" @click="showCreateDialog = true">添加第一个连接</el-button>
          </el-empty>
        </div>

        <div v-else class="connection-grid">
          <div 
            v-for="connection in filteredConnections" 
            :key="connection.id" 
            class="connection-card"
          >
            <div class="connection-header">
              <div class="connection-title">
                <h3>{{ connection.service_name }}</h3>
                <el-tag 
                  :type="getServiceTypeTagType(connection.service_type)" 
                  size="small"
                >
                  {{ getServiceTypeName(connection.service_type) }}
                </el-tag>
                <el-tag 
                  v-if="connection.is_default" 
                  type="warning" 
                  size="small"
                >
                  默认
                </el-tag>
              </div>
              
              <el-dropdown @command="handleConnectionAction" trigger="click">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', connection}">编辑</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'test', connection}">测试连接</el-dropdown-item>
                    <el-dropdown-item 
                      :command="{action: 'toggle', connection}"
                      :divided="true"
                    >
                      {{ connection.is_active ? '禁用' : '启用' }}
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'delete', connection}">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="connection-info">
              <div class="info-item">
                <span class="label">服务地址:</span>
                <span class="value" :title="connection.server_url">
                  {{ connection.server_url }}
                </span>
              </div>
              
              <div class="info-item" v-if="connection.description">
                <span class="label">描述:</span>
                <span class="value">{{ connection.description }}</span>
              </div>
              
              <div class="info-item">
                <span class="label">状态:</span>
                <el-tag 
                  :type="getStatusTagType(connection.test_status)" 
                  size="small"
                >
                  {{ getStatusText(connection.test_status) }}
                </el-tag>
                <span v-if="connection.last_tested_at" class="test-time">
                  {{ formatDate(connection.last_tested_at) }}
                </span>
              </div>
              
              <div class="info-item" v-if="!connection.is_active">
                <el-tag type="info" size="small">已禁用</el-tag>
              </div>
            </div>

            <div class="connection-actions">
              <el-button-group>
                <el-button 
                  size="small" 
                  @click="testConnectionFrontend(connection)"
                  :loading="connection.testing && connection.testMethod === 'frontend'"
                  type="primary"
                >
                  <el-icon><Link /></el-icon>
                  前端测试
                </el-button>
                
                <el-button 
                  size="small" 
                  @click="testConnectionBackend(connection)"
                  :loading="connection.testing && connection.testMethod === 'backend'"
                  type="info"
                >
                  <el-icon><Link /></el-icon>
                  后端测试
                </el-button>
                
                <el-button 
                  size="small" 
                  @click="editConnection(connection)"
                >
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
              </el-button-group>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 添加/编辑连接对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingConnection ? '编辑连接' : '添加连接'" 
      width="700px"
      :close-on-click-modal="false"
      @close="resetCreateForm"
    >
      <el-form 
        ref="createFormRef" 
        :model="createForm" 
        :rules="createRules" 
        label-width="120px"
      >
        <el-form-item label="连接名称" prop="service_name">
          <el-input 
            v-model="createForm.service_name" 
            placeholder="请输入连接名称"
          />
        </el-form-item>
        
        <el-form-item label="服务类型" prop="service_type">
          <el-radio-group 
            v-model="createForm.service_type" 
            @change="onServiceTypeChange"
            :disabled="editingConnection"
          >
            <el-radio label="geoserver">GeoServer</el-radio>
            <el-radio label="martin">Martin</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- GeoServer 配置 -->
        <template v-if="createForm.service_type === 'geoserver'">
          <el-form-item label="服务地址" prop="server_url">
            <el-input 
              v-model="createForm.server_url" 
              placeholder="http://your-server:8080/geoserver"
            />
            <div class="form-tip">请输入完整的GeoServer访问地址</div>
          </el-form-item>
          
          <el-form-item label="管理员账号" prop="username">
            <el-input 
              v-model="createForm.username" 
              placeholder="admin"
            />
          </el-form-item>
          
          <el-form-item label="管理员密码" prop="password">
            <el-input 
              v-model="createForm.password" 
              type="password" 
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="默认工作空间" prop="workspace">
            <el-input 
              v-model="createForm.workspace" 
              placeholder="default"
            />
            <div class="form-tip">用于发布数据的默认工作空间</div>
          </el-form-item>
        </template>
        
        <!-- Martin 配置 -->
        <template v-if="createForm.service_type === 'martin'">
          <el-form-item label="服务地址" prop="server_url">
            <el-input 
              v-model="createForm.server_url" 
              placeholder="http://your-server:3000"
            />
            <div class="form-tip">请输入Martin服务的访问地址</div>
          </el-form-item>
          
          <el-form-item label="数据库连接" prop="database_url">
            <el-input 
              v-model="createForm.database_url" 
              placeholder="postgresql://user:password@host:5432/database"
            />
            <div class="form-tip">Martin连接的PostGIS数据库地址（可选）</div>
          </el-form-item>
          
          <el-form-item label="API密钥" prop="api_key">
            <el-input 
              v-model="createForm.api_key" 
              placeholder="API密钥（如果需要）"
              show-password
            />
            <div class="form-tip">如果Martin服务需要认证，请填写API密钥</div>
          </el-form-item>
        </template>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="createForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入连接描述"
          />
        </el-form-item>
        
        <el-form-item label="设为默认">
          <el-switch v-model="createForm.is_default" />
          <div class="form-tip">设为默认后，发布数据时将优先使用此连接</div>
        </el-form-item>
        
        <!-- 连接测试 -->
        <el-form-item>
          <div class="test-buttons">
            <el-button 
              type="primary" 
              @click="testConnectionFormFrontend" 
              :loading="testLoading && testMethod === 'frontend'"
              :disabled="!canTestConnection"
            >
              <el-icon><Link /></el-icon>
              前端测试
            </el-button>
            <el-button 
              type="info" 
              @click="testConnectionFormBackend" 
              :loading="testLoading && testMethod === 'backend'"
              :disabled="!canTestConnection"
            >
              <el-icon><Link /></el-icon>
              后端测试
            </el-button>
          </div>
          <div v-if="connectionTestResult" class="test-result" :class="connectionTestResult.success ? 'success' : 'error'">
            <div class="test-message">{{ connectionTestResult.message }}</div>
            <div v-if="connectionTestResult.data && connectionTestResult.data.testMethod" class="test-method">
              测试方式: {{ connectionTestResult.data.testMethod === 'frontend' ? '前端直连' : '后端代理' }}
            </div>
            <div v-if="connectionTestResult.data && connectionTestResult.data.version" class="test-details">
              版本: {{ connectionTestResult.data.version }}
            </div>
            <div v-if="connectionTestResult.data && connectionTestResult.data.workspaceCount !== undefined" class="test-details">
              工作空间: {{ connectionTestResult.data.workspaceCount }} 个
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConnection" :loading="createLoading">
            {{ editingConnection ? '更新' : '添加' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, MoreFilled, Link, Edit
} from '@element-plus/icons-vue'
import authService from '@/auth/authService'
import { testServiceConnection } from '@/utils/geoserverTest'

export default {
  name: 'ServiceConnectionView',
  components: {
    Plus, Refresh, MoreFilled, Link, Edit
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const createLoading = ref(false)
    const testLoading = ref(false)
    const testMethod = ref('frontend') // 'frontend' 或 'backend'
    const connections = ref([])
    const connectionTestResult = ref(null)
    
    // 过滤条件
    const filterType = ref('')
    
    // 对话框控制
    const showCreateDialog = ref(false)
    const editingConnection = ref(null)
    
    // 创建表单
    const createForm = reactive({
      service_name: '',
      service_type: 'geoserver',
      server_url: '',
      description: '',
      is_default: false,
      // GeoServer 配置
      username: '',
      password: '',
      workspace: 'default',
      // Martin 配置
      database_url: '',
      api_key: ''
    })
    
    const createFormRef = ref(null)
    
    // 表单验证规则
    const createRules = {
      service_name: [
        { required: true, message: '请输入连接名称', trigger: 'blur' },
        { min: 2, max: 50, message: '连接名称长度应为2-50个字符', trigger: 'blur' }
      ],
      service_type: [
        { required: true, message: '请选择服务类型', trigger: 'change' }
      ],
      server_url: [
        { required: true, message: '请输入服务地址', trigger: 'blur' },
        { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
      ],
      username: [
        { 
          required: () => createForm.service_type === 'geoserver', 
          message: '请输入管理员账号', 
          trigger: 'blur' 
        }
      ],
      password: [
        { 
          required: () => createForm.service_type === 'geoserver', 
          message: '请输入管理员密码', 
          trigger: 'blur' 
        }
      ]
    }
    
    // 计算属性
    const filteredConnections = computed(() => {
      return connections.value.filter(connection => {
        const typeMatch = !filterType.value || connection.service_type === filterType.value
        return typeMatch
      })
    })
    
    const canTestConnection = computed(() => {
      if (!createForm.server_url) return false
      
      if (createForm.service_type === 'geoserver') {
        return createForm.username && createForm.password
      } else if (createForm.service_type === 'martin') {
        return true // Martin只需要服务地址即可测试
      }
      
      return false
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
      
      // 检查响应内容类型
      const contentType = response.headers.get('content-type')
      let data = null
      
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json()
        } catch (jsonError) {
          console.error('JSON解析失败:', jsonError)
          throw new Error(`JSON解析失败: ${jsonError.message}`)
        }
      } else {
        // 如果不是JSON响应，获取文本内容
        const textData = await response.text()
        console.warn('收到非JSON响应:', textData)
        data = { error: textData || '服务器返回了非JSON响应' }
      }
      
      if (!response.ok) {
        const errorMessage = data && data.error ? data.error : `请求失败 (${response.status})`
        throw new Error(errorMessage)
      }
      
      return data
    }
    
    // 加载连接列表
    const loadConnections = async () => {
      try {
        loading.value = true
        const data = await apiRequest('/api/service-connections')
        connections.value = data.data.map(connection => ({
          ...connection,
          testing: false,
          testMethod: null
        }))
      } catch (error) {
        ElMessage.error('加载连接列表失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 保存连接
    const saveConnection = async () => {
      try {
        await createFormRef.value.validate()
        createLoading.value = true
        
        const requestData = {
          service_name: createForm.service_name,
          service_type: createForm.service_type,
          server_url: createForm.server_url,
          description: createForm.description,
          is_default: createForm.is_default
        }
        
        // 添加服务特定配置
        if (createForm.service_type === 'geoserver') {
          requestData.username = createForm.username
          requestData.password = createForm.password
          requestData.workspace = createForm.workspace || 'default'
        } else if (createForm.service_type === 'martin') {
          if (createForm.database_url) {
            requestData.database_url = createForm.database_url
          }
          if (createForm.api_key) {
            requestData.api_key = createForm.api_key
          }
        }
        
        if (editingConnection.value) {
          // 更新连接
          await apiRequest(`/api/service-connections/${editingConnection.value.id}`, {
            method: 'PUT',
            body: JSON.stringify(requestData)
          })
          ElMessage.success('连接更新成功')
        } else {
          // 创建连接
          await apiRequest('/api/service-connections', {
            method: 'POST',
            body: JSON.stringify(requestData)
          })
          ElMessage.success('连接添加成功')
        }
        
        showCreateDialog.value = false
        resetCreateForm()
        loadConnections()
      } catch (error) {
        console.error('保存连接失败:', error)
        const errorMessage = error.message || error.toString()
        ElMessage.error(`保存连接失败: ${errorMessage}`)
      } finally {
        createLoading.value = false
      }
    }
    
    // 重置创建表单
    const resetCreateForm = () => {
      Object.assign(createForm, {
        service_name: '',
        service_type: 'geoserver',
        server_url: '',
        description: '',
        is_default: false,
        username: '',
        password: '',
        workspace: 'default',
        database_url: '',
        api_key: ''
      })
      connectionTestResult.value = null
      editingConnection.value = null
      createFormRef.value?.resetFields()
    }
    
    // 服务类型变更处理
    const onServiceTypeChange = () => {
      // 清空服务特定的字段
      createForm.server_url = ''
      createForm.username = ''
      createForm.password = ''
      createForm.workspace = 'default'
      createForm.database_url = ''
      createForm.api_key = ''
      connectionTestResult.value = null
    }
    
    // 前端测试连接（表单中）
    const testConnectionFormFrontend = async () => {
      try {
        testLoading.value = true
        testMethod.value = 'frontend'
        connectionTestResult.value = null
        
        const testConfig = {
          service_type: createForm.service_type,
          server_url: createForm.server_url
        }
        
        if (createForm.service_type === 'geoserver') {
          testConfig.username = createForm.username
          testConfig.password = createForm.password
          testConfig.workspace = createForm.workspace
        } else if (createForm.service_type === 'martin') {
          if (createForm.api_key) {
            testConfig.api_key = createForm.api_key
          }
        }
        
        const result = await testServiceConnection(testConfig, true)
        
        connectionTestResult.value = result
        
        if (result.success) {
          ElMessage.success(result.message)
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        connectionTestResult.value = {
          success: false,
          message: error.message || '前端测试失败'
        }
        
        ElMessage.error('前端测试失败: ' + error.message)
      } finally {
        testLoading.value = false
      }
    }
    
    // 后端测试连接（表单中）
    const testConnectionFormBackend = async () => {
      try {
        testLoading.value = true
        testMethod.value = 'backend'
        connectionTestResult.value = null
        
        const testData = {
          service_type: createForm.service_type,
          server_url: createForm.server_url
        }
        
        if (createForm.service_type === 'geoserver') {
          testData.username = createForm.username
          testData.password = createForm.password
        } else if (createForm.service_type === 'martin') {
          if (createForm.api_key) {
            testData.api_key = createForm.api_key
          }
        }
        
        const response = await apiRequest('/api/service-connections/test', {
          method: 'POST',
          body: JSON.stringify(testData)
        })
        
        connectionTestResult.value = {
          success: true,
          message: response.message || '连接测试成功',
          data: { testMethod: 'backend', ...response.data }
        }
        
        ElMessage.success('连接测试成功')
      } catch (error) {
        connectionTestResult.value = {
          success: false,
          message: error.message || '连接测试失败',
          data: { testMethod: 'backend' }
        }
        
        console.error('表单连接测试失败:', error)
        const errorMessage = error.message || error.toString()
        ElMessage.error(`连接测试失败: ${errorMessage}`)
      } finally {
        testLoading.value = false
      }
    }
    
    // 前端测试现有连接
    const testConnectionFrontend = async (connection) => {
      try {
        connection.testing = true
        connection.testMethod = 'frontend'
        
        // 构建测试配置
        let config = {}
        if (connection.connection_config) {
          if (typeof connection.connection_config === 'string') {
            try {
              config = JSON.parse(connection.connection_config)
            } catch (parseError) {
              console.warn('解析连接配置失败:', parseError)
              config = {}
            }
          } else if (typeof connection.connection_config === 'object') {
            config = connection.connection_config
          }
        }
        const testConfig = {
          service_type: connection.service_type,
          server_url: connection.server_url,
          ...config
        }
        
        const result = await testServiceConnection(testConfig, true)
        
        if (result.success) {
          ElMessage.success(result.message)
        } else {
          ElMessage.error(result.message)
        }
        
        // 可选：更新本地状态，不重新加载整个列表
        connection.test_status = result.success ? 'success' : 'failed'
        connection.last_tested_at = new Date().toISOString()
        
      } catch (error) {
        console.error('前端测试失败:', error)
        const errorMessage = error.message || error.toString()
        ElMessage.error(`前端测试失败: ${errorMessage}`)
        connection.test_status = 'failed'
      } finally {
        connection.testing = false
        connection.testMethod = null
      }
    }
    
    // 后端测试现有连接
    const testConnectionBackend = async (connection) => {
      try {
        connection.testing = true
        connection.testMethod = 'backend'
        
        await apiRequest(`/api/service-connections/${connection.id}/test`, {
          method: 'POST'
        })
        
        ElMessage.success('连接测试成功')
        loadConnections() // 重新加载以更新测试状态
      } catch (error) {
        console.error('后端测试失败:', error)
        const errorMessage = error.message || error.toString()
        ElMessage.error(`连接测试失败: ${errorMessage}`)
      } finally {
        connection.testing = false
        connection.testMethod = null
      }
    }
    
    // 编辑连接
    const editConnection = (connection) => {
      editingConnection.value = connection
      
      // 填充表单
      createForm.service_name = connection.service_name
      createForm.service_type = connection.service_type
      createForm.server_url = connection.server_url
      createForm.description = connection.description || ''
      createForm.is_default = connection.is_default
      
      // 填充连接配置
      if (connection.connection_config) {
        const config = connection.connection_config
        if (connection.service_type === 'geoserver') {
          createForm.username = config.username || ''
          createForm.password = '' // 不显示密码
          createForm.workspace = config.workspace || 'default'
        } else if (connection.service_type === 'martin') {
          createForm.database_url = config.database_url || ''
          createForm.api_key = '' // 不显示API密钥
        }
      }
      
      showCreateDialog.value = true
    }
    
    // 处理连接操作
    const handleConnectionAction = ({ action, connection }) => {
      switch (action) {
        case 'edit':
          editConnection(connection)
          break
        case 'test':
          // 默认使用前端测试
          testConnectionFrontend(connection)
          break
        case 'toggle':
          toggleConnection(connection)
          break
        case 'delete':
          deleteConnection(connection)
          break
      }
    }
    
    // 切换连接状态
    const toggleConnection = async (connection) => {
      try {
        await apiRequest(`/api/service-connections/${connection.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            is_active: !connection.is_active
          })
        })
        
        ElMessage.success(`连接已${connection.is_active ? '禁用' : '启用'}`)
        loadConnections()
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      }
    }
    
    // 删除连接
    const deleteConnection = async (connection) => {
      try {
        await ElMessageBox.confirm(
          `确认删除连接 "${connection.service_name}" 吗？此操作不可恢复。`,
          '删除确认',
          {
            confirmButtonText: '确认删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        await apiRequest(`/api/service-connections/${connection.id}`, {
          method: 'DELETE'
        })
        
        ElMessage.success('连接删除成功')
        loadConnections()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除连接失败: ' + error.message)
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
        'success': '连接正常',
        'failed': '连接失败',
        'unknown': '未测试'
      }
      return map[status] || status
    }
    
    const getStatusTagType = (status) => {
      const map = {
        'success': 'success',
        'failed': 'danger',
        'unknown': 'info'
      }
      return map[status] || 'info'
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    // 初始化
    onMounted(() => {
      loadConnections()
    })
    
    return {
      // 响应式数据
      loading,
      createLoading,
      testLoading,
      testMethod,
      connections,
      connectionTestResult,
      
      // 过滤条件
      filterType,
      filteredConnections,
      
      // 对话框控制
      showCreateDialog,
      editingConnection,
      
      // 表单
      createForm,
      createFormRef,
      createRules,
      
      // 计算属性
      canTestConnection,
      
      // 方法
      loadConnections,
      saveConnection,
      resetCreateForm,
      onServiceTypeChange,
      testConnectionFormFrontend,
      testConnectionFormBackend,
      testConnectionFrontend,
      testConnectionBackend,
      editConnection,
      handleConnectionAction,
      toggleConnection,
      deleteConnection,
      
      // 工具方法
      getServiceTypeName,
      getServiceTypeTagType,
      getStatusText,
      getStatusTagType,
      formatDate
    }
  }
}
</script>

<style scoped>
.service-connection {
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

.test-info-alert {
  margin-top: 15px;
}

.test-info-alert .el-alert__content p {
  margin-bottom: 5px;
}

.test-info-alert .el-alert__content .tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.connection-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
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

.connection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.connection-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.3s;
}

.connection-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.connection-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.connection-title h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #303133;
}

.connection-title .el-tag {
  margin-left: 8px;
}

.connection-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-item .label {
  color: #909399;
  white-space: nowrap;
  margin-right: 8px;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
  flex: 1;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.test-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 8px;
}

.connection-actions {
  display: flex;
  justify-content: center;
}

/* 表单提示文字 */
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

/* 测试按钮组 */
.test-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

/* 连接测试结果 */
.test-result {
  margin-top: 10px;
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
}

.test-result.success {
  background-color: #f0f9ff;
  border: 1px solid #e1f5fe;
  color: #2e7d32;
}

.test-result.error {
  background-color: #fff3f3;
  border: 1px solid #ffebee;
  color: #d32f2f;
}

.test-message {
  font-weight: 500;
  margin-bottom: 5px;
}

.test-method {
  font-size: 12px;
  color: #666;
  margin-bottom: 3px;
}

.test-details {
  font-size: 12px;
  color: #888;
  margin-bottom: 2px;
}

@media (max-width: 768px) {
  .service-connection {
    padding: 10px;
  }
  
  .connection-grid {
    grid-template-columns: 1fr;
  }
  
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
}
</style> 