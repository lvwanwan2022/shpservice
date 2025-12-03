const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 8080;

// 静态文件服务
app.use(express.static(path.join(__dirname, 'dist')));

// API 代理配置
const backend_url = 'http://10.20.148.169:5030';
const MARTIN_BASE_URL = 'http://10.20.148.169:3000';
const GEOSERVER_BASE_URL = 'http://10.20.148.169:8083';

// 代理 API 请求到后端
app.use('/api', createProxyMiddleware({
  target: backend_url,
  changeOrigin: true,
  logLevel: 'debug',
  onError: (err, req, res) => {
    console.error('API代理错误:', err.message);
  }
}));

// 代理 Martin 请求
app.use('/martin', createProxyMiddleware({
  target: MARTIN_BASE_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/martin': ''
  },
  logLevel: 'debug',
  onError: (err, req, res) => {
    console.error('Martin代理错误:', err.message);
  }
}));

// 代理 GeoServer 请求
app.use('/geoserver', createProxyMiddleware({
  target: GEOSERVER_BASE_URL,
  changeOrigin: true,
  logLevel: 'debug',
  onError: (err, req, res) => {
    console.error('GeoServer代理错误:', err.message);
  }
}));

// SPA 路由支持 - 所有其他请求都返回 index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('🚀 前端生产服务器已启动!');
  console.log(`📱 本地访问: http://localhost:${PORT}`);
  console.log(`🌐 网络访问: http://10.20.148.169:${PORT}`);
  console.log('✅ 支持 SPA 路由和 API 代理');
});
