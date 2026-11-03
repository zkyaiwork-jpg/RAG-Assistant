import { http } from './http'

export async function fetchStats() {
  const { data } = await http.get('/stats')
  return data
}

export async function fetchHealth() {
  const { data } = await http.get('/health')
  return data
}
