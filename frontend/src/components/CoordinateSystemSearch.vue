<template>
  <el-dialog
    v-model="visible"
    title="坐标系搜索"
    width="800px"
    :before-close="handleClose"
  >
    <div class="coordinate-search">
      <!-- 搜索框 -->
      <div class="search-section">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入坐标系名称或EPSG代码，支持空格分隔多个关键词。如：西安 1980、beijing 54、国家 2000、4326等"
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #append>
            <el-button @click="handleSearch" :loading="searching">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 常用坐标系 -->
      <div class="common-section" v-if="!searchResults.length && !hasSearched">
        <h4>常用坐标系</h4>
        <div class="coordinate-list">
          <div
            v-for="item in commonCoordinateSystems"
            :key="item.srid"
            class="coordinate-item"
            @click="selectCoordinateSystem(item)"
          >
            <div class="coordinate-code">{{ item.epsg_code }}</div>
            <div class="coordinate-name">{{ item.name || '未知坐标系' }}</div>
          </div>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div class="results-section" v-if="searchResults.length">
        <h4>搜索结果 ({{ searchResults.length }})</h4>
        <div class="coordinate-list">
          <div
            v-for="item in searchResults"
            :key="item.srid"
            class="coordinate-item"
            @click="selectCoordinateSystem(item)"
          >
            <div class="coordinate-code">{{ item.epsg_code }}</div>
            <div class="coordinate-name">{{ item.name || '未知坐标系' }}</div>
            <div class="coordinate-detail" v-if="item.name">
              {{ item.display_name }}
            </div>
          </div>
        </div>
      </div>

      <!-- 无结果提示 -->
      <div class="no-results" v-if="hasSearched && !searchResults.length && !searching">
        <el-empty description="未找到匹配的坐标系">
          <el-button @click="clearSearch">重新搜索</el-button>
        </el-empty>
      </div>

      <!-- 加载状态 -->
      <div class="loading" v-if="searching">
        <el-skeleton :rows="5" animated />
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleClose" :disabled="!selectedCoordinateSystem">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ref, /* reactive, */ watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import gisApi from '@/api/gis'

export default {
  name: 'CoordinateSystemSearch',
  components: {
    Search
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'select'],
  setup(props, { emit }) {
    // 响应式数据
    const visible = ref(false)
    const searchKeyword = ref('')
    const searching = ref(false)
    const hasSearched = ref(false)
    const searchResults = ref([])
    const commonCoordinateSystems = ref([])
    const selectedCoordinateSystem = ref(null)

    // 监听props变化
    watch(() => props.modelValue, (newVal) => {
      visible.value = newVal
      if (newVal) {
        // 对话框打开时重置状态
        resetState()
        loadCommonCoordinateSystems()
      }
    })

    // 监听visible变化
    watch(visible, (newVal) => {
      emit('update:modelValue', newVal)
    })

    // 方法
    const resetState = () => {
      searchKeyword.value = ''
      searching.value = false
      hasSearched.value = false
      searchResults.value = []
      selectedCoordinateSystem.value = null
    }

    const loadCommonCoordinateSystems = async () => {
      try {
        const response = await gisApi.getCommonCoordinateSystems()
        if (response.success) {
          commonCoordinateSystems.value = response.coordinate_systems
        }
      } catch (error) {
        console.error('加载常用坐标系失败:', error)
        ElMessage.error('加载常用坐标系失败')
      }
    }

    const handleSearch = async () => {
      if (!searchKeyword.value.trim()) {
        ElMessage.warning('请输入搜索关键词')
        return
      }

      searching.value = true
      hasSearched.value = true

      try {
        const response = await gisApi.searchCoordinateSystems(searchKeyword.value.trim())
        if (response.success) {
          searchResults.value = response.coordinate_systems
          if (searchResults.value.length === 0) {
            ElMessage.info('未找到匹配的坐标系，请尝试其他关键词')
          }
        } else {
          throw new Error(response.error || '搜索失败')
        }
      } catch (error) {
        console.error('搜索坐标系失败:', error)
        ElMessage.error('搜索坐标系失败: ' + (error.response?.data?.error || error.message))
        searchResults.value = []
      } finally {
        searching.value = false
      }
    }

    const selectCoordinateSystem = (item) => {
      selectedCoordinateSystem.value = item
      emit('select', item)
      handleClose()
    }

    const clearSearch = () => {
      searchKeyword.value = ''
      hasSearched.value = false
      searchResults.value = []
    }

    const handleClose = () => {
      visible.value = false
    }

    // 生命周期
    onMounted(() => {
      if (props.modelValue) {
        loadCommonCoordinateSystems()
      }
    })

    return {
      visible,
      searchKeyword,
      searching,
      hasSearched,
      searchResults,
      commonCoordinateSystems,
      selectedCoordinateSystem,
      handleSearch,
      selectCoordinateSystem,
      clearSearch,
      handleClose
    }
  }
}
</script>

<style scoped>
.coordinate-search {
  max-height: 500px;
  overflow-y: auto;
}

.search-section {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
}

.common-section,
.results-section {
  margin-bottom: 20px;
}

.common-section h4,
.results-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.coordinate-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.coordinate-item {
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.coordinate-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.coordinate-code {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
  margin-bottom: 4px;
}

.coordinate-name {
  color: #303133;
  font-size: 13px;
  margin-bottom: 2px;
}

.coordinate-detail {
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
}

.loading {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 滚动条样式 */
.coordinate-list::-webkit-scrollbar {
  width: 6px;
}

.coordinate-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.coordinate-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.coordinate-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 