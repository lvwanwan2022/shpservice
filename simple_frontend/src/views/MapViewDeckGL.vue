<template>
  <div class="map-view">
    <!-- 主要内容区域 -->
    <div class="map-content">
      <!-- 左侧图层面板 - 桌面端显示 -->
      <div class="layer-panel desktop-only" :class="{ 'collapsed': layerPanelCollapsed }">
        <div class="panel-content" v-show="!layerPanelCollapsed">
          <div class="panel-header">
            <h3>图层管理</h3>
            <div class="header-right">
              <span class="layer-count">{{ (layersList || []).length }} 个图层</span>
              <el-button type="primary" size="small" @click="showAddLayerDialog">
                <i class="el-icon-plus"></i> 添加图层
              </el-button>
              <!-- 面板切换按钮 -->
              <el-button 
                link 
                size="small" 
                @click="toggleLayerPanel"
                class="panel-toggle-btn"
                :title="layerPanelCollapsed ? '展开面板' : '收起面板'"
              >
                <span class="toggle-icon">{{ layerPanelCollapsed ? '》' : '《' }}</span>
              </el-button>
            </div>
          </div>
          
          <!-- 场景选择 -->
          <div class="scene-selector">
            <el-select 
              v-model="selectedSceneId" 
              placeholder="选择场景" 
              @change="onSceneChange"
              style="width: 100%"
              size="small"
            >
              <el-option
                v-for="scene in sceneList"
                :key="scene.id"
                :label="scene.name"
                :value="scene.id"
              />
            </el-select>
          </div>
          
          <div class="panel-body">
            <!-- 图层卡片列表 -->
            <div class="layer-cards" v-if="layersList && layersList.length > 0">
              <div 
                v-for="layer in sortedLayersList" 
                :key="layer.scene_layer_id || layer.id" 
                class="layer-card"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                  'invisible': !layer.visibility
                }"
                @click="selectLayer(layer)"
              >
                <div class="layer-card-header" :class="{ 'invisible': !layer.visibility }">
                  <div class="layer-title">
                    <!-- 可见性控制checkbox -->
                    <el-checkbox 
                      v-model="layer.visibility" 
                      @change="toggleLayerVisibility(layer)"
                      @click.stop
                    ></el-checkbox>
                    <!-- 当前活动图层标识 -->
                    <i v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" 
                       class="el-icon-location active-indicator" 
                       title="当前活动图层"></i>
                    <div class="layer-name-wrapper">
                      <span class="layer-name" :title="layer.layer_name || layer.name || '未命名图层'">
                        {{ layer.layer_name || layer.name || '未命名图层' }}
                      </span>
                    </div>
                  </div>
                  <div class="layer-actions">
                    <!-- 缩放到图层范围 -->
                    <el-button 
                      link 
                      @click.stop="zoomToLayer(layer)"
                      class="zoom-btn"
                      title="缩放到图层范围"
                    >
                      <span>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <path d="M15.5 14h-.79l-.28-.27A6.5 6.5 0 1 0 13 15.5l.27.28v.79l5 4.99L19.49 20l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/>
                          <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
                        </svg>
                      </span>
                    </el-button>

                    <!-- 设置按钮 -->
                    <el-button 
                      link 
                      @click.stop="toggleLayerSettings(layer)"
                      class="settings-btn"
                      title="图层设置"
                    >
                      <span>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
                        </svg>
                      </span>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">🗺️</div>
              <div class="empty-text">暂无图层</div>
              <div class="empty-description">点击"添加图层"开始使用</div>
            </div>
          </div>
        </div>
        
        <!-- 收起状态下的内容 -->
        <div class="collapsed-content" v-show="layerPanelCollapsed">
          <!-- 展开按钮 -->
          <div class="collapsed-toggle" @click="toggleLayerPanel">
            <el-button 
              link 
              size="small"
              class="expand-btn"
              title="展开面板"
            >
            <span class="toggle-icon">》</span>
            </el-button>
          </div>
          
          <!-- 收起状态下的场景选择样式 -->
          <div class="collapsed-scene-selector" v-if="sceneList && sceneList.length > 0">
            <!-- 场景区域标题 -->
             
            <div class="collapsed-section-title">场景</div>
            <div 
              v-for="scene in sceneList" 
              :key="scene.id" 
              class="collapsed-scene-item"
              :class="{ 'active': selectedSceneId === scene.id }"
              @click="onSceneChange(scene.id)"
              :title="`场景: ${scene.name}
👆 点击切换到此场景`"
            >
              <div class="scene-short-name">{{ scene.name.substring(0, 2) }}</div>
              <div v-if="selectedSceneId === scene.id" class="scene-active-dot"></div>
            </div>
          </div>
          
          <!-- 分隔线 -->
          <div class="collapsed-separator" v-if="sceneList && sceneList.length > 0 && layersList && layersList.length > 0"></div>
          
          <!-- 收起状态下的图层列表 -->
          <div class="collapsed-layers" v-if="layersList && layersList.length > 0">
            <!-- 图层区域标题 -->
            <div class="collapsed-section-title">图层</div>
            <div 
              v-for="(layer) in sortedLayersList" 
              :key="layer.scene_layer_id || layer.id" 
              class="collapsed-layer-item"
              :class="{ 
                'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                'invisible': !layer.visibility
              }"
              @click="selectLayer(layer)"
              :title="`图层: ${layer.layer_name || layer.name || '未命名图层'}
