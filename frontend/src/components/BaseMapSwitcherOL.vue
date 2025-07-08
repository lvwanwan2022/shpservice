<template>
  <div class="base-map-switcher">
    <el-tooltip content="切换底图" placement="left" :show-after="500">
      <el-dropdown @command="switchBaseMap" trigger="click">
        <el-button type="primary" circle size="small">
          <i class="el-icon-map-location"></i>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="gaode" :class="{ active: currentBaseMap === 'gaode' }">
              高德地图
            </el-dropdown-item>
            <el-dropdown-item command="gaodeSatellite" :class="{ active: currentBaseMap === 'gaodeSatellite' }">
              高德卫星图
            </el-dropdown-item>
            <el-dropdown-item command="osm" :class="{ active: currentBaseMap === 'osm' }">
              OpenStreetMap
            </el-dropdown-item>
            <el-dropdown-item command="esriSatellite" :class="{ active: currentBaseMap === 'esriSatellite' }">
              Esri 世界影像
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-tooltip>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'BaseMapSwitcherOL',
  props: {
    map: { type: Object, required: true }
  },
  emits: ['base-map-changed'],
  setup(props, { emit }) {
    const currentBaseMap = ref('gaode')
    
    const switchBaseMap = (command) => {
      if (!props.map || !props.map.baseLayers) return
      
      const { gaode, gaodeSatellite, osm, esriSatellite } = props.map.baseLayers
      
      // 隐藏所有底图
      gaode.setVisible(false)
      gaodeSatellite.setVisible(false)
      osm.setVisible(false)
      esriSatellite.setVisible(false)
      
      // 显示选择的底图
      switch(command) {
        case 'gaode':
          gaode.setVisible(true)
          currentBaseMap.value = 'gaode'
          break
        case 'gaodeSatellite':
          gaodeSatellite.setVisible(true)
          currentBaseMap.value = 'gaodeSatellite'
          break
        case 'osm':
          osm.setVisible(true)
          currentBaseMap.value = 'osm'
          break
        case 'esriSatellite':
          esriSatellite.setVisible(true)
          currentBaseMap.value = 'esriSatellite'
          break
        default:
          gaode.setVisible(true)
          currentBaseMap.value = 'gaode'
      }
      
      emit('base-map-changed', command)
    }
    
    return {
      currentBaseMap,
      switchBaseMap
    }
  }
}
</script>

<style scoped>
.base-map-switcher {
  /* 移除绝对定位，现在由父容器 .map-controls 管理位置 */
  /*box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);*/
}

/* 🔥 手机端底图切换按钮修复 */
@media (max-width: 768px) {
  .base-map-switcher .el-button.is-circle {
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
  
  .base-map-switcher .el-button.is-circle i {
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
  }
}

.active {
  background-color: #409EFF;
  color: white;
}
</style> 