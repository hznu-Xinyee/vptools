<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- 左侧品牌区域 -->
      <BrandSection />

      <!-- 右侧表单区域 -->
      <div class="form-section">
        <div class="form-wrapper">
          <!-- 登录表单 -->
          <div v-if="mode === 'login'" class="form-content">
            <h1 class="form-title">登录您的账户</h1>
            <p class="form-subtitle">欢迎回来，请使用您的账号登录</p>

            <form @submit.prevent="handleLogin" class="auth-form">
              <FormField
                v-model="loginForm.username"
                type="text"
                label="用户名"
                placeholder="请输入用户名"
                :disabled="loading"
                required
              />

              <FormField
                v-model="loginForm.password"
                type="password"
                label="密码"
                placeholder="请输入密码"
                :disabled="loading"
                :show-toggle="true"
                required
              />

              <div v-if="error" class="error-message">{{ error }}</div>

              <SubmitButton
                :loading="loading"
                text="登录"
                loading-text="登录中..."
              />
            </form>

            <div class="switch-mode">
              <span>还没有账号？</span>
              <a href="#" @click.prevent="switchToRegister" class="link">立即注册</a>
            </div>
          </div>

          <!-- 注册表单 -->
          <div v-else class="form-content">
            <h1 class="form-title">创建新账户</h1>
            <p class="form-subtitle">加入我们，开启智能视频处理之旅</p>

            <form @submit.prevent="handleRegister" class="auth-form">
              <FormField
                v-model="registerForm.username"
                type="text"
                label="用户名"
                placeholder="请输入用户名（3-20位）"
                :error="errors.username"
                :disabled="loading"
                required
              />

              <FormField
                v-model="registerForm.email"
                type="email"
                label="邮箱"
                placeholder="请输入邮箱地址"
                :error="errors.email"
                :disabled="loading"
                required
              />

              <FormField
                v-model="registerForm.password"
                type="password"
                label="密码"
                placeholder="请输入密码（至少8位）"
                :error="errors.password"
                :disabled="loading"
                :show-toggle="true"
                required
              />

              <FormField
                v-model="registerForm.confirmPassword"
                type="password"
                label="确认密码"
                placeholder="请再次输入密码"
                :error="errors.confirmPassword"
                :disabled="loading"
                :show-toggle="true"
                required
              />

              <div v-if="error" class="error-message">{{ error }}</div>

              <SubmitButton
                :loading="loading"
                text="注册"
                loading-text="注册中..."
              />
            </form>

            <div class="switch-mode">
              <span>已有账户？</span>
              <a href="#" @click.prevent="switchToLogin" class="link">前往登录</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import BrandSection from '../components/auth/BrandSection.vue'
import FormField from '../components/auth/FormField.vue'
import SubmitButton from '../components/auth/SubmitButton.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const mode = ref('login')
const loading = ref(false)
const error = ref('')

const loginForm = ref({
  username: '',
  password: ''
})

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const errors = computed(() => {
  const errs = {}

  if (registerForm.value.username && (registerForm.value.username.length < 3 || registerForm.value.username.length > 20)) {
    errs.username = '用户名长度应为3-20位'
  }

  if (registerForm.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.value.email)) {
    errs.email = '请输入有效的邮箱地址'
  }

  if (registerForm.value.password && registerForm.value.password.length < 8) {
    errs.password = '密码长度至少为8位'
  }

  if (registerForm.value.confirmPassword && registerForm.value.password !== registerForm.value.confirmPassword) {
    errs.confirmPassword = '两次输入的密码不一致'
  }

  return errs
})

const switchToRegister = () => {
  mode.value = 'register'
  error.value = ''
  router.push('/register')
}

const switchToLogin = () => {
  mode.value = 'login'
  error.value = ''
  router.push('/login')
}

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  const result = await authStore.login(loginForm.value.username, loginForm.value.password)

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error
  }

  loading.value = false
}

const handleRegister = async () => {
  if (Object.keys(errors.value).length > 0) {
    error.value = '请检查输入信息'
    return
  }

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  error.value = ''

  const result = await authStore.register(
    registerForm.value.username,
    registerForm.value.email,
    registerForm.value.password
  )

  if (result.success) {
    switchToLogin()
  } else {
    error.value = result.error
  }

  loading.value = false
}

onMounted(() => {
  if (route.path === '/register') {
    mode.value = 'register'
  } else {
    mode.value = 'login'
  }
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #000000;
  display: flex;
  position: relative;
  overflow: hidden;
}

.auth-container {
  width: 100%;
  height: 100vh;
  display: flex;
  background: #000000;
  position: relative;
  z-index: 2;
}

.form-section {
  flex: 1;
  background: #000000;
  padding: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

.form-wrapper {
  width: 100%;
  max-width: 360px;
}

.form-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
  text-align: center;
}

.form-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  margin-bottom: 32px;
}

.auth-form {
  margin-bottom: 24px;
}

.error-message {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: rgba(239, 68, 68, 0.9);
  font-size: 13px;
  text-align: center;
}

.switch-mode {
  text-align: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  margin-left: 4px;
  transition: color 0.2s;
  cursor: pointer;
}

.link:hover {
  color: #ffffff;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .auth-container {
    flex-direction: column;
    max-width: 500px;
    height: auto;
    margin: 10px;
  }

  .form-section {
    padding: 40px 30px;
  }
}
</style>
