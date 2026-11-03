<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">工作台</h1>
        <p class="page-desc">{{ greeting }}，这里是知识库的当前状态</p>
      </div>
      <div style="display: flex; gap: 8px;">
        <router-link class="btn" :to="{ name: 'search' }">去检索</router-link>
        <router-link class="btn btn-primary" :to="{ name: 'chat' }">开始提问</router-link>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">知识库文档</div>
        <div class="stat-value">{{ stats.document_count ?? '-' }}</div>
        <div class="stat-hint">已入库的制度文件</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">文本分块</div>
        <div class="stat-value">{{ stats.chunk_count ?? '-' }}</div>
        <div class="stat-hint">约 100 字一张卡片</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">累计提问</div>
        <div class="stat-value">{{ stats.question_count ?? '-' }}</div>
        <div class="stat-hint">全部用户的问题总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">服务状态</div>
        <div class="stat-value" style="font-size: 20px;">
          <span :class="healthBadgeClass">{{ healthText }}</span>
        </div>
        <div class="stat-hint">向量库 · 数据库 · 模型配置</div>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <span>最近入库</span>
        <router-link v-if="canViewFiles" class="btn btn-sm" :to="{ name: 'documents' }">查看全部</router-link>
      </div>

      <loading-block v-if="loading" :rows="4" />
      <empty-state v-else-if="!recentDocuments.length" title="还没有文档" desc="上传第一份制度文件后，这里会显示最近入库记录" />
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>文件名</th>
              <th>文件夹</th>
              <th>可见范围</th>
              <th>分块</th>
              <th>上传时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in recentDocuments" :key="doc.document_id || doc.filename">
              <td class="cell-strong">{{ doc.filename }}</td>
              <td>{{ doc.folder_name || '未分配' }}</td>
              <td><span :class="visibilityClass(doc.visibility)">{{ visibilityLabel(doc.visibility) }}</span></td>
              <td>{{ doc.chunk_count ?? '-' }}</td>
              <td class="cell-sub">{{ formatDateTime(doc.uploaded_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchHealth, fetchStats } from '../api/stats'
import { fetchDocuments } from '../api/documents'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { formatDateTime, visibilityClass, visibilityLabel } from '../utils/format'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const auth = useAuth()
const stats = ref({})
const health = ref({})
const documents = ref([])
const loading = ref(true)

const canViewFiles = computed(() => auth.hasPermission('file_view'))

const greeting = computed(() => {
  const hour = new Date().getHours()
  const name = auth.state.profile?.real_name || auth.state.profile?.username || ''
  const prefix = hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
  return name ? `${prefix}，${name}` : prefix
})

const healthText = computed(() => {
  if (!health.value.status) return '未知'
  return health.value.status === 'healthy' ? '运行正常' : '部分异常'
})

const healthBadgeClass = computed(() => (health.value.status === 'healthy' ? 'badge badge-ok' : 'badge badge-warn'))

const recentDocuments = computed(() =>
  [...documents.value]
    .sort((a, b) => new Date(b.uploaded_at || 0) - new Date(a.uploaded_at || 0))
    .slice(0, 5),
)

onMounted(async () => {
  loading.value = true
  try {
    const [statsData, healthData] = await Promise.all([fetchStats(), fetchHealth()])
    stats.value = statsData
    health.value = healthData
  } catch (error) {
    toast.error(getErrorMessage(error, '加载概况失败'))
  }

  if (canViewFiles.value) {
    try {
      documents.value = await fetchDocuments()
    } catch (error) {
      toast.error(getErrorMessage(error, '加载文档列表失败'))
    }
  }
  loading.value = false
})
</script>
