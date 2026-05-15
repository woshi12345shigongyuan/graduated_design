<template>
  <div ref="containerRef" class="message-list">
    <div v-if="!chatStore.hasMessages" class="empty-state">
      <div class="empty-mark">AI</div>
      <h4>开始一次高质量食谱检索</h4>
      <p>你可以直接提问菜谱、食材替换、步骤优化或烹饪时间。</p>
      <div class="example-questions">
        <button
          v-for="question in exampleQuestions"
          :key="question"
          class="example-btn neon-btn"
          @click="$emit('example', question)"
        >
          {{ question }}
        </button>
      </div>
    </div>

    <div v-else class="messages">
      <article
        v-for="message in chatStore.messages"
        :key="message.id"
        :class="['message', message.role, { error: message.isError }]"
      >
        <div class="avatar">{{ message.role === 'user' ? 'U' : 'AI' }}</div>

        <div class="bubble">
          <div class="bubble-meta">
            <span class="role">{{ message.role === 'user' ? '你' : '烹饪助手' }}</span>
            <span class="time">{{ formatTime(message.timestamp) }}</span>

            <button
              v-if="message.audioUrl && !message.isTyping"
              class="audio-btn"
              :class="{ playing: playingAudioUrl === message.audioUrl }"
              @click="playAudio(message.audioUrl)"
            >
              {{ playingAudioUrl === message.audioUrl ? '停止播报' : '语音播报' }}
            </button>
          </div>

          <div v-if="message.isTyping" class="typing-indicator" aria-label="模型正在生成中">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div v-else class="text-block">
            <p v-if="message.role === 'user'" class="plain-text">{{ message.content }}</p>
            <div v-else class="markdown-text" v-html="renderMarkdown(message.content)"></div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onUnmounted, ref } from 'vue'
import { marked } from 'marked'
import { useChatStore } from '../stores/chat'
import { audioPlayer } from '../services/speech'

const chatStore = useChatStore()
const containerRef = ref(null)
const playingAudioUrl = ref(null)

const exampleQuestions = [
  '帮我做一个 20 分钟内完成的晚餐',
  '推荐三道适合减脂期的家常菜',
  '红烧肉做得更软烂有哪些关键点？',
  '只有鸡蛋和番茄，可以做什么？'
]

defineEmits(['example'])

defineExpose({
  scrollToBottom() {
    nextTick(() => {
      if (containerRef.value) {
        containerRef.value.scrollTop = containerRef.value.scrollHeight
      }
    })
  }
})

function renderMarkdown(content) {
  if (!content) return ''

  try {
    const safeText = escapeHtml(String(content))
    return marked.parse(safeText, {
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false
    })
  } catch {
    return escapeHtml(String(content))
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  if (isToday) return `${hours}:${minutes}`

  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}/${day} ${hours}:${minutes}`
}

async function playAudio(url) {
  if (playingAudioUrl.value === url) {
    audioPlayer.stop()
    playingAudioUrl.value = null
    return
  }

  playingAudioUrl.value = url

  audioPlayer.onEnded = () => {
    playingAudioUrl.value = null
  }

  try {
    await audioPlayer.play(url)
  } catch (error) {
    console.error('播放语音失败:', error)
    playingAudioUrl.value = null
  }
}

onUnmounted(() => {
  audioPlayer.stop()
  playingAudioUrl.value = null
})
</script>

<style scoped>
.message-list {
  min-height: 0;
  overflow-y: auto;
  scroll-behavior: smooth;
  background: var(--chat-bg);
}

.empty-state {
  min-height: 100%;
  width: min(860px, 100%);
  margin: 0 auto;
  padding: clamp(42px, 9vh, 96px) 24px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.empty-mark {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #10a37f, #37b5ff);
  box-shadow: 0 12px 28px rgba(16, 163, 127, 0.2);
}

.empty-state h4 {
  margin: 22px 0 8px;
  color: var(--text-main);
  font-size: clamp(1.45rem, 3vw, 2.1rem);
  letter-spacing: -0.03em;
}

.empty-state p {
  margin: 0;
  max-width: 560px;
  color: var(--text-muted);
}

.example-questions {
  width: 100%;
  margin-top: 30px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.example-btn {
  min-height: 58px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  text-align: left;
  background: var(--bg-elevated);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.example-btn:hover {
  background: var(--item-hover);
}

.messages {
  padding: 18px 0 28px;
}

.message {
  border-bottom: 1px solid rgba(229, 229, 229, 0.72);
}

.message.assistant {
  background: #f7f7f8;
}

.message.error {
  background: #fff5f6;
}

.message {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 16px;
  padding: 24px max(24px, calc((100% - 820px) / 2));
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  color: #fff;
  background: #10a37f;
  font-size: 0.76rem;
  font-weight: 800;
}

.message.user .avatar {
  background: #6e6e80;
}

.bubble {
  min-width: 0;
}

.bubble-meta {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.role {
  color: var(--text-main);
  font-size: 0.9rem;
  font-weight: 700;
}

.time {
  color: var(--text-faint);
  font-size: 0.78rem;
}

.audio-btn {
  min-height: 28px;
  padding: 0 9px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  color: var(--text-muted);
  background: var(--bg-elevated);
  font-size: 0.76rem;
}

.audio-btn:hover,
.audio-btn.playing {
  color: #0f7a62;
  background: rgba(16, 163, 127, 0.08);
  border-color: rgba(16, 163, 127, 0.24);
}

.typing-indicator {
  display: inline-flex;
  gap: 5px;
  padding-top: 8px;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-faint);
  animation: typingPulse 1s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.14s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.28s;
}

@keyframes typingPulse {
  0%, 80%, 100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.text-block {
  color: var(--text-main);
  font-size: 0.98rem;
  line-height: 1.75;
}

.plain-text {
  margin: 0;
  white-space: pre-wrap;
}

.markdown-text :deep(p) {
  margin: 0 0 0.9em;
}

.markdown-text :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-text :deep(ul),
.markdown-text :deep(ol) {
  margin: 0.6em 0 0.9em;
  padding-left: 1.4em;
}

.markdown-text :deep(li) {
  margin: 0.25em 0;
}

.markdown-text :deep(code) {
  padding: 0.15em 0.35em;
  border-radius: 5px;
  background: rgba(0, 0, 0, 0.06);
}

.markdown-text :deep(pre) {
  overflow-x: auto;
  padding: 14px;
  border-radius: 12px;
  background: #202123;
  color: #f7f7f8;
}

@media (max-width: 720px) {
  .message {
    grid-template-columns: 30px minmax(0, 1fr);
    gap: 12px;
    padding: 20px 16px;
  }

  .example-questions {
    grid-template-columns: 1fr;
  }
}
</style>
