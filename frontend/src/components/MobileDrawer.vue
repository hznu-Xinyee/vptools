<template>
  <!-- Backdrop -->
  <Transition name="fade">
    <div
      v-if="isOpen"
      @click="$emit('close')"
      class="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
      aria-hidden="true"
    ></div>
  </Transition>

  <!-- Drawer -->
  <Transition :name="position === 'left' ? 'slide-left' : 'slide-right'">
    <aside
      v-if="isOpen"
      :class="[
        'fixed top-0 bottom-0 z-50 bg-white shadow-xl overflow-y-auto lg:hidden smooth-scroll',
        position === 'left' ? 'left-0' : 'right-0',
        width === 'narrow' ? 'w-64' : width === 'medium' ? 'w-80' : 'w-96'
      ]"
    >
      <!-- Close Button -->
      <div class="sticky top-0 z-10 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h2 class="text-base font-medium text-gray-900">{{ title }}</h2>
        <button
          @click="$emit('close')"
          class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition tap-target"
          aria-label="Close drawer"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="p-4">
        <slot></slot>
      </div>
    </aside>
  </Transition>
</template>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  position: {
    type: String,
    default: 'left',
    validator: (value) => ['left', 'right'].includes(value)
  },
  width: {
    type: String,
    default: 'medium',
    validator: (value) => ['narrow', 'medium', 'wide'].includes(value)
  }
})

defineEmits(['close'])
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active, .slide-left-leave-active {
  transition: transform 0.3s ease;
}
.slide-left-enter-from {
  transform: translateX(-100%);
}
.slide-left-leave-to {
  transform: translateX(-100%);
}

.slide-right-enter-active, .slide-right-leave-active {
  transition: transform 0.3s ease;
}
.slide-right-enter-from {
  transform: translateX(100%);
}
.slide-right-leave-to {
  transform: translateX(100%);
}
</style>
