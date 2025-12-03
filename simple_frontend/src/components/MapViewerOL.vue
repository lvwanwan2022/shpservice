<template>
  <div class="map-viewer">
    <div class="map-container" ref="mapContainer"></div>
    
    <!-- 底图切换器和刷新按钮组 -->
    <div class="map-controls">
      <BaseMapSwitcherOL v-if="map" :map="map" @base-map-changed="onBaseMapChanged" />
      <el-tooltip v-if="map" content="刷新图层" placement="left" :show-after="500"  :hide-after="1000">
        <el-button 
          type="success" 
          circle 
          size="small" 
          @click="refreshAllLayers"
          :loading="refreshing"
          class="refresh-button"
        >
        <svg t="1752031016790" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="5670" width="16" height="16"><path d="M1023.99872 479.424681V25.601248l-133.119834 129.919838A520.639349 520.639349 0 0 0 518.591352 0.00128C232.12771 0.00128 0 229.312993 0 512.00064s232.12771 511.99936 518.655352 511.99936c198.783752 0 371.199536-110.399862 458.367427-272.25566h-193.791758a359.87155 359.87155 0 0 1-264.575669 114.687857c-198.271752 0-359.039551-158.719802-359.039552-354.431557 0-195.775755 160.767799-354.431557 359.039552-354.431557 101.567873 0 193.279758 41.727948 258.559676 108.607864L558.655302 479.424681H1023.99872z" fill="#2c2c2c" p-id="5671"></path></svg>
        </el-button>
      </el-tooltip>
      <el-tooltip v-if="map" :content="layersCacheEnabled ? '关闭缓存' : '开启缓存'" placement="left" :show-after="500" :hide-after="1000">
        <el-button 
          :type="layersCacheEnabled ? 'warning' : 'info'" 
          circle 
          size="small" 
          @click="toggleLayersCache"
          class="cache-toggle-button"
        >
          
            <svg :class="layersCacheEnabled ? 'el-icon-folder-opened' : 'el-icon-folder'" t="1752031063403" class="icon" viewBox="0 0 1026 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="7600" width="16" height="16"><path d="M767.66305 531.384715l-236.251012 236.251011h-36.395426l-236.251012-236.251011L340.176422 449.973893 449.107294 559.47943V257.780503h127.703249v301.698927l109.505537-109.505537z m159.629062 279.542413l-92.137895-92.137894a395.880074 395.880074 0 1 0-204.325199 157.011145l99.161573 99.161573a511.834624 511.834624 0 1 1 197.429224-164.034824z" p-id="7601"></path></svg>
        
        </el-button>
      </el-tooltip>
      <el-tooltip v-if="map" :content="userLocationVisible ? '关闭定位' : '我的位置'" placement="left" :show-after="500" :hide-after="1000">
        <el-button 
          :type="userLocationVisible ? 'primary' : 'info'" 
          circle 
          size="small" 
          @click="toggleUserLocation"
          :loading="locationLoading"
          class="location-button"
        >
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M3.05,13H1V11H3.05C3.5,6.83 6.83,3.5 11,3.05V1H13V3.05C17.17,3.5 20.5,6.83 20.95,11H23V13H20.95C20.5,17.17 17.17,20.5 13,20.95V23H11V20.95C6.83,20.5 3.5,17.17 3.05,13M12,5A7,7 0 0,0 5,12A7,7 0 0,0 12,19A7,7 0 0,0 19,12A7,7 0 0,0 12,5Z"/>
          </svg>
        </el-button>
      </el-tooltip>
    </div>

    <!-- 右下角信息面板 -->
    <div class="map-info-panel">
      <!-- 坐标信息 -->
      <div class="coordinate-info" v-if="mouseCoordinates">
        <span class="coordinate-text">{{ mouseCoordinates.lon }}°, {{ mouseCoordinates.lat }}°</span>
      </div>
      
      <!-- 版权信息 -->
      <div class="copyright-info">
        <span v-if="currentBaseMapAttribution" v-html="currentBaseMapAttribution"></span>
        <span v-else>© OpenLayers</span>
      </div>
    </div>
    
    <!-- 添加图层对话框 -->
    <el-dialog title="添加图层" v-model="addLayerDialogVisible" :width="isMobile ? '95%' : '800px'" :fullscreen="isMobile">
      <div class="add-layer-dialog-content">
        <!-- 数据检索区 -->
        <div class="layer-search-area">
          <!-- 移动端搜索切换按钮 -->
          <div class="mobile-search-toggle" @click="toggleMobileLayerSearch">
            <el-icon class="toggle-icon" :class="{ 'rotated': mobileLayerSearchExpanded }">
              <ArrowDown />
            </el-icon>
            <span class="toggle-text">搜索筛选</span>
            <div class="search-summary" v-if="!mobileLayerSearchExpanded && hasActiveLayerFilters">
              <el-tag size="small" type="primary">{{ getActiveLayerFiltersText() }}</el-tag>
            </div>
          </div>
          
          <!-- 搜索表单 -->
          <div class="search-form-container" :class="{ 'mobile-collapsed': !mobileLayerSearchExpanded }">
            <el-form :inline="!isMobile" :model="layerSearchForm" class="layer-search-form">
          <el-form-item label="服务类型">
            <el-select v-model="layerSearchForm.service_type" placeholder="请选择服务类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="GeoServer服务" value="geoserver" />
              <el-option label="Martin服务" value="martin" />
            </el-select>
          </el-form-item>
          <el-form-item label="专业">
            <el-select v-model="layerSearchForm.discipline" placeholder="请选择专业" clearable>
              <el-option v-for="item in disciplines" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="数据类型">
            <el-select v-model="layerSearchForm.file_type" placeholder="请选择数据类型" clearable>
              <el-option v-for="item in fileTypes" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchLayers">搜索</el-button>
                <el-button @click="resetLayerSearch">清空</el-button>
          </el-form-item>
        </el-form>
          </div>
        </div>
        
        <!-- 图层列表 -->
        <div class="layer-list-container">
          <!-- 移动端卡片布局 -->
          <div class="mobile-layer-cards">
            <div v-for="layer in availableLayers" :key="layer.id" class="mobile-layer-card">
              <!-- 卡片头部：图层名称 -->
              <div class="mobile-layer-card-header">
                <div class="mobile-layer-name">{{ layer.layer_name }}</div>
              </div>
              
              <!-- 基本信息网格 -->
              <div class="mobile-layer-info">
                <div class="mobile-info-item">
                  <div class="mobile-info-label">数据类型</div>
                  <div class="mobile-info-value">
                    <el-tag v-if="layer.file_type" size="small" type="primary">{{ layer.file_type.toUpperCase() }}</el-tag>
                    <span v-else>-</span>
                  </div>
                </div>
                <div class="mobile-info-item">
                  <div class="mobile-info-label">专业</div>
                  <div class="mobile-info-value">
                    <el-tag v-if="layer.discipline" size="small" type="success">{{ layer.discipline }}</el-tag>
                    <span v-else>-</span>
                  </div>
                </div>
                <div class="mobile-info-item">
                  <div class="mobile-info-label">文件大小</div>
                  <div class="mobile-info-value">{{ formatFileSize(layer.file_size) }}</div>
                </div>
                <div class="mobile-info-item">
                  <div class="mobile-info-label">上传时间</div>
                  <div class="mobile-info-value">{{ formatDate(layer.upload_time) }}</div>
                </div>
              </div>
              
              <!-- 服务发布状态和操作 -->
              <div class="mobile-service-section">
                <!-- GeoServer服务 -->
                <div class="mobile-service-item" v-if="layer.geoserver_service?.is_published">
                  <div class="mobile-service-header">
                    <div class="mobile-service-title">GeoServer服务</div>
                    <el-tag type="success" size="small">已发布</el-tag>
                  </div>
                  <div class="mobile-service-actions">
                    <el-button 
                      size="small" 
                      type="primary" 
                      @click="addLayerToScene(layer, 'geoserver')"
                      :disabled="isLayerInScene(layer.id, 'geoserver')"
                    >
                      {{ isLayerInScene(layer.id, 'geoserver') ? '已添加' : '添加到场景' }}
                    </el-button>
                  </div>
                </div>
                
                <!-- Martin服务 -->
                <div class="mobile-service-item" v-if="layer.martin_service?.is_published">
                  <div class="mobile-service-header">
                    <div class="mobile-service-title">Martin服务</div>
                    <el-tag type="primary" size="small">已发布</el-tag>
                  </div>
                  <div class="mobile-service-actions">
                    <el-button 
                      size="small" 
                      type="success" 
                      @click="addLayerToScene(layer, 'martin')"
                      :disabled="isLayerInScene(layer.id, 'martin')"
                    >
                      {{ isLayerInScene(layer.id, 'martin') ? '已添加' : '添加到场景' }}
                    </el-button>
                  </div>
                </div>
                
                <!-- 未发布状态 -->
                <div class="mobile-service-item" v-if="!hasAnyPublishedService(layer)">
                  <div class="mobile-service-header">
                    <div class="mobile-service-title">服务状态</div>
                    <el-tag type="warning" size="small">未发布</el-tag>
                  </div>
                  <div class="mobile-service-note">此图层暂无可用服务</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 桌面端表格布局 -->
          <div class="desktop-layer-table">
        <el-table :data="availableLayers" style="width: 100%" max-height="400">
          <el-table-column prop="layer_name" label="图层名称" min-width="150" />
          <el-table-column prop="file_type" label="数据类型" width="100" />
          <el-table-column prop="discipline" label="专业" width="100" />
          <el-table-column label="服务状态" width="120">
            <template #default="scope">
              <div class="service-status">
                <el-tag v-if="scope.row.geoserver_service?.is_published" type="success" size="small">GeoServer已发布</el-tag>
                <el-tag v-if="scope.row.martin_service?.is_published" type="primary" size="small">Martin已发布</el-tag>
                <el-tag v-if="!hasAnyPublishedService(scope.row)" type="warning" size="small">未发布</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <div class="layer-actions">
                <el-button 
                  v-if="scope.row.geoserver_service?.is_published"
                  size="small" 
                  type="primary" 
                  @click="addLayerToScene(scope.row, 'geoserver')"
                  :disabled="isLayerInScene(scope.row.id, 'geoserver')"
                >
                  {{ isLayerInScene(scope.row.id, 'geoserver') ? '已添加' : '添加GeoServer' }}
                </el-button>
                <el-button 
                  v-if="scope.row.martin_service?.is_published"
                  size="small" 
                  type="success" 
                  @click="addLayerToScene(scope.row, 'martin')"
                  :disabled="isLayerInScene(scope.row.id, 'martin')"
                >
                  {{ isLayerInScene(scope.row.id, 'martin') ? '已添加' : '添加Martin' }}
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 图层样式设置对话框 -->
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
                  <el-form-item label="边框颜色">
                    <el-color-picker v-model="styleForm.polygon.outlineColor"></el-color-picker>
                  </el-form-item>
                  <el-form-item label="不透明度">
                    <el-slider v-model="styleForm.polygon.fillOpacity" :min="0" :max="1" :step="0.1"></el-slider>
                  </el-form-item>
                </template>
              </template>
              <template v-else>
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

    <!-- OpenLayers 弹窗 -->
    <div id="popup" class="ol-popup">
      <a href="#" id="popup-closer" class="ol-popup-closer"></a>
      <div id="popup-content"></div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import gisApi from '@/api/gis'
// OpenLayers 相关导入
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorLayer from 'ol/layer/Vector'
import { TileWMS, VectorTile, XYZ } from 'ol/source'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { fromLonLat, transformExtent, transform } from 'ol/proj'
import * as projlv from 'ol/proj'
import Overlay from 'ol/Overlay'
import { Style, Fill, Stroke, Circle } from 'ol/style'
import { MVT } from 'ol/format'
import BaseMapSwitcherOL from './BaseMapSwitcherOL.vue'
import DxfStyleEditor from './DxfStyleEditor.vue'
import SldStyleSelector from './SldStyleSelector.vue'
import defaultDxfStylesConfig from '@/config/defaultDxfStyles.json'
// 引入proj4库用于坐标系转换
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'
// 引入ol-proj-ch库中的GCJ02坐标系
import gcj02Mecator, { gcj02 } from '@/utils/GCJ02'
import { MARTIN_BASE_URL } from '@/config/index'
import { Loading, ArrowDown } from '@element-plus/icons-vue'
import { convertGeoServerUrlToProxy } from '@/utils/urlUtils'
import { getRecommendedPreloadLevel, getRecommendedCacheSize, getDeviceType } from '@/utils/deviceUtils'
import { 
  createWmtsTileLoadFunction, 
  createMvtTileLoadFunction
} from '@/services/tileCache/tileLoadFunctions.js';
import { TileCacheService, getGlobalSceneDataCacheService } from '@/services/tileCache';

