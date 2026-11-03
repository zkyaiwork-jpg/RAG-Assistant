<template>
  <div class="login-page">
    <form class="login-card" @submit.prevent="submit">
      <div class="login-brand">
        <span class="sidebar-brand-mark">AI</span>
        <div>
          <div class="login-title">企业 AI 知识库助手</div>
          <div class="login-sub">用大白话问公司制度，答案带出处</div>
        </div>
      </div>

      <div class="field">
        <label class="field-label" for="username">用户名</label>
        <input
          id="username"
          v-model.trim="form.username"
          class="input"
          autocomplete="username"
          placeholder="请输入用户名"
        />
      </div>

      <div class="field">
        <label class="field-label" for="password">密码</label>
        <input
          id="password"
          v-model="form.password"
          class="input"
          type="password"
          autocomplete="current-password"
          placeholder="请输入密码"
        />
      </div>

      <p v-if="errorMessage" class="field-error">{{ errorMessage }}</p>

      <button class="btn btn-primary btn-block" type="submit" :disabled="loading">
        <span v-if="loading" class="spinner" />
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <p class="login-tip">本系统不开放注册，账号由管理员分配</p>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const router = useRouter()
const route = useRoute()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  if (!form.username || !form.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await auth.login(form.username, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>
