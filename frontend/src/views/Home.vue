<!--
 * @Author: Lvwan-793145268@qq.com
 * @Date: 2025-05-11 22:20:44
 * @LastEditors: Lvwan-793145268@qq.com
 * @LastEditTime: 2025-06-05 16:38:50
 * @FilePath: \shpservice\frontend\src\views\Home.vue
 * @Description: 
 * Copyright (c) 2025 by Lvwan, All Rights Reserved. 
-->
<template>
  <div class="home-container">
    <h1>GIS服务管理系统</h1>
    <div class="home-card-container">

      <el-card class="home-card" @click="goToUpload">
        <div class="card-icon">
          <i class="el-icon-upload"></i>
        </div>
        <div class="card-title">数据上传</div>
        <div class="card-desc">上传SHP等GIS文件数据</div>
      </el-card>
      <el-card class="home-card" @click="goToScene">
        <div class="card-icon">
          <i class="el-icon-menu"></i>
        </div>
        <div class="card-title">场景管理</div>
        <div class="card-desc">创建和管理地图场景配置</div>
      </el-card>
      <el-card class="home-card" @click="goToMapOL">
        <div class="card-icon">
          <i class="el-icon-location"></i>
        </div>
        <div class="card-title">地图浏览(OpenLayers)</div>
        <div class="card-desc">使用OpenLayers浏览地图服务和图层数据</div>
      </el-card>
      <el-card class="home-card" @click="goToMap">
        <div class="card-icon">
          <i class="el-icon-map-location"></i>
        </div>
        <div class="card-title">地图浏览(Leaflet-测试)</div>
        <div class="card-desc">使用Leaflet浏览地图服务和图层数据</div>
      </el-card>
      
     

      <el-card class="home-card" @click="goToFeedback">
        <div class="card-icon">
          <i class="el-icon-chat-line-square"></i>
        </div>
        <div class="card-title">用户反馈</div>
        <div class="card-desc">提交反馈建议，参与产品改进</div>
      </el-card>
      
      
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
  methods: {
    goToMap() {
      this.$router.push('/map-lf')
    },
    goToMapOL() {
      this.$router.push('/map-ol')
    },
    goToUpload() {
      this.$router.push('/upload')
    },
    goToScene() {
      this.$router.push('/scene')
    },
    goToFeedback() {
      this.$router.push('/feedback')
    }
  }
}
</script>

<style scoped>
.home-container {
  padding: 20px;
  text-align: center;
}

.home-card-container {
  display: flex;
  justify-content: center;
  margin-top: 50px;
  flex-wrap: wrap;
}

.home-card {
  width: 220px;
  height: 200px;
  margin: 20px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.home-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.card-icon {
  font-size: 50px;
  color: #409EFF;
  margin-bottom: 15px;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
}

.card-desc {
  color: #666;
  font-size: 14px;
}
</style> 