export default {
  name: 'MapViewerOL',
  components: { BaseMapSwitcherOL, DxfStyleEditor, SldStyleSelector, Loading, ArrowDown },
  props: {
    sceneId: { type: [Number, String], default: null },
    readonly: { type: Boolean, default: false }
  },
  emits: ['layerAdded', 'layer-selected'],
  setup(props, { emit }) {
    const route = useRoute()
    const mapContainer = ref(null)
    const map = ref(null)
    const mapLayers = ref({})
    const mvtLayers = ref({})
    const currentScene = ref(null)
    const layersList = ref([])  // 确保初始化为空数组
    const currentActiveLayer = ref(null)
    const popup = ref(null)
    // 缓存服务实例
    let tileCacheService = null;
    const layersCacheEnabled = ref(false); // 当前图层的缓存状态
    // 坐标系初始化状态
    const projectionsInitialized = ref(false)
    
    // 刷新状态
    const refreshing = ref(false)
    
    // 鼠标坐标信息
    const mouseCoordinates = ref(null)
    
    // 当前底图版权信息
    const currentBaseMapAttribution = ref('')
    
    // 用户位置相关
    const userLocationVisible = ref(false)
    const locationLoading = ref(false)
    const userLocationLayer = ref(null)
    const userLocationFeature = ref(null)
    
    // 异步初始化坐标系
    const initializeProjections = async () => {
      if (!projectionsInitialized.value) {
        await initProjections()
        projectionsInitialized.value = true
      }
    }
    
    // 初始化坐标系
    const initProjections = async () => {
      try {
        //console.log('🔄 开始从后端获取坐标系定义...')
        
        // 从后端获取常用坐标系的proj4定义
        const response = await gisApi.getProj4Definitions()
        
        if (response.success && response.proj4_definitions) {
          // 注册投影定义
          Object.entries(response.proj4_definitions).forEach(([epsgCode, info]) => {
            if (info.proj4) {
              proj4.defs(epsgCode, info.proj4)
              //console.log(`✅ 注册坐标系: ${epsgCode} - ${info.name || '未知'}`)
            }
          })
          
          // 注册到OpenLayers
          register(proj4)
         
          //console.log(`✅ 坐标系初始化完成，共注册${Object.keys(response.proj4_definitions).length}个坐标系`)
          return true
        } else {
          throw new Error(response.message || '获取坐标系定义失败')
        }
        
      } catch (error) {
        console.warn('⚠️ 从后端获取坐标系定义失败，使用备用定义:', error.message)
        
        // 备用方案：使用硬编码的常用坐标系定义
        const fallbackProjections = {
          'EPSG:2379': '+proj=tmerc +lat_0=0 +lon_0=102 +k=1 +x_0=500000 +y_0=0 +ellps=IAU76 +towgs84=24,-123,-94,0,0,0,0 +units=m +no_defs +type=crs',
          'EPSG:2343': '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=15.8,-154.4,-82.3,0,0,0,0 +units=m +no_defs',
          'EPSG:2431': '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +datum=WGS84 +units=m +no_defs',
          'EPSG:4545': '+proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=15.8,-154.4,-82.3,0,0,0,0 +units=m +no_defs',
          'EPSG:4547': '+proj=tmerc +lat_0=0 +lon_0=102 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=15.8,-154.4,-82.3,0,0,0,0 +units=m +no_defs'
        }
        
        // 注册备用投影定义
        Object.entries(fallbackProjections).forEach(([code, def]) => {
          proj4.defs(code, def)
          //console.log(`⚠️ 备用注册坐标系: ${code}`)
        })
        
        // 注册到OpenLayers
        register(proj4)
        
        //console.log('⚠️ 坐标系初始化完成（使用备用定义）')
        return false
      }
    }
    const initCacheService = async () => {
      try {
        tileCacheService = new TileCacheService({
          maxCacheSize: 500 * 1024 * 1024, // 500MB
          maxCacheAge: 7 * 24 * 60 * 60 * 1000 // 7天
        });
      } catch (error) {
        console.error('初始化缓存服务失败:', error);
        ElMessage.error('初始化缓存服务失败: ' + error.message);
      }
    };

    // 动态注册单个坐标系
    const registerProjection = async (epsgCode) => {
      try {
        // 检查是否已经注册
        if (proj4.defs(epsgCode)) {
          //console.log(`✅ 坐标系 ${epsgCode} 已注册`)
          return true
        }
        
        //console.log(`🔄 动态获取坐标系定义: ${epsgCode}`)
        const response = await gisApi.getSingleProj4Definition(epsgCode)
        
        if (response.success && response.crs_info && response.crs_info.proj4_definition) {
          proj4.defs(epsgCode, response.crs_info.proj4_definition)
          register(proj4)
          //console.log(`✅ 动态注册坐标系: ${epsgCode} - ${response.crs_info.name || '未知'}`)
          return true
        } else {
          console.warn(`⚠️ 无法获取 ${epsgCode} 的proj4定义`)
          return false
        }
        
      } catch (error) {
        console.error(`❌ 动态注册坐标系 ${epsgCode} 失败:`, error.message)
        return false
      }
    }
    
    // 添加图层对话框
    const addLayerDialogVisible = ref(false)
    const availableLayers = ref([])
    const layerSearchForm = reactive({
      service_type: '',
      discipline: '',
      file_type: ''
    })
    
    // 移动端搜索相关
    const mobileLayerSearchExpanded = ref(true)
    
    // 设备检测
    const isMobile = computed(() => {
      return window.innerWidth <= 768
    })
    
    // 图层样式对话框
    const styleDialogVisible = ref(false)
    const currentStyleLayer = ref(null)
    const activeStyleTab = ref('basic')
    const dxfStyleEditorRef = ref(null)
    const savingDxfStyles = ref(false)
    
    const styleForm = reactive({
      point: { size: 2, color: '#FF0000' },
      line: { width: 2, color: '#0000FF' },
      polygon: { fillColor: '#00FF00', outlineColor: '#000000', fillopacity: 0.5 },
      raster: { opacity: 1 }
    })
    
    const disciplines = ref(['综合', '测绘', '地勘', '水文', '水工', '施工', '建筑', '金结', '电一', '电二', '消防', '暖通', '给排水', '环水', '移民', '其他'])
    const fileTypes = ref(['shp', 'dem', 'dom', 'dwg', 'dxf', 'geojson'])
    
    const isVectorLayer = computed(() => currentStyleLayer.value && ['shp', 'dwg', 'dxf', 'geojson'].includes(currentStyleLayer.value.file_type))
    const hasPointGeometry = computed(() => isVectorLayer.value)
    const hasLineGeometry = computed(() => isVectorLayer.value)
    const hasPolygonGeometry = computed(() => isVectorLayer.value)
    const isDxfMartinLayer = computed(() => {
      return currentStyleLayer.value?.service_type === 'martin' && 
             currentStyleLayer.value?.file_type === 'dxf' && 
             Boolean(currentStyleLayer.value?.martin_service_id)
    })
    
    // 判断是否为Martin图层（包括所有类型的Martin图层）
    const isMartinLayer = computed(() => {
      return currentStyleLayer.value?.service_type === 'martin' && 
             Boolean(currentStyleLayer.value?.martin_service_id)
    })
    
    // 图层样式缓存
    const layerStyleCache = reactive({})
    
    // 初始化地图
    const initMap = () => {
      //console.log('=== 开始地图初始化 ===')
      
      // 1. 清理现有地图
      if (map.value) {
        map.value.setTarget(null)
        map.value = null
      }
      
      // 2. 检查容器
      if (!mapContainer.value) {
        console.error('❌ 地图容器未找到')
        return
      }
      //console.log('✅ 地图容器已找到:', mapContainer.value)
      
      // 3. 检查OpenLayers导入
      if (!Map || !View || !TileLayer || !XYZ) {
        console.error('❌ OpenLayers模块导入失败')
        //console.log('Map:', Map, 'View:', View, 'TileLayer:', TileLayer, 'XYZ:', XYZ)
        return
      }
      //console.log('✅ OpenLayers模块导入正常')
      
      try {
        // 4. 创建底图图层
        //console.log('创建底图图层...')
        // 创建GCJ02坐标系,对高德地图进行纠偏
        // const gcj02Extent = [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244];
        //   const gcjMecator = new projlv.Projection({
        //     code: "GCJ-02",
        //     extent: gcj02Extent,
        //     units: "m"
        //   });
        //   projlv.addProjection(gcjMecator);
 // 设置GCJ02的有效范围（基于中国区域）
        

        // 获取设备特定的预加载配置
        const preloadLevel = getRecommendedPreloadLevel()
        //console.log('preloadLevel',preloadLevel)
        const cacheSize = getRecommendedCacheSize()
        const deviceType = getDeviceType()
        
        //console.log(`🚀 地图预加载配置 - 设备类型: ${deviceType}, 预加载级别: ${preloadLevel}, 缓存大小: ${cacheSize}`)
        if (!tileCacheService) {
        ElMessage.warning('缓存服务未初始化');
        return;
      }
        const wmtsTileLoadFunction_gaode = createWmtsTileLoadFunction({
          layerId: 'gaode',
          tileCacheService: tileCacheService,
          enableCacheStorage: layersCacheEnabled.value
        });
        console.log('gaodeTileLoadFunction',layersCacheEnabled.value)
        const gaodeSource =new XYZ({
            url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            crossOrigin: 'anonymous',
            projection: gcj02Mecator, // 使用GCJ02坐标系
            maxZoom: 18,              // 高德地图原生最大缩放级别
            minZoom: 3,               // 最小缩放级别
           // cacheSize: cacheSize      // 设置缓存大小
          });
          gaodeSource.setTileLoadFunction(wmtsTileLoadFunction_gaode);

        // 高德地图 - 使用GCJ02坐标系修正偏移
        const gaodeLayer = new TileLayer({
          source: gaodeSource,
          visible: true,
          maxZoom: 23,                // 允许过采样到更高级别
          minZoom: 3,
          //preload: preloadLevel       // 设置预加载级别
        })
        
        const wmtsTileLoadFunction_gaodeSatellite = createWmtsTileLoadFunction({
          layerId: 'gaodeSatellite',
          tileCacheService: tileCacheService,
          enableCacheStorage: layersCacheEnabled.value
        });
        const gaodeSatelliteSource =new XYZ({
            url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
            crossOrigin: 'anonymous',
            projection: gcj02Mecator, // 使用GCJ02坐标系
            maxZoom: 18,              // 高德卫星图原生最大缩放级别
            minZoom: 3,
          });
        // 高德卫星地图 - 使用GCJ02坐标系修正偏移
        const gaodeSatelliteLayer = new TileLayer({
          source: gaodeSatelliteSource,
          visible: false,
          maxZoom: 23,                // 允许过采样到更高级别
          minZoom: 3,
          preload: preloadLevel       // 设置预加载级别
        })
        gaodeSatelliteSource.setTileLoadFunction(wmtsTileLoadFunction_gaodeSatellite);
        
        const wmtsTileLoadFunction_osm = createWmtsTileLoadFunction({
          layerId: 'osm',
          tileCacheService: tileCacheService,
          enableCacheStorage: layersCacheEnabled.value
        });
        const osmSource =new XYZ({
          url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          crossOrigin: 'anonymous',
          maxZoom: 19,              // OSM原生最大缩放级别
          minZoom: 1,
          cacheSize: cacheSize      // 设置缓存大小
        });
        osmSource.setTileLoadFunction(wmtsTileLoadFunction_osm);
        
        // OpenStreetMap
        const osmLayer = new TileLayer({
          source: osmSource,
          visible: false,
          maxZoom: 23,                // 允许过采样到更高级别
          minZoom: 1,
          preload: preloadLevel       // 设置预加载级别
        })
        const wmtsTileLoadFunction_esriSatellite = createWmtsTileLoadFunction({
          layerId: 'esriSatellite',
          tileCacheService: tileCacheService,
          enableCacheStorage: layersCacheEnabled.value
        });
        const esriSatelliteSource =new XYZ({
          url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          crossOrigin: 'anonymous',
          maxZoom: 21,              // Esri影像最大缩放级别（原生支持21级）
          minZoom: 1,
          cacheSize: cacheSize      // 设置缓存大小
        });
        esriSatelliteSource.setTileLoadFunction(wmtsTileLoadFunction_esriSatellite);
        // Esri 世界影像（卫星图）
        const esriSatelliteLayer = new TileLayer({
          source: esriSatelliteSource,
          visible: false,
          maxZoom: 23,                // 允许过采样到更高级别
          minZoom: 1,
          preload: preloadLevel       // 设置预加载级别
        })
       
        
        //console.log('✅ 底图图层创建成功')
        
        // 5. 创建地图实例
        //console.log('创建地图实例...')
        map.value = new Map({
          target: mapContainer.value,
          layers: [gaodeLayer, gaodeSatelliteLayer, osmLayer, esriSatelliteLayer],
          view: new View({
            center: fromLonLat([104.0667, 30.6667]), // 成都坐标
            zoom: 10,
            maxZoom: 23,  // 全局最大缩放级别（适配所有底图）
            minZoom: 1    // 全局最小缩放级别
          }),
          // 设置Canvas渲染器属性来优化性能
          pixelRatio: window.devicePixelRatio || 1,
          // 在OpenLayers 10.x中，可以通过设置renderer选项来优化Canvas
          renderer: 'canvas'
        })
        
        // 等地图渲染完成后设置Canvas的willReadFrequently属性
        map.value.once('rendercomplete', () => {
          try {
            const mapElement = map.value.getTargetElement()
            const canvas = mapElement.querySelector('canvas')
            if (canvas) {
              // 尝试重新获取context并设置willReadFrequently
              const existingContext = canvas.getContext('2d')
              if (existingContext) {
                // 设置一个标记，让浏览器知道这个Canvas会被频繁读取
                canvas.setAttribute('data-will-read-frequently', 'true')
                console.log('✅ Canvas willReadFrequently 属性已设置')
              }
            }
          } catch (error) {
            console.warn('设置Canvas willReadFrequently属性时出错:', error)
          }
        })

        // Canvas willReadFrequently 优化说明：
        // 1. 改用鼠标悬停检测，只在鼠标停止移动100ms后检查要素，大幅减少Canvas读取次数
        // 2. 设置Canvas属性标记，提示浏览器优化频繁读取操作
        // 3. 添加鼠标离开事件清理定时器，避免不必要的要素检测
        // 4. 这种方式将Canvas读取频率从每次移动降低到仅在悬停时，性能提升显著
        
        // 6. 设置底图引用供切换器使用
        map.value.baseLayers = {
          gaode: gaodeLayer,
          gaodeSatellite: gaodeSatelliteLayer,
          osm: osmLayer,
          esriSatellite: esriSatelliteLayer
        }
        
        // 7. 添加瓦片加载错误处理
        const addTileErrorHandling = (layer, layerName) => {
          layer.getSource().on('tileloaderror', function(event) {
            console.warn(`${layerName}底图瓦片加载失败:`, event)
            // 可以在这里添加降级处理或显示用户友好的错误信息
          })
        }
        
        // 添加过采样监听和调试功能
        const addOversamplingSupport = (layer, layerName, nativeMaxZoom) => {
          const source = layer.getSource()
          
          // 监听瓦片加载开始
          source.on('tileloadstart', function(event) {
            const tileCoord = event.tile.getTileCoord()
            const z = tileCoord[0]
            
            // 检查是否是过采样瓦片
            if (z > nativeMaxZoom) {
              console.log(`${layerName}: 正在过采样加载 Z${z} (原生最大Z${nativeMaxZoom})`)
            }
          })
          
          // 监听瓦片加载成功
          source.on('tileloadend', function(event) {
            const tileCoord = event.tile.getTileCoord()
            const z = tileCoord[0]
            
            // 为过采样瓦片添加视觉标识（可选，用于调试）
            if (z > nativeMaxZoom) {
              const img = event.tile.getImage()
              if (img && img.style) {
                img.style.filter = 'contrast(0.9) brightness(0.95)'
                img.title = `${layerName}过采样瓦片 (Z${z}/原生Z${nativeMaxZoom})`
              }
            }
          })
        }
        
        addTileErrorHandling(gaodeLayer, '高德地图')
        addTileErrorHandling(gaodeSatelliteLayer, '高德卫星图')
        addTileErrorHandling(osmLayer, 'OpenStreetMap')
        addTileErrorHandling(esriSatelliteLayer, 'Esri影像')
        
        // 添加过采样支持
        addOversamplingSupport(gaodeLayer, '高德地图', 18)
        addOversamplingSupport(gaodeSatelliteLayer, '高德卫星图', 18)
        addOversamplingSupport(osmLayer, 'OpenStreetMap', 19)
        addOversamplingSupport(esriSatelliteLayer, 'Esri影像', 21) // Esri原生支持21级，不需要过采样
        
        // 8. 监听缩放级别变化，动态调整底图可见性
        map.value.getView().on('change:resolution', function() {
          const currentZoom = map.value.getView().getZoom()
          const currentBaseLayer = getCurrentVisibleBaseLayer()
          
          if (currentBaseLayer) {
            const layerMaxZoom = currentBaseLayer.getMaxZoom()
            const layerMinZoom = currentBaseLayer.getMinZoom()
            
            // 如果当前缩放级别超出底图支持范围，显示警告
            if (currentZoom > layerMaxZoom) {
              console.warn(`当前缩放级别(${Math.floor(currentZoom)})超出底图最大级别(${layerMaxZoom})，可能无法显示瓦片`)
            } else if (currentZoom < layerMinZoom) {
              console.warn(`当前缩放级别(${Math.floor(currentZoom)})低于底图最小级别(${layerMinZoom})，可能无法显示瓦片`)
            }
          }
        })
        
        // 9. 获取当前可见底图的辅助函数
        const getCurrentVisibleBaseLayer = () => {
          const baseLayers = map.value.baseLayers
          for (const layer of Object.values(baseLayers)) {
            if (layer.getVisible()) {
              return layer
            }
          }
          return null
        }
        
        //console.log('✅ 地图实例创建成功')
        
        // 10. 监听地图渲染
        map.value.once('rendercomplete', () => {
          //console.log('🎉 地图首次渲染完成！')
        })
        
        // 11. 延迟强制更新尺寸
        setTimeout(() => {
          if (map.value) {
            //console.log('强制更新地图尺寸...')
            map.value.updateSize()
          }
        }, 200)
        
        // 12. 初始化弹窗
        initializePopup()
        
        // 13. 初始化坐标跟踪
        initializeCoordinateTracking()
        
        // 14. 设置底图版权信息
        updateBaseMapAttribution('gaode')
        
        //console.log('=== 地图初始化完成 ===')
        
      } catch (error) {
        console.error('❌ 地图初始化失败:', error)
        console.error('错误堆栈:', error.stack)
      }
    }
    
    // 初始化弹窗 - 简化版本
    const initializePopup = () => {
      if (!map.value) return
      
      // 获取弹窗元素
      const container = document.getElementById('popup')
      const content = document.getElementById('popup-content')
      const closer = document.getElementById('popup-closer')
      
      if (!container || !content || !closer) {
        console.error('❌ 弹窗元素未找到')
        return
      }
      
      // 创建弹窗覆盖物
      popup.value = new Overlay({
        element: container,
        autoPan: {
          animation: {
            duration: 250,
          },
        },
      })
      
      // 添加到地图
      map.value.addOverlay(popup.value)
      
      // 关闭按钮事件
      closer.onclick = function () {
        popup.value.setPosition(undefined)
        closer.blur()
        return false
      }
      
      // 地图点击事件
      map.value.on('click', function (evt) {
        const coordinate = evt.coordinate
        const pixel = evt.pixel
        
        // 检查点击位置是否有要素
        const features = map.value.getFeaturesAtPixel(pixel)
        //console.log('features',features)
        if (features && features.length > 0) {
          // 找到第一个要素
          const feature = features[0]
          
          // 找到要素所属的图层
          const targetLayer = map.value.forEachFeatureAtPixel(pixel, (feat, layer) => {
             if (feat === feature && layer && mvtLayers.value && Object.values(mvtLayers.value).includes(layer)) {
              //console.log('lv-targetLayer:', layer)
               return layer
             }
            
            return null
          })
          
          if (targetLayer) {
            // 显示弹窗
            showPopup(feature, targetLayer, coordinate, content)
          }
        } else {
          // 点击空白处，隐藏弹窗
          popup.value.setPosition(undefined)
        }
      })
      
      // 鼠标悬停检测 - 只在鼠标停止移动时检查要素（大幅减少性能开销）
      let hoverTimeout = null
      const hoverDelay = 100 // 鼠标停止移动100ms后检查要素
      
      map.value.on('pointermove', function (evt) {
        if (evt.dragging) return
        
        // 清除之前的定时器
        if (hoverTimeout) {
          clearTimeout(hoverTimeout)
        }
        
        // 立即重置鼠标样式为默认
        map.value.getTargetElement().style.cursor = ''
        
        // 设置新的定时器，延迟检查要素
        hoverTimeout = setTimeout(() => {
          const pixel = evt.pixel
          const hasFeature = map.value.hasFeatureAtPixel(pixel, {
            layerFilter: (layer) => {
              // 只对MVT图层启用手型cursor
              return mvtLayers.value && Object.values(mvtLayers.value).includes(layer)
            }
          })
          
          // 改变鼠标样式
          map.value.getTargetElement().style.cursor = hasFeature ? 'pointer' : ''
        }, hoverDelay)
      })
      
      // 鼠标离开地图时清理定时器和样式
      map.value.on('pointerleave', function () {
        if (hoverTimeout) {
          clearTimeout(hoverTimeout)
          hoverTimeout = null
        }
        map.value.getTargetElement().style.cursor = ''
      })
      
      //console.log('✅ 弹窗初始化完成')
    }
    
    // 显示弹窗 - 简化版本
    const showPopup = (feature, layer, coordinate, contentElement) => {
      if (!popup.value || !feature) return
      
      // 获取要素属性
      const properties = feature.getProperties()
      
      // 找到对应的图层信息
      const layerInfo = layer._layerInfo
      //console.log('lv-layer:', layer)
      //if (!layerInfo) return
      //console.log('layerInfo:', layerInfo)
      // 构建弹窗内容
      let content = `<div style="padding: 10px;">
        <h4 style="margin: 0 0 10px 0; color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px;">
          ${layerInfo.layer_name}
          <small style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 5px;">
            ${layerInfo.file_type?.toUpperCase() || 'MVT'}
          </small>
        </h4>`
      
      // 处理属性
      const filteredProperties = Object.entries(properties)
        .filter(([key, value]) => {
          // 排除几何相关和内部属性
          if (key === 'geometry' || key === 'geom') return false
          if (value == null || value === 'NULL' || value === '') return false
          if (typeof value === 'object') return false
          return true
        })
        //.slice(0, 6) // 限制为6个属性
      
      if (filteredProperties.length === 0) {
        content += '<div style="color: #999; font-style: italic;">暂无属性信息</div>'
      } else {
        filteredProperties.forEach(([key, value]) => {
          // 格式化属性名和值
          let displayKey = key.length > 15 ? key.substring(0, 15) + '...' : key
          let displayValue = String(value).length > 30 ? String(value).substring(0, 30) + '...' : value
          
          // 特殊格式化数字
          if (typeof value === 'number' && value % 1 !== 0) {
            displayValue = Number(value).toFixed(3)
          }
          
          content += `
            <div style="margin-bottom: 8px; display: flex;">
              <span style="color: #666; margin-right: 10px; min-width: 80px; font-weight: 500;">${displayKey}：</span>
              <span style="color: #333; flex: 1;">${displayValue}</span>
            </div>
          `
        })
        
        const totalProperties = Object.keys(properties).length - 2 // 排除geometry等
        if (totalProperties > 6) {
          content += `<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; color: #999; font-style: italic; font-size: 12px; text-align: center;">共 ${totalProperties} 个属性</div>`
        }
      }
      
      content += '</div>'
      
      // 设置内容和位置
      contentElement.innerHTML = content
      popup.value.setPosition(coordinate)
      
      //console.log('🎯 显示弹窗:', layerInfo.layer_name)
    }
    
    // 加载场景
    const loadScene = async (sceneId) => {
      if (!sceneId) {
        console.warn('场景ID为空，跳过加载')
        return
      }
      
      // 检查地图实例是否存在
      if (!map.value) {
        console.warn('地图实例不存在，延迟加载场景:', sceneId)
        // 延迟重试
        setTimeout(() => {
          if (map.value) {
            loadScene(sceneId)
          } else {
            console.error('地图初始化超时，无法加载场景:', sceneId)
          }
        }, 1000)
        return
      }
      
      try {
        //console.log('开始加载场景:', sceneId)
        //console.log('sceneId:', String(sceneId))
        const response = await gisApi.getScene(sceneId)
        
        
        currentScene.value = response.scene || response.data?.scene
        
        // 🔥 确保layers是数组 - 检查不同的可能位置
        const layers = response.layers || response.data?.layers || []
        //console.log('lv-response11:', layers)
        if (Array.isArray(layers)) {
          layersList.value = layers
        } else {
          console.warn('场景图层数据不是数组，使用空数组:', layers)
          layersList.value = []
        }
        
        //console.log('场景数据加载完成，图层数量:', layersList.value.length)
        
        // 清除现有图层
        clearAllLayers()
        
        // 按layer_order排序后添加图层（顺序小的先添加，这样大的会在上层）
        const sortedLayers = [...layersList.value].sort((a, b) => {
          const orderA = a.layer_order || 0
          const orderB = b.layer_order || 0
          return orderA - orderB // 升序排列，小的先添加
        })
        
        // 添加新图层
        for (const layer of sortedLayers) {
          //console.log('lvlayertype:', layer)
          if (layer.service_type === 'martin') {
            await addMartinLayer(layer)
          } else {
            await addGeoServerLayer(layer)
          }
        }
        
        //console.log('✅ 场景加载完成:', response.scene?.name)
        
      } catch (error) {
        console.error('加载场景失败:', error)
        ElMessage.error(`加载场景失败: ${error.message}`)
      }
    }
    
    // 添加Martin图层
    const addMartinLayer = async (layer) => {
      
      if (!layer.mvt_url) {
        console.warn('MVT URL不存在，跳过图层:', layer.layer_name)
        return
      }
      
      // 检查地图实例是否存在
      if (!map.value) {
        console.error('地图实例不存在，无法添加Martin图层:', layer.layer_name)
        return
      }

      // 调试 MARTIN_BASE_URL
      //console.log('MARTIN_BASE_URL:', MARTIN_BASE_URL)
      
      // 确保 MARTIN_BASE_URL 有值，如果没有则使用默认值
      const baseUrl = MARTIN_BASE_URL
      
      
      let mvtUrl = layer.mvt_url
      if (mvtUrl.includes('localhost:3000')) {
        // 替换硬编码的URL为配置变量
        
        // 检查是否是 MBTiles 服务
        if (layer.file_type === 'mbtiles' || mvtUrl.includes('/mbtiles/')) {
          const mbtilesMatch = mvtUrl.match(/\/mbtiles\/([^/]+)\/\{z\}/) || []
          const fileName = mbtilesMatch[1] || 'default'
          mvtUrl = `${MARTIN_BASE_URL}/${fileName}/{z}/{x}/{y}`
        } else {
          const tableName = mvtUrl.match(/\/([^/]+)\/\{z\}/)?.[1] || 'default'
          mvtUrl = `${MARTIN_BASE_URL}/${tableName}/{z}/{x}/{y}`
          
        }
      }

      //console.log('lv1-mvtUrl:', mvtUrl)
      let layerStyleConfig = layerStyleCache[layer.id] || {}
      
      // 如果缓存中没有样式配置，尝试从后端获取
      if (Object.keys(layerStyleConfig).length === 0) {
        try {
          console.log('🔄 从后端获取图层样式配置...')
          let savedStyleConfig = null
          
          if (layer.service_type === 'martin' && layer.martin_service_id) {
            // 获取Martin服务样式
            const response = await gisApi.getMartinServiceStyle(layer.martin_service_id)
            if (response?.success && response.data?.style_config) {
              savedStyleConfig = response.data.style_config
              console.log('✅ 获取到Martin服务样式配置:', savedStyleConfig)
            }
          } else {
            // 获取普通图层样式
            const response = await gisApi.getLayerStyle(layer.id)
            if (response?.success && response.data?.style_config) {
              savedStyleConfig = response.data.style_config
              console.log('✅ 获取到图层样式配置:', savedStyleConfig)
            }
          }
          
          if (savedStyleConfig) {
            layerStyleConfig = savedStyleConfig
            // 将样式配置保存到缓存中
            layerStyleCache[layer.id] = savedStyleConfig
          }
        } catch (error) {
          console.error('❌ 获取样式配置失败:', error)
        }
      }
      
      // 如果是DXF文件且没有缓存样式，使用默认DXF样式
      if (layer.file_type === 'dxf' && Object.keys(layerStyleConfig).length === 0) {
        //console.log('使用默认DXF样式配置')
        layerStyleConfig = defaultDxfStylesConfig.defaultDxfStyles
      }
            

      // 创建样式函数 - 重新设计的版本
      const createStyleFunction = () => {
        const isDxf = layer.file_type === 'dxf'
        const defaultStyles = isDxf ? defaultDxfStylesConfig.defaultDxfStyles : {}
        
        // 样式缓存，提高性能
        const styleCache = {}
        
        return (feature) => {
          const properties = feature.getProperties()
          //console.log('properties',properties)
          const geometryType = feature.getGeometry().getType()
          
          // 🔧 解决MVT layer属性冲突问题 - 后端方案
          // 现在在后端ogr2ogr导入时已将DXF的layer字段重命名为cad_layer字段
          // 这样避免了与MVT规范的layer属性（表名）冲突
          
          let dxfLayerName = null
          let useLayerBasedStyle = false
          
          // 查找DXF图层名称 - 现在使用专门的cad_layer字段
          const isDxf = layer.file_type === 'dxf'
          
          // 优先查找cad_layer字段（后端已重命名）
          if (properties.cad_layer && 
              typeof properties.cad_layer === 'string' && 
              properties.cad_layer.trim() !== '') {
            dxfLayerName = properties.cad_layer.trim()
            useLayerBasedStyle = true
            //console.log(`✅ 找到CAD图层名称: "${dxfLayerName}" (来源: cad_layer字段)`)
          }
          // 备用：检查其他可能的字段名（兼容旧数据）
          else if (isDxf) {
            const fallbackFields = ['layer_name', 'dxf_layer', 'subclasses', 'layername', 'entity_layer']
            
            for (const fieldName of fallbackFields) {
              const fieldValue = properties[fieldName]
              
              if (fieldValue && 
                  typeof fieldValue === 'string' && 
                  fieldValue.trim() !== '' &&
                  !fieldValue.includes('vector_') && 
                  !fieldValue.includes('table_') &&
                  !fieldValue.match(/^[a-f0-9]{8,}$/)) {
                    
                dxfLayerName = fieldValue.trim()
                useLayerBasedStyle = true
                //console.log(`⚠️ 使用备用字段获取图层名称: "${dxfLayerName}" (来源: ${fieldName}字段)`)
                break
              }
            }
          }
          
         
          
          // 样式策略1：DXF图层 - 根据是否找到图层名称决定样式方式
          if (isDxf) {
            if (dxfLayerName) {
              // 找到了DXF图层名称，使用图层匹配样式
              const cacheKey = `dxf_layer_${dxfLayerName}_${geometryType}`
              if (styleCache[cacheKey]) {
                return styleCache[cacheKey]
              }
              
              // 获取图层特定样式：优先使用用户自定义样式，其次使用默认样式
              const layerSpecificStyle = layerStyleConfig[dxfLayerName] || defaultStyles[dxfLayerName] || {}
              
              // 如果没有找到匹配的样式配置，使用通用默认样式
              const finalStyle = Object.keys(layerSpecificStyle).length > 0 ? layerSpecificStyle : {
                weight: 1,
                color: '#666666',
                opacity: 0.8,
                fillColor: '#CCCCCC',
                fill: false,
                fillOpacity: 0.3,
                radius: 3,
                visible: true
              }
              
              //console.log(`🎨 使用DXF图层样式: ${dxfLayerName} (${geometryType})`, finalStyle)
              
              let style = createStyleFromConfig(finalStyle, geometryType)
              
              // 处理图层可见性
              if (finalStyle.visible === false) {
                style = new Style({}) // 返回空样式以隐藏
              }
              
              // 缓存样式
              styleCache[cacheKey] = style
              return style
            } else {
              // 没有找到DXF图层名称，使用DXF通用默认样式
              const cacheKey = `dxf_default_${geometryType}`
              if (styleCache[cacheKey]) {
                return styleCache[cacheKey]
              }
              
              // 使用DXF通用默认样式
              const defaultStyle = {
                weight: 1,
                color: '#888888',
                opacity: 0.8,
                fillColor: '#DDDDDD',
                fill: false,
                fillOpacity: 0.3,
                radius: 3,
                visible: true
              }
              
              //console.log(`🎨 使用DXF通用默认样式 (${geometryType})`, defaultStyle)
              
              let style = createStyleFromConfig(defaultStyle, geometryType)
              styleCache[cacheKey] = style
              return style
            }
          }
          
          // 样式策略2：非DXF图层但有图层字段的矢量切片图层 - 使用layer字段匹配样式
          else if (useLayerBasedStyle && dxfLayerName) {
            // 创建缓存键
            const cacheKey = `layer_${dxfLayerName}_${geometryType}`
            if (styleCache[cacheKey]) {
              return styleCache[cacheKey]
            }
            
            // 获取图层特定样式：优先使用用户自定义样式，其次使用默认样式
            const layerSpecificStyle = layerStyleConfig[dxfLayerName] || defaultStyles[dxfLayerName] || {}
            
            // 如果没有找到匹配的样式配置，使用通用默认样式
            const finalStyle = Object.keys(layerSpecificStyle).length > 0 ? layerSpecificStyle : {
              weight: 1,
              color: '#666666',
              opacity: 0.8,
              fillColor: '#CCCCCC',
              fill: false,
              fillOpacity: 0.3,
              radius: 3,
              visible: true
            }
            
            //console.log(`🎨 使用layer字段样式: ${dxfLayerName} (${geometryType})`, finalStyle)
            
            let style = createStyleFromConfig(finalStyle, geometryType)
            
            // 处理图层可见性
            if (finalStyle.visible === false) {
              style = new Style({}) // 返回空样式以隐藏
            }
            
            // 缓存样式
            styleCache[cacheKey] = style
            return style
          }
          
          // 样式策略3：没有layer字段的图层 - 使用基础点线面样式
          else {
            // 创建缓存键
            const cacheKey = `basic_${geometryType}`
            if (styleCache[cacheKey]) {
              return styleCache[cacheKey]
            }
            
            // 获取基础样式配置（从样式面板的表单配置）
            const basicStyles = {
              point: styleForm.point || { color: '#FF0000', size: 2 },
              line: styleForm.line || { color: '#0000FF', width: 2 },
              polygon: styleForm.polygon || { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
            }
            
            //console.log(`🎨 使用基础几何样式: ${geometryType}`, basicStyles)
            
            let style
            if (geometryType === 'Point' || geometryType === 'MultiPoint') {
              style = new Style({
                image: new Circle({
                  radius: basicStyles.point.size || 6,
                  fill: new Fill({
                    color: basicStyles.point.color || '#FF0000'
                  }),
                  stroke: new Stroke({
                    color: '#FFFFFF',
                    width: 1
                  })
                })
              })
            } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
              style = new Style({
                stroke: new Stroke({
                  color: basicStyles.line.color || '#0000FF',
                  width: basicStyles.line.width || 2
                })
              })
            } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
              const fillColor = basicStyles.polygon.fillColor || '#00FF00'
              const fillOpacity = basicStyles.polygon.fillOpacity !== undefined ? basicStyles.polygon.fillOpacity : 0.3
              
              // 转换颜色和透明度
              let finalFillColor = fillColor
              if (fillOpacity !== 1 && fillColor.startsWith('#')) {
                const r = parseInt(fillColor.slice(1, 3), 16)
                const g = parseInt(fillColor.slice(3, 5), 16)
                const b = parseInt(fillColor.slice(5, 7), 16)
                finalFillColor = `rgba(${r}, ${g}, ${b}, ${fillOpacity})`
              }
              
              style = new Style({
                stroke: new Stroke({
                  color: basicStyles.polygon.outlineColor || '#000000',
                  width: 1
                }),
                fill: new Fill({
                  color: finalFillColor
                })
              })
            } else {
              // 默认样式
              style = new Style({
                stroke: new Stroke({
                  color: '#0066cc',
                  width: 2
                }),
                fill: new Fill({
                  color: 'rgba(102, 204, 255, 0.3)'
                }),
                image: new Circle({
                  radius: 4,
                  fill: new Fill({
                    color: '#66ccff'
                  }),
                  stroke: new Stroke({
                    color: '#0066cc',
                    width: 1
                  })
                })
              })
            }
            
            // 缓存样式
            styleCache[cacheKey] = style
            return style
          }
        }
      }
      
      // 样式配置转换为OpenLayers样式的辅助函数
      const createStyleFromConfig = (styleConfig, geometryType) => {
        if (geometryType === 'Point' || geometryType === 'MultiPoint') {
          // 点样式
          return new Style({
            image: new Circle({
              radius: styleConfig.radius || 4,
              fill: new Fill({
                color: styleConfig.fillColor || styleConfig.color || '#66ccff'
              }),
              stroke: new Stroke({
                color: styleConfig.color || '#0066cc',
                width: 1
              })
            })
          })
        } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
          // 线样式
          const dashArray = styleConfig.dashArray
          return new Style({
            stroke: new Stroke({
              color: styleConfig.color || '#0066cc',
              width: styleConfig.weight || 2,
              lineDash: dashArray ? dashArray.split(',').map(Number) : undefined
            })
          })
        } else if (geometryType === 'Polygon' || geometryType === 'MultiPolygon') {
          // 面样式
          const fillColor = styleConfig.fillColor || styleConfig.color || '#66ccff'
          const fillOpacity = styleConfig.fillOpacity !== undefined ? styleConfig.fillOpacity : 0.3
          
          // 转换颜色和透明度
          let finalFillColor = fillColor
          if (fillOpacity !== 1 && fillColor.startsWith('#')) {
            const r = parseInt(fillColor.slice(1, 3), 16)
            const g = parseInt(fillColor.slice(3, 5), 16)
            const b = parseInt(fillColor.slice(5, 7), 16)
            finalFillColor = `rgba(${r}, ${g}, ${b}, ${fillOpacity})`
          }
          
          return new Style({
            stroke: new Stroke({
              color: styleConfig.color || '#0066cc',
              width: styleConfig.weight || 1
            }),
            fill: styleConfig.fill !== false ? new Fill({
              color: finalFillColor
            }) : undefined
          })
        } else {
          // 默认样式
          return new Style({
            stroke: new Stroke({
              color: styleConfig.color || '#0066cc',
              width: styleConfig.weight || 2
            }),
            fill: new Fill({
              color: styleConfig.fillColor || styleConfig.color || '#66ccff'
            }),
            image: new Circle({
              radius: styleConfig.radius || 4,
              fill: new Fill({
                color: styleConfig.fillColor || styleConfig.color || '#66ccff'
              }),
              stroke: new Stroke({
                color: styleConfig.color || '#0066cc',
                width: 1
              })
            })
          })
        }
      }
      
      try {
        // 检查是否为栅格mbtiles
        const isRasterMbtiles = layer.file_type === 'raster.mbtiles' || layer.martin_service_type==='raster.mbtiles';
        //console.log('lv-0728-layer:', layer.martin_service_type)
        let olLayer;
        
        if (isRasterMbtiles) {
          // 创建栅格XYZ图层 - 用于栅格mbtiles
          olLayer = new TileLayer({
            source: new XYZ({
              url: mvtUrl,
              maxZoom: 22,
              minZoom: 0,
              wrapX: false,
              transition: 0,
              attributions: layer.attribution || [],
              cacheSize: 256
            }),
            opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
            visible: layer.visibility !== false,
            zIndex: layer.layer_order || 1,
            properties: {
              layerId: layer.id,
              layerName: layer.layer_name,
              serviceType: 'martin',
              fileType: layer.file_type
            }
          });
          
          //console.log('创建栅格MBTiles图层:', layer.layer_name);
        } else {

          
          // 创建矢量切片图层 - 用于矢量mbtiles和其他矢量数据
          // 创建带缓存功能的MVT瓦片加载函数
          const mvtTileLoadFunction = createMvtTileLoadFunction({
            layerId: layer.id.toString(),
            tileCacheService: tileCacheService,
            enableCacheStorage: layersCacheEnabled.value
          })
          
          olLayer = new VectorTileLayer({
            declutter: true, // 启用标注防冲突
            source: new VectorTile({
              format: new MVT(),
              url: mvtUrl,
              maxZoom: 22, // 最大缩放级别
              minZoom: 0,  // 最小缩放级别
              wrapX: false, // 防止世界重复
              transition: 0, // 禁用过渡动画，提高性能
              // 添加属性信息
              attributions: layer.attribution || [],
              // 设置瓦片缓存大小
              cacheSize: 128,
              // 设置自定义的瓦片加载函数，支持缓存
              tileLoadFunction: mvtTileLoadFunction
            }),
            style: createStyleFunction(),
            opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
            visible: layer.visibility !== false,
            // 设置渲染顺序
            zIndex: layer.layer_order || 1,
            // 添加图层标识
            properties: {
              layerId: layer.id,
              layerName: layer.layer_name,
              serviceType: 'martin',
              fileType: layer.file_type
            }
          });
          
          console.log('创建矢量MBTiles图层 (带缓存):', layer.layer_name, '缓存状态:', layersCacheEnabled.value ? '开启' : '关闭');
        }
        
        // 使用统一变量名
        const mvtLayer = olLayer;
        
        // 启用弹窗交互
        mvtLayer._popupEnabled = true
        mvtLayer._layerInfo = layer
        
        // 存储图层引用
        mvtLayers.value[layer.id] = mvtLayer
        
        // 添加到地图（如果图层可见）
        if (layer.visibility !== false && map.value) {
          map.value.addLayer(mvtLayer)
          //console.log('✅ MVT图层添加成功:', layer.layer_name)
        }
        
        // 添加图层事件监听 - 改进版本
        const source = mvtLayer.getSource()
        
        // 瓦片加载错误处理
        source.on('tileloaderror', (evt) => {
          console.warn('MVT瓦片加载失败:', evt.tile.src_)
          console.warn('错误详情:', evt)
          
          // 可以在这里添加重试逻辑
          if (evt.tile.getState() === 3) { // ERROR state
            setTimeout(() => {
              //console.log('重试加载MVT瓦片:', evt.tile.src_)
              evt.tile.load()
            }, 1000)
          }
        })
        
        // 瓦片加载成功
        source.on('tileloadend', (evt) => {
          //console.log('MVT瓦片加载完成:', evt.tile.src_)
        })
        
        // 瓦片开始加载
        source.on('tileloadstart', (evt) => {
          console.debug('MVT瓦片开始加载:', evt.tile.src_)
        })
        
        // 监听源变化
        source.on('change', () => {
          console.debug('MVT源状态变化:', source.getState())
        })
        
        return mvtLayer
        
      } catch (error) {
        console.error('创建MVT图层失败:', error)
        console.error('错误详情:', {
          layerName: layer.layer_name,
          mvtUrl: mvtUrl,
          error: error.message,
          stack: error.stack
        })
        ElMessage.error(`MVT图层创建失败: ${layer.layer_name} - ${error.message}`)
        throw error
      }
    }
    
    // 添加GeoServer图层
    const addGeoServerLayer = async (layer) => {
      if (!layer.wms_url || !layer.geoserver_layer) {
        console.warn('WMS URL或图层名称不存在，跳过图层:', layer.layer_name)
        return
      }
      
      // 检查地图实例是否存在
      if (!map.value) {
        console.error('地图实例不存在，无法添加GeoServer图层:', layer.layer_name)
        return
      }
      
      // 处理WMS URL - 将所有 GeoServer URL 转换为使用代理路径，避免 CORS 问题
      let wmsUrl = layer.wms_url.split('?')[0]
      // 使用工具函数转换 GeoServer URL 为代理路径
      wmsUrl = convertGeoServerUrlToProxy(wmsUrl)
      
      //console.log('创建WMS图层:', layer.layer_name, 'URL:', wmsUrl)
      
      // 获取图层坐标系信息
      let layerCRS = 'EPSG:4326' // 默认坐标系
      let wmsVersion = '1.1.1' // 默认版本
      let crsParam = 'SRS' // 默认使用SRS参数
      
      try {
        // 确保坐标系已初始化
        //await initializeProjections()
        // 尝试获取图层的坐标系信息
        if (layer.layer_id) {
          const response = await gisApi.getLayerCRSInfo(layer.layer_id)
          if (response.success && response.crs_info) {
            layerCRS = response.crs_info.epsg_code || layerCRS
            //console.log(`✅ 获取到图层坐标系: ${layerCRS}`)
            
            // 动态注册坐标系（如果需要）
            if (response.crs_info.proj4_definition) {
              //console.log(`🔄 动态注册坐标系: ${layerCRS}`)
              proj4.defs(layerCRS, response.crs_info.proj4_definition)
              register(proj4)
              //console.log(`✅ 坐标系注册完成: ${layerCRS}`)
            }
            
            // 使用推荐的WMS版本
            wmsVersion = response.crs_info.recommended_wms_version || wmsVersion
          }
        }
        
        // 根据坐标系调整WMS参数
        if (layerCRS.startsWith('EPSG:')) {
          // 对于投影坐标系，使用WMS 1.1.0和SRS参数
          if (!layerCRS.includes('4326') && !layerCRS.includes('3857')) {
            wmsVersion = '1.1.0'
            crsParam = 'SRS'
          } else {
            // 对于地理坐标系，使用WMS 1.1.1和SRS参数
            wmsVersion = '1.1.1'
            crsParam = 'SRS'
          }
        }
        
      } catch (error) {
        console.warn('获取图层坐标系失败，使用默认值:', error.message)
      }
      
      try {
        // 构建WMS参数
        const wmsParams = {
          'LAYERS': layer.geoserver_layer,
          'FORMAT': 'image/png',
          'TRANSPARENT': true,
          'VERSION': wmsVersion,
          'STYLES': '',
          'TILED': true
        }
        
        // 设置坐标系参数
        wmsParams[crsParam] = layerCRS
        //console.log('lv-projection:', wmsParams)
        const wmsLayer = new TileLayer({
          source: new TileWMS({
            url: wmsUrl,
            params: wmsParams,
            projection: layerCRS, // 明确指定WMS源数据的投影
            serverType: 'geoserver'
          }),
          opacity: typeof layer.opacity === 'number' ? layer.opacity : 1.0,
          visible: layer.visibility !== false,
          zIndex: layer.layer_order || 1,
          // 添加图层标识
          properties: {
            layerId: layer.id,
            layerName: layer.layer_name,
            serviceType: 'geoserver'
          }
        })
        
        // 存储图层引用
        mapLayers.value[layer.id] = wmsLayer
        
        // 添加到地图（如果图层可见）
        if (layer.visibility !== false) {
          map.value.addLayer(wmsLayer)
          //console.log(`✅ WMS图层添加成功: ${layer.layer_name} (坐标系: ${layerCRS})`)
        }
        
      } catch (error) {
        console.error('创建WMS图层失败:', error)
        ElMessage.error(`WMS图层创建失败: ${layer.layer_name}`)
      }
    }
    
    // 清除所有图层
    const clearAllLayers = () => {
      if (!map.value) {
        console.warn('地图实例不存在，无法清除图层')
        // 清空图层引用即可
        mapLayers.value = {}
        mvtLayers.value = {}
        return
      }
      
      try {
        Object.values(mapLayers.value).forEach(layer => {
          if (layer && map.value) {
            map.value.removeLayer(layer)
          }
        })
        Object.values(mvtLayers.value).forEach(layer => {
          if (layer && map.value) {
            map.value.removeLayer(layer)
          }
        })
        
        // 清空图层引用
        mapLayers.value = {}
        mvtLayers.value = {}
        
        //console.log('✅ 所有图层已清除')
      } catch (error) {
        console.error('清除图层时出错:', error)
        // 强制清空引用
        mapLayers.value = {}
        mvtLayers.value = {}
      }
    }

    // 刷新所有图层
    const refreshAllLayers = async () => {
      if (!map.value) {
        ElMessage.warning('地图未初始化')
        return
      }

      if (!props.sceneId) {
        ElMessage.warning('没有选中的场景')
        return
      }

      refreshing.value = true
      
      try {
        // 保存当前地图视口
        const currentView = map.value.getView()
        const currentCenter = currentView.getCenter()
        const currentZoom = currentView.getZoom()
        const currentRotation = currentView.getRotation()
        
        

        // 重新加载场景
        await loadScene(props.sceneId)

        // 恢复地图视口
        if (currentCenter && currentZoom !== undefined) {
          map.value.getView().setCenter(currentCenter)
          map.value.getView().setZoom(currentZoom)
          if (currentRotation !== undefined) {
            map.value.getView().setRotation(currentRotation)
          }
          //console.log('✅ 视口已恢复')
        }

        ElMessage.success('图层刷新成功')
        
      } catch (error) {
        console.error('刷新图层失败:', error)
        ElMessage.error(`刷新图层失败: ${error.message}`)
      } finally {
        refreshing.value = false
      }
    }
    
    // 切换图层可见性
    const toggleLayerVisibility = (layer) => {
      const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
      if (!targetLayer) return
      
      if (layer.visibility) {
        map.value.addLayer(targetLayer)
      } else {
        map.value.removeLayer(targetLayer)
      }
      
      updateLayerVisibility(layer.id, layer.visibility)
    }
    
    // 更新图层可见性到服务器
    const updateLayerVisibility = async (layerId, visibility) => {
      if (props.readonly) return
      await gisApi.updateSceneLayer(props.sceneId, layerId, { visibility })
    }

    // 🔥 更新图层透明度
    const updateLayerOpacity = (layer, opacity) => {
      console.log('🎯 更新图层透明度:', layer.layer_name, '透明度:', opacity)
      
      // 确保透明度在有效范围内
      const normalizedOpacity = Math.max(0, Math.min(1, opacity))
      
      // 根据服务类型获取对应的图层对象
      const targetLayer = layer.service_type === 'martin' 
        ? mvtLayers.value[layer.id] 
        : mapLayers.value[layer.id]
      
      if (!targetLayer) {
        console.warn('❌ 未找到图层对象:', layer.id, layer.service_type)
        return
      }
      
      // 设置图层透明度
      if (targetLayer.setOpacity) {
        targetLayer.setOpacity(normalizedOpacity)
        console.log('✅ 图层透明度已更新:', layer.layer_name, normalizedOpacity)
      } else {
        console.warn('❌ 图层对象不支持setOpacity方法:', layer.id)
      }
    }
    
    // 显示样式设置对话框
    const showStyleDialog = async (layer) => {
      //console.log('=== showStyleDialog 被调用 ===')
      //console.log('传入的 layer 参数:', layer)
      //console.log('layer 完整对象:', JSON.stringify(layer, null, 2))
      
      emit('layer-selected', layer)
      currentStyleLayer.value = layer
      
      // 调试 isDxfMartinLayer 计算
      //console.log('计算 isDxfMartinLayer:')
      //console.log('  service_type:', currentStyleLayer.value?.service_type)
      //console.log('  file_type:', currentStyleLayer.value?.file_type)
      //console.log('  martin_service_id:', currentStyleLayer.value?.martin_service_id)
      //console.log('  Boolean(martin_service_id):', Boolean(currentStyleLayer.value?.martin_service_id))
      
      const isDxfResult = currentStyleLayer.value?.service_type === 'martin' && 
                         currentStyleLayer.value?.file_type === 'dxf' && 
                         Boolean(currentStyleLayer.value?.martin_service_id)
      //console.log('  最终计算结果:', isDxfResult)
      
      activeStyleTab.value = isDxfResult ? 'dxf' : 'basic'
      
      //console.log('设置后的状态:')
      //console.log('currentStyleLayer.value:', currentStyleLayer.value)
      //console.log('activeStyleTab.value:', activeStyleTab.value)
      //console.log('isDxfMartinLayer.value:', isDxfMartinLayer.value)
      
      // 从后端获取保存的样式配置
      try {
        let savedStyleConfig = null
        
        console.log('🔍 开始获取图层样式配置...')
        console.log('图层信息:', {
          id: currentStyleLayer.value.id,
          name: currentStyleLayer.value.layer_name,
          service_type: currentStyleLayer.value.service_type,
          file_type: currentStyleLayer.value.file_type,
          martin_service_id: currentStyleLayer.value.martin_service_id
        })
        
        if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
          // 获取Martin服务样式
          console.log('📡 获取Martin服务样式...')
          const response = await gisApi.getMartinServiceStyle(currentStyleLayer.value.martin_service_id)
          console.log('Martin服务样式响应:', response)
          
          if (response?.success && response.data?.style_config) {
            savedStyleConfig = response.data.style_config
            console.log('✅ 获取到Martin服务样式配置:', savedStyleConfig)
          } else {
            console.log('⚠️ Martin服务样式响应格式异常:', response)
          }
        } else {
          // 获取普通图层样式
          console.log('📡 获取普通图层样式...')
          const response = await gisApi.getLayerStyle(currentStyleLayer.value.id)
          console.log('普通图层样式响应:', response)
          
          if (response?.success && response.data?.style_config) {
            savedStyleConfig = response.data.style_config
            console.log('✅ 获取到图层样式配置:', savedStyleConfig)
          } else {
            console.log('⚠️ 普通图层样式响应格式异常:', response)
          }
        }
        
        // 如果有保存的样式配置，使用它；否则使用默认值
        if (savedStyleConfig) {
          console.log('✅ 从后端获取到保存的样式配置:', savedStyleConfig)
          
          // 更新样式表单
          if (savedStyleConfig.point) {
            styleForm.point = { 
              color: savedStyleConfig.point.color || '#FF0000', 
              size: savedStyleConfig.point.size || 6 
            }
          } else {
            styleForm.point = { color: '#FF0000', size: 6 }
          }
          
          if (savedStyleConfig.line) {
            styleForm.line = { 
              color: savedStyleConfig.line.color || '#0000FF', 
              width: savedStyleConfig.line.width || 2 
            }
          } else {
            styleForm.line = { color: '#0000FF', width: 2 }
          }
          
          if (savedStyleConfig.polygon) {
            styleForm.polygon = { 
              fillColor: savedStyleConfig.polygon.fillColor || '#00FF00', 
              fillOpacity: savedStyleConfig.polygon.fillOpacity !== undefined ? savedStyleConfig.polygon.fillOpacity : 0.3, 
              outlineColor: savedStyleConfig.polygon.outlineColor || '#000000' 
            }
          } else {
            styleForm.polygon = { fillColor: '#00FF00', fillOpacity: 0.3, outlineColor: '#000000' }
          }
          
          if (savedStyleConfig.raster) {
            styleForm.raster = { opacity: savedStyleConfig.raster.opacity !== undefined ? savedStyleConfig.raster.opacity : 1 }
          } else {
            styleForm.raster = { opacity: 1 }
          }
          
          // 将样式配置保存到缓存中
          layerStyleCache[currentStyleLayer.value.id] = savedStyleConfig
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
      //console.log('styleDialogVisible 设置为 true')
      //console.log('================================')
    }
    
    // 应用样式
    const applyStyle = async () => {
      if (!currentStyleLayer.value) return
      
      const styleConfig = isVectorLayer.value 
        ? { point: { ...styleForm.point }, line: { ...styleForm.line }, polygon: { ...styleForm.polygon } }
        : { raster: { ...styleForm.raster } }
      
      // 将样式配置保存到缓存中，供重新加载图层时使用
      layerStyleCache[currentStyleLayer.value.id] = styleConfig
      console.log('lv-styleConfig:', styleConfig)
      try {
        if (currentStyleLayer.value.service_type === 'martin' && currentStyleLayer.value.martin_service_id) {
          // Martin服务样式更新
          await gisApi.updateMartinServiceStyle(currentStyleLayer.value.martin_service_id, styleConfig)
          
          // 重新加载Martin图层
          const mvtLayer = mvtLayers.value[currentStyleLayer.value.id]
          if (mvtLayer) {
            map.value.removeLayer(mvtLayer)
            delete mvtLayers.value[currentStyleLayer.value.id]
            await addMartinLayer(currentStyleLayer.value)
          }
        } else {
          // GeoServer图层样式更新
          await gisApi.updateLayerStyle(currentStyleLayer.value.id, styleConfig)
          
          // 对于GeoServer WMS图层，需要特殊处理
          if (currentStyleLayer.value.service_type === 'geoserver') {
            const wmsLayer = mapLayers.value[currentStyleLayer.value.id]
            if (wmsLayer) {
              // 获取WMS源
              const wmsSource = wmsLayer.getSource()
              if (wmsSource) {
                // 检查是否修改了点样式（这需要SLD支持）
                const hasPointStyleChanges = styleConfig.point && (
                  styleConfig.point.color !== undefined || 
                  styleConfig.point.size !== undefined
                )
                
                if (hasPointStyleChanges) {
                  // 点样式修改需要重新加载图层，因为WMS不支持动态点样式
                  console.log('⚠️ 检测到点样式修改，需要重新加载WMS图层')
                  map.value.removeLayer(wmsLayer)
                  delete mapLayers.value[currentStyleLayer.value.id]
                  await addGeoServerLayer(currentStyleLayer.value)
                } else {
                  // 其他样式修改（透明度等）可以直接更新
                  const currentParams = wmsSource.getParams()
                  const newParams = {
                    ...currentParams,
                    // 添加时间戳参数强制刷新
                    '_t': Date.now()
                  }
                  wmsSource.updateParams(newParams)
                  
                  // 如果修改了透明度，直接更新图层透明度
                  if (styleConfig.raster && styleConfig.raster.opacity !== undefined) {
                    wmsLayer.setOpacity(styleConfig.raster.opacity)
                  }
                  
                  console.log('✅ GeoServer WMS图层样式已更新')
                }
              }
            }
          } else {
            // 其他类型的图层，重新加载
            const wmsLayer = mapLayers.value[currentStyleLayer.value.id]
            if (wmsLayer) {
              map.value.removeLayer(wmsLayer)
              delete mapLayers.value[currentStyleLayer.value.id]
              await addGeoServerLayer(currentStyleLayer.value)
            }
          }
        }
        
        ElMessage.success('样式应用成功')
      } catch (error) {
        console.error('❌ 应用样式失败:', error)
        ElMessage.error('样式应用失败: ' + (error.message || '未知错误'))
      }
      
      styleDialogVisible.value = false
    }
    
    // 显示添加图层对话框
    const showAddLayerDialog = async () => {
      if (!props.sceneId) return
      addLayerDialogVisible.value = true
      // 移动端默认展开搜索
      if (isMobile.value) {
        mobileLayerSearchExpanded.value = false
      }
      await fetchAvailableLayers()
    }
    
    // 获取可用图层
    const fetchAvailableLayers = async () => {
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
    }
    
    // 搜索图层
    const searchLayers = () => fetchAvailableLayers()
    
    // 重置图层搜索
    const resetLayerSearch = () => {
      layerSearchForm.service_type = ''
      layerSearchForm.discipline = ''
      layerSearchForm.file_type = ''
      fetchAvailableLayers()
    }
    
    // 切换移动端图层搜索展开状态
    const toggleMobileLayerSearch = () => {
      mobileLayerSearchExpanded.value = !mobileLayerSearchExpanded.value
    }
    
    // 检查是否有激活的图层筛选条件
    const hasActiveLayerFilters = computed(() => {
      return layerSearchForm.service_type || layerSearchForm.discipline || layerSearchForm.file_type
    })
    
    // 获取激活图层筛选条件的文字描述
    const getActiveLayerFiltersText = () => {
      const filters = []
      if (layerSearchForm.service_type) filters.push('服务')
      if (layerSearchForm.discipline) filters.push('专业')
      if (layerSearchForm.file_type) filters.push('类型')
      return filters.length > 0 ? `${filters.join('+')}` : ''
    }
    
    // 格式化文件大小
    const formatFileSize = (size) => {
      if (!size) return '-'
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB'
      return (size / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour12: false })
    }
    
    // 检查图层是否已在场景中
    const isLayerInScene = (fileId, serviceType) => layersList.value.some(layer => layer.file_id === fileId && layer.service_type === serviceType)
    
    // 检查文件是否有任何已发布的服务
    const hasAnyPublishedService = (file) => (file.geoserver_service?.is_published) || (file.martin_service?.is_published)
    
    // 添加图层到场景
    const addLayerToScene = async (file, serviceType) => {
      try {
        if (!props.sceneId) {
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
        //const jsonbig=require('json-bigint')({ storeAsString: true })
        if (serviceType === 'martin') {
          const martinServices = await gisApi.searchMartinServices({ file_id: serviceInfo.file_id })
          
          const martinService = martinServices.data.services.find(service => service.file_id === serviceInfo.file_id)
          
          if (!martinService) {
            ElMessage.error('未找到对应的Martin服务')
            return
          }
          
          layerData = {
            ...layerData,
            layer_id: String(martinService.database_record_id || martinService.id),  // 转换为字符串
            martin_service_id: String(martinService.database_record_id || martinService.id),  // 转换为字符串
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
            layer_id: String(geoserverLayerId),  // 转换为字符串
            geoserver_layer_name: serviceInfo.layer_name,
            wms_url: serviceInfo.wms_url,
            wfs_url: serviceInfo.wfs_url
          }
        }
        
        await gisApi.addLayerToScene(props.sceneId, layerData)
        
        ElMessage.success(`图层 "${file.file_name}" 添加成功`)
        
        addLayerDialogVisible.value = false
        await loadScene(props.sceneId)
        emit('layerAdded', { sceneId: props.sceneId, layerData })
        
      } catch (error) {
        const errorMessage = error.response?.data?.error || error.message || '添加图层失败'
        ElMessage.error(`添加图层失败: ${errorMessage}`)
      }
    }
    
    // 移除图层
    const removeLayer = async (layer) => {
      await gisApi.removeLayerFromScene(props.sceneId, layer.id)
      
      const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
      if (targetLayer) {
        map.value.removeLayer(targetLayer)
        if (layer.service_type === 'martin') {
          delete mvtLayers.value[layer.id]
        } else {
          delete mapLayers.value[layer.id]
        }
      }
      
      layersList.value = layersList.value.filter(item => item.id !== layer.id)
    }
    
    // 底图切换处理
    const onBaseMapChanged = (baseMapType) => {
      //console.log('切换底图到:', baseMapType)
      // 更新版权信息
      updateBaseMapAttribution(baseMapType)
    }
    
    // 设置当前活动图层
    const setActiveLayer = (layer) => {
      currentActiveLayer.value = layer
      emit('layer-selected', layer)
    }
    
    // 将图层置顶
    const bringLayerToTop = (layer) => {
      currentActiveLayer.value = layer
      emit('layer-selected', layer)
      
      if (layer.service_type === 'martin') {
        const mvtLayer = mvtLayers.value[layer.id]
        if (mvtLayer) {
          map.value.removeLayer(mvtLayer)
          map.value.addLayer(mvtLayer)
          mvtLayer._popupEnabled = true
        }
      } else {
        const wmsLayer = mapLayers.value[layer.id]
        if (wmsLayer) {
          map.value.removeLayer(wmsLayer)
          map.value.addLayer(wmsLayer)
        }
      }
    }
    
    // DXF样式更新处理
    const onDxfStylesUpdated = async (styleData) => {
      //console.log('接收到DXF样式更新:', styleData)
      
      if (!currentStyleLayer.value || currentStyleLayer.value.service_type !== 'martin') {
        console.warn('当前图层不是Martin图层，无法应用DXF样式')
        return
      }
      
      // 动态应用样式到图层
      await applyDxfStylesToLayer(currentStyleLayer.value, styleData.allStyles || { [styleData.layerName]: styleData.style })
    }
    
    // 应用DXF样式到图层
    const applyDxfStylesToLayer = async (layer, styleConfig) => {
      if (!layer || !layer.martin_service_id || !styleConfig) {
        console.warn('参数不完整，无法应用DXF样式')
        return
      }
      
      try {
        //console.log('应用DXF样式到图层:', layer.layer_name, styleConfig)
        
        // 获取现有的MVT图层
        const existingMvtLayer = mvtLayers.value[layer.id]
        
        if (existingMvtLayer) {
          // 移除现有图层
          map.value.removeLayer(existingMvtLayer)
          delete mvtLayers.value[layer.id]
          
          // 缓存样式配置
          layerStyleCache[layer.id] = styleConfig
          
          // 重新创建并添加图层
          await addMartinLayer(layer)
          
          //console.log('DXF样式已应用到图层:', layer.layer_name)
        } else {
          console.warn('未找到要更新样式的MVT图层:', layer.layer_name)
        }
      } catch (error) {
        console.error('应用DXF样式失败:', error)
        ElMessage.error('应用DXF样式失败: ' + error.message)
      }
    }
    
    // 应用并保存DXF样式
    const applyAndSaveDxfStyles = async () => {
      if (!dxfStyleEditorRef.value) return
      
      savingDxfStyles.value = true
      const success = await dxfStyleEditorRef.value.saveStylesToDatabase()
      
      if (success) {
        styleDialogVisible.value = false
        ElMessage.success('DXF样式已保存')
      }
      savingDxfStyles.value = false
    }
    
    // 处理属性弹窗控制
    const onPopupControlChanged = (controlData) => {
      const { enabled, layerId } = controlData
      const mvtLayer = mvtLayers.value[layerId]
      if (mvtLayer) {
        mvtLayer._popupEnabled = enabled
        if (!enabled && popup.value) {
          popup.value.setPosition(undefined)
        }
      }
    }

    // SLD样式应用处理
    const onSldStyleApplied = async (styleData) => {
      console.log('SLD样式已应用:', styleData)
      ElMessage.success('SLD样式应用成功')
      
      // 刷新地图图层以显示新的样式
      await refreshMapLayers()
    }

    // SLD样式移除处理
    const onSldStyleRemoved = async () => {
      console.log('SLD样式已移除')
      ElMessage.success('SLD样式移除成功')
      
      // 刷新地图图层以显示默认样式
      await refreshMapLayers()
    }

    // 获取图层几何类型
    const getLayerGeometryType = (layer) => {
      // 根据图层类型和属性判断几何类型
      if (layer.geometry_type) {
        return layer.geometry_type.toLowerCase()
      }
      
      // 根据图层名称或其他属性推断
      const layerName = layer.name?.toLowerCase() || ''
      if (layerName.includes('point') || layerName.includes('点')) {
        return 'point'
      } else if (layerName.includes('line') || layerName.includes('线')) {
        return 'line'
      } else if (layerName.includes('polygon') || layerName.includes('面')) {
        return 'polygon'
      }
      
      // 默认返回空字符串，让用户手动选择
      return ''
    }

    // 刷新地图图层
    const refreshMapLayers = async () => {
      try {
        // 重新加载当前场景的图层
        if (currentScene.value) {
          await loadScene(currentScene.value.id)
        }
        ElMessage.success('地图图层已刷新')
      } catch (error) {
        console.error('刷新地图图层失败:', error)
        ElMessage.error('刷新地图图层失败')
      }
    }

    /* // 添加地图点击事件处理
    const setupMapClickEvents = () => {
      map.value.on('singleclick', (evt) => {
        const coordinate = evt.coordinate
        const pixel = evt.pixel

        // 检查是否点击了MVT图层
        map.value.forEachFeatureAtPixel(pixel, (feature, layer) => {
          // 找到对应的图层数据
          const layerData = Object.values(mvtLayers.value).find(mvtLayer => mvtLayer === layer)
          if (layerData && layerData._popupEnabled) {
            const layerInfo = layersList.value.find(l => mvtLayers.value[l.id] === layer)
            if (layerInfo) {
              currentActiveLayer.value = layerInfo
              emit('layer-selected', layerInfo)
              
              const properties = feature.getProperties()
              const content = Object.entries(properties)
                .filter(([, value]) => value != null && value !== 'NULL' && value !== '')
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br/>')
              
              const popupContent = `<h4>${layerInfo.layer_name}</h4>${content || '无属性信息'}`
              document.getElementById('popup-content').innerHTML = popupContent
              popup.value.setPosition(coordinate)
              
              return true // 停止进一步检查
            }
          }
        })
      })
    } */
    
    // 监听sceneId变化
    watch(() => props.sceneId, (newValue, oldValue) => {
      if (newValue && newValue !== oldValue && map.value) {
        setTimeout(() => loadScene(newValue), 100)
      }
    })
    
    // 获取图层坐标系信息
    const getLayerCRSInfo = async (layer) => {
      try {
        if (layer.file_id) {
          const response = await gisApi.getLayerCRSInfo(layer.file_id)
          if (response.success && response.crs_info) {
            return {
              epsgCode: response.crs_info.epsg_code || 'EPSG:4326',
              proj4Def: response.crs_info.proj4_definition || null,
              name: response.crs_info.name || '未知坐标系'
            }
          }
        }
        
        // 从图层属性中获取
        const targetLayer = layer.service_type === 'martin' ? mvtLayers.value[layer.id] : mapLayers.value[layer.id]
        if (targetLayer && targetLayer.get('properties')) {
          const props = targetLayer.get('properties')
          return {
            epsgCode: props.originalCRS || 'EPSG:4326',
            proj4Def: null,
            name: props.originalCRS || 'EPSG:4326'
          }
        }
        
        return {
          epsgCode: 'EPSG:4326',
          proj4Def: null,
          name: 'WGS84'
        }
      } catch (error) {
        console.warn('获取图层坐标系信息失败:', error.message)
        return {
          epsgCode: 'EPSG:4326',
          proj4Def: null,
          name: 'WGS84 (默认)'
        }
      }
    }
    
    // 坐标转换辅助函数
    const transformCoordinates = (coordinates, fromCRS, toCRS) => {
      try {
        if (fromCRS === toCRS) {
          return coordinates
        }
        
        // 如果是范围（4个数值），使用transformExtent
        if (Array.isArray(coordinates) && coordinates.length === 4) {
          return transformExtent(coordinates, fromCRS, toCRS)
        }
        
        // 如果是点坐标（2个数值），使用transform
        if (Array.isArray(coordinates) && coordinates.length === 2) {
          return transform(coordinates, fromCRS, toCRS)
        }
        
        return coordinates
      } catch (error) {
        console.error(`坐标转换失败: ${fromCRS} -> ${toCRS}`, error)
        return coordinates
      }
    }

    // 初始化坐标跟踪功能
    const initializeCoordinateTracking = () => {
      if (!map.value) return
      
      // 监听鼠标移动事件，更新坐标信息
      map.value.on('pointermove', function(evt) {
        if (evt.dragging) return
        
        // 获取屏幕坐标对应的地理坐标
        const coordinate = evt.coordinate
        
        // 转换为经纬度（WGS84）
        const lonLatCoord = transform(coordinate, 'EPSG:3857', 'EPSG:4326')
        
        // 更新坐标显示（保留6位小数）
        mouseCoordinates.value = {
          lon: Number(lonLatCoord[0]).toFixed(6),
          lat: Number(lonLatCoord[1]).toFixed(6)
        }
      })
      
      // 当鼠标离开地图区域时清除坐标显示
      map.value.on('pointerleave', function() {
        mouseCoordinates.value = null
      })
    }

    // 更新底图版权信息
    const updateBaseMapAttribution = (baseMapType) => {
      const attributions = {
        'gaode': '© 高德地图',
        'gaodeSatellite': '© 高德地图',
        'osm': '© OpenStreetMap contributors',
        'esriSatellite': '© Esri, Maxar, Earthstar Geographics'
      }
      
      currentBaseMapAttribution.value = attributions[baseMapType] || ''
    }
    
    // 切换底图缓存开关
    const toggleLayersCache = () => {
      layersCacheEnabled.value = !layersCacheEnabled.value
      
      // 重新设置所有底图的 tileLoadFunction
      if (map.value && map.value.baseLayers) {
        const baseLayers = map.value.baseLayers
        
        // 高德地图
        if (baseLayers.gaode) {
          const gaodeSource = baseLayers.gaode.getSource()
          if (gaodeSource && gaodeSource.setTileLoadFunction) {
            const wmtsTileLoadFunction_gaode = createWmtsTileLoadFunction({
              layerId: 'gaode',
              tileCacheService: tileCacheService,
              enableCacheStorage: layersCacheEnabled.value
            })
            gaodeSource.setTileLoadFunction(wmtsTileLoadFunction_gaode)
          }
        }
        
        // 高德卫星图
        if (baseLayers.gaodeSatellite) {
          const gaodeSatelliteSource = baseLayers.gaodeSatellite.getSource()
          if (gaodeSatelliteSource && gaodeSatelliteSource.setTileLoadFunction) {
            const wmtsTileLoadFunction_gaodeSatellite = createWmtsTileLoadFunction({
              layerId: 'gaodeSatellite',
              tileCacheService: tileCacheService,
              enableCacheStorage: layersCacheEnabled.value
            })
            gaodeSatelliteSource.setTileLoadFunction(wmtsTileLoadFunction_gaodeSatellite)
          }
        }
        
        // OSM
        if (baseLayers.osm) {
          const osmSource = baseLayers.osm.getSource()
          if (osmSource && osmSource.setTileLoadFunction) {
            const wmtsTileLoadFunction_osm = createWmtsTileLoadFunction({
              layerId: 'osm',
              tileCacheService: tileCacheService,
              enableCacheStorage: layersCacheEnabled.value
            })
            osmSource.setTileLoadFunction(wmtsTileLoadFunction_osm)
          }
        }
        
        // Esri卫星图
        if (baseLayers.esriSatellite) {
          const esriSatelliteSource = baseLayers.esriSatellite.getSource()
          if (esriSatelliteSource && esriSatelliteSource.setTileLoadFunction) {
            const wmtsTileLoadFunction_esriSatellite = createWmtsTileLoadFunction({
              layerId: 'esriSatellite',
              tileCacheService: tileCacheService,
              enableCacheStorage: layersCacheEnabled.value
            })
            esriSatelliteSource.setTileLoadFunction(wmtsTileLoadFunction_esriSatellite)
          }
        }
      }
      
      // 重新设置所有MVT图层的 tileLoadFunction
      if (mvtLayers.value && Object.keys(mvtLayers.value).length > 0) {
        Object.entries(mvtLayers.value).forEach(([layerId, mvtLayer]) => {
          try {
            if (mvtLayer && mvtLayer.getSource) {
              const source = mvtLayer.getSource()
              if (source && source.setTileLoadFunction) {
                // 为MVT图层创建新的瓦片加载函数
                const mvtTileLoadFunction = createMvtTileLoadFunction({
                  layerId: layerId,
                  tileCacheService: tileCacheService,
                  enableCacheStorage: layersCacheEnabled.value
                })
                source.setTileLoadFunction(mvtTileLoadFunction)
                console.log(`MVT图层 ${layerId} 缓存状态已更新:`, layersCacheEnabled.value ? '开启' : '关闭')
              }
            }
          } catch (error) {
            console.error(`更新MVT图层 ${layerId} 缓存状态失败:`, error)
          }
        })
      }
      
      console.log('图层缓存状态已切换:', layersCacheEnabled.value ? '开启' : '关闭')
      console.log('已更新底图缓存:', Object.keys(map.value?.baseLayers || {}).length, '个')
      console.log('已更新MVT图层缓存:', Object.keys(mvtLayers.value || {}).length, '个')
    }
    
    // 创建用户位置图层
    const createUserLocationLayer = () => {
      if (userLocationLayer.value) {
        return userLocationLayer.value
      }
      
      const vectorSource = new VectorSource()
      const vectorLayer = new VectorLayer({
        source: vectorSource,
        style: new Style({
          image: new Circle({
            radius: 8,
            fill: new Fill({ color: '#409EFF' }),
            stroke: new Stroke({ color: '#ffffff', width: 2 })
          })
        }),
        zIndex: 1000
      })
      
      userLocationLayer.value = vectorLayer
      return vectorLayer
    }
    
    // 获取用户位置
    const getUserLocation = () => {
      return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('此浏览器不支持地理位置定位'))
          return
        }
        
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy
            })
          },
          (error) => {
            let message = '获取位置失败'
            switch (error.code) {
              case error.PERMISSION_DENIED:
                message = '用户拒绝了位置访问权限'
                break
              case error.POSITION_UNAVAILABLE:
                message = '位置信息不可用'
                break
              case error.TIMEOUT:
                message = '获取位置超时'
                break
            }
            reject(new Error(message))
          },
          {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 60000
          }
        )
      })
    }
    
    // 显示用户位置
    const showUserLocation = async () => {
      try {
        locationLoading.value = true
        
        // 获取用户位置
        const location = await getUserLocation()
        
        // 浏览器获取的是WGS84坐标，在高德地图上显示需要转换为GCJ02坐标
        const gcj02Coords = gcj02.toWGS84([location.longitude, location.latitude])
        console.log('原始GPS坐标(WGS84):', [location.longitude, location.latitude])
        console.log('转换后高德坐标(GCJ02):', gcj02Coords)
        const userCoords = fromLonLat(gcj02Coords)
        // 创建位置图层（如果不存在）
        const locationLayer = createUserLocationLayer()
        
        // 如果地图中没有位置图层，添加它
        if (!map.value.getLayers().getArray().includes(locationLayer)) {
          map.value.addLayer(locationLayer)
        }
        
        // 创建位置点特征
        if (userLocationFeature.value) {
          locationLayer.getSource().removeFeature(userLocationFeature.value)
        }
        
        userLocationFeature.value = new Feature({
          geometry: new Point(userCoords),
          name: '我的位置'
        })
        
        locationLayer.getSource().addFeature(userLocationFeature.value)
        
        // 缩放到用户位置
        map.value.getView().animate({
          center: userCoords,
          zoom: 16,
          duration: 1000
        })
        
        userLocationVisible.value = true
        ElMessage.success('已定位到您的位置')
        
      } catch (error) {
        console.error('获取位置失败:', error)
        ElMessage.error(error.message || '获取位置失败')
      } finally {
        locationLoading.value = false
      }
    }
    
    // 隐藏用户位置
    const hideUserLocation = () => {
      if (userLocationLayer.value && map.value) {
        map.value.removeLayer(userLocationLayer.value)
        userLocationLayer.value = null
        userLocationFeature.value = null
      }
      userLocationVisible.value = false
      ElMessage.info('已关闭位置显示')
    }
    
    // 切换用户位置显示
    const toggleUserLocation = async () => {
      if (userLocationVisible.value) {
        hideUserLocation()
      } else {
        await showUserLocation()
      }
    }
    
    onMounted(() => {
      initCacheService();
      nextTick(async () => {
        // 增加一个小延迟确保DOM完全渲染
        setTimeout(async () => {
          //console.log('DOM准备就绪，开始初始化...')
          
          try {
            // 首先初始化坐标系
            await initializeProjections()
            
            // 然后初始化地图
            initMap()
            
            // 强制更新地图尺寸
            if (map.value) {
              // 使用requestAnimationFrame确保DOM完全渲染后再更新尺寸
              requestAnimationFrame(() => {
                setTimeout(() => {
                  if (map.value) {
                    map.value.updateSize()
                    //console.log('地图尺寸已更新')
                  }
                }, 100)
              })
            }
            
            const sceneId = props.sceneId || route.query.scene_id
            if (sceneId) {
              setTimeout(() => loadScene(sceneId), 300)
            }
          } catch (error) {
            console.error('地图初始化过程中出错:', error)
          }
        }, 100) // 增加延迟时间
      })
    })
    
    onUnmounted(() => {
      // 清理弹窗
      if (popup.value) {
        map.value?.removeOverlay(popup.value)
      }
      
      clearAllLayers()
      if (map.value) {
        map.value.setTarget(null)
        map.value = null
      }
    })
    
    
    
    return {
      mapContainer,
      map,
      currentScene,
      layersList,
      currentActiveLayer,
      addLayerDialogVisible,
      availableLayers,
      layerSearchForm,
      disciplines,
      fileTypes,
      styleDialogVisible,
      currentStyleLayer,
      styleForm,
      isVectorLayer,
      hasPointGeometry,
      hasLineGeometry,
      hasPolygonGeometry,
      isDxfMartinLayer,
      isMartinLayer,
      toggleLayerVisibility,
      updateLayerOpacity,
      showAddLayerDialog,
      searchLayers,
      addLayerToScene,
      removeLayer,
      showStyleDialog,
      applyStyle,
      onBaseMapChanged,
      isLayerInScene,
      hasAnyPublishedService,
      activeStyleTab,
      dxfStyleEditorRef,
      savingDxfStyles,
      onDxfStylesUpdated,
      applyAndSaveDxfStyles,
      onPopupControlChanged,
      onSldStyleApplied,
      onSldStyleRemoved,
      getLayerGeometryType,
      refreshMapLayers,
      setActiveLayer,
      bringLayerToTop,
      getLayerCRSInfo,
      transformCoordinates,
      initializeProjections,
      registerProjection,
      projectionsInitialized,
      layerStyleCache,
      applyDxfStylesToLayer,
      popup,
      refreshing,
      refreshAllLayers,
      mouseCoordinates,
      currentBaseMapAttribution,
      initializeCoordinateTracking,
      updateBaseMapAttribution,
      layersCacheEnabled,
      toggleLayersCache,
      // 用户定位相关
      userLocationVisible,
      locationLoading,
      toggleUserLocation,
      // 移动端图层搜索相关
      mobileLayerSearchExpanded,
      isMobile,
      toggleMobileLayerSearch,
      hasActiveLayerFilters,
      getActiveLayerFiltersText,
      resetLayerSearch,
      formatFileSize,
      formatDate,
      ArrowDown
    }
  },
  expose: ['showStyleDialog', 'showAddLayerDialog', 'toggleLayerVisibility', 'updateLayerOpacity', 'map', 'bringLayerToTop', 'setActiveLayer', 'currentActiveLayer', 'getLayerCRSInfo', 'transformCoordinates', 'initializeProjections', 'registerProjection', 'projectionsInitialized', 'applyDxfStylesToLayer']
}
</script>

