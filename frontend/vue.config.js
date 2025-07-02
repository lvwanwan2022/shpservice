/*
 * @Author: Lvwan-793145268@qq.com
 * @Date: 2025-05-11 22:17:16
 * @LastEditors: Lvwan-793145268@qq.com
 * @LastEditTime: 2025-06-03 15:26:42
 * @FilePath: \shpservice\frontend\vue.config.js
 * @Description: 
 * Copyright (c) 2025 by Lvwan, All Rights Reserved. 
 */
const { defineConfig } = require('@vue/cli-service')

// 从环境变量获取Martin服务的基础URL，默认为http://192.168.1.17:3000
//const backend_url = 'http://192.168.1.17:5030'
const backend_url = 'http://172.16.118.124:5030'
//const MARTIN_BASE_URL = 'http://192.168.1.17:3000'
const MARTIN_BASE_URL = 'http://172.16.118.124:3000'
//console.log('Vue配置中使用的 MARTIN_BASE_URL:', MARTIN_BASE_URL)



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
        target: 'http://localhost:8083',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        pathRewrite: {
          '^/geoserver': '/geoserver'
        },
        onError: (err, req, res) => {
          console.error('GeoServer代理错误:', err.message)
          console.error('请求URL:', req.url)
          console.error('目标:', 'http://localhost:8083' + req.url)
        }
      }
    }
  }
})
