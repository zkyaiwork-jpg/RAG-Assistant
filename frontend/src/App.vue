<template>
  <div v-if="isDesktop" class="desktop-title-bar">
    <div class="desktop-title-bar-drag-region" />
  </div>
  <div :class="isDesktop ? 'desktop-content' : ''">
    <router-view />
  </div>
  <toast-host />
</template>

<script setup>
import { ref } from 'vue'
import ToastHost from './components/ToastHost.vue'

// Electron 桌面版通过 preload 注入 window.desktopApp。
// 存在时在顶部留出 40px 给系统绘制的窗口按钮，并让这条区域可以拖动窗口。
const isDesktop = ref(Boolean(window.desktopApp))
</script>
