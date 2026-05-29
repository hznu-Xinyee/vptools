<template>
  <div class="form-field">
    <label v-if="label" :for="id" class="field-label">{{ label }}</label>
    <div class="input-wrapper">
      <input
        :id="id"
        :type="showPassword ? 'text' : type"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :maxlength="maxlength"
        class="field-input"
        :class="{ 'has-error': error, 'disabled': disabled }"
      />
      <button
        v-if="showToggle && type === 'password'"
        type="button"
        @click="showPassword = !showPassword"
        class="toggle-password"
        tabindex="-1"
      >
        <component :is="showPassword ? EyeOff : Eye" class="icon" />
      </button>
    </div>
    <div v-if="error" class="field-error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  showToggle: {
    type: Boolean,
    default: false
  },
  maxlength: {
    type: Number,
    default: undefined
  }
})

defineEmits(['update:modelValue'])

const showPassword = ref(false)
const id = computed(() => `field-${Math.random().toString(36).substr(2, 9)}`)
</script>

<style scoped>
.form-field {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
}

.field-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  transition: all 0.2s ease;
}

.field-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.field-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.3);
}

.field-input.has-error {
  border-color: rgba(239, 68, 68, 0.5);
}

.field-input.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.toggle-password:hover {
  color: rgba(255, 255, 255, 0.8);
}

.toggle-password .icon {
  width: 18px;
  height: 18px;
}

.field-error {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(239, 68, 68, 0.9);
}
</style>
