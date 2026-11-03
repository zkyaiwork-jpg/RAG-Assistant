import { http } from './http'

export async function fetchFolders() {
  const { data } = await http.get('/folders')
  return Array.isArray(data) ? data : []
}

export async function createFolder(name) {
  const { data } = await http.post('/folders', { name })
  return data
}