类型: ${getLayerTypeText(layer)}
👆 点击选中此图层
🔄 双击缩放到图层范围`"
              @dblclick="zoomToLayer(layer)"
            >
              <div class="layer-short-name">{{ (layer.layer_name || layer.name || '未命名').substring(0, 2) }}</div>
              <div v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" class="layer-active-dot"></div>
              <div v-if="!layer.visibility" class="layer-invisible-dot"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 地图区域 -->
      <div class="map-container-wrapper" :class="{ 'with-panel': !layerPanelCollapsed }">
        <MapViewerDeckGL
          ref="mapViewer"
          :layers="layersList"
          :layers-cache-enabled="layersCacheEnabled"
          @map-ready="onMapReady"
          @layer-click="onLayerClick"
          @layers-cache-toggle="toggleLayersCache"
        />
        
        <!-- 🔥 手机端底部浮动按钮 -->
        <div class="mobile-layer-fab" @click="toggleMobileDrawer">
          <div class="fab-content">
            <i class="el-icon-menu"></i>
            <span class="fab-text">图层</span>
            <div class="fab-badge" v-if="layersList && layersList.length > 0">
              {{ layersList.length }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 🔥 手机端抽屉式图层面板 -->
    <div class="mobile-drawer-overlay mobile-only" :class="{ 'show': mobileDrawerVisible }" @click="closeMobileDrawer">
      <div class="mobile-drawer" :class="{ 'show': mobileDrawerVisible }" @click.stop>
        <!-- 抽屉头部 -->
        <div class="mobile-drawer-header">
          <div class="drawer-handle"></div>
          <div class="drawer-title">
            <h3>图层管理</h3>
            <div class="drawer-actions">
              <el-button type="primary" size="small" @click="showAddLayerDialog">
                <i class="el-icon-plus"></i>
                <span>添加图层</span>
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 抽屉内容 -->
        <div class="mobile-drawer-content">
          <!-- 场景选择标签页 -->
          <div class="mobile-tabs">
            <div 
              class="mobile-tab" 
              :class="{ 'active': mobileActiveTab === 'scene' }"
              @click="mobileActiveTab = 'scene'"
            >
              <i class="el-icon-folder"></i>
              <span>场景</span>
            </div>
            <div 
              class="mobile-tab" 
              :class="{ 'active': mobileActiveTab === 'layers' }"
              @click="mobileActiveTab = 'layers'"
            >
              <i class="el-icon-menu"></i>
              <span>图层</span>
              <div class="tab-badge" v-if="layersList && layersList.length > 0">
                {{ layersList.length }}
              </div>
            </div>
          </div>
          
          <!-- 场景选择内容 -->
          <div class="mobile-tab-content" v-show="mobileActiveTab === 'scene'">
            <div class="mobile-scene-list">
              <div 
                v-for="scene in sceneList" 
                :key="scene.id"
                class="mobile-scene-item"
                :class="{ 'active': selectedSceneId === scene.id }"
                @click="selectMobileScene(scene.id)"
              >
                <div class="scene-info">
                  <h4>{{ scene.name }}</h4>
                  <p>{{ scene.description || '暂无描述' }}</p>
                </div>
                <div class="scene-meta">
                  <el-tag v-if="scene.is_public" type="success" size="small">公开</el-tag>
                  <el-tag v-else type="warning" size="small">私有</el-tag>
                </div>
              </div>
              
              <!-- 场景空状态 -->
              <div v-if="!sceneList || sceneList.length === 0" class="mobile-empty">
                <i class="el-icon-folder"></i>
                <p>暂无场景</p>
              </div>
            </div>
          </div>
          
          <!-- 图层列表内容 -->
          <div class="mobile-tab-content" v-show="mobileActiveTab === 'layers'">
            <div class="mobile-layer-list">
              <div 
                v-for="layer in sortedLayersList" 
                :key="layer.scene_layer_id || layer.id"
                class="mobile-layer-item"
                :class="{ 
                  'active': currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id,
                  'invisible': !layer.visibility
                }"
                @click="selectLayer(layer)"
              >
                <div class="layer-main-info">
                  <div class="layer-header">
                    <el-checkbox 
                      v-model="layer.visibility" 
                      @change="toggleLayerVisibility(layer)"
                      @click.stop
                    />
                    <div class="layer-name-container">
                      <span class="layer-name" :title="layer.layer_name">{{ layer.layer_name }}</span>
                      <i v-if="currentActiveLayer && currentActiveLayer.scene_layer_id === layer.scene_layer_id" 
                         class="el-icon-location active-indicator"></i>
                    </div>
                  </div>
                  
                  <div class="layer-tags">
                    <span class="tag">{{ layer.file_type }}</span>
                    <span class="tag">{{ layer.discipline }}</span>
                    <span v-if="layer.service_type" class="tag" :class="getServiceTypeClass(layer.service_type)">
                      {{ getServiceTypeText(layer) }}
                    </span>
                  </div>
                  
                  <!-- 移动端透明度控制 -->
                  <div class="mobile-opacity-control" @click.stop>
                    <span class="opacity-label">透明度</span>
                    <el-slider
                      v-model="layer.opacity"
                      :min="0"
                      :max="1"
                      :step="0.1"
                      :show-tooltip="false"
                      size="small"
                      @input="updateLayerOpacityInMap(layer)"
                      @change="updateLayerOpacityInDatabase(layer)"
                      class="mobile-opacity-slider"
                    />
                    <span class="opacity-value">{{ Math.round((layer.opacity || 1) * 100) }}%</span>
                  </div>
                </div>
                
                <div class="layer-actions">
                  <el-button size="small" @click.stop="zoomToLayer(layer)" title="缩放到图层" class="action-btn zoom-btn">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M15.5 14h-.79l-.28-.27A6.5 6.5 0 1 0 13 15.5l.27.28v.79l5 4.99L19.49 20l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/>
                      <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
                    </svg>
                  </el-button>
                  <el-button size="small" @click.stop="showStyleDialog(layer)" title="样式设置" class="action-btn style-btn">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
                    </svg>
                  </el-button>
                  <el-button size="small" @click.stop="removeLayer(layer)" title="删除图层" class="action-btn delete-btn">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z"/>
                    </svg>
                  </el-button>
                </div>
              </div>
              
              <!-- 图层空状态 -->
              <div v-if="!layersList || layersList.length === 0" class="mobile-empty">
                <i class="el-icon-map-location"></i>
                <p>当前场景暂无图层</p>
                <el-button type="primary" @click="showAddLayerDialog">添加图层</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加图层对话框 -->
    <el-dialog title="添加图层" v-model="addLayerDialogVisible" :width="isMobile ? '95%' : '800px'" :fullscreen="isMobile">
      <div class="add-layer-dialog-content">
        <!-- 搜索和筛选 -->
        <div class="layer-search-section">
          <el-form :inline="!isMobile" :model="layerSearchForm">
            <el-form-item label="服务类型">
              <el-select v-model="layerSearchForm.service_type" placeholder="全部" clearable>
                <el-option label="全部" value="" />
                <el-option label="GeoServer" value="geoserver" />
                <el-option label="Martin" value="martin" />
              </el-select>
            </el-form-item>
            <el-form-item label="数据类型">
              <el-select v-model="layerSearchForm.file_type" placeholder="全部" clearable>
                <el-option label="全部" value="" />
                <el-option label="Shapefile" value="shp" />
                <el-option label="GeoTIFF" value="tif" />
                <el-option label="DXF" value="dxf" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchLayers">搜索</el-button>
              <el-button @click="resetSearch">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 可用图层列表 -->
        <div class="available-layers" v-loading="loadingLayers">
          <div 
            v-for="layer in availableLayers" 
            :key="layer.id"
            class="available-layer-item"
            :class="{ 'selected': selectedLayers.includes(layer.id) }"
          >
            <div class="layer-preview">
              <div class="preview-placeholder">
                {{ getLayerIcon(layer) }}
              </div>
            </div>
            <div class="layer-details">
              <div class="layer-name">{{ layer.layer_name || layer.file_name || layer.original_name || '未命名图层' }}</div>
              <div class="layer-description">{{ layer.description || getLayerTypeText(layer) }}</div>
              <div class="layer-meta">
                <span class="meta-item">{{ layer.file_type?.toUpperCase() }}</span>
                <span class="meta-item">专业: {{ layer.discipline || '未知' }}</span>
              </div>
              
              <!-- 服务状态和操作按钮 -->
              <div class="layer-services">
                <!-- GeoServer服务 -->
                <div v-if="layer.geoserver_service?.is_published" class="service-item">
                  <el-tag type="success" size="small">GeoServer已发布</el-tag>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="addLayerToScene(layer, 'geoserver')"
                    :disabled="isLayerInScene(layer.id, 'geoserver')"
                  >
                    {{ isLayerInScene(layer.id, 'geoserver') ? '已添加' : '添加GeoServer' }}
                  </el-button>
                </div>
                
                <!-- Martin服务 -->
                <div v-if="layer.martin_service?.is_published" class="service-item">
                  <el-tag type="primary" size="small">Martin已发布</el-tag>
                  <el-button 
                    size="small" 
                    type="success" 
                    @click="addLayerToScene(layer, 'martin')"
                    :disabled="isLayerInScene(layer.id, 'martin')"
                  >
                    {{ isLayerInScene(layer.id, 'martin') ? '已添加' : '添加Martin' }}
                  </el-button>
                </div>
                
                <!-- 未发布状态 -->
                <div v-if="!hasAnyPublishedService(layer)" class="service-item">
                  <el-tag type="warning" size="small">服务未发布</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="totalLayers > 0">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalLayers"
            layout="prev, pager, next, total"
            @current-change="handlePageChange"
          />
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addLayerDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="addSelectedLayers"
            :disabled="selectedLayers.length === 0"
          >
            添加选中图层 ({{ selectedLayers.length }})
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 🔥 图层样式设置对话框 -->
    <el-dialog title="图层样式设置" v-model="styleDialogVisible" width="800px" :close-on-click-modal="false">
      <div class="style-dialog-content" v-if="styleDialogVisible && currentStyleLayer && activeStyleTab">
        <el-tabs v-model="activeStyleTab" :key="`style-tabs-${currentStyleLayer.id || 'unknown'}-${activeStyleTab}`">
          <el-tab-pane label="基础样式" name="basic">
            
            
            <el-form :model="styleForm" label-width="100px">
              <template v-if="isVectorLayer">
                <template v-if="hasPointGeometry">
                  <h4>点样式</h4>
                  <el-form-item label="大小">
                    <el-slider v-model="styleForm.point.size" :min="1" :max="15" :step="1"></el-slider>
                  </el-form-item>
                  <el-form-item label="颜色">
                    <el-color-picker v-model="styleForm.point.color"></el-color-picker>
                  </el-form-item>
                </template>
                
                <template v-if="hasLineGeometry">
                  <h4>线样式</h4>
                  <el-form-item label="线宽">
                    <el-slider v-model="styleForm.line.width" :min="1" :max="8" :step="1"></el-slider>
                  </el-form-item>
                  <el-form-item label="颜色">
                    <el-color-picker v-model="styleForm.line.color"></el-color-picker>
                  </el-form-item>
                </template>
                
                <template v-if="hasPolygonGeometry">
                  <h4>面样式</h4>
                  <el-form-item label="填充颜色">
                    <el-color-picker v-model="styleForm.polygon.fillColor"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="填充透明度">
                    <el-slider v-model="styleForm.polygon.fillOpacity" :min="0" :max="1" :step="0.1"></el-slider>
                  </el-form-item>
                  <el-form-item label="边框颜色">
                    <el-color-picker v-model="styleForm.polygon.outlineColor"></el-color-picker>
                  </el-form-item>
                </template>
                
                <!-- 如果没有检测到具体的几何类型，显示通用样式设置 -->
                <template v-if="!hasPointGeometry && !hasLineGeometry && !hasPolygonGeometry">
                  <h4>通用样式</h4>
                  <el-form-item label="点大小">
                    <el-slider v-model="styleForm.point.size" :min="1" :max="15" :step="1"></el-slider>
                  </el-form-item>
                  <el-form-item label="点颜色">
                    <el-color-picker v-model="styleForm.point.color"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="线宽">
                    <el-slider v-model="styleForm.line.width" :min="1" :max="8" :step="1"></el-slider>
                  </el-form-item>
                  <el-form-item label="线颜色">
                    <el-color-picker v-model="styleForm.line.color"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="填充颜色">
                    <el-color-picker v-model="styleForm.polygon.fillColor"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="填充透明度">
                    <el-slider v-model="styleForm.polygon.fillOpacity" :min="0" :max="1" :step="0.1"></el-slider>
                  </el-form-item>
                  <el-form-item label="边框颜色">
                    <el-color-picker v-model="styleForm.polygon.outlineColor"></el-color-picker>
                  </el-form-item>
                </template>
              </template>
              
              <template v-else>
                <h4>栅格样式</h4>
                <el-form-item label="透明度">
                  <el-slider v-model="styleForm.raster.opacity" :min="0" :max="1" :step="0.1"></el-slider>
                </el-form-item>
              </template>
            </el-form>
          </el-tab-pane>

          <el-tab-pane v-if="isDxfMartinLayer === true" label="Martin(DXF)" name="dxf">
            <div v-if="currentStyleLayer && currentStyleLayer.martin_service_id">
              <DxfStyleEditor 
                :key="`dxf-editor-${currentStyleLayer.martin_service_id}`"
                :layer-data="currentStyleLayer" 
                :martin-service-id="currentStyleLayer.martin_service_id"
                @styles-updated="onDxfStylesUpdated"
                @popup-control-changed="onPopupControlChanged"
                ref="dxfStyleEditorRef"
              />
            </div>
            <div v-else class="loading-placeholder">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在加载样式编辑器...</span>
              <div style="margin-top: 10px; font-size: 12px; color: #999;">
                调试信息: martin_service_id = {{ currentStyleLayer?.martin_service_id }} ({{ typeof currentStyleLayer?.martin_service_id }})
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="!isMartinLayer" label="SLD样式" name="sld">
            <div v-if="currentStyleLayer">
              <SldStyleSelector 
                :key="`sld-selector-${currentStyleLayer.id}`"
                :layer-id="currentStyleLayer.id"
                :layer-geometry-type="getLayerGeometryType(currentStyleLayer)"
                @style-applied="onSldStyleApplied"
                @style-removed="onSldStyleRemoved"
                ref="sldStyleSelectorRef"
              />
            </div>
            <div v-else class="loading-placeholder">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在加载SLD样式选择器...</span>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div v-else class="dialog-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在初始化对话框...</span>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="styleDialogVisible = false">取消</el-button>
          <el-button v-if="activeStyleTab === 'basic'" type="primary" @click="applyStyle">应用样式</el-button>
          <el-button v-if="activeStyleTab === 'dxf' && isDxfMartinLayer === true" type="primary" @click="applyAndSaveDxfStyles" :loading="savingDxfStyles">保存样式到数据库</el-button>
          <el-button v-if="activeStyleTab === 'sld' && !isMartinLayer" type="primary" @click="refreshMapLayers">刷新地图</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 🔥 图层设置对话框 -->
    <el-dialog 
      :title="currentSettingsLayer ? `图层设置 - ${currentSettingsLayer.layer_name || currentSettingsLayer.name || '未命名图层'}` : '图层设置'" 
      v-model="layerSettingsDialogVisible" 
      width="600px" 
      :close-on-click-modal="false"
      @close="closeLayerSettingsDialog"
    >
      <div class="layer-settings-dialog-content" v-if="layerSettingsDialogVisible && currentSettingsLayer">
        <!-- 图层信息标签 -->
        <div class="settings-section">
          <div class="section-title">
            <i class="el-icon-info"></i>
            <span>图层信息</span>
          </div>
          <div class="layer-card-info">
            <span class="tag">{{ currentSettingsLayer.file_type }}</span>
            <span class="tag">{{ currentSettingsLayer.discipline }}</span>
            <span class="tag">{{ currentSettingsLayer.dimension }}</span>
            <!-- 显示服务类型 -->
            <span v-if="currentSettingsLayer.service_type" class="tag" :class="getServiceTypeClass(currentSettingsLayer.service_type)">
              {{ getServiceTypeText(currentSettingsLayer) }}
            </span>
            <!-- 显示图层状态 -->
            <span class="tag" :class="getLayerStatusClass(currentSettingsLayer)">
              {{ getLayerStatusText(currentSettingsLayer) }}
            </span>
          </div>
        </div>
        
        <!-- 透明度控制 -->
        <div class="settings-section">
          <div class="section-title">
            <i class="el-icon-view"></i>
            <span>透明度调节</span>
          </div>
          <div class="layer-opacity-control">
            <div class="opacity-row">
              <el-slider
                v-model="currentSettingsLayer.opacity"
                :min="0"
                :max="1"
                :step="0.01"
                :show-tooltip="true"
                :format-tooltip="(val) => Math.round(val * 100) + '%'"
                @input="updateLayerOpacityInMap(currentSettingsLayer)"
                @change="updateLayerOpacityInDatabase(currentSettingsLayer)"
                class="opacity-slider"
              />
              <span class="opacity-value">{{ Math.round((currentSettingsLayer.opacity || 1) * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- 图层顺序控制 -->
        <div class="settings-section">
          <div class="section-title">
            <i class="el-icon-sort"></i>
            <span>图层顺序</span>
          </div>
          <div class="layer-order-control">
            <el-button 
              size="small" 
              icon="el-icon-top" 
              @click="moveLayerUp(sortedLayersList.findIndex(l => l.scene_layer_id === currentSettingsLayer.scene_layer_id))"
              :disabled="sortedLayersList.findIndex(l => l.scene_layer_id === currentSettingsLayer.scene_layer_id) === 0"
              class="order-btn"
            >上移一层</el-button>
            <el-button 
              size="small" 
              icon="el-icon-bottom" 
              @click="moveLayerDown(sortedLayersList.findIndex(l => l.scene_layer_id === currentSettingsLayer.scene_layer_id))"
              :disabled="sortedLayersList.findIndex(l => l.scene_layer_id === currentSettingsLayer.scene_layer_id) === sortedLayersList.length - 1"
              class="order-btn"
            >下移一层</el-button>
          </div>
        </div>

        <!-- 图层操作按钮 -->
        <div class="settings-section settings-actions">
          <el-button 
            size="small" 
            type="primary" 
            @click="showStyleDialog(currentSettingsLayer)"
            class="action-btn style-action-btn"
            title="样式设置"
          >
            <i class="el-icon-brush"></i>
            <span>样式设置</span>
          </el-button>
          
          <el-button 
            size="small" 
            type="danger" 
            @click="handleRemoveLayerFromDialog" 
            class="action-btn delete-action-btn"
            title="删除图层"
          >
            <i class="el-icon-delete"></i>
            <span>删除图层</span>
          </el-button>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeLayerSettingsDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import MapViewerDeckGL from '@/components/MapViewerDeckGL.vue'
import { isMobileDevice } from '@/utils/deviceUtils'
import gisApi from '@/api/gis'
// 🔥 添加样式设置相关组件导入
import DxfStyleEditor from '@/components/DxfStyleEditor.vue'
import SldStyleSelector from '@/components/SldStyleSelector.vue'
import { Loading } from '@element-plus/icons-vue'

export default {
  name: 'MapViewDeckGL',
  components: {
    MapViewerDeckGL,
    // 🔥 添加样式设置相关组件
    DxfStyleEditor,
    SldStyleSelector,
    Loading
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    // 响应式数据
    const mapViewer = ref(null)
    const deckglMap = ref(null)
    const layerPanelCollapsed = ref(false)
    // 🔥 手机端抽屉相关状态
    const mobileDrawerVisible = ref(false)
    const mobileActiveTab = ref('layers') // 'scene' or 'layers'
    
    // 🔥 拖拽手柄相关状态
    const isDragging = ref(false)
    const dragStartY = ref(0)
    const drawerStartY = ref(0)
    const addLayerDialogVisible = ref(false)
    const loadingLayers = ref(false)
    const layersCacheEnabled = ref(true)
    const loading = ref(false)
    const currentActiveLayer = ref(null)
    
    // 🔥 样式设置相关响应式数据
    const styleDialogVisible = ref(false)
    const currentStyleLayer = ref(null)
    const activeStyleTab = ref('basic')
    const savingDxfStyles = ref(false)
    const dxfStyleEditorRef = ref(null)
    const sldStyleSelectorRef = ref(null)
    
    // 样式表单
    const styleForm = reactive({
      point: { color: '#FF0000', size: 6 },
      line: { color: '#0000FF', width: 2 },
      polygon: { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' },
      raster: { opacity: 1 }
    })
    
    // 图层样式缓存
    const layerStyleCache = ref({})
    
    // 图层管理
    const layersList = ref([])
    const availableLayers = ref([])
    const selectedLayers = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalLayers = ref(0)
    
    // 场景管理
    const sceneList = ref([])
    const selectedSceneId = ref(null)
    
    // 搜索表单
    const layerSearchForm = reactive({
      service_type: '',
      file_type: '',
      keyword: ''
    })
    
    // 🔥 图层设置对话框相关
    const layerSettingsDialogVisible = ref(false)
    const currentSettingsLayer = ref(null)
    
    // 计算属性
    const isMobile = computed(() => isMobileDevice())
    
    const sortedLayersList = computed(() => {
      return [...layersList.value].sort((a, b) => (b.zIndex || 0) - (a.zIndex || 0))
    })
    
    // 🔥 样式设置相关计算属性
    const isVectorLayer = computed(() => {
      if (!currentStyleLayer.value) return false
      // 更宽松的向量图层判断，包括更多文件类型
      const vectorTypes = ['shp', 'dxf', 'dwg', 'geojson', 'kml', 'gml']
      return vectorTypes.includes(currentStyleLayer.value.file_type) || 
             currentStyleLayer.value.service_type === 'martin' // Martin服务通常是向量图层
    })
    
    const isMartinLayer = computed(() => {
      return currentStyleLayer.value?.service_type === 'martin'
    })
    
    const isDxfMartinLayer = computed(() => {
      return currentStyleLayer.value?.service_type === 'martin' && 
             currentStyleLayer.value?.file_type === 'dxf' && 
             Boolean(currentStyleLayer.value?.martin_service_id)
    })
    
    const hasPointGeometry = computed(() => {
      if (!currentStyleLayer.value) return false
      const geometryType = currentStyleLayer.value.geometry_type || currentStyleLayer.value.dimension || currentStyleLayer.value.geom_type
      if (!geometryType) return false
      const normalizedType = geometryType.toLowerCase()
      return normalizedType.includes('point')
    })
    
    const hasLineGeometry = computed(() => {
      if (!currentStyleLayer.value) return false
      const geometryType = currentStyleLayer.value.geometry_type || currentStyleLayer.value.dimension || currentStyleLayer.value.geom_type
      if (!geometryType) return false
      const normalizedType = geometryType.toLowerCase()
      return normalizedType.includes('line') || normalizedType.includes('linestring')
    })
    
    const hasPolygonGeometry = computed(() => {
      if (!currentStyleLayer.value) return false
      const geometryType = currentStyleLayer.value.geometry_type || currentStyleLayer.value.dimension || currentStyleLayer.value.geom_type
      if (!geometryType) return false
      const normalizedType = geometryType.toLowerCase()
      return normalizedType.includes('polygon')
    })
    
    // 地图准备完成
    const onMapReady = (mapInstance) => {
      deckglMap.value = mapInstance
      console.log('Deck.gl地图准备完成')
    }
    
    // 图层点击事件
    const onLayerClick = (event) => {
      console.log('图层点击:', event)
      // 🔥 修改：处理要素选择事件
      if (event.feature && event.layer) {
        // 可以在这里添加额外的要素选择逻辑
        // 例如：更新当前活动图层、显示要素详情等
        console.log('要素已选择:', event.feature.properties)
      }
    }
    
    // 🔥 新增：清除要素选择
    const clearFeatureSelection = () => {
      if (mapViewer.value && mapViewer.value.clearFeatureSelection) {
        mapViewer.value.clearFeatureSelection()
      }
    }
    
    // 切换图层面板
    const toggleLayerPanel = () => {
      layerPanelCollapsed.value = !layerPanelCollapsed.value
    }
    
    // 显示移动端图层面板
    // 🔥 手机端抽屉控制方法
    const toggleMobileDrawer = () => {
      mobileDrawerVisible.value = !mobileDrawerVisible.value
      // 默认显示图层标签页
      if (mobileDrawerVisible.value) {
        mobileActiveTab.value = 'layers'
      }
    }
    
    const closeMobileDrawer = () => {
      mobileDrawerVisible.value = false
      // 重置拖拽状态
      isDragging.value = false
      dragStartY.value = 0
      drawerStartY.value = 0
    }
    
    const selectMobileScene = (sceneId) => {
      // 选择场景后自动切换到图层标签页
      onSceneChange(sceneId)
      mobileActiveTab.value = 'layers'
    }
    
    // 🔥 拖拽手柄事件处理
    const handleDrawerHandleClick = () => {
      // 点击拖拽手柄直接关闭抽屉
      closeMobileDrawer()
    }
    
    const handleDrawerDragStart = (event) => {
      isDragging.value = true
      
      // 支持触摸和鼠标事件
      const clientY = event.touches ? event.touches[0].clientY : event.clientY
      dragStartY.value = clientY
      
      // 获取抽屉当前位置
      const drawer = event.target.closest('.mobile-drawer')
      if (drawer) {
        const rect = drawer.getBoundingClientRect()
        drawerStartY.value = rect.top
      }
      
      // 阻止默认行为和事件冒泡
      event.preventDefault()
      event.stopPropagation()
      
      // 添加全局事件监听器
      if (event.touches) {
        document.addEventListener('touchmove', handleDrawerDragMove, { passive: false })
        document.addEventListener('touchend', handleDrawerDragEnd, { once: true })
      } else {
        document.addEventListener('mousemove', handleDrawerDragMove)
        document.addEventListener('mouseup', handleDrawerDragEnd, { once: true })
      }
    }
    
    const handleDrawerDragMove = (event) => {
      if (!isDragging.value) return
      
      // 支持触摸和鼠标事件
      const clientY = event.touches ? event.touches[0].clientY : event.clientY
      const deltaY = clientY - dragStartY.value
      
      // 只有向下拖拽才有效果
      if (deltaY > 10) {
        // 计算透明度，越往下拖越透明
        const opacity = Math.max(0.3, 1 - (deltaY / 200))
        
        // 获取抽屉元素并应用样式
        const drawer = document.querySelector('.mobile-drawer')
        if (drawer) {
          drawer.style.transform = `translateY(${deltaY}px)`
          drawer.style.opacity = opacity.toString()
        }
        
        // 如果拖拽距离超过阈值，准备关闭
        if (deltaY > 100) {
          const overlay = document.querySelector('.mobile-drawer-overlay')
          if (overlay) {
            overlay.style.opacity = (1 - (deltaY - 100) / 100).toString()
          }
        }
      }
      
      // 阻止默认行为
      event.preventDefault()
    }
    
    const handleDrawerDragEnd = (event) => {
      if (!isDragging.value) return
      
      // 支持触摸和鼠标事件
      const clientY = event.touches ? 
        (event.changedTouches ? event.changedTouches[0].clientY : dragStartY.value) : 
        event.clientY
      const deltaY = clientY - dragStartY.value
      
      // 移除全局事件监听器
      document.removeEventListener('touchmove', handleDrawerDragMove)
      document.removeEventListener('mousemove', handleDrawerDragMove)
      
      // 重置样式
      const drawer = document.querySelector('.mobile-drawer')
      if (drawer) {
        drawer.style.transform = ''
        drawer.style.opacity = ''
      }
      
      const overlay = document.querySelector('.mobile-drawer-overlay')
      if (overlay) {
        overlay.style.opacity = ''
      }
      
      // 如果向下拖拽距离足够，关闭抽屉
      if (deltaY > 80) {
        closeMobileDrawer()
      }
      
      // 重置拖拽状态
      isDragging.value = false
      dragStartY.value = 0
      drawerStartY.value = 0
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = async (layer) => {
      try {
        // 先更新数据库中的可见性状态
        await gisApi.updateSceneLayer(selectedSceneId.value, layer.id, {
          visible: layer.visibility
        })
        
        // 通知MapViewerDeckGL组件更新地图显示
        if (mapViewer.value && mapViewer.value.toggleLayerVisibility) {
          mapViewer.value.toggleLayerVisibility(layer)
        } else {
          // 如果直接调用方法不可用，则发送自定义事件
          const event = new CustomEvent('layerVisibilityChanged', {
            detail: {
              layerId: layer.id,
              layer: layer,
              visibility: layer.visibility
            }
          })
          window.dispatchEvent(event)
        }
        
      } catch (error) {
        console.error('更新图层可见性失败', error)
        ElMessage.error('更新图层可见性失败')
        // 回滚状态
        layer.visibility = !layer.visibility
      }
    }
    
    // 更新地图中的图层透明度（不调用API）
    const updateLayerOpacityInMap = (layer) => {
      // 限制透明度范围
      if (layer.opacity < 0) layer.opacity = 0
      if (layer.opacity > 1) layer.opacity = 1
      
      console.log(`更新图层 ${layer.layer_name} 透明度: ${Math.round(layer.opacity * 100)}%`)
      
      // 立即更新地图中的图层透明度
      if (mapViewer.value && mapViewer.value.updateLayerOpacity) {
        mapViewer.value.updateLayerOpacity(layer, layer.opacity)
      }
    }
    
    // 更新图层透明度（兼容原有调用）
    const updateLayerOpacity = (layer, newOpacity = null) => {
      if (newOpacity !== null) {
        layer.opacity = newOpacity
      }
      
      // 限制透明度范围
      if (layer.opacity < 0) layer.opacity = 0
      if (layer.opacity > 1) layer.opacity = 1
      
      console.log(`更新图层 ${layer.layer_name} 透明度: ${Math.round(layer.opacity * 100)}%`)
      
      // 1. 立即更新地图中的图层透明度
      if (mapViewer.value && mapViewer.value.updateLayerOpacity) {
        mapViewer.value.updateLayerOpacity(layer, layer.opacity)
      }
      
      // 2. 防抖更新数据库
      updateLayerOpacityInDatabase(layer)
    }
    
    // 防抖定时器映射
    const opacityUpdateTimers = ref(new Map())
    
    // 🔥 更新数据库中的图层透明度（防抖）
    const updateLayerOpacityInDatabase = async (layer) => {
      if (!selectedSceneId.value || !layer.scene_layer_id) {
        console.warn('缺少场景ID或图层ID，跳过数据库更新')
        return
      }
      
      // 清除之前的定时器
      if (opacityUpdateTimers.value.has(layer.id)) {
        clearTimeout(opacityUpdateTimers.value.get(layer.id))
      }
      
      // 设置新的防抖定时器（500ms后执行）
      const timer = setTimeout(async () => {
        try {
          const updateData = {
            opacity: layer.opacity
          }
          
          // 调用后端API更新透明度
          await gisApi.updateSceneLayer(selectedSceneId.value, layer.id, updateData)
          
          // 清除定时器
          opacityUpdateTimers.value.delete(layer.id)
        } catch (error) {
          console.error('保存透明度失败:', error)
          ElMessage.error('透明度设置保存失败')
        }
      }, 500)
      
      opacityUpdateTimers.value.set(layer.id, timer)
    }
    
    // 🔥 显示样式设置对话框
    const showStyleDialog = async (layer) => {
      console.log('=== showStyleDialog 被调用 ===')
      console.log('传入的 layer 参数:', layer)
      console.log('layer 完整对象:', JSON.stringify(layer, null, 2))
      
      currentStyleLayer.value = layer
      
      // 调试 isDxfMartinLayer 计算
      console.log('计算 isDxfMartinLayer:')
      console.log('  service_type:', currentStyleLayer.value?.service_type)
      console.log('  file_type:', currentStyleLayer.value?.file_type)
      console.log('  martin_service_id:', currentStyleLayer.value?.martin_service_id)
      console.log('  Boolean(martin_service_id):', Boolean(currentStyleLayer.value?.martin_service_id))
      
      const isDxfResult = currentStyleLayer.value?.service_type === 'martin' && 
                         currentStyleLayer.value?.file_type === 'dxf' && 
                         Boolean(currentStyleLayer.value?.martin_service_id)
      console.log('  最终计算结果:', isDxfResult)
      
      activeStyleTab.value = isDxfResult ? 'dxf' : 'basic'
      
      console.log('设置后的状态:')
      console.log('currentStyleLayer.value:', currentStyleLayer.value)
      console.log('activeStyleTab.value:', activeStyleTab.value)
      console.log('isDxfMartinLayer.value:', isDxfMartinLayer.value)
      
      // 从后端获取保存的样式配置
      try {
        let savedStyleConfig = null
        
        if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
          // Martin服务样式
          const response = await gisApi.getMartinServiceStyle(currentStyleLayer.value.martin_service_id)
          if (response?.success && response.data) {
            savedStyleConfig = response.data
            console.log('✅ 从Martin服务获取到样式配置:', savedStyleConfig)
          }
        } else {
          // GeoServer服务样式
          const response = await gisApi.getLayerStyle(currentStyleLayer.value.id)
          if (response?.success && response.data) {
            savedStyleConfig = response.data
            console.log('✅ 从GeoServer服务获取到样式配置:', savedStyleConfig)
          }
        }
        
        if (savedStyleConfig) {
          console.log('✅ 应用保存的样式配置')
          // 应用保存的样式配置到表单
          if (savedStyleConfig.point) {
            styleForm.point = { ...styleForm.point, ...savedStyleConfig.point }
          }
          if (savedStyleConfig.line) {
            styleForm.line = { ...styleForm.line, ...savedStyleConfig.line }
          }
          if (savedStyleConfig.polygon) {
            styleForm.polygon = { ...styleForm.polygon, ...savedStyleConfig.polygon }
          }
          if (savedStyleConfig.raster) {
            styleForm.raster = { ...styleForm.raster, ...savedStyleConfig.raster }
          }
          
          // 保存到缓存
          layerStyleCache.value[currentStyleLayer.value.id] = savedStyleConfig
        } else {
          console.log('⚠️ 未找到保存的样式配置，使用默认值')
          // 重置样式表单为默认值
          styleForm.point = { color: '#FF0000', size: 6 }
          styleForm.line = { color: '#0000FF', width: 2 }
          styleForm.polygon = { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
          styleForm.raster = { opacity: 1 }
        }
      } catch (error) {
        console.error('❌ 获取样式配置失败:', error)
        // 出错时使用默认值
        styleForm.point = { color: '#FF0000', size: 6 }
        styleForm.line = { color: '#0000FF', width: 2 }
        styleForm.polygon = { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
        styleForm.raster = { opacity: 1 }
      }
      
      styleDialogVisible.value = true
      console.log('styleDialogVisible 设置为 true')
      console.log('================================')
      
      // 🔥 手机端：样式设置后自动关闭图层管理抽屉
      if (isMobile.value && mobileDrawerVisible.value) {
        closeMobileDrawer()
      }
    }
    
    // 获取服务类型样式类
    const getServiceTypeClass = (serviceType) => {
      const classMap = {
        'geoserver': 'service-geoserver',
        'martin': 'service-martin',
        'wms': 'service-wms',
        'mvt': 'service-mvt'
      }
      return classMap[serviceType] || 'service-default'
    }
    
    // 获取服务类型文本
    const getServiceTypeText = (layer) => {
      const textMap = {
        'geoserver': 'GeoServer',
        'martin': 'Martin',
        'wms': 'WMS',
        'mvt': 'MVT'
      }
      return textMap[layer.service_type] || layer.service_type || '未知'
    }
    
    // 获取图层状态样式类
    const getLayerStatusClass = (layer) => {
      if (layer.visibility === false) {
        return 'status-hidden'
      }
      return 'status-visible'
    }
    
    // 获取图层状态文本
    const getLayerStatusText = (layer) => {
      if (layer.visibility === false) {
        return '隐藏'
      }
      return '可见'
    }
    
    // 缩放到图层 - 适配Deck.gl
    const zoomToLayer = async (layer) => {
      try {
        // 检查地图实例
        if (!mapViewer.value || !mapViewer.value.deckgl) {
          ElMessage.error('地图实例未初始化')
          return
        }
        
        let bbox = null
        let originalCRS = 'EPSG:4326'
        
        // 1. 优先使用图层边界API
        try {
          const response = await gisApi.getSceneLayerBounds(layer.scene_layer_id)
          if (response?.success && response.data?.bbox) {
            bbox = response.data.bbox
            originalCRS = response.data.coordinate_system || 'EPSG:4326'
            console.log('从图层边界API获取到边界:', bbox, '原始坐标系:', originalCRS)
          }
        } catch (apiError) {
          console.warn('图层边界API调用失败，尝试其他方式:', apiError)
        }
        
        // 2. 如果API调用失败，尝试从图层属性获取
        if (!bbox && layer.bbox) {
          if (typeof layer.bbox === 'string') {
            try {
              bbox = JSON.parse(layer.bbox)
            } catch (e) {
              console.error('解析图层边界框失败:', e)
            }
          } else {
            bbox = layer.bbox
          }
        }
        
        // 3. 如果仍然没有边界，尝试从文件信息获取
        if (!bbox && layer.file_id) {
          try {
            const response = await gisApi.getFileBounds(layer.file_id)
            if (response?.bbox) {
              bbox = response.bbox
              if (typeof bbox === 'string') {
                bbox = JSON.parse(bbox)
              }
            }
          } catch (fileError) {
            console.warn('获取文件边界失败:', fileError)
          }
        }
        
        if (!bbox) {
          ElMessage.warning('无法获取图层边界信息')
          return
        }
        
        // 4. 验证边界框数据
        let bounds = null
        if (Array.isArray(bbox) && bbox.length === 4) {
          // [minx, miny, maxx, maxy] 格式
          bounds = {
            minx: parseFloat(bbox[0]),
            miny: parseFloat(bbox[1]), 
            maxx: parseFloat(bbox[2]),
            maxy: parseFloat(bbox[3])
          }
        } else if (bbox.minx !== undefined) {
          // {minx, miny, maxx, maxy} 格式
          bounds = {
            minx: parseFloat(bbox.minx),
            miny: parseFloat(bbox.miny),
            maxx: parseFloat(bbox.maxx),
            maxy: parseFloat(bbox.maxy)
          }
        } else {
          ElMessage.warning('边界框数据格式不正确')
          return
        }
        
        // 5. 验证数值有效性
        if (isNaN(bounds.minx) || isNaN(bounds.miny) || isNaN(bounds.maxx) || isNaN(bounds.maxy)) {
          ElMessage.warning('边界框数据格式错误')
          return
        }
        
        // 6. 计算中心点和缩放级别
        const centerLon = (bounds.minx + bounds.maxx) / 2
        const centerLat = (bounds.miny + bounds.maxy) / 2
        
        // 计算合适的缩放级别（基于边界框大小）
        const lonDiff = Math.abs(bounds.maxx - bounds.minx)
        const latDiff = Math.abs(bounds.maxy - bounds.miny)
        const maxDiff = Math.max(lonDiff, latDiff)
        
        let zoom = 10
        if (maxDiff < 0.001) zoom = 16
        else if (maxDiff < 0.01) zoom = 14
        else if (maxDiff < 0.1) zoom = 12
        else if (maxDiff < 1) zoom = 10
        else if (maxDiff < 10) zoom = 8
        else zoom = 6
        
        // 7. 使用Deck.gl进行视图动画
        const deckglInstance = mapViewer.value.deckgl
        if (deckglInstance) {
          deckglInstance.setProps({
            initialViewState: {
              longitude: centerLon,
              latitude: centerLat,
              zoom: zoom,
              pitch: 0,
              bearing: 0,
              transitionDuration: 1000,
              transitionInterpolator: null // 使用默认插值器
            }
          })
          
          // 设置当前活动图层
          currentActiveLayer.value = layer
          
          // 🔥 手机端：缩放后自动关闭图层管理抽屉
          if (isMobile.value && mobileDrawerVisible.value) {
            closeMobileDrawer()
          }
          
          ElMessage.success(`已缩放到图层"${layer.layer_name}"范围 (${originalCRS})`)
        }
        
      } catch (error) {
        console.error('缩放到图层失败:', error)
        ElMessage.error(`缩放到图层失败: ${error.message}`)
      }
    }
    
    // 选择图层
    const selectLayer = (layer) => {
      console.log('选择图层:', layer.layer_name)
      currentActiveLayer.value = layer
      
      ElMessage.success(`已选中图层: ${layer.layer_name}`)
    }

    // 🔥 打开图层设置对话框
    const toggleLayerSettings = (layer) => {
      currentSettingsLayer.value = layer
      layerSettingsDialogVisible.value = true
    }
    
    // 🔥 关闭图层设置对话框
    const closeLayerSettingsDialog = () => {
      layerSettingsDialogVisible.value = false
      currentSettingsLayer.value = null
    }
    
    // 🔥 从对话框删除图层
    const handleRemoveLayerFromDialog = async () => {
      if (!currentSettingsLayer.value) return
      await removeLayer(currentSettingsLayer.value)
      closeLayerSettingsDialog()
    }

    // 移除图层
    const removeLayer = async (layer) => {
      try {
        await ElMessageBox.confirm(`确认从场景中移除图层"${layer.layer_name}"？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        try {
          await gisApi.removeLayerFromScene(selectedSceneId.value, layer.id)
          ElMessage.success('图层移除成功')
          // 刷新图层列表
          fetchSceneLayers(selectedSceneId.value)
        } catch (error) {
          console.error('移除图层失败', error)
          ElMessage.error('移除图层失败')
        }
      } catch {
        // 用户取消
      }
    }

    // 🔥 图层顺序调整方法
    const moveLayerUp = async (index) => {
      if (index === 0) return
      
      try {
        const newOrders = calculateNewLayersOrder(index, index - 1)
        await updateLayersOrder(newOrders)
        ElMessage.success('图层上移成功')
        await fetchSceneLayers(selectedSceneId.value)
        // 打印当前图层顺序
        console.log('图层顺序（上移后）:', layersList.value.map(layer => ({ 
          name: layer.layer_name, 
          order: layer.layer_order, 
          zIndex: layer.zIndex 
        })))
      } catch (error) {
        console.error('图层上移失败', error)
        ElMessage.error('图层上移失败')
      }
    }
    
    const moveLayerDown = async (index) => {
      if (index === sortedLayersList.value.length - 1) return
      
      try {
        const newOrders = calculateNewLayersOrder(index, index + 1)
        await updateLayersOrder(newOrders)
        ElMessage.success('图层下移成功')
        await fetchSceneLayers(selectedSceneId.value)
        // 打印当前图层顺序
        console.log('图层顺序（下移后）:', layersList.value.map(layer => ({ 
          name: layer.layer_name, 
          order: layer.layer_order, 
          zIndex: layer.zIndex 
        })))
      } catch (error) {
        console.error('图层下移失败', error)
        ElMessage.error('图层下移失败')
      }
    }
    
    // 计算新的图层顺序
    const calculateNewLayersOrder = (fromIndex, toIndex) => {
      // 使用原始图层列表而不是排序后的列表来进行顺序调整
      const originalLayers = [...layersList.value]
      
      // 首先按layer_order降序排序，确保顺序一致
      const sortedLayers = [...originalLayers].sort((a, b) => (b.layer_order || 0) - (a.layer_order || 0))
      
      const movedLayer = sortedLayers[fromIndex]
      
      // 移除被移动的图层
      sortedLayers.splice(fromIndex, 1)
      // 插入到新位置
      sortedLayers.splice(toIndex, 0, movedLayer)
      
      // 重新分配layer_order值
      const newOrders = {}
      const totalLayers = sortedLayers.length
      
      // 从1开始分配，值越大越在上面
      sortedLayers.forEach((layer, index) => {
        const newOrder = totalLayers - index
        newOrders[layer.id] = newOrder
      })
      
      return newOrders
    }
    
    // 批量更新图层顺序
    const updateLayersOrder = async (newOrders) => {
      await gisApi.reorderSceneLayers(selectedSceneId.value, newOrders)
    }
    
    // 获取图层类型文本
    const getLayerTypeText = (layer) => {
      const typeMap = {
        'geoserver': 'GeoServer服务',
        'martin': 'Martin服务',
        'shp': 'Shapefile',
        'tif': 'GeoTIFF',
        'dxf': 'DXF图纸'
      }
      return typeMap[layer.service_type] || typeMap[layer.file_type] || '未知类型'
    }
    
    // 获取图层图标
    const getLayerIcon = (layer) => {
      const iconMap = {
        'raster': '🖼️',
        'vector': '📍',
        'geoserver': '🌐',
        'martin': '⚡',
        'shp': '📄',
        'tif': '🖼️',
        'dxf': '📐'
      }
      return iconMap[layer.type] || iconMap[layer.service_type] || iconMap[layer.file_type] || '📄'
    }
    
    // 显示添加图层对话框
    const showAddLayerDialog = async () => {
      addLayerDialogVisible.value = true
      await loadAvailableLayers()
    }
    
    // 加载可用图层
    const loadAvailableLayers = async () => {
      loadingLayers.value = true
      try {
        // 参考OpenLayers版本的实现 - 使用正确的API
        const params = { ...layerSearchForm }
        Object.keys(params).forEach(key => params[key] === '' && delete params[key])

        const response = await gisApi.getFiles(params)
        let filteredFiles = response.data.files || []

        if (layerSearchForm.service_type) {
          filteredFiles = filteredFiles.filter(file => {
            if (layerSearchForm.service_type === 'geoserver') {
              return file.geoserver_service?.is_published
            } else if (layerSearchForm.service_type === 'martin') {
              return file.martin_service?.is_published
            }
            return false
          })
        }

        availableLayers.value = filteredFiles.map(file => ({
          ...file,
          layer_name: file.layer_name || file.file_name || file.original_name || '未命名图层'
        }))
        totalLayers.value = availableLayers.value.length
      } catch (error) {
        console.error('加载图层失败:', error)
        ElMessage.error('加载图层列表失败')
        // 使用模拟数据作为降级处理
        availableLayers.value = [
          {
            id: 1,
            name: '示例矢量图层',
            description: '这是一个示例矢量图层',
            service_type: 'geoserver',
            file_type: 'shp',
            type: 'vector',
            url: 'http://example.com/geoserver/wms'
          },
          {
            id: 2,
            name: '示例栅格图层',
            description: '这是一个示例栅格图层',
            service_type: 'martin',
            file_type: 'tif',
            type: 'raster',
            url: 'http://example.com/tiles/{z}/{x}/{y}.png'
          }
        ]
        totalLayers.value = availableLayers.value.length
      } finally {
        loadingLayers.value = false
      }
    }
    
    // 搜索图层
    const searchLayers = () => {
      currentPage.value = 1
      loadAvailableLayers()
    }
    
    // 重置搜索
    const resetSearch = () => {
      Object.assign(layerSearchForm, {
        service_type: '',
        file_type: '',
        keyword: ''
      })
      searchLayers()
    }
    
    // 切换图层选择
    const toggleLayerSelection = (layer) => {
      const index = selectedLayers.value.indexOf(layer.id)
      if (index > -1) {
        selectedLayers.value.splice(index, 1)
      } else {
        selectedLayers.value.push(layer.id)
      }
    }

    // 检查图层是否已在场景中
    const isLayerInScene = (fileId, serviceType) => {
      return layersList.value.some(layer => layer.file_id === fileId && layer.service_type === serviceType)
    }

    // 检查文件是否有任何已发布的服务
    const hasAnyPublishedService = (file) => {
      return (file.geoserver_service?.is_published) || (file.martin_service?.is_published)
    }

    // 添加图层到场景 - 参考OpenLayers版本实现
    const addLayerToScene = async (file, serviceType) => {
      try {
        if (!selectedSceneId.value) {
          ElMessage.error('缺少场景ID，无法添加图层')
          return
        }
        
        const serviceInfo = serviceType === 'martin' ? file.martin_service : file.geoserver_service
        
        if (!serviceInfo?.is_published) {
          ElMessage.error('服务未发布或不存在')
          return
        }
        
        let layerData = {
          layer_name: file.file_name,
          visible: true,
          service_type: serviceType,
          file_id: file.id,
          file_type: file.file_type,
          discipline: file.discipline
        }
        
        if (serviceType === 'martin') {
          const martinServices = await gisApi.searchMartinServices({ file_id: serviceInfo.file_id })
          
          const martinService = martinServices.data.services.find(service => service.file_id === serviceInfo.file_id)
          
          if (!martinService) {
            ElMessage.error('未找到对应的Martin服务')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: String(martinService.database_record_id || martinService.id),
            martin_service_id: String(martinService.database_record_id || martinService.id),
            mvt_url: serviceInfo.mvt_url,
            tilejson_url: serviceInfo.tilejson_url
          }
        } else {
          const geoserverLayerId = serviceInfo.layer_id
          if (!geoserverLayerId) {
            ElMessage.error('GeoServer服务缺少图层ID')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: String(geoserverLayerId),
            geoserver_layer_name: serviceInfo.layer_name,
            wms_url: serviceInfo.wms_url,
            wfs_url: serviceInfo.wfs_url
          }
        }
        
        await gisApi.addLayerToScene(selectedSceneId.value, layerData)
        
        ElMessage.success(`图层 "${file.file_name}" 添加成功`)
        
        addLayerDialogVisible.value = false
        fetchSceneLayers(selectedSceneId.value)
        
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || '添加图层失败'
        ElMessage.error(`添加图层失败: ${errorMessage}`)
      }
    }
    
    // 添加选中图层
    const addSelectedLayers = () => {
      const layersToAdd = availableLayers.value.filter(layer => 
        selectedLayers.value.includes(layer.id)
      )
      
      layersToAdd.forEach(async (layer) => {
        // 检查是否有可用的服务
        if (layer.martin_service?.is_published) {
          await addLayerToScene(layer, 'martin')
        } else if (layer.geoserver_service?.is_published) {
          await addLayerToScene(layer, 'geoserver')
        }
      })
      
      selectedLayers.value = []
      addLayerDialogVisible.value = false
    }
    
    // 处理分页变化
    const handlePageChange = (page) => {
      currentPage.value = page
      loadAvailableLayers()
    }
    
    // 场景变化
    const onSceneChange = (sceneId) => {
      selectedSceneId.value = sceneId
      
      // 更新URL参数
      router.replace({
        name: 'MapDeckGL',
        query: { scene_id: sceneId }
      })
      
      fetchSceneLayers(sceneId)
    }
    
    // 切换图层缓存
    const toggleLayersCache = () => {
      layersCacheEnabled.value = !layersCacheEnabled.value
      ElMessage.success(layersCacheEnabled.value ? '已开启图层缓存' : '已关闭图层缓存')
    }
    
    // 获取场景列表
    const fetchSceneList = async () => {
      try {
        const response = await gisApi.getScenes()
        sceneList.value = response.data.scenes
        //console.log('sceneListlen:', sceneList.value.length)
        // 如果URL中有scene_id参数，设置为当前选中的场景
        const sceneIdFromQuery = route.query.scene_id
        //console.log('sceneIdFromQuery:', sceneIdFromQuery)
        if (sceneIdFromQuery) {
          selectedSceneId.value = sceneIdFromQuery
        } else if (sceneList.value.length > 0) {
          // 如果没有指定场景，选择第一个场景
          selectedSceneId.value = sceneList.value[0].id
        }
      } catch (error) {
        console.error('获取场景列表失败', error)
        ElMessage.error('获取场景列表失败')
      }
    }

    // 获取场景图层
    const fetchSceneLayers = async (sceneId) => {
      if (!sceneId) {
        layersList.value = []
        currentActiveLayer.value = null
        return
      }
      
      try {
        loading.value = true
        const response = await gisApi.getScene(sceneId)
        layersList.value = response.data.layers || []
        
        // 🔥 初始化图层不透明度（如果没有设置或为0则默认为1）
        layersList.value.forEach(layer => {
          if (layer.opacity === undefined || layer.opacity === null || layer.opacity === 0) {
            layer.opacity = 1.0  // 默认100%不透明度
          }
          // 确保数值在有效范围内
          layer.opacity = Math.max(0, Math.min(1, parseFloat(layer.opacity) || 1.0))
          
          // 🔥 关键修复：将layer_order映射到zIndex，确保排序正确
          layer.zIndex = layer.layer_order || 0
        })
        
        // 清除选中状态
        currentActiveLayer.value = null
      } catch (error) {
        console.error('获取场景图层失败', error)
        ElMessage.error('获取场景图层失败')
        layersList.value = []
      } finally {
        loading.value = false
      }
    }

    // 监听选中场景变化
    watch(selectedSceneId, (newSceneId) => {
      if (newSceneId) {
        fetchSceneLayers(newSceneId)
      }
    })

    // 组件挂载时获取数据
    onMounted(() => {
      fetchSceneList()
    })
    
    // 🔥 应用样式
    const applyStyle = async () => {
      if (!currentStyleLayer.value) return
      
      const styleConfig = isVectorLayer.value 
        ? { point: { ...styleForm.point }, line: { ...styleForm.line }, polygon: { ...styleForm.polygon } }
        : { raster: { ...styleForm.raster } }
      
      // 将样式配置保存到缓存中，供重新加载图层时使用
      layerStyleCache.value[currentStyleLayer.value.id] = styleConfig
      
      if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
        await gisApi.updateMartinServiceStyle(currentStyleLayer.value.martin_service_id, styleConfig)
      } else {
        await gisApi.updateLayerStyle(currentStyleLayer.value.id, styleConfig)
      }
      
      // 重新加载图层
      if (currentStyleLayer.value.service_type === 'martin') {
        // 通知MapViewerDeckGL组件更新图层样式
        if (mapViewer.value && mapViewer.value.updateMartinLayerStyle) {
          await mapViewer.value.updateMartinLayerStyle(currentStyleLayer.value, styleConfig)
        }
      } else {
        // 通知MapViewerDeckGL组件更新GeoServer图层样式
        if (mapViewer.value && mapViewer.value.updateGeoServerLayerStyle) {
          await mapViewer.value.updateGeoServerLayerStyle(currentStyleLayer.value, styleConfig)
        }
      }
      
      styleDialogVisible.value = false
      ElMessage.success('样式应用成功')
    }
    
    // 🔥 应用并保存DXF样式
    const applyAndSaveDxfStyles = async () => {
      if (!currentStyleLayer.value || !dxfStyleEditorRef.value) return
      
      try {
        savingDxfStyles.value = true
        await dxfStyleEditorRef.value.saveStylesToDatabase()
        ElMessage.success('DXF样式保存成功')
        styleDialogVisible.value = false
      } catch (error) {
        console.error('保存DXF样式失败:', error)
        ElMessage.error('保存DXF样式失败')
      } finally {
        savingDxfStyles.value = false
      }
    }
    
    // 🔥 DXF样式更新回调
    const onDxfStylesUpdated = (styles) => {
      console.log('DXF样式已更新:', styles)
      // 通知地图组件更新样式
      if (mapViewer.value && mapViewer.value.updateDxfStyles) {
        mapViewer.value.updateDxfStyles(currentStyleLayer.value, styles)
      }
    }
    
    // 🔥 弹窗控制变化回调
    const onPopupControlChanged = (popupConfig) => {
      console.log('弹窗控制配置已更新:', popupConfig)
      // 通知地图组件更新弹窗配置
      if (mapViewer.value && mapViewer.value.updatePopupConfig) {
        mapViewer.value.updatePopupConfig(currentStyleLayer.value, popupConfig)
      }
    }
    
    // 🔥 SLD样式应用回调
    const onSldStyleApplied = (styleInfo) => {
      console.log('SLD样式已应用:', styleInfo)
      ElMessage.success('SLD样式应用成功')
    }
    
    // 🔥 SLD样式移除回调
    const onSldStyleRemoved = () => {
      console.log('SLD样式已移除')
      ElMessage.success('SLD样式移除成功')
    }
    
    // 🔥 刷新地图图层
    const refreshMapLayers = () => {
      if (mapViewer.value && mapViewer.value.refreshLayers) {
        mapViewer.value.refreshLayers()
        ElMessage.success('地图图层已刷新')
      }
    }
    
    // 🔥 获取图层几何类型
    const getLayerGeometryType = (layer) => {
      return layer.geometry_type || layer.dimension || 'unknown'
    }
    
    return {
      // 组件引用
      mapViewer,
      
      // 响应式数据
      layerPanelCollapsed,
      // 🔥 手机端抽屉相关
      mobileDrawerVisible,
      mobileActiveTab,
      toggleMobileDrawer,
      closeMobileDrawer,
      selectMobileScene,
      
      // 🔥 拖拽手柄相关
      isDragging,
      handleDrawerHandleClick,
      handleDrawerDragStart,
      addLayerDialogVisible,
      loadingLayers,
      layersCacheEnabled,
      loading,
      layersList,
      availableLayers,
      selectedLayers,
      currentPage,
      pageSize,
      totalLayers,
      sceneList,
      selectedSceneId,
      layerSearchForm,
      currentActiveLayer,
      // 🔥 图层设置对话框相关
      layerSettingsDialogVisible,
      currentSettingsLayer,
      
      // 🔥 样式设置相关响应式数据
      styleDialogVisible,
      currentStyleLayer,
      activeStyleTab,
      savingDxfStyles,
      dxfStyleEditorRef,
      sldStyleSelectorRef,
      styleForm,
      layerStyleCache,
      
      // 计算属性
      isMobile,
      sortedLayersList,
      
      // 🔥 样式设置相关计算属性
      isVectorLayer,
      isMartinLayer,
      isDxfMartinLayer,
      hasPointGeometry,
      hasLineGeometry,
      hasPolygonGeometry,
      
      // 方法
      onMapReady,
      onLayerClick,
      toggleLayerPanel,

      toggleLayerVisibility,
      updateLayerOpacity,
      updateLayerOpacityInDatabase,
      zoomToLayer,
      removeLayer,
      getLayerTypeText,
      getLayerIcon,
      showAddLayerDialog,
      showStyleDialog,
      getServiceTypeClass,
      getServiceTypeText,
      getLayerStatusClass,
      getLayerStatusText,
      searchLayers,
      resetSearch,
      // 🔥 图层设置相关方法
      toggleLayerSettings,
      closeLayerSettingsDialog,
      handleRemoveLayerFromDialog,
      moveLayerUp,
      moveLayerDown,
      
      toggleLayerSelection,
      addSelectedLayers,
      addLayerToScene,
      isLayerInScene,
      hasAnyPublishedService,
      loadAvailableLayers,
      handlePageChange,
      onSceneChange,
      toggleLayersCache,
      fetchSceneList,
      fetchSceneLayers,
      selectLayer,
      
      applyStyle,
      applyAndSaveDxfStyles,
      onDxfStylesUpdated,
      onPopupControlChanged,
      onSldStyleApplied,
      onSldStyleRemoved,
      refreshMapLayers,
      getLayerGeometryType,
      clearFeatureSelection
    }
  }
}
</script>

