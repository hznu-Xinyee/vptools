<template>
  <header class="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 h-14">
    <div class="flex items-center justify-between h-full px-4">
      <!-- Hamburger Menu Button -->
      <button
        @click="$emit('toggle-menu')"
        class="p-2 -ml-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition tap-target"
        aria-label="Toggle navigation menu"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Title -->
      <h1 class="text-base font-medium text-gray-900 truncate px-2">{{ title }}</h1>

      <!-- Config/Settings Button -->
      <button
        @click="$emit('toggle-config')"
        class="p-2 -mr-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition tap-target"
        aria-label="Toggle settings"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'VP智能视频翻译'
  }
})

defineEmits(['toggle-menu', 'toggle-config'])
</script>
