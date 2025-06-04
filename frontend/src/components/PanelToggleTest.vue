<template>
  <div class="panel-toggle-test">
    <el-card header="图层面板收起/弹出测试">
      <div class="test-info">
        <p><strong>测试说明:</strong> 验证地图浏览页面右侧图层控制面板的收起/弹出功能</p>
        <p><strong>预期行为:</strong> 点击面板左侧的箭头按钮，面板应该平滑收起或展开</p>
      </div>
      
      <div class="test-instructions">
        <h4>测试步骤:</h4>
        <ol>
          <li>打开地图浏览页面（任意场景）</li>
          <li>观察右侧图层控制面板</li>
          <li>点击面板左侧的圆形箭头按钮</li>
          <li>验证面板是否平滑收起，只显示箭头按钮</li>
          <li>再次点击箭头按钮</li>
          <li>验证面板是否平滑展开，显示完整内容</li>
          <li>检查地图是否在面板收起/展开时自动调整尺寸</li>
        </ol>
      </div>
      
      <div class="test-features">
        <h4>功能特点:</h4>
        <ul>
          <li>✅ 移除了调试工具面板</li>
          <li>✅ 添加了面板收起/展开按钮</li>
          <li>✅ 平滑的动画过渡效果</li>
          <li>✅ 收起时只显示圆形按钮</li>
          <li>✅ 展开时显示完整图层控制</li>
          <li>✅ 地图自动调整尺寸</li>
          <li>✅ 保持所有原有功能</li>
        </ul>
      </div>
      
      <div class="test-controls">
        <el-button @click="openMapView" type="primary">
          打开地图浏览页面
        </el-button>
        <el-button @click="showTips" type="info">
          显示使用提示
        </el-button>
      </div>
      
      <div class="usage-tips" v-if="showUsageTips">
        <h4>使用提示:</h4>
        <div class="tip-item">
          <strong>收起面板:</strong> 当需要更大的地图显示区域时，点击箭头按钮收起面板
        </div>
        <div class="tip-item">
          <strong>展开面板:</strong> 当需要操作图层时，点击箭头按钮展开面板
        </div>
        <div class="tip-item">
          <strong>自动调整:</strong> 面板收起/展开时，地图会自动调整尺寸以适应新的布局
        </div>
        <div class="tip-item">
          <strong>保持功能:</strong> 所有图层操作功能（可见性切换、样式设置、添加/删除图层）都保持不变
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'PanelToggleTest',
  setup() {
    const router = useRouter()
    const showUsageTips = ref(false)
    
    const openMapView = () => {
      // 跳转到地图浏览页面
      router.push({ name: 'MapView' })
      ElMessage.success('正在打开地图浏览页面...')
    }
    
    const showTips = () => {
      showUsageTips.value = !showUsageTips.value
    }
    
    return {
      showUsageTips,
      openMapView,
      showTips
    }
  }
}
</script>

<style scoped>
.panel-toggle-test {
  margin: 10px 0;
}

.test-info {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.test-instructions {
  margin-bottom: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.test-instructions ol {
  margin: 10px 0;
  padding-left: 20px;
}

.test-instructions li {
  margin-bottom: 5px;
}

.test-features {
  margin-bottom: 15px;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.test-features ul {
  margin: 10px 0;
  padding-left: 20px;
}

.test-features li {
  margin-bottom: 5px;
  color: #67c23a;
}

.test-controls {
  margin-bottom: 15px;
}

.test-controls .el-button {
  margin-right: 10px;
}

.usage-tips {
  padding: 15px;
  background-color: #fffbf0;
  border-radius: 4px;
  border: 1px solid #e6a23c;
}

.tip-item {
  margin-bottom: 10px;
  padding: 8px;
  background-color: white;
  border-radius: 4px;
  border-left: 3px solid #e6a23c;
}

.tip-item strong {
  color: #e6a23c;
}
</style> 