<style>
/* 全局样式 - 重置el-main的默认样式 */
.el-main {
  padding: 0 !important;
}
</style>

<style scoped>
.map-view {
  height: 100%; /* 使用100%适应父容器(el-main)的高度：calc(100vh - 60px) */
  width: 100%; /* 确保宽度也是100% */
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin: 0 !important; /* 强制移除外边距，消除与el-main的白边 */
  padding: 0 !important; /* 强制移除内边距 */
}

.map-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  height: 100%;
  width: 100%; /* 确保宽度100% */
  overflow: hidden;
  margin: 0; /* 移除外边距 */
  padding: 0; /* 移除内边距 */
  border: none; /* 移除边框 */
  background: transparent; /* 透明背景 */
}

/* 左侧图层面板 */
.layer-panel {
  width: 350px;
  background: #f8f9fa;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  z-index: 1000;
  position: relative;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
}

.layer-panel.collapsed {
  width: 48px;
  min-width: 48px;
  max-width: 48px;
  background: #e8f4f8;
}

.panel-content {
  width: 350px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 0 8px 8px 0;
  margin: 4px 0 4px 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #fafbfc 0%, #f8f9fa 100%);
  border-radius: 0 8px 0 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layer-count {
  font-size: 12px;
  color: #909399;
}

.panel-toggle-btn {
  padding: 4px 8px !important;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.panel-toggle-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.toggle-icon {
  font-size: 14px;
  color: #606266;
  font-weight: bold;
}

.panel-toggle-btn:hover .toggle-icon {
  color: #409eff;
}

/* 收起状态下的内容样式 */
.collapsed-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

/* 收起状态下的场景选择样式 */
.collapsed-scene-selector {
  padding: 8px 0 5px 0;
  border-bottom: 1px solid #e4e7ed;
}

.collapsed-section-title {
  font-size: 8px;
  color: #909399;
  text-align: center;
  margin-bottom: 4px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.collapsed-scene-item {
  position: relative;
  height: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 1px 2px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 2px;
  user-select: none;
}

.collapsed-scene-item:hover {
  background: rgba(103, 194, 58, 0.1);
  cursor: pointer;
}

.collapsed-scene-item:active {
  transform: scale(0.95);
  background: rgba(103, 194, 58, 0.2);
}

.collapsed-scene-item.active {
  background: rgba(103, 194, 58, 0.15);
  border-left: 3px solid #67c23a;
}

.scene-short-name {
  font-size: 11px;
  font-weight: 600;
  color: #67c23a;
  text-align: center;
  line-height: 1.1;
  max-width: 36px;
  word-break: break-all;
  padding: 0 2px;
}

.collapsed-scene-item.active .scene-short-name {
  color: #5ca632;
}

.scene-active-dot {
  position: absolute;
  bottom: 3px;
  left: 50%;
  transform: translateX(-50%);
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #67c23a;
}

/* 分隔线样式 */
.collapsed-separator {
  height: 1px;
  background: linear-gradient(90deg, transparent, #e4e7ed 20%, #e4e7ed 80%, transparent);
  margin: 5px 4px;
}

.collapsed-layers {
  flex: 1;
  overflow-y: auto;
  padding: 5px 0;
}

.collapsed-layer-item {
  position: relative;
  height: 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 1px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 2px;
  margin: 1px 2px;
  user-select: none; /* 防止双击时选中文本 */
}

.collapsed-layer-item:hover {
  background: rgba(64, 158, 255, 0.1);
  cursor: pointer;
}

/* 双击时的反馈效果 */
.collapsed-layer-item:active {
  transform: scale(0.95);
  background: rgba(64, 158, 255, 0.2);
}

/* 双击动画效果 */
@keyframes dblclick-zoom {
  0% { transform: scale(1); }
  50% { transform: scale(0.9); }
  100% { transform: scale(1); }
}

.collapsed-layer-item.zoom-animation {
  animation: dblclick-zoom 0.2s ease-in-out;
}

.collapsed-layer-item.active {
  background: rgba(64, 158, 255, 0.15);
  border-left: 3px solid #409eff;
}

.collapsed-layer-item.invisible {
  opacity: 0.5;
}
.collapsed-toggle {
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.collapsed-toggle:hover {
  background: #e6f1fc;
}

.scene-selector {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* 图层卡片 */
.layer-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.layer-card {
  /* CSS变量定义 - 与OpenLayers保持一致 */
  --layer-card-spacing: 4px;
  --layer-card-padding: 6px 10px;
  --layer-card-border-radius: 6px;
  --layer-info-spacing: 2px;
  --tag-padding: 0px 4px;

  background: white;
  border: 1px solid #e4e7ed;
  border-radius: var(--layer-card-border-radius);
  margin-bottom: var(--layer-card-spacing);
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}


.layer-card:hover {
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.08);
  border-color: #c6e2ff;
}

.layer-card.active {
  border-color: #409eff;
  box-shadow: 0 1px 8px rgba(64, 158, 255, 0.15);
}

.layer-card.invisible {
  opacity: 0.6;
}

.layer-card-header {
  padding: var(--layer-card-padding);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f5f7fa;
  background: white;
  border-radius: var(--layer-card-border-radius) var(--layer-card-border-radius) 0 0;
}

.layer-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  flex: 1;
  min-width: 0; /* 允许flex子项收缩 */
}

.layer-name-wrapper {
  flex: 1;
  min-width: 0; /* 允许收缩 */
  overflow: hidden;
}

.layer-name {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  width: 100%;
}

.active-indicator {
  color: #409eff;
  font-size: 16px;
}

.layer-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0; /* 防止按钮被压缩 */
  margin-left: auto; /* 推到右边 */
}

.zoom-btn, .remove-btn, .settings-btn {
  padding: 4px;
  color: #666;
  transition: color 0.2s;
}

.zoom-btn:hover {
  color: #409eff;
}

.remove-btn:hover {
  color: #f56c6c;
}

.settings-btn {
  padding: 4px;
  color: #666;
  transition: all 0.2s;
}

.settings-btn:hover {
  color: #409eff;
  background: transparent;
}

.settings-btn.active {
  color: #409eff;
  background: transparent;
}

.settings-btn.active svg {
  animation: rotate 0.5s ease;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(180deg); }
}

/* 🔥 设置面板样式优化 */
.layer-settings-panel {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-top: 2px solid #e4e7ed;
  animation: slideDown 0.3s ease;
  overflow: hidden;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

.settings-section {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.settings-section:last-child {
  border-bottom: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
}

.section-title i {
  color: #909399;
  font-size: 14px;
}

.layer-card-info {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  display: inline-block;
  padding: var(--tag-padding);
  background: #f5f7fa;
  color: #4e5969;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
}

.tag.service-geoserver {
  background: #e1f3d8;
  color: #67c23a;
}

.tag.service-martin {
  background: #fdf6ec;
  color: #e6a23c;
}

.tag.service-wms {
  background: #f0f9ff;
  color: #409eff;
}

.tag.service-mvt {
  background: #f5f2ff;
  color: #9c88ff;
}

.tag.status-visible {
  background: #e1f3d8;
  color: #67c23a;
}

.tag.status-hidden {
  background: #fef0f0;
  color: #f56c6c;
}

/* 🔥 透明度控制样式优化 */
.layer-opacity-control {
  background: white;
  border-radius: 6px;
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
}

.opacity-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.opacity-value {
  font-size: 13px;
  color: #409eff;
  font-weight: 600;
  min-width: 42px;
  text-align: right;
  flex-shrink: 0;
  background: #ecf5ff;
  padding: 4px 8px;
  border-radius: 4px;
}

.opacity-slider {
  flex: 1;
}

.opacity-slider :deep(.el-slider__runway) {
  height: 6px;
  background: linear-gradient(90deg, #f0f2f5 0%, #e4e7ed 100%);
  border-radius: 3px;
}

.opacity-slider :deep(.el-slider__bar) {
  height: 6px;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
  border-radius: 3px;
  box-shadow: 0 0 4px rgba(64, 158, 255, 0.3);
}

.opacity-slider :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 3px solid #409eff;
  background: #fff;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
  transition: all 0.2s;
}

.opacity-slider :deep(.el-slider__button:hover) {
  transform: scale(1.2);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.5);
}




.collapsed-section-title {
  writing-mode: horizontal-tb;
  text-orientation: mixed;
  padding: 4px 2px;
  text-align: center;
  font-size: 10px;
  color: #909399;
  font-weight: 500;
  background: #f0f2f5;
  margin: 1px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed-scene-selector {
  padding: 8px 0;
}





.scene-short-name {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
  word-break: break-all;
}

.scene-active-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 6px;
  height: 6px;
  background: #67c23a;
  border-radius: 50%;
  border: 1px solid white;
}

.collapsed-separator {
  height: 1px;
  background: #e4e7ed;
  margin: 8px 4px;
}

.collapsed-layers {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.collapsed-layer-item {
  margin: 4px;
  padding: 6px 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  text-align: center;
}

.collapsed-layer-item:hover {
  background: #ecf5ff;
  transform: translateX(2px);
}

.collapsed-layer-item.active {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.collapsed-layer-item.invisible {
  opacity: 0.5;
  background: #f5f7fa;
}

.layer-short-name {
  font-size: 10px;
  font-weight: 500;
  line-height: 1.2;
  word-break: break-all;
}

.layer-active-dot {
  position: absolute;
  top: 1px;
  right: 1px;
  width: 6px;
  height: 6px;
  background: #67c23a;
  border-radius: 50%;
  border: 1px solid white;
}

.layer-invisible-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 6px;
  height: 6px;
  background: #f56c6c;
  border-radius: 50%;
  border: 1px solid white;
}

.layer-card-body {
  padding: 12px;
  border-top: 1px solid #f0f0f0;
}

.layer-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.layer-type, .layer-service {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #f0f2f5;
  color: #666;
}

.layer-opacity {
  margin-top: 8px;
}

.opacity-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.opacity-slider {
  width: 100%;
}

.layer-control {
  margin-bottom: 12px;
}

.layer-control label {
  display: block;
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.layer-buttons {
  display: flex;
  gap: 8px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.empty-description {
  font-size: 12px;
}



.expand-btn {
  padding: 8px 12px !important;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.expand-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.expand-btn .toggle-icon {
  font-size: 16px;
  color: #606266;
  font-weight: bold;
}

.expand-btn:hover .toggle-icon {
  color: #409eff;
}

/* 地图区域 */
.map-container-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: transparent;
  min-height: 0; /* 防止flex容器高度计算问题 */
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  outline: none;
}

/* .map-container-wrapper.with-panel 样式已移除，不再需要 */

/* 🔥 手机端专用样式 - 桌面端隐藏移动端组件 */
.mobile-layer-fab,
.mobile-drawer-overlay {
  display: none;
}

/* 桌面端显示侧边栏，手机端隐藏 */
.desktop-only {
  display: block;
}



/* 手机端样式 */
@media (max-width: 768px) {
  /* 隐藏桌面端组件 */
  .desktop-only {
    display: none !important;
  }

  /* 显示手机端组件 */
  .mobile-only {
    display: block !important;
  }

  /* 手机端抽屉样式 */
  .mobile-drawer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 2000;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
  }

  .mobile-drawer-overlay.show {
    opacity: 1;
    visibility: visible;
  }
/* 🔥 抽屉面板 */
.mobile-drawer {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-radius: 20px 20px 0 0;
    transform: translateY(100%);
    transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    max-height: 75vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.15);
    overflow: hidden;
    /* 🔥 为拖拽准备的变量 */
    --drawer-opacity: 1;
    opacity: var(--drawer-opacity);
  }
  
  .mobile-drawer.show {
    transform: translateY(0);
  }
  
  /* 抽屉头部 */
  .mobile-drawer-header {
    padding: 15px 20px 10px;
    border-bottom: 1px solid #f0f0f0;
    flex-shrink: 0;
    background: white;
  }
  
  .drawer-handle {
    width: 50px; /* 🔥 手机应用常见的短横线宽度 */
    height: 4px; /* 🔥 适中的高度 */
    background: #e4e7ed; /* 🔥 更淡的颜色，低调不显眼 */
    border-radius: 2px; /* 🔥 圆润的圆角 */
    margin: 8px auto 16px; /* 🔥 上下间距，居中 */
    cursor: grab; /* 🔥 显示拖拽光标 */
    transition: all 0.15s ease; /* 🔥 更快的过渡 */
    position: relative;
    user-select: none; /* 🔥 防止选中文本 */
    opacity: 0.6; /* 🔥 更透明，更低调 */
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08); /* 🔥 微妙的阴影 */
  }

  /* 🔥 为了增加点击区域，使用伪元素 */
  .drawer-handle::before {
    content: '';
    position: absolute;
    top: -8px;
    left: -8px;
    right: -8px;
    bottom: -8px;
    cursor: grab;
  }
  
  .drawer-handle:hover {
    background: #d3d4d6; /* 🔥 悬停时稍微深一点，但仍然低调 */
    opacity: 1; /* 🔥 悬停时不透明 */
    cursor: grab;
  }
  
  .drawer-handle:active,
  .drawer-handle.dragging {
    background: #c0c4cc; /* 🔥 拖拽时稍微深一点 */
    opacity: 1; /* 🔥 拖拽时不透明 */
    cursor: grabbing; /* 🔥 拖拽光标 */
  }

  .drawer-handle:active::before,
  .drawer-handle.dragging::before {
    cursor: grabbing; /* 🔥 伪元素也要改变光标 */
  }
  
  .drawer-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .drawer-title h3 {
    margin: 0;
    font-size: 18px;
    color: #303133;
    font-weight: 600;
  }
  
  .drawer-actions {
    display: flex;
    gap: 8px;
  }
  
  .drawer-actions .el-button {
    border-radius: 8px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 4px; /* 🔥 图标和文字间距 */
    padding: 8px 12px; /* 🔥 调整内边距适应文字 */
  }
  
  .drawer-actions .el-button i {
    font-size: 14px; /* 🔥 确保图标大小合适 */
  }
  
  .drawer-actions .el-button span {
    font-size: 13px; /* 🔥 文字大小 */
    white-space: nowrap; /* 🔥 防止文字换行 */
  }
  
  /* 抽屉内容 */
  .mobile-drawer-content {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: white;
  }

  .mobile-drawer-close {
    background: none;
    border: none;
    font-size: 24px;
    color: #909399;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mobile-drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  /* 手机端标签页 */
  .mobile-tabs {
    display: flex;
    border-bottom: 1px solid #e4e7ed;
    background: #f8f9fa;
  }

  .mobile-tab {
    flex: 1;
    padding: 16px;
    text-align: center;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: #606266;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    position: relative;
  }

  .mobile-tab.active {
    color: #409eff;
    border-bottom-color: #409eff;
    background: white;
  }

  .tab-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: #f56c6c;
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    min-width: 16px;
    text-align: center;
  }

  .mobile-tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  /* 手机端场景列表 */
  .mobile-scene-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .mobile-scene-item {
    border: 1px solid #e4e7ed;
    border-radius: 12px;
    padding: 16px;
    background: white;
    transition: all 0.3s;
    cursor: pointer;
  }

  .mobile-scene-item:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }

  .mobile-scene-item.active {
    border-color: #409eff;
    background: #f0f9ff;
  }

  .scene-info h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }

  .scene-info p {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }

  .scene-meta {
    margin-top: 8px;
  }

  /* 手机端图层列表 */
  .mobile-layer-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .mobile-layer-item {
    border: 1px solid #e4e7ed;
    border-radius: 12px;
    padding: 16px;
    background: white;
    transition: all 0.3s;
  }

  .mobile-layer-item:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  }

  .mobile-layer-item.active {
    border-color: #409eff;
    background: #f0f9ff;
  }

  .mobile-layer-item.invisible {
    opacity: 0.6;
  }

  .layer-main-info {
    margin-bottom: 12px;
  }

  .layer-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .layer-name {
    font-weight: 600;
    font-size: 15px;
    color: #303133;
    flex: 1;
  }

  .active-indicator {
    color: #409eff;
    font-size: 16px;
  }

  .layer-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }

  .tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    background: #f0f0f0;
    color: #606266;
  }

  .mobile-opacity-control {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .opacity-label {
    font-size: 13px;
    color: #606266;
    min-width: 60px;
  }

  .mobile-opacity-slider {
    flex: 1;
  }

  .opacity-value {
    font-size: 13px;
    color: #409eff;
    min-width: 40px;
    text-align: right;
  }

  .layer-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .action-btn {
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #dcdfe6;
    background: white;
    color: #606266;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .action-btn:hover {
    border-color: #409eff;
    color: #409eff;
  }

  .action-btn.zoom-btn:hover {
    border-color: #67c23a;
    color: #67c23a;
  }

  .action-btn.style-btn:hover {
    border-color: #e6a23c;
    color: #e6a23c;
  }

  .action-btn.delete-btn:hover {
    border-color: #f56c6c;
    color: #f56c6c;
  }

  .mobile-empty {
    text-align: center;
    padding: 40px 20px;
    color: #909399;
  }

  .mobile-empty i {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .mobile-empty p {
    margin: 0 0 16px 0;
    font-size: 14px;
  }

  /* 手机端浮动按钮 */
  .mobile-layer-fab {
    position: fixed;
    left: 50%;
    bottom: 5px;
    transform: translateX(-50%);
    z-index: 2000;
    background: #409EFF;
    color: #fff;
    border-radius: 24px;
    box-shadow: 0 4px 16px rgba(64,158,255,0.18);
    padding: 0 5px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 2px;
    cursor: pointer;
    transition: box-shadow 0.2s, background 0.2s;
    border: none;
    outline: none;
    user-select: none;
    will-change: transform;
    opacity: 0.96;
  }
  .mobile-layer-fab:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
  }
  
  .mobile-layer-fab:active {
    transform: scale(0.95);
  }
  
  .fab-content {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 20px;
    color: white;
    font-weight: 500;
    position: relative;
  }
  
  .fab-content i {
    font-size: 18px;
  }
  
  .fab-text {
    font-size: 14px;
    font-weight: 600;
    
  }
  
  .fab-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: #f56c6c;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    border: 2px solid white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  /* 手机端地图容器 */
  .map-container {
    height: 100vh;
    width: 100vw;
  }

  /* 手机端按钮样式 */
  .mobile-btn {
    padding: 8px 16px;
    font-size: 13px;
    border-radius: 6px;
    border: 1px solid #dcdfe6;
    background: white;
    color: #606266;
    cursor: pointer;
    transition: all 0.3s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }

  .mobile-btn:hover {
    border-color: #409eff;
    color: #409eff;
  }

  .mobile-btn.primary {
    background: #409eff;
    border-color: #409eff;
    color: white;
  }

  .mobile-btn.primary:hover {
    background: #337ecc;
    border-color: #337ecc;
  }

  .mobile-btn.danger {
    background: #f56c6c;
    border-color: #f56c6c;
    color: white;
  }

  .mobile-btn.danger:hover {
    background: #e74c3c;
    border-color: #e74c3c;
  }
}

