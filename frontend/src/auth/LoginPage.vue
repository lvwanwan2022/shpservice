<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>系统登录</h2>
        <p>请输入您的用户名和密码</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="loginForm.username"
            type="text"
            placeholder="请输入用户名"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group remember-me">
          <label>
            <input
              v-model="loginForm.rememberMe"
              type="checkbox"
              :disabled="loading"
            />
            <span>记住我</span>
          </label>
        </div>
        
        <button
          type="submit"
          class="login-btn"
          :disabled="loading"
        >
          <span v-if="loading">登录中...</span>
          <span v-else>登录</span>
        </button>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </form>
      
      <div class="login-footer">
        <p>测试账号: admin/admin123 </p>
        <p>
          还没有账户？
          <router-link to="/register" class="register-link">立即注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import authService from './authService'

export default {
  name: 'LoginPage',
  data() {
    return {
      loginForm: {
        username: '',
        password: '',
        rememberMe: false
      },
      loading: false,
      errorMessage: ''
    }
  },
  
  created() {
    // 如果已经登录，重定向到首页
    if (authService.isAuthenticated()) {
      this.redirectAfterLogin()
    }
    
    // 检查是否有来自注册页面的消息
    if (this.$route.query.message) {
      this.$message?.success?.(this.$route.query.message)
    }
  },
  
  methods: {
    async handleLogin() {
      this.loading = true
      this.errorMessage = ''
      
      try {
        const result = await authService.login(
          this.loginForm.username,
          this.loginForm.password
        )
        
        if (result.success) {
          this.$message?.success?.(result.data.message || '登录成功')
          //console.log('登录成功，用户信息:', result.data.user)
          // 给一点时间让状态更新
          setTimeout(() => {
            this.redirectAfterLogin()
          }, 100)
        } else {
          this.errorMessage = result.message
        }
      } catch (error) {
        this.errorMessage = '登录失败，请稍后重试'
        console.error('登录错误:', error)
      } finally {
        this.loading = false
      }
    },
    
    redirectAfterLogin() {
      // 获取重定向路径
      const redirect = this.$route.query.redirect || '/'
      this.$router.push(redirect)
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  color: #333;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.login-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.login-form {
  width: 100%;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.form-group input[type="text"],
.form-group input[type="password"] {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.form-group input[type="text"]:focus,
.form-group input[type="password"]:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.remember-me {
  margin-bottom: 25px;
}

.remember-me label {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 0;
}

.remember-me input[type="checkbox"] {
  margin-right: 8px;
  width: auto;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  color: #e74c3c;
  text-align: center;
  margin-top: 15px;
  padding: 12px;
  background-color: #fdf2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 14px;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e1e5e9;
}

.login-footer p {
  color: #888;
  font-size: 12px;
  margin: 0;
}

.register-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.register-link:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    padding: 10px;
  }
  
  .login-box {
    padding: 30px 20px;
  }
  
  .login-header h2 {
    font-size: 24px;
  }
}
</style> 