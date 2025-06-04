import { createStore } from 'vuex'
import gisApi from '@/api/gis'

export default createStore({
  state: {
    // 场景列表
    scenes: [],
    // 当前场景
    currentScene: null,
    // 图层列表
    layers: [],
    // 图层树结构
    layerTree: [],
    // WFS服务列表
    wfsServices: [],
    // 当前加载的WFS服务
    currentWfsService: null
  },
  getters: {
    getScenes: state => state.scenes,
    getCurrentScene: state => state.currentScene,
    getLayers: state => state.layers,
    getLayerTree: state => state.layerTree,
    getWfsServices: state => state.wfsServices,
    getCurrentWfsService: state => state.currentWfsService
  },
  mutations: {
    // 设置场景列表
    SET_SCENES(state, scenes) {
      state.scenes = scenes
    },
    // 设置当前场景
    SET_CURRENT_SCENE(state, scene) {
      state.currentScene = scene
    },
    // 添加场景
    ADD_SCENE(state, scene) {
      state.scenes.push(scene)
    },
    // 设置图层列表
    SET_LAYERS(state, layers) {
      state.layers = layers
    },
    // 添加图层
    ADD_LAYER(state, layer) {
      state.layers.push(layer)
    },
    // 设置图层树
    SET_LAYER_TREE(state, layerTree) {
      state.layerTree = layerTree
    },
    // 设置WFS服务列表
    SET_WFS_SERVICES(state, services) {
      state.wfsServices = services
    },
    // 设置当前WFS服务
    SET_CURRENT_WFS_SERVICE(state, service) {
      state.currentWfsService = service
    },
    // 添加WFS服务
    ADD_WFS_SERVICE(state, service) {
      state.wfsServices.push(service)
    }
  },
  actions: {
    // 获取场景列表
    async fetchScenes({ commit }) {
      // 模拟异步请求
      const scenes = [
        { id: 1, name: '默认场景', description: '默认GIS场景' }
      ]
      commit('SET_SCENES', scenes)
      commit('SET_CURRENT_SCENE', scenes[0])
      return scenes
    },
    // 获取图层列表
    async fetchLayers({ commit }) {
      try {
        // 尝试从后端API获取图层
        const response = await gisApi.getLayers()
        const layers = response.data || []
        commit('SET_LAYERS', layers)
        
        // 初始化图层树
        const layerTree = [
          {
            id: 'root',
            label: '图层管理',
            children: []
          }
        ]
        
        // 如果有图层数据，添加到图层树
        if (layers.length > 0) {
          layers.forEach(layer => {
            layerTree[0].children.push({
              id: layer.id,
              label: layer.name,
              type: layer.type,
              data: layer
            })
          })
        }
        
        commit('SET_LAYER_TREE', layerTree)
        return layers
      } catch (error) {
        console.error('获取图层列表失败:', error)
        
        // 使用默认图层树
        const layerTree = [
          {
            id: 'root',
            label: '图层管理',
            children: []
          }
        ]
        commit('SET_LAYER_TREE', layerTree)
        return []
      }
    },
    // 添加图层
    addLayer({ commit, state }, layer) {
      commit('ADD_LAYER', layer)
      
      // 更新图层树
      const layerTree = JSON.parse(JSON.stringify(state.layerTree))
      layerTree[0].children.push({
        id: layer.id,
        label: layer.name,
        type: layer.type,
        data: layer,
        children: []
      })
      commit('SET_LAYER_TREE', layerTree)
    },
    // 获取WFS服务列表
    async fetchWfsServices({ commit }) {
      try {
        const response = await gisApi.getServices()
        const services = response.data || []
        // 过滤只获取WFS类型的服务
        const wfsServices = services.filter(service => service.type === 'wfs')
        commit('SET_WFS_SERVICES', wfsServices)
        return wfsServices
      } catch (error) {
        console.error('获取WFS服务列表失败:', error)
        return []
      }
    },
    // 发布WFS服务
    async publishWfsService({ commit, state }, { fileId, params }) {
      try {
        const response = await gisApi.publishWfsService(fileId, params)
        if (response.success) {
          const wfsService = response.data
          commit('ADD_WFS_SERVICE', wfsService)
          
          // 同时添加为一个图层
          const layer = {
            id: wfsService.id,
            name: wfsService.service_name,
            type: 'wfs',
            url: wfsService.wfs_url,
            visible: false,
            data: wfsService
          }
          commit('ADD_LAYER', layer)
          
          // 更新图层树
          const layerTree = JSON.parse(JSON.stringify(state.layerTree))
          layerTree[0].children.push({
            id: layer.id,
            label: layer.name,
            type: layer.type,
            data: layer,
            children: []
          })
          commit('SET_LAYER_TREE', layerTree)
          
          return wfsService
        }
        return null
      } catch (error) {
        console.error('发布WFS服务失败:', error)
        return null
      }
    },
    // 设置当前WFS服务
    setCurrentWfsService({ commit }, service) {
      commit('SET_CURRENT_WFS_SERVICE', service)
    }
  }
}) 