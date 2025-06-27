<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <h2>用户注册</h2>
        <p>创建您的新账户</p>
      </div>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="registerForm.username"
            type="text"
            placeholder="请输入用户名（至少3位）"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="registerForm.email"
            type="email"
            placeholder="请输入邮箱地址"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            :disabled="loading"
          />
        </div>
        
        <button
          type="submit"
          class="register-btn"
          :disabled="loading"
        >
          <span v-if="loading">注册中...</span>
          <span v-else>注册</span>
        </button>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </form>
      
      <div class="register-footer">
        <p>
          已有账户？
          <router-link to="/login" class="login-link">立即登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import authService from './authService'

export default {
  name: 'RegisterPage',
  data() {
    return {
      registerForm: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      loading: false,
      errorMessage: ''
    }
  },
  
  created() {
    // 如果已经登录，重定向到首页
    if (authService.isAuthenticated()) {
      this.$router.push('/')
    }
  },
  
  methods: {
    async handleRegister() {
      this.loading = true
      this.errorMessage = ''
      
      try {
        // 表单验证
        if (!this.validateForm()) {
          this.loading = false
          return
        }
        
        //console.log('开始注册用户:', this.registerForm.username)
        
        const result = await authService.register(
          this.registerForm.username,
          this.registerForm.password,
          this.registerForm.email
        )
        
        //console.log('注册API返回结果:', result)
        
        if (result.success) {
          this.$message?.success?.(result.message || '注册成功')
          //console.log('注册成功，用户信息:', result.data)
          
          // 注册成功后跳转到登录页面
          setTimeout(() => {
            this.$router.push({
              path: '/login',
              query: { message: '注册成功，请登录' }
            })
          }, 1000)
        } else {
          this.errorMessage = result.message
          console.error('注册失败:', result.message)
        }
      } catch (error) {
        this.errorMessage = '注册失败，请稍后重试'
        console.error('注册异常:', error)
        
        // 如果是网络错误，提供更详细的错误信息
        if (error.response) {
          console.error('服务器响应错误:', error.response.data)
          this.errorMessage = error.response.data.message || '服务器错误，请稍后重试'
        } else if (error.request) {
          console.error('网络请求错误:', error.request)
          this.errorMessage = '网络连接失败，请检查网络连接'
        }
      } finally {
        this.loading = false
      }
    },
    
    validateForm() {
      // 用户名验证
      if (this.registerForm.username.length < 3) {
        this.errorMessage = '用户名长度不能少于3位'
        return false
      }
      
      // 邮箱格式验证
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(this.registerForm.email)) {
        this.errorMessage = '请输入有效的邮箱地址'
        return false
      }
      
      // 密码验证
      if (this.registerForm.password.length < 6) {
        this.errorMessage = '密码长度不能少于6位'
        return false
      }
      
      // 确认密码验证
      if (this.registerForm.password !== this.registerForm.confirmPassword) {
        this.errorMessage = '两次输入的密码不一致'
        return false
      }
      
      return true
    }
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-box {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  color: #333;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.register-header p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

.register-form {
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
.form-group input[type="email"],
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
.form-group input[type="email"]:focus,
.form-group input[type="password"]:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.register-btn {
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
  margin-bottom: 15px;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.register-btn:disabled {
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

.register-footer {
  margin-top: 20px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e1e5e9;
}

.register-footer p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.login-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.login-link:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-container {
    padding: 10px;
  }
  
  .register-box {
    padding: 30px 20px;
  }
  
  .register-header h2 {
    font-size: 24px;
  }
}
</style> 