/* 桌面端样式 */
.desktop-only {
  display: block;
}

.mobile-only {
  display: none;
}

/* 添加图层对话框 */
.add-layer-dialog-content {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.layer-search-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.available-layers {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
  padding: 10px 0;
}

.available-layer-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.available-layer-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.available-layer-item.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.layer-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-placeholder {
  font-size: 20px;
  color: #909399;
}

.layer-details {
  flex: 1;
}

.layer-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 5px;
  word-break: break-word;
}

.layer-description {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.4;
}

.layer-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.meta-item {
  font-size: 11px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 3px;
}

.layer-services {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px;
  background: #fafbfc;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.service-item .el-tag {
  flex-shrink: 0;
}

.service-item .el-button {
  flex-shrink: 0;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding: 15px 0;
  border-top: 1px solid #ebeef5;
}

/* 🔥 桌面端面板收缩功能样式加强 */
@media (min-width: 769px) {
  .desktop-only {
    display: block !important;
  }
  
  .mobile-only {
    display: none !important;
  }
  
  .layer-panel {
    width: 350px !important;
    transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
  }
  
  .layer-panel.collapsed {
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
  }
  
  .map-container-wrapper {
    transition: margin-left 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  }
  
  /* 确保收起状态下内容正确显示 */
  .layer-panel.collapsed .panel-content {
    display: none !important;
  }
  
  .layer-panel.collapsed .collapsed-content {
    display: flex !important;
    flex-direction: column;
    height: 100%;
  }
  
  /* 🔥 确保桌面端操作按钮始终可见 */
  .layer-actions {
    opacity: 1 !important;
    display: flex !important;
  }
  
  .layer-actions .el-button {
    opacity: 1 !important;
    visibility: visible !important;
  }
}

