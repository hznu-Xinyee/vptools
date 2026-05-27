<template>
  <div class="brand-section">
    <Particles
      :particle-count="isMobile ? 60 : 120"
      :particle-spread="8"
      :speed="0.06"
      :particle-colors="['#ffffff']"
      :move-particles-on-hover="false"
      :alpha-particles="true"
      :particle-base-size="isMobile ? 50 : 70"
      :size-randomness="1.5"
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
  background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%);
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
}

.brand-title {
  font-size: 48px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.8) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
}

@media (max-width: 768px) {
  .brand-section {
    display: none;
  }
}
</style>
