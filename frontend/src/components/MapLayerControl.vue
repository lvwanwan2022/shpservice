<template>
  <div class="map-layer-control">
    <el-card header="底图控制" class="layer-control-card">
      <div class="base-layer-selector">
        <h4>底图选择</h4>
        <el-radio-group v-model="currentBaseLayer" @change="changeBaseLayer">
          <el-radio-button 
            v-for="(service, key) in availableServices" 
            :key="key" 
            :label="key"
            :disabled="service.requiresApiKey && !apiKey"
          >
            {{ service.name }}
          </el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="api-key-input" v-if="showApiKeyInput">
        <h4>天地图API密钥</h4>
        <el-input 
          v-model="apiKey" 
          placeholder="请输入天地图API密钥"
          @change="updateApiKey"
        >
          <template #append>
            <el-button @click="applyApiKey">应用</el-button>
          </template>
        </el-input>
        <div class="api-key-help">
          <small>
            <a href="https://console.tianditu.gov.cn/" target="_blank">
              点击这里申请天地图API密钥
            </a>
          </small>
        </div>
      </div>
      
      <div class="layer-info" v-if="currentLayerInfo">
        <h4>当前底图信息</h4>
        <p><strong>名称:</strong> {{ currentLayerInfo.name }}</p>
        <p><strong>最大缩放:</strong> {{ currentLayerInfo.maxZoom }}</p>
        <p><strong>状态:</strong> 
          <span :class="layerStatusClass">{{ layerStatus }}</span>
        </p>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MAP_SERVICES, createMapLayer } from '@/utils/mapServices'

export default {
  name: 'MapLayerControl',
  props: {
    mapInstance: {
      type: Object,
      default: null
    }
  },
  emits: ['base-layer-changed'],
  setup(props, { emit }) {
    const currentBaseLayer = ref('AMAP')
    const apiKey = ref('')
    const currentLayer = ref(null)
    const layerStatus = ref('正常')
    
    // 可用的地图服务
    const availableServices = computed(() => {
      return Object.fromEntries(
        Object.entries(MAP_SERVICES).filter(([key, service]) => {
          // 返回所有可用的服务
          return true
        })
      )
    })
    
    // 是否显示API密钥输入
    const showApiKeyInput = computed(() => {
      const service = MAP_SERVICES[currentBaseLayer.value]
      return service && service.requiresApiKey
    })
    
    // 当前图层信息
    const currentLayerInfo = computed(() => {
      return MAP_SERVICES[currentBaseLayer.value]
    })
    
    // 图层状态样式
    const layerStatusClass = computed(() => {
      return {
        'status-normal': layerStatus.value === '正常',
        'status-error': layerStatus.value === '错误',
        'status-loading': layerStatus.value === '加载中'
      }
    })
    
    // 切换底图
    const changeBaseLayer = (serviceKey) => {
      if (!props.mapInstance) {
        ElMessage.warning('地图实例不存在')
        return
      }
      
      try {
        layerStatus.value = '加载中'
        
        // 移除当前图层
        if (currentLayer.value && props.mapInstance.hasLayer(currentLayer.value)) {
          props.mapInstance.removeLayer(currentLayer.value)
        }
        
        // 创建新图层
        const newLayer = createMapLayer(serviceKey, apiKey.value)
        
        if (!newLayer) {
          ElMessage.error('无法创建地图图层，请检查API密钥')
          layerStatus.value = '错误'
          return
        }
        
        // 添加事件监听
        newLayer.on('loading', () => {
          layerStatus.value = '加载中'
        })
        
        newLayer.on('load', () => {
          layerStatus.value = '正常'
        })
        
        newLayer.on('tileerror', () => {
          layerStatus.value = '错误'
          ElMessage.error('底图加载失败')
        })
        
        // 添加到地图
        newLayer.addTo(props.mapInstance)
        currentLayer.value = newLayer
        layerStatus.value = '正常'
        
        ////console.log(`切换到底图: ${MAP_SERVICES[serviceKey].name}`)
        ElMessage.success(`已切换到${MAP_SERVICES[serviceKey].name}`)
        
        // 通知父组件
        emit('base-layer-changed', {
          serviceKey,
          layer: newLayer,
          service: MAP_SERVICES[serviceKey]
        })
        
      } catch (error) {
        console.error('切换底图失败:', error)
        ElMessage.error('切换底图失败')
        layerStatus.value = '错误'
      }
    }
    
    // 更新API密钥
    const updateApiKey = () => {
      // 如果当前使用的是需要API密钥的服务，重新加载
      const service = MAP_SERVICES[currentBaseLayer.value]
      if (service && service.requiresApiKey) {
        changeBaseLayer(currentBaseLayer.value)
      }
    }
    
    // 应用API密钥
    const applyApiKey = () => {
      if (!apiKey.value.trim()) {
        ElMessage.warning('请输入API密钥')
        return
      }
      updateApiKey()
    }
    
    // 监听地图实例变化
    watch(() => props.mapInstance, (newMap) => {
      if (newMap && !currentLayer.value) {
        // 地图实例可用时，初始化默认底图
        changeBaseLayer(currentBaseLayer.value)
      }
    })
    
    return {
      currentBaseLayer,
      apiKey,
      availableServices,
      showApiKeyInput,
      currentLayerInfo,
      layerStatus,
      layerStatusClass,
      changeBaseLayer,
      updateApiKey,
      applyApiKey
    }
  }
}
</script>

<style scoped>
.map-layer-control {
  margin-bottom: 10px;
}

.layer-control-card {
  background: rgba(255, 255, 255, 0.95);
}

.base-layer-selector h4,
.api-key-input h4,
.layer-info h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.base-layer-selector .el-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.base-layer-selector .el-radio-button {
  margin: 0;
}

.api-key-input {
  margin-top: 15px;
}

.api-key-help {
  margin-top: 5px;
}

.api-key-help a {
  color: #409eff;
  text-decoration: none;
}

.api-key-help a:hover {
  text-decoration: underline;
}

.layer-info {
  margin-top: 15px;
  font-size: 12px;
}

.layer-info p {
  margin: 5px 0;
}

.status-normal {
  color: #67c23a;
}

.status-error {
  color: #f56c6c;
}

.status-loading {
  color: #e6a23c;
}
</style> 