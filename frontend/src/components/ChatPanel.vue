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
      content: '抱歉，当前请求失败。请检查后端服务状态后重试。',
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
  border-radius: 18px;
  border: 1px solid rgba(138, 169, 204, 0.24);
  background: linear-gradient(160deg, rgba(10, 17, 30, 0.82), rgba(8, 14, 24, 0.66));
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(112, 156, 211, 0.08);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid rgba(116, 149, 185, 0.24);
  background: linear-gradient(180deg, rgba(16, 28, 46, 0.75), rgba(12, 20, 34, 0.45));
}

.header-main {
  min-width: 0;
}

.header-kicker {
  margin: 0;
  color: var(--text-faint);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.18em;
}

.header-main h3 {
  margin: 8px 0 6px;
  font-size: clamp(1.02rem, 1.4vw, 1.24rem);
}

.header-meta {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.82rem;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.header-meta i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(154, 182, 214, 0.6);
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: flex-start;
  gap: 8px;
}

.header-btn {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(131, 165, 207, 0.34);
  background: rgba(11, 20, 34, 0.7);
  color: var(--text-muted);
  font-size: 0.8rem;
  transition: border-color 0.22s ease, color 0.22s ease, transform 0.22s ease;
}

.header-btn.active {
  border-color: rgba(124, 183, 248, 0.7);
  color: #d9ecff;
}

.header-btn:hover {
  transform: translateY(-1px);
  color: var(--text-main);
}

.clear-btn {
  border-color: rgba(243, 130, 157, 0.5);
  color: #ffc4d3;
}

.clear-btn:hover {
  border-color: rgba(244, 129, 160, 0.8);
  color: #ffe2e8;
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: rgba(4, 8, 15, 0.7);
  display: grid;
  place-items: center;
  padding: 16px;
}

.confirm-dialog {
  width: min(380px, 100%);
  padding: 20px;
  border-radius: 16px;
}

.dialog-title {
  margin: 0;
  font-size: 1.05rem;
}

.dialog-desc {
  margin: 8px 0 16px;
  color: var(--text-muted);
  font-size: 0.86rem;
  line-height: 1.55;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dialog-btn {
  min-height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(136, 170, 209, 0.35);
  background: rgba(11, 19, 33, 0.72);
  color: var(--text-main);
  padding: 0 14px;
}

.dialog-btn.danger {
  background: rgba(243, 99, 128, 0.14);
  border-color: rgba(243, 126, 152, 0.48);
  color: #ffc6d4;
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

@media (max-width: 760px) {
  .chat-header {
    flex-direction: column;
  }

  .header-actions {
    justify-content: flex-start;
  }
}
</style>