<style scoped>
.map-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  background: transparent; /* 🔥 移除调试背景色，使用透明背景 */
  overflow: hidden;
  contain: layout style; /* CSS containment 优化 */
  margin: 0; /* 🔥 移除外边距 */
  padding: 0; /* 🔥 移除内边距 */
  border: none; /* 🔥 移除边框 */
}

.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: transparent; /* 🔥 移除调试背景色，使用透明背景 */
  min-height: 0; /* 防止flex容器高度计算问题 */
  contain: layout style; /* CSS containment 优化 */
  border: none; /* 移除调试边框 */
  margin: 0; /* 🔥 移除外边距 */
  padding: 0; /* 🔥 移除内边距 */
  outline: none; /* 🔥 移除轮廓 */
}

.add-layer-dialog-content {
  min-height: 300px;
}

/* 图层搜索区域样式 */
.layer-search-area {
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
.mobile-layer-cards {
  display: none;
}

.layer-list-container {
  margin-top: 20px;
}

.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

/* 搜索表单控件宽度设置 */
.search-form .el-form-item {
  margin-bottom: 0;
  margin-right: 20px;
}

.search-form .el-form-item:last-child {
  margin-right: 0;
}

.search-form .el-form-item .el-form-item__label {
  font-weight: 500;
  color: #606266;
  width: auto !important;
  margin-right: 8px;
}

.search-form .el-select {
  width: 160px;
  min-width: 140px;
}

/* 服务类型选择框稍微宽一点 */
.search-form .el-form-item:first-child .el-select {
  width: 180px;
}

.service-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-start;
}

