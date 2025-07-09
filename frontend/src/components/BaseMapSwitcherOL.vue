<template>
  <div class="base-map-switcher">
    <el-tooltip content="切换底图" placement="left" :show-after="500">
      <el-dropdown @command="switchBaseMap" trigger="click">
        <el-button type="primary" circle size="small">
          <svg t="1752030794383" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4606" width="16" height="16"><path d="M950.9888 514.59072l-189.0816 80.64 189.0816 97.4848a30.16704 30.16704 0 0 1 0 42.88512L540.0576 953.37472c-11.9296 11.84768-44.0832 11.84768-56.0128 0L72.73472 735.60064a30.16704 30.16704 0 0 1 0-42.88512l189.06112-97.4848-189.06112-80.64a30.16704 30.16704 0 0 1 0-42.88512l203.0592-97.4848L72.74496 279.552c-11.9296-11.83744-11.9296-45.03552 0-56.89344L484.0448 71.07584c11.9296-11.84768 44.0832-11.84768 56.0128 0L950.9888 222.6688c11.9296 11.85792 11.9296 45.056 0 56.89344l-203.08992 94.65856 203.08992 97.4848a30.16704 30.16704 0 0 1 0 42.88512zM185.10848 701.21472c-11.9296 11.84768-7.08608 2.23232 4.84352 14.08l294.0928 154.05056c11.93984 11.84768 44.09344 11.84768 56.02304 0l285.82912-146.67776c11.9296-11.84768 26.90048-5.16096 14.98112-17.00864l-135.4752-63.55968-165.33504 73.19552c-11.9296 11.84768-44.0832 11.84768-56.0128 0L315.99616 641.024l-130.88768 60.19072zM834.17088 253.1328c11.9296-11.84768 4.62848-5.67296-7.29088-17.5104L540.0576 127.0784c-11.9296-11.84768-44.0832-11.84768-56.0128 0L189.952 239.12448c-11.93984 11.85792-11.93984 2.16064 0 14.00832L484.0448 379.1872c11.9296 11.84768 44.0832 11.84768 56.0128 0L834.17088 253.1328z m0 224.08192l-156.7744-70.12352-137.3184 70.12352c-11.93984 11.84768-44.09344 11.84768-56.02304 0l-140.05248-71.20896-154.05056 71.20896c-11.9296 11.84768-11.9296 2.1504 0 13.99808l294.0928 140.05248c11.93984 11.84768 44.09344 11.84768 56.02304 0L834.17088 491.2128c11.9296-11.84768 11.9296-2.1504 0-13.99808z" fill="#000000" p-id="4607"></path></svg>
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