<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">知识库文档</h1>
        <p class="page-desc">上传制度文件后系统会自动解析、切片并建立语义索引</p>
      </div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button v-if="canUpload" class="btn" type="button" @click="folderModalVisible = true">新建文件夹</button>
        <button v-if="canUpload" class="btn btn-primary" type="button" @click="openUploadModal">上传文档</button>
      </div>
    </div>

    <div class="toolbar">
      <input v-model.trim="keyword" class="input" placeholder="按文件名筛选" />
      <select v-model="folderFilter" class="select">
        <option value="">全部文件夹</option>
        <option v-for="folder in folders" :key="folder.id" :value="String(folder.id)">{{ folder.name }}</option>
        <option value="none">未分配</option>
      </select>
      <select v-model="visibilityFilter" class="select">
        <option value="">全部可见范围</option>
        <option v-for="level in visibilityLevels" :key="level.value" :value="level.value">{{ level.label }}</option>
      </select>
      <span class="toolbar-spacer" />
      <button class="btn btn-sm" type="button" :disabled="loading" @click="loadDocuments">刷新</button>
    </div>

    <div class="card">
      <loading-block v-if="loading" :rows="6" />
      <empty-state
        v-else-if="!filteredDocuments.length"
        :title="documents.length ? '没有符合条件的文档' : '知识库还是空的'"
        :desc="documents.length ? '换个筛选条件试试' : '上传一份 DOCX / PDF / TXT 开始建库'"
      />
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>文件名</th>
              <th>类型</th>
              <th>大小</th>
              <th>分块</th>
              <th>可见范围</th>
              <th>文件夹</th>
              <th>上传时间</th>
              <th style="text-align: right;">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in filteredDocuments" :key="doc.document_id || doc.filename">
              <td>
                <div class="cell-strong">{{ doc.filename }}</div>
                <div v-if="doc.original_name && doc.original_name !== doc.filename" class="cell-sub">{{ doc.original_name }}</div>
              </td>
              <td><span class="badge">{{ (doc.file_type || '').toUpperCase() || '-' }}</span></td>
              <td class="cell-sub">{{ formatBytes(doc.file_size ?? doc.size) }}</td>
              <td>{{ doc.chunk_count ?? '-' }}</td>
              <td><span :class="visibilityClass(doc.visibility)">{{ visibilityLabel(doc.visibility) }}</span></td>
              <td>{{ doc.folder_name || '未分配' }}</td>
              <td class="cell-sub">{{ formatDateTime(doc.uploaded_at) }}</td>
              <td>
                <div class="table-actions">
                  <button v-if="canEdit" class="btn btn-sm" type="button" @click="openEditModal(doc)">编辑</button>
                  <button v-if="canDelete" class="btn btn-sm btn-danger" type="button" @click="askDelete(doc)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 上传弹窗 -->
    <base-modal v-model="uploadVisible" title="上传文档">
      <div class="field">
        <label class="field-label">选择文件（支持 DOCX / PDF / TXT）</label>
        <input ref="fileInputRef" class="input" type="file" accept=".docx,.pdf,.txt" @change="onFileChange" />
        <p class="field-hint">同名文件会被视为新版本：新版本索引成功后才会替换旧的</p>
      </div>

      <div class="form-row">
        <div class="field">
          <label class="field-label">所属文件夹</label>
          <select v-model="uploadForm.folderId" class="select">
            <option value="">不指定</option>
            <option v-for="folder in folders" :key="folder.id" :value="String(folder.id)">{{ folder.name }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">可见范围</label>
          <select v-model="uploadForm.visibility" class="select">
            <option v-for="level in allowedVisibilityLevels" :key="level.value" :value="level.value">{{ level.label }}</option>
          </select>
        </div>
      </div>

      <div v-if="uploadForm.visibility === 'team'" class="field">
        <label class="field-label">目标小组</label>
        <select v-model="uploadForm.teamId" class="select">
          <option value="">请选择小组</option>
          <option v-for="team in uploadTeams" :key="team.id" :value="String(team.id)">
            {{ team.department?.name ? team.department.name + ' / ' : '' }}{{ team.name }}
          </option>
        </select>
        <p v-if="!uploadTeams.length" class="field-hint">当前账号没有可选小组，请让管理员先分配</p>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="uploadVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="uploading || !selectedFile" @click="submitUpload">
          <span v-if="uploading" class="spinner" />
          {{ uploading ? '上传并解析中...' : '上传' }}
        </button>
      </template>
    </base-modal>

    <!-- 编辑弹窗 -->
    <base-modal v-model="editVisible" title="编辑文档信息">
      <div class="field">
        <label class="field-label">显示名称</label>
        <input v-model.trim="editForm.originalName" class="input" placeholder="给这份文档起个中文名" />
      </div>
      <div class="form-row">
        <div class="field">
          <label class="field-label">可见范围</label>
          <select v-model="editForm.visibility" class="select">
            <option v-for="level in allowedVisibilityLevels" :key="level.value" :value="level.value">{{ level.label }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">所属文件夹</label>
          <select v-model="editForm.folderId" class="select">
            <option value="">移回未分配</option>
            <option v-for="folder in folders" :key="folder.id" :value="String(folder.id)">{{ folder.name }}</option>
          </select>
        </div>
      </div>
      <div v-if="editForm.visibility === 'team'" class="field">
        <label class="field-label">目标小组</label>
        <select v-model="editForm.teamId" class="select">
          <option value="">请选择小组</option>
          <option v-for="team in uploadTeams" :key="team.id" :value="String(team.id)">
            {{ team.department?.name ? team.department.name + ' / ' : '' }}{{ team.name }}
          </option>
        </select>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="editVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="submitEdit">保存</button>
      </template>
    </base-modal>

    <!-- 新建文件夹 -->
    <base-modal v-model="folderModalVisible" title="新建文件夹">
      <div class="field">
        <label class="field-label">文件夹名称</label>
        <input v-model.trim="newFolderName" class="input" placeholder="例如：人事制度" @keyup.enter="submitFolder" />
      </div>
      <template #footer>
        <button class="btn" type="button" @click="folderModalVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="!newFolderName" @click="submitFolder">创建</button>
      </template>
    </base-modal>

    <!-- 删除确认 -->
    <base-modal v-model="deleteVisible" title="确认删除">
      <p>确定删除 <strong>{{ deleteTarget?.filename }}</strong> 吗？</p>
      <p class="field-hint" style="margin-top: 8px;">原文件和它的语义索引会一起删除，无法恢复。</p>
      <template #footer>
        <button class="btn" type="button" @click="deleteVisible = false">取消</button>
        <button class="btn btn-danger" type="button" :disabled="deleting" @click="confirmDelete">确认删除</button>
      </template>
    </base-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { deleteDocument, fetchDocuments, fetchUploadTeams, updateDocument, uploadDocument } from '../api/documents'
import { createFolder, fetchFolders } from '../api/folders'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { VISIBILITY_LEVELS, formatBytes, formatDateTime, visibilityClass, visibilityLabel } from '../utils/format'
import BaseModal from '../components/BaseModal.vue'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const auth = useAuth()
const visibilityLevels = VISIBILITY_LEVELS

const documents = ref([])
const folders = ref([])
const uploadTeams = ref([])
const loading = ref(true)
const keyword = ref('')
const folderFilter = ref('')
const visibilityFilter = ref('')

const uploadVisible = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const fileInputRef = ref(null)
const uploadForm = reactive({ folderId: '', visibility: 'private', teamId: '' })

const editVisible = ref(false)
const saving = ref(false)
const editForm = reactive({ documentId: null, originalName: '', visibility: 'private', folderId: '', teamId: '' })

const folderModalVisible = ref(false)
const newFolderName = ref('')

const deleteVisible = ref(false)
const deleting = ref(false)
const deleteTarget = ref(null)

const canUpload = computed(() => auth.hasPermission('file_upload'))
const canEdit = computed(() => auth.hasPermission('file_edit'))
const canDelete = computed(() => auth.hasPermission('file_delete'))

// 可见范围按发布权限过滤：没有 file_publish_company 就不能选"全公司"
const allowedVisibilityLevels = computed(() =>
  visibilityLevels.filter((level) => !level.permission || auth.hasPermission(level.permission)),
)

const filteredDocuments = computed(() => {
  const text = keyword.value.toLowerCase()
  return documents.value
    .filter((doc) => {
      if (text && !String(doc.filename || '').toLowerCase().includes(text)) return false
      if (folderFilter.value === 'none' && doc.folder_id) return false
      if (folderFilter.value && folderFilter.value !== 'none' && String(doc.folder_id) !== folderFilter.value) return false
      if (visibilityFilter.value && doc.visibility !== visibilityFilter.value) return false
      return true
    })
    .sort((a, b) => new Date(b.uploaded_at || 0) - new Date(a.uploaded_at || 0))
})

async function loadDocuments() {
  loading.value = true
  try {
    documents.value = await fetchDocuments()
  } catch (error) {
    toast.error(getErrorMessage(error, '加载文档列表失败'))
  } finally {
    loading.value = false
  }
}

async function loadFolders() {
  try {
    folders.value = await fetchFolders()
  } catch (error) {
    toast.error(getErrorMessage(error, '加载文件夹失败'))
  }
}

async function loadTeams() {
  if (!canUpload.value) return
  try {
    uploadTeams.value = await fetchUploadTeams()
  } catch {
    uploadTeams.value = []
  }
}

function openUploadModal() {
  resetUpload()
  uploadVisible.value = true
}

function resetUpload() {
  selectedFile.value = null
  uploadForm.folderId = ''
  uploadForm.visibility = 'private'
  uploadForm.teamId = ''
  uploading.value = false
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function submitUpload() {
  if (!selectedFile.value) {
    toast.error('请先选择文件')
    return
  }
  if (uploadForm.visibility === 'team' && !uploadForm.teamId) {
    toast.error('请选择目标小组')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  if (uploadForm.folderId) formData.append('folder_id', uploadForm.folderId)
  formData.append('visibility', uploadForm.visibility)
  if (uploadForm.visibility === 'team' && uploadForm.teamId) {
    formData.append('team_id', uploadForm.teamId)
  }

  uploading.value = true
  try {
    const result = await uploadDocument(formData)
    toast.success(`上传成功，共生成 ${result.vector_count ?? 0} 个文本块`)
    uploadVisible.value = false
    resetUpload()
    await loadDocuments()
    await loadFolders()
  } catch (error) {
    toast.error(getErrorMessage(error, '上传失败'))
  } finally {
    uploading.value = false
  }
}

function openEditModal(doc) {
  editForm.documentId = doc.document_id
  editForm.originalName = doc.original_name || doc.filename
  editForm.visibility = doc.visibility || 'private'
  editForm.folderId = doc.folder_id ? String(doc.folder_id) : ''
  editForm.teamId = doc.team_id ? String(doc.team_id) : ''
  editVisible.value = true
}

async function submitEdit() {
  if (editForm.visibility === 'team' && !editForm.teamId) {
    toast.error('请选择目标小组')
    return
  }
  const original = documents.value.find((doc) => doc.document_id === editForm.documentId) || {}
  saving.value = true
  try {
    // 只提交真正改动过的字段：没改可见范围就不碰它，
    // 避免"只改个名字"却因为发布权限不足被拒。
    const payload = {}
    if (editForm.originalName && editForm.originalName !== (original.original_name || original.filename)) {
      payload.original_name = editForm.originalName
    }
    if (editForm.visibility !== original.visibility) {
      payload.visibility = editForm.visibility
      if (editForm.visibility === 'team') payload.team_id = Number(editForm.teamId)
    }
    const originalFolder = original.folder_id ? String(original.folder_id) : ''
    if (editForm.folderId !== originalFolder) {
      payload.folder_id = editForm.folderId ? Number(editForm.folderId) : null
    }
    if (!Object.keys(payload).length) {
      toast.info('没有需要保存的改动')
      editVisible.value = false
      return
    }
    await updateDocument(editForm.documentId, payload)
    toast.success('已保存')
    editVisible.value = false
    await loadDocuments()
  } catch (error) {
    toast.error(getErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

function askDelete(doc) {
  deleteTarget.value = doc
  deleteVisible.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteDocument(deleteTarget.value.filename)
    toast.success('已删除')
    deleteVisible.value = false
    await loadDocuments()
  } catch (error) {
    toast.error(getErrorMessage(error, '删除失败'))
  } finally {
    deleting.value = false
  }
}

async function submitFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  try {
    await createFolder(name)
    toast.success('文件夹已创建')
    newFolderName.value = ''
    folderModalVisible.value = false
    await loadFolders()
  } catch (error) {
    toast.error(getErrorMessage(error, '创建文件夹失败'))
  }
}

onMounted(() => {
  loadDocuments()
  loadFolders()
  loadTeams()
})
</script>
