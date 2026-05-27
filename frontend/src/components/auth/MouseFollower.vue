<template>
  <div class="mouse-follower">
    <div class="mouse-smoke" ref="mouseSmokeRef"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const mouseSmokeRef = ref(null)
let mouseThrottle = false

const handleMouseMove = (event) => {
  if (mouseSmokeRef.value && !mouseThrottle) {
    mouseThrottle = true

    requestAnimationFrame(() => {
      const x = event.clientX
      const y = event.clientY

      if (mouseSmokeRef.value) {
        mouseSmokeRef.value.style.left = `${x}px`
        mouseSmokeRef.value.style.top = `${y}px`
      }

      if (Math.random() > 0.7) {
        createSmokeParticle(x, y)
      }

      mouseThrottle = false
    })
  }
}

const createSmokeParticle = (x, y) => {
  const particle = document.createElement('div')
  particle.className = 'smoke-particle'
  particle.style.left = `${x}px`
  particle.style.top = `${y}px`

  document.body.appendChild(particle)

  setTimeout(() => {
    if (particle.parentNode) {
      particle.parentNode.removeChild(particle)
    }
  }, 2000)
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
.mouse-smoke {
  position: fixed;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 40%, transparent 70%);
  filter: blur(15px);
  pointer-events: none;
  z-index: 1;
  transform: translate(-50%, -50%);
  transition: opacity 0.3s ease;
}

:global(.smoke-particle) {
  position: fixed;
  width: 3px;
  height: 3px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  pointer-events: none;
  z-index: 1;
  animation: smokeFloat 2s ease-out forwards;
}

@keyframes smokeFloat {
  0% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) translateY(-50px) scale(2);
    filter: blur(10px);
  }
}
</style>
