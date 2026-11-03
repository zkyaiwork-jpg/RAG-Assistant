// 各种展示用的小工具：时间、文件大小、可见性/角色/状态的中文名

export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function formatBytes(size) {
  if (size === null || size === undefined || Number.isNaN(Number(size))) return '-'
  const bytes = Number(size)
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export const VISIBILITY_LABELS = {
  private: '仅自己',
  team: '小组可见',
  department: '部门可见',
  company: '全公司可见',
}

export const VISIBILITY_LEVELS = [
  { value: 'private', label: '仅自己', permission: null },
  { value: 'team', label: '小组可见', permission: 'file_publish_team' },
  { value: 'department', label: '部门可见', permission: 'file_publish_department' },
  { value: 'company', label: '全公司可见', permission: 'file_publish_company' },
]

export const ROLE_LABELS = {
  admin: '系统管理员',
  manager: '部门经理',
  leader: '小组长',
  employee: '普通员工',
}

export function roleLabel(name) {
  if (!name) return '-'
  return ROLE_LABELS[name] || name
}

export function visibilityLabel(value) {
  if (!value) return '-'
  return VISIBILITY_LABELS[value] || value
}

export function visibilityClass(value) {
  if (value === 'company') return 'badge badge-ok'
  if (value === 'department') return 'badge badge-primary'
  if (value === 'team') return 'badge badge-warn'
  return 'badge'
}

export function statusLabel(status) {
  return status === 'active' ? '正常' : '已停用'
}

export function auditActionLabel(action) {
  const map = {
    auth_login_success: '登录成功',
    auth_login_failed: '登录失败',
    document_upload: '上传文档',
    document_update: '修改文档',
    document_delete: '删除文档',
    user_create: '创建用户',
    user_update: '修改用户',
    user_status_change: '变更用户状态',
    user_password_reset: '重置密码',
    department_create: '创建部门',
    team_create: '创建团队',
    model_config_update: '更新模型配置',
    model_config_test: '测试模型连接',
    system_bootstrap_admin: '系统初始化',
  }
  return map[action] || action
}

export function distanceLabel(distance) {
  if (distance === null || distance === undefined) return '-'
  return Number(distance).toFixed(3)
}
