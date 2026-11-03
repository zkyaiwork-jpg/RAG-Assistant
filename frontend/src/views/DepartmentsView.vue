<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">部门管理</h1>
        <p class="page-desc">部门是文档可见性判断的基础，员工和文档都会归属到部门</p>
      </div>
      <button v-if="canManage" class="btn btn-primary" type="button" @click="openCreate">新建部门</button>
    </div>

    <div class="card">
      <loading-block v-if="loading" :rows="5" />
      <empty-state v-else-if="!departments.length" title="还没有部门" desc="先建部门，再建小组和用户" />
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>部门名称</th>
              <th>说明</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in departments" :key="item.id">
              <td class="cell-strong">{{ item.name }}</td>
              <td class="cell-sub">{{ item.description || '-' }}</td>
              <td class="cell-sub">{{ formatDateTime(item.created_time) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <base-modal v-model="createVisible" title="新建部门">
      <div class="field">
        <label class="field-label">部门名称</label>
        <input v-model.trim="form.name" class="input" placeholder="例如：人力资源部" />
      </div>
      <div class="field">
        <label class="field-label">说明（可选）</label>
        <input v-model.trim="form.description" class="input" placeholder="例如：负责招聘、考勤与员工关系" />
      </div>
      <template #footer>
        <button class="btn" type="button" @click="createVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving || !form.name" @click="submit">创建</button>
      </template>
    </base-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { createDepartment, fetchDepartments } from '../api/admin'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { formatDateTime } from '../utils/format'
import BaseModal from '../components/BaseModal.vue'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const auth = useAuth()
const canManage = computed(() => auth.hasPermission('user_manage'))

const departments = ref([])
const loading = ref(true)
const createVisible = ref(false)
const saving = ref(false)
const form = reactive({ name: '', description: '' })

async function load() {
  loading.value = true
  try {
    departments.value = await fetchDepartments()
  } catch (error) {
    toast.error(getErrorMessage(error, '加载部门失败'))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.name = ''
  form.description = ''
  createVisible.value = true
}

async function submit() {
  saving.value = true
  try {
    await createDepartment({ name: form.name, description: form.description || null })
    toast.success('部门已创建')
    createVisible.value = false
    await load()
  } catch (error) {
    toast.error(getErrorMessage(error, '创建失败'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
