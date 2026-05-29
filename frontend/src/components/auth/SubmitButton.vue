<template>
  <button
    type="submit"
    :disabled="disabled || loading"
    class="submit-button"
    :class="{ 'loading': loading, 'disabled': disabled }"
  >
    <span v-if="loading" class="spinner"></span>
    <span class="button-text">{{ loading ? loadingText : text }}</span>
  </button>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '提交'
  },
  loadingText: {
    type: String,
    default: '处理中...'
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.submit-button {
  width: 100%;
  padding: 12px 24px;
  background: #ffffff;
  color: #000000;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-button:hover:not(.disabled):not(.loading) {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
}

.submit-button:active:not(.disabled):not(.loading) {
  transform: translateY(0);
}

.submit-button.disabled,
.submit-button.loading {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.button-text {
  line-height: 1;
}
</style>
