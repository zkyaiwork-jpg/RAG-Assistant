import { http } from './http'

export async function fetchDocuments() {
  const { data } = await http.get('/documents')
  return data.documents || []
}

export async function uploadDocument(formData) {
  const { data } = await http.post('/upload', formData)
  return data
}

export async function deleteDocument(filename) {
  const { data } = await http.delete(`/documents/${encodeURIComponent(filename)}`)
  return data
}

export async function updateDocument(documentId, payload) {
  const { data } = await http.patch(`/documents/${documentId}`, payload)
  return data
}

// 上传时可选的小组：后端按当前用户的角色自动过滤，前端不用自己判断
export async function fetchUploadTeams() {
  const { data } = await http.get('/teams/available-for-upload')
  return data.items || []
}
