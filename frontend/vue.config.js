/*
 * @Author: WangNing
 * @Date: 2025-05-11 22:17:16
 * @LastEditors: WangNing
 * @LastEditTime: 2025-06-03 15:26:42
 * @FilePath: \shpservice\frontend\vue.config.js
 * @Description: 
 * Copyright (c) 2025 by VGE, All Rights Reserved. 
 */
const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  // 添加开发服务器代理配置
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5030',
        changeOrigin: true,
        logLevel: 'debug',
        onError: (err, req, res) => {
          console.error('API代理错误:', err.message)
        },
        onProxyReq: (proxyReq, req, res) => {
          //console.log('API代理请求:', req.method, req.url)
        }
      },
      '/martin': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        pathRewrite: {
          '^/martin': ''
        },
        onError: (err, req, res) => {
          console.error('Martin代理错误:', err.message)
          console.error('请求URL:', req.url)
          console.error('目标:', 'http://localhost:3000' + req.url.replace('/martin', ''))
        },
        onProxyReq: (proxyReq, req, res) => {
          console.log('Martin代理请求:', req.method, req.url, '-> http://localhost:3000' + req.url.replace('/martin', ''))
        },
        onProxyRes: (proxyRes, req, res) => {
          console.log('Martin代理响应:', proxyRes.statusCode, req.url)
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
        },
        onProxyReq: (proxyReq, req, res) => {
          //console.log('GeoServer代理请求:', req.method, req.url, '-> http://localhost:8083' + req.url)
        },
        onProxyRes: (proxyRes, req, res) => {
          //console.log('GeoServer代理响应:', proxyRes.statusCode, req.url)
        }
      }
    }
  }
})
