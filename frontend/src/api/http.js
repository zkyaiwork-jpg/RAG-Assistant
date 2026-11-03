import axios from 'axios'
import { clearToken, getToken } from '../utils/token'

// 后端地址：开发环境走 Vite 代理（/api -> 8000），生产环境走 nginx 转发。
// 想直连后端时，在 .env 里把 VITE_API_BASE_URL 写成 http://127.0.0.1:8000
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const http = axios.create({
  baseURL,
  timeout: 180000, // 问答要等大模型，给足 3 分钟
})

// 401 统一处理：由 main.js 注入跳转逻辑，避免这里直接依赖 router
let unauthorizedHandler = null

export function configureHttp(options = {}) {
  if (typeof options.onUnauthorized === 'function') {
    unauthorizedHandler = options.onUnauthorized
  }
}

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''
    if (status === 401 && !url.includes('/auth/login')) {
      clearToken()
      if (unauthorizedHandler) unauthorizedHandler()
    }
    return Promise.reject(error)
  },
)

// 把后端的 detail 提取成一句能给人看的中文
export function getErrorMessage(error, fallback = '请求失败，请稍后重试') {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error && error.message ? error.message : fallback
  }
  if (error.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试'
  }
  if (!error.response) {
    return '无法连接后端服务，请确认 FastAPI 已启动'
  }
  const detail = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg).filter(Boolean)
    if (messages.length) return messages.join('；')
  }
  if (error.response.status === 403) return '没有执行该操作的权限'
  if (error.response.status === 404) return '请求的数据不存在'
  if (error.response.status >= 500) return '服务端异常，请稍后重试'
  return fallback
}

export default http
