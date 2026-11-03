<template>
  <div class="login-page">
    <form class="login-card" @submit.prevent="submit">
      <div class="login-brand">
        <span class="sidebar-brand-mark">AI</span>
        <div>
          <div class="login-title">欢迎使用企业 AI 知识库助手</div>
          <div class="login-sub">先告诉我们要怎么称呼你</div>
        </div>
      </div>

      <div class="field">
        <label class="field-label" for="userName">你的名字</label>
        <input id="userName" v-model.trim="userName" class="input" placeholder="例如：张伟" />
        <p class="field-hint">这个名字只保存在本机，用于桌面版的问候语显示</p>
      </div>

      <p v-if="errorMessage" class="field-error">{{ errorMessage }}</p>

      <button class="btn btn-primary btn-block" type="submit" :disabled="!userName || saving">
        {{ saving ? '保存中...' : '开始使用' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const desktop = window.desktopApp

const userName = ref('')
const saving = ref(false)
const errorMessage = ref('')

// 只有桌面版（Electron 注入 window.desktopApp）才有"本机用户名"，
// 浏览器里访问这个地址就直接回首页。
onMounted(async () => {
  if (!desktop) {
    router.replace({ name: 'dashboard' })
    return
  }
  try {
    const info = await desktop.getUserInfo()
    if (info?.userName) userName.value = info.userName
  } catch {
    // 读不到就让用户自己输
  }
})

async function submit() {
  if (!userName.value || !desktop) return
  saving.value = true
  errorMessage.value = ''
  try {
    await desktop.saveUserName(userName.value)
    router.replace({ name: 'dashboard' })
  } catch {
    errorMessage.value = '保存失败，请重试'
  } finally {
    saving.value = false
  }
}
</script>
