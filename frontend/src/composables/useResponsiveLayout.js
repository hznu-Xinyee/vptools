import { ref, computed } from 'vue'
import { useBreakpoint } from './useBreakpoint'

export function useResponsiveLayout() {
  const { isMobile, isTablet, isDesktop } = useBreakpoint()

  // Mobile menu state
  const isMobileMenuOpen = ref(false)
  const isConfigSidebarOpen = ref(false)
  const isHistorySidebarOpen = ref(false)

  // Layout configuration
  const layoutConfig = computed(() => ({
    showNavSidebar: isDesktop.value || isMobileMenuOpen.value,
    showConfigSidebar: isDesktop.value || isConfigSidebarOpen.value,
    showHistorySidebar: isDesktop.value || isHistorySidebarOpen.value,
    useStackedVideos: isMobile.value,
    videoContainerClass: isMobile.value ? 'w-full' : isTablet.value ? 'w-[45vw]' : 'w-[32vw] max-w-[460px]'
  }))

  const toggleMobileMenu = () => {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
    if (isMobileMenuOpen.value) {
      isConfigSidebarOpen.value = false
      isHistorySidebarOpen.value = false
    }
  }

  const toggleConfigSidebar = () => {
    isConfigSidebarOpen.value = !isConfigSidebarOpen.value
    if (isConfigSidebarOpen.value) {
      isMobileMenuOpen.value = false
      isHistorySidebarOpen.value = false
    }
  }

  const toggleHistorySidebar = () => {
    isHistorySidebarOpen.value = !isHistorySidebarOpen.value
    if (isHistorySidebarOpen.value) {
      isMobileMenuOpen.value = false
      isConfigSidebarOpen.value = false
    }
  }

  const closeAllSidebars = () => {
    isMobileMenuOpen.value = false
    isConfigSidebarOpen.value = false
    isHistorySidebarOpen.value = false
  }

  return {
    isMobile,
    isTablet,
    isDesktop,
    layoutConfig,
    isMobileMenuOpen,
    isConfigSidebarOpen,
    isHistorySidebarOpen,
    toggleMobileMenu,
    toggleConfigSidebar,
    toggleHistorySidebar,
    closeAllSidebars
  }
}
