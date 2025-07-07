<template>
  <div id="app">
    <el-container>
      <el-header height="60px">
        <nav class="main-header">
          <!-- 移动端菜单按钮 -->
          <div class="mobile-menu-btn" @click="toggleMobileMenu">
            <el-icon size="24"><Menu /></el-icon>
          </div>
          
          <div class="logo">
            <router-link to="/">GIS服务管理系统</router-link>
          </div>
          
          <div class="nav-center">
            <div class="nav-links">
              <router-link to="/">首页</router-link>
              <router-link to="/upload">数据上传</router-link>
              <router-link to="/scene">场景管理</router-link>
              <!-- <router-link to="/map-lf">地图浏览(Leaflet)</router-link> -->
              <router-link to="/map-ol">地图浏览(OpenLayers)</router-link>
              
              <router-link to="/cache-manager">缓存管理</router-link>
            </div>
          </div>
          
          <!-- 登录认证模块 - 用户信息组件 -->
          <div class="user-section">
            <UserInfo />
          </div>
        </nav>
      </el-header>
      
      <!-- 移动端导航抽屉 -->
      <el-drawer
        v-model="mobileMenuVisible"
        title="导航菜单"
        direction="ltr"
        size="280px"
        :modal="true"
        :show-close="true"
      >
        <div class="mobile-nav-menu">
          <div class="mobile-nav-item" 
               v-for="item in navItems" 
               :key="item.path"
               @click="navigateToPage(item.path)"
               :class="{ active: $route.path === item.path }">
            <el-icon size="20" class="nav-icon">
              <component :is="item.icon" />
            </el-icon>
            <span class="nav-text">{{ item.name }}</span>
          </div>
        </div>
      </el-drawer>
      
      <el-main>
        <router-view/>
        <!-- 临时调试组件 -->
        <AuthDebug v-if="showDebug" @close="showDebug = false" />
      </el-main>
    </el-container>
  </div>
</template>

<script>
// 登录认证模块 - 导入用户信息组件
import UserInfo from '@/auth/UserInfo.vue'
import AuthDebug from '@/auth/AuthDebug.vue'
import { 
  Menu, House, Upload, Film, 
  MapLocation, Setting 
} from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    UserInfo,
    AuthDebug,
    Menu,
    House,
    Upload,
    Film,
    MapLocation,
    Setting
  },
  data() {
    return {
      showDebug: false,  // 临时开启调试
      mobileMenuVisible: false,  // 移动端菜单可见性
      navItems: [
        { path: '/', name: '首页', icon: 'House' },
        { path: '/upload', name: '数据上传', icon: 'Upload' },
        { path: '/scene', name: '场景管理', icon: 'Film' },
        { path: '/map-ol', name: '地图浏览', icon: 'MapLocation' },
        { path: '/cache-manager', name: '缓存管理', icon: 'Setting' }
      ]
    }
  },
  methods: {
    toggleMobileMenu() {
      this.mobileMenuVisible = !this.mobileMenuVisible
    },
    navigateToPage(path) {
      this.$router.push(path)
      this.mobileMenuVisible = false  // 导航后关闭菜单
    }
  }
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

.nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
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
  transition: background-color 0.3s;
}

.nav-links a:hover, .nav-links a.router-link-active {
  background-color: rgba(255, 255, 255, 0.2);
}

.user-section {
  display: flex;
  align-items: center;
}

.el-main {
  padding: 0;
  height: calc(100vh - 60px);
  overflow: hidden;
}

/* 桌面端隐藏移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
}
</style>
