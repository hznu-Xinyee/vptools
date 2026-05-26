<template>
  <div :class="containerClass">
    <!-- Desktop/Tablet: Side-by-side comparison -->
    <div v-if="showComparison && !isMobile" class="flex gap-4 md:gap-6 items-start justify-center w-full">
      <!-- Original Video -->
      <div :class="videoColumnClass">
        <div class="text-xs text-gray-500 mb-1 text-center">{{ originalLabel }}</div>
        <div class="w-full flex items-center justify-center">
          <video
            v-if="originalVideoUrl"
            :src="originalVideoUrl"
            controls
            class="w-full max-h-[50vh] rounded-lg shadow"
          ></video>
          <div v-else class="w-full aspect-video flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
            <slot name="original-placeholder">
              <div class="text-center text-gray-400 text-sm">无原视频</div>
            </slot>
          </div>
        </div>
      </div>

      <!-- Divider -->
      <div class="w-px bg-gray-300 self-stretch min-h-[40vh]"></div>

      <!-- Translated Video -->
      <div :class="videoColumnClass">
        <div class="text-xs text-gray-500 mb-1 text-center">{{ translatedLabel }}</div>
        <div class="w-full flex items-center justify-center">
          <video
            v-if="translatedVideoUrl"
            :src="translatedVideoUrl"
            controls
            class="w-full max-h-[50vh] rounded-lg shadow"
          ></video>
          <div v-else class="w-full aspect-video flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
            <slot name="translated-placeholder">
              <div class="text-center text-gray-400 text-sm">{{ translatedPlaceholder }}</div>
            </slot>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile: Stacked Videos -->
    <div v-else-if="showComparison && isMobile" class="flex flex-col gap-4 w-full max-w-md mx-auto">
      <!-- Original Video -->
      <div class="w-full">
        <div class="text-xs text-gray-500 mb-1">{{ originalLabel }}</div>
        <video
          v-if="originalVideoUrl"
          :src="originalVideoUrl"
          controls
          class="w-full rounded-lg shadow"
        ></video>
        <div v-else class="w-full aspect-video flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <slot name="original-placeholder">
            <div class="text-center text-gray-400 text-sm">无原视频</div>
          </slot>
        </div>
      </div>

      <!-- Translated Video -->
      <div class="w-full">
        <div class="text-xs text-gray-500 mb-1">{{ translatedLabel }}</div>
        <video
          v-if="translatedVideoUrl"
          :src="translatedVideoUrl"
          controls
          class="w-full rounded-lg shadow"
        ></video>
        <div v-else class="w-full aspect-video flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <slot name="translated-placeholder">
            <div class="text-center text-gray-400 text-sm">{{ translatedPlaceholder }}</div>
          </slot>
        </div>
      </div>
    </div>

    <!-- Single Video -->
    <div v-else class="w-full flex items-center justify-center">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBreakpoint } from '@/composables/useBreakpoint'

const props = defineProps({
  showComparison: {
    type: Boolean,
    default: false
  },
  originalVideoUrl: {
    type: String,
    default: ''
  },
  translatedVideoUrl: {
    type: String,
    default: ''
  },
  originalLabel: {
    type: String,
    default: '原视频'
  },
  translatedLabel: {
    type: String,
    default: '翻译后'
  },
  translatedPlaceholder: {
    type: String,
    default: '视频生成中'
  }
})

const { isMobile, isTablet } = useBreakpoint()

const containerClass = computed(() => {
  return 'w-full h-full flex items-center justify-center p-4 md:p-6'
})

const videoColumnClass = computed(() => {
  if (isMobile.value) return 'w-full'
  if (isTablet.value) return 'flex-1 max-w-[400px]'
  return 'flex-1 max-w-[460px]'
})
</script>
