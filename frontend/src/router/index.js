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


const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
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

export default router 