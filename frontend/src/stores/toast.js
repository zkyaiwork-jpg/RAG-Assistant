import { reactive } from 'vue'

// 全局提示条：任何地方调用 toast.success(...) 即可，App.vue 里统一渲染
const state = reactive({ items: [] })
let seed = 0

function push(message, type = 'info', duration = 3200) {
  const id = ++seed
  state.items.push({ id, message, type })
  window.setTimeout(() => remove(id), duration)
}

function remove(id) {
  const index = state.items.findIndex((item) => item.id === id)
  if (index !== -1) state.items.splice(index, 1)
}

export const toast = {
  state,
  remove,
  info: (message) => push(message, 'info'),
  success: (message) => push(message, 'success'),
  error: (message) => push(message, 'error'),
}
