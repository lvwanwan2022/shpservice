<template>
  <el-dialog
    v-model="visible"
    title="反馈统计信息"
    width="800px"
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
            <div class="stat-number">{{ getOtherCategoryCount() }}</div>
            <div class="stat-label">其他分类</div>
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
        <div class="chart-container">
          <v-chart 
            class="chart" 
            :option="categoryChartOption" 
            autoresize
          />
        </div>
      </div>

      <!-- 按模块统计 -->
      <div class="stats-section">
        <h3>按模块统计</h3>
        <div class="chart-container">
          <v-chart 
            class="chart" 
            :option="moduleChartOption" 
            autoresize
          />
        </div>
      </div>

      <!-- 按修改类型统计 -->
      <div class="stats-section">
        <h3>按修改类型统计</h3>
        <div class="chart-container">
          <v-chart 
            class="chart" 
            :option="typeChartOption" 
            autoresize
          />
        </div>
      </div>

      <!-- 按状态统计 -->
      <div class="stats-section">
        <h3>按状态统计</h3>
        <div class="chart-container">
          <v-chart 
            class="chart" 
            :option="statusChartOption" 
            autoresize
          />
        </div>
      </div>

      <!-- 趋势分析 -->
      <div class="stats-section">
        <h3>趋势分析</h3>
        <div class="trend-analysis">
          <div class="trend-item">
            <div class="trend-icon">📈</div>
            <div class="trend-content">
              <div class="trend-title">解决率</div>
              <div class="trend-value">
                {{ getResolveRate() }}%
              </div>
            </div>
          </div>
          <div class="trend-item">
            <div class="trend-icon">📊</div>
            <div class="trend-content">
              <div class="trend-title">功能vs问题比例</div>
              <div class="trend-value">
                {{ getFeatureBugRatio() }}
              </div>
            </div>
          </div>
          <div class="trend-item">
            <div class="trend-icon">💻</div>
            <div class="trend-content">
              <div class="trend-title">前端vs后端比例</div>
              <div class="trend-value">
                {{ getFrontendBackendRatio() }}
              </div>
            </div>
          </div>
          <div class="trend-item">
            <div class="trend-icon">⚙️</div>
            <div class="trend-content">
              <div class="trend-title">最活跃模块</div>
              <div class="trend-value">
                {{ getMostActiveModule() }}
              </div>
            </div>
          </div>
          <div class="trend-item">
            <div class="trend-icon">🔧</div>
            <div class="trend-content">
              <div class="trend-title">最常见类型</div>
              <div class="trend-value">
                {{ getMostCommonType() }}
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
          🔄 刷新数据
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
// 移除不需要的图标导入
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import feedbackApi from '../api/feedbackApi'

use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