.layer-actions .el-button {
  padding: 4px 8px;
  font-size: 12px;
  min-height: auto;
  line-height: 1.2;
}

.style-dialog-content h4 {
  margin: 15px 0 10px;
  color: #606266;
}

/* OpenLayers popup styles */
.ol-popup {
  position: absolute;
  background-color: white;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  padding: 15px;
  border-radius: 10px;
  border: 1px solid #cccccc;
  bottom: 12px;
  left: -50px;
  min-width: 280px;
  max-width: 400px;
}

.ol-popup:after, 
.ol-popup:before {
  top: 100%;
  border: solid transparent;
  content: " ";
  height: 0;
  width: 0;
  position: absolute;
  pointer-events: none;
}

.ol-popup:after {
  border-top-color: white;
  border-width: 10px;
  left: 48px;
  margin-left: -10px;
}

.ol-popup:before {
  border-top-color: #cccccc;
  border-width: 11px;
  left: 48px;
  margin-left: -11px;
}

.ol-popup-closer {
  text-decoration: none;
  position: absolute;
  top: 2px;
  right: 8px;
  color: #333;
  font-size: 16px;
  font-weight: bold;
}

.ol-popup-closer:after {
  content: "✖";
}

.ol-popup-closer:hover {
  color: #666;
}

