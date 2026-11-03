<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">审计日志</h1>
        <p class="page-desc">登录、文档变更、权限调整、模型配置等关键操作都会留痕</p>
      </div>
      <button class="btn btn-sm" type="button" :disabled="loading" @click="load">刷新</button>
    </div>

    <div class="toolbar">
      <select v-model="filters.action" class="select" @change="reload(1)">
        <option value="">全部操作</option>
        <option v-for="option in actionOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
      <select v-model="filters.result" class="select" @change="reload(1)">
        <option value="">全部结果</option>
        <option value="success">成功</option>
        <option value="failed">失败</option>
      </select>
      <span class="toolbar-spacer" />
      <span class="cell-sub">共 {{ total }} 条记录</span>
    </div>

    <div class="card">
      <loading-block v-if="loading" :rows="6" />
      <empty-state v-else-if="!logs.length" title="没有审计记录" desc="调整筛选条件，或先做一些操作" />
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>时间</th>
              <th>操作</th>
              <th>对象</th>
              <th>结果</th>
              <th>操作人</th>
              <th>IP</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id">
              <td class="cell-sub" style="white-space: nowrap;">{{ formatDateTime(log.created_time) }}</td>
              <td class="cell-strong">{{ auditActionLabel(log.action) }}</td>
              <td>
                <span class="badge">{{ log.resource_type }}</span>
                <span style="margin-left: 6px;">{{ log.resource_name || '-' }}</span>
              </td>
              <td>
                <span :class="log.result === 'success' ? 'badge badge-ok' : 'badge badge-danger'">
                  {{ log.result === 'success' ? '成功' : '失败' }}
                </span>
              </td>
              <td>{{ log.actor_name || '-' }}</td>
              <td class="cell-sub">{{ log.ip_address || '-' }}</td>
              <td class="cell-sub" style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {{ log.detail || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pager">
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button class="btn btn-sm" type="button" :disabled="page <= 1" @click="reload(page - 1)">上一页</button>
        <button class="btn btn-sm" type="button" :disabled="page >= totalPages" @click="reload(page + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { fetchAuditLogs } from '../api/admin'
import { getErrorMessage } from '../api/http'
import { toast } from '../stores/toast'
import { auditActionLabel, formatDateTime } from '../utils/format'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const actionOptions = [
  { value: 'auth_login_success', label: '登录成功' },
  { value: 'auth_login_failed', label: '登录失败' },
  { value: 'document_upload', label: '上传文档' },
  { value: 'document_update', label: '修改文档' },
  { value: 'document_delete', label: '删除文档' },
  { value: 'user_create', label: '创建用户' },
  { value: 'user_update', label: '修改用户' },
  { value: 'user_status_change', label: '变更用户状态' },
  { value: 'user_password_reset', label: '重置密码' },
  { value: 'department_create', label: '创建部门' },
  { value: 'team_create', label: '创建团队' },
  { value: 'model_config_update', label: '更新模型配置' },
  { value: 'model_config_test', label: '测试模型连接' },
]

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const loading = ref(true)
const filters = reactive({ action: '', result: '' })

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function load() {
  loading.value = true
  try {
    const data = await fetchAuditLogs({
      page: page.value,
      page_size: pageSize,
      ...(filters.action ? { action: filters.action } : {}),
      ...(filters.result ? { result: filters.result } : {}),
    })
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    toast.error(getErrorMessage(error, '加载审计日志失败'))
  } finally {
    loading.value = false
  }
}

function reload(targetPage) {
  page.value = targetPage
  load()
}

onMounted(load)
</script>
