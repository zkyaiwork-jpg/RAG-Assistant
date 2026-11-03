<template>
  <div class="app-shell">
    <app-sidebar :open="sidebarOpen" @navigate="sidebarOpen = false" />
    <div class="main-area">
      <app-topbar :title="title" :desc="desc" @toggle-menu="sidebarOpen = !sidebarOpen" />
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const route = useRoute()
const sidebarOpen = ref(false)

const title = computed(() => route.meta.title || '企业 AI 知识库助手')
const desc = computed(() => route.meta.desc || '')
</script>
