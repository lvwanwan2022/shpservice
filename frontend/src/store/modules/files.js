import gisApi from '@/api/gis'
import { FileModel, FilterParams, PaginationParams } from '@/types'

const state = {
  // 文件列表
  files: [],
  // 当前文件
  currentFile: null,
  // 分页信息
  pagination: {
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 0
  },
  // 过滤条件
  filters: new FilterParams(),
  // 加载状态
  loading: false,
  // 上传状态
  uploading: false,
  uploadProgress: 0,
  // 用户列表
  users: [],
  // 学科列表
  disciplines: [],
  // 文件类型列表
  fileTypes: [],
  // 统计信息
  statistics: {
    total_files: 0,
    total_size: 0,
    by_type: {},
    by_discipline: {},
    by_status: {}
  }
}

const mutations = {
  // 设置文件列表
  SET_FILES(state, { files, pagination }) {
    state.files = files.map(file => new FileModel(file))
    state.pagination = { ...state.pagination, ...pagination }
  },

  // 设置当前文件
  SET_CURRENT_FILE(state, file) {
    state.currentFile = file ? new FileModel(file) : null
  },

  // 添加文件
  ADD_FILE(state, file) {
    const newFile = new FileModel(file)
    state.files.unshift(newFile)
    state.pagination.total += 1
  },

  // 更新文件
  UPDATE_FILE(state, updatedFile) {
    const index = state.files.findIndex(file => file.id === updatedFile.id)
    if (index !== -1) {
      state.files.splice(index, 1, new FileModel(updatedFile))
    }
    if (state.currentFile && state.currentFile.id === updatedFile.id) {
      state.currentFile = new FileModel(updatedFile)
    }
  },

  // 删除文件
  DELETE_FILE(state, fileId) {
    const index = state.files.findIndex(file => file.id === fileId)
    if (index !== -1) {
      state.files.splice(index, 1)
      state.pagination.total -= 1
    }
    if (state.currentFile && state.currentFile.id === fileId) {
      state.currentFile = null
    }
  },

  // 设置过滤条件
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters }
  },

  // 重置过滤条件
  RESET_FILTERS(state) {
    state.filters = new FilterParams()
  },

  // 设置分页
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination }
  },

  // 设置加载状态
  SET_LOADING(state, loading) {
    state.loading = loading
  },

  // 设置上传状态
  SET_UPLOADING(state, uploading) {
    state.uploading = uploading
  },

  // 设置上传进度
  SET_UPLOAD_PROGRESS(state, progress) {
    state.uploadProgress = progress
  },

  // 设置用户列表
  SET_USERS(state, users) {
    state.users = users
  },

  // 设置学科列表
  SET_DISCIPLINES(state, disciplines) {
    state.disciplines = disciplines
  },

  // 设置文件类型列表
  SET_FILE_TYPES(state, fileTypes) {
    state.fileTypes = fileTypes
  },

  // 设置统计信息
  SET_STATISTICS(state, statistics) {
    state.statistics = { ...state.statistics, ...statistics }
  }
}

