<template>
  <div class="brand-section">
    <Particles
      :particle-count="isMobile ? 60 : 160"
      :particle-spread="10"
      :speed="0.05"
      :particle-colors="['#ffffff', '#818cf8', '#c084fc', '#e0f2fe']"
      :move-particles-on-hover="true"
      :particle-hover-factor="0.4"
      :alpha-particles="true"
      :particle-base-size="isMobile ? 80 : 120"
      :size-randomness="1.0"
      :camera-distance="20"
      :disable-rotation="false"
      :pixel-ratio="pixelRatio"
    />
    <div class="brand-content">
      <h1 class="brand-title">MiraClip</h1>
      <p class="brand-subtitle">智能视频翻译平台</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Particles from '../Particles.vue'

const isMobile = ref(false)
const pixelRatio = ref(1)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  pixelRatio.value = Math.min(window.devicePixelRatio || 1, 2)
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.brand-section {
  flex: 1;
  background: radial-gradient(circle at 50% 40%, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.05) 40%, #000000 100%);
  padding: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 2;
  text-align: center;
  pointer-events: none; /* Allow mouse events to pass through to the canvas underneath */
}

.brand-title {
  font-size: 52px;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 18px;
  background: linear-gradient(135deg, #ffffff 30%, rgba(255, 255, 255, 0.75) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.03em;
  text-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
}

.brand-subtitle {
  font-size: 16px;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.25em;
  text-transform: uppercase;
  padding-left: 0.25em; /* Offset for letter-spacing to ensure absolute horizontal centering */
}

@media (max-width: 768px) {
  .brand-section {
    display: none;
  }
}
</style>
