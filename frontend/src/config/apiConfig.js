/**
 * API服务配置
 * 支持环境变量动态配置，与vue.config.js保持一致
 */

// 构建服务配置
const createServiceConfig = (hostEnv, portEnv, protocolEnv, defaultHost, defaultPort, defaultProtocol = 'http') => ({
  host: process.env[hostEnv] || defaultHost,
  port: parseInt(process.env[portEnv]) || defaultPort,
  protocol: process.env[protocolEnv] || defaultProtocol,
  get url() {
    return `${this.protocol}://${this.host}:${this.port}`
  }
})

// 配置对象
const apiConfig = {
  // 后端API服务地址
  backendApi: createServiceConfig(
    'VUE_APP_BACKEND_HOST', 
    'VUE_APP_BACKEND_PORT', 
    'VUE_APP_BACKEND_PROTOCOL',
    '127.0.0.1', 
    5030
  ),
  
  // Martin瓦片服务地址  
  martinService: createServiceConfig(
    'VUE_APP_MARTIN_HOST',
    'VUE_APP_MARTIN_PORT', 
    'VUE_APP_MARTIN_PROTOCOL',
    'localhost',
    3000
  ),
  
  // GeoServer服务地址
  geoServerService: {
    ...createServiceConfig(
      'VUE_APP_GEOSERVER_HOST',
      'VUE_APP_GEOSERVER_PORT',
      'VUE_APP_GEOSERVER_PROTOCOL', 
      'localhost',
      8083
    ),
    path: '/geoserver',
    get fullUrl() {
      return `${this.protocol}://${this.host}:${this.port}${this.path}`
    }
  }
}

// 便捷访问方法
export const getBackendUrl = () => apiConfig.backendApi.url
export const getMartinUrl = () => apiConfig.martinService.url
export const getGeoServerUrl = () => apiConfig.geoServerService.fullUrl



export { apiConfig }
export default apiConfig 