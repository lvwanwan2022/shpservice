import gisApi from '@/api/gis'
import { LayerModel, PaginationParams } from '@/types'

const state = {
  // 图层列表
  layers: [],
  // 当前图层
  currentLayer: null,
  // 分页信息
  pagination: {
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 0
  },
  // 过滤条件
  filters: {
    workspace_id: null,
    enabled: null,
    queryable: null,
    file_id: null,
    name: ''
  },
  // 加载状态
  loading: false,
  // 发布状态
  publishing: false,
  // 统计信息
  statistics: {
    total_layers: 0,
    enabled_layers: 0,
    by_workspace: {},
    by_type: {}
  }
}

const mutations = {
  // 设置图层列表
  SET_LAYERS(state, { layers, pagination }) {
    state.layers = layers.map(layer => new LayerModel(layer))
    state.pagination = { ...state.pagination, ...pagination }
  },

  // 设置当前图层
  SET_CURRENT_LAYER(state, layer) {
    state.currentLayer = layer ? new LayerModel(layer) : null
  },

  // 添加图层
  ADD_LAYER(state, layer) {
    const newLayer = new LayerModel(layer)
    state.layers.unshift(newLayer)
    state.pagination.total += 1
  },

  // 更新图层
  UPDATE_LAYER(state, updatedLayer) {
    const index = state.layers.findIndex(layer => layer.id === updatedLayer.id)
    if (index !== -1) {
      state.layers.splice(index, 1, new LayerModel(updatedLayer))
    }
    if (state.currentLayer && state.currentLayer.id === updatedLayer.id) {
      state.currentLayer = new LayerModel(updatedLayer)
    }
  },

  // 删除图层
  DELETE_LAYER(state, layerId) {
    const index = state.layers.findIndex(layer => layer.id === layerId)
    if (index !== -1) {
      state.layers.splice(index, 1)
      state.pagination.total -= 1
    }
    if (state.currentLayer && state.currentLayer.id === layerId) {
      state.currentLayer = null
    }
  },

  // 设置过滤条件
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters }
  },

  // 重置过滤条件
  RESET_FILTERS(state) {
    state.filters = {
      workspace_id: null,
      enabled: null,
      queryable: null,
      file_id: null,
      name: ''
    }
  },

  // 设置分页
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination }
  },

  // 设置加载状态
  SET_LOADING(state, loading) {
    state.loading = loading
  },

  // 设置发布状态
  SET_PUBLISHING(state, publishing) {
    state.publishing = publishing
  },

  // 设置统计信息
  SET_STATISTICS(state, statistics) {
    state.statistics = { ...state.statistics, ...statistics }
  }
}

