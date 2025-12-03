/*
 * @Author: Lvwan-793145268@qq.com
 * @Date: 2025-05-11 22:17:16
 * @LastEditors: WangNi * @LastEditTime: 2025-08-08 21:42:07
 * @FilePath: \shpservice\frontend\vue.config.js
 * @Description: 
 * Copyright (c) 2025 by Lvwan, All Rights Reserved. 
 */
const { defineConfig } = require('@vue/cli-service')
const base_url='http://10.20.124.20'
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
  
  // 生产环境配置
  publicPath: '/',
  outputDir: 'dist',
  assetsDir: 'static',
  productionSourceMap: false,
  
  // 添加开发服务器代理配置
  devServer: {
    host: '::',  // 启用IPv6监听，同时支持IPv4和IPv6
    port: 8080,
    allowedHosts: 'all',  // 允许所有主机访问
    historyApiFallback: true,  // 🔥 添加：支持 SPA 路由
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
  },
  
  // 🔥 添加：生产环境优化配置
  chainWebpack: config => {
    if (process.env.NODE_ENV === 'production') {
      // 删除预加载和预获取，减少初始加载时间
      config.plugins.delete('preload')
      config.plugins.delete('prefetch')
      
      // 优化分包策略
      config.optimization.splitChunks({
        chunks: 'all',
        cacheGroups: {
          vendor: {
            name: 'chunk-vendors',
            test: /[\\/]node_modules[\\/]/,
            priority: 10,
            chunks: 'initial'
          },
          common: {
            name: 'chunk-common',
            minChunks: 2,
            priority: 5,
            chunks: 'initial',
            reuseExistingChunk: true
          }
        }
      })
    }
  },
  
  // 🔥 添加：PWA 配置（可选）
  pwa: {
    name: 'GIS Server Management System',
    themeColor: '#4DBA87',
    msTileColor: '#000000',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',
    workboxPluginMode: 'InjectManifest',
    workboxOptions: {
      swSrc: 'src/service-worker.js'
    }
  }
})
