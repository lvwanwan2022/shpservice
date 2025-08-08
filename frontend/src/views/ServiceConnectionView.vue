<template>
  <div class="service-connection">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>我的服务连接</h1>
      <p class="page-description">管理您的外部Geoserver和Martin服务连接配置</p>
      
      <!-- 服务下载和使用说明 -->
      <div class="service-guides">
        <el-collapse v-model="activeGuides" accordion>
          <el-collapse-item title="📦 文件服务程序下载" name="file-service">
            <div class="guide-content">
              <div class="download-section">
                <h4>🛠️ Main.zip 文件服务程序</h4>
                <p>客户端文件服务程序，用于在本地发布文件服务供系统连接使用</p>
                <div class="download-buttons">
                  <el-button type="primary" @click="downloadFileService">
                    <el-icon><Download /></el-icon>
                    下载 Main.zip
                  </el-button>
                  <el-button type="info" @click="showFileServiceGuide = true">
                    <el-icon><Document /></el-icon>
                    使用说明
                  </el-button>
                </div>
              </div>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="🗺️ Martin瓦片服务" name="martin">
            <div class="guide-content">
              <div class="download-section">
                <h4>📍 Martin MVT服务</h4>
                <p>现代化矢量瓦片服务，支持PostGIS数据库直接发布MVT瓦片</p>
                <div class="download-buttons">
                  <el-button type="success" @click="openMartinDownload">
                    <el-icon><Link /></el-icon>
                    官方下载
                  </el-button>
                  <el-button type="info" @click="showMartinGuide = true">
                    <el-icon><Document /></el-icon>
                    使用说明
                  </el-button>
                </div>
              </div>
            </div>
          </el-collapse-item>
          
          <el-collapse-item title="🌍 GeoServer地图服务" name="geoserver">
            <div class="guide-content">
              <div class="download-section">
                <h4>🗺️ GeoServer WMS/WFS服务</h4>
                <p>企业级地理信息服务器，支持多种数据格式和OGC标准服务</p>
                <div class="download-buttons">
                  <el-button type="warning" @click="openGeoServerDownload">
                    <el-icon><Link /></el-icon>
                    官方下载
                  </el-button>
                  <el-button type="info" @click="showGeoServerGuide = true">
                    <el-icon><Document /></el-icon>
                    使用说明
                  </el-button>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
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
            
            <!-- Martin文件服务信息 -->
            <div v-if="connection.service_type === 'martin' && getFileServiceInfo(connection)" class="info-item">
              <span class="label">文件服务:</span>
              <span class="value" :title="getFileServiceInfo(connection)">
                {{ getFileServiceInfo(connection) }}
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
                <el-tooltip 
                  content="前端直接测试（可能受CORS限制，适用于本地或已配置CORS的服务）" 
                  placement="top"
                >
                  <el-button 
                    size="small" 
                    @click="testConnectionFrontend(connection)"
                    :loading="connection.testing && connection.testMethod === 'frontend'"
                    type="primary"
                  >
                    <el-icon><Link /></el-icon>
                    前端测试
                  </el-button>
                </el-tooltip>
                
                <el-tooltip 
                  content="通过后端测试（推荐，无CORS限制，更可靠）" 
                  placement="top"
                >
                  <el-button 
                    size="small" 
                    @click="testConnectionBackend(connection)"
                    :loading="connection.testing && connection.testMethod === 'backend'"
                    type="success"
                  >
                    <el-icon><Link /></el-icon>
                    后端测试 ⭐
                  </el-button>
                </el-tooltip>
                
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
          <el-form-item label="Martin地址" prop="server_url">
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
          
          <!-- 文件服务配置 -->
          <el-divider content-position="left">
            <span style="color: #409EFF; font-weight: bold;">📁 文件服务配置</span>
          </el-divider>
          
          <el-form-item label="文件服务地址" prop="file_service_url">
            <el-input 
              v-model="createForm.file_service_url" 
              placeholder="http://client-ip:8080"
            />
            <div class="form-tip">客户端Main.exe程序发布的文件服务地址</div>
          </el-form-item>
          
          <el-form-item label="文件夹地址" prop="file_folder_url">
            <el-input 
              v-model="createForm.file_folder_url" 
              placeholder="http://client-ip:8080/files"
            />
            <div class="form-tip">文件服务的文件夹访问地址（含端口号）</div>
          </el-form-item>
          
          <el-form-item label="文件服务账号" prop="file_service_username">
            <el-input 
              v-model="createForm.file_service_username" 
              placeholder="请输入文件服务登录账号"
            />
            <div class="form-tip">访问文件服务的用户名</div>
          </el-form-item>
          
          <el-form-item label="文件服务密码" prop="file_service_password">
            <el-input 
              v-model="createForm.file_service_password" 
              type="password"
              placeholder="请输入文件服务登录密码"
              show-password
            />
            <div class="form-tip">访问文件服务的密码</div>
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

    <!-- 文件服务使用说明对话框 -->
    <el-dialog 
      v-model="showFileServiceGuide" 
      title="📁 文件服务程序使用说明" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="guide-dialog">
        <h3>🛠️ Main.zip 程序使用说明</h3>
        
        <div class="guide-step">
          <h4>1. 下载和运行</h4>
          <ul>
            <li>下载 Main.zip 程序包到客户端计算机</li>
            <li>解压zip文件，双击运行main.exe程序，会弹出配置界面</li>
            <li>设置文件夹路径、端口号、用户名和密码</li>
            <li>点击"启动服务"按钮</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>2. 配置说明</h4>
          <ul>
            <li><strong>文件夹路径：</strong>选择要共享的文件夹</li>
            <li><strong>端口号：</strong>默认8080，如冲突可修改</li>
            <li><strong>用户名/密码：</strong>用于访问控制</li>
            <li><strong>最大容量：</strong>限制文件夹的最大使用空间</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>3. 连接配置</h4>
          <ul>
            <li><strong>文件服务地址：</strong>http://客户端IP:端口号</li>
            <li><strong>文件夹地址：</strong>http://客户端IP:端口号/files</li>
            <li><strong>账号密码：</strong>使用程序中设置的用户名和密码</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>4. 功能特点</h4>
          <ul>
            <li>✅ 支持文件上传下载</li>
            <li>✅ 分块上传大文件</li>
            <li>✅ 用户认证和权限控制</li>
            <li>✅ 系统托盘后台运行</li>
            <li>✅ 跨域支持，便于前端调用</li>
          </ul>
        </div>
      </div>
    </el-dialog>

    <!-- Martin服务使用说明对话框 -->
    <el-dialog 
      v-model="showMartinGuide" 
      title="🗺️ Martin服务使用说明" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="guide-dialog">
        <h3>📍 Martin MVT瓦片服务配置</h3>
        
        <div class="guide-step">
          <h4>1. 下载和安装</h4>
          <ul>
            <li>访问 <a href="https://github.com/maplibre/martin/releases" target="_blank">Martin官方下载页面</a></li>
            <li>下载适合你操作系统的版本</li>
            <li>解压到合适的目录</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>2. 配置文件</h4>
          <pre class="code-block">
