<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">智能检索</h1>
        <p class="page-desc">按"意思"找原文：不用背关键词，描述你想找的内容即可</p>
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom: 16px;">
      <form @submit.prevent="runSearch">
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <input v-model.trim="query" class="input" style="flex: 1; min-width: 240px;" placeholder="例如：出差住宿标准" />
          <select v-model="folderId" class="select" style="width: 160px;">
            <option value="">全部文件夹</option>
            <option v-for="folder in folders" :key="folder.id" :value="String(folder.id)">{{ folder.name }}</option>
          </select>
          <select v-model="fileType" class="select" style="width: 130px;">
            <option value="">全部格式</option>
            <option value="docx">DOCX</option>
            <option value="pdf">PDF</option>
            <option value="txt">TXT</option>
          </select>
          <button class="btn btn-primary" type="submit" :disabled="searching || !query">
            <span v-if="searching" class="spinner" />
            {{ searching ? '检索中' : '检索' }}
          </button>
        </div>
      </form>
      <p class="field-hint" style="margin-top: 10px;">
        检索范围始终限定在“你有权限查看的文档”之内；如果没有结果，说明知识库确实没有相关内容。
      </p>
    </div>

    <loading-block v-if="searching" :rows="5" />
    <empty-state
      v-else-if="!searched"
      title="输入一个问题开始检索"
      desc="检索会返回最相关的几段原文，方便你核对"
    />
    <empty-state
      v-else-if="!results.length"
      title="没有检索到相关内容"
      desc="可以换个说法，或确认文档是否已上传（也可能你没有该文档的查看权限）"
    />
    <div v-else class="result-list">
      <div v-for="(item, index) in results" :key="index" class="result-card">
        <div class="result-head">
          <span class="result-file">{{ index + 1 }}. {{ item.filename || '未知文档' }}</span>
          <span style="display: flex; gap: 6px;">
            <span v-if="item.folder_name" class="badge">{{ item.folder_name }}</span>
            <span v-if="item.chunk_index !== null && item.chunk_index !== undefined" class="badge">第 {{ item.chunk_index + 1 }} 段</span>
            <span class="badge badge-primary">距离 {{ distanceLabel(item.distance) }}</span>
          </span>
        </div>
        <div class="result-body">{{ cleanContent(item.content) }}</div>
        <div class="result-foot">
          <span class="badge">{{ (item.file_type || '').toUpperCase() || '文档' }}</span>
          <span class="badge">{{ item.embedding_model || 'bge-small-zh' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { fetchFolders } from '../api/folders'
import { getErrorMessage } from '../api/http'
import { searchKnowledge } from '../api/search'
import { toast } from '../stores/toast'
import { distanceLabel } from '../utils/format'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const query = ref('')
const folderId = ref('')
const fileType = ref('')
const folders = ref([])
const results = ref([])
const searching = ref(false)
const searched = ref(false)

// 去掉制度文档里的内部标记（RULE 编号、章节编号），只展示正文
function cleanContent(text) {
  if (!text) return ''
  return String(text)
    .replace(/RULE\s*\d+[:：]?/gi, '')
    .replace(/^第[一二三四五六七八九十百零〇\d]+[条章节]\s*/gm, '')
    .trim()
}

async function runSearch() {
  if (!query.value) return
  searching.value = true
  searched.value = true
  try {
    results.value = await searchKnowledge({
      query: query.value,
      limit: 5,
      ...(folderId.value ? { folder_id: Number(folderId.value) } : {}),
      ...(fileType.value ? { file_type: fileType.value } : {}),
    })
  } catch (error) {
    toast.error(getErrorMessage(error, '检索失败'))
    results.value = []
  } finally {
    searching.value = false
  }
}

onMounted(async () => {
  try {
    folders.value = await fetchFolders()
  } catch {
    folders.value = []
  }
})
</script>
