import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    // 编辑器/代理写入源码时会先在同目录生成临时文件再改名。不忽略这些临时
    // 目录会让文件监听器抢到被占用的文件句柄，watcher 直接 EBUSY 崩溃。
    watch: {
      ignored: [
        '**/node_modules/**',
        '**/.git/**',
        '**/*.tmpdir/**',
      ],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
