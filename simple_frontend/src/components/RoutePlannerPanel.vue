<template>
  <div v-if="isOpen" class="route-planner-panel">
    <div class="panel-header">
      <h3>路径规划师</h3>
      <el-button 
        link 
        @click="onClose"
        class="close-btn"
      >
        <el-icon><Close /></el-icon>
      </el-button>
    </div>

    <div class="panel-body">
      <!-- 模式选择 -->
      <section class="section">
        <label class="section-label">模式</label>
        <div class="mode-buttons">
          <el-button 
            :type="mode === 'DRAW' ? 'primary' : 'default'"
            @click="setMode('DRAW')"
            class="mode-btn"
          >
            <el-icon><EditPen /></el-icon>
            <span>绘制</span>
          </el-button>
          <el-button 
            :type="mode === 'EDIT' ? 'warning' : 'default'"
            @click="setMode('EDIT')"
            class="mode-btn"
          >
            <el-icon><Edit /></el-icon>
            <span>编辑</span>
          </el-button>
        </div>
        <div class="mode-hint">
          <span v-if="mode === 'DRAW'">点击地图绘制线条。在端点附近绘制可延长路线。</span>
          <span v-else>拖动点以移动。双击线条插入点。点击白色控制点可编辑其转弯半径。</span>
        </div>
      </section>

      <!-- 选中点属性 -->
      <section class="section">
        <label class="section-label">转弯半径</label>
        
        <div v-if="hasSelection && selectedRadius !== null" class="selected-radius-control">
          <div class="selected-header">
            <span>选中角点</span>
          </div>
          
          <div class="radius-input-group">
            <el-slider
              v-model="localSelectedRadius"
              :min="0"
              :max="50000"
              :step="50"
              class="radius-slider"
            />
            <div class="radius-input-wrapper">
              <el-input-number
                v-model="localSelectedRadius"
                :min="0"
                :max="50000"
                :step="50"
                class="radius-input"
              />
              <span class="radius-unit">m</span>
            </div>
          </div>

          <p class="hint-text">正在调整选中红点的半径。</p>
        </div>
        
        <div v-else class="no-selection">
          在地图上选择一个控制点以编辑其半径。
        </div>

        <!-- 默认半径配置 -->
        <div class="default-radius-control">
          <div class="default-radius-header">
            <span>默认半径 (新点)</span>
            <span class="default-radius-value">{{ defaultRadius }} m</span>
          </div>
          <el-slider
            v-model="localDefaultRadius"
            :min="0"
            :max="50000"
            :step="50"
            class="default-radius-slider"
          />
        </div>
      </section>

      <!-- 数据管理 -->
      <section class="section">
        <label class="section-label">数据管理</label>
        <div class="data-actions">
          <el-button 
            @click="onExport"
            class="action-btn"
          >
            <el-icon><Download /></el-icon>
            <span>导出</span>
          </el-button>
          <el-button 
            @click="triggerImport"
            class="action-btn"
          >
            <el-icon><Upload /></el-icon>
            <span>导入</span>
          </el-button>
        </div>
        <input 
          type="file" 
          accept=".csv"
          ref="fileInputRef"
          class="file-input-hidden"
          @change="handleFileSelect"
        />
      </section>
    </div>

    <div class="panel-footer">
      <p class="footer-hint">左键点击选择点。双击地图结束绘制。按 Delete 删除选中点。</p>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { Close, EditPen, Edit, Download, Upload } from '@element-plus/icons-vue'

export default {
  name: 'RoutePlannerPanel',
  components: {
    Close,
    EditPen,
    Edit,
    Download,
    Upload
  },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    mode: {
      type: String,
      default: 'DRAW' // 'DRAW' | 'EDIT' | 'NONE'
    },
    defaultRadius: {
      type: Number,
      default: 5000
    },
    selectedRadius: {
      type: Number,
      default: null
    },
    hasSelection: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'mode-change', 'default-radius-change', 'selected-radius-change', 'export', 'import'],
  setup(props, { emit }) {
    const fileInputRef = ref(null)

    const localSelectedRadius = computed({
      get: () => props.selectedRadius,
      set: (val) => emit('selected-radius-change', val)
    })

    const localDefaultRadius = computed({
      get: () => props.defaultRadius,
      set: (val) => emit('default-radius-change', val)
    })

    const onClose = () => {
      emit('close')
    }

    const setMode = (newMode) => {
      emit('mode-change', newMode)
    }

    const onExport = () => {
      emit('export')
    }

    const triggerImport = () => {
      fileInputRef.value?.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files?.[0]
      if (file) {
        emit('import', file)
        // 清空input，以便可以再次选择同一个文件
        event.target.value = ''
      }
    }

    return {
      fileInputRef,
      localSelectedRadius,
      localDefaultRadius,
      onClose,
      setMode,
      onExport,
      triggerImport,
      handleFileSelect
    }
  }
}
</script>

<style scoped>
.route-planner-panel {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 320px;
  background: white;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 20;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.close-btn {
  padding: 4px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.section {
  margin-bottom: 24px;
}

.section-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.mode-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  height: auto;
}

.mode-hint {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  line-height: 1.5;
}

.selected-radius-control {
  background: #ecf5ff;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
  margin-bottom: 16px;
}

.selected-header {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.radius-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.radius-slider {
  flex: 1;
}

.radius-input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100px;
}

.radius-input {
  flex: 1;
}

.radius-unit {
  font-size: 12px;
  color: #909399;
}

.hint-text {
  font-size: 12px;
  color: #409eff;
  margin: 0;
}

.no-selection {
  padding: 16px;
  border-radius: 8px;
  border: 1px dashed #dcdfe6;
  text-align: center;
  color: #909399;
  font-size: 14px;
  margin-bottom: 16px;
}

.default-radius-control {
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.default-radius-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #606266;
}

.default-radius-value {
  font-family: monospace;
  color: #909399;
}

.default-radius-slider {
  width: 100%;
}

.data-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.file-input-hidden {
  display: none;
}

.panel-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  background: #f5f7fa;
  text-align: center;
}

.footer-hint {
  font-size: 10px;
  color: #909399;
  margin: 0;
  line-height: 1.4;
}
</style>
