<template>
  <div class="upload-page">
    <div class="page-header">
      <h1>数据管理</h1>
      <el-button type="primary" @click="showUploadDialog">数据上传</el-button>
    </div>

    <!-- 数据检索区 -->
    <div class="search-area">
      <!-- 移动端搜索切换按钮 -->
      <div class="mobile-search-toggle" @click="toggleMobileSearch">
        <el-icon class="toggle-icon" :class="{ 'rotated': mobileSearchExpanded }">
          <ArrowDown />
        </el-icon>
        <span class="toggle-text">搜索筛选</span>
        <div class="search-summary" v-if="!mobileSearchExpanded && hasActiveFilters">
          <el-tag size="small" type="primary">{{ getActiveFiltersText() }}</el-tag>
        </div>
      </div>
      
      <!-- 搜索表单 -->
      <div class="search-form-container" :class="{ 'mobile-collapsed': !mobileSearchExpanded }">
        <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="上传人员">
          <el-select v-model="searchForm.user_id" placeholder="请选择上传人员" clearable style="width: 150px;">
            <el-option v-for="user in uploaders" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="searchForm.discipline" placeholder="请选择专业" clearable style="width: 120px;">
            <el-option v-for="item in disciplines" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据类型">
          <el-select v-model="searchForm.file_type" placeholder="请选择数据类型" clearable style="width: 130px;">
            <el-option v-for="item in fileTypes" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="searchForm.tags" placeholder="请输入标签关键词" clearable style="width: 160px;" />
        </el-form-item>
        <el-form-item label="文件名">
          <el-input v-model="searchForm.file_name" placeholder="请输入文件名关键词" clearable style="width: 160px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchFiles">搜索</el-button>
          <el-button @click="resetSearch">清空</el-button>
        </el-form-item>
      </el-form>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <!-- 移动端卡片布局 -->
      <div class="mobile-file-cards">
        <div v-for="file in fileList" :key="file.id" class="mobile-file-card">
          <!-- 卡片头部：文件名和操作按钮 -->
          <div class="mobile-file-card-header">
            <div class="mobile-file-name">{{ file.file_name }}</div>
            <div class="mobile-file-actions">
              <el-button size="small" type="danger" @click="deleteFile(file)">删除</el-button>
            </div>
          </div>
          
          <!-- 基本信息网格 -->
          <div class="mobile-file-info">
            <div class="mobile-info-row">
              <div class="mobile-info-item">
                <span class="mobile-info-label">大小</span>
                <span class="mobile-info-value">{{ formatFileSize(file.file_size) }}</span>
              </div>
              <div class="mobile-info-item">
                <span class="mobile-info-label">上传人</span>
                <span class="mobile-info-value">{{ file.uploader }}</span>
              </div>
            </div>
            <div class="mobile-info-row">
              <div class="mobile-info-item">
                <span class="mobile-info-label">专业</span>
                <span class="mobile-info-value">
                  <el-tag v-if="file.discipline" size="small" type="success">{{ file.discipline }}</el-tag>
                  <span v-else>-</span>
                </span>
              </div>
              <div class="mobile-info-item">
                <span class="mobile-info-label">类型</span>
                <span class="mobile-info-value">
                  <el-tag v-if="file.file_type" size="small" type="primary">{{ file.file_type }}</el-tag>
                  <span v-else>-</span>
                </span>
              </div>
            </div>
            <!-- 坐标系信息 -->
            <div v-if="needsCoordinateSystem(file)" class="mobile-coordinate-row">
              <span class="mobile-info-label">坐标系</span>
              <div class="mobile-coordinate-container">
                <div v-if="!file.editing_coordinate" class="mobile-coordinate-display">
                  <span class="mobile-coordinate-text" :class="{ 'not-set': !file.coordinate_system }">
                    {{ file.coordinate_system || '未设置' }}
                  </span>
                  <el-button 
                    size="small" 
                    type="primary"
                    @click="startEditCoordinate(file)"
                    title="编辑坐标系"
                    class="mobile-edit-coordinate-btn"
                    circle
                  >
                    <i class="el-icon-edit"></i>
                  </el-button>
                </div>
                <div v-else class="mobile-coordinate-edit">
                  <div class="mobile-coordinate-edit-row">
                    <el-input 
                      v-model="file.temp_coordinate_system"
                      size="small"
                      placeholder="如: EPSG:4326"
                      @keyup.enter="saveCoordinate(file)"
                    />
                  </div>
                  <div class="mobile-coordinate-edit-buttons">
                    <el-button 
                      size="small" 
                      type="success"
                      @click="openCoordinateSearchForFile(file)"
                      title="搜索坐标系"
                      class="mobile-search-coordinate-btn"
                      circle
                    >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="11" cy="11" r="8"></circle>
                      <path d="m21 21-4.35-4.35"></path>
                      <path d="M11 7v8"></path>
                      <path d="M7 11h8"></path>
                    </svg>
                    </el-button>
                    <el-button 
                      size="small" 
                      type="primary"
                      @click="saveCoordinate(file)"
                      title="保存"
                      class="mobile-save-coordinate-btn"
                      circle
                    >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                      <polyline points="17,21 17,13 7,13 7,21"></polyline>
                      <polyline points="7,3 7,8 15,8"></polyline>
                      <path d="M9 17h6"></path>
                    </svg>
                    </el-button>
                    <el-button 
                      size="small" 
                      type="info"
                      @click="cancelEditCoordinate(file)"
                      title="取消"
                      class="mobile-cancel-coordinate-btn"
                      circle
                    >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="m15 9-6 6"></path>
                      <path d="m9 9 6 6"></path>
                    </svg>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="mobile-coordinate-row">
              <span class="mobile-info-label">坐标系</span>
              <span class="mobile-not-applicable-text">不适用</span>
            </div>
          </div>
          
          <!-- 服务发布状态 -->
          <div class="mobile-service-section">
            <div class="mobile-service-header">服务状态</div>
            <div class="mobile-service-grid">
              <!-- GeoServer服务 -->
              <div class="mobile-service-item">
                <div class="mobile-service-name">GeoServer</div>
                <div class="mobile-service-content">
                  <el-tag 
                    v-if="file.geoserver_service && file.geoserver_service.is_published"
                    type="success" 
                    size="small"
                  >已发布</el-tag>
                  <el-tag 
                    v-else
                    :type="canPublishGeoServer(file) ? 'info' : 'warning'" 
                    size="small"
                  >{{ canPublishGeoServer(file) ? '未发布' : '不支持' }}</el-tag>
                  <div class="mobile-service-actions">
                    <template v-if="file.geoserver_service && file.geoserver_service.is_published">
                      <el-button 
                        v-if="file.geoserver_service.wfs_url"
                        size="small" 
                        @click="copyServiceUrl(file.geoserver_service.wfs_url)"
                      >WFS</el-button>
                      <el-button 
                        v-if="file.geoserver_service.wms_url"
                        size="small" 
                        @click="copyServiceUrl(file.geoserver_service.wms_url)"
                      >WMS</el-button>
                      <el-button 
                        size="small" 
                        type="danger"
                        @click="unpublishGeoServerService(file)"
                        :loading="file.unpublishingGeoServer"
                      >取消</el-button>
                    </template>
                    <template v-else>
                      <el-button 
                        size="small" 
                        type="primary" 
                        @click="publishGeoServerService(file)"
                        :loading="file.publishingGeoServer"
                        :disabled="!canPublishGeoServer(file)"
                      >发布</el-button>
                    </template>
                  </div>
                </div>
              </div>
              
              <!-- Martin服务 -->
              <div class="mobile-service-item">
                <div class="mobile-service-name">Martin</div>
                <div class="mobile-service-content">
                  <el-tag 
                    v-if="file.martin_service && file.martin_service.is_published"
                    type="success" 
                    size="small"
                  >已发布</el-tag>
                  <el-tag v-else type="info" size="small">未发布</el-tag>
                  <div class="mobile-service-actions">
                    <template v-if="file.martin_service && file.martin_service.is_published">
                      <el-button 
                        v-if="file.martin_service.mvt_url"
                        size="small" 
                        @click="copyServiceUrl(file.martin_service.mvt_url)"
                      >MVT</el-button>
                      <el-button 
                        v-if="file.martin_service.tilejson_url"
                        size="small" 
                        @click="copyServiceUrl(file.martin_service.tilejson_url)"
                      >JSON</el-button>
                      <el-button 
                        size="small" 
                        type="danger"
                        @click="unpublishMartinService(file)"
                        :loading="file.unpublishingMartin"
                      >取消</el-button>
                    </template>
                    <template v-else>
                      <el-button 
                        size="small" 
                        type="primary" 
                        @click="publishMartinService(file)"
                        :loading="file.publishingMartin"
                        :disabled="!canPublishMartin(file)"
                      >发布</el-button>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 桌面端表格布局 -->
      <el-table :data="fileList" style="width: 100%" border>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="file_name" label="文件名" min-width="200">
          <template #default="scope">
            <div class="file-name-container">
              <el-tooltip :content="scope.row.file_name" placement="top" :disabled="scope.row.file_name.length < 20">
                <span class="file-name-text">{{ truncateText(scope.row.file_name, 20) }}</span>
              </el-tooltip>
              <el-tag 
                v-if="scope.row.discipline" 
                size="small" 
                type="success" 
                class="discipline-tag"
                effect="plain"
              >
                {{ scope.row.discipline }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="GeoServer服务" width="200">
          <template #default="scope">
            <div class="service-publish">
              <div v-if="scope.row.geoserver_service && scope.row.geoserver_service.is_published" class="published-service">
                <div class="service-status">
                  <el-tag type="success" size="small">已发布</el-tag>
                </div>
                <div class="service-actions">
                  <el-button 
                    v-if="scope.row.geoserver_service.wfs_url"
                    size="small" 
                    link 
                    @click="copyServiceUrl(scope.row.geoserver_service.wfs_url)"
                    class="service-btn"
                  >
                    <i class="el-icon-link"></i> WFS
                  </el-button>
                  <el-button 
                    v-if="scope.row.geoserver_service.wms_url"
                    size="small" 
                    link 
                    @click="copyServiceUrl(scope.row.geoserver_service.wms_url)"
                    class="service-btn"
                  >
                    <i class="el-icon-link"></i> WMS
                  </el-button>
                  <el-button 
                    size="small" 
                    link 
                    @click="unpublishGeoServerService(scope.row)"
                    :loading="scope.row.unpublishingGeoServer"
                    class="unpublish-btn"
                  >
                    <i class="el-icon-delete"></i> 取消
                  </el-button>
                </div>
              </div>
              <div v-else class="unpublished-service">
                <div class="status-info">
                  <el-tag 
                    :type="canPublishGeoServer(scope.row) ? 'info' : 'warning'" 
                    size="small"
                  >
                    {{ canPublishGeoServer(scope.row) ? '未发布' : '不能发布' }}
                  </el-tag>
                </div>
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="publishGeoServerService(scope.row)"
                  :loading="scope.row.publishingGeoServer"
                  :disabled="!canPublishGeoServer(scope.row)"
                >
                  <i class="el-icon-upload2"></i> 发布
                </el-button>
                <div v-if="!canPublishGeoServer(scope.row)" class="publish-tip">
                  <el-tooltip 
                    :content="scope.row.file_type && scope.row.file_type.toLowerCase() === 'dxf' ? 'DXF文件不支持GeoServer服务发布' : '该文件类型不支持GeoServer服务'" 
                    placement="top"
                  >
                    <i class="el-icon-warning-outline"></i>
                    <span class="tip-text">不支持</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column width="200">
          <template #header>
            <div class="column-header">
              <span>Martin服务</span>
              <el-tooltip content="重启Martin服务" placement="top">
                <el-button 
                  size="small" 
                  type="warning" 
                  circle
                  @click="restartMartinService"
                  :loading="restartingMartin"
                  class="restart-btn"
                >
                  <i class="el-icon-refresh"></i>
                </el-button>
              </el-tooltip>
            </div>
          </template>
          <template #default="scope">
            <div class="service-publish">
              <div v-if="scope.row.martin_service && scope.row.martin_service.is_published" class="published-service">
                <div class="service-status">
                  <el-tag type="success" size="small">已发布</el-tag>
                </div>
                <div class="service-actions">
                  <el-button 
                    v-if="scope.row.martin_service.mvt_url"
                    size="small" 
                    link 
                    @click="copyServiceUrl(scope.row.martin_service.mvt_url)"
                    class="service-btn"
                  >
                    <i class="el-icon-link"></i> MVT
                  </el-button>
                  <el-button 
                    v-if="scope.row.martin_service.tilejson_url"
                    size="small" 
                    link 
                    @click="copyServiceUrl(scope.row.martin_service.tilejson_url)"
                    class="service-btn"
                  >
                    <i class="el-icon-link"></i> TileJSON
                  </el-button>
                  <el-button 
                    size="small" 
                    link 
                    @click="unpublishMartinService(scope.row)"
                    :loading="scope.row.unpublishingMartin"
                    class="unpublish-btn"
                  >
                    <i class="el-icon-delete"></i> 取消
                  </el-button>
                </div>
              </div>
              <div v-else class="unpublished-service">
                <div class="status-info">
                  <el-tag type="info" size="small">未发布</el-tag>
                </div>
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="publishMartinService(scope.row)"
                  :loading="scope.row.publishingMartin"
                  :disabled="!canPublishMartin(scope.row)"
                >
                  <i class="el-icon-upload2"></i> 发布
                </el-button>
                <div v-if="!canPublishMartin(scope.row)" class="publish-tip">
                  <el-tooltip content="Martin服务支持GeoJSON、SHP、DXF、MBTiles和TIF文件" placement="top">
                    <i class="el-icon-warning-outline"></i>
                    <span class="tip-text">不支持</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="100">
          <template #default="scope">
            {{ formatFileSize(scope.row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_public" label="共有/私有" width="90">
          <template #default="scope">
            {{ scope.row.is_public ? '共有' : '私有' }}
          </template>
        </el-table-column>
        <el-table-column prop="uploader" label="上传人员" width="100" />
        <el-table-column prop="upload_date" label="上传日期" width="100">
          <template #default="scope">
            {{ formatDate(scope.row.upload_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="coordinate_system" label="坐标系" width="150">
          <template #default="scope">
            <div v-if="needsCoordinateSystem(scope.row)" class="coordinate-system-cell">
              <div v-if="!scope.row.editing_coordinate" class="coordinate-display">
                <span class="coordinate-text" :class="{ 'not-set': !scope.row.coordinate_system }">
                  {{ scope.row.coordinate_system || '未设置' }}
                </span>
                <el-button 
                  size="small" 
                  type="primary"
                  @click="startEditCoordinate(scope.row)"
                  title="编辑坐标系"
                  class="edit-coordinate-btn"
                  circle
                >
                  <i class="el-icon-edit"></i>
                </el-button>
              </div>
              <div v-else class="coordinate-edit">
                <div class="coordinate-edit-row">
                  <el-input 
                    v-model="scope.row.temp_coordinate_system"
                    size="small"
                    placeholder="如: EPSG:4326"
                    style="width: 110px;"
                    @keyup.enter="saveCoordinate(scope.row)"
                  />
                </div>
                <div class="coordinate-edit-buttons">
                  <el-button 
                    size="small" 
                    type="info"
                    link
                    @click="viewCoordinateInfo(scope.row)"
                    title="查看原始坐标系信息"
                    class="view-coordinate-btn"
                  >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  </el-button>
                  <el-button 
                    size="small" 
                    type="success"
                    link
                    @click="openCoordinateSearchForFile(scope.row)"
                    title="搜索坐标系"
                    class="search-coordinate-btn"
                  >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="11" cy="11" r="8"></circle>
                      <path d="m21 21-4.35-4.35"></path>
                      <path d="M11 7v8"></path>
                      <path d="M7 11h8"></path>
                    </svg>
                  </el-button>
                  <el-button 
                    size="small" 
                    type="primary"
                    link
                    @click="saveCoordinate(scope.row)"
                    title="保存"
                    class="save-coordinate-btn"
                  >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                      <polyline points="17,21 17,13 7,13 7,21"></polyline>
                      <polyline points="7,3 7,8 15,8"></polyline>
                      <path d="M9 17h6"></path>
                    </svg>
                  </el-button>
                  <el-button 
                    size="small" 
                    type="info"
                    link
                    @click="cancelEditCoordinate(scope.row)"
                    title="取消"
                    class="cancel-coordinate-btn"
                  >
                    <svg class="coordinate-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"></circle>
                      <path d="m15 9-6 6"></path>
                      <path d="m9 9 6 6"></path>
                    </svg>
                  </el-button>
                </div>
              </div>
            </div>
            <div v-else class="coordinate-not-applicable">
              <span class="not-applicable-text">不适用</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签/类型" width="120">
          <template #default="scope">
            <el-tooltip :content="`标签: ${scope.row.tags || '无'} | 数据类型: ${scope.row.file_type || '未知'}`" placement="top">
              <div class="tags-and-type-list">
                <!-- 数据类型标签 -->
                <el-tag 
                  v-if="scope.row.file_type" 
                  size="small" 
                  type="primary" 
                  class="file-type-tag"
                >
                  {{ scope.row.file_type }}
                </el-tag>
                
                <!-- 标签列表 -->
                <div v-if="scope.row.tags" class="tags-section">
                  <el-tag 
                    v-for="(tag, index) in getTagsList(scope.row.tags)" 
                    :key="index" 
                    size="small" 
                    type="success"
                    class="tag-item"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="dimension" label="2D/3D" width="80" />
        <el-table-column prop="description" label="文件描述" width="150">
          <template #default="scope">
            <el-tooltip :content="scope.row.description" placement="top" :disabled="!scope.row.description">
              <span class="description-text">{{ truncateText(scope.row.description, 20) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button size="small" link @click="deleteFile(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <!-- 新的写法 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[12, 24, 36, 48]"
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
    </div>

    <!-- 上传弹窗 -->
    <el-dialog title="数据上传" v-model="uploadDialogVisible" width="600px">
      <el-form :model="uploadForm" ref="uploadFormRef" :rules="rules" label-width="100px">
        <el-form-item label="文件名" prop="file_name">
          <el-input v-model="uploadForm.file_name" placeholder="请输入文件名，最多30字" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="上传文件" prop="file">
          <el-upload
            class="upload-demo"
            drag
            :http-request="handleFileUpload"
            :on-remove="handleRemove"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            :limit="1"
            :auto-upload="false"
            ref="uploadRef"
          >
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：dem.tif(最大10GB), dom.tif(最大10GB), vector.mbtiles(矢量瓦片,最大50GB), raster.mbtiles(栅格瓦片,最大50GB), dxf, geojson, zip(最大500MB, shp需打包成zip上传)<br>
                <span style="color: #67C23A; font-size: 12px;">
                  💡 大文件(>500MB)将自动使用分片上传，网络中断时会自动重试，确保上传成功
                </span>
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="专业" prop="discipline">
          <el-select v-model="uploadForm.discipline" placeholder="请选择专业">
            <el-option v-for="item in disciplines" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="2D/3D" prop="dimension">
          <el-select v-model="uploadForm.dimension" placeholder="请选择">
            <el-option label="2D" value="2D" />
            <el-option label="3D" value="3D" />
          </el-select>
        </el-form-item>
        <el-form-item label="共有/私有" prop="is_public">
          <el-select v-model="uploadForm.is_public" placeholder="请选择">
            <el-option label="共有" :value="true" />
            <el-option label="私有" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据类型" prop="file_type">
          <el-select v-model="uploadForm.file_type" placeholder="请选择数据类型" @change="handleFileTypeChange">
            <el-option v-for="item in fileTypes" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="坐标系" prop="coordinate_system" v-if="showCoordinateSystem">
          <div class="coordinate-system-input">
            <el-select v-model="uploadForm.coordinate_system" placeholder="请选择坐标系" class="coordinate-select">
              <el-option label="EPSG:3857 - Web Mercator" value="EPSG:3857" />
              <el-option label="EPSG:4326 - WGS 84" value="EPSG:4326" />
              <el-option label="EPSG:4490 - CGCS2000" value="EPSG:4490" />
              <el-option label="EPSG:4214 - Beijing 1954" value="EPSG:4214" />
              <el-option label="EPSG:4610 - Xian 1980" value="EPSG:4610" />
            </el-select>
            <el-button 
              type="primary" 
              :icon="Search" 
              @click="openCoordinateSearch"
              class="search-button"
              title="搜索更多坐标系"
            >
              搜索
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="文件标签" prop="tags">
          <el-input v-model="uploadForm.tags" placeholder="请输入标签，多个标签用逗号分隔，最多5个标签" />
          <div class="tag-tips">标签个数最多5个，一个标签最多6个中文字</div>
        </el-form-item>
        <el-form-item label="文件描述" prop="description">
          <el-input
            type="textarea"
            v-model="uploadForm.description"
            placeholder="请输入文件描述，最多300字"
            :rows="4"
            maxlength="300"
            show-word-limit
          />
        </el-form-item>
        
        <!-- 上传进度条 -->
        <el-form-item v-if="uploading">
          <div class="upload-progress">
            <div class="progress-info">
              <span class="progress-text">{{ uploadProgressText }}</span>
              <span class="progress-percentage">{{ uploadProgress }}%</span>
            </div>
            <el-progress 
              :percentage="uploadProgress" 
              :status="uploadProgressStatus"
              :stroke-width="8"
              :show-text="false"
            />
            <div class="progress-detail" v-if="uploadDetail">
              <small>{{ uploadDetail }}</small>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 坐标系搜索弹窗 -->
    <CoordinateSystemSearch 
      v-model="coordinateSearchVisible" 
      @select="handleCoordinateSelect" 
    />

    <!-- 坐标系信息查看对话框 -->
    <el-dialog
      v-model="coordinateInfoVisible"
      title="原始坐标系信息"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-loading="coordinateInfoLoading" class="coordinate-info-dialog">
        <div v-if="coordinateInfoData" class="coordinate-info-content">
          <!-- 基本文件信息 -->
          <div class="info-section">
            <h4>文件信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <label>文件名:</label>
                <span>{{ coordinateInfoData.file_name }}</span>
              </div>
              <div class="info-item">
                <label>原始文件名:</label>
                <span>{{ coordinateInfoData.original_name }}</span>
              </div>
              <div class="info-item">
                <label>文件类型:</label>
                <span>{{ coordinateInfoData.file_type }}</span>
              </div>
            </div>
          </div>

          <!-- 坐标系信息 -->
          <div class="info-section">
            <h4>坐标系信息</h4>
            <div v-if="coordinateInfoData.coordinate_info.error" class="error-message">
              <el-alert
                :title="coordinateInfoData.coordinate_info.error"
                type="error"
                :closable="false"
              />
            </div>
            <div v-else class="coordinate-details">
              <!-- Shapefile特殊信息 -->
              <div v-if="coordinateInfoData.file_type === 'shp'" class="shp-specific-info">
                <!-- ZIP文件内容 -->
                <div v-if="coordinateInfoData.coordinate_info.zip_contents" class="info-item">
                  <label>ZIP文件内容:</label>
                  <div class="zip-contents">
                    <el-tag v-for="file in coordinateInfoData.coordinate_info.zip_contents" :key="file" 
                            size="small" type="info" class="file-tag">
                      {{ file }}
                    </el-tag>
                  </div>
                </div>

                <!-- .prj文件内容 -->
                <div v-if="coordinateInfoData.coordinate_info.prj_file_content" class="info-item">
                  <label>.prj文件内容:</label>
                  <el-input
                    type="textarea"
                    :value="coordinateInfoData.coordinate_info.prj_file_content"
                    :rows="4"
                    readonly
                    class="prj-textarea"
                  />
                </div>

                <!-- PRJ与GDAL信息对比 -->
                <div v-if="coordinateInfoData.coordinate_info.prj_gdal_comparison" class="info-item">
                  <label>坐标系信息验证:</label>
                  <div class="comparison-result">
                    <el-alert
                      :title="coordinateInfoData.coordinate_info.prj_gdal_comparison.match ? 
                              '.prj文件与GDAL读取的坐标系信息一致' : 
                              '.prj文件与GDAL读取的坐标系信息不一致'"
                      :type="coordinateInfoData.coordinate_info.prj_gdal_comparison.match ? 'success' : 'warning'"
                      :closable="false"
                    />
                  </div>
                </div>
              </div>

              <!-- EPSG代码 -->
              <div v-if="coordinateInfoData.coordinate_info.epsg_code" class="info-item">
                <label>EPSG代码:</label>
                <el-tag type="primary" size="large">{{ coordinateInfoData.coordinate_info.epsg_code }}</el-tag>
              </div>
              
              <!-- 投影参数机构 -->
              <div v-if="coordinateInfoData.coordinate_info.authority" class="info-item">
                <label>参数机构:</label>
                <span>{{ coordinateInfoData.coordinate_info.authority }}</span>
              </div>

              <!-- WKT信息 -->
              <div v-if="coordinateInfoData.coordinate_info.wkt" class="info-item wkt-section">
                <label>WKT格式:</label>
                <el-input
                  type="textarea"
                  :value="coordinateInfoData.coordinate_info.wkt"
                  :rows="6"
                  readonly
                  class="wkt-textarea"
                />
              </div>

              <!-- PROJ4信息 -->
              <div v-if="coordinateInfoData.coordinate_info.proj4" class="info-item">
                <label>PROJ4格式:</label>
                <el-input
                  :value="coordinateInfoData.coordinate_info.proj4"
                  readonly
                  class="proj4-input"
                />
              </div>

              <!-- 空间范围 -->
              <div v-if="coordinateInfoData.coordinate_info.extent" class="info-item">
                <label>空间范围:</label>
                <div class="extent-info">
                  <div v-if="coordinateInfoData.coordinate_info.extent.type === 'bounds'">
                    <div class="bounds-grid">
                      <div>西: {{ coordinateInfoData.coordinate_info.extent.coordinates.west }}</div>
                      <div>东: {{ coordinateInfoData.coordinate_info.extent.coordinates.east }}</div>
                      <div>南: {{ coordinateInfoData.coordinate_info.extent.coordinates.south }}</div>
                      <div>北: {{ coordinateInfoData.coordinate_info.extent.coordinates.north }}</div>
                    </div>
                  </div>
                  <div v-else>
                    <code>{{ JSON.stringify(coordinateInfoData.coordinate_info.extent, null, 2) }}</code>
                  </div>
                </div>
              </div>

              <!-- 栅格信息（针对TIF文件） -->
              <div v-if="coordinateInfoData.coordinate_info.raster_size" class="info-item">
                <label>栅格大小:</label>
                <span>{{ coordinateInfoData.coordinate_info.raster_size[0] }} × {{ coordinateInfoData.coordinate_info.raster_size[1] }} 像素</span>
              </div>
              
              <div v-if="coordinateInfoData.coordinate_info.band_count" class="info-item">
                <label>波段数:</label>
                <span>{{ coordinateInfoData.coordinate_info.band_count }}</span>
              </div>
              
              <div v-if="coordinateInfoData.coordinate_info.data_type" class="info-item">
                <label>数据类型:</label>
                <span>{{ coordinateInfoData.coordinate_info.data_type }}</span>
              </div>

              <!-- MBTiles特殊信息 -->
              <div v-if="coordinateInfoData.coordinate_info.tile_info" class="info-item">
                <label>瓦片信息:</label>
                <div class="tile-info-grid">
                  <div v-for="(value, key) in coordinateInfoData.coordinate_info.tile_info" :key="key" class="tile-info-item">
                    <label>{{ key }}:</label>
                    <span>{{ value }}</span>
                  </div>
                </div>
              </div>

                              <!-- 边界分析（针对没有坐标系的shapefile） -->
                <div v-if="coordinateInfoData.coordinate_info.extent_analysis" class="info-item">
                  <label>数据边界分析:</label>
                  <div class="extent-analysis">
                    <div class="bounds-info">
                      <div class="bound-item">
                        <span>范围: </span>
                        <code>{{ coordinateInfoData.coordinate_info.extent_analysis.min_x?.toFixed(6) }}, {{ coordinateInfoData.coordinate_info.extent_analysis.min_y?.toFixed(6) }}</code>
                        <span> 到 </span>
                        <code>{{ coordinateInfoData.coordinate_info.extent_analysis.max_x?.toFixed(6) }}, {{ coordinateInfoData.coordinate_info.extent_analysis.max_y?.toFixed(6) }}</code>
                      </div>
                      <div class="bound-item">
                        <span>尺寸: </span>
                        <code>{{ coordinateInfoData.coordinate_info.extent_analysis.width?.toFixed(6) }} × {{ coordinateInfoData.coordinate_info.extent_analysis.height?.toFixed(6) }}</code>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 分析注释 -->
                <div v-if="coordinateInfoData.coordinate_info.analysis_notes && coordinateInfoData.coordinate_info.analysis_notes.length > 0" class="info-item">
                  <label>分析结果:</label>
                  <div class="analysis-notes">
                    <div v-for="(note, index) in coordinateInfoData.coordinate_info.analysis_notes" :key="index" class="note-item">
                      <i class="el-icon-info"></i>
                      <span>{{ note }}</span>
                    </div>
                  </div>
                </div>

                <!-- 坐标系建议 -->
                <div v-if="coordinateInfoData.coordinate_info.suggested_crs && coordinateInfoData.coordinate_info.suggested_crs.length > 0" class="info-item">
                  <label>建议的坐标系:</label>
                  <div class="suggested-crs">
                    <div v-for="(suggestion, index) in coordinateInfoData.coordinate_info.suggested_crs" :key="index" class="crs-suggestion">
                      <el-tag type="success" size="small">{{ suggestion.epsg }}</el-tag>
                      <span class="crs-name">{{ suggestion.name }}</span>
                      <span class="crs-reason">{{ suggestion.reason }}</span>
                    </div>
                  </div>
                </div>

                <!-- 通用坐标系建议 -->
                <div v-if="coordinateInfoData.coordinate_info.suggestions" class="info-item">
                  <label>常用坐标系参考:</label>
                  <div class="coordinate-suggestions">
                    <!-- 地理坐标系 -->
                    <div class="suggestion-category">
                      <h5>地理坐标系（经纬度）:</h5>
                      <div v-for="(crs, index) in coordinateInfoData.coordinate_info.suggestions.common_geographic" :key="'geo-' + index" class="crs-item">
                        <div class="crs-header">
                          <el-tag type="primary" size="small">{{ crs.epsg }}</el-tag>
                          <span class="crs-title">{{ crs.name }}</span>
                        </div>
                        <div class="crs-description">{{ crs.description }}</div>
                        <div class="crs-use-cases">
                          <span class="use-case-label">适用于:</span>
                          <el-tag v-for="useCase in crs.use_cases" :key="useCase" size="mini" type="info">{{ useCase }}</el-tag>
                        </div>
                      </div>
                    </div>

                    <!-- 投影坐标系 -->
                    <div class="suggestion-category">
                      <h5>投影坐标系（米/英尺）:</h5>
                      <div v-for="(crs, index) in coordinateInfoData.coordinate_info.suggestions.common_projected" :key="'proj-' + index" class="crs-item">
                        <div class="crs-header">
                          <el-tag type="warning" size="small">{{ crs.epsg }}</el-tag>
                          <span class="crs-title">{{ crs.name }}</span>
                        </div>
                        <div class="crs-description">{{ crs.description }}</div>
                        <div class="crs-use-cases">
                          <span class="use-case-label">适用于:</span>
                          <el-tag v-for="useCase in crs.use_cases" :key="useCase" size="mini" type="info">{{ useCase }}</el-tag>
                        </div>
                      </div>
                    </div>

                    <!-- 检测提示 -->
                    <div class="suggestion-category">
                      <h5>检测提示:</h5>
                      <div class="detection-tips">
                        <div v-for="(tip, index) in coordinateInfoData.coordinate_info.suggestions.detection_tips" :key="index" class="tip-item">
                          <i class="el-icon-bulb"></i>
                          <span>{{ tip }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 注意事项 -->
                <div v-if="coordinateInfoData.coordinate_info.note" class="info-item">
                  <el-alert
                    :title="coordinateInfoData.coordinate_info.note"
                    type="info"
                    :closable="false"
                  />
                </div>
            </div>
          </div>
        </div>
        
        <div v-if="coordinateInfoLoading" class="loading-message">
          正在读取坐标系信息...
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="coordinateInfoVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- TIF转换进度对话框 -->
    <TifConversionDialog
      v-model:visible="tifConversionDialogVisible"
      :task-id="tifConversionTaskId"
      :file-info="tifConversionFileInfo"
      :min-zoom="tifConversionMinZoom"
      :max-zoom="tifConversionMaxZoom"
      @completed="handleTifConversionCompleted"
      @error="handleTifConversionError"
      @retry="handleTifConversionRetry"
      @close="handleTifConversionDialogClose"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'
import gisApi from '@/api/gis'
import CoordinateSystemSearch from '@/components/CoordinateSystemSearch.vue'
import TifConversionDialog from '@/components/TifConversionDialog.vue'
import { processServiceUrl } from '@/utils/urlUtils.js'

export default {
  name: 'UploadView',
  components: {
    CoordinateSystemSearch,
    TifConversionDialog
  },
  setup() {
    // 响应式数据
    const fileList = ref([])
    const uploaders = ref([])
    const disciplines = ref(['综合', '测绘', '地勘', '水文', '水工', '施工', '建筑', '金结', '电一', '电二', '消防', '暖通', '给排水', '环水', '移民', '其他'])
    const fileTypes = ref(['shp', 'dem.tif', 'dom.tif', 'dxf', 'geojson', 'vector.mbtiles', 'raster.mbtiles'])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(12)
    const uploadDialogVisible = ref(false)
    const uploading = ref(false)
    const restartingMartin = ref(false)
    
    // 坐标系搜索相关
    const coordinateSearchVisible = ref(false)
    const currentEditingFile = ref(null)
    
    // 坐标系信息查看对话框相关
    const coordinateInfoVisible = ref(false)
    const coordinateInfoData = ref(null)
    const coordinateInfoLoading = ref(false) // 添加当前正在编辑的文件引用
    
    // TIF转换对话框相关
    const tifConversionDialogVisible = ref(false)
    const tifConversionTaskId = ref('')
    const tifConversionFileInfo = ref({})
    const tifConversionMinZoom = ref(2)
    const tifConversionMaxZoom = ref(18)
    
    // 移动端搜索相关
    const mobileSearchExpanded = ref(false)
    
    // 表单引用
    const uploadFormRef = ref(null)
    const uploadRef = ref(null)
    
    // 搜索表单
    const searchForm = reactive({
      user_id: '',
      discipline: '',
      file_type: '',
      tags: '',
      file_name: ''
    })
    
    // 上传表单
    const uploadForm = reactive({
      file_name: '',
      file: null,
      discipline: '',
      dimension: '',
      is_public: true,
      file_type: '',
      coordinate_system: '',
      tags: '',
      description: ''
    })
    
    // 表单验证规则
    const rules = {
      file_name: [
        { required: true, message: '请输入文件名', trigger: 'blur' },
        { min: 1, max: 30, message: '文件名长度在1到30个字符', trigger: 'blur' }
      ],
      discipline: [
        { required: true, message: '请选择专业', trigger: 'change' }
      ],
      dimension: [
        { required: true, message: '请选择2D/3D', trigger: 'change' }
      ],
      file_type: [
        { required: true, message: '请选择数据类型', trigger: 'change' }
      ],
      coordinate_system: [
        { 
          validator: (rule, value, callback) => {
            if (['dxf', 'dom.tif', 'dem.tif'].includes(uploadForm.file_type) && !value) {
              callback(new Error('DXF/TIF文件必须选择坐标系'))
            } else {
              callback()
            }
          }, 
          trigger: 'change' 
        }
      ]
    }
    
    // 上传进度相关
    const uploadProgress = ref(0)
    const uploadProgressText = ref('')
    const uploadProgressStatus = ref('')
    const uploadDetail = ref('')
    
    // 生命周期
    onMounted(() => {
      fetchFileList()
      fetchUploaders()
    })
    
    // 方法
    // 获取文件列表
    const fetchFileList = async () => {
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value
        }
        
        // 映射搜索参数
        if (searchForm.user_id) {
          params.user_id = searchForm.user_id
        }
        
        if (searchForm.discipline) {
          params.discipline = searchForm.discipline
        }
        
        if (searchForm.file_type) {
          params.file_type = searchForm.file_type
        }
        
        // 将标签和文件名合并为search参数
        const searchTerms = []
        if (searchForm.tags) {
          searchTerms.push(searchForm.tags.trim())
        }
        if (searchForm.file_name) {
          searchTerms.push(searchForm.file_name.trim())
        }
        
        if (searchTerms.length > 0) {
          params.search = searchTerms.join(' ')
        }
        
        const response = await gisApi.getFiles(params)
        
        fileList.value = response.data.files
        //console.log('文件列表:', response)
        total.value = response.total
      } catch (error) {
        ElMessage.error('获取文件列表失败')
      }
    }

    // 获取上传人员列表
    const fetchUploaders = async () => {
      try {
        const response = await gisApi.getUsers()
        uploaders.value = response.users
      } catch (error) {
        console.error('获取上传人员列表失败', error)
      }
    }

    // 搜索文件
    const searchFiles = () => {
      currentPage.value = 1
      fetchFileList()
    }

    // 重置搜索
    const resetSearch = () => {
      Object.keys(searchForm).forEach(key => {
        searchForm[key] = ''
      })
      currentPage.value = 1
      fetchFileList()
    }
    
    // 切换移动端搜索展开状态
    const toggleMobileSearch = () => {
      mobileSearchExpanded.value = !mobileSearchExpanded.value
    }
    
    // 检查是否有激活的筛选条件
    const hasActiveFilters = computed(() => {
      return searchForm.user_id || searchForm.discipline || searchForm.file_type || searchForm.tags || searchForm.file_name
    })
    
    // 获取激活筛选条件的文字描述
    const getActiveFiltersText = () => {
      const filters = []
      if (searchForm.user_id) filters.push('用户')
      if (searchForm.discipline) filters.push('专业')
      if (searchForm.file_type) filters.push('类型')
      if (searchForm.tags) filters.push('标签')
      if (searchForm.file_name) filters.push('文件名')
      return filters.length > 0 ? `${filters.join('+')}` : ''
    }

    // 分页变化
    const handleSizeChange = (val) => {
      pageSize.value = val
      fetchFileList()
    }
    
    const handleCurrentChange = (val) => {
      currentPage.value = val
      fetchFileList()
    }

    // 显示上传对话框
    const showUploadDialog = () => {
      uploadDialogVisible.value = true
      resetUploadForm()
    }

    // 重置上传表单
    const resetUploadForm = () => {
      if (uploadFormRef.value) {
        uploadFormRef.value.resetFields()
      }
      
      // 重置表单数据
      uploadForm.file_name = ''
      uploadForm.file = null
      uploadForm.discipline = ''
      uploadForm.dimension = ''
      uploadForm.is_public = true
      uploadForm.file_type = ''
      uploadForm.coordinate_system = ''
      uploadForm.tags = ''
      uploadForm.description = ''
      
      // 重置进度状态
      uploadProgress.value = 0
      uploadProgressText.value = ''
      uploadProgressStatus.value = ''
      uploadDetail.value = ''
      
      // 清除upload组件的文件列表
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
    }

    // 文件类型变化
    const handleFileTypeChange = (val) => {
      // 如果不是需要坐标系的文件类型，则清空坐标系
      if (!['dxf', 'dom.tif', 'dem.tif'].includes(val)) {
        uploadForm.coordinate_system = ''
      }
    }

    // 处理文件上传前的验证
    const beforeUpload = (/* file */) => { // 注释掉未使用的参数
      // 在auto-upload=false模式下，主要的文件处理在handleFileChange中
      // 这里只是一个额外的检查
      return false // 阻止自动上传
    }

    // 处理文件移除
    const handleRemove = () => {
      //console.log('文件被移除')
      uploadForm.file = null
    }

    // 处理文件变化（选择/拖拽）
    const handleFileChange = (file) => {
      //console.log('文件变化:', file)
      
      if (file && file.raw) {
        const validExtensions = ['tif', 'mbtiles', 'dxf', 'geojson', 'zip']
        const extension = file.name.split('.').pop().toLowerCase()
        
        if (!validExtensions.includes(extension)) {
          ElMessage.error('不支持的文件类型！')
          // 清除文件
          if (uploadRef.value) {
            uploadRef.value.clearFiles()
          }
          uploadForm.file = null
          return
        }
        
        // 根据文件扩展名自动设置文件类型
        if (extension === 'mbtiles') {
          // 对于mbtiles文件，需要用户选择是矢量还是栅格类型
          // 默认不设置，让用户自己选择
          if (!uploadForm.file_type || !uploadForm.file_type.includes('mbtiles')) {
            ElMessage.info('请在下方选择正确的MBTiles类型：vector.mbtiles(矢量瓦片)或raster.mbtiles(栅格瓦片)')
          }
        } else if (extension === 'tif') {
          // 对于tif文件，可以自动设置为dem.tif
          if (!uploadForm.file_type || !uploadForm.file_type.includes('tif')) {
            uploadForm.file_type = 'dem.tif'
          }
        } else if (extension === 'dxf') {
          uploadForm.file_type = 'dxf'
        
        } else if (extension === 'geojson') {
          uploadForm.file_type = 'geojson'
        } else if (extension === 'zip') {
          uploadForm.file_type = 'shp'
        }
        
        uploadForm.file = file.raw
        //console.log('文件已设置:', uploadForm.file)
      } else {
        uploadForm.file = null
      }
    }

    // 自定义上传
    const handleFileUpload = () => {
      // 这个函数在auto-upload=false时不会被调用
      // 实际的上传逻辑在submitUpload中处理
      return false
    }

    // 提交上传
    const submitUpload = async () => {
      //console.log('开始提交上传，当前文件:', uploadForm.file)
      
      if (!uploadForm.file) {
        ElMessage.error('请选择文件')
        return
      }
      
      try {
        await uploadFormRef.value.validate()
        
        // 验证需要坐标系的文件类型必须有坐标系
        if (['dxf', 'dom.tif', 'dem.tif'].includes(uploadForm.file_type) && !uploadForm.coordinate_system) {
          ElMessage.error('DXF/TIF文件必须选择坐标系')
          return
        }
        
        uploading.value = true
        
        // 重置进度状态
        uploadProgress.value = 0
        uploadProgressStatus.value = ''
        uploadDetail.value = ''
        
        // 创建表单数据
        const formData = new FormData()
        formData.append('file', uploadForm.file)
        
        // 添加其他字段
        Object.keys(uploadForm).forEach(key => {
          if (key !== 'file' && uploadForm[key] !== null && uploadForm[key] !== undefined) {
            formData.append(key, uploadForm[key])
          }
        })
        
        //console.log('表单数据准备完成，开始发送请求')
        //console.log('上传表单数据:', uploadForm)
        
        // 检查文件大小，显示相应提示和进度文本
        const fileSizeMB = uploadForm.file.size / 1024 / 1024
        if (fileSizeMB > 500) {
          uploadProgressText.value = '分片上传中'
          uploadDetail.value = `文件大小: ${fileSizeMB.toFixed(2)}MB，使用分片上传模式`
          ElMessage.info(`文件较大(${fileSizeMB.toFixed(2)}MB)，将使用分片上传模式，请耐心等待...`)
        } else {
          uploadProgressText.value = '文件上传中'
          uploadDetail.value = `文件大小: ${fileSizeMB.toFixed(2)}MB`
        }
        
        // 发送上传请求
        await gisApi.uploadFile(formData, (progress) => {
          //console.log(`上传进度: ${progress}%`)
          uploadProgress.value = progress
          
          // 根据进度更新状态
          if (progress === 100) {
            uploadProgressText.value = '处理文件中'
            uploadProgressStatus.value = 'success'
            uploadDetail.value = '文件上传完成，正在处理...'
          } else {
            uploadProgressStatus.value = ''
            if (fileSizeMB > 500) {
              uploadDetail.value = `分片上传进度: ${progress}%，文件大小: ${fileSizeMB.toFixed(2)}MB`
            } else {
              uploadDetail.value = `上传进度: ${progress}%，文件大小: ${fileSizeMB.toFixed(2)}MB`
            }
          }
        })
        
        // 上传成功
        uploadProgress.value = 100
        uploadProgressText.value = '上传完成'
        uploadProgressStatus.value = 'success'
        uploadDetail.value = '文件上传并处理成功'
        
        ElMessage.success('数据上传成功！如需发布服务，请在列表中点击"发布服务"按钮')
        
        // 延迟关闭对话框，让用户看到成功状态
        setTimeout(() => {
          uploadDialogVisible.value = false
        }, 1000)
        
        fetchFileList()
      } catch (error) {
        console.error('文件上传失败', error)
        
        // 设置失败状态
        uploadProgressStatus.value = 'exception'
        uploadProgressText.value = '上传失败'
        
        // 根据错误类型显示不同的提示
        let errorMessage = '文件上传失败'
        if (error.message) {
          if (error.message.includes('分片')) {
            errorMessage = `分片上传失败: ${error.message}`
            uploadDetail.value = '分片上传过程中发生错误'
          } else if (error.message.includes('网络')) {
            errorMessage = '网络连接失败，请检查网络状态后重试'
            uploadDetail.value = '网络连接中断，请检查网络后重试'
          } else if (error.message.includes('超时')) {
            errorMessage = '上传超时，请重试。如果文件很大，请确保网络稳定'
            uploadDetail.value = '上传超时，建议检查网络稳定性'
          } else {
            errorMessage = error.message
            uploadDetail.value = error.message
          }
        }
        
        ElMessage.error(errorMessage)
      } finally {
        uploading.value = false
        
        // 延迟重置进度状态
        setTimeout(() => {
          uploadProgress.value = 0
          uploadProgressText.value = ''
          uploadProgressStatus.value = ''
          uploadDetail.value = ''
        }, 3000)
      }
    }

    // 删除文件
    const deleteFile = (file) => {
      ElMessageBox.confirm(`确认删除"${file.file_name}"数据？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await gisApi.deleteFile(file.id)
          ElMessage.success('文件删除成功')
          fetchFileList()
        } catch (error) {
          console.error('删除文件失败', error)
          const errorMessage = error.response?.data?.error || error.response?.data?.message || error.message || '删除文件失败'
          ElMessage.error(errorMessage)
        }
      }).catch(() => {
        // 用户取消删除操作，不需要显示错误信息
      })
    }

    // 辅助方法
    // 格式化文件大小
    const formatFileSize = (size) => {
      if (!size) return '0 B'
      
      const units = ['B', 'KB', 'MB', 'GB']
      let index = 0
      while (size >= 1024 && index < units.length - 1) {
        size /= 1024
        index++
      }
      
      return size.toFixed(2) + ' ' + units[index]
    }
    
    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      
      const date = new Date(dateStr)
      return date.toLocaleDateString()
    }
    
    // 截断文本
    const truncateText = (text, maxLength) => {
      if (!text) return ''
      
      if (text.length <= maxLength) {
        return text
      }
      
      return text.substr(0, maxLength) + '...'
    }
    
    // 获取标签列表
    const getTagsList = (tagsStr) => {
      if (!tagsStr) return []
      
      return tagsStr.split(',').filter(tag => tag.trim())
    }

    // 服务发布相关方法
    // 判断文件是否可以发布GeoServer服务
    const canPublishGeoServer = (file) => {
      const geoserverSupportedTypes = ['shp', 'geojson', 'tif', 'tiff', 'dem.tif', 'dom.tif']
      return geoserverSupportedTypes.includes(file.file_type.toLowerCase())
    }

    // 判断文件是否可以发布Martin服务
    const canPublishMartin = (file) => {
      const martinSupportedTypes = ['geojson', 'shp', 'dxf', 'mbtiles', 'vector.mbtiles', 'raster.mbtiles', 'tif', 'tiff', 'dem.tif', 'dom.tif']
      return martinSupportedTypes.includes(file.file_type.toLowerCase())
    }

    // 发布GeoServer服务
    const publishGeoServerService = async (file) => {
      if (!file) {
        ElMessage.warning('请先选择要发布的文件')
        return
      }
      
      try {
        //console.log(`发布GeoServer服务：${file.id}`)
        
        // 检查需要坐标系的文件类型是否需要坐标系选择
        let publishParams = {}
        const needsCoordinateSystem = ['shp', 'dxf', 'dom.tif', 'dem.tif', 'tif', 'tiff', 'dom', 'dem'].includes(file.file_type.toLowerCase())
        
        if (needsCoordinateSystem) {
          const coordinate_system = file.coordinate_system || await selectCoordinateSystemForPublish(file)
          if (!coordinate_system) {
            ElMessage.warning(`${file.file_type.toUpperCase()}文件发布需要选择坐标系`)
            return
          }
          publishParams.coordinate_system = coordinate_system
          
          // 特别提示EPSG:2379等投影坐标系
          if (coordinate_system === 'EPSG:2379') {
            ElMessage.info('正在使用CGCS2000 39度带投影坐标系发布DOM文件')
          }
        }
        
        // 设置发布中状态
        file.publishingGeoServer = true
        
        const result = await gisApi.publishGeoServerService(file.id, publishParams)
        
        if (result.success) {
          ElMessage.success(`GeoServer服务发布成功${result.coordinate_system ? `，坐标系: ${result.coordinate_system}` : ''}`)
          fetchFileList() // 刷新列表
        } else {
          throw new Error(result.error || 'GeoServer服务发布失败')
        }
      } catch (error) {
        console.error('发布GeoServer服务失败', error)
        ElMessage.error(`发布GeoServer服务失败: ${error.response?.data?.error || error.message || '未知错误'}`)
      } finally {
        file.publishingGeoServer = false
      }
    }

    // 发布Martin服务
    const publishMartinService = async (file) => {
      if (!file) {
        ElMessage.warning('请先选择要发布的文件')
        return
      }
      
      try {
        // 设置发布中状态
        file.publishingMartin = true
        
        let result
        let publishParams = {}
        
        // 检查DXF文件是否需要坐标系选择
        if (file.file_type.toLowerCase() === 'dxf') {
          const coordinate_system = file.coordinate_system || await selectCoordinateSystemForPublish(file)
          if (!coordinate_system) {
            ElMessage.warning('DXF文件发布需要选择坐标系')
            return
          }
          publishParams.coordinate_system = coordinate_system
          
          // 使用DXF专用的Martin发布接口
          result = await gisApi.publishDxfMartinService(file.id, publishParams)
        } else if (file.file_type.toLowerCase() === 'mbtiles' || file.file_type.toLowerCase() === 'vector.mbtiles' || file.file_type.toLowerCase() === 'raster.mbtiles') {
          // 使用MBTiles专用的Martin发布接口
          result = await gisApi.publishMbtilesMartinService(file.id, publishParams)
        } else if (['tif', 'tiff', 'dem.tif', 'dom.tif'].includes(file.file_type.toLowerCase())) {
          // TIF文件需要转换为MBTiles再发布Martin服务
          
          // 询问用户是否确认转换
          try {
            await ElMessageBox.confirm(
              `TIF文件需要先转换为MBTiles格式才能发布Martin服务。\n\n转换过程可能需要几分钟到几十分钟，具体取决于文件大小。\n\n确认开始转换并发布吗？`,
              '确认TIF转换',
              {
                confirmButtonText: '确定转换',
                cancelButtonText: '取消',
                type: 'info',
                dangerouslyUseHTMLString: true
              }
            )
          } catch {
            return // 用户取消操作
          }
          
          // 获取转换参数
          let maxZoom = 20 // 默认最大缩放级别
          let minZoom = 2 // 默认最小缩放级别
          
          try {
            const { value } = await ElMessageBox.prompt(
              '请设置最大缩放级别（1-25）：\n\n建议值：\n- 小文件(<50MB): 18级\n- 中等文件(50-200MB): 20级\n- 大文件(>200MB): 16级',
              '设置缩放级别',
              {
                confirmButtonText: '确定',
                cancelButtonText: '使用默认值(20)',
                inputPattern: /^([1-9]|1[0-9]|2[0-5])$/,
                inputErrorMessage: '请输入1-25之间的数字',
                inputValue: '20',
                dangerouslyUseHTMLString: true
              }
            )
            maxZoom = parseInt(value) || 20
          } catch {
            // 用户取消或使用默认值
            maxZoom = 20
          }
          
          publishParams.max_zoom = maxZoom
          publishParams.min_zoom = minZoom
          
            // 启动异步转换任务
            const conversionResponse = await gisApi.startTifConversionAsync(file.id, publishParams)
            
            if (conversionResponse.success) {
              // 设置对话框信息
              tifConversionFileInfo.value = {
                name: file.file_name,
                type: file.file_type,
                id: file.id
              }
              tifConversionTaskId.value = conversionResponse.task_id
              tifConversionMinZoom.value = minZoom
              tifConversionMaxZoom.value = maxZoom
              
              // 显示转换进度对话框
              tifConversionDialogVisible.value = true
              
              // 监听转换完成事件
              const handleConversionCompleted = () => {
                ElMessage.success('TIF文件转换并发布Martin服务成功')
                fetchFileList() // 刷新文件列表
                file.publishingMartin = false // 重要：重置发布状态
              }
              
              const handleConversionError = (error) => {
                ElMessage.error(`转换失败: ${error}`)
                file.publishingMartin = false // 重要：重置发布状态
              }
              
              // 监听对话框关闭事件
              const handleDialogClose = () => {
                file.publishingMartin = false // 重要：对话框关闭时也要重置状态
              }
              
              // 临时存储事件处理器以便清理
              tifConversionFileInfo.value.onCompleted = handleConversionCompleted
              tifConversionFileInfo.value.onError = handleConversionError
              tifConversionFileInfo.value.onDialogClose = handleDialogClose
              
              ElMessage.success('TIF转换任务已启动，正在后台处理...')
              
              // 成功启动异步任务，不执行后续的同步result处理逻辑
              return
            } else {
              throw new Error(conversionResponse.error || '启动转换任务失败')
          }
        } else {
          // 使用通用的Martin发布接口
          result = await gisApi.publishMartinService(file.id, publishParams)
        }
        
        if (result.success) {
          ElMessage.success('Martin服务发布成功')
          fetchFileList() // 刷新列表
        } else {
          throw new Error(result.error || 'Martin服务发布失败')
        }
      } catch (error) {
        console.error('发布Martin服务失败', error)
        ElMessage.error(`发布Martin服务失败: ${error.response?.data?.error || error.message || '未知错误'}`)
      } finally {
        file.publishingMartin = false
      }
    }

    // 为发布选择坐标系的函数
    const selectCoordinateSystemForPublish = async (file) => {
      return new Promise((resolve) => {
        ElMessageBox.prompt(
          `文件"${file.file_name}"需要设置坐标系，请选择坐标系：`,
          '选择坐标系',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            inputPattern: /^EPSG:\d+$/,
            inputErrorMessage: '请输入有效的坐标系格式，如 EPSG:4326',
            inputValue: 'EPSG:4326'
          }
        ).then(({ value }) => {
          resolve(value)
        }).catch(() => {
          resolve(null)
        })
      })
    }

    // 取消发布GeoServer服务
    const unpublishGeoServerService = async (file) => {
      try {
        await ElMessageBox.confirm(
          `确认取消发布"${file.file_name}"的GeoServer服务吗？取消后将无法通过WMS/WFS访问数据。`,
          '确认取消发布',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        file.unpublishingGeoServer = true
        
        const response = await gisApi.unpublishGeoServerService(file.id)
        
        if (response.success) {
          ElMessage.success('GeoServer服务取消发布成功')
          fetchFileList() // 刷新列表
        } else {
          throw new Error(response.error || 'GeoServer服务取消发布失败')
        }
      } catch (error) {
        if (error === 'cancel') return
        console.error('取消发布GeoServer服务失败', error)
        ElMessage.error(`取消发布GeoServer服务失败: ${error.response?.data?.error || error.message || '未知错误'}`)
      } finally {
        file.unpublishingGeoServer = false
      }
    }

    // 取消发布Martin服务
    const unpublishMartinService = async (file) => {
      try {
        await ElMessageBox.confirm(
          `确认取消发布"${file.file_name}"的Martin服务吗？取消后将无法通过MVT瓦片访问数据。`,
          '确认取消发布',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        file.unpublishingMartin = true
        
        const response = await gisApi.unpublishMartinService(file.id)
        
        if (response.success) {
          ElMessage.success('Martin服务取消发布成功')
          fetchFileList() // 刷新列表
        } else {
          throw new Error(response.error || 'Martin服务取消发布失败')
        }
      } catch (error) {
        if (error === 'cancel') return
        console.error('取消发布Martin服务失败', error)
        ElMessage.error(`取消发布Martin服务失败: ${error.response?.data?.error || error.message || '未知错误'}`)
      } finally {
        file.unpublishingMartin = false
      }
    }



    // 复制服务地址
    const copyServiceUrl = async (url) => {
      try {
        // 使用工具函数处理URL中的localhost地址替换
        const processedUrl = processServiceUrl(url)
        
        await navigator.clipboard.writeText(processedUrl)
        ElMessage.success('服务地址已复制到剪贴板')
        
        // 在开发环境下显示URL转换信息
        if (process.env.NODE_ENV === 'development' && url !== processedUrl) {
          //console.log('原始URL:', url)
          //console.log('处理后URL:', processedUrl)
        }
      } catch (error) {
        // 降级方案：创建临时输入框
        const processedUrl = processServiceUrl(url)
        
        const textArea = document.createElement('textarea')
        textArea.value = processedUrl
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        ElMessage.success('服务地址已复制到剪贴板')
        
        // 在开发环境下显示URL转换信息
        if (process.env.NODE_ENV === 'development' && url !== processedUrl) {
          //console.log('原始URL:', url)
          //console.log('处理后URL:', processedUrl)
        }
      }
    }

    // 重启Martin服务
    const restartMartinService = async () => {
      try {
        await ElMessageBox.confirm(
          '重启Martin服务会暂时中断瓦片服务访问，确认继续？',
          '确认重启',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        restartingMartin.value = true
        ElMessage.info('正在重启Martin服务，请稍候...')
        
        const response = await gisApi.restartMartinService()
        
        if (response.success || response.status === 'restarted') {
          ElMessage.success('Martin服务重启成功')
          // 刷新文件列表以更新服务状态
          fetchFileList()
        } else {
          ElMessage.error(response.message || 'Martin服务重启失败')
        }
      } catch (error) {
        if (error === 'cancel') return
        console.error('重启Martin服务失败', error)
        ElMessage.error(`重启Martin服务失败: ${error.response?.data?.error || error.message || '未知错误'}`)
      } finally {
        restartingMartin.value = false
      }
    }

    // 是否显示坐标系选择
    const showCoordinateSystem = computed(() => {
      return [ 'dxf', 'dom.tif', 'dem.tif'].includes(uploadForm.file_type)
    })

    // 坐标系搜索相关方法
    // 打开坐标系搜索对话框
    const openCoordinateSearch = () => {
      currentEditingFile.value = null // 清除当前编辑文件，表示这是上传表单的搜索
      coordinateSearchVisible.value = true
    }

    // 处理坐标系选择
    const handleCoordinateSelect = (selectedCoordinateSystem) => {
      if (currentEditingFile.value) {
        // 文件列表中的坐标系编辑
        currentEditingFile.value.temp_coordinate_system = selectedCoordinateSystem.epsg_code
        coordinateSearchVisible.value = false
        ElMessage.success(`已选择坐标系: ${selectedCoordinateSystem.display_name}`)
      } else {
        // 上传表单中的坐标系选择
        uploadForm.coordinate_system = selectedCoordinateSystem.epsg_code
        coordinateSearchVisible.value = false
        ElMessage.success(`已选择坐标系: ${selectedCoordinateSystem.display_name}`)
      }
    }

    // 判断文件是否需要坐标系
    const needsCoordinateSystem = (file) => {
      const fileType = file.file_type?.toLowerCase()
      const needs = ['shp','dxf', 'dom.tif', 'dem.tif', 'vector.mbtiles', 'raster.mbtiles'].includes(fileType)
      return needs
    }

    // 开始编辑坐标系
    const startEditCoordinate = (file) => {
      // 确保响应式属性存在
      if (!('editing_coordinate' in file)) {
        file.editing_coordinate = false
      }
      if (!('temp_coordinate_system' in file)) {
        file.temp_coordinate_system = ''
      }
      
      file.editing_coordinate = true
      file.temp_coordinate_system = file.coordinate_system || ''
    }

    // 取消编辑坐标系
    const cancelEditCoordinate = (file) => {
      file.editing_coordinate = false
      file.temp_coordinate_system = ''
    }

    // 保存坐标系
    const saveCoordinate = async (file) => {
      try {
        const newCoordinateSystem = file.temp_coordinate_system?.trim()
        
        // 验证坐标系格式
        if (newCoordinateSystem && !/^EPSG:\d+$/.test(newCoordinateSystem)) {
          ElMessage.error('坐标系格式错误，请输入如 EPSG:4326 的格式')
          return
        }

        // 调用API更新文件的坐标系
        await gisApi.updateFile(file.id, {
          coordinate_system: newCoordinateSystem
        })

        // 更新本地数据
        file.coordinate_system = newCoordinateSystem
        file.editing_coordinate = false
        file.temp_coordinate_system = ''

        ElMessage.success('坐标系更新成功')
      } catch (error) {
        console.error('更新坐标系失败', error)
        ElMessage.error('更新坐标系失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 为文件打开坐标系搜索
    const openCoordinateSearchForFile = (file) => {
      currentEditingFile.value = file
      coordinateSearchVisible.value = true
    }

    // 查看文件原始坐标系信息
    const viewCoordinateInfo = async (file) => {
      try {
        coordinateInfoLoading.value = true
        coordinateInfoData.value = null
        coordinateInfoVisible.value = true
        
        console.log('查看文件坐标系信息:', file.id)
        
        // 调用API获取坐标系信息
        const response = await gisApi.getFileCoordinateInfo(file.id)
        console.log('坐标系信息:', response)
        if (response.data.success) {
          coordinateInfoData.value = response.data.data
          console.log('坐标系信息:', response.data)
        } else {
          throw new Error(response.error || '获取坐标系信息失败')
        }
      } catch (error) {
        console.error('获取坐标系信息失败:', error)
        ElMessage.error('获取坐标系信息失败: ' + (error.response?.data?.error || error.message))
        coordinateInfoVisible.value = false
      } finally {
        coordinateInfoLoading.value = false
      }
    }

    // TIF转换对话框处理函数
    const handleTifConversionCompleted = (result) => {
      console.log('TIF转换完成:', result)
      ElMessage.success('TIF文件转换并发布Martin服务成功')
      fetchFileList() // 刷新文件列表
      tifConversionDialogVisible.value = false
      
      // 重置发布状态
      resetPublishingState()
    }

    const handleTifConversionError = (error) => {
      console.error('TIF转换失败:', error)
      ElMessage.error(`TIF文件转换失败: ${error}`)
      
      // 重置发布状态
      resetPublishingState()
    }

    const handleTifConversionRetry = () => {
      console.log('重试TIF转换')
      tifConversionDialogVisible.value = false
      
      // 重置发布状态
      resetPublishingState()
    }

    // 新增：对话框关闭处理函数
    const handleTifConversionDialogClose = () => {
      console.log('TIF转换对话框关闭')
      tifConversionDialogVisible.value = false
      
      // 重置发布状态
      resetPublishingState()
    }

    // 新增：重置发布状态的通用函数
    const resetPublishingState = () => {
      // 重置所有文件的发布状态
      fileList.value.forEach(file => {
        if (file.publishingMartin) {
          file.publishingMartin = false
        }
      })
    }

    return {
      fileList,
      uploaders,
      disciplines,
      fileTypes,
      total,
      currentPage,
      pageSize,
      uploadDialogVisible,
      uploading,
      restartingMartin,
      searchForm,
      uploadForm,
      rules,
      coordinateSearchVisible,
      uploadFormRef,
      uploadRef,
      showCoordinateSystem,
      handleFileUpload,
      handleRemove,
      handleFileChange,
      handleFileTypeChange,
      beforeUpload,
      submitUpload,
      showUploadDialog,
      fetchFileList,
      searchFiles,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      deleteFile,
      publishGeoServerService,
      publishMartinService,
      unpublishGeoServerService,
      unpublishMartinService,
      restartMartinService,
      formatFileSize,
      formatDate,
      getTagsList,
      canPublishGeoServer,
      canPublishMartin,
      truncateText,
      copyServiceUrl,
      openCoordinateSearch,
      handleCoordinateSelect,
      Search,
      ArrowDown,
      uploadProgress,
      uploadProgressText,
      uploadProgressStatus,
      uploadDetail,
      // 坐标系编辑相关
      needsCoordinateSystem,
      startEditCoordinate,
      cancelEditCoordinate,
      saveCoordinate,
      openCoordinateSearchForFile,
      currentEditingFile,
      // 坐标系信息查看相关
      viewCoordinateInfo,
      coordinateInfoVisible,
      coordinateInfoData,
      coordinateInfoLoading,
      // TIF转换对话框相关
      tifConversionDialogVisible,
      tifConversionTaskId,
      tifConversionFileInfo,
      tifConversionMinZoom,
      tifConversionMaxZoom,
      handleTifConversionCompleted,
      handleTifConversionError,
      handleTifConversionRetry,
      handleTifConversionDialogClose,
      resetPublishingState,
      // 移动端搜索相关
      mobileSearchExpanded,
      toggleMobileSearch,
      hasActiveFilters,
      getActiveFiltersText
    }
  }
}
</script>

<style scoped>
.upload-page {
  padding: 20px;
}

/* TIF转换进度加载样式 */
:deep(.tif-conversion-loading) {
  z-index: 9999 !important;
}

:deep(.tif-conversion-loading .el-loading-text) {
  color: #ffffff !important;
  font-size: 16px !important;
  line-height: 1.6 !important;
  white-space: pre-line !important;
  text-align: center !important;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5) !important;
}

:deep(.tif-conversion-loading .el-loading-spinner) {
  margin-top: -40px !important;
}

:deep(.tif-conversion-loading .el-loading-spinner .path) {
  stroke: #409EFF !important;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-area {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

/* 桌面端隐藏移动端搜索切换按钮 */
.mobile-search-toggle {
  display: none;
}

/* 桌面端隐藏移动端卡片 */
.mobile-file-cards {
  display: none;
}

.file-list {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  max-width: 100%;
  overflow: hidden;
}

.tag-item {
  margin-right: 2px;
  margin-bottom: 2px;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 文件描述列样式优化 */
.description-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: block;
}

.tag-tips {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
}

.no-preview {
  text-align: center;
  color: #909399;
}

.no-preview i {
  font-size: 48px;
  margin-bottom: 10px;
}

.service-publish {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 60px;
}

.service-column {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 60px;
  width: 100%;
}

.published-service {
  width: 100%;
}

.service-status {
  margin-bottom: 8px;
}

.service-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.unpublished-service {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
}

.status-info {
  margin-bottom: 8px;
}

.publish-tip {
  color: #909399;
  font-size: 12px;
  display: flex;
  align-items: center;
}

.tip-text {
  margin-left: 5px;
}

.service-btn {
  margin-right: 4px;
  font-weight: 500;
}

.unpublish-btn {
  color: #f56c6c;
  font-size: 12px;
}

.file-name-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 5px;
  width: 100%;
}

.file-name-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.discipline-tag {
  flex-shrink: 0;
  margin-left: 5px;
  font-size: 10px !important;
  padding: 1px 4px !important;
  height: 16px !important;
  line-height: 14px !important;
  border-radius: 2px !important;
  transform: scale(0.9);
  transform-origin: center;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.restart-btn {
  margin-left: 5px;
}

.tags-and-type-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 100%;
  overflow: hidden;
}

.file-type-tag {
  align-self: flex-start;
  font-weight: 500;
  border-radius: 3px;
  font-size: 10px !important;
  padding: 1px 4px !important;
  height: 16px !important;
  line-height: 14px !important;
  text-transform: uppercase;
}

.tags-section {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  max-width: 100%;
  overflow: hidden;
}

.tags-section .tag-item {
  font-size: 10px !important;
  padding: 1px 3px !important;
  height: 15px !important;
  line-height: 13px !important;
  transform: scale(0.9);
  transform-origin: left center;
}

.coordinate-system-input {
  display: flex;
  align-items: center;
  gap: 5px;
}

.coordinate-select {
  width: 200px;
}

.search-button {
  margin-top: 5px;
}

.upload-progress {
  margin-top: 10px;
  margin-bottom: 10px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-text {
  font-weight: 500;
  color: #409eff;
}

.progress-percentage {
  font-weight: 600;
  color: #409eff;
}

.progress-detail {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
  text-align: center;
}

/* 坐标系编辑相关样式 */
.coordinate-system-cell {
  min-height: 32px;
  display: flex;
  align-items: center;
}

.coordinate-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.coordinate-display:hover {
  background-color: #f8f9fa;
}

.coordinate-text {
  flex: 1;
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.coordinate-text.not-set {
  color: #f56c6c;
  font-style: italic;
}

.coordinate-edit {
  display: flex;
  flex-direction: column;
  gap: 1px;
  width: 100%;
  padding: 1px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.coordinate-edit-row {
  display: flex;
  align-items: center;
  width: 100%;
}

.coordinate-edit-buttons {
  display: flex;
  align-items: center;
  gap: 0px;
  justify-content: flex-start;
}

.search-coordinate-btn {
  margin-right: 0px;
  font-weight: 500;
  color: #67c23a !important;
  background-color: #f0f9ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  
}

.search-coordinate-btn:hover {
  background-color: #e1f3d8;
  transform: scale(1.05);
}

.save-coordinate-btn {
  margin-right: 0px;
  font-weight: 500;
  color: #409eff !important;
  background-color: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  
}

.save-coordinate-btn:hover {
  background-color: #d9ecff;
  transform: scale(1.05);
}

.view-coordinate-btn {
  margin-right: 0px;
  font-weight: 500;
  color: #606266 !important;
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  
}

.view-coordinate-btn:hover {
  background-color: #e4e7ed;
  transform: scale(1.05);
}

.cancel-coordinate-btn {
  color: #f56c6c !important;
  font-size: 12px;
  background-color: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  
}

.cancel-coordinate-btn:hover {
  background-color: #fde2e2;
  transform: scale(1.05);
}

.coordinate-not-applicable {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
}

.not-applicable-text {
  font-size: 12px;
  color: #c0c4cc;
  font-style: italic;
}

/* 移动端特定样式 */
.mobile-file-card {
  margin-bottom: 10px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 8px 0 rgba(0, 0, 0, 0.08);
}

.mobile-file-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.mobile-file-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-file-actions {
  display: flex;
  gap: 6px;
}

.mobile-file-info {
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mobile-info-row {
  display: flex;
  gap: 12px;
}

.mobile-info-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.mobile-info-label {
  font-size: 12px;
  color: #606266;
  min-width: 40px;
  font-weight: 500;
}

.mobile-info-value {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-coordinate-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mobile-coordinate-container {
  flex: 1;
  min-width: 0;
}

.mobile-service-section {
  padding: 8px 12px;
  border-top: 1px solid #ebeef5;
}

.mobile-service-header {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.mobile-service-grid {
  display: flex;
  gap: 8px;
}

.mobile-service-item {
  flex: 1;
  min-width: 0;
}

.mobile-service-name {
  font-size: 11px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 4px;
}

.mobile-service-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobile-service-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.mobile-coordinate-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 4px 6px;
  border-radius: 3px;
  transition: background-color 0.3s ease;
}

.mobile-coordinate-display:hover {
  background-color: #f8f9fa;
}

.mobile-coordinate-text {
  flex: 1;
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.mobile-coordinate-text.not-set {
  color: #f56c6c;
  font-style: italic;
}

.mobile-coordinate-edit {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  padding: 3px;
  background-color: #f8f9fa;
  border-radius: 3px;
  border: 1px solid #e9ecef;
}

.mobile-coordinate-edit-row {
  display: flex;
  align-items: center;
  width: 100%;
}

.mobile-coordinate-edit .el-input {
  width: 100% !important;
}

.mobile-coordinate-edit-buttons {
  display: flex;
  gap: 0px;
  justify-content: flex-start;
}

.mobile-edit-coordinate-btn {
  font-weight: 500;
  color: #ffffff !important;
  background-color: #409eff !important;
  border: 1px solid #409eff;
  border-radius: 50% !important;
  padding: 0 !important;
  font-size: 9px;
  min-width: 18px !important;
  width: 18px !important;
  height: 18px !important;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-edit-coordinate-btn:hover {
  background-color: #337ecc !important;
  border-color: #337ecc;
  transform: scale(1.1);
  box-shadow: 0 1px 6px rgba(64, 158, 255, 0.3);
}

.mobile-edit-coordinate-btn .el-icon-edit {
  font-size: 9px;
  margin: 0;
}

.mobile-search-coordinate-btn,
.mobile-save-coordinate-btn,
.mobile-cancel-coordinate-btn {
  font-weight: 500;
  border-radius: 3px;
  padding: 2px 4px;
  font-size: 10px;
  min-width: 16px !important;
  width: 16px !important;
  height: 16px !important;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 2px;
}

.mobile-search-coordinate-btn:last-child,
.mobile-save-coordinate-btn:last-child,
.mobile-cancel-coordinate-btn:last-child {
  margin-right: 0;
}

.mobile-search-coordinate-btn {
  color: #67c23a !important;
  background-color: #f0f9ff;
  border: 1px solid #d9ecff;
}

.mobile-search-coordinate-btn:hover {
  background-color: #e1f3d8;
}

.mobile-save-coordinate-btn {
  color: #409eff !important;
  background-color: #ecf5ff;
  border: 1px solid #b3d8ff;
}

.mobile-save-coordinate-btn:hover {
  background-color: #d9ecff;
}

.mobile-cancel-coordinate-btn {
  color: #f56c6c !important;
  background-color: #fef0f0;
  border: 1px solid #fbc4c4;
}

.mobile-cancel-coordinate-btn:hover {
  background-color: #fde2e2;
}

/* 移动端不适用文本样式 */
.mobile-not-applicable-text {
  font-size: 12px;
  color: #c0c4cc;
  font-style: italic;
}

/* 坐标系信息对话框样式 */
.coordinate-info-dialog {
  min-height: 200px;
}

.coordinate-info-content {
  font-size: 14px;
}

.info-section {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
}

.info-section h4 {
  margin: 0 0 12px 0;
  color: #409eff;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.info-item label {
  font-weight: 600;
  color: #606266;
  font-size: 13px;
}

.info-item span {
  color: #303133;
  word-break: break-all;
}

.wkt-section {
  margin-top: 16px;
}

.wkt-textarea :deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background-color: #f8f9fa;
}

.proj4-input :deep(.el-input__inner) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background-color: #f8f9fa;
}

.extent-info {
  background-color: #f0f9ff;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #bfdbfe;
}

.bounds-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.bounds-grid div {
  padding: 4px 8px;
  background-color: white;
  border-radius: 3px;
  border: 1px solid #e0e7ff;
}

.tile-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.tile-info-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  background-color: #f0f9ff;
  border-radius: 4px;
  font-size: 12px;
}

.tile-info-item label {
  font-weight: 600;
  color: #374151;
}

.error-message {
  margin: 16px 0;
}

.loading-message {
  text-align: center;
  padding: 40px;
  color: #606266;
  font-size: 14px;
}

.coordinate-details {
  max-height: 500px;
  overflow-y: auto;
}

/* Shapefile特殊信息样式 */
.shp-specific-info {
  background-color: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.zip-contents {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.file-tag {
  font-family: 'Courier New', monospace;
  font-size: 11px;
}

.prj-textarea :deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  background-color: #f8f9fa;
  border: 1px solid #bfdbfe;
  color: #2563eb;
}

.comparison-result {
  margin-top: 8px;
}

/* 边界分析和坐标系建议样式 */
.extent-analysis {
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.bounds-info {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.bound-item {
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.bound-item span {
  color: #606266;
  font-weight: 500;
}

.bound-item code {
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  color: #495057;
}

.analysis-notes {
  background-color: #e3f2fd;
  padding: 12px;
  border-radius: 6px;
  border-left: 4px solid #2196f3;
}

.note-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #1565c0;
}

.note-item:last-child {
  margin-bottom: 0;
}

.note-item i {
  color: #2196f3;
  margin-top: 2px;
}

.suggested-crs {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.crs-suggestion {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-radius: 6px;
  border: 1px solid #bfdbfe;
}

.crs-name {
  font-weight: 600;
  color: #1e40af;
}

.crs-reason {
  font-size: 12px;
  color: #6b7280;
  font-style: italic;
}

.coordinate-suggestions {
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
  background-color: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e1e5e9;
}

.suggestion-category {
  margin-bottom: 20px;
}

.suggestion-category:last-child {
  margin-bottom: 0;
}

.suggestion-category h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #374151;
  font-weight: 600;
  border-bottom: 1px solid #d1d5db;
  padding-bottom: 6px;
}

.crs-item {
  margin-bottom: 12px;
  padding: 12px;
  background-color: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.crs-item:last-child {
  margin-bottom: 0;
}

.crs-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.crs-title {
  font-weight: 600;
  color: #1f2937;
  font-size: 13px;
}

.crs-description {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.4;
}

.crs-use-cases {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.use-case-label {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
}

.detection-tips {
  background-color: #fffbeb;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #fbbf24;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #92400e;
  line-height: 1.4;
}

.tip-item:last-child {
  margin-bottom: 0;
}

.tip-item i {
  color: #f59e0b;
  margin-top: 1px;
}

/* 移动端响应式样式 */
@media (max-width: 768px) {
  /* 移动端标签样式调整 */
  .mobile-info-value .el-tag {
    font-size: 10px !important;
    padding: 1px 4px !important;
    height: 16px !important;
    line-height: 14px !important;
    transform: scale(0.9);
  }

  .mobile-service-content .el-tag {
    font-size: 10px !important;
    padding: 1px 4px !important;
    height: 16px !important;
    line-height: 14px !important;
    transform: scale(0.9);
  }

  /* 移动端按钮样式调整 */
  .mobile-file-actions .el-button,
  .mobile-service-actions .el-button {
    font-size: 11px !important;
    padding: 4px 8px !important;
    height: 24px !important;
    line-height: 16px !important;
  }
  /* 移动端显示搜索切换按钮 */
  .mobile-search-toggle {
    display: flex !important;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background-color: #ffffff;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    margin-bottom: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .mobile-search-toggle:hover {
    background-color: #f8f9fa;
    border-color: #409eff;
  }

  .mobile-search-toggle .toggle-icon {
    font-size: 16px;
    color: #409eff;
    transition: transform 0.3s ease;
  }

  .mobile-search-toggle .toggle-icon.rotated {
    transform: rotate(180deg);
  }

  .mobile-search-toggle .toggle-text {
    font-size: 15px;
    font-weight: 500;
    color: #303133;
    margin-left: 8px;
  }

  .mobile-search-toggle .search-summary {
    margin-left: auto;
  }

  /* 移动端显示卡片布局 */
  .mobile-file-cards {
    display: block !important;
  }

  /* 移动端隐藏桌面端表格 */
  .el-table {
    display: none !important;
  }

  /* 移动端搜索表单折叠样式 */
  .search-form-container {
    overflow: hidden;
    transition: max-height 0.3s ease;
  }

  .search-form-container.mobile-collapsed {
    max-height: 0;
    opacity: 0;
    visibility: hidden;
  }

  /* 移动端搜索表单样式调整 */
  .search-form .el-form-item {
    width: 100%;
    margin-bottom: 12px;
  }

  .search-form .el-form-item .el-select,
  .search-form .el-form-item .el-input {
    width: 100% !important;
  }

  /* 移动端页面头部样式调整 */
  .page-header {
    padding: 16px 0;
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .page-header h1 {
    margin: 0;
    font-size: 22px;
    text-align: center;
  }

  .page-header .el-button {
    width: 100%;
  }

  /* 移动端搜索区域样式调整 */
  .search-area {
    padding: 16px;
    margin-bottom: 16px;
  }

  /* 移动端分页样式调整 */
  .pagination {
    flex-direction: column;
    gap: 12px;
  }

  .pagination .el-pagination {
    justify-content: center;
  }

  /* 移动端坐标系编辑样式调整 */
  .mobile-coordinate-edit {
    flex-direction: column;
    gap: 6px;
    padding: 6px;
  }

  .mobile-coordinate-edit .el-input {
    width: 100% !important;
  }

  .mobile-coordinate-edit-buttons {
    justify-content: flex-end;
    
  }

  .coordinate-icon {
    width: 8px;
    height: 12px;
  }
}

/* 超小屏幕适配 */
@media (max-width: 480px) {
  .upload-page {
    padding: 8px;
  }

  .mobile-file-card {
    margin-bottom: 8px;
  }

  .mobile-file-card-header {
    padding: 6px 10px;
  }

  .mobile-file-name {
    font-size: 13px;
  }

  .mobile-file-info {
    padding: 6px 10px;
  }

  .mobile-service-section {
    padding: 6px 10px;
  }

  .mobile-service-header {
    font-size: 12px;
  }

  .mobile-service-name {
    font-size: 10px;
  }

  .mobile-info-label {
    font-size: 11px;
    min-width: 35px;
  }

  .mobile-info-value {
    font-size: 12px;
  }

  .mobile-coordinate-edit-buttons .el-button {
    padding: 1px 1px;
    font-size: 11px;
  }

  .mobile-service-grid {
    gap: 6px;
  }

  .mobile-service-actions {
    gap: 3px;
  }

  .mobile-file-actions .el-button,
  .mobile-service-actions .el-button {
    font-size: 10px !important;
    padding: 3px 6px !important;
    height: 20px !important;
    line-height: 14px !important;
  }

  .mobile-info-value .el-tag,
  .mobile-service-content .el-tag {
    font-size: 9px !important;
    padding: 1px 3px !important;
    height: 14px !important;
    line-height: 12px !important;
    transform: scale(0.85);
  }
}

/* SVG图标样式 */
.coordinate-icon {
  width: 14px;
  height: 14px;
  display: inline-block;
  vertical-align: middle;
}

.search-coordinate-btn .coordinate-icon {
  color: #67c23a;
}

.save-coordinate-btn .coordinate-icon {
  color: #409eff;
}

.cancel-coordinate-btn .coordinate-icon {
  color: #909399;
}

/* 按钮悬停效果 */
.search-coordinate-btn:hover .coordinate-icon {
  color: #85ce61;
}

.save-coordinate-btn:hover .coordinate-icon {
  color: #66b1ff;
}

.cancel-coordinate-btn:hover .coordinate-icon {
  color: #a6a9ad;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .coordinate-icon {
    width: 12px;
    height: 12px;
  }
}

.not-applicable-text {
  font-size: 12px;
  color: #c0c4cc;
  font-style: italic;
}

.edit-coordinate-btn {
  margin-left: 8px;
  font-weight: 500;
  color: #ffffff !important;
  background-color: #409eff !important;
  border: 1px solid #409eff;
  border-radius: 50% !important;
  padding: 0 !important;
  font-size: 10px;
  min-width: 20px !important;
  width: 20px !important;
  height: 20px !important;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-coordinate-btn:hover {
  background-color: #337ecc !important;
  border-color: #337ecc;
  transform: scale(1.2);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.edit-coordinate-btn .el-icon-edit {
  font-size: 10px;
  margin: 0;
}
</style>