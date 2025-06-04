<template>
  <div class="base-map-switcher">
    <div class="switcher-card" :class="{ 'expanded': expanded }">
      <div class="card-header" @click="toggleExpanded">
        <div class="header-left">
          <el-icon class="map-icon"><MapLocation /></el-icon>
          <span class="title">底图</span>
        </div>
        <el-icon class="toggle-icon" :class="{ 'rotated': expanded }">
          <ArrowDown />
        </el-icon>
      </div>

      <div v-show="expanded" class="card-content">
        <div class="base-map-grid">
          <div 
            v-for="baseMap in baseMaps" 
            :key="baseMap.key"
            class="base-map-item"
            :class="{ 'active': currentBaseMap === baseMap.key }"
            @click="switchBaseMap(baseMap.key)"
          >
            <div class="map-preview">
              <img :src="baseMap.preview" :alt="baseMap.name" />
              <div class="overlay">
                <el-icon v-if="currentBaseMap === baseMap.key" class="check-icon">
                  <Check />
                </el-icon>
              </div>
            </div>
            <span class="map-name">{{ baseMap.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElIcon } from 'element-plus'
import { MapLocation, ArrowDown, Check } from '@element-plus/icons-vue'

export default {
  name: 'BaseMapSwitcher',
  components: {
    ElIcon,
    MapLocation,
    ArrowDown,
    Check
  },
  props: {
    map: {
      type: Object,
      required: true
    }
  },
  emits: ['base-map-changed'],
  setup(props, { emit }) {
    const expanded = ref(false)
    const currentBaseMap = ref('gaode_normal')
    const baseMaps = ref([
      {
        key: 'gaode_normal',
        name: '高德普通',
        preview: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA4MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik0xMCAyMEg3MEw2MCA0MEgxMFYyMFoiIGZpbGw9IiNEQ0RDREMiLz4KPHBhdGggZD0iTTIwIDEwSDUwVjMwSDIwVjEwWiIgZmlsbD0iI0U4RThFOCIvPgo8cGF0aCBkPSJNMzAgNTBINDBWNDVIMzBWNTBaIiBmaWxsPSIjQ0NDQ0NDIi8+Cjx0ZXh0IHg9IjQwIiB5PSIzNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjNjY2NjY2Ij7pq5jlvrc8L3RleHQ+Cjwvc3ZnPgo=',
        layer: null
      },
      {
        key: 'gaode_satellite',
        name: '高德卫星',
        preview: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA4MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjMkE0RTRFIS8+CjxwYXRoIGQ9Ik0xMCAyMEg3MEw2MCA0MEgxMFYyMFoiIGZpbGw9IiM0RDY5NEQiLz4KPHBhdGggZD0iTTIwIDEwSDUwVjMwSDIwVjEwWiIgZmlsbD0iIzZBODU2QSIvPgo8cGF0aCBkPSJNMzAgNTBINDBWNDVIMzBWNTBaIiBmaWxsPSIjMzU1MDM1Ii8+Cjx0ZXh0IHg9IjQwIiB5PSIzNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjQ0NDQ0NDIj7ljaHmmJ88L3RleHQ+Cjwvc3ZnPgo=',
        layer: null
      },
      {
        key: 'gaode_road',
        name: '高德路网',
        preview: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA4MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjRkZGRkZGIi8+CjxwYXRoIGQ9Ik0xMCAyMEg3MEw2MCA0MEgxMFYyMFoiIGZpbGw9IiNGRkM5NDMiLz4KPHBhdGggZD0iTTIwIDEwSDUwVjMwSDIwVjEwWiIgZmlsbD0iI0ZGRURCNSIvPgo8cGF0aCBkPSJNMzAgNTBINDBWNDVIMzBWNTBaIiBmaWxsPSIjRkZBNTAwIi8+Cjx0ZXh0IHg9IjQwIiB5PSIzNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjNjY2NjY2Ij7ovZPnvZE8L3RleHQ+Cjwvc3ZnPgo='
      }
    ])

    // 底图图层缓存
    const layerCache = ref({})

    const toggleExpanded = () => {
      expanded.value = !expanded.value
    }

    const createGaodeLayer = (type) => {
      const { L } = window
      if (!L) return null

      const subdomains = ['01', '02', '03', '04']
      let url = ''
      let attribution = '© 高德地图'

      switch (type) {
        case 'gaode_normal':
          url = 'https://webrd{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
          break
        case 'gaode_satellite':
          url = 'https://webst{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
          attribution += ' 卫星图'
          break
        case 'gaode_road':
          url = 'https://webst{s}.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}'
          attribution += ' 路网图'
          break
        default:
          return null
      }

      return L.tileLayer(url, {
        subdomains,
        attribution,
        maxZoom: 18,
        detectRetina: true
      })
    }

    const switchBaseMap = (baseMapKey) => {
      if (currentBaseMap.value === baseMapKey) return

      const map = props.map
      if (!map) return

      // 移除当前底图
      if (layerCache.value[currentBaseMap.value]) {
        map.removeLayer(layerCache.value[currentBaseMap.value])
      }

      // 创建或获取新底图图层
      if (!layerCache.value[baseMapKey]) {
        layerCache.value[baseMapKey] = createGaodeLayer(baseMapKey)
      }

      // 添加新底图
      if (layerCache.value[baseMapKey]) {
        layerCache.value[baseMapKey].addTo(map)
        currentBaseMap.value = baseMapKey
        
        // 发出底图切换事件
        emit('base-map-changed', {
          key: baseMapKey,
          name: baseMaps.value.find(bm => bm.key === baseMapKey)?.name,
          layer: layerCache.value[baseMapKey]
        })
      }
    }

    const initializeBaseMaps = () => {
      // 创建默认底图
      const defaultLayer = createGaodeLayer(currentBaseMap.value)
      if (defaultLayer && props.map) {
        layerCache.value[currentBaseMap.value] = defaultLayer
        defaultLayer.addTo(props.map)
      }
    }

    // 监听点击地图外区域关闭展开状态
    const handleDocumentClick = (event) => {
      if (!event.target.closest('.base-map-switcher')) {
        expanded.value = false
      }
    }

    onMounted(() => {
      initializeBaseMaps()
      document.addEventListener('click', handleDocumentClick)
    })

    return {
      expanded,
      currentBaseMap,
      baseMaps,
      toggleExpanded,
      switchBaseMap
    }
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleDocumentClick)
  }
}
</script>

