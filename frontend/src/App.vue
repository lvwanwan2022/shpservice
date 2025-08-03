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
              <router-link to="/service-manager">服务管理</router-link>
              <!-- <router-link to="/map-lf">地图浏览(Leaflet)</router-link> -->
              <router-link to="/map-ol">地图浏览(OpenLayers)</router-link>
              <router-link to="/map-deckgl">地图浏览(Deck.gl)</router-link>
              
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
  MapLocation, Setting, View 
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
    Setting,
    View
  },
  data() {
    return {
      showDebug: false,  // 临时开启调试
      mobileMenuVisible: false,  // 移动端菜单可见性
      navItems: [
        { path: '/', name: '首页', icon: 'House' },
        { path: '/upload', name: '数据上传', icon: 'Upload' },
        { path: '/scene', name: '场景管理', icon: 'Film' },
        { path: '/service-manager', name: '服务管理', icon: 'Setting' },
        { path: '/map-ol', name: '地图浏览(OpenLayers)', icon: 'MapLocation' },
        { path: '/map-deckgl', name: '地图浏览(Deck.gl)', icon: 'View' },
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

html, body {
  margin: 0 !important; /* 🔥 强制确保没有默认边距 */
  padding: 0 !important; /* 🔥 强制确保没有默认内边距 */
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important; /* 🔥 防止页面滚动 */
  font-family: Arial, Helvetica, sans-serif;
  background: transparent !important; /* 🔥 透明背景 */
  border: none !important; /* 🔥 移除可能的边框 */
  outline: none !important; /* 🔥 移除轮廓 */
  box-sizing: border-box !important; /* 🔥 确保盒模型 */
}

#app {
  width: 100% !important;
  height: 100vh !important;
  overflow: hidden !important;
  margin: 0 !important; /* 🔥 强制确保没有外边距 */
  padding: 0 !important; /* 🔥 强制确保没有内边距 */
  border: none !important; /* 🔥 移除边框 */
  outline: none !important; /* 🔥 移除轮廓 */
  box-sizing: border-box !important; /* 🔥 确保盒模型 */
  position: absolute !important; /* 🔥 绝对定位确保完全填充 */
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
}

/* 🔥 确保Element Plus容器组件没有默认边距 */
.el-container {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  height: 100vh !important;
}

/* 🔥 确保Vue组件根元素没有默认边距 */
div[data-v-inspector] {
  margin: 0 !important;
  padding: 0 !important;
}

/* 🔥 针对可能的Vue组件包装器 */
.el-main > div {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  height: 100% !important;
  border: none !important;
  background: transparent !important;
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
  padding: 0; /* 🔥 确保没有内边距 */
  margin: 0; /* 🔥 确保没有外边距 */
  height: calc(100vh - 60px); /* 🔥 精确计算高度：总视口高度减去导航栏高度 */
  width: 100%; /* 🔥 确保宽度100% */
  overflow: hidden;
  background: transparent; /* 🔥 透明背景 */
  border: none; /* 🔥 移除边框 */
}

/* 🔥 确保router-view没有默认边距，消除el-main和map-view之间的白边 */
.el-main {
  /* 使用flexbox确保子元素完全填充 */
  display: flex !important;
  flex-direction: column !important;
}

.el-main > .router-view,
.el-main > div:first-child {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  height: 100% !important;
  flex: 1 !important;
  border: none !important;
  background: transparent !important;
}

/* 桌面端隐藏移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
}
</style>
