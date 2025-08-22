if (typeof window !== 'undefined') {
  window.__VUE_OPTIONS_API__ = true
  window.__VUE_PROD_DEVTOOLS__ = false
  window.__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false
}
/*
 * @Author: Lvwan-793145268@qq.com
 * @Date: 2025-05-11 22:17:16
 * @LastEditors: Lvwan-793145268@qq.com
 * @LastEditTime: 2025-05-11 22:58:53
 * @FilePath: \shpservice\frontend\src\main.js
 * @Description: 
 * Copyright (c) 2025 by Lvwan, All Rights Reserved. 
 */
import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 只引入我们需要的图标
import { 
  Search, Refresh, User, Clock, Paperclip, 
  Like, DisLike, ChatDotRound, View 
} from '@element-plus/icons-vue'
import router from './router'
import store from './store'
// 引入响应式布局CSS
import './assets/responsive.css'

// 导入全局错误处理器
import { installGlobalErrorHandlers } from './utils/errorHandler'







// 安装全局错误处理器（在应用创建前安装）
installGlobalErrorHandlers()

const app = createApp(App)

// // 全局错误处理
// app.config.errorHandler = (err, vm, info) => {
//   console.warn('全局错误处理:', err, info)
  
//   // 忽略ResizeObserver错误（这是一个无害的警告）
//   if (err.message && err.message.includes('ResizeObserver loop completed with undelivered notifications')) {
//     console.warn('忽略ResizeObserver循环警告（这是正常的）')
//     return
//   }
  
//   // 针对VectorGrid已知的坐标问题进行特殊处理
//   if (err.message && (
//     err.message.includes("Cannot read properties of undefined (reading 'lat')") ||
//     err.message.includes("Cannot read properties of undefined (reading 'lng')")
//   )) {
//     console.warn('检测到VectorGrid坐标错误，已自动忽略:', err.message)
//     console.warn('这通常是由Martin服务的点要素引起的，已应用修复补丁')
//     return
//   }
  
//   // 其他错误继续抛出
//   console.error('应用错误:', err)
// }

// 监听全局未捕获的Promise错误
// window.addEventListener('unhandledrejection', (event) => {
//   const error = event.reason
  
//   // 忽略ResizeObserver错误
//   if (error && error.message && error.message.includes('ResizeObserver loop completed with undelivered notifications')) {
//     console.warn('忽略ResizeObserver Promise错误（这是正常的）')
//     event.preventDefault()
//     return
//   }
  
//   if (error && error.message && (
//     error.message.includes("Cannot read properties of undefined (reading 'lat')") ||
//     error.message.includes("Cannot read properties of undefined (reading 'lng')")
//   )) {
//     console.warn('检测到未捕获的VectorGrid坐标Promise错误，已自动忽略:', error.message)
//     event.preventDefault()
//     return
//   }
  
//   console.error('未捕获的Promise错误:', error)
// })

// // 监听全局错误事件（包括ResizeObserver错误）
// window.addEventListener('error', (event) => {
//   if (event.message && event.message.includes('ResizeObserver loop completed with undelivered notifications')) {
//     console.warn('忽略ResizeObserver全局错误（这是正常的）')
//     event.preventDefault()
//     return false
//   }
// })



app.use(ElementPlus)

// 注册Element Plus图标（使用符合命名规范的名称）
app.component('ElSearch', Search)
app.component('ElRefresh', Refresh)
app.component('ElUser', User)
app.component('ElClock', Clock)
app.component('ElPaperclip', Paperclip)
app.component('ElLike', Like)
app.component('ElDisLike', DisLike)
app.component('ElChatDotRound', ChatDotRound)
app.component('ElView', View)

app.use(router)
app.use(store)
app.mount('#app')



//console.log('应用已启动，错误处理器已安装')
