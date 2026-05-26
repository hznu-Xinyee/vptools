import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLayoutStore = defineStore('layout', () => {
  // Mobile menu state
  const isMobileMenuOpen = ref(false)
  const isConfigSidebarOpen = ref(false)
  const isHistorySidebarOpen = ref(false)

  // Current feature
  const currentFeature = ref('auto-video-translate')

  // Sidebar collapse state (for tablet)
  const isNavCollapsed = ref(false)
  const isConfigCollapsed = ref(false)

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

  const setFeature = (feature) => {
    currentFeature.value = feature
    closeAllSidebars()
  }

  return {
    isMobileMenuOpen,
    isConfigSidebarOpen,
    isHistorySidebarOpen,
    currentFeature,
    isNavCollapsed,
    isConfigCollapsed,
    toggleMobileMenu,
    toggleConfigSidebar,
    toggleHistorySidebar,
    closeAllSidebars,
    setFeature
  }
})
