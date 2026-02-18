<template>
  <div ref="containerRef" class="message-list">
    <!-- 空状态 -->
    <div v-if="!chatStore.hasMessages" class="empty-state">
      <div class="empty-icon">💬</div>
      <p class="empty-title">开始对话吧！</p>
      <p class="empty-hint">问我任何关于食谱的问题，例如：</p>
      <div class="example-questions">
        <button @click="$emit('example', q)" v-for="q in exampleQuestions" :key="q" class="example-btn">
          {{ q }}
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div v-else class="messages">
      <div 
        v-for="message in chatStore.messages" 
        :key="message.id" 
        :class="['message', message.role, { 'error': message.isError }]"
      >
        <!-- 头像 -->
        <div class="avatar">
          <span v-if="message.role === 'user'">👤</span>
          <span v-else>🍳</span>
        </div>

        <!-- 消息内容 -->
        <div class="content">
          <!-- 正在输入动画 -->
          <div v-if="message.isTyping" class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <!-- 消息文本 -->
          <div v-else class="text" v-html="renderMarkdown(message.content)"></div>

          <!-- 音频播放按钮 -->
          <button 
            v-if="message.audioUrl && !message.isTyping" 
            @click="playAudio(message.audioUrl)"
            class="audio-btn"
            :class="{ 'playing': playingAudioUrl === message.audioUrl }"
          >
            {{ playingAudioUrl === message.audioUrl ? '⏸️' : '🔊' }}
          </button>

          <!-- 时间戳 -->
          <div class="timestamp">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { audioPlayer } from '../services/speech'
import { marked } from 'marked'

const chatStore = useChatStore()
const containerRef = ref(null)
const playingAudioUrl = ref(null)

const exampleQuestions = [
  '宫保鸡丁怎么做？',
  '推荐几道简单的素菜',
  '红烧肉需要什么食材？',
  '有什么快手早餐？'
]

// 定义事件
defineEmits(['example'])

// 暴露滚动方法给父组件
defineExpose({
  scrollToBottom() {
    nextTick(() => {
      if (containerRef.value) {
        containerRef.value.scrollTop = containerRef.value.scrollHeight
      }
    })
  }
})

// 渲染 Markdown
function renderMarkdown(content) {
  if (!content) return ''
  try {
    return marked(content, {
      breaks: true,
      gfm: true
    })
  } catch {
    return content
  }
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  
  if (isToday) {
    return `${hours}:${minutes}`
  } else {
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    return `${month}/${day} ${hours}:${minutes}`
  }
}

// 播放音频
async function playAudio(url) {
  if (playingAudioUrl.value === url) {
    // 正在播放，停止
    audioPlayer.stop()
    playingAudioUrl.value = null
  } else {
    // 播放新音频
    playingAudioUrl.value = url
    
    audioPlayer.onEnded = () => {
      playingAudioUrl.value = null
    }
    
    try {
      await audioPlayer.play(url)
    } catch (error) {
      console.error('播放失败:', error)
      playingAudioUrl.value = null
    }
  }
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.empty-hint {
  font-size: 0.95rem;
  margin-bottom: 16px;
}

.example-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  max-width: 400px;
}

.example-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.example-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 消息样式 */
.messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message.assistant {
  flex-direction: row;
  margin-right: auto;
}

.avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  background: #f0f0f0;
}

.message.user .avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message.assistant .avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.content {
  position: relative;
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 16px;
  min-width: 60px;
}

.message.user .content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .content {
  background: #f5f5f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message.error .content {
  background: #fee;
  border: 1px solid #fcc;
}

/* 文本样式 */
.text {
  line-height: 1.6;
  word-break: break-word;
}

.text :deep(p) {
  margin: 0 0 8px 0;
}

.text :deep(p:last-child) {
  margin-bottom: 0;
}

.text :deep(ul), .text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.text :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.message.user .text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

/* 打字动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 音频按钮 */
.audio-btn {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s, transform 0.2s;
}

.audio-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.audio-btn.playing {
  opacity: 1;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* 时间戳 */
.timestamp {
  font-size: 0.75rem;
  opacity: 0.5;
  margin-top: 6px;
  text-align: right;
}

.message.user .timestamp {
  text-align: left;
}
</style>