listen_addresses: 0.0.0.0:3000
worker_processes: 32
cache_size_mb: 5120
# Enable or disable Martin web UI. At the moment, only allows `enable-for-all` which enables the web UI for all connections. This may be undesirable in a production environment. [default: disable]
web_ui: disable

# CORS Configuration
#
# Defaults to `cors: true`, which allows all origins.
# Sending/Acting on CORS headers can be completely disabled via `cors: false`
cors: true
#cors:
  # Sets the `Access-Control-Allow-Origin` header [default: *]
  # '*' will use the requests `ORIGIN` header
  #origin:
    #- http://localhost:8080
  # Sets `Access-Control-Max-Age` Header. [default: null]
  # null means not setting the header for preflight requests
  #max_age: 3600
postgres:
  connection_string: "postgresql://用户名:密码@localhost:5432/数据库名"
  auto_publish:
    tables:
      from_schemas: ["public"]
      id_regex: "^vector_.*"  # 只发布符合规则的表
mbtiles:
  paths:
    # scan this whole dir, matching all *.mbtiles files
    - F:/PluginDevelopment/shpservice/FilesData/mbtiles
      </pre>
        </div>

        <div class="guide-step">
          <h4>3. 启动服务</h4>
          <ul>
            <li>命令行运行：<code>martin config.yaml</code></li>
            <li>服务将在配置的端口启动（默认3000）</li>
            <li>访问 http://localhost:3000/catalog 查看数据源</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>4. 数据库要求</h4>
          <ul>
            <li>需要PostgreSQL数据库，并安装PostGIS扩展</li>
            <li>空间数据表需要正确的几何字段和SRID</li>
            <li>建议为表创建空间索引以提高性能</li>
          </ul>
        </div>
      </div>
    </el-dialog>

    <!-- GeoServer使用说明对话框 -->
    <el-dialog 
      v-model="showGeoServerGuide" 
      title="🌍 GeoServer使用说明" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="guide-dialog">
        <h3>🗺️ GeoServer地图服务配置</h3>
        
        <div class="guide-step">
          <h4>1. 下载和安装</h4>
          <ul>
            <li>访问 <a href="https://geoserver.org/download/" target="_blank">GeoServer官方下载页面</a></li>
            <li>选择平台包下载（推荐Web Archive (.war)或安装包）</li>
            <li>解压或安装到合适的目录</li>
            <li>需要Java 8或更高版本</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>2. 启动服务</h4>
          <ul>
            <li>Windows: 运行 bin/startup.bat</li>
            <li>Linux/Mac: 运行 bin/startup.sh</li>
            <li>默认端口8080，访问 http://localhost:8080/geoserver</li>
            <li>默认管理员账号：admin/geoserver</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>3. 工作空间和数据源</h4>
          <ul>
            <li>创建工作空间（Workspace）</li>
            <li>添加数据存储（Data Store）：Shapefile、PostGIS等</li>
            <li>发布图层（Layer）</li>
            <li>配置样式（Style）</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>4. 服务类型</h4>
          <ul>
            <li><strong>WMS：</strong>Web地图服务，返回地图图片</li>
            <li><strong>WFS：</strong>Web要素服务，返回矢量数据</li>
            <li><strong>WCS：</strong>Web覆盖服务，返回栅格数据</li>
            <li><strong>WMTS：</strong>Web地图瓦片服务</li>
          </ul>
        </div>

        <div class="guide-step">
          <h4>5. 连接配置</h4>
          <ul>
            <li><strong>服务地址：</strong>http://服务器IP:8080/geoserver</li>
            <li><strong>管理员账号：</strong>admin（或自定义）</li>
            <li><strong>管理员密码：</strong>geoserver（建议修改）</li>
            <li><strong>工作空间：</strong>发布数据时使用的工作空间名称</li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, MoreFilled, Link, Edit, Download, Document
} from '@element-plus/icons-vue'
import authService from '@/auth/authService'
import { testServiceConnection, testGeoserverInNewWindow } from '@/utils/geoserverTest'