const actions = {
  // 获取图层列表
  async fetchLayers({ commit, state }, params = {}) {
    commit('SET_LOADING', true)
    try {
      const queryParams = {
        ...state.filters,
        page: state.pagination.page,
        page_size: state.pagination.page_size,
        ...params
      }

      // 移除空值
      Object.keys(queryParams).forEach(key => {
        if (queryParams[key] === '' || queryParams[key] === null || queryParams[key] === undefined) {
          delete queryParams[key]
        }
      })

      const response = await gisApi.getLayers(queryParams)
      
      commit('SET_LAYERS', {
        layers: response.layers || [],
        pagination: {
          total: response.total || 0,
          page: response.page || 1,
          page_size: response.page_size || 20,
          total_pages: response.total_pages || 0
        }
      })

      return response
    } catch (error) {
      console.error('获取图层列表失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取图层详情
  async fetchLayer({ commit }, layerId) {
    try {
      const response = await gisApi.getLayer(layerId)
      commit('SET_CURRENT_LAYER', response)
      return response
    } catch (error) {
      console.error('获取图层详情失败:', error)
      throw error
    }
  },

  // 发布图层
  async publishLayer({ commit, dispatch }, { fileId, params = {} }) {
    commit('SET_PUBLISHING', true)
    try {
      const response = await gisApi.publishLayer(fileId, params)
      
      // 重新获取图层列表
      await dispatch('fetchLayers')
      
      return response
    } catch (error) {
      console.error('发布图层失败:', error)
      throw error
    } finally {
      commit('SET_PUBLISHING', false)
    }
  },

  // 更新图层
  async updateLayer({ commit }, { layerId, data }) {
    try {
      await gisApi.updateLayer(layerId, data)
      
      // 重新获取图层详情
      const updatedLayer = await gisApi.getLayer(layerId)
      commit('UPDATE_LAYER', updatedLayer)
      
      return updatedLayer
    } catch (error) {
      console.error('更新图层失败:', error)
      throw error
    }
  },

  // 删除图层
  async deleteLayer({ commit }, layerId) {
    try {
      await gisApi.deleteLayer(layerId)
      commit('DELETE_LAYER', layerId)
    } catch (error) {
      console.error('删除图层失败:', error)
      throw error
    }
  },

  // 获取图层能力信息
  async fetchLayerCapabilities({ commit }, { layerId, serviceType = 'WMS' }) {
    try {
      const response = await gisApi.getLayerCapabilities(layerId, serviceType)
      return response
    } catch (error) {
      console.error('获取图层能力信息失败:', error)
      throw error
    }
  },

  // 获取图层预览
  async fetchLayerPreview({ commit }, { layerId, bbox, width = 512, height = 512, srs = 'EPSG:4326' }) {
    try {
      const response = await gisApi.getLayerPreview(layerId, bbox, width, height, srs)
      return response
    } catch (error) {
      console.error('获取图层预览失败:', error)
      throw error
    }
  },

  // 设置过滤条件并重新获取数据
  async setFilters({ commit, dispatch }, filters) {
    commit('SET_FILTERS', filters)
    commit('SET_PAGINATION', { page: 1 }) // 重置到第一页
    await dispatch('fetchLayers')
  },

  // 设置分页并重新获取数据
  async setPagination({ commit, dispatch }, pagination) {
    commit('SET_PAGINATION', pagination)
    await dispatch('fetchLayers')
  },

  // 重置过滤条件
  async resetFilters({ commit, dispatch }) {
    commit('RESET_FILTERS')
    commit('SET_PAGINATION', { page: 1 })
    await dispatch('fetchLayers')
  },

  // 获取统计信息
  async fetchStatistics({ commit }) {
    try {
      const response = await gisApi.getLayerStatistics()
      commit('SET_STATISTICS', response)
      return response
    } catch (error) {
      console.error('获取图层统计信息失败:', error)
      throw error
    }
  }
}

const getters = {
  // 获取图层列表
  layers: state => state.layers,

  // 获取当前图层
  currentLayer: state => state.currentLayer,

  // 获取分页信息
  pagination: state => state.pagination,

  // 获取过滤条件
  filters: state => state.filters,

  // 获取加载状态
  loading: state => state.loading,

  // 获取发布状态
  publishing: state => state.publishing,

  // 获取统计信息
  statistics: state => state.statistics,

  // 根据ID获取图层
  getLayerById: state => id => {
    return state.layers.find(layer => layer.id === id)
  },

  // 根据工作空间过滤图层
  getLayersByWorkspace: state => workspaceId => {
    return state.layers.filter(layer => layer.workspace_id === workspaceId)
  },

  // 根据文件ID过滤图层
  getLayersByFile: state => fileId => {
    return state.layers.filter(layer => layer.file_id === fileId)
  },

  // 获取启用的图层
  getEnabledLayers: state => {
    return state.layers.filter(layer => layer.enabled)
  },

  // 获取可查询的图层
  getQueryableLayers: state => {
    return state.layers.filter(layer => layer.queryable)
  },

  // 获取矢量图层
  getVectorLayers: state => {
    return state.layers.filter(layer => layer.featuretype_id)
  },

  // 获取栅格图层
  getRasterLayers: state => {
    return state.layers.filter(layer => layer.coverage_id)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 