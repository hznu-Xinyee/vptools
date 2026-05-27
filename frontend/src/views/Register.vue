<template>
  <div class="register-page">
    <MouseFollower />

    <div class="register-container">
      <!-- 左侧品牌区域 -->
      <BrandSection />

      <!-- 右侧注册表单 -->
      <div class="form-section">
        <div class="form-wrapper">
          <h1 class="form-title">创建新账户</h1>
          <p class="form-subtitle">加入我们，开启智能视频处理之旅</p>

          <form @submit.prevent="handleRegister" class="register-form">
            <FormField
              v-model="username"
              type="text"
              label="用户名"
              placeholder="请输入用户名（3-20位）"
              :error="errors.username"
              :disabled="loading"
              required
            />

            <FormField
              v-model="email"
              type="email"
              label="邮箱"
              placeholder="请输入邮箱地址"
              :error="errors.email"
              :disabled="loading"
              required
            />

            <FormField
              v-model="password"
              type="password"
              label="密码"
              placeholder="请输入密码（至少8位）"
              :error="errors.password"
              :disabled="loading"
              :show-toggle="true"
              required
            />

            <FormField
              v-model="confirmPassword"
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
            <router-link to="/login" class="link">前往登录</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import MouseFollower from '../components/auth/MouseFollower.vue'
import BrandSection from '../components/auth/BrandSection.vue'
import FormField from '../components/auth/FormField.vue'
import SubmitButton from '../components/auth/SubmitButton.vue'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

const errors = computed(() => {
  const errs = {}

  if (username.value && (username.value.length < 3 || username.value.length > 20)) {
    errs.username = '用户名长度应为3-20位'
  }

  if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errs.email = '请输入有效的邮箱地址'
  }

  if (password.value && password.value.length < 8) {
    errs.password = '密码长度至少为8位'
  }

  if (confirmPassword.value && password.value !== confirmPassword.value) {
    errs.confirmPassword = '两次输入的密码不一致'
  }

  return errs
})

const handleRegister = async () => {
  if (Object.keys(errors.value).length > 0) {
    error.value = '请检查输入信息'
    return
  }

  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  error.value = ''

  const result = await authStore.register(username.value, email.value, password.value)

  if (result.success) {
    router.push('/login')
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: #000000;
  display: flex;
  position: relative;
  overflow: hidden;
}

.register-container {
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
  /* 隐藏滚动条但保持滚动功能 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.form-section::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
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

.register-form {
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
  .register-container {
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
