/*
 * @Author: WangNing
 * @Date: 2025-05-11 22:20:01
 * @LastEditors: WangNing
 * @LastEditTime: 2025-06-13 20:47:53
 * @FilePath: \shpservice\frontend\src\router\index.js
 * @Description: 
 * Copyright (c) 2025 by VGE, All Rights Reserved. 
 */
import { createRouter, createWebHashHistory } from 'vue-router'
// 登录认证模块 - 独立导入，方便移植
import { authGuard } from '@/auth/authGuard'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: false } // 首页不需要登录
  },
  // 登录认证路由 - 独立配置
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/auth/LoginPage.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/map-lf',
    name: 'MapLF',
    component: () => import('@/views/MapViewLF.vue')
  },
  {
    path: '/map-ol',
    name: 'MapOL',
    component: () => import('@/views/MapViewOL.vue')
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/UploadView.vue')
  },
  {
    path: '/scene',
    name: 'Scene',
    component: () => import('@/views/SceneView.vue')
  }
  
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 一行代码实现全局路由权限验证
router.beforeEach(authGuard)

export default router 