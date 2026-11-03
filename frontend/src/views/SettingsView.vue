<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">模型设置</h1>
        <p class="page-desc">回答用的生成模型在这里配置，密钥加密后存数据库，页面上不会回显</p>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px; max-width: 720px;">
      <loading-block v-if="loading" :rows="5" />
      <form v-else @submit.prevent="save">
        <div class="form-row">
          <div class="field">
            <label class="field-label">服务商</label>
            <select v-model="form.provider" class="select">
              <option value="deepseek">DeepSeek</option>
              <option value="openai">OpenAI</option>
              <option value="qwen">通义千问</option>
            </select>
          </div>
          <div class="field">
            <label class="field-label">模型名</label>
            <input v-model.trim="form.modelName" class="input" placeholder="例如：deepseek-chat" />
          </div>
        </div>

        <div class="field">
          <label class="field-label">接口地址</label>
          <input v-model.trim="form.baseUrl" class="input" placeholder="例如：https://api.deepseek.com" />
        </div>

        <div class="field">
          <label class="field-label">API Key</label>
          <input
            v-model.trim="form.apiKey"
            class="input"
            type="password"
            :placeholder="config.api_key_configured ? '已配置，留空表示不修改' : '首次配置必须填写'"
          />
          <p class="field-hint">
            当前状态：
            <span :class="config.api_key_configured ? 'badge badge-ok' : 'badge badge-warn'">
              {{ config.api_key_configured ? '已配置' : '未配置' }}
            </span>
            <span v-if="config.updated_time" style="margin-left: 8px;">更新于 {{ formatDateTime(config.updated_time) }}</span>
          </p>
        </div>

        <div class="field">
          <label class="field-label" style="display: flex; align-items: center; gap: 8px;">
            <input v-model="form.isActive" type="checkbox" />
            启用为当前模型
          </label>
        </div>

        <div style="display: flex; gap: 10px; margin-top: 6px;">
          <button class="btn btn-primary" type="submit" :disabled="saving">
            <span v-if="saving" class="spinner" />
            保存配置
          </button>
          <button class="btn" type="button" :disabled="testing" @click="testConnection">
            <span v-if="testing" class="spinner spinner-dark" />
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
        </div>
        <p class="field-hint" style="margin-top: 10px;">
          测试连接会用当前生效的配置发一次极小的请求（只要求模型回 1 个 token），成功即表示可用。
        </p>
      </form>
    </div>

    <div class="card card-pad" style="max-width: 720px;">
      <h2 style="font-size: 14px; margin-bottom: 12px;">当前账号</h2>
      <table class="table">
        <tbody>
          <tr>
            <td style="width: 120px; color: var(--text-muted);">账号</td>
            <td>{{ profile?.username }}</td>
          </tr>
          <tr>
            <td style="color: var(--text-muted);">姓名</td>
            <td>{{ profile?.real_name }}</td>
          </tr>
          <tr>
            <td style="color: var(--text-muted);">角色</td>
            <td><span class="badge badge-primary">{{ roleLabel(profile?.role?.name) }}</span></td>
          </tr>
          <tr>
            <td style="color: var(--text-muted);">部门 / 小组</td>
            <td>{{ profile?.department?.name || '-' }} / {{ profile?.team?.name || '-' }}</td>
          </tr>
          <tr>
            <td style="color: var(--text-muted);">权限点</td>
            <td>
              <span v-for="code in profile?.permissions || []" :key="code" class="badge" style="margin: 0 6px 6px 0;">
                {{ code }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getErrorMessage } from '../api/http'
import { fetchModelConfig, saveModelConfig, testModelConnection } from '../api/modelConfig'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { formatDateTime, roleLabel } from '../utils/format'
import LoadingBlock from '../components/LoadingBlock.vue'

const auth = useAuth()
const profile = computed(() => auth.state.profile)

const config = ref({})
const loading = ref(true)
const saving = ref(false)
const testing = ref(false)

const form = reactive({
  provider: 'deepseek',
  modelName: 'deepseek-chat',
  baseUrl: 'https://api.deepseek.com',
  apiKey: '',
  isActive: true,
})

async function load() {
  loading.value = true
  try {
    const data = await fetchModelConfig()
    config.value = data || {}
    form.provider = data?.provider || 'deepseek'
    form.modelName = data?.model_name || 'deepseek-chat'
    form.baseUrl = data?.base_url || 'https://api.deepseek.com'
    form.isActive = data?.is_active ?? true
    form.apiKey = ''
  } catch (error) {
    toast.error(getErrorMessage(error, '加载模型配置失败'))
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!form.modelName || !form.baseUrl) {
    toast.error('模型名和接口地址不能为空')
    return
  }
  saving.value = true
  try {
    const payload = {
      provider: form.provider,
      model_name: form.modelName,
      base_url: form.baseUrl,
      is_active: form.isActive,
    }
    if (form.apiKey) payload.api_key = form.apiKey
    const data = await saveModelConfig(payload)
    config.value = data || {}
    form.apiKey = ''
    toast.success('配置已保存')
  } catch (error) {
    toast.error(getErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  try {
    await testModelConnection()
    toast.success('连接正常，模型可用')
  } catch (error) {
    toast.error(getErrorMessage(error, '连接测试失败'))
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>
