import { http } from './http'

export async function searchKnowledge(params) {
  const { data } = await http.get('/search', { params })
  return data.results || []
}
