<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>AI Talk</h1>
        <p>智能对话系统</p>
      </div>
      
      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- 登录表单 -->
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-width="0"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名"
                size="large"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                show-password
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loginLoading"
                @click="handleLogin"
                class="login-btn"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 注册表单 -->
        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-width="0"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="用户名"
                size="large"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="邮箱"
                size="large"
              >
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="密码"
                size="large"
                show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="确认密码"
                size="large"
                show-password
                @keyup.enter="handleRegister"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="registerLoading"
                @click="handleRegister"
                class="login-btn"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { authAPI } from '../api'

export default {
  name: 'Login',
  components: {
    User,
    Lock,
    Message
  },
  setup() {
    const router = useRouter()
    const activeTab = ref('login')
    const loginLoading = ref(false)
    const registerLoading = ref(false)
    
    // 登录表单
    const loginFormRef = ref()
    const loginForm = reactive({
      username: '',
      password: ''
    })
    
    const loginRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }
    
    // 注册表单
    const registerFormRef = ref()
    const registerForm = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== registerForm.password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }
    
    const registerRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请确认密码', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }
    
    // 登录处理
    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      try {
        await loginFormRef.value.validate()
        loginLoading.value = true
        
        const response = await authAPI.login({
          username: loginForm.username,
          password: loginForm.password
        })
        
        // 保存 token 和用户信息
        localStorage.setItem('token', response.access_token)
        localStorage.setItem('user', JSON.stringify({
          username: loginForm.username
        }))
        
        ElMessage.success('登录成功')
        router.push('/chat')
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loginLoading.value = false
      }
    }
    
    // 注册处理
    const handleRegister = async () => {
      if (!registerFormRef.value) return
      
      try {
        await registerFormRef.value.validate()
        registerLoading.value = true
        
        await authAPI.register({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })
        
        ElMessage.success('注册成功，请登录')
        activeTab.value = 'login'
        
        // 清空注册表单
        Object.keys(registerForm).forEach(key => {
          registerForm[key] = ''
        })
      } catch (error) {
        console.error('注册失败:', error)
      } finally {
        registerLoading.value = false
      }
    }
    
    return {
      activeTab,
      loginLoading,
      registerLoading,
      loginFormRef,
      loginForm,
      loginRules,
      registerFormRef,
      registerForm,
      registerRules,
      handleLogin,
      handleRegister
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 32px;
  color: #333;
  margin-bottom: 10px;
}

.login-header p {
  color: #666;
  font-size: 14px;
}

.login-tabs {
  margin-bottom: 20px;
}

.login-form {
  margin-top: 20px;
}

.login-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  padding: 12px 15px;
}
</style> 