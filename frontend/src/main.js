import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { configureHttp } from './api/http'
import { useAuth } from './stores/auth'
import './styles/main.css'

// 任何接口返回 401，都清掉登录状态并回到登录页
configureHttp({
  onUnauthorized: () => {
    useAuth().logout()
    const current = router.currentRoute.value
    if (current.name !== 'login') {
      router.replace({ name: 'login', query: { redirect: current.fullPath } })
    }
  },
})

createApp(App).use(router).mount('#app')
