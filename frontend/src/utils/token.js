// 登录凭证的读写：只放在这里，其他文件统一调用
const TOKEN_KEY = 'enterprise_ai_kb_access_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}
