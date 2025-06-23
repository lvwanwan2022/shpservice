/**
 * 登录认证服务模块
 * Author: 自动生成
 * Description: 提供前端登录认证功能，方便移植到其他项目
 */

import axios from 'axios'

class AuthService {
  constructor() {
    this.baseURL = process.env.VUE_APP_BASE_API || '/api'
    this.tokenKey = 'auth_token'
    this.userKey = 'user_info'
    this.listeners = [] // 登录状态变化监听器
    
    // 创建axios实例
    this.http = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    // 请求拦截器 - 自动添加token
    this.http.interceptors.request.use(
      config => {
        const token = this.getToken()
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
      },
      error => {
        return Promise.reject(error)
      }
    )
    
    // 响应拦截器 - 处理401错误
    this.http.interceptors.response.use(
      response => response,
      error => {
        if (error.response && error.response.status === 401) {
          this.logout()
          // 可以在这里添加页面跳转逻辑
          if (window.location.hash !== '#/login') {
            window.location.hash = '#/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }
  
  /**
   * 用户登录
   * @param {string} username 用户名
   * @param {string} password 密码
   * @returns {Promise} 登录结果
   */
  async login(username, password) {
    try {
      const response = await this.http.post('/auth/login', {
        username,
        password
      })
      
      if (response.data.code === 200) {
        const { token, user } = response.data.data
        this.setUser(user)  // 先设置用户信息
        this.setToken(token)  // 后设置token，这会触发监听器
        return { success: true, data: response.data }
      } else {
        return { success: false, message: response.data.message }
      }
    } catch (error) {
      const message = error.response?.data?.message || '登录失败，请检查网络连接'
      return { success: false, message }
    }
  }
  
  /**
   * 用户注册
   * @param {string} username 用户名
   * @param {string} password 密码
   * @param {string} email 邮箱
   * @returns {Promise} 注册结果
   */
  async register(username, password, email) {
    try {
      const response = await this.http.post('/auth/register', {
        username,
        password,
        email
      })
      
      if (response.data.code === 200) {
        return { success: true, data: response.data.data, message: response.data.message }
      } else {
        return { success: false, message: response.data.message }
      }
    } catch (error) {
      const message = error.response?.data?.message || '注册失败，请检查网络连接'
      return { success: false, message }
    }
  }
  
  /**
   * 用户登出
   */
  async logout() {
    try {
      // 可选：调用后端登出接口
      await this.http.post('/auth/logout')
    } catch (error) {
      console.warn('登出接口调用失败:', error)
    } finally {
      // 清除本地存储
      this.removeToken()
      this.removeUser()
    }
  }
  
  /**
   * 验证token是否有效
   * @returns {Promise<boolean>} 验证结果
   */
  async verifyToken() {
    try {
      const response = await this.http.post('/auth/verify')
      return response.data.code === 200
    } catch (error) {
      return false
    }
  }
  
  /**
   * 获取当前用户信息
   * @returns {Promise} 用户信息
   */
  async getCurrentUser() {
    try {
      const response = await this.http.get('/auth/userinfo')
      if (response.data.code === 200) {
        this.setUser(response.data.data)
        return response.data.data
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
    return null
  }
  
  /**
   * 设置token
   * @param {string} token JWT token
   */
  setToken(token) {
    localStorage.setItem(this.tokenKey, token)
    this.notifyListeners('login')
  }
  
  /**
   * 获取token
   * @returns {string|null} JWT token
   */
  getToken() {
    return localStorage.getItem(this.tokenKey)
  }
  
  /**
   * 移除token
   */
  removeToken() {
    localStorage.removeItem(this.tokenKey)
    this.notifyListeners('logout')
  }
  
  /**
   * 设置用户信息
   * @param {object} user 用户信息
   */
  setUser(user) {
    localStorage.setItem(this.userKey, JSON.stringify(user))
    console.log('设置用户信息:', user)
  }
  
  /**
   * 获取用户信息
   * @returns {object|null} 用户信息
   */
  getUser() {
    const user = localStorage.getItem(this.userKey)
    return user ? JSON.parse(user) : null
  }
  
  /**
   * 移除用户信息
   */
  removeUser() {
    localStorage.removeItem(this.userKey)
  }
  
  /**
   * 检查是否已登录
   * @returns {boolean} 是否已登录
   */
  isAuthenticated() {
    return !!this.getToken()
  }
  
  /**
   * 获取配置好的axios实例 - 一行代码实现带认证的API调用
   * 使用方法: authService.http.get('/api/data')
   * @returns {object} axios实例
   */
  get apiClient() {
    return this.http
  }
  
  /**
   * 添加登录状态变化监听器
   * @param {function} callback 回调函数
   */
  addListener(callback) {
    this.listeners.push(callback)
  }
  
  /**
   * 移除登录状态变化监听器
   * @param {function} callback 回调函数
   */
  removeListener(callback) {
    const index = this.listeners.indexOf(callback)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }
  
  /**
   * 通知所有监听器
   * @param {string} event 事件类型
   */
  notifyListeners(event) {
    this.listeners.forEach(callback => {
      callback(event, this.isAuthenticated(), this.getUser())
    })
  }
}

// 创建全局认证服务实例
const authService = new AuthService()

// 导出认证服务和axios实例
export default authService

// 导出带认证的axios实例，供其他模块使用
export const authHttp = authService.apiClient 