export default {
  name: 'ServiceConnectionView',
  components: {
    Plus, Refresh, MoreFilled, Link, Edit, Download, Document
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const createLoading = ref(false)
    const testLoading = ref(false)
    const testMethod = ref('frontend') // 'frontend' 或 'backend'
    const connections = ref([])
    const connectionTestResult = ref(null)
    
    // 指南相关
    const activeGuides = ref('')
    const showFileServiceGuide = ref(false)
    const showMartinGuide = ref(false)
    const showGeoServerGuide = ref(false)
    
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
      api_key: '',
      // 文件服务配置
      file_service_url: '',
      file_folder_url: '',
      file_service_username: '',
      file_service_password: ''
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
          if (createForm.file_service_url) {
            requestData.file_service_url = createForm.file_service_url
          }
          if (createForm.file_folder_url) {
            requestData.file_folder_url = createForm.file_folder_url
          }
          if (createForm.file_service_username) {
            requestData.file_service_username = createForm.file_service_username
          }
          if (createForm.file_service_password) {
            requestData.file_service_password = createForm.file_service_password
          }
        }
        
        if (editingConnection.value) {
          // 更新连接
          console.log('🔍 前端调试 - 更新连接:', {
            connectionId: editingConnection.value.id,
            connectionIdType: typeof editingConnection.value.id,
            requestData: requestData
          })
          
          try {
            await apiRequest(`/api/service-connections/${editingConnection.value.id}`, {
              method: 'PUT',
              body: JSON.stringify(requestData)
            })
            ElMessage.success('连接更新成功')
          } catch (error) {
            // 如果连接不存在，可能是前端数据过期，重新加载连接列表
            if (error.message && error.message.includes('连接不存在')) {
              ElMessage.error('连接信息已过期，正在刷新列表...')
              await loadConnections() // 重新加载连接列表
              showCreateDialog.value = false // 关闭对话框
              editingConnection.value = null
              return
            }
            throw error // 重新抛出其他错误
          }
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
        api_key: '',
        file_service_url: '',
        file_folder_url: '',
        file_service_username: '',
        file_service_password: ''
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
      // 清空文件服务相关字段
      createForm.file_service_url = ''
      createForm.file_folder_url = ''
      createForm.file_service_username = ''
      createForm.file_service_password = ''
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
          if (createForm.file_service_url) {
            testConfig.file_service_url = createForm.file_service_url
          }
          if (createForm.file_folder_url) {
            testConfig.file_folder_url = createForm.file_folder_url
          }
          if (createForm.file_service_username) {
            testConfig.file_service_username = createForm.file_service_username
          }
          if (createForm.file_service_password) {
            testConfig.file_service_password = createForm.file_service_password
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
          if (createForm.file_service_url) {
            testData.file_service_url = createForm.file_service_url
          }
          if (createForm.file_folder_url) {
            testData.file_folder_url = createForm.file_folder_url
          }
          if (createForm.file_service_username) {
            testData.file_service_username = createForm.file_service_username
          }
          if (createForm.file_service_password) {
            testData.file_service_password = createForm.file_service_password
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
          // 显示更详细的错误信息和建议
          console.error('前端测试失败详情:', result)
          
          let errorMessage = result.message
          if (result.data && result.data.suggestion) {
            errorMessage += `\n💡 ${result.data.suggestion}`
          }
          
          // 对于CORS相关错误或需要特殊处理的情况，显示更友好的提示
          const needsSpecialHandling = result.message.includes('跨域') || 
                                      result.message.includes('CORS') || 
                                      result.message.includes('前端测试受跨域限制') ||
                                      result.message.includes('检测到远程GeoServer服务') ||
                                      (result.data && result.data.showWindowTest);
          
          if (needsSpecialHandling) {
            // 检查是否可以提供新窗口测试
            if (result.data && result.data.showWindowTest) {
              console.log('🔍 显示新窗口测试对话框:', result.data);
              showNewWindowTestDialog(connection, result.data)
            } else {
              ElMessage({
                type: 'warning',
                message: '⚠️ 前端测试受浏览器安全策略限制',
                duration: 4000,
                showClose: true
              })
              
              setTimeout(() => {
                ElMessage({
                  type: 'info',
                  message: '💡 建议使用右侧的"后端测试"按钮，后端测试不受CORS限制且更可靠',
                  duration: 6000,
                  showClose: true
                })
              }, 1500)
            }
          } else {
            ElMessage.error(errorMessage)
          }
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
        
        console.log('🔍 前端调试 - 后端测试连接:', {
          connectionId: connection.id,
          connectionIdType: typeof connection.id,
          connection: connection
        })
        
        // 🔥 在测试前先验证连接是否存在
        try {
          const response = await apiRequest('/api/service-connections')
          const currentConnections = response.data
          const currentConnection = currentConnections.find(conn => conn.id === connection.id)
          
          if (!currentConnection) {
            ElMessage.error('该连接已不存在，正在刷新列表...')
            await loadConnections()
            return
          }
        } catch (validationError) {
          console.warn('验证连接存在性失败，继续使用原连接信息:', validationError)
        }
        
        await apiRequest(`/api/service-connections/${connection.id}/test`, {
          method: 'POST'
        })
        
        ElMessage.success('连接测试成功')
        loadConnections() // 重新加载以更新测试状态
      } catch (error) {
        console.error('后端测试失败:', error)
        const errorMessage = error.message || error.toString()
        
        // 如果是404错误，可能是连接信息过期
        if (error.message && error.message.includes('404')) {
          ElMessage.error('连接信息可能已过期，正在刷新列表...')
          await loadConnections() // 重新加载连接列表
        } else {
          ElMessage.error(`后端测试失败: ${errorMessage}`)
        }
      } finally {
        connection.testing = false
        connection.testMethod = null
      }
    }
    
    // 编辑连接
    const editConnection = async (connection) => {
      console.log('🔍 前端调试 - 编辑连接:', {
        connectionId: connection.id,
        connectionIdType: typeof connection.id,
        connection: connection
      })
      
      // 🔥 在编辑前验证连接是否仍然存在
      try {
        const response = await apiRequest('/api/service-connections')
        const currentConnections = response.data
        const currentConnection = currentConnections.find(conn => conn.id === connection.id)
        
        if (!currentConnection) {
          ElMessage.error('该连接已不存在，正在刷新列表...')
          await loadConnections()
          return
        }
        
        // 使用最新的连接信息
        editingConnection.value = currentConnection
      } catch (error) {
        console.error('验证连接存在性失败:', error)
        // 如果验证失败，仍然尝试使用原连接信息
        editingConnection.value = connection
      }
      
      // 填充表单（使用最新的连接信息）
      const connToUse = editingConnection.value || connection
      createForm.service_name = connToUse.service_name
      createForm.service_type = connToUse.service_type
      createForm.server_url = connToUse.server_url
      createForm.description = connToUse.description || ''
      createForm.is_default = connToUse.is_default
      
      // 填充连接配置
      if (connToUse.connection_config) {
        const config = connToUse.connection_config
        if (connToUse.service_type === 'geoserver') {
          createForm.username = config.username || ''
          createForm.password = '' // 不显示密码
          createForm.workspace = config.workspace || 'default'
        } else if (connToUse.service_type === 'martin') {
          createForm.database_url = config.database_url || ''
          createForm.api_key = '' // 不显示API密钥
          // 文件服务配置
          createForm.file_service_url = config.file_service_url || ''
          createForm.file_folder_url = config.file_folder_url || ''
          createForm.file_service_username = config.file_service_username || ''
          createForm.file_service_password = '' // 不显示密码
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
    
    // 新窗口测试对话框
    const showNewWindowTestDialog = (connection, testData) => {
      ElMessageBox.confirm(
        '前端直接测试受到CORS限制，但我们可以通过新窗口测试连接。这将打开一个指导页面，帮助您手动验证GeoServer连接。',
        '🌐 新窗口测试',
        {
          confirmButtonText: '🚀 开始新窗口测试',
          cancelButtonText: '❌ 取消',
          type: 'info',
          dangerouslyUseHTMLString: true,
          customStyle: { width: '500px' }
        }
      ).then(async () => {
        try {
          connection.testing = true
          connection.testMethod = 'new-window'
          
          const config = {
            server_url: testData.server_url,
            username: testData.username,
            password: testData.password
          }
          
          const result = await testGeoserverInNewWindow(config)
          
          if (result.success) {
            ElMessage.success(result.message)
            connection.test_status = 'success'
          } else {
            ElMessage.error(result.message)
            connection.test_status = 'failed'
          }
          
          connection.last_tested_at = new Date().toISOString()
          
        } catch (error) {
          ElMessage.error(`新窗口测试失败: ${error.message}`)
        } finally {
          connection.testing = false
          connection.testMethod = null
        }
      }).catch(() => {
        // 用户取消
      })
    }
    
         // 文件服务下载
     const downloadFileService = async () => {
       try {
         const response = await fetch('/api/service-connections/file-service/download', {
           headers: {
             'Authorization': `Bearer ${authService.getToken()}`
           }
         });
         
         if (response.ok) {
           const blob = await response.blob();
           const url = window.URL.createObjectURL(blob);
           const a = document.createElement('a');
           a.href = url;
           a.download = '文件服务程序.zip';
           document.body.appendChild(a);
           a.click();
           window.URL.revokeObjectURL(url);
           document.body.removeChild(a);
           ElMessage.success('文件服务程序下载成功');
         } else {
           const errorData = await response.json();
           ElMessage.error(errorData.error || '下载失败');
         }
       } catch (error) {
         ElMessage.error('下载失败: ' + error.message);
       }
     };

         // Martin 官方下载
     const openMartinDownload = () => {
       const url = 'https://github.com/maplibre/martin/releases'; // 正确的Martin官方下载地址
       window.open(url, '_blank');
     };

    // GeoServer 官方下载
    const openGeoServerDownload = () => {
      const url = 'https://geoserver.org/download/'; // 示例URL
      window.open(url, '_blank');
    };

    

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
    
    // 获取文件服务信息
    const getFileServiceInfo = (connection) => {
      if (connection.service_type !== 'martin') return null
      
      let config = {}
      if (connection.connection_config) {
        if (typeof connection.connection_config === 'string') {
          try {
            config = JSON.parse(connection.connection_config)
          } catch (e) {
            return null
          }
        } else {
          config = connection.connection_config
        }
      }
      
      if (config.file_service_url) {
        return config.file_service_url
      }
      
      return null
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
      
      // 指南相关
      activeGuides,
      showFileServiceGuide,
      showMartinGuide,
      showGeoServerGuide,
      
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
      showNewWindowTestDialog,
      downloadFileService,
      openMartinDownload,
      openGeoServerDownload,
      
      // 工具方法
      getServiceTypeName,
      getServiceTypeTagType,
      getStatusText,
      getStatusTagType,
      formatDate,
      getFileServiceInfo
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

.service-guides {
  margin-bottom: 20px;
}

.guide-content {
  padding: 15px;
  background-color: #f9fafc;
  border: 1px solid #e9e9eb;
  border-radius: 4px;
}

.download-section {
  margin-bottom: 15px;
}

.download-section h4 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #303133;
}

.download-section p {
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.6;
}

.download-buttons {
  display: flex;
  gap: 10px;
}

/* 使用说明对话框样式 */
.guide-dialog {
  line-height: 1.6;
}

.guide-dialog h3 {
  color: #409EFF;
  margin-bottom: 20px;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 10px;
}

.guide-step {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-left: 4px solid #409EFF;
  border-radius: 0 4px 4px 0;
}

.guide-step h4 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 16px;
}

.guide-step ul {
  margin: 0;
  padding-left: 20px;
}

.guide-step li {
  margin-bottom: 5px;
  color: #606266;
}

.guide-step strong {
  color: #409EFF;
}

.code-block {
  background-color: #f4f4f5;
  border: 1px solid #e9e9eb;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: #2d3748;
  white-space: pre-wrap;
  margin: 10px 0;
}

.guide-step code {
  background-color: #f4f4f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #e83e8c;
}

.guide-step a {
  color: #409EFF;
  text-decoration: none;
}

.guide-step a:hover {
  text-decoration: underline;
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