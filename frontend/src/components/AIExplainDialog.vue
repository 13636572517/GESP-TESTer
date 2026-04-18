<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="860px"
    top="3vh"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <!-- 题目摘要 -->
    <div class="q-summary" v-if="currentQuestion">
      <el-tag size="small" type="info">
        {{ currentQuestion.question_type === 3 ? '判断题' : '单选题' }}
      </el-tag>
      <el-tag v-if="isCorrect !== null" :type="isCorrect ? 'success' : 'danger'" size="small">
        {{ isCorrect ? '已答对' : '已答错' }}
      </el-tag>
      <span v-if="!isCorrect && userAnswer" class="q-answer-hint">
        你选了 <strong>{{ userAnswer }}</strong>，
        正确答案是 <strong>{{ currentQuestion.answer }}</strong>
      </span>
      <span v-else-if="!isCorrect" class="q-answer-hint">
        正确答案是 <strong>{{ currentQuestion.answer }}</strong>
      </span>
    </div>

    <!-- 对话区域 -->
    <div class="chat-body" ref="chatBodyEl">
      <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.role]">
        <div class="msg-avatar">
          <el-avatar v-if="msg.role === 'assistant'" :size="30" style="background:#1865F2;font-size:12px;flex-shrink:0">AI</el-avatar>
          <el-avatar v-else :size="30" style="background:#6B7280;font-size:12px;flex-shrink:0">我</el-avatar>
        </div>
        <div class="msg-bubble" v-html="renderMd(msg.content)"></div>
      </div>
      <!-- 等待中（三个点） -->
      <div v-if="aiStreaming && !streamingContent" class="chat-msg assistant">
        <el-avatar :size="30" style="background:#1865F2;font-size:12px;flex-shrink:0">AI</el-avatar>
        <div class="msg-bubble loading-dots"><span></span><span></span><span></span></div>
      </div>
      <!-- 流式输出中 -->
      <div v-if="aiStreaming && streamingContent" class="chat-msg assistant">
        <el-avatar :size="30" style="background:#1865F2;font-size:12px;flex-shrink:0">AI</el-avatar>
        <div class="msg-bubble streaming" v-html="renderMd(streamingContent)"></div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input-wrap">
      <el-input
        v-model="chatInput"
        type="textarea"
        :rows="2"
        placeholder="输入追问，回车发送（Shift+Enter 换行）"
        :disabled="aiStreaming"
        @keydown.enter.exact.prevent="sendUserMsg"
        resize="none"
      />
      <el-button
        type="primary"
        :loading="aiStreaming"
        :disabled="!chatInput.trim()"
        @click="sendUserMsg"
        style="height:56px;min-width:72px"
      >发送</el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

// ── 状态 ─────────────────────────────────────────────────
const visible          = ref(false)
const title            = ref('')
const currentQuestion  = ref(null)
const userAnswer       = ref('')
const isCorrect        = ref(null)

const chatMessages     = ref([])
const chatInput        = ref('')
const aiStreaming      = ref(false)
const streamingContent = ref('')
const chatBodyEl       = ref(null)

// ── 对外暴露 open 方法 ────────────────────────────────────
defineExpose({
  open(opts) {
    // opts: { question, userAnswer?, isCorrect?, title }
    currentQuestion.value  = opts.question
    userAnswer.value       = opts.userAnswer || ''
    isCorrect.value        = opts.isCorrect ?? null
    title.value            = opts.title || 'AI 讲解'
    chatMessages.value     = []
    chatInput.value        = ''
    streamingContent.value = ''
    visible.value          = true
    nextTick(() => callAI([]))
  }
})

// ── 发送追问 ──────────────────────────────────────────────
async function sendUserMsg() {
  const text = chatInput.value.trim()
  if (!text || aiStreaming.value) return
  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: text })
  scrollBottom()
  await callAI(chatMessages.value.slice())
}