#popup-content {
  max-height: 300px;
  overflow-y: auto;
}

/* 地图控件组样式 */
.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center; /* 🔥 确保所有按钮居中对齐 */
  gap: 8px;
}

/* 🔥 手机端地图控件按钮修复 */
@media (max-width: 768px) {
  .map-controls {
    top: 8px;
    right: 8px;
    gap: 6px;
  }
  
  /* 🔥 确保所有圆形按钮在手机端保持正确的圆形形状 */
  .map-controls .el-button.is-circle {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
  }
  
  /* 🔥 确保图标在按钮中居中 */
  .map-controls .el-button.is-circle i {
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
  }
  
  /* 🔥 针对具体按钮的额外修复 */
  .map-controls .refresh-button {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
  }
  
  .map-controls .cache-toggle-button {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
    
  }
  
  .map-controls .location-button {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
  }
  
  .map-controls .base-map-switcher {
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    min-height: 32px !important;
  }
  
  /* 🔥 确保所有按钮容器对齐 */
  .map-controls > * {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
  }
}

.refresh-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid #67c23a;
}

.refresh-button:hover {
  background-color: #5daf34;
  border-color: #5daf34;
}

.refresh-button.is-loading {
  background-color: #85ce61;
  border-color: #85ce61;
}

.location-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid #409EFF;
}