/* 🔥 移动端浮动按钮样式 */
.mobile-layer-toggle {
  position: absolute;
  bottom: 80px;
  right: 20px;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.mobile-layer-toggle .el-button {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border: none;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.4);
}

.mobile-layer-toggle .el-button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.5);
}

/* 🔥 移动端抽屉样式 */
.mobile-layer-drawer {
  z-index: 1500;
}

.mobile-layer-drawer :deep(.el-drawer) {
  background: #f8f9fa;
}

.mobile-layer-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 16px 20px;
  background: linear-gradient(90deg, #fafbfc 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e4e7ed;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.scene-selector.mobile {
  padding: 16px 20px;
  background: white;
  margin: 0 0 16px 0;
  border-radius: 8px;
  margin: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.mobile-layer-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.mobile-layer-item {
  background: white;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
}

.mobile-layer-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.mobile-layer-item .layer-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #fafbfc 0%, #fff 100%);
}

.mobile-layer-item .layer-info .layer-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

/* 🔥 修复图层名称过长覆盖按钮的问题 */
.layer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-width: 0; /* 允许flex子项收缩 */
}

.layer-name-container {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0; /* 允许收缩 */
  overflow: hidden;
}

.layer-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0; /* 允许收缩 */
}

.layer-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0; /* 防止按钮被压缩 */
  margin-left: auto; /* 推到右边 */
}

