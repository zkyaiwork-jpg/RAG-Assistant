import { http } from './http'

// 提问。conversation_id 为空表示开一个新会话；
// 后端会返回真实会话 id，下一轮必须带回去，才能接着同一个会话聊。
export async function sendQuestion(question, conversationId) {
  const payload = { question }
  if (conversationId) payload.conversation_id = conversationId
  const { data } = await http.post('/chat', payload)
  return data
}

export async function fetchConversations() {
  const { data } = await http.get('/chat/conversations')
  return data.conversations || []
}

export async function fetchConversation(conversationId) {
  const { data } = await http.get(`/chat/conversations/${conversationId}`)
  return data
}
