import { computed, reactive } from 'vue'
import { fetchProfile, loginRequest } from '../api/auth'
import { clearToken, getToken, setToken } from '../utils/token'

// 轻量状态管理：只用 Vue 自带的 reactive + computed，
// 因为全局状态只有"当前登录用户的资料和权限"这一份，没必要上 Pinia。
const state = reactive({
  profile: null,
  loading: false,
  loginError: '',
})

const isLoggedIn = computed(() => Boolean(state.profile))
const displayName = computed(() => state.profile?.real_name || state.profile?.username || '未登录')
const roleName = computed(() => state.profile?.role?.name || '')
const permissions = computed(() => state.profile?.permissions || [])

function hasPermission(code) {
  return permissions.value.includes(code)
}

async function loadProfile() {
  if (!getToken()) return null
  state.loading = true
  try {
    state.profile = await fetchProfile()
    return state.profile
  } finally {
    state.loading = false
  }
}

async function login(username, password) {
  state.loginError = ''
  const result = await loginRequest({ username, password })
  setToken(result.access_token)
  try {
    await loadProfile()
  } catch (error) {
    clearToken()
    throw error
  }
}

function logout() {
  clearToken()
  state.profile = null
  state.loginError = ''
}

export function useAuth() {
  return {
    state,
    isLoggedIn,
    displayName,
    roleName,
    permissions,
    hasPermission,
    loadProfile,
    login,
    logout,
  }
}
