import { http } from './http'

export async function loginRequest(payload) {
  const { data } = await http.post('/auth/login', payload)
  return data
}

export async function fetchProfile() {
  const { data } = await http.get('/auth/me')
  return data
}
