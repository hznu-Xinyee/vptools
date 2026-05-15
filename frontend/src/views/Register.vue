<template>
  <div class="min-h-screen bg-neutral-800 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <h2 class="text-2xl font-medium text-neutral-200 mb-8 text-center">注册</h2>
      <form @submit.prevent="handleRegister" class="space-y-6">
        <div class="space-y-2">
          <label for="username" class="text-sm text-neutral-400">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            required
            class="w-full px-4 py-3 bg-neutral-700 text-neutral-200 placeholder-neutral-400 rounded-md focus:outline-none focus:ring-0 transition-all duration-200"
          />
        </div>
        <div class="space-y-2">
          <label for="email" class="text-sm text-neutral-400">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="请输入邮箱"
            required
            class="w-full px-4 py-3 bg-neutral-700 text-neutral-200 placeholder-neutral-400 rounded-md focus:outline-none focus:ring-0 transition-all duration-200"
          />
        </div>
        <div class="space-y-2">
          <label for="password" class="text-sm text-neutral-400">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            required
            class="w-full px-4 py-3 bg-neutral-700 text-neutral-200 placeholder-neutral-400 rounded-md focus:outline-none focus:ring-0 transition-all duration-200"
          />
        </div>
        <div class="space-y-2">
          <label for="confirmPassword" class="text-sm text-neutral-400">确认密码</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            class="w-full px-4 py-3 bg-neutral-700 text-neutral-200 placeholder-neutral-400 rounded-md focus:outline-none focus:ring-0 transition-all duration-200"
          />
        </div>
        <div v-if="error" class="text-sm text-red-400 text-center py-2">{{ error }}</div>
        <button 
          type="submit" 
          :disabled="loading"
          class="w-full px-4 py-3 bg-neutral-200 text-neutral-900 rounded-md font-medium hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <p class="text-center mt-6 text-sm text-neutral-400">
        已有账号？
        <router-link to="/login" class="text-neutral-200 hover:underline transition-all duration-200">
          立即登录
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

const handleRegister = async () => {
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
