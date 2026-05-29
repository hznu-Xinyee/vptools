<template>
  <div ref="containerRef" class="particles-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Renderer, Camera, Geometry, Program, Mesh } from 'ogl'

const props = defineProps({
  particleCount: {
    type: Number,
    default: 200
  },
  particleSpread: {
    type: Number,
    default: 10
  },
  speed: {
    type: Number,
    default: 0.1
  },
  particleColors: {
    type: Array,
    default: () => ['#ffffff']
  },
  moveParticlesOnHover: {
    type: Boolean,
    default: false
  },
  particleHoverFactor: {
    type: Number,
    default: 1
  },
  alphaParticles: {
    type: Boolean,
    default: false
  },
  particleBaseSize: {
    type: Number,
    default: 100
  },
  sizeRandomness: {
    type: Number,
    default: 1
  },
  cameraDistance: {
    type: Number,
    default: 20
  },
  disableRotation: {
    type: Boolean,
    default: false
  },
  pixelRatio: {
    type: Number,
    default: 1
  }
})

const containerRef = ref(null)
const mouseRef = ref({ x: 0, y: 0 })

const defaultColors = ['#ffffff', '#ffffff', '#ffffff']

const hexToRgb = hex => {
  hex = hex.replace(/^#/, '')
  if (hex.length === 3) {
    hex = hex
      .split('')
      .map(c => c + c)
      .join('')
  }
  const int = parseInt(hex, 16)
  const r = ((int >> 16) & 255) / 255
  const g = ((int >> 8) & 255) / 255
  const b = (int & 255) / 255
  return [r, g, b]
}

const vertex = /* glsl */ `
  attribute vec3 position;
  attribute vec4 random;
  attribute vec3 color;

  uniform mat4 modelMatrix;
  uniform mat4 viewMatrix;
  uniform mat4 projectionMatrix;
  uniform float uTime;
  uniform float uSpread;
  uniform float uBaseSize;
  uniform float uSizeRandomness;

  varying vec4 vRandom;
  varying vec3 vColor;

  void main() {
    vRandom = random;
    vColor = color;

    vec3 pos = position * uSpread;
    pos.z *= 10.0;

    vec4 mPos = modelMatrix * vec4(pos, 1.0);
    float t = uTime;
    mPos.x += sin(t * random.z + 6.28 * random.w) * mix(0.1, 1.5, random.x);
    mPos.y += sin(t * random.y + 6.28 * random.x) * mix(0.1, 1.5, random.w);
    mPos.z += sin(t * random.w + 6.28 * random.y) * mix(0.1, 1.5, random.z);

    vec4 mvPos = viewMatrix * mPos;

    if (uSizeRandomness == 0.0) {
      gl_PointSize = uBaseSize;
    } else {
      gl_PointSize = (uBaseSize * (1.0 + uSizeRandomness * (random.x - 0.5))) / length(mvPos.xyz);
    }

    gl_Position = projectionMatrix * mvPos;
  }
`

const fragment = /* glsl */ `
  precision highp float;

  uniform float uTime;
  uniform float uAlphaParticles;
  varying vec4 vRandom;
  varying vec3 vColor;

  void main() {
    vec2 uv = gl_PointCoord.xy;
    float d = length(uv - vec2(0.5));

    if(uAlphaParticles < 0.5) {
      if(d > 0.5) {
        discard;
      }
      gl_FragColor = vec4(vColor + 0.2 * sin(uv.yxx + uTime + vRandom.y * 6.28), 1.0);
    } else {
      float circle = smoothstep(0.5, 0.4, d) * 0.8;
      gl_FragColor = vec4(vColor + 0.2 * sin(uv.yxx + uTime + vRandom.y * 6.28), circle);
    }
  }
`

let renderer = null
let gl = null
let camera = null
let geometry = null
let program = null
let mesh = null
let animationFrameId = null
let lastTime = performance.now()
let elapsed = 0

let activeResizeHandler = null
let activeMouseMoveHandler = null
let activeContainer = null
let activeMouseTarget = null
let activeGl = null

const initParticles = () => {
  cleanup()

  const container = containerRef.value
  if (!container) return

  renderer = new Renderer({
    dpr: props.pixelRatio,
    depth: false,
    alpha: true
  })
  gl = renderer.gl
  container.appendChild(gl.canvas)
  gl.clearColor(0, 0, 0, 0)

  camera = new Camera(gl, { fov: 15 })
  camera.position.set(0, 0, props.cameraDistance)

  let cachedRect = null
  const updateRect = () => {
    cachedRect = container.getBoundingClientRect()
  }

  const resize = () => {
    const width = container.clientWidth
    const height = container.clientHeight
    if (width && height && renderer && camera) {
      renderer.setSize(width, height)
      camera.perspective({ aspect: gl.canvas.width / gl.canvas.height })
    }
    updateRect()
  }
  window.addEventListener('resize', resize, false)
  resize()

  const handleMouseMove = e => {
    if (!cachedRect) updateRect()
    const x = ((e.clientX - cachedRect.left) / cachedRect.width) * 2 - 1
    const y = -(((e.clientY - cachedRect.top) / cachedRect.height) * 2 - 1)
    mouseRef.value = { x, y }
  }

  const mouseTarget = container.parentElement || container
  if (props.moveParticlesOnHover) {
    mouseTarget.addEventListener('mousemove', handleMouseMove)
  }

  const count = props.particleCount
  const positions = new Float32Array(count * 3)
  const randoms = new Float32Array(count * 4)
  const colors = new Float32Array(count * 3)
  const palette = props.particleColors && props.particleColors.length > 0 ? props.particleColors : defaultColors

  for (let i = 0; i < count; i++) {
    let x, y, z, len
    do {
      x = Math.random() * 2 - 1
      y = Math.random() * 2 - 1
      z = Math.random() * 2 - 1
      len = x * x + y * y + z * z
    } while (len > 1 || len === 0)
    const r = Math.cbrt(Math.random())
    positions.set([x * r, y * r, z * r], i * 3)
    randoms.set([Math.random(), Math.random(), Math.random(), Math.random()], i * 4)
    const col = hexToRgb(palette[Math.floor(Math.random() * palette.length)])
    colors.set(col, i * 3)
  }

  geometry = new Geometry(gl, {
    position: { size: 3, data: positions },
    random: { size: 4, data: randoms },
    color: { size: 3, data: colors }
  })

  program = new Program(gl, {
    vertex,
    fragment,
    uniforms: {
      uTime: { value: 0 },
      uSpread: { value: props.particleSpread },
      uBaseSize: { value: props.particleBaseSize * props.pixelRatio },
      uSizeRandomness: { value: props.sizeRandomness },
      uAlphaParticles: { value: props.alphaParticles ? 1 : 0 }
    },
    transparent: true,
    depthTest: false
  })

  mesh = new Mesh(gl, { mode: gl.POINTS, geometry, program })

  lastTime = performance.now()

  const update = t => {
    animationFrameId = requestAnimationFrame(update)

    // Performance guard: do not render or update if container is hidden (e.g., display: none on mobile)
    if (container.clientWidth === 0 || container.clientHeight === 0) {
      return
    }

    const delta = t - lastTime
    lastTime = t
    elapsed += delta * props.speed

    program.uniforms.uTime.value = elapsed * 0.001

    if (props.moveParticlesOnHover) {
      mesh.position.x = -mouseRef.value.x * props.particleHoverFactor
      mesh.position.y = -mouseRef.value.y * props.particleHoverFactor
    } else {
      mesh.position.x = 0
      mesh.position.y = 0
    }

    if (!props.disableRotation) {
      mesh.rotation.x = Math.sin(elapsed * 0.0002) * 0.1
      mesh.rotation.y = Math.cos(elapsed * 0.0005) * 0.15
      mesh.rotation.z += 0.01 * props.speed
    }

    renderer.render({ scene: mesh, camera })
  }

  animationFrameId = requestAnimationFrame(update)

  activeResizeHandler = resize
  activeMouseMoveHandler = handleMouseMove
  activeContainer = container
  activeMouseTarget = mouseTarget
  activeGl = gl
}

const cleanup = () => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  if (activeResizeHandler) {
    window.removeEventListener('resize', activeResizeHandler)
    activeResizeHandler = null
  }
  if (activeMouseTarget && activeMouseMoveHandler) {
    activeMouseTarget.removeEventListener('mousemove', activeMouseMoveHandler)
    activeMouseMoveHandler = null
  }
  activeMouseTarget = null
  if (activeContainer && activeGl && activeGl.canvas && activeContainer.contains(activeGl.canvas)) {
    activeContainer.removeChild(activeGl.canvas)
  }
  activeContainer = null
  activeGl = null
  renderer = null
  gl = null
  camera = null
  geometry = null
  program = null
  mesh = null
}

onMounted(() => {
  initParticles()
})

onUnmounted(() => {
  cleanup()
})

// Watchers for full re-initialization on structural props changes
watch(
  () => [props.particleCount, props.particleColors, props.cameraDistance, props.moveParticlesOnHover],
  () => {
    initParticles()
  },
  { deep: true }
)

// Watchers for dynamic uniform updates without recreating WebGL context
watch(
  () => props.particleSpread,
  (val) => {
    if (program) program.uniforms.uSpread.value = val
  }
)

watch(
  () => props.particleBaseSize,
  (val) => {
    if (program) program.uniforms.uBaseSize.value = val * props.pixelRatio
  }
)

watch(
  () => props.pixelRatio,
  (val) => {
    if (program) program.uniforms.uBaseSize.value = props.particleBaseSize * val
  }
)

watch(
  () => props.sizeRandomness,
  (val) => {
    if (program) program.uniforms.uSizeRandomness.value = val
  }
)

watch(
  () => props.alphaParticles,
  (val) => {
    if (program) program.uniforms.uAlphaParticles.value = val ? 1 : 0
  }
)
</script>

<style scoped>
.particles-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
