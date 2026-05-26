import { ref, onMounted, onUnmounted, computed } from 'vue'

export function useBreakpoint() {
  const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)

  const updateWidth = () => {
    windowWidth.value = window.innerWidth
  }

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', updateWidth)
    }
  })

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', updateWidth)
    }
  })

  // Tailwind breakpoints
  const isMobile = computed(() => windowWidth.value < 768)
  const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024)
  const isDesktop = computed(() => windowWidth.value >= 1024)
  const isLargeDesktop = computed(() => windowWidth.value >= 1280)

  // Specific breakpoints
  const breakpoint = computed(() => {
    if (windowWidth.value < 480) return 'xs'
    if (windowWidth.value < 640) return 'sm'
    if (windowWidth.value < 768) return 'md'
    if (windowWidth.value < 1024) return 'lg'
    if (windowWidth.value < 1280) return 'xl'
    return '2xl'
  })

  return {
    windowWidth,
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    breakpoint
  }
}