.mobile-layer-item {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.layer-main-info {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start; /* 改为顶部对齐 */
  background: linear-gradient(90deg, #fafbfc 0%, #fff 100%);
  min-width: 0; /* 允许收缩 */
}

.layer-main-info > div:first-child {
  flex: 1;
  min-width: 0; /* 允许收缩 */
  margin-right: 12px; /* 给按钮留出空间 */
}

.mobile-layer-item .layer-info .layer-type {
  font-size: 12px;
  color: #909399;
}

.mobile-layer-item .layer-controls {
  padding: 16px;
  border-top: 1px solid #f5f7fa;
  background: #fafbfc;
}

.mobile-layer-item .opacity-control {
  margin-bottom: 16px;
}

.mobile-layer-item .opacity-control span {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  display: block;
}

.mobile-layer-item .layer-actions {
  display: flex;
  gap: 12px;
}

.mobile-layer-item .layer-actions .el-button {
  flex: 1;
}

/* 🔥 手机端样式 */
@media (max-width: 768px) {
  /* 🔥 确保手机端没有白边和高度问题 */
  .map-view {
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }
  
  .map-content {
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  
  .map-container-wrapper {
    height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  
  /* 隐藏桌面端侧边栏 */
  .desktop-only {
    display: none !important;
  }
  
  /* 显示手机端组件 */
  .mobile-only {
    display: block !important;
  }
  
  /* 🔥 确保Element Plus对话框在手机端能正确显示 */
  :deep(.el-dialog__wrapper) {
    z-index: 2000 !important;
  }
  
  :deep(.el-overlay) {
    z-index: 2000 !important;
  }
  
  /* 地图容器占满全屏 */
  .map-container-wrapper {
    width: 100% !important;
    margin-left: 0 !important;
  }
}

/* 🔥 样式设置对话框样式 */
.style-dialog-content {
  min-height: 400px;
}

.style-dialog-content .el-tabs {
  height: 100%;
}

.style-dialog-content .el-tab-pane {
  padding: 20px 0;
}

.style-dialog-content h4 {
  margin: 20px 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.style-dialog-content .el-form-item {
  margin-bottom: 20px;
}

.style-dialog-content .el-color-picker {
  width: 100%;
}

.style-dialog-content .el-slider {
  margin: 10px 0;
}

.loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  text-align: center;
}

.loading-placeholder .el-icon {
  font-size: 32px;
  margin-bottom: 16px;
  color: #409eff;
}

.loading-placeholder span {
  font-size: 14px;
  margin-bottom: 8px;
}

.dialog-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
  text-align: center;
}

.dialog-loading .el-icon {
  font-size: 48px;
  margin-bottom: 20px;
  color: #409eff;
}

.dialog-loading span {
  font-size: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

/* 🔥 图层设置对话框样式 */
.layer-settings-dialog-content {
  padding: 0;
}

.layer-settings-dialog-content .settings-section {
  padding: 16px 0;
  border-bottom: 1px solid #f0f2f5;
}

.layer-settings-dialog-content .settings-section:last-child {
  border-bottom: none;
}

.layer-settings-dialog-content .section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.layer-settings-dialog-content .section-title i {
  color: #409eff;
  font-size: 16px;
}

.layer-settings-dialog-content .layer-opacity-control {
  padding: 12px 0;
}

.layer-settings-dialog-content .opacity-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.layer-settings-dialog-content .opacity-slider {
  flex: 1;
}

.layer-settings-dialog-content .opacity-value {
  min-width: 50px;
  text-align: right;
  color: #606266;
  font-size: 14px;
}

.layer-settings-dialog-content .layer-order-control {
  display: flex;
  gap: 12px;
}

.layer-settings-dialog-content .order-btn {
  flex: 1;
}

.layer-settings-dialog-content .settings-actions {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.layer-settings-dialog-content .action-btn {
  flex: 1;
}
</style>