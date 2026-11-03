<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">用户管理</h1>
        <p class="page-desc">账号由管理员创建，用户不能自行注册</p>
      </div>
      <button v-if="canManage" class="btn btn-primary" type="button" @click="openCreate">新建用户</button>
    </div>

    <div class="toolbar">
      <select v-model="filters.status" class="select" @change="reload(1)">
        <option value="">全部状态</option>
        <option value="active">正常</option>
        <option value="inactive">已停用</option>
      </select>
      <select v-model="filters.roleId" class="select" @change="reload(1)">
        <option value="">全部角色</option>
        <option v-for="role in roles" :key="role.id" :value="String(role.id)">{{ roleLabel(role.name) }}</option>
      </select>
      <select v-model="filters.departmentId" class="select" @change="reload(1)">
        <option value="">全部部门</option>
        <option v-for="department in departments" :key="department.id" :value="String(department.id)">{{ department.name }}</option>
      </select>
      <span class="toolbar-spacer" />
      <span class="cell-sub">共 {{ total }} 个账号</span>
    </div>

    <div class="card">
      <loading-block v-if="loading" :rows="6" />
      <empty-state v-else-if="!users.length" title="没有用户" desc="可以调整筛选条件，或新建一个账号" />
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>账号 / 姓名</th>
              <th>角色</th>
              <th>部门</th>
              <th>小组</th>
              <th>状态</th>
              <th>创建时间</th>
              <th style="text-align: right;">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>
                <div class="cell-strong">{{ user.username }}</div>
                <div class="cell-sub">{{ user.real_name }}</div>
              </td>
              <td><span class="badge badge-primary">{{ roleLabel(user.role?.name) }}</span></td>
              <td>{{ user.department?.name || '-' }}</td>
              <td>{{ user.team?.name || '-' }}</td>
              <td>
                <span :class="user.status === 'active' ? 'badge badge-ok' : 'badge badge-danger'">
                  {{ statusLabel(user.status) }}
                </span>
              </td>
              <td class="cell-sub">{{ formatDate(user.created_time) }}</td>
              <td>
                <div class="table-actions">
                  <button class="btn btn-sm" type="button" @click="openEdit(user)">编辑</button>
                  <button class="btn btn-sm" type="button" @click="openReset(user)">重置密码</button>
                  <button class="btn btn-sm btn-danger" type="button" @click="askDelete(user)">删除</button>
                </div>
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

    <!-- 新建 / 编辑 -->
    <base-modal v-model="formVisible" :title="editingId ? '编辑用户' : '新建用户'">
      <div class="form-row">
        <div class="field">
          <label class="field-label">账号</label>
          <input v-model.trim="form.username" class="input" :disabled="Boolean(editingId)" placeholder="登录用的账号" />
        </div>
        <div class="field">
          <label class="field-label">姓名</label>
          <input v-model.trim="form.realName" class="input" placeholder="真实姓名" />
        </div>
      </div>

      <div v-if="!editingId" class="field">
        <label class="field-label">初始密码</label>
        <input v-model="form.password" class="input" type="password" placeholder="至少 8 位" />
        <p class="field-hint">创建后请让本人登录后修改密码</p>
      </div>

      <div class="form-row">
        <div class="field">
          <label class="field-label">角色</label>
          <select v-model="form.roleId" class="select">
            <option value="">请选择角色</option>
            <option v-for="role in roles" :key="role.id" :value="String(role.id)">{{ roleLabel(role.name) }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">部门</label>
          <select v-model="form.departmentId" class="select">
            <option value="">不指定</option>
            <option v-for="department in departments" :key="department.id" :value="String(department.id)">{{ department.name }}</option>
          </select>
        </div>
      </div>

      <div class="form-row">
        <div class="field">
          <label class="field-label">小组</label>
          <select v-model="form.teamId" class="select">
            <option value="">不指定</option>
            <option v-for="team in teamOptions" :key="team.id" :value="String(team.id)">
              {{ team.department?.name ? team.department.name + ' / ' : '' }}{{ team.name }}
            </option>
          </select>
        </div>
        <div v-if="editingId" class="field">
          <label class="field-label">状态</label>
          <select v-model="form.status" class="select">
            <option value="active">正常</option>
            <option value="inactive">停用</option>
          </select>
          <p class="field-hint">停用后该账号的登录凭证会立即失效</p>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="formVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="submitForm">
          {{ editingId ? '保存' : '创建' }}
        </button>
      </template>
    </base-modal>

    <!-- 重置密码 -->
    <base-modal v-model="resetVisible" title="重置密码">
      <p style="margin-bottom: 14px;">为 <strong>{{ resetTarget?.username }}</strong> 设置新密码，重置后该用户所有旧登录凭证立即失效。</p>
      <div class="field">
        <label class="field-label">新密码</label>
        <input v-model="newPassword" class="input" type="password" placeholder="至少 8 位" />
      </div>
      <template #footer>
        <button class="btn" type="button" @click="resetVisible = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving || newPassword.length < 8" @click="submitReset">确认重置</button>
      </template>
    </base-modal>

    <!-- 删除确认 -->
    <base-modal v-model="deleteVisible" title="确认删除">
      <p>确定删除账号 <strong>{{ deleteTarget?.username }}</strong> 吗？</p>
      <p class="field-hint" style="margin-top: 8px;">如果只是想禁止登录，建议把状态改为"停用"。</p>
      <template #footer>
        <button class="btn" type="button" @click="deleteVisible = false">取消</button>
        <button class="btn btn-danger" type="button" :disabled="saving" @click="confirmDelete">确认删除</button>
      </template>
    </base-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  createUser,
  deleteUser,
  fetchDepartments,
  fetchRoles,
  fetchTeams,
  fetchUsers,
  resetUserPassword,
  updateUser,
} from '../api/admin'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { formatDate, roleLabel, statusLabel } from '../utils/format'
import BaseModal from '../components/BaseModal.vue'
import EmptyState from '../components/EmptyState.vue'
import LoadingBlock from '../components/LoadingBlock.vue'

const auth = useAuth()
const canManage = computed(() => auth.hasPermission('user_manage'))

const users = ref([])
const roles = ref([])
const departments = ref([])
const teams = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(true)
const saving = ref(false)

const filters = reactive({ status: '', roleId: '', departmentId: '' })

const formVisible = ref(false)
const editingId = ref(null)
const form = reactive({
  username: '',
  realName: '',
  password: '',
  roleId: '',
  departmentId: '',
  teamId: '',
  status: 'active',
})

const resetVisible = ref(false)
const resetTarget = ref(null)
const newPassword = ref('')

const deleteVisible = ref(false)
const deleteTarget = ref(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

// 选了部门之后，小组下拉只显示该部门下的小组
const teamOptions = computed(() => {
  if (!form.departmentId) return teams.value
  return teams.value.filter((team) => String(team.department_id) === String(form.departmentId))
})

async function loadUsers() {
  loading.value = true
  try {
    const data = await fetchUsers({
      page: page.value,
      page_size: pageSize,
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.roleId ? { role_id: Number(filters.roleId) } : {}),
      ...(filters.departmentId ? { department_id: Number(filters.departmentId) } : {}),
    })
    users.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    toast.error(getErrorMessage(error, '加载用户失败'))
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [roleList, departmentList, teamList] = await Promise.all([fetchRoles(), fetchDepartments(), fetchTeams()])
    roles.value = roleList
    departments.value = departmentList
    teams.value = teamList
  } catch (error) {
    toast.error(getErrorMessage(error, '加载角色/部门/小组失败'))
  }
}

function reload(targetPage = page.value) {
  page.value = targetPage
  loadUsers()
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    username: '',
    realName: '',
    password: '',
    roleId: roles.value.find((role) => role.name === 'employee')?.id
      ? String(roles.value.find((role) => role.name === 'employee').id)
      : '',
    departmentId: '',
    teamId: '',
    status: 'active',
  })
  formVisible.value = true
}

function openEdit(user) {
  editingId.value = user.id
  Object.assign(form, {
    username: user.username,
    realName: user.real_name || '',
    password: '',
    roleId: user.role?.id ? String(user.role.id) : '',
    departmentId: user.department?.id ? String(user.department.id) : '',
    teamId: user.team?.id ? String(user.team.id) : '',
    status: user.status || 'active',
  })
  formVisible.value = true
}

async function submitForm() {
  saving.value = true
  try {
    if (editingId.value) {
      await updateUser(editingId.value, {
        real_name: form.realName,
        ...(form.roleId ? { role_id: Number(form.roleId) } : {}),
        department_id: form.departmentId ? Number(form.departmentId) : null,
        team_id: form.teamId ? Number(form.teamId) : null,
        status: form.status,
      })
      toast.success('已保存')
    } else {
      if (!form.username || !form.password || !form.roleId) {
        toast.error('账号、密码、角色都要填')
        saving.value = false
        return
      }
      await createUser({
        username: form.username,
        password: form.password,
        real_name: form.realName || form.username,
        role_id: Number(form.roleId),
        department_id: form.departmentId ? Number(form.departmentId) : null,
        team_id: form.teamId ? Number(form.teamId) : null,
      })
      toast.success('用户已创建')
      page.value = 1
    }
    formVisible.value = false
    await loadUsers()
  } catch (error) {
    toast.error(getErrorMessage(error, '保存失败'))
  } finally {
    saving.value = false
  }
}

function openReset(user) {
  resetTarget.value = user
  newPassword.value = ''
  resetVisible.value = true
}

async function submitReset() {
  if (!resetTarget.value) return
  saving.value = true
  try {
    await resetUserPassword(resetTarget.value.id, newPassword.value)
    toast.success('密码已重置，该用户需要重新登录')
    resetVisible.value = false
  } catch (error) {
    toast.error(getErrorMessage(error, '重置失败'))
  } finally {
    saving.value = false
  }
}

function askDelete(user) {
  deleteTarget.value = user
  deleteVisible.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  saving.value = true
  try {
    await deleteUser(deleteTarget.value.id)
    toast.success('已删除')
    deleteVisible.value = false
    await loadUsers()
  } catch (error) {
    toast.error(getErrorMessage(error, '删除失败'))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  await loadUsers()
})
</script>