const actions = {
  // 获取文件列表
  async fetchFiles({ commit, state }, params = {}) {
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

      const response = await gisApi.getFiles(queryParams)
      
      commit('SET_FILES', {
        files: response.files || [],
        pagination: {
          total: response.total || 0,
          page: response.page || 1,
          page_size: response.page_size || 20,
          total_pages: response.total_pages || 0
        }
      })

      return response
    } catch (error) {
      console.error('获取文件列表失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取文件详情
  async fetchFile({ commit }, fileId) {
    try {
      const response = await gisApi.getFile(fileId)
      commit('SET_CURRENT_FILE', response)
      return response
    } catch (error) {
      console.error('获取文件详情失败:', error)
      throw error
    }
  },

  // 上传文件
  async uploadFile({ commit, dispatch }, { formData, onProgress }) {
    commit('SET_UPLOADING', true)
    commit('SET_UPLOAD_PROGRESS', 0)
    
    try {
      const response = await gisApi.uploadFile(formData, (progress) => {
        commit('SET_UPLOAD_PROGRESS', progress)
        if (onProgress) onProgress(progress)
      })

      if (response.file) {
        commit('ADD_FILE', response.file)
      }

      return response
    } catch (error) {
      console.error('文件上传失败:', error)
      throw error
    } finally {
      commit('SET_UPLOADING', false)
      commit('SET_UPLOAD_PROGRESS', 0)
    }
  },

  // 更新文件
  async updateFile({ commit }, { fileId, data }) {
    try {
      await gisApi.updateFile(fileId, data)
      
      // 重新获取文件详情
      const updatedFile = await gisApi.getFile(fileId)
      commit('UPDATE_FILE', updatedFile)
      
      return updatedFile
    } catch (error) {
      console.error('更新文件失败:', error)
      throw error
    }
  },

  // 删除文件
  async deleteFile({ commit }, fileId) {
    try {
      await gisApi.deleteFile(fileId)
      commit('DELETE_FILE', fileId)
    } catch (error) {
      console.error('删除文件失败:', error)
      throw error
    }
  },

  // 设置过滤条件并重新获取数据
  async setFilters({ commit, dispatch }, filters) {
    commit('SET_FILTERS', filters)
    commit('SET_PAGINATION', { page: 1 }) // 重置到第一页
    await dispatch('fetchFiles')
  },

  // 设置分页并重新获取数据
  async setPagination({ commit, dispatch }, pagination) {
    commit('SET_PAGINATION', pagination)
    await dispatch('fetchFiles')
  },

  // 重置过滤条件
  async resetFilters({ commit, dispatch }) {
    commit('RESET_FILTERS')
    commit('SET_PAGINATION', { page: 1 })
    await dispatch('fetchFiles')
  },

  // 获取用户列表
  async fetchUsers({ commit }) {
    try {
      const response = await gisApi.getUsers()
      commit('SET_USERS', response.users || [])
      return response.users
    } catch (error) {
      console.error('获取用户列表失败:', error)
      throw error
    }
  },

  // 获取学科列表
  async fetchDisciplines({ commit }) {
    try {
      const response = await gisApi.getDisciplines()
      commit('SET_DISCIPLINES', response.disciplines || [])
      return response.disciplines
    } catch (error) {
      console.error('获取学科列表失败:', error)
      throw error
    }
  },

  // 获取文件类型列表
  async fetchFileTypes({ commit }) {
    try {
      const response = await gisApi.getFileTypes()
      commit('SET_FILE_TYPES', response.file_types || [])
      return response.file_types
    } catch (error) {
      console.error('获取文件类型列表失败:', error)
      throw error
    }
  },

  // 获取统计信息
  async fetchStatistics({ commit }) {
    try {
      const response = await gisApi.getFileStatistics()
      commit('SET_STATISTICS', response)
      return response
    } catch (error) {
      console.error('获取统计信息失败:', error)
      throw error
    }
  }
}

const getters = {
  // 获取文件列表
  files: state => state.files,

  // 获取当前文件
  currentFile: state => state.currentFile,

  // 获取分页信息
  pagination: state => state.pagination,

  // 获取过滤条件
  filters: state => state.filters,

  // 获取加载状态
  loading: state => state.loading,

  // 获取上传状态
  uploading: state => state.uploading,

  // 获取上传进度
  uploadProgress: state => state.uploadProgress,

  // 获取用户列表
  users: state => state.users,

  // 获取学科列表
  disciplines: state => state.disciplines,

  // 获取文件类型列表
  fileTypes: state => state.fileTypes,

  // 获取统计信息
  statistics: state => state.statistics,

  // 根据ID获取文件
  getFileById: state => id => {
    return state.files.find(file => file.id === id)
  },

  // 根据类型过滤文件
  getFilesByType: state => type => {
    return state.files.filter(file => file.file_type === type)
  },

  // 根据学科过滤文件
  getFilesByDiscipline: state => discipline => {
    return state.files.filter(file => file.discipline === discipline)
  },

  // 获取公开文件
  getPublicFiles: state => {
    return state.files.filter(file => file.is_public)
  },

  // 获取私有文件
  getPrivateFiles: state => {
    return state.files.filter(file => !file.is_public)
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 