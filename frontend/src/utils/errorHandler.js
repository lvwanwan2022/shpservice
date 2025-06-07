/**
 * 全局错误处理工具
 * 处理ResizeObserver等已知的无害错误
 */

// 已知的无害错误消息
const HARMLESS_ERRORS = [
  'ResizeObserver loop completed with undelivered notifications.',
  'ResizeObserver loop limit exceeded',
  'Script error.',
  'Non-Error promise rejection captured'
]

/**
 * 检查错误是否为无害错误
 * @param {Error|string} error - 错误对象或错误消息
 * @returns {boolean} - 是否为无害错误
 */
export function isHarmlessError(error) {
  const message = typeof error === 'string' ? error : error?.message || ''
  return HARMLESS_ERRORS.some(harmlessMessage => 
    message.includes(harmlessMessage)
  )
}

/**
 * ResizeObserver错误处理器
 * @param {ErrorEvent} event - 错误事件
 */
export function handleResizeObserverError(event) {
  if (isHarmlessError(event.error || event.message)) {
    // 阻止错误冒泡到控制台
    event.stopImmediatePropagation()
    event.preventDefault()
    return false
  }
}

/**
 * 安装全局错误处理器
 */
export function installGlobalErrorHandlers() {
  // 处理同步错误
  window.addEventListener('error', handleResizeObserverError, true)
  
  // 处理Promise拒绝
  window.addEventListener('unhandledrejection', (event) => {
    if (isHarmlessError(event.reason)) {
      event.preventDefault()
      return false
    }
  })
  
  // 处理Vue警告（如果需要）
  if (process.env.NODE_ENV === 'development') {
    const originalWarn = console.warn
    console.warn = function(...args) {
      const message = args.join(' ')
      if (isHarmlessError(message)) {
        return
      }
      originalWarn.apply(console, args)
    }
  }
  
  console.log('✅ 全局错误处理器已安装')
}

/**
 * 卸载全局错误处理器
 */
export function uninstallGlobalErrorHandlers() {
  window.removeEventListener('error', handleResizeObserverError, true)
  window.removeEventListener('unhandledrejection', handleResizeObserverError)
  console.log('✅ 全局错误处理器已卸载')
}

/**
 * 专门用于地图组件的错误处理
 */
export class MapErrorHandler {
  constructor() {
    this.handlers = []
  }
  
  /**
   * 安装地图组件错误处理
   */
  install() {
    const handler = (event) => {
      if (event.error?.message?.includes('ResizeObserver') || 
          event.message?.includes('ResizeObserver')) {
        event.stopImmediatePropagation()
        event.preventDefault()
        return false
      }
    }
    
    window.addEventListener('error', handler, true)
    this.handlers.push(handler)
    
    return () => this.cleanup()
  }
  
  /**
   * 清理错误处理器
   */
  cleanup() {
    this.handlers.forEach(handler => {
      window.removeEventListener('error', handler, true)
    })
    this.handlers = []
  }
}

// 默认导出
export default {
  isHarmlessError,
  handleResizeObserverError,
  installGlobalErrorHandlers,
  uninstallGlobalErrorHandlers,
  MapErrorHandler
} 