/**
 * 全局配置文件
 */

// Martin服务的基础URL，从环境变量获取
export const MARTIN_BASE_URL =process.env.VUE_APP_BACKEND_PROTOCOL+'://'+ process.env.VUE_APP_MARTIN_HOST+':'+process.env.VUE_APP_MARTIN_PORT
//export const MARTIN_BASE_URL ='http://172.16.118.124:3000'


// API服务的基础URL
export const API_BASE_URL = '/api'

// GeoServer服务的基础URL
export const GEOSERVER_BASE_URL = '/geoserver'

export default {
  MARTIN_BASE_URL,
  API_BASE_URL,
  GEOSERVER_BASE_URL
} 