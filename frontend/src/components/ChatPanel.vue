<template>
  <div class="chat-panel">
    <header class="chat-header">
      <div class="header-main">
        <p class="header-kicker">Conversation Core</p>
        <h3>智能对话工作区</h3>
        <p class="header-meta">
          <span>{{ chatStore.hasMessages ? `${chatStore.messages.length} 条消息` : '尚无消息' }}</span>
          <i></i>
          <span>{{ chatStore.isLoading ? '模型响应中' : '等待输入' }}</span>
        </p>
      </div>

      <div class="header-actions">
        <button
          class="header-btn neon-btn"
          :class="{ active: chatStore.voiceSettings.autoPlay }"
          :title="chatStore.voiceSettings.autoPlay ? '点击关闭自动语音播报' : '点击开启自动语音播报'"
          @click="toggleAutoPlay"
        >
          自动播报 {{ chatStore.voiceSettings.autoPlay ? '开' : '关' }}
        </button>

        <button
          v-if="chatStore.hasMessages"
          class="header-btn clear-btn"
          title="清空对话"
          @click="confirmClear"
        >
          清空记录
        </button>
      </div>
    </header>

    <MessageList ref="messageListRef" @example="handleSend" />

    <MessageInput @send="handleSend" />

    <transition name="dialog-fade">
      <div v-if="showClearConfirm" class="confirm-overlay" @click="showClearConfirm = false">
        <div class="confirm-dialog glass-panel" @click.stop>
          <p class="dialog-title">确认清空会话记录？</p>
          <p class="dialog-desc">该操作会移除本地存储中的当前会话消息，不影响后端服务。</p>
          <div class="dialog-actions">
            <button class="dialog-btn" @click="showClearConfirm = false">取消</button>
            <button class="dialog-btn danger" @click="handleClear">确认清空</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { inject, nextTick, ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { chatApi } from '../services/api'
import { audioPlayer } from '../services/speech'
import MessageInput from './MessageInput.vue'
import MessageList from './MessageList.vue'

const chatStore = useChatStore()
const messageListRef = ref(null)
const showClearConfirm = ref(false)

const avatarStatus = inject('avatarStatus', ref('idle'))
const isSpeaking = inject('isSpeaking', ref(false))
const currentEmotion = inject('currentEmotion', ref('neutral'))
const videoUrlToPlay = inject('videoUrlToPlay', ref(null))
const onPlaybackEnded = inject('onPlaybackEnded', () => {})

function confirmClear() {
  showClearConfirm.value = true
}

function handleClear() {
  chatStore.clearMessages()
  showClearConfirm.value = false
}

function toggleAutoPlay() {
  chatStore.updateVoiceSettings({ autoPlay: !chatStore.voiceSettings.autoPlay })
}

async function handleSend(rawMessage) {
  const message = String(rawMessage ?? '').trim()
  if (!message || chatStore.isLoading) return

  chatStore.addUserMessage(message)
  chatStore.setLoading(true)

  avatarStatus.value = 'thinking'
  currentEmotion.value = 'neutral'

  const typingMessage = chatStore.addTypingMessage()

  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollToBottom()
  }

  try {
    const response = await chatApi.sendMessage(message, {
      enableTts: chatStore.voiceSettings.enabled,
      voice: chatStore.voiceSettings.voice,
      sessionId: chatStore.sessionId
    })

    const answerText = response.answer || '暂时没有获取到有效回复，请稍后再试。'

    chatStore.updateMessage(typingMessage.id, {
      content: answerText,
      audioUrl: response.audio_url,
      videoUrl: response.video_url,
      isTyping: false,
      isError: false
    })

    setEmotionFromAnswer(answerText)
    avatarStatus.value = 'speaking'

    if (response.video_url && chatStore.voiceSettings.autoPlay) {
      isSpeaking.value = true
      videoUrlToPlay.value = response.video_url
    } else if (response.audio_url && chatStore.voiceSettings.autoPlay) {
      isSpeaking.value = true
      audioPlayer.onEnded = () => {
        isSpeaking.value = false
        avatarStatus.value = 'idle'
        onPlaybackEnded()
      }
      try {
        await audioPlayer.play(response.audio_url)
      } catch (playError) {
        console.error('播放语音失败:', playError)
        isSpeaking.value = false
        avatarStatus.value = 'idle'
      }
    } else {
      avatarStatus.value = 'idle'
      isSpeaking.value = false
    }
  } catch (error) {
    console.error('发送消息失败:', error)

    chatStore.updateMessage(typingMessage.id, {
      content: `抱歉，当前请求失败：${error.message || '请检查后端服务状态后重试。'}`,
      isTyping: false,
      isError: true
    })

    currentEmotion.value = 'sorry'
    avatarStatus.value = 'idle'
    isSpeaking.value = false
  } finally {
    chatStore.setLoading(false)

    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollToBottom()
    }
  }
}

function setEmotionFromAnswer(answer) {
  if (answer.includes('抱歉') || answer.includes('没有找到') || answer.includes('无法')) {
    currentEmotion.value = 'sorry'
    return
  }

  if (answer.includes('推荐') || answer.includes('美味') || answer.includes('好吃')) {
    currentEmotion.value = 'happy'
    return
  }

  if (answer.includes('？') || answer.includes('请问') || answer.includes('是否')) {
    currentEmotion.value = 'confused'
    return
  }

  currentEmotion.value = 'neutral'
}
</script>

<style scoped>
.chat-panel {
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  background: var(--chat-bg);
  overflow: hidden;
}

.chat-header {
  min-height: 54px;
  padding: 10px clamp(18px, 3vw, 34px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border-bottom: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.88);
}

.header-kicker {
  display: none;
}

.header-main h3 {
  margin: 0;
  color: var(--text-main);
  font-size: 0.98rem;
  font-weight: 650;
  letter-spacing: 0;
}

.header-meta {
  margin: 3px 0 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-faint);
  font-size: 0.78rem;
}

.header-meta i {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--line-strong);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-btn {
  min-height: 32px;
  padding: 0 11px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  color: var(--text-muted);
  background: var(--bg-elevated);
  font-size: 0.8rem;
}

.header-btn:hover {
  background: var(--item-hover);
}

.header-btn.active {
  color: #0f7a62;
  border-color: rgba(16, 163, 127, 0.24);
  background: rgba(16, 163, 127, 0.08);
}

.clear-btn {
  color: var(--danger);
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.22);
}

.confirm-dialog {
  width: min(420px, 100%);
  padding: 22px;
  border-radius: 18px;
  background: var(--bg-panel-strong);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-soft);
}

.dialog-title {
  margin: 0 0 8px;
  font-weight: 700;
}

.dialog-desc {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.dialog-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dialog-btn {
  min-height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.dialog-btn:hover {
  background: var(--item-hover);
}

.dialog-btn.danger {
  color: #fff;
  border-color: var(--danger);
  background: var(--danger);
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.18s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .chat-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
