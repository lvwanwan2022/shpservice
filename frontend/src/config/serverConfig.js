/**
 * 服务器配置
 * 支持环境变量覆盖，如果没有环境变量则使用默认配置
 */

// 默认配置
const defaultConfig = {
  development: {
    backend: {
      host: process.env.VUE_APP_BACKEND_HOST || '127.0.0.1',
      port: parseInt(process.env.VUE_APP_BACKEND_PORT) || 5030,
      protocol: process.env.VUE_APP_BACKEND_PROTOCOL || 'http'
    },
    martin: {
      host: process.env.VUE_APP_MARTIN_HOST || 'localhost',
      port: parseInt(process.env.VUE_APP_MARTIN_PORT) || 3000,
      protocol: process.env.VUE_APP_MARTIN_PROTOCOL || 'http'
    },
    geoserver: {
      host: process.env.VUE_APP_GEOSERVER_HOST || 'localhost',
      port: parseInt(process.env.VUE_APP_GEOSERVER_PORT) || 8083,
      protocol: process.env.VUE_APP_GEOSERVER_PROTOCOL || 'http'
    },
    devServer: {
      port: parseInt(process.env.VUE_APP_DEV_SERVER_PORT) || 8080
    }
  },
  production: {
    backend: {
      host: process.env.VUE_APP_BACKEND_HOST || 'localhost',
      port: parseInt(process.env.VUE_APP_BACKEND_PORT) || 5030,
      protocol: process.env.VUE_APP_BACKEND_PROTOCOL || 'http'
    },
    martin: {
      host: process.env.VUE_APP_MARTIN_HOST || 'localhost',
      port: parseInt(process.env.VUE_APP_MARTIN_PORT) || 3000,
      protocol: process.env.VUE_APP_MARTIN_PROTOCOL || 'http'
    },
    geoserver: {
      host: process.env.VUE_APP_GEOSERVER_HOST || 'localhost',
      port: parseInt(process.env.VUE_APP_GEOSERVER_PORT) || 8083,
      protocol: process.env.VUE_APP_GEOSERVER_PROTOCOL || 'http'
    }
  }
}

/**
 * 获取当前环境的配置
 */
function getCurrentConfig() {
  const env = process.env.NODE_ENV || 'development'
  return defaultConfig[env] || defaultConfig.development
}

/**
 * 构建服务URL
 */
function buildUrl(serviceConfig) {
  return `${serviceConfig.protocol}://${serviceConfig.host}:${serviceConfig.port}`
}

/**
 * 获取服务URLs
 */
export function getServiceUrls() {
  const config = getCurrentConfig()
  return {
    backend: buildUrl(config.backend),
    martin: buildUrl(config.martin),
    geoserver: buildUrl(config.geoserver)
  }
}

/**
 * 获取开发服务器配置
 */
export function getDevServerConfig() {
  const config = getCurrentConfig()
  return config.devServer || { port: 8080 }
}

// 导出配置
export const serverConfig = defaultConfig
export default getCurrentConfig() 