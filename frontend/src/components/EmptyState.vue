<template>
  <div class="empty">
    <div class="empty-title">{{ title }}</div>
    <div v-if="desc">{{ desc }}</div>
    <div v-if="$slots.default" style="margin-top: 14px;">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无数据' },
  desc: { type: String, default: '' },
})
</script>
