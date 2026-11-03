import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发环境把 /api 开头的请求转发给 FastAPI（8000），并去掉 /api 前缀。
// 这样前端代码里永远只写 /api/xxx，开发和生产（nginx）行为一致。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
