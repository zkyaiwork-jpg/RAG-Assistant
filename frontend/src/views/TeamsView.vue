<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">团队管理</h1>
        <p class="page-desc">小组挂在部门下，用于"小组可见"的文档和组长权限</p>
      </div>
      <button v-if="canManage" class="btn btn-primary" type="button" @click="openCreate">新建小组</button>
    </div>

    <div class="card">
      <loading-block v-if="loading" :rows="5" />
      <empty-state v-else-if="!teams.length" title="还没有小组" desc="先创建部门，再在这里建小组" />
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>小组名称</th>
              <th>所属部门</th>
              <th>说明</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in teams" :key="item.id">
              <td class="cell-strong">{{ item.name }}</td>
              <td>{{ item.department?.name || '-' }}</td>
              <td class="cell-sub">{{ item.description || '-' }}</td>
              <td class="cell-sub">{{ formatDateTime(item.created_time) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <base-modal v-model="createVisible" title="新建小组">
      <div class="field">
        <label class="field-label">小组名称</label>
        <input v-model.trim="form.name" class="input" placeholder="例如：人事一组" />
      </div>
      <div class="field">
        <label class="field-label">所属部门</label>
        <select v-model="form.departmentId" class="select">
          <option value="">请选择部门</option>
          <option v-for="department in departments" :key="department.id" :value="String(department.id)">{{ department.name }}</option>
        </select>
        <p v-if="!departments.length" class="field-hint">还没有部门，请先去"部门管理"创建</p>
      </div>
      <div class="field">
        <label class="field-label">说明（可选）</label>
        <input v-model.trim="form.description" class="input" />
      </div>
      <template #footer>
        <button class="btn" type="button" @click="createVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving || !form.name || !form.departmentId" @click="submit">创建</button>
      </template>
    </base-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { createTeam, fetchDepartments, fetchTeams } from '../api/admin'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { formatDateTime } from '../utils/format'
import BaseModal from '../components/BaseModal.vue'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const auth = useAuth()
const canManage = computed(() => auth.hasPermission('user_manage'))

const teams = ref([])
const departments = ref([])
const loading = ref(true)
const createVisible = ref(false)
const saving = ref(false)
const form = reactive({ name: '', departmentId: '', description: '' })

async function load() {
  loading.value = true
  try {
    const [teamList, departmentList] = await Promise.all([fetchTeams(), fetchDepartments()])
    teams.value = teamList
    departments.value = departmentList
  } catch (error) {
    toast.error(getErrorMessage(error, '加载小组失败'))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.name = ''
  form.departmentId = ''
  form.description = ''
  createVisible.value = true
}

async function submit() {
  saving.value = true
  try {
    await createTeam({
      name: form.name,
      department_id: Number(form.departmentId),
      description: form.description || null,
    })
    toast.success('小组已创建')
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
