<template>
  <div class="min-h-screen bg-neutral-800 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <h1 class="text-3xl font-bold text-white mb-2 text-center">VP视频工具箱</h1>
      <h2 class="text-xl font-medium text-neutral-200 mb-8 text-center">登录</h2>
      <form @submit.prevent="handleLogin" class="space-y-6">
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
        <div v-if="error" class="text-sm text-red-400 text-center py-2">{{ error }}</div>
        <button 
          type="submit" 
          :disabled="loading"
          class="w-full px-4 py-3 bg-neutral-200 text-neutral-900 rounded-md font-medium hover:bg-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <p class="text-center mt-6 text-sm text-neutral-400">
        还没有账号？
        <router-link to="/register" class="text-neutral-200 hover:underline transition-all duration-200">
          立即注册
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
