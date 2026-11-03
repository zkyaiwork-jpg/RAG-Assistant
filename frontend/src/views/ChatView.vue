<template>
  <div class="page">
    <div class="chat-layout">
      <!-- 左侧：会话列表 -->
      <aside class="chat-side">
        <div class="chat-side-head">
          <button class="btn btn-primary btn-block btn-sm" type="button" @click="startNewChat">＋ 新对话</button>
        </div>
        <div class="chat-side-list">
          <div v-if="conversationsLoading" style="padding: 10px;">
            <div class="skeleton" style="margin-bottom: 8px;" />
            <div class="skeleton" style="margin-bottom: 8px; width: 80%;" />
            <div class="skeleton" style="width: 65%;" />
          </div>
          <empty-state v-else-if="!conversations.length" title="还没有会话" desc="问第一个问题吧" />
          <template v-else>
            <div
              v-for="item in conversations"
              :key="item.id"
              :class="['chat-side-item', item.id === conversationId ? 'active' : '']"
              @click="openConversation(item.id)"
            >
              {{ item.title || '新对话' }}
              <span class="chat-side-time">{{ formatDateTime(item.updated_time) }}</span>
            </div>
          </template>
        </div>
      </aside>

      <!-- 右侧：对话区 -->
      <section class="chat-main">
        <div ref="scrollRef" class="chat-scroll">
          <div v-if="!messages.length" class="chat-welcome">
            <div class="chat-welcome-mark">AI</div>
            <h2 style="font-size: 17px; color: var(--text);">您好，我是企业知识库助手</h2>
            <p style="margin-top: 6px; font-size: 13px;">我只依据公司制度文档回答，并且会告诉您答案出自哪里</p>
            <div class="quick-questions">
              <button
                v-for="question in quickQuestions"
                :key="question"
                class="quick-chip"
                type="button"
                @click="send(question)"
              >
                {{ question }}
              </button>
            </div>
          </div>

          <template v-else>
            <div v-for="message in messages" :key="message.id" :class="['chat-row', message.role === 'user' ? 'user' : '']">
              <span :class="['chat-avatar', message.role === 'user' ? 'user-avatar' : '']">
                {{ message.role === 'user' ? userInitial : 'AI' }}
              </span>
              <div class="chat-bubble-wrap">
                <div :class="['chat-bubble', message.error ? 'error' : '']">
                  <div v-if="message.role === 'assistant' && !message.error" class="md" v-html="renderMarkdown(message.content)" />
                  <template v-else>{{ message.content }}</template>
                </div>

                <div v-if="message.sources && message.sources.length" class="chat-sources">
                  <div class="chat-sources-title">回答依据（{{ message.sources.length }} 条）</div>
                  <div v-for="(source, index) in message.sources" :key="index" class="source-item">
                    <div>
                      <span class="source-file">{{ source.filename || '未知文档' }}</span>
                      <span v-if="source.folder_name" class="badge" style="margin-left: 6px;">{{ source.folder_name }}</span>
                      <span v-if="source.chunk_index !== null && source.chunk_index !== undefined" class="badge" style="margin-left: 6px;">
                        第 {{ source.chunk_index + 1 }} 段
                      </span>
                      <span class="badge" style="margin-left: 6px;">距离 {{ distanceLabel(source.distance) }}</span>
                    </div>
                    <div v-if="source.content" class="source-snippet">{{ source.content }}</div>
                  </div>
                </div>

                <div v-if="message.error && message.question" style="margin-top: 8px;">
                  <button class="btn btn-sm" type="button" @click="send(message.question)">重试</button>
                </div>
              </div>
            </div>

            <div v-if="sending" class="chat-row">
              <span class="chat-avatar">AI</span>
              <div class="chat-bubble" style="color: var(--text-muted);">AI 正在检索资料并组织回答...</div>
            </div>
          </template>
        </div>

        <div class="chat-composer">
          <div class="chat-input-row">
            <textarea
              ref="inputRef"
              v-model="draft"
              class="chat-textarea"
              rows="1"
              placeholder="请输入问题，例如：事假怎么申请？（Enter 发送，Shift+Enter 换行）"
              :disabled="sending"
              @keydown.enter.exact.prevent="submitDraft"
            />
            <button class="btn btn-primary" type="button" :disabled="sending || !draft.trim()" @click="submitDraft">
              <span v-if="sending" class="spinner" />
              {{ sending ? '回答中' : '发送' }}
            </button>
          </div>
          <p class="chat-hint">AI 生成内容仅供参考，重要信息请核对引用的原文</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { fetchConversation, fetchConversations, sendQuestion } from '../api/chat'
import { getErrorMessage } from '../api/http'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'
import { distanceLabel, formatDateTime } from '../utils/format'
import { renderMarkdown } from '../utils/markdown'
import EmptyState from '../components/EmptyState.vue'

const auth = useAuth()

const quickQuestions = ['事假怎么申请？', '报销需要几天内提交？', '会议室要提前多久预约？', '出差住宿标准是多少？']

const conversations = ref([])
const conversationsLoading = ref(true)
const conversationId = ref(null)
const messages = ref([])
const draft = ref('')
const sending = ref(false)
const scrollRef = ref(null)
const inputRef = ref(null)
let seed = 0

const userInitial = computed(() => (auth.displayName.value || 'U').slice(0, 1).toUpperCase())

function nextId(prefix) {
  seed += 1
  return `${prefix}-${seed}`
}

async function scrollToBottom() {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

async function loadConversations() {
  conversationsLoading.value = true
  try {
    conversations.value = await fetchConversations()
  } catch (error) {
    toast.error(getErrorMessage(error, '加载会话列表失败'))
  } finally {
    conversationsLoading.value = false
  }
}

function startNewChat() {
  conversationId.value = null
  messages.value = []
  draft.value = ''
  inputRef.value?.focus()
}

async function openConversation(id) {
  if (sending.value) return
  try {
    const detail = await fetchConversation(id)
    conversationId.value = detail.id
    messages.value = (detail.messages || []).map((message) => ({
      id: nextId('history'),
      role: message.role,
      content: message.content,
      sources: message.sources || [],
    }))
    await scrollToBottom()
  } catch (error) {
    toast.error(getErrorMessage(error, '打开会话失败'))
  }
}

function submitDraft() {
  const question = draft.value.trim()
  if (!question || sending.value) return
  draft.value = ''
  send(question)
}

async function send(question) {
  if (sending.value) return
  const text = String(question || '').trim()
  if (!text) return

  messages.value.push({ id: nextId('user'), role: 'user', content: text })
  sending.value = true
  await scrollToBottom()

  try {
    const result = await sendQuestion(text, conversationId.value)
    // 关键：把后端返回的真实会话 id 记下来，下一轮才能接着同一个会话
    if (result.conversation_id) conversationId.value = result.conversation_id
    messages.value.push({
      id: nextId('assistant'),
      role: 'assistant',
      content: result.answer || '（服务没有返回内容）',
      sources: result.sources || [],
    })
    await loadConversations()
  } catch (error) {
    messages.value.push({
      id: nextId('error'),
      role: 'assistant',
      content: `回答失败：${getErrorMessage(error, '请稍后重试')}`,
      error: true,
      question: text,
    })
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

onMounted(() => {
  loadConversations()
  inputRef.value?.focus()
})
</script>
