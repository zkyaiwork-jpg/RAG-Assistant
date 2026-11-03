import { http } from './http'

export async function fetchModelConfig() {
  const { data } = await http.get('/model-config')
  return data
}

export async function saveModelConfig(payload) {
  const { data } = await http.put('/model-config', payload)
  return data
}

export async function testModelConnection() {
  const { data } = await http.post('/model-config/test')
  return data
}
