<template>
  <div class="base-map-switcher">
    <el-tooltip content="切换底图" placement="left" :show-after="500">
      <el-dropdown @command="handleCommand" trigger="click">
        <el-button type="info" circle size="small" class="base-map-button">
          <svg t="1752030794383" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4606" width="16" height="16">
            <path d="M950.9888 514.59072l-189.0816 80.64 189.0816 97.4848a30.16704 30.16704 0 0 1 0 42.88512L540.0576 953.37472c-11.9296 11.84768-44.0832 11.84768-56.0128 0L72.73472 735.60064a30.16704 30.16704 0 0 1 0-42.88512l189.06112-97.4848-189.06112-80.64a30.16704 30.16704 0 0 1 0-42.88512l203.0592-97.4848L72.74496 279.552c-11.9296-11.83744-11.9296-45.03552 0-56.89344L484.0448 71.07584c11.9296-11.84768 44.0832-11.84768 56.0128 0L950.9888 222.6688c11.9296 11.85792 11.9296 45.056 0 56.89344l-203.08992 94.65856 203.08992 97.4848a30.16704 30.16704 0 0 1 0 42.88512zM185.10848 701.21472c-11.9296 11.84768-7.08608 2.23232 4.84352 14.08l294.0928 154.05056c11.93984 11.84768 44.09344 11.84768 56.02304 0l285.82912-146.67776c11.9296-11.84768 26.90048-5.16096 14.98112-17.00864l-135.4752-63.55968-165.33504 73.19552c-11.9296 11.84768-44.0832 11.84768-56.0128 0L315.99616 641.024l-130.88768 60.19072zM834.17088 253.1328c11.9296-11.84768 4.62848-5.67296-7.29088-17.5104L540.0576 127.0784c-11.9296-11.84768-44.0832-11.84768-56.0128 0L189.952 239.12448c-11.93984 11.85792-11.93984 2.16064 0 14.00832L484.0448 379.1872c11.9296 11.84768 44.0832 11.84768 56.0128 0L834.17088 253.1328z m0 224.08192l-156.7744-70.12352-137.3184 70.12352c-11.93984 11.84768-44.09344 11.84768-56.02304 0l-140.05248-71.20896-154.05056 71.20896c-11.9296 11.84768-11.9296 2.1504 0 13.99808l294.0928 140.05248c11.93984 11.84768 44.09344 11.84768 56.02304 0L834.17088 491.2128c11.9296-11.84768 11.9296-2.1504 0-13.99808z" fill="#000000" p-id="4607"></path>
          </svg>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="none" :class="{ active: currentBaseMap.key === 'none' }">
              <span :class="{ 'active-text': currentBaseMap.key === 'none' }">无底图</span>
            </el-dropdown-item>
            <el-dropdown-item command="gaode" :class="{ active: currentBaseMap.key === 'gaode' }">
              <span :class="{ 'active-text': currentBaseMap.key === 'gaode' }">高德地图</span>
            </el-dropdown-item>
            <el-dropdown-item command="gaodeSatellite" :class="{ active: currentBaseMap.key === 'gaodeSatellite' }">
              <span :class="{ 'active-text': currentBaseMap.key === 'gaodeSatellite' }">高德卫星图</span>
            </el-dropdown-item>
            <el-dropdown-item command="osm" :class="{ active: currentBaseMap.key === 'osm' }">
              <span :class="{ 'active-text': currentBaseMap.key === 'osm' }">OpenStreetMap</span>
            </el-dropdown-item>
            <el-dropdown-item command="esriSatellite" :class="{ active: currentBaseMap.key === 'esriSatellite' }">
              <span :class="{ 'active-text': currentBaseMap.key === 'esriSatellite' }">Esri 世界影像</span>
            </el-dropdown-item>
            
            <el-dropdown-item command="3d" :class="{ active: currentBaseMap.key === '3d' }">
              <span :class="{ 'active-text': currentBaseMap.key === '3d' }">🌍 三维模式</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-tooltip>
  </div>
</template>

<script>
//import { ref } from 'vue'

export default {
  name: 'BaseMapSwitcherDeckGL',
  props: {
    currentBaseMap: {
      type: Object,
      required: true
    }
  },
  emits: ['base-map-change'],
  setup(props, { emit }) {
    
    // 底图配置 - 参考OpenLayers的配置，添加三维模式和无底图选项
    const baseMaps = {
      none: {
        key: 'none',
        name: '无底图',
        url: null, // 无底图模式
        attribution: '',
        isNone: true
      },
      gaode: {
        key: 'gaode',
        name: '高德地图',
        url: 'https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
        attribution: '© 高德地图'
      },
      gaodeSatellite: {
        key: 'gaodeSatellite',
        name: '高德卫星图',
        url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
        attribution: '© 高德地图'
      },
      osm: {
        key: 'osm',
        name: 'OpenStreetMap',
        url: 'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '© OpenStreetMap contributors'
      },
      esriSatellite: {
        key: 'esriSatellite',
        name: 'Esri 世界影像',
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: '© Esri, Maxar, Earthstar Geographics'
      },
      
      '3d': {
        key: '3d',
        name: '三维模式',
        url: null, // 三维模式不需要瓦片URL
        attribution: '© Deck.gl 三维渲染',
        is3D: true
      },
      'exit3d': {
        key: 'exit3d',
        name: '退出三维',
        url: null,
        attribution: '',
        isExit3D: true
      }
    }

    // 处理底图切换 - 参考OpenLayers的切换逻辑
    const handleCommand = (command) => {
      const baseMapConfig = baseMaps[command]
      if (baseMapConfig && baseMapConfig.key !== props.currentBaseMap.key) {
        emit('base-map-change', baseMapConfig)
      }
    }

    return {
      baseMaps,
      handleCommand
    }
  }
}
</script>

<style scoped>
.base-map-switcher {
  /* 移除绝对定位，现在由父容器 .map-controls 管理位置 */
}

/* 激活状态样式 - 参考OpenLayers */
.el-dropdown-item.active {
  background-color: #ecf5ff;
  color: #409EFF;
  font-weight: 500;
}

/* 当前选中底图的文本样式 */
.el-dropdown-item.active .active-text {
  color: #409EFF;
  font-weight: 600;
}

/* 未选中状态的文本样式 */
.el-dropdown-item:not(.active) .active-text {
  color: #606266;
  font-weight: normal;
}

/* 统一按钮大小 */
.base-map-button {
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  border: none;
  color: #333;
  transition: all 0.2s ease;
}

.base-map-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.base-map-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.base-map-button svg {
  width: 16px;
  height: 16px;
}

/* 手机端底图切换按钮修复 - 参考OpenLayers */
@media (max-width: 768px) {
  .base-map-switcher .el-button.is-circle,
  .base-map-switcher .base-map-button {
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
  
  .base-map-switcher .el-button.is-circle svg,
  .base-map-switcher .base-map-button svg {
    width: 16px !important;
    height: 16px !important;
  }
}
</style> 