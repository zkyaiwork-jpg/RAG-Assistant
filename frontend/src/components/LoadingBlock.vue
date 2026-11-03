<template>
  <div class="card card-pad">
    <div v-for="index in rows" :key="index" class="skeleton" :style="{ marginBottom: '10px', width: `${100 - index * 6}%` }" />
  </div>
</template>

<script setup>
defineProps({ rows: { type: Number, default: 4 } })
</script>
