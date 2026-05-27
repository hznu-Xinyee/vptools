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

let cleanup = null

onMounted(() => {
  const container = containerRef.value
  if (!container) return

  const renderer = new Renderer({
    dpr: props.pixelRatio,
    depth: false,
    alpha: true
  })
  const gl = renderer.gl
  container.appendChild(gl.canvas)
  gl.clearColor(0, 0, 0, 0)

  const camera = new Camera(gl, { fov: 15 })
  camera.position.set(0, 0, props.cameraDistance)

  const resize = () => {
    const width = container.clientWidth
    const height = container.clientHeight
    renderer.setSize(width, height)
    camera.perspective({ aspect: gl.canvas.width / gl.canvas.height })
  }
  window.addEventListener('resize', resize, false)
  resize()

  const handleMouseMove = e => {
    const rect = container.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
    const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1)
    mouseRef.value = { x, y }
  }

  if (props.moveParticlesOnHover) {
    container.addEventListener('mousemove', handleMouseMove)
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

  const geometry = new Geometry(gl, {
    position: { size: 3, data: positions },
    random: { size: 4, data: randoms },
    color: { size: 3, data: colors }
  })

  const program = new Program(gl, {
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

  const particles = new Mesh(gl, { mode: gl.POINTS, geometry, program })

  let animationFrameId
  let lastTime = performance.now()
  let elapsed = 0

  const update = t => {
    animationFrameId = requestAnimationFrame(update)
    const delta = t - lastTime
    lastTime = t
    elapsed += delta * props.speed

    program.uniforms.uTime.value = elapsed * 0.001

    if (props.moveParticlesOnHover) {
      particles.position.x = -mouseRef.value.x * props.particleHoverFactor
      particles.position.y = -mouseRef.value.y * props.particleHoverFactor
    } else {
      particles.position.x = 0
      particles.position.y = 0
    }

    if (!props.disableRotation) {
      particles.rotation.x = Math.sin(elapsed * 0.0002) * 0.1
      particles.rotation.y = Math.cos(elapsed * 0.0005) * 0.15
      particles.rotation.z += 0.01 * props.speed
    }

    renderer.render({ scene: particles, camera })
  }

  animationFrameId = requestAnimationFrame(update)

  cleanup = () => {
    window.removeEventListener('resize', resize)
    if (props.moveParticlesOnHover) {
      container.removeEventListener('mousemove', handleMouseMove)
    }
    cancelAnimationFrame(animationFrameId)
    if (container.contains(gl.canvas)) {
      container.removeChild(gl.canvas)
    }
  }
})

onUnmounted(() => {
  if (cleanup) {
    cleanup()
  }
})
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
