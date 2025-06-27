<template>
  <div class="user-info">
    <!-- 未登录状态 -->
    <div v-if="!isLoggedIn" class="auth-buttons">
      <el-button 
        type="primary" 
        size="small" 
        @click="goToLogin"
        class="login-btn"
      >
        登录
      </el-button>
    </div>
    
    <!-- 已登录状态 -->
    <el-dropdown v-else @command="handleCommand" class="user-dropdown">
      <span class="user-trigger">
        <el-icon><User /></el-icon>
        <span class="username">{{ displayName }}</span>
        <el-icon class="el-icon--right"><ArrowDown /></el-icon>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item disabled>
            <div class="user-detail">
              <p><strong>用户名：</strong>{{ userInfo.username }}</p>
              <p><strong>姓名：</strong>{{ userInfo.name }}</p>
              <p><strong>角色：</strong>{{ getRoleName(userInfo.role) }}</p>
              <p v-if="userInfo.email"><strong>邮箱：</strong>{{ userInfo.email }}</p>
            </div>
          </el-dropdown-item>
          <el-dropdown-item divided command="profile">
            <el-icon><User /></el-icon> 个人资料
          </el-dropdown-item>
          <el-dropdown-item command="settings">
            <el-icon><Setting /></el-icon> 设置
          </el-dropdown-item>
          <el-dropdown-item divided command="logout">
            <el-icon><SwitchButton /></el-icon> 退出登录
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script>
import authService from './authService'
import { User, ArrowDown, Setting, SwitchButton } from '@element-plus/icons-vue'

export default {
  name: 'UserInfo',
  components: {
    User,
    ArrowDown,
    Setting,
    SwitchButton
  },
  data() {
    return {
      userInfo: {},
      isLoggedIn: false
    }
  },
  
  computed: {
    displayName() {
      if (!this.isLoggedIn || !this.userInfo) {
        return '未登录'
      }
      return this.userInfo.name || this.userInfo.username || '用户'
    }
  },
  
  created() {
    // 在组件创建时就检查状态
    this.checkAuthStatus()
  },
  
  mounted() {
    this.checkAuthStatus()
    
    // 添加登录状态监听器
    this.authListener = (event, isLoggedIn, userInfo) => {
      //console.log('用户状态变化:', { event, isLoggedIn, userInfo })
      this.isLoggedIn = isLoggedIn
      this.userInfo = userInfo || {}
    }
    authService.addListener(this.authListener)
    
    // 监听路由变化，确保状态更新
    this.$router.afterEach(() => {
      this.$nextTick(() => {
        this.checkAuthStatus()
      })
    })
  },
  
  beforeUnmount() {
    // 移除监听器
    if (this.authListener) {
      authService.removeListener(this.authListener)
    }
  },
  
  methods: {
    checkAuthStatus() {
      this.isLoggedIn = authService.isAuthenticated()
      if (this.isLoggedIn) {
        this.userInfo = authService.getUser() || {}
        //console.log('检查认证状态:', { 
          //isLoggedIn: this.isLoggedIn, 
          //userInfo: this.userInfo,
          //token: authService.getToken()
        //})
      } else {
        this.userInfo = {}
        //console.log('用户未登录')
      }
    },
    
    goToLogin() {
      this.$router.push('/login')
    },
    
    async handleCommand(command) {
      switch (command) {
        case 'profile':
          this.showProfile()
          break
        case 'settings':
          this.showSettings()
          break
        case 'logout':
          await this.handleLogout()
          break
      }
    },
    
    showProfile() {
      this.$message.info('个人资料功能开发中...')
    },
    
    showSettings() {
      this.$message.info('设置功能开发中...')
    },
    
    async handleLogout() {
      try {
        await authService.logout()
        this.$message.success('退出登录成功')
        this.checkAuthStatus()
        // 跳转到首页
        if (this.$route.path !== '/') {
          this.$router.push('/')
        }
      } catch (error) {
        console.error('退出登录失败:', error)
        this.$message.error('退出登录失败')
      }
    },
    
    getRoleName(role) {
      const roleMap = {
        'admin': '管理员',
        'user': '普通用户'
      }
      return roleMap[role] || role
    }
  }
}
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
  height: 100%;
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.login-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.login-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.user-dropdown {
  color: white;
  cursor: pointer;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-trigger:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.user-detail {
  padding: 5px 0;
  min-width: 200px;
}

.user-detail p {
  margin: 5px 0;
  font-size: 13px;
  color: #606266;
}

.user-detail strong {
  color: #303133;
}

/* 下拉菜单项图标样式 */
:deep(.el-dropdown-menu__item .el-icon) {
  margin-right: 8px;
  width: 16px;
}
</style> 