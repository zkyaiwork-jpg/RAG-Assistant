<template>
  <header class="topbar">
    <div style="display: flex; align-items: center; gap: 12px; min-width: 0;">
      <button class="btn btn-sm menu-btn" type="button" @click="$emit('toggle-menu')">菜单</button>
      <div style="min-width: 0;">
        <div class="topbar-title">{{ title }}</div>
        <div v-if="desc" class="topbar-sub">{{ desc }}</div>
      </div>
    </div>

    <div class="topbar-user">
      <div class="user-chip">
        <span class="avatar">{{ initial }}</span>
        <span class="user-meta">
          <span class="user-name">{{ displayName }}</span>
          <span class="user-role">{{ roleText }}</span>
        </span>
      </div>
      <button class="btn btn-sm" type="button" @click="handleLogout">退出登录</button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'
import { roleLabel } from '../utils/format'

defineProps({ title: String, desc: String })
defineEmits(['toggle-menu'])

const auth = useAuth()
const router = useRouter()

const displayName = computed(() => auth.state.profile?.real_name || auth.state.profile?.username || '未登录')
const roleText = computed(() => roleLabel(auth.roleName.value))
const initial = computed(() => (displayName.value || 'U').slice(0, 1).toUpperCase())

function handleLogout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<style scoped>
.menu-btn {
  display: none;
}

@media (max-width: 900px) {
  .menu-btn {
    display: inline-flex;
  }
}
</style>