export default {
  name: 'FeedbackStatsDialog',
  components: {
    VChart
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

    const getOtherCategoryCount = () => {
      return stats.value?.by_category?.othercategory || 0
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

    const getOtherCategoryPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getOtherCategoryCount() / total) * 100)
    }

    // 模块统计计算
    const getFrontendCount = () => {
      return stats.value?.by_module?.frontend || 0
    }

    const getBackendCount = () => {
      return stats.value?.by_module?.backend || 0
    }

    const getDatabaseCount = () => {
      return stats.value?.by_module?.database || 0
    }

    const getApiCount = () => {
      return stats.value?.by_module?.api || 0
    }

    const getDeploymentCount = () => {
      return stats.value?.by_module?.deployment || 0
    }

    const getDocumentationCount = () => {
      return stats.value?.by_module?.documentation || 0
    }

    const getOtherModuleCount = () => {
      return stats.value?.by_module?.othermodule || 0
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

    const getDatabasePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getDatabaseCount() / total) * 100)
    }

    const getApiPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getApiCount() / total) * 100)
    }

    const getDeploymentPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getDeploymentCount() / total) * 100)
    }

    const getDocumentationPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getDocumentationCount() / total) * 100)
    }

    const getOtherModulePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getOtherModuleCount() / total) * 100)
    }

    // 修改类型统计计算
    const getUiCount = () => {
      return stats.value?.by_type?.ui || 0
    }

    const getCodeCount = () => {
      return stats.value?.by_type?.code || 0
    }

    const getPerformanceCount = () => {
      return stats.value?.by_type?.performance || 0
    }

    const getFeatureTypeCount = () => {
      return stats.value?.by_type?.feature || 0
    }

    const getArchitectureCount = () => {
      return stats.value?.by_type?.architecture || 0
    }

    const getSecurityCount = () => {
      return stats.value?.by_type?.security || 0
    }

    const getOtherTypeCount = () => {
      return stats.value?.by_type?.othertype || 0
    }

    const getUiPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getUiCount() / total) * 100)
    }

    const getCodePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getCodeCount() / total) * 100)
    }

    const getPerformancePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getPerformanceCount() / total) * 100)
    }

    const getFeatureTypePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getFeatureTypeCount() / total) * 100)
    }

    const getArchitecturePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getArchitectureCount() / total) * 100)
    }

    const getSecurityPercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getSecurityCount() / total) * 100)
    }

    const getOtherTypePercentage = () => {
      const total = stats.value?.total || 0
      if (total === 0) return 0
      return Math.round((getOtherTypeCount() / total) * 100)
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

    const getMostActiveModule = () => {
      const moduleStats = stats.value?.by_module || {}
      const moduleLabels = {
        frontend: '前端',
        backend: '后端',
        database: '数据库',
        api: 'API',
        deployment: '部署',
        documentation: '文档',
        othermodule: '其他'
      }
      
      let maxCount = 0
      let mostActiveModule = '暂无'
      
      Object.keys(moduleStats).forEach(module => {
        if (moduleStats[module] > maxCount) {
          maxCount = moduleStats[module]
          mostActiveModule = moduleLabels[module] || module
        }
      })
      
      return mostActiveModule
    }

    const getMostCommonType = () => {
      const typeStats = stats.value?.by_type || {}
      const typeLabels = {
        ui: '界面优化',
        code: '代码修改',
        performance: '性能优化',
        feature: '功能新增',
        architecture: '架构调整',
        security: '安全修复',
        othertype: '其他'
      }
      
      let maxCount = 0
      let mostCommonType = '暂无'
      
      Object.keys(typeStats).forEach(type => {
        if (typeStats[type] > maxCount) {
          maxCount = typeStats[type]
          mostCommonType = typeLabels[type] || type
        }
      })
      
      return mostCommonType
    }

    // 图表选项计算属性
    const categoryChartOption = computed(() => {
      const data = [
        { value: getFeatureCount(), name: '功能建议' },
        { value: getBugCount(), name: '问题反馈' },
        { value: getOtherCategoryCount(), name: '其他分类' }
      ].filter(item => item.value > 0)

      return {
        title: {
          text: '分类分布',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: { fontSize: 12 }
        },
        series: [
          {
            name: '分类统计',
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
    })

    const moduleChartOption = computed(() => {
      const data = [
        { value: getFrontendCount(), name: '前端' },
        { value: getBackendCount(), name: '后端' },
        { value: getDatabaseCount(), name: '数据库' },
        { value: getApiCount(), name: 'API' },
        { value: getDeploymentCount(), name: '部署' },
        { value: getDocumentationCount(), name: '文档' },
        { value: getOtherModuleCount(), name: '其他模块' }
      ].filter(item => item.value > 0)

      return {
        title: {
          text: '模块分布',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: { fontSize: 12 }
        },
        series: [
          {
            name: '模块统计',
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
    })

    const typeChartOption = computed(() => {
      const data = [
        { value: getUiCount(), name: '界面优化' },
        { value: getCodeCount(), name: '代码修改' },
        { value: getPerformanceCount(), name: '性能优化' },
        { value: getFeatureTypeCount(), name: '功能新增' },
        { value: getArchitectureCount(), name: '架构调整' },
        { value: getSecurityCount(), name: '安全修复' },
        { value: getOtherTypeCount(), name: '其他类型' }
      ].filter(item => item.value > 0)

      return {
        title: {
          text: '修改类型分布',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: { fontSize: 12 }
        },
        series: [
          {
            name: '类型统计',
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
    })

    const statusChartOption = computed(() => {
      const data = [
        { value: getOpenCount(), name: '待处理' },
        { value: getInProgressCount(), name: '处理中' },
        { value: getResolvedCount(), name: '已解决' },
        { value: getClosedCount(), name: '已关闭' }
      ].filter(item => item.value > 0)

      return {
        title: {
          text: '状态分布',
          left: 'center',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: { fontSize: 12 }
        },
        series: [
          {
            name: '状态统计',
            type: 'pie',
            radius: '50%',
            data: data,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
    })

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
      getOtherCategoryCount,
      getFeaturePercentage,
      getBugPercentage,
      getOtherCategoryPercentage,

      // 模块统计
      getFrontendCount,
      getBackendCount,
      getDatabaseCount,
      getApiCount,
      getDeploymentCount,
      getDocumentationCount,
      getOtherModuleCount,
      getFrontendPercentage,
      getBackendPercentage,
      getDatabasePercentage,
      getApiPercentage,
      getDeploymentPercentage,
      getDocumentationPercentage,
      getOtherModulePercentage,

      // 修改类型统计
      getUiCount,
      getCodeCount,
      getPerformanceCount,
      getFeatureTypeCount,
      getArchitectureCount,
      getSecurityCount,
      getOtherTypeCount,
      getUiPercentage,
      getCodePercentage,
      getPerformancePercentage,
      getFeatureTypePercentage,
      getArchitecturePercentage,
      getSecurityPercentage,
      getOtherTypePercentage,

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
      getFrontendBackendRatio,
      getMostActiveModule,
      getMostCommonType,

      // 图表选项
      categoryChartOption,
      moduleChartOption,
      typeChartOption,
      statusChartOption
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
.type-stats,
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

.trend-icon {
  font-size: 24px;
  min-width: 24px;
  text-align: center;
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
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-container {
  height: 300px;
  width: 100%;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.chart {
  height: 100%;
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .trend-analysis {
    grid-template-columns: 1fr;
  }
}
</style> 