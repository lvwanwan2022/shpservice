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
      <!-- 行业模式选择 -->
      <section class="section">
        <label class="section-label">行业模式</label>
        <div class="industry-mode-buttons">
          <el-button 
            :type="industryMode === 'WATER' ? 'primary' : 'default'"
            @click="setIndustryMode('WATER')"
            class="industry-mode-btn"
          >
            <el-icon><Water /></el-icon>
            <span>水利行业</span>
          </el-button>
          <el-button 
            :type="industryMode === 'HIGHWAY' ? 'primary' : 'default'"
            @click="setIndustryMode('HIGHWAY')"
            class="industry-mode-btn"
          >
            <el-icon><Van /></el-icon>
            <span>公路行业</span>
          </el-button>
        </div>
        <div v-if="industryMode === 'HIGHWAY'" class="highway-hint">
          公路模式启用缓和曲线（回旋线）。<br/>连接方式: 直线-回旋线-圆-回旋线-直线。
        </div>
      </section>

      <!-- 模式选择 -->
      <section class="section">
        <label class="section-label">交互模式</label>
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
          <span v-else>拖动点以移动。双击线条插入点。点击白色控制点可查看其参数。</span>
        </div>
      </section>

      <!-- 选中点属性 -->
      <section class="section">
        <label class="section-label">参数设置</label>
        
        <div v-if="hasSelection && selectedRadius !== null && selectedRadius !== undefined" class="selected-control">
          <div class="selected-header">
            <span>选中角点</span>
          </div>
          
          <!-- 半径编辑（编辑模式和绘制模式都可以编辑） -->
          <div class="radius-input-group">
            <div class="param-label">圆曲线半径 (R)</div>
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

          <!-- 缓和曲线长度（仅公路模式） -->
          <div v-if="industryMode === 'HIGHWAY' && selectedSpiralLen !== null && selectedSpiralLen !== undefined" class="spiral-input-group">
            <div class="param-label">缓和曲线长 (Ls)</div>
            <el-slider
              v-model="localSelectedSpiralLen"
              :min="0"
              :max="2000"
              :step="10"
              class="spiral-slider"
            />
            <div class="spiral-input-wrapper">
              <el-input-number
                v-model="localSelectedSpiralLen"
                :min="0"
                :max="2000"
                :step="10"
                class="spiral-input"
              />
              <span class="spiral-unit">m</span>
            </div>
          </div>
        </div>
        
        <div v-else class="no-selection">
          在地图上选择一个控制点以查看其参数。
        </div>

        <!-- 默认参数配置 -->
        <div class="default-control">
          <div class="default-param">
            <div class="default-param-header">
              <span>默认半径 (R)</span>
              <span class="default-param-value">{{ defaultRadius }} m</span>
            </div>
            <el-slider
              v-model="localDefaultRadius"
              :min="0"
              :max="50000"
              :step="50"
              class="default-param-slider"
            />
          </div>
          
          <div v-if="industryMode === 'HIGHWAY'" class="default-param">
            <div class="default-param-header">
              <span>默认缓和曲线 (Ls)</span>
              <span class="default-param-value">{{ defaultSpiralLen }} m</span>
            </div>
            <el-slider
              v-model="localDefaultSpiralLen"
              :min="0"
              :max="2000"
              :step="10"
              class="default-param-slider"
            />
          </div>
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
import { Close, EditPen, Edit, Download, Upload, Water, Van } from '@element-plus/icons-vue'

export default {
  name: 'RoutePlannerPanel',
  components: {
    Close,
    EditPen,
    Edit,
    Download,
    Upload,
    Water,
    Van
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
    industryMode: {
      type: String,
      default: 'WATER' // 'WATER' | 'HIGHWAY'
    },
    defaultRadius: {
      type: Number,
      default: 5000
    },
    defaultSpiralLen: {
      type: Number,
      default: 0
    },
    selectedRadius: {
      type: Number,
      default: null
    },
    selectedSpiralLen: {
      type: Number,
      default: null
    },
    hasSelection: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'mode-change', 'industry-mode-change', 'default-radius-change', 'default-spiral-len-change', 'selected-radius-change', 'selected-spiral-len-change', 'export', 'import'],
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

    const localDefaultSpiralLen = computed({
      get: () => props.defaultSpiralLen,
      set: (val) => emit('default-spiral-len-change', val)
    })

    const localSelectedSpiralLen = computed({
      get: () => props.selectedSpiralLen,
      set: (val) => emit('selected-spiral-len-change', val)
    })

    const onClose = () => {
      emit('close')
    }

    const setMode = (newMode) => {
      emit('mode-change', newMode)
    }

    const setIndustryMode = (newMode) => {
      emit('industry-mode-change', newMode)
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
      localSelectedSpiralLen,
      localDefaultRadius,
      localDefaultSpiralLen,
      onClose,
      setMode,
      setIndustryMode,
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

.industry-mode-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}

.industry-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.highway-hint {
  font-size: 11px;
  color: #9333ea;
  background: #f3e8ff;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #e9d5ff;
  line-height: 1.5;
}

.selected-control {
  background: #ecf5ff;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
  margin-bottom: 16px;
}

.readonly-param {
  margin-bottom: 12px;
}

.param-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.param-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
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

.spiral-input-group {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(147, 51, 234, 0.2);
}

.spiral-slider {
  flex: 1;
}

.spiral-input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100px;
  margin-top: 8px;
}

.spiral-input {
  flex: 1;
}

.spiral-unit {
  font-size: 12px;
  color: #909399;
}

.default-control {
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.default-param {
  margin-bottom: 16px;
}

.default-param:last-child {
  margin-bottom: 0;
}

.default-param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #606266;
}

.default-param-value {
  font-family: monospace;
  color: #909399;
}

.default-param-slider {
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
