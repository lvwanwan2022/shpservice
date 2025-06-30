<template>
  <div class="auth-debug" style="position: fixed; top: 100px; right: 20px; background: white; border: 1px solid #ccc; padding: 10px; border-radius: 4px; z-index: 9999; font-size: 12px;">
    <h4>认证调试信息</h4>
    <p><strong>是否登录:</strong> {{ isLoggedIn }}</p>
    <p><strong>Token:</strong> {{ token ? '有' : '无' }}</p>
    <p><strong>用户信息:</strong></p>
    <pre>{{ JSON.stringify(userInfo, null, 2) }}</pre>
    <button @click="refresh">刷新</button>
    <button @click="close">关闭</button>
  </div>
</template>

<script>
import authService from './authService'

export default {
  name: 'AuthDebug',
  data() {
    return {
      isLoggedIn: false,
      token: null,
      userInfo: {}
    }
  },
  
  mounted() {
    this.refresh()
    
    // 监听状态变化
    this.authListener = () => {
      this.refresh()
    }
    authService.addListener(this.authListener)
  },
  
  beforeUnmount() {
    if (this.authListener) {
      authService.removeListener(this.authListener)
    }
  },
  
  methods: {
    refresh() {
      this.isLoggedIn = authService.isAuthenticated()
      this.token = authService.getToken()
      this.userInfo = authService.getUser()
      
    },
    
    close() {
      this.$emit('close')
    }
  }
}
</script> 