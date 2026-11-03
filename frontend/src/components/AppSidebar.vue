<template>
  <aside :class="['sidebar', open ? 'open' : '']">
    <div class="sidebar-brand">
      <span class="sidebar-brand-mark">AI</span>
      <span class="sidebar-brand-text">企业知识库</span>
    </div>

    <nav class="sidebar-nav">
      <template v-for="group in visibleGroups" :key="group.title">
        <p class="sidebar-group-title">{{ group.title }}</p>
        <router-link
          v-for="item in group.items"
          :key="item.name"
          :to="{ name: item.name }"
          :class="['nav-item', isActive(item.name) ? 'active' : '']"
          @click="$emit('navigate')"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path :d="icons[item.icon]" />
          </svg>
          <span>{{ item.label }}</span>
        </router-link>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div>企业 AI 知识库助手</div>
      <div>Vue 3 + FastAPI · v1.0</div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '../stores/auth'

defineProps({ open: Boolean })
defineEmits(['navigate'])

const route = useRoute()
const auth = useAuth()

const icons = {
  grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  file: 'M6 3h8l4 4v14H6z M14 3v4h4',
  chat: 'M4 5h16v11H9l-5 4z',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14z M20 20l-4-4',
  users: 'M12 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8z M4 21c0-4 3.6-6 8-6s8 2 8 6',
  building: 'M5 21V5l7-2v18 M12 21h7V9l-7-2 M8 9h1 M8 13h1 M8 17h1 M16 12h1 M16 16h1',
  team: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M2 20c0-3 3-5 7-5s7 2 7 5 M17 11a3 3 0 1 0 0-5.9 M22 20c0-2.5-2-4.2-5-4.7',
  audit: 'M7 3h7l4 4v14H7z M10 12h6 M10 16h6 M10 8h3',
  sliders: 'M4 7h9 M17 7h3 M4 12h4 M12 12h8 M4 17h7 M15 17h5 M13 5v4 M8 10v4 M11 15v4',
}

const groups = [
  {
    title: '概览',
    items: [{ name: 'dashboard', label: '工作台', icon: 'grid' }],
  },
  {
    title: '知识',
    items: [
      { name: 'documents', label: '知识库文档', icon: 'file', permission: 'file_view' },
      { name: 'chat', label: 'AI 问答', icon: 'chat', permission: 'file_view' },
      { name: 'search', label: '智能检索', icon: 'search', permission: 'file_view' },
    ],
  },
  {
    title: '管理',
    items: [
      { name: 'users', label: '用户管理', icon: 'users', permission: 'user_manage' },
      { name: 'departments', label: '部门管理', icon: 'building', permission: 'user_manage' },
      { name: 'teams', label: '团队管理', icon: 'team', permission: 'user_manage' },
      { name: 'audit', label: '审计日志', icon: 'audit', permission: 'audit_view' },
      { name: 'settings', label: '模型设置', icon: 'sliders', permission: 'model_manage' },
    ],
  },
]

// 没权限的菜单直接不渲染
const visibleGroups = computed(() =>
  groups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => !item.permission || auth.hasPermission(item.permission)),
    }))
    .filter((group) => group.items.length > 0),
)

function isActive(name) {
  return route.name === name
}
</script>
