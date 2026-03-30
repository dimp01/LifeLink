<template>
  <div class="chat-page">
    <div class="chat-wrapper">
      <!-- Header -->
      <div class="chat-header">
        <div class="chat-avatar">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </div>
        <div class="chat-header-info">
          <h2>LifeLink AI Assistant</h2>
          <span class="status-dot"></span>
          <span class="status-text">Organ Donation Expert</span>
        </div>
        <div class="chat-badge">Domain-Locked AI</div>
      </div>

      <!-- Disclaimer -->
      <div class="disclaimer">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
        This chatbot answers <strong>organ donation queries only</strong>. It does not provide medical diagnoses or prescriptions.
      </div>

      <!-- Messages -->
      <div class="messages-area" ref="messagesEl">
        <!-- Welcome message -->
        <div class="message bot-message" v-if="messages.length === 0">
          <div class="msg-avatar bot-avatar">AI</div>
          <div class="msg-bubble">
            <p>Hello! I'm the LifeLink AI Assistant. I'm here to answer your questions about <strong>organ donation</strong> — registration, myths, procedures, religious perspectives, and more.</p>
            <p style="margin-top:8px; opacity:0.8; font-size:0.85em;">Ask me anything about organ donation!</p>
            <div class="quick-questions">
              <button v-for="q in quickQuestions" :key="q" @click="sendQuick(q)" class="quick-btn">{{ q }}</button>
            </div>
          </div>
        </div>

        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['message', msg.role === 'user' ? 'user-message' : 'bot-message']"
        >
          <div v-if="msg.role === 'bot'" class="msg-avatar bot-avatar">AI</div>
          <div class="msg-bubble">
            <div v-if="msg.role === 'bot'" class="prose" v-html="renderMd(msg.text)"></div>
            <p v-else style="white-space: pre-wrap; margin:0;">{{ msg.text }}</p>
            <div v-if="msg.classification" class="msg-meta">
              <span :class="['classif-badge', msg.classification === 'organ_related' ? 'badge-green' : 'badge-red']">
                {{ msg.classification === 'organ_related' ? '✓ Organ Related' : '✗ Off-Topic' }}
              </span>
              <span class="confidence-text">{{ (msg.confidence * 100).toFixed(0) }}% confidence</span>
            </div>
          </div>
          <div v-if="msg.role === 'user'" class="msg-avatar user-avatar">
            {{ userInitial }}
          </div>
        </div>

        <!-- Typing indicator -->
        <div class="message bot-message" v-if="loading">
          <div class="msg-avatar bot-avatar">AI</div>
          <div class="msg-bubble typing-bubble">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="chat-input-area">
        <textarea
          v-model="input"
          @keydown.enter.exact.prevent="send"
          placeholder="Ask about organ donation…"
          rows="1"
          :disabled="loading"
          class="chat-input"
          ref="inputEl"
          @input="autoResize"
        ></textarea>
        <button @click="send" :disabled="loading || !input.trim()" class="send-btn">
          <svg v-if="!loading" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
          <span v-else class="spinner"></span>
        </button>
      </div>
      <p class="input-hint">Press Enter to send · Shift+Enter for new line</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import { useAuthStore } from '../stores/auth.js'
import api from '../services/api.js'

marked.setOptions({ breaks: true, gfm: true })

function renderMd(text) {
  return marked.parse(text || '')
}

const auth = useAuthStore()
const messages = ref([])
const input = ref('')
const loading = ref(false)
const messagesEl = ref(null)
const inputEl = ref(null)

const userInitial = auth.user?.full_name?.[0]?.toUpperCase() || auth.user?.email?.[0]?.toUpperCase() || 'U'

const quickQuestions = [
  'What organs can I donate?',
  'Is organ donation allowed in Islam?',
  'How do I register as a donor?',
  'Does donation affect my funeral?',
]

async function sendQuick(q) {
  input.value = q
  await send()
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true

  // Reset textarea height
  if (inputEl.value) {
    inputEl.value.style.height = 'auto'
  }

  await scrollBottom()

  try {
    // Build history from previous organ-related turns only (skip rejections)
    const history = messages.value
      .filter(m => m.classification !== 'non_organ_related')
      .map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', text: m.text }))

    const payload = { query: text, history }
    if (auth.user?.user_id) payload.user_id = auth.user.user_id
    console.log(payload)

    const { data } = await api.post('/chat', payload)

    messages.value.push({
      role: 'bot',
      text: data.response,
      classification: data.classification,
      confidence: data.confidence,
    })
  } catch (err) {
    messages.value.push({
      role: 'bot',
      text: '⚠️ Sorry, I encountered an error. Please try again.',
      classification: null,
      confidence: null,
    })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 140) + 'px'
}
</script>

