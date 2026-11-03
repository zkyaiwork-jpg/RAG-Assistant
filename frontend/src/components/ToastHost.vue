<template>
  <div class="toast-host">
    <div
      v-for="item in toast.state.items"
      :key="item.id"
      :class="['toast', item.type === 'success' ? 'toast-success' : '', item.type === 'error' ? 'toast-error' : '']"
      @click="toast.remove(item.id)"
    >
      {{ item.message }}
    </div>
  </div>
</template>

<script setup>
import { toast } from '../stores/toast'
</script>
