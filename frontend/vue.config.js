/*
 * @Author: Lvwan-793145268@qq.com
 * @Date: 2025-05-11 22:17:16
 * @LastEditors: WangNing
 * @LastEditTime: 2025-08-05 11:18:42
 * @FilePath: \shpservice\frontend\vue.config.js
 * @Description: 
 * Copyright (c) 2025 by Lvwan, All Rights Reserved. 
 */
const { defineConfig } = require('@vue/cli-service')
const base_url='http://172.16.101.52'
//const base_url='http://10.20.186.58'
// 从环境变量获取Martin服务的基础URL，默认为http://192.168.1.17:3000
//const backend_url = 'http://192.168.1.17:5030'
const backend_url = base_url+':5030'
//const MARTIN_BASE_URL = 'http://192.168.1.17:3000'
const MARTIN_BASE_URL = base_url+':3000'  
//console.log('Vue配置中使用的 MARTIN_BASE_URL:', MARTIN_BASE_URL)
//const GEOSERVER_BASE_URL = 'http://192.168.1.17:8083'
const GEOSERVER_BASE_URL = base_url+':8083'


module.exports = defineConfig({
  transpileDependencies: true,
  // 添加开发服务器代理配置
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: backend_url,
        changeOrigin: true,
        logLevel: 'debug',
        onError: (err, req, res) => {
          console.error('API代理错误:', err.message)
        }
      },
      '/martin': {
        target: MARTIN_BASE_URL,
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        pathRewrite: {
          '^/martin': ''
        },
        onError: (err, req, res) => {
          console.error('Martin代理错误:', err.message)
          console.error('请求URL:', req.url)
          console.error('目标:', MARTIN_BASE_URL + req.url.replace('/martin', ''))
        }
      },
      '/geoserver': {
        target: GEOSERVER_BASE_URL,
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        pathRewrite: {
          '^/geoserver': '/geoserver'
        },
        onError: (err, req, res) => {
          console.error('GeoServer代理错误:', err.message)
          console.error('请求URL:', req.url)
          console.error('目标:', GEOSERVER_BASE_URL + req.url)
        }
      }
    },
    client: {
      overlay: false
    }

  }
})