<style scoped>
.chat-page {
  min-height: calc(100vh - 70px);
  background: linear-gradient(135deg, #0a0a0f 0%, #111827 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.chat-wrapper {
  width: 100%;
  max-width: 760px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  height: 80vh;
  min-height: 500px;
  backdrop-filter: blur(12px);
  overflow: hidden;
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 24px;
  background: rgba(255,255,255,0.04);
  border-bottom: 1px solid rgba(255,255,255,0.07);
}

.chat-avatar {
  width: 44px; height: 44px;
  background: linear-gradient(135deg, #e53e3e, #fc8181);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: white; flex-shrink: 0;
}

.chat-header-info { flex: 1; }
.chat-header-info h2 { color: #f1f5f9; font-size: 1rem; font-weight: 700; margin: 0; }

.status-dot {
  display: inline-block; width: 8px; height: 8px;
  background: #22c55e; border-radius: 50; margin-right: 5px; vertical-align: middle;
}
.status-text { color: #94a3b8; font-size: 0.78rem; }

.chat-badge {
  background: rgba(99,102,241,0.15);
  border: 1px solid rgba(99,102,241,0.3);
  color: #a5b4fc;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* Disclaimer */
.disclaimer {
  background: rgba(234,179,8,0.08);
  border-bottom: 1px solid rgba(234,179,8,0.15);
  color: #fbbf24;
  font-size: 0.8rem;
  padding: 8px 20px;
  display: flex; align-items: center; gap: 7px;
}

/* Messages */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

.messages-area::-webkit-scrollbar { width: 4px; }
.messages-area::-webkit-scrollbar-track { background: transparent; }
.messages-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

.message {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.user-message { flex-direction: row-reverse; }

.msg-avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
}

.bot-avatar {
  background: linear-gradient(135deg, #e53e3e, #fc8181);
  color: white;
}

.user-avatar {
  background: linear-gradient(135deg, #6366f1, #818cf8);
  color: white;
}

.msg-bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 0.9rem;
  line-height: 1.6;
}

.bot-message .msg-bubble {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  color: #e2e8f0;
  border-bottom-left-radius: 4px;
}

.user-message .msg-bubble {
  background: linear-gradient(135deg, #6366f1, #818cf8);
  color: white;
  border-bottom-right-radius: 4px;
}

/* Typing indicator */
.typing-bubble {
  display: flex; align-items: center; gap: 5px;
  padding: 14px 18px;
}

.dot {
  width: 7px; height: 7px;
  background: #94a3b8;
  border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

/* Message meta */
.msg-meta {
  margin-top: 8px;
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}

.classif-badge {
  font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 10px;
}
.badge-green { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.badge-red   { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }

.confidence-text { font-size: 0.7rem; color: #64748b; }

/* Quick questions */
.quick-questions {
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px;
}
.quick-btn {
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.3);
  color: #a5b4fc;
  font-size: 0.75rem; padding: 5px 11px; border-radius: 20px; cursor: pointer;
  transition: all 0.2s;
}
.quick-btn:hover {
  background: rgba(99,102,241,0.25); color: #c7d2fe;
}

/* Input */
.chat-input-area {
  display: flex; align-items: flex-end; gap: 10px;
  padding: 14px 20px;
  background: rgba(255,255,255,0.03);
  border-top: 1px solid rgba(255,255,255,0.07);
}

.chat-input {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  color: #f1f5f9;
  font-size: 0.9rem;
  padding: 10px 14px;
  resize: none;
  outline: none;
  line-height: 1.5;
  max-height: 140px;
  overflow-y: auto;
  transition: border-color 0.2s;
  font-family: inherit;
}
.chat-input::placeholder { color: #475569; }
.chat-input:focus { border-color: rgba(99,102,241,0.5); }

.send-btn {
  width: 44px; height: 44px; flex-shrink: 0;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  border: none; border-radius: 12px; cursor: pointer; color: white;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.send-btn:hover:not(:disabled) { transform: scale(1.05); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.input-hint {
  text-align: center; font-size: 0.72rem; color: #334155;
  padding: 4px 0 10px; margin: 0;
}

/* Markdown prose styles for bot messages */
.prose :deep(p) {
  margin: 0 0 8px 0;
  line-height: 1.65;
}
.prose :deep(p:last-child) { margin-bottom: 0; }

.prose :deep(strong) {
  color: #f1f5f9;
  font-weight: 700;
}

.prose :deep(ol),
.prose :deep(ul) {
  margin: 6px 0 10px 0;
  padding-left: 1.4em;
}
.prose :deep(ol) { list-style: decimal; }
.prose :deep(ul) { list-style: disc; }

.prose :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}
.prose :deep(li strong) { color: #93c5fd; }

.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  color: #f1f5f9;
  font-weight: 700;
  margin: 12px 0 6px 0;
  line-height: 1.3;
}
.prose :deep(h1) { font-size: 1.1em; }
.prose :deep(h2) { font-size: 1.0em; }
.prose :deep(h3) { font-size: 0.95em; }

.prose :deep(blockquote) {
  border-left: 3px solid rgba(99,102,241,0.5);
  padding-left: 10px;
  margin: 8px 0;
  color: #94a3b8;
  font-style: italic;
}

.prose :deep(code) {
  background: rgba(255,255,255,0.08);
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 0.85em;
  color: #a5b4fc;
  font-family: monospace;
}

.prose :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.08);
  margin: 10px 0;
}

.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .chat-wrapper { height: 90vh; border-radius: 12px; }
  .msg-bubble { max-width: 88%; }
  .chat-badge { display: none; }
}
</style>
