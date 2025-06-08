<template>
  <div class="base-map-switcher">
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
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
}

.active {
  background-color: #409EFF;
  color: white;
}
</style> 