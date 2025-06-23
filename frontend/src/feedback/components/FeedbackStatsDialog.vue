<template>
  <el-dialog
    v-model="visible"
    title="反馈统计信息"
    width="600px"
    class="feedback-stats-dialog"
  >
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <div v-else-if="stats" class="stats-content">
      <!-- 总体统计 -->
      <div class="stats-section">
        <h3>总体统计</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ stats.total || 0 }}</div>
            <div class="stat-label">总反馈数</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ getFeatureCount() }}</div>
            <div class="stat-label">功能建议</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ getBugCount() }}</div>
            <div class="stat-label">问题反馈</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ getResolvedCount() }}</div>
            <div class="stat-label">已解决</div>
          </div>
        </div>
      </div>

      <!-- 按分类统计 -->
      <div class="stats-section">
        <h3>按分类统计</h3>
        <div class="category-stats">
          <div class="progress-item">
            <div class="progress-header">
              <span>功能建议</span>
              <span>{{ getFeatureCount() }}</span>
            </div>
            <el-progress 
              :percentage="getFeaturePercentage()" 
              :color="'#67c23a'"
              :show-text="false"
            />
          </div>
          <div class="progress-item">
            <div class="progress-header">
              <span>问题反馈</span>
              <span>{{ getBugCount() }}</span>
            </div>
            <el-progress 
              :percentage="getBugPercentage()" 
              :color="'#f56c6c'"
              :show-text="false"
            />
          </div>
        </div>
      </div>

      <!-- 按模块统计 -->
      <div class="stats-section">
        <h3>按模块统计</h3>
        <div class="module-stats">
          <div class="progress-item">
            <div class="progress-header">
              <span>前端</span>
              <span>{{ getFrontendCount() }}</span>
            </div>
            <el-progress 
              :percentage="getFrontendPercentage()" 
              :color="'#409eff'"
              :show-text="false"
            />
          </div>
          <div class="progress-item">
            <div class="progress-header">
              <span>后端</span>
              <span>{{ getBackendCount() }}</span>
            </div>
            <el-progress 
              :percentage="getBackendPercentage()" 
              :color="'#e6a23c'"
              :show-text="false"
            />
          </div>
        </div>
      </div>

      <!-- 按状态统计 -->
      <div class="stats-section">
        <h3>按状态统计</h3>
        <div class="status-stats">
          <div class="progress-item">
            <div class="progress-header">
              <span>待处理</span>
              <span>{{ getOpenCount() }}</span>
            </div>
            <el-progress 
              :percentage="getOpenPercentage()" 
              :color="'#909399'"
              :show-text="false"
            />
          </div>
          <div class="progress-item">
            <div class="progress-header">
              <span>处理中</span>
              <span>{{ getInProgressCount() }}</span>
            </div>
            <el-progress 
              :percentage="getInProgressPercentage()" 
              :color="'#e6a23c'"
              :show-text="false"
            />
          </div>
          <div class="progress-item">
            <div class="progress-header">
              <span>已解决</span>
              <span>{{ getResolvedCount() }}</span>
            </div>
            <el-progress 
              :percentage="getResolvedPercentage()" 
              :color="'#67c23a'"
              :show-text="false"
            />
          </div>
          <div class="progress-item">
            <div class="progress-header">
              <span>已关闭</span>
              <span>{{ getClosedCount() }}</span>
            </div>
            <el-progress 
              :percentage="getClosedPercentage()" 
              :color="'#c0c4cc'"
              :show-text="false"
            />
          </div>
        </div>
      </div>

      <!-- 趋势分析 -->
      <div class="stats-section">
        <h3>趋势分析</h3>
        <div class="trend-analysis">
          <div class="trend-item">
            <el-icon><TrendCharts /></el-icon>
            <div class="trend-content">
              <div class="trend-title">解决率</div>
              <div class="trend-value">
                {{ getResolveRate() }}%
              </div>
            </div>
          </div>
          <div class="trend-item">
            <el-icon><DataBoard /></el-icon>
            <div class="trend-content">
              <div class="trend-title">功能vs问题比例</div>
              <div class="trend-value">
                {{ getFeatureBugRatio() }}
              </div>
            </div>
          </div>
          <div class="trend-item">
            <el-icon><Monitor /></el-icon>
            <div class="trend-content">
              <div class="trend-title">前端vs后端比例</div>
              <div class="trend-value">
                {{ getFrontendBackendRatio() }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-container">
      <el-empty description="暂无统计数据" />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button type="primary" @click="refreshStats">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  DataBoard,
  Monitor,
  Refresh
} from '@element-plus/icons-vue'
import feedbackApi from '../api/feedbackApi'