// ── SSE 流式调用 ──────────────────────────────────────────
async function callAI(history) {
  if (aiStreaming.value) return
  aiStreaming.value      = true
  streamingContent.value = ''

  const q = currentQuestion.value
  try {
    const response = await fetch('/api/user/ai-explain/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`,
      },
      body: JSON.stringify({
        question_id: q.id,
        user_answer: userAnswer.value,
        is_correct:  isCorrect.value ?? false,
        messages:    history,
      }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader  = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer    = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') break
        try {
          const parsed = JSON.parse(raw)
          if (parsed.error) { streamingContent.value = `❌ ${parsed.error}`; break }
          if (parsed.content) { streamingContent.value += parsed.content; scrollBottom() }
        } catch { /* skip */ }
      }
    }

    if (streamingContent.value) {
      chatMessages.value.push({ role: 'assistant', content: streamingContent.value })
    }
  } catch (e) {
    const msg = e.message || ''
    if (msg.includes('请先在右上角') || msg.includes('401')) {
      ElMessage.warning({ message: '请先在右上角「我的 AI 设置」中配置您的 API Key', duration: 4000 })
    } else {
      chatMessages.value.push({ role: 'assistant', content: `❌ 请求失败：${msg}` })
    }
  } finally {
    streamingContent.value = ''
    aiStreaming.value      = false
    scrollBottom()
  }
}

function scrollBottom() {
  nextTick(() => {
    if (chatBodyEl.value) chatBodyEl.value.scrollTop = chatBodyEl.value.scrollHeight
  })
}

// ── Markdown 渲染 ─────────────────────────────────────────
function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
function renderMd(text) {
  if (!text) return ''
  let h = text.replace(/```(\w*)\n?([\s\S]*?)```/g,
    (_, __, code) => `<pre class="ai-pre"><code>${escHtml(code.trim())}</code></pre>`)
  h = h.replace(/`([^`\n]+)`/g, '<code class="ai-code">$1</code>')
  h = h.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
  h = h.replace(/^###\s+(.+)$/gm, '<p class="ai-h3">$1</p>')
  h = h.replace(/^##\s+(.+)$/gm,  '<p class="ai-h2">$1</p>')
  h = h.replace(/^\d+\.\s+(.+)$/gm, '<div class="ai-li">$1</div>')
  h = h.replace(/^[-*]\s+(.+)$/gm,  '<div class="ai-li">• $1</div>')
  h = h.replace(/(?<!<\/pre>)\n(?!<pre)/g, '<br>')
  return h
}
</script>

<style scoped>
/* 题目摘要 */
.q-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  background: #F7F8FA;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}
.q-answer-hint { color: #374151; }
.q-answer-hint strong { color: #1865F2; }

/* 对话区域 */
.chat-body {
  height: 520px;
  overflow-y: auto;
  padding: 4px 0 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.chat-msg.user { flex-direction: row-reverse; }

.msg-bubble {
  max-width: 86%;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.55;
  word-break: break-word;
}
.chat-msg.assistant .msg-bubble {
  background: #F0F4FF;
  border-bottom-left-radius: 4px;
}
.chat-msg.user .msg-bubble {
  background: #1865F2;
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* 流式光标 */
.msg-bubble.streaming::after {
  content: '▋';
  animation: blink 0.7s step-end infinite;
  color: #1865F2;
  margin-left: 2px;
}
@keyframes blink { 50% { opacity: 0; } }

/* 加载三点 */
.loading-dots { display: flex; gap: 5px; padding: 12px 16px; align-items: center; }
.loading-dots span {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #1865F2;
  animation: bounce 1.2s infinite ease-in-out;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40%            { transform: scale(1.1); opacity: 1; }
}

/* 输入区 */
.chat-input-wrap {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid #E5E7EB;
  padding-top: 12px;
}

/* Markdown */
:deep(.ai-pre) {
  background: #1e1e2e; color: #cdd6f4;
  border-radius: 5px; padding: 8px 12px;
  overflow-x: auto; font-size: 12px; margin: 4px 0;
}
:deep(.ai-code) {
  background: #E8EDFF; color: #1865F2;
  padding: 1px 4px; border-radius: 3px; font-size: 12px;
}
:deep(.ai-h2) { font-size: 13px; font-weight: 700; margin: 5px 0 1px; color: #21242C; }
:deep(.ai-h3) { font-size: 13px; font-weight: 600; margin: 4px 0 1px; color: #374151; }
:deep(.ai-li) { padding-left: 12px; margin: 1px 0; }
</style>
