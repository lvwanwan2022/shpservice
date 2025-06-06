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
          <el-dropdown-item command="tianditu" :class="{ active: currentBaseMap === 'tianditu' }">
            天地图
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
      
      const { gaode, tianditu } = props.map.baseLayers
      
      // 隐藏所有底图
      gaode.setVisible(false)
      tianditu.setVisible(false)
      
      // 显示选择的底图
      switch(command) {
        case 'gaode':
          gaode.setVisible(true)
          currentBaseMap.value = 'gaode'
          break
        case 'tianditu':
          tianditu.setVisible(true)
          currentBaseMap.value = 'tianditu'
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