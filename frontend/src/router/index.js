import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'
import { getToken } from '../utils/token'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('../views/DashboardView.vue'),
        meta: { title: '工作台', desc: '知识库概况与快捷入口' },
      },
      {
        path: 'documents',
        name: 'documents',
        component: () => import('../views/DocumentsView.vue'),
        meta: { title: '知识库文档', desc: '上传、归档与权限设置', permission: 'file_view' },
      },
      {
        path: 'chat',
        name: 'chat',
        component: () => import('../views/ChatView.vue'),
        meta: { title: 'AI 问答', desc: '基于企业知识库回答问题并给出来源', permission: 'file_view' },
      },
      {
        path: 'search',
        name: 'search',
        component: () => import('../views/SearchView.vue'),
        meta: { title: '智能检索', desc: '按意思找原文，不依赖关键词', permission: 'file_view' },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('../views/UsersView.vue'),
        meta: { title: '用户管理', desc: '账号、角色与组织归属', permission: 'user_manage' },
      },
      {
        path: 'departments',
        name: 'departments',
        component: () => import('../views/DepartmentsView.vue'),
        meta: { title: '部门管理', desc: '企业部门与说明', permission: 'user_manage' },
      },
      {
        path: 'teams',
        name: 'teams',
        component: () => import('../views/TeamsView.vue'),
        meta: { title: '团队管理', desc: '部门下的小组', permission: 'user_manage' },
      },
      {
        path: 'audit',
        name: 'audit',
        component: () => import('../views/AuditView.vue'),
        meta: { title: '审计日志', desc: '关键操作留痕，可追溯', permission: 'audit_view' },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../views/SettingsView.vue'),
        meta: { title: '模型设置', desc: '配置大模型服务与密钥', permission: 'model_manage' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：没登录跳登录页；有登录但缺权限就回工作台
router.beforeEach(async (to) => {
  const auth = useAuth()

  if (to.meta.public) {
    if (getToken() && to.name === 'login') {
      try {
        if (!auth.state.profile) await auth.loadProfile()
        return { name: 'dashboard' }
      } catch {
        auth.logout()
      }
    }
    return true
  }

  if (!getToken()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (!auth.state.profile) {
    try {
      await auth.loadProfile()
    } catch {
      auth.logout()
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }

  const permission = to.meta.permission
  if (permission && !auth.hasPermission(permission)) {
    return { name: 'dashboard' }
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 企业 AI 知识库助手` : '企业 AI 知识库助手'
})

export default router
