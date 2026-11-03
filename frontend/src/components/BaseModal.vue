<template>
  <teleport to="body">
    <div v-if="modelValue" class="modal-mask" @click.self="close">
      <div :class="['modal', wide ? 'modal-wide' : '']" role="dialog" aria-modal="true">
        <div class="modal-head">
          <span>{{ title }}</span>
          <button class="modal-close" type="button" aria-label="关闭" @click="close">×</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="modal-foot">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  wide: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

function onKeydown(event) {
  if (event.key === 'Escape' && props.modelValue) close()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>
