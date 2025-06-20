/**
 * 路由认证守卫模块
 * Author: 自动生成
 * Description: 提供路由级别的登录验证，一行代码实现权限控制
 */

import authService from './authService'

/**
 * 路由前置守卫 - 一行代码实现路由权限验证
 * 使用方法: 在router/index.js中添加 router.beforeEach(authGuard)
 * 
 * @param {object} to 目标路由
 * @param {object} from 来源路由
 * @param {function} next 下一步函数
 */
export function authGuard(to, from, next) {
  // 不需要认证的路由列表
  const publicRoutes = ['/login', '/register', '/']
  
  // 检查是否为公开路由
  if (publicRoutes.includes(to.path)) {
    return next()
  }
  
  // 检查路由meta中的权限配置
  if (to.meta && to.meta.requiresAuth === false) {
    return next()
  }
  
  // 检查是否已登录
  if (!authService.isAuthenticated()) {
    // 保存用户原本要访问的路径
    const redirectPath = to.fullPath
    return next({
      path: '/login',
      query: { redirect: redirectPath }
    })
  }
  
  // 验证token有效性（可选，适合对安全要求较高的应用）
  // authService.verifyToken().then(isValid => {
  //   if (!isValid) {
  //     authService.logout()
  //     return next('/login')
  //   }
  //   next()
  // }).catch(() => {
  //   return next('/login')
  // })
  
  next()
}

/**
 * 简化版路由守卫 - 仅检查token存在性
 * 使用方法: router.beforeEach(simpleAuthGuard)
 */
export function simpleAuthGuard(to, from, next) {
  const publicRoutes = ['/login', '/']
  
  if (publicRoutes.includes(to.path) || authService.isAuthenticated()) {
    next()
  } else {
    next('/login')
  }
}

/**
 * 为单个路由添加认证检查的高阶函数
 * 使用方法: 
 * const protectedRoute = withAuth(() => import('@/views/ProtectedView.vue'))
 */
export function withAuth(componentImport) {
  return () => {
    if (!authService.isAuthenticated()) {
      // 重定向到登录页
      window.location.hash = '#/login'
      return Promise.reject(new Error('需要登录'))
    }
    return componentImport()
  }
}

export default authGuard 