.location-button:hover {
  background-color: #3a8ee6;
  border-color: #3a8ee6;
}

.location-button.is-loading {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
}

.loading-placeholder .el-icon {
  margin-bottom: 10px;
}

.dialog-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.dialog-loading .el-icon {
  margin-bottom: 10px;
  font-size: 24px;
}

/* 右下角信息面板样式 */
.map-info-panel {
  position: absolute;
  bottom: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 6px;
  pointer-events: none; /* 允许鼠标事件穿透到地图 */
}

/* 坐标信息样式 */
.coordinate-info {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 10px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
  white-space: nowrap;
  color: #666;
  font-weight: 500;
  line-height: 1.2;
}

.coordinate-text {
  color: #666;
  font-weight: 500;
  letter-spacing: 0.5px;
}
.el-button+.el-button {
    margin-left: 0px;
}
/* 版权信息样式 */
.copyright-info {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 10px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: #666;
  font-weight: 500;
  line-height: 1.2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
  text-align: right;
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.copyright-info a {
  color: #2563eb;
  text-decoration: none;
}

.copyright-info a:hover {
  text-decoration: underline;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .map-info-panel {
    bottom: 0;
    right: 0;
    gap: 4px;
    flex-direction: column;
    align-items: flex-end;
  }
  
  .coordinate-info {
    padding: 2px 4px;
    font-size: 8px;
  }
  
  .copyright-info {
    padding: 2px 4px;
    font-size: 8px;
    max-width: 150px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  /* 原有搜索表单样式 */
  .search-form {
    padding: 12px;
  }
  
  .search-form .el-form-item {
    margin-right: 0;
    margin-bottom: 12px;
    width: 100%;
  }
  
  .search-form .el-form-item:last-child {
    margin-bottom: 0;
  }
  
  .search-form .el-select {
    width: 100% !important;
    max-width: 300px;
  }
  
  /* 移动端图层搜索样式 */
  .layer-search-area {
    padding: 12px;
    margin-bottom: 16px;
  }
  
  /* 显示移动端搜索切换按钮 */
  .mobile-search-toggle {
    display: flex !important;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #ffffff;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
  }
  
  .mobile-search-toggle:hover {
    background: #f8f9fa;
  }
  
  .toggle-icon {
    font-size: 16px;
    color: #409eff;
    transition: transform 0.3s ease;
    margin-right: 8px;
  }
  
  .toggle-icon.rotated {
    transform: rotate(180deg);
  }
  
  .toggle-text {
    font-weight: 500;
    color: #333;
    flex: 1;
  }
  
  .search-summary {
    margin-left: 8px;
  }
  
  /* 搜索表单容器控制 */
  .search-form-container {
    overflow: hidden;
    transition: all 0.3s ease;
  }
  
  .search-form-container.mobile-collapsed {
    height: 0 !important;
    opacity: 0;
    margin: 0;
    padding: 0;
  }
  
  .layer-search-form {
    background: #ffffff;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .layer-search-form .el-form-item {
    margin-bottom: 12px;
    width: 100%;
  }
  
  .layer-search-form .el-form-item:last-child {
    margin-bottom: 0;
  }
  
  .layer-search-form .el-select,
  .layer-search-form .el-input {
    width: 100%;
  }
  
  .layer-search-form .el-form-item__label {
    width: auto !important;
    margin-bottom: 4px;
    font-weight: 500;
    color: #606266;
  }
  
  /* 隐藏桌面端表格，显示移动端卡片 */
  .desktop-layer-table {
    display: none !important;
  }
  
  .mobile-layer-cards {
    display: block !important;
  }
  
  /* 移动端图层卡片样式 - 紧凑版 */
  .mobile-layer-card {
    background: #ffffff;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    border: 1px solid #e5e7eb;
    transition: all 0.3s ease;
  }
  
  .mobile-layer-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-1px);
  }
  
  .mobile-layer-card:last-child {
    margin-bottom: 0;
  }
  
  /* 图层卡片头部 - 紧凑版 */
  .mobile-layer-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #f0f2f5;
  }
  
  .mobile-layer-name {
    font-size: 14px;
    font-weight: 600;
    color: #1f2937;
    line-height: 1.3;
    word-break: break-all;
  }
  
  /* 基本信息网格 - 紧凑版 */
  .mobile-layer-info {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 8px;
    margin-bottom: 8px;
  }
  
  .mobile-info-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .mobile-info-label {
    font-size: 10px;
    color: #6b7280;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    line-height: 1.2;
  }
  
  .mobile-info-value {
    font-size: 12px;
    color: #374151;
    font-weight: 500;
    line-height: 1.3;
  }
  
  .mobile-info-value .el-tag {
    font-size: 10px !important;
    padding: 1px 4px !important;
    height: 16px !important;
    line-height: 14px !important;
  }
  
  /* 服务发布状态区域 - 紧凑版 */
  .mobile-service-section {
    border-top: 1px solid #f0f2f5;
    padding-top: 8px;
  }
  
  .mobile-service-item {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
  }
  
  .mobile-service-item:last-child {
    margin-bottom: 0;
  }
  
  .mobile-service-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  
  .mobile-service-title {
    font-size: 12px;
    font-weight: 600;
    color: #374151;
  }
  
  .mobile-service-header .el-tag {
    font-size: 10px !important;
    padding: 1px 4px !important;
    height: 16px !important;
    line-height: 14px !important;
  }
  
  .mobile-service-actions {
    display: flex;
    justify-content: center;
  }
  
  .mobile-service-actions .el-button {
    width: 100%;
    max-width: 160px;
    font-size: 12px !important;
    padding: 4px 8px !important;
    height: 28px !important;
  }
  
  .mobile-service-note {
    text-align: center;
    font-size: 11px;
    color: #9ca3af;
    font-style: italic;
    line-height: 1.2;
  }
}

.cache-toggle-button {
  /*box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);*/
  /*transition: all 0.3s ease;*/
}

.cache-toggle-button.el-button--warning {
  background-color: #e6a23c;
  border-color: #e6a23c;
}

.cache-toggle-button.el-button--warning:hover {
  background-color: #ebb563;
  border-color: #ebb563;
}

.cache-toggle-button.el-button--info {
  background-color: #909399;
  border-color: #909399;
}

.cache-toggle-button.el-button--info:hover {
  background-color: #a6a9ad;
  border-color: #a6a9ad;
}
</style> 