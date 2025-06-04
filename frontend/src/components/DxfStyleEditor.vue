<template>
  <div class="dxf-style-editor">
    <div class="editor-header">
      <h4>Martin(DXF) 图层样式设置</h4>
      <div class="header-actions">
        <el-button size="small" @click="loadDefaultStyles">
          使用默认样式
        </el-button>
        <el-button size="small" type="primary" @click="addNewLayer">
          添加图层
        </el-button>
        <div class="popup-control">
          <el-switch
            v-model="enableAttributePopup"
            @change="onPopupControlChange"
            active-text="属性弹窗"
            size="small"
            style="margin-left: 10px;"
          />
          <el-tooltip content="开启/关闭鼠标悬停显示要素属性信息" placement="top">
            <el-icon class="popup-help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
        <!-- <el-button size="small" type="success" @click="saveStylesToDatabase" :loading="saving">
          保存样式
        </el-button> -->
      </div>
    </div>

    <div class="editor-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-content">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在加载图层信息...</span>
      </div>

      <!-- 图层表格 -->
      <div v-else class="layer-table-container">
        <div v-if="Object.keys(layerStyles).length === 0" class="empty-layers">
          <el-empty description="暂无图层样式配置">
            <el-button type="primary" @click="loadDefaultStyles">
              加载默认样式
            </el-button>
          </el-empty>
        </div>

        <div v-else>
          <!-- 搜索过滤 -->
          <div class="table-header">
            <el-input
              v-model="filterText"
              placeholder="搜索图层..."
              size="small"
              style="width: 200px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <div class="group-filter">
              <el-select v-model="selectedGroup" placeholder="选择分组" size="small" clearable @change="handleGroupFilter">
                <el-option label="全部" value="" />
                <el-option v-for="(layers, groupName) in groupedLayers" :key="groupName" :label="groupName" :value="groupName" />
                <el-option label="其他图层" value="ungrouped" />
              </el-select>
            </div>
          </div>

          <!-- 图层样式表格 -->
          <el-table
            :data="filteredLayerList"
            style="width: 100%"
            size="small"
            stripe
            border
            max-height="400"
            @row-click="handleRowClick"
          >
            <el-table-column width="50">
              <template #default="scope">
                <el-switch 
                  v-model="scope.row.style.visible" 
                  size="small"
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                />
              </template>
            </el-table-column>
            
            <el-table-column prop="displayName" label="图层名称" min-width="120" show-overflow-tooltip>
              <template #default="scope">
                <div class="layer-name-cell">
                  <span class="layer-display-name">{{ scope.row.style.name || scope.row.name }}</span>
                  <el-tag size="small" type="info" class="layer-code">{{ scope.row.name }}</el-tag>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="样式预览" width="80">
              <template #default="scope">
                <div 
                  class="style-preview-box"
                  :style="getTablePreviewStyle(scope.row.name)"
                  @click.stop
                ></div>
              </template>
            </el-table-column>
            
            <el-table-column label="颜色" width="80">
              <template #default="scope">
                <el-color-picker 
                  v-model="scope.row.style.color" 
                  size="small"
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                />
              </template>
            </el-table-column>
            
            <el-table-column label="线宽" width="90">
              <template #default="scope">
                <el-input-number 
                  v-model="scope.row.style.weight" 
                  size="small"
                  :min="0.1" 
                  :max="10" 
                  :step="0.1" 
                  :precision="1"
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                />
              </template>
            </el-table-column>
            
            <el-table-column label="透明度" width="90">
              <template #default="scope">
                <el-input-number 
                  v-model="scope.row.style.opacity" 
                  size="small"
                  :min="0" 
                  :max="1" 
                  :step="0.1" 
                  :precision="1"
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                />
              </template>
            </el-table-column>
            
            <el-table-column label="线型" width="100">
              <template #default="scope">
                <el-select 
                  v-model="scope.row.style.dashArray" 
                  size="small" 
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                >
                  <el-option label="实线" value="" />
                  <el-option label="虚线" value="5,5" />
                  <el-option label="点线" value="2,2" />
                  <el-option label="点划线" value="10,5,2,5" />
                </el-select>
              </template>
            </el-table-column>
            
            <el-table-column label="填充" width="60">
              <template #default="scope">
                <el-switch 
                  v-model="scope.row.style.fill" 
                  size="small"
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                />
              </template>
            </el-table-column>
            
            <el-table-column label="填充色" width="80">
              <template #default="scope">
                <el-color-picker 
                  v-model="scope.row.style.fillColor" 
                  size="small"
                  :disabled="!scope.row.style.fill"
                  @change="updateLayerStyle(scope.row.name)"
                  @click.stop
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 添加新图层对话框 -->
    <el-dialog title="添加新图层" v-model="addLayerDialogVisible" width="400px">
      <el-form :model="newLayerForm" label-width="80px">
        <el-form-item label="图层代码" required>
          <el-input v-model="newLayerForm.code" placeholder="如: CUSTOM_LAYER" />
        </el-form-item>
        <el-form-item label="图层名称" required>
          <el-input v-model="newLayerForm.name" placeholder="如: 自定义图层" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newLayerForm.description" placeholder="图层描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addLayerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAddLayer">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage /*, ElMessageBox */ } from 'element-plus'
import { Loading, Search, QuestionFilled } from '@element-plus/icons-vue'
import { dxfStyleManager } from '@/utils/dxfStyleManager'

export default {
  name: 'DxfStyleEditor',
  components: {
    Loading,
    Search,
    QuestionFilled
  },
  props: {
    layerData: {
      type: Object,
      required: true
    },
    martinServiceId: {
      type: Number,
      required: true
    }
  },
  emits: ['styles-updated', 'popup-control-changed'],
  setup(props, { emit }) {
    const loading = ref(false)
    const saving = ref(false)
    const layerStyles = ref({})
    const availableLayers = ref([])
    const addLayerDialogVisible = ref(false)
    const filterText = ref('')
    const selectedGroup = ref('')
    const enableAttributePopup = ref(true)

    // 编辑表单 - 保留给添加新图层使用
    const editForm = reactive({
      name: '',
      description: '',
      weight: 1.5,
      color: '#666666',
      opacity: 0.8,
      fillColor: '#CCCCCC',
      fill: false,
      fillOpacity: 0.3,
      radius: 4,
      zIndex: 1,
      visible: true,
      dashArray: ''
    })

    // 新图层表单
    const newLayerForm = reactive({
      code: '',
      name: '',
      description: ''
    })

    // 计算分组图层
    const groupedLayers = computed(() => {
      const layerGroups = dxfStyleManager.getLayerGroups()
      const grouped = {}

      Object.keys(layerGroups).forEach(groupName => {
        const groupLayers = layerGroups[groupName].filter(layerName => 
          layerStyles.value[layerName]
        )
        if (groupLayers.length > 0) {
          grouped[groupName] = groupLayers
        }
      })

      return grouped
    })

    // 计算未分组图层
    const ungroupedLayers = computed(() => {
      const layerGroups = dxfStyleManager.getLayerGroups()
      const allGroupedLayers = Object.values(layerGroups).flat()
      
      return Object.keys(layerStyles.value).filter(layerName => 
        !allGroupedLayers.includes(layerName)
      )
    })

    // 计算过滤后的图层列表（表格数据）
    const filteredLayerList = computed(() => {
      let layers = Object.keys(layerStyles.value).map(name => ({
        name,
        style: layerStyles.value[name],
        displayName: layerStyles.value[name]?.name || name
      }))

      // 分组过滤
      if (selectedGroup.value) {
        if (selectedGroup.value === 'ungrouped') {
          const layerGroups = dxfStyleManager.getLayerGroups()
          const allGroupedLayers = Object.values(layerGroups).flat()
          layers = layers.filter(layer => !allGroupedLayers.includes(layer.name))
        } else {
          const groupLayers = groupedLayers.value[selectedGroup.value] || []
          layers = layers.filter(layer => groupLayers.includes(layer.name))
        }
      }

      // 文本过滤
      if (filterText.value) {
        const searchText = filterText.value.toLowerCase()
        layers = layers.filter(layer => 
          layer.name.toLowerCase().includes(searchText) ||
          layer.displayName.toLowerCase().includes(searchText)
        )
      }

      return layers
    })

    // 初始化数据
    const initializeData = async () => {
      loading.value = true
      try {
        // 获取Martin服务的图层列表
        if (props.layerData.martin_service?.postgis_table) {
          availableLayers.value = await dxfStyleManager.getLayersFromMartinService(
            props.layerData.martin_service.postgis_table
          )
        }

        // 获取现有样式配置
        const savedStyles = await dxfStyleManager.getMartinServiceStyle(props.martinServiceId)
        
        if (savedStyles) {
          layerStyles.value = savedStyles
        } else {
          // 使用默认样式
          const defaultStyles = dxfStyleManager.getDefaultStyles()
          layerStyles.value = dxfStyleManager.mergeStyles(availableLayers.value, defaultStyles)
        }
      } catch (error) {
        console.error('初始化DXF样式编辑器失败:', error)
        ElMessage.error('加载图层样式失败')
      } finally {
        loading.value = false
      }
    }

    // 加载默认样式
    const loadDefaultStyles = () => {
      const defaultStyles = dxfStyleManager.getDefaultStyles()
      layerStyles.value = dxfStyleManager.mergeStyles(availableLayers.value, defaultStyles)
      
      // 触发样式更新事件，让地图实时显示新的默认样式
      emit('styles-updated', {
        layerName: null, // 表示所有图层
        style: null,
        allStyles: layerStyles.value
      })
      
      ElMessage.success('已加载默认样式')
    }

    // 获取表格样式预览
    const getTablePreviewStyle = (layerName) => {
      const style = layerStyles.value[layerName]
      if (!style) return {}

      const baseStyle = {
        width: '30px',
        height: `${Math.max(style.weight || 1, 2)}px`,
        backgroundColor: style.color,
        opacity: style.opacity,
        borderRadius: '1px'
      }

      if (style.dashArray) {
        baseStyle.backgroundImage = `repeating-linear-gradient(
          to right,
          ${style.color} 0px,
          ${style.color} 3px,
          transparent 3px,
          transparent 6px
        )`
        baseStyle.backgroundColor = 'transparent'
      }

      return baseStyle
    }

    // 处理分组过滤
    const handleGroupFilter = (value) => {
      selectedGroup.value = value
    }

    // 处理行点击
    const handleRowClick = (row, column, /* event */) => {
      // 如果点击的是操作列，不处理
      if (column.property === 'operations') return
      // 可以在这里添加行选择逻辑
    }

    // 判断是否为点图层
    const isPointLayer = (layerName) => {
      return ['KZD', 'GCD', 'JZD'].includes(layerName)
    }

    // 更新图层样式（实时更新）
    const updateLayerStyle = (layerName) => {
      emit('styles-updated', {
        layerName,
        style: layerStyles.value[layerName],
        allStyles: layerStyles.value
      })
    }

    // 添加新图层
    const addNewLayer = () => {
      newLayerForm.code = ''
      newLayerForm.name = ''
      newLayerForm.description = ''
      addLayerDialogVisible.value = true
    }

    // 确认添加图层
    const confirmAddLayer = () => {
      if (!newLayerForm.code || !newLayerForm.name) {
        ElMessage.warning('请填写图层代码和名称')
        return
      }

      if (layerStyles.value[newLayerForm.code]) {
        ElMessage.warning('图层代码已存在')
        return
      }

      layerStyles.value[newLayerForm.code] = dxfStyleManager.createNewLayerStyle(
        newLayerForm.code,
        {
          name: newLayerForm.name,
          description: newLayerForm.description
        }
      )

      addLayerDialogVisible.value = false
      ElMessage.success('图层已添加')
    }

    // 保存所有样式到数据库并应用
    const saveStylesToDatabase = async () => {
      try {
        saving.value = true
        const success = await dxfStyleManager.saveMartinServiceStyle(
          props.martinServiceId,
          layerStyles.value
        )
        
        if (success) {
          ElMessage.success('样式配置已保存并应用')
          return true
        } else {
          ElMessage.error('保存样式配置失败')
          return false
        }
      } catch (error) {
        console.error('保存样式配置失败:', error)
        ElMessage.error('保存样式配置失败')
        return false
      } finally {
        saving.value = false
      }
    }

    // 监听props变化
    watch(() => props.martinServiceId, () => {
      if (props.martinServiceId) {
        initializeData()
      }
    }, { immediate: true })

    // 暴露给父组件的方法
    const getStyles = () => layerStyles.value
    const hasChanges = () => Object.keys(layerStyles.value).length > 0

    // 处理属性弹窗控制
    const onPopupControlChange = () => {
      // 通知父组件属性弹窗开关状态变化
      emit('popup-control-changed', {
        enabled: enableAttributePopup.value,
        martinServiceId: props.martinServiceId,
        layerId: props.layerData.id
      })
      
      ElMessage.success(
        enableAttributePopup.value 
          ? '已开启属性弹窗，鼠标悬停图层要素将显示属性信息' 
          : '已关闭属性弹窗'
      )
    }

    return {
      loading,
      saving,
      layerStyles,
      availableLayers,
      addLayerDialogVisible,
      filterText,
      selectedGroup,
      editForm,
      newLayerForm,
      groupedLayers,
      ungroupedLayers,
      filteredLayerList,
      loadDefaultStyles,
      getTablePreviewStyle,
      handleGroupFilter,
      handleRowClick,
      isPointLayer,
      updateLayerStyle,
      addNewLayer,
      confirmAddLayer,
      saveStylesToDatabase,
      getStyles,
      hasChanges,
      enableAttributePopup,
      onPopupControlChange
    }
  }
}
</script>

<style scoped>
.dxf-style-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
}

.editor-header h4 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.editor-content {
  flex: 1;
  overflow: hidden;
  padding: 12px;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #909399;
}

.loading-content .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.layer-table-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.group-filter {
  width: 150px;
}

.layer-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-display-name {
  font-weight: 500;
  color: #303133;
}

.layer-code {
  font-size: 12px !important;
}

.style-preview-box {
  margin: 0 auto;
  border-radius: 2px;
  cursor: pointer;
}

.empty-layers {
  text-align: center;
  padding: 40px;
}

/* 表格内控件样式调整 */
:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-color-picker) {
  width: 100%;
}

/* 表格行悬停效果 */
:deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

/* 对话框内的表单样式 */
.dialog-footer {
  text-align: right;
}

.dialog-footer .el-button {
  margin-left: 8px;
}

.popup-control {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 10px;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.popup-control:hover {
  background-color: #ecf5ff;
  border-color: #409eff;
}

.popup-help-icon {
  cursor: pointer;
  color: #909399;
  font-size: 14px;
}

.popup-help-icon:hover {
  color: #409eff;
}
</style> 