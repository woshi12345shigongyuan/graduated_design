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
  padding: 16px 18px;
  scroll-behavior: smooth;
}

.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px 10px;
}

.empty-mark {
  width: 72px;
  height: 72px;
  border-radius: 24px;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-size: 1.18rem;
  letter-spacing: 0.09em;
  color: #d6ebff;
  background: linear-gradient(140deg, rgba(120, 178, 244, 0.24), rgba(130, 113, 255, 0.2));
  border: 1px solid rgba(137, 175, 220, 0.4);
  box-shadow: 0 18px 30px rgba(18, 43, 74, 0.3);
}

.empty-state h4 {
  margin: 18px 0 8px;
  font-size: 1.18rem;
}

.empty-state p {
  margin: 0;
  color: var(--text-muted);
  max-width: 38ch;
  line-height: 1.65;
}

.example-questions {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.example-btn {
  border-radius: 999px;
  min-height: 34px;
  padding: 0 14px;
  border-color: rgba(138, 173, 212, 0.4);
  font-size: 0.82rem;
  color: #d6eaff;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: min(88%, 760px);
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  border: 1px solid rgba(141, 175, 214, 0.35);
  background: rgba(12, 22, 36, 0.78);
  color: #d7ebff;
  flex-shrink: 0;
}

.message.assistant .avatar {
  background: linear-gradient(140deg, rgba(109, 163, 230, 0.22), rgba(129, 113, 255, 0.22));
}

.message.user .avatar {
  background: linear-gradient(140deg, rgba(106, 210, 183, 0.2), rgba(105, 164, 231, 0.22));
}

.bubble {
  min-width: 0;
  width: fit-content;
  max-width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(133, 165, 201, 0.28);
  background: linear-gradient(160deg, rgba(13, 23, 39, 0.85), rgba(9, 16, 28, 0.7));
  padding: 10px 12px;
  box-shadow: 0 10px 24px rgba(2, 9, 20, 0.3);
}

.message.user .bubble {
  border-color: rgba(117, 201, 180, 0.32);
  background: linear-gradient(150deg, rgba(14, 29, 41, 0.9), rgba(9, 18, 28, 0.76));
}

.message.error .bubble {
  border-color: rgba(247, 133, 160, 0.48);
  background: linear-gradient(160deg, rgba(53, 20, 35, 0.65), rgba(28, 14, 24, 0.68));
}

.bubble-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  min-height: 20px;
}

.role {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-faint);
}

.time {
  margin-left: auto;
  color: var(--text-faint);
  font-size: 0.72rem;
}

.audio-btn {
  border: 1px solid rgba(127, 165, 209, 0.36);
  border-radius: 999px;
  background: rgba(12, 24, 39, 0.72);
  color: #c7e2ff;
  min-height: 24px;
  padding: 0 10px;
  font-size: 0.72rem;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.audio-btn:hover {
  border-color: rgba(131, 190, 248, 0.72);
  transform: translateY(-1px);
}

.audio-btn.playing {
  border-color: rgba(115, 214, 188, 0.85);
  color: #d7fff4;
}

.text-block {
  color: var(--text-main);
  line-height: 1.65;
  font-size: 0.93rem;
}

.plain-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-text :deep(*) {
  word-break: break-word;
}

.markdown-text :deep(p) {
  margin: 0 0 8px;
}

.markdown-text :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-text :deep(ul),
.markdown-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-text :deep(code) {
  border-radius: 6px;
  padding: 2px 5px;
  background: rgba(130, 167, 212, 0.18);
  color: #cce6ff;
  font-size: 0.86em;
}

.markdown-text :deep(pre) {
  margin: 8px 0;
  border-radius: 10px;
  border: 1px solid rgba(135, 167, 203, 0.28);
  padding: 10px;
  overflow-x: auto;
  background: rgba(8, 14, 24, 0.8);
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 0;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: rgba(149, 188, 228, 0.88);
  animation: typingPulse 1.15s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.14s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.28s;
}

@keyframes typingPulse {
  0%,
  100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  50% {
    transform: translateY(-3px);
    opacity: 1;
  }
}

@media (max-width: 760px) {
  .message-list {
    padding: 12px;
  }

  .message {
    max-width: 94%;
  }
}
</style>
