<template>
  <div id="app">
    <el-container>
      <el-header height="60px">
        <nav class="main-header">
          <div class="logo">
            <router-link to="/">GIS服务管理系统</router-link>
          </div>
          <div class="nav-links">
            <router-link to="/">首页</router-link>
            <router-link to="/map">地图浏览(Leaflet)</router-link>
            <router-link to="/map-ol">地图浏览(OpenLayers)</router-link>
            <router-link to="/scene">场景管理</router-link>
            <router-link to="/upload">数据上传</router-link>
          </div>
        </nav>
      </el-header>
      <el-main>
        <router-view/>
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, Helvetica, sans-serif;
}

#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.el-header {
  background-color: #409EFF;
  color: white;
  padding: 0;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.logo a {
  color: white;
  font-size: 1.2rem;
  font-weight: bold;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 4px;
}

.nav-links a:hover, .nav-links a.router-link-active {
  background-color: rgba(255, 255, 255, 0.2);
}

.el-main {
  padding: 0;
  height: calc(100vh - 60px);
  overflow: hidden;
}
</style>
