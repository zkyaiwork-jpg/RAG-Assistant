import { http } from './http'

/* ---------- 角色 ---------- */
export async function fetchRoles() {
  const { data } = await http.get('/roles')
  return data.items || []
}

/* ---------- 用户 ---------- */
export async function fetchUsers(params) {
  const { data } = await http.get('/users', { params })
  return data
}

export async function createUser(payload) {
  const { data } = await http.post('/users', payload)
  return data
}

export async function updateUser(userId, payload) {
  const { data } = await http.patch(`/users/${userId}`, payload)
  return data
}

export async function resetUserPassword(userId, newPassword) {
  const { data } = await http.post(`/users/${userId}/reset-password`, { new_password: newPassword })
  return data
}

export async function deleteUser(userId) {
  await http.delete(`/users/${userId}`)
}

/* ---------- 部门 ---------- */
export async function fetchDepartments() {
  const { data } = await http.get('/departments')
  return data.items || []
}

export async function createDepartment(payload) {
  const { data } = await http.post('/departments', payload)
  return data
}

/* ---------- 团队 ---------- */
export async function fetchTeams() {
  const { data } = await http.get('/teams')
  return data.items || []
}

export async function createTeam(payload) {
  const { data } = await http.post('/teams', payload)
  return data
}

/* ---------- 审计日志 ---------- */
export async function fetchAuditLogs(params) {
  const { data } = await http.get('/audit-logs', { params })
  return data
}
