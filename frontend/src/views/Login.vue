<template>
  <div class="login-page">
    <MouseFollower />

    <div class="login-container">
      <!-- 左侧品牌区域 -->
      <BrandSection />

      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-wrapper">
          <h1 class="form-title">登录您的账户</h1>
          <p class="form-subtitle">欢迎回来，请使用您的账号登录</p>

          <form @submit.prevent="handleLogin" class="login-form">
            <FormField
              v-model="username"
              type="text"
              label="用户名"
              placeholder="请输入用户名"
              :error="error && !username ? '请输入用户名' : ''"
              :disabled="loading"
              required
            />

            <FormField
              v-model="password"
              type="password"
              label="密码"
              placeholder="请输入密码"
              :error="error && !password ? '请输入密码' : ''"
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
            <router-link to="/register" class="link">立即注册</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import MouseFollower from '../components/auth/MouseFollower.vue'
import BrandSection from '../components/auth/BrandSection.vue'
import FormField from '../components/auth/FormField.vue'
import SubmitButton from '../components/auth/SubmitButton.vue'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  const result = await authStore.login(username.value, password.value)

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #000000;
  display: flex;
  position: relative;
  overflow: hidden;
}

.login-container {
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
}

.form-wrapper {
  width: 100%;
  max-width: 360px;
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

.login-form {
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
}

.link:hover {
  color: #ffffff;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .login-container {
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