export default {
  name: 'FeedbackStatsDialog',
  components: {
    TrendCharts,
    DataBoard,
    Monitor,
    Refresh
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const loading = ref(false)
    const stats = ref(null)

    // 对话框可见性
    const visible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    // 监听对话框显示
    watch(visible, (newVisible) => {
      if (newVisible) {
        loadStats()
      }
    })

    // 加载统计数据
    const loadStats = async () => {
      try {
        loading.value = true
        const response = await feedbackApi.getFeedbackStats()
        
        if (response.code === 200) {
          stats.value = response.data
        } else {
          throw new Error(response.message || '获取统计数据失败')
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
        ElMessage.error(error.message || '加载统计数据失败')
        stats.value = null
      } finally {
        loading.value = false
      }
    }

    // 刷新统计数据
    const refreshStats = () => {
      loadStats()
    }

    // 分类统计计算
    const getFeatureCount = () => {
      return stats.value?.by_category?.feature || 0
    }

    const getBugCount = () => {
      return stats.value?.by_category?.bug || 0
    }

    const getFeaturePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getFeatureCount() / total) * 100)
    }

    const getBugPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getBugCount() / total) * 100)
    }

    // 模块统计计算
    const getFrontendCount = () => {
      return stats.value?.by_module?.frontend || 0
    }

    const getBackendCount = () => {
      return stats.value?.by_module?.backend || 0
    }

    const getFrontendPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getFrontendCount() / total) * 100)
    }

    const getBackendPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getBackendCount() / total) * 100)
    }

    // 状态统计计算
    const getOpenCount = () => {
      return stats.value?.by_status?.open || 0
    }

    const getInProgressCount = () => {
      return stats.value?.by_status?.in_progress || 0
    }

    const getResolvedCount = () => {
      return stats.value?.by_status?.resolved || 0
    }

    const getClosedCount = () => {
      return stats.value?.by_status?.closed || 0
    }

    const getOpenPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getOpenCount() / total) * 100)
    }

    const getInProgressPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getInProgressCount() / total) * 100)
    }

    const getResolvedPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getResolvedCount() / total) * 100)
    }

    const getClosedPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getClosedCount() / total) * 100)
    }

    // 趋势分析计算
    const getResolveRate = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      const resolved = getResolvedCount() + getClosedCount()
      return Math.round((resolved / total) * 100)
    }

    const getFeatureBugRatio = () => {
      const featureCount = getFeatureCount()
      const bugCount = getBugCount()
      
      if (bugCount === 0) {
        return featureCount > 0 ? `${featureCount}:0` : '0:0'
      }
      
      if (featureCount === 0) {
        return `0:${bugCount}`
      }
      
      // 计算最简比例
      const gcd = (a, b) => b === 0 ? a : gcd(b, a % b)
      const divisor = gcd(featureCount, bugCount)
      
      return `${featureCount / divisor}:${bugCount / divisor}`
    }

    const getFrontendBackendRatio = () => {
      const frontendCount = getFrontendCount()
      const backendCount = getBackendCount()
      
      if (backendCount === 0) {
        return frontendCount > 0 ? `${frontendCount}:0` : '0:0'
      }
      
      if (frontendCount === 0) {
        return `0:${backendCount}`
      }
      
      // 计算最简比例
      const gcd = (a, b) => b === 0 ? a : gcd(b, a % b)
      const divisor = gcd(frontendCount, backendCount)
      
      return `${frontendCount / divisor}:${backendCount / divisor}`
    }

    return {
      loading,
      stats,
      visible,

      // 方法
      loadStats,
      refreshStats,

      // 分类统计
      getFeatureCount,
      getBugCount,
      getFeaturePercentage,
      getBugPercentage,

      // 模块统计
      getFrontendCount,
      getBackendCount,
      getFrontendPercentage,
      getBackendPercentage,

      // 状态统计
      getOpenCount,
      getInProgressCount,
      getResolvedCount,
      getClosedCount,
      getOpenPercentage,
      getInProgressPercentage,
      getResolvedPercentage,
      getClosedPercentage,

      // 趋势分析
      getResolveRate,
      getFeatureBugRatio,
      getFrontendBackendRatio
    }
  }
}
</script>

<style scoped>
.feedback-stats-dialog :deep(.el-dialog__body) {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.loading-container {
  padding: 20px 0;
}

.error-container {
  padding: 40px 0;
  text-align: center;
}

.stats-content {
  font-size: 14px;
}

.stats-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #ebeef5;
}

.stats-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.stats-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.category-stats,
.module-stats,
.status-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #303133;
}

.progress-header span:first-child {
  font-weight: 500;
}

.progress-header span:last-child {
  font-weight: 600;
  color: #409eff;
}

.trend-analysis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.trend-item .el-icon {
  font-size: 24px;
  color: #409eff;
}

.trend-content {
  flex: 1;
}

.trend-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.trend-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .feedback-stats-dialog :deep(.el-dialog) {
    width: 95vw;
    margin: 5vh auto;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .stat-item {
    padding: 16px;
  }
  
  .stat-number {
    font-size: 24px;
  }
  
  .trend-analysis {
    grid-template-columns: 1fr;
  }
}
</style> 