<style scoped>
.base-map-switcher {
  position: absolute;
  top: 15px;
  right: 15px;
  z-index: 1000;
}

.switcher-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  transition: all 0.3s ease;
  min-width: 120px;
  max-width: 240px;
}

.switcher-card.expanded {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.card-header {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  transition: background 0.3s;
}

.card-header:hover {
  background: #e6f1fc;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.map-icon {
  color: #409eff;
  font-size: 16px;
}

.title {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.toggle-icon {
  color: #909399;
  font-size: 14px;
  transition: transform 0.3s ease;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.card-content {
  padding: 12px;
}

.base-map-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.base-map-item {
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.base-map-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.base-map-item.active {
  border-color: #409eff;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
}

.map-preview {
  position: relative;
  width: 100%;
  height: 60px;
  overflow: hidden;
  background: #f5f5f5;
}

.map-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.base-map-item:hover .map-preview img {
  transform: scale(1.05);
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.base-map-item.active .overlay {
  opacity: 1;
}

.check-icon {
  color: white;
  font-size: 24px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.map-name {
  display: block;
  padding: 8px 6px;
  text-align: center;
  font-size: 12px;
  color: #606266;
  background: white;
  border-top: 1px solid #f0f0f0;
}

.base-map-item.active .map-name {
  color: #409eff;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .base-map-switcher {
    top: 10px;
    right: 10px;
  }
  
  .switcher-card {
    min-width: 100px;
    max-width: 200px;
  }
  
  .base-map-grid {
    grid-template-columns: 1fr;
  }
  
  .map-preview {
    height: 50px;
  }
}

/* 动画效果 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-content {
  animation: slideDown 0.3s ease when expanded;
}
</style> 