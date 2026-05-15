<template>
  <div class="message-input">
    <div v-if="isListening" class="voice-status">
      <div class="voice-wave">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </div>
      <p>{{ interimText || '正在聆听，请继续说...' }}</p>
      <button class="stop-btn" @click="stopListening">结束识别</button>
    </div>

    <div v-else class="input-shell">
      <textarea
        ref="inputRef"
        v-model="inputText"
        rows="1"
        :disabled="chatStore.isLoading"
        placeholder="输入你的问题，Enter 发送，Shift + Enter 换行"
        @input="handleInput"
        @keydown.enter.exact.prevent="handleSend"
      ></textarea>

      <div class="action-buttons">
        <button
          class="voice-btn"
          :disabled="chatStore.isLoading || !speechSupported"
          :title="speechSupported ? '语音输入' : '当前浏览器不支持语音识别'"
          @click="startListening"
        >
          语音输入
        </button>

        <button
          class="send-btn"
          :disabled="!inputText.trim() || chatStore.isLoading"
          @click="handleSend"
        >
          <span v-if="chatStore.isLoading" class="loading-spinner"></span>
          <span v-else>发送</span>
        </button>
      </div>
    </div>

    <p v-if="voiceNotice" class="voice-notice">{{ voiceNotice }}</p>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useChatStore } from '../stores/chat'
import { speechRecognition } from '../services/speech'

const MAX_TEXTAREA_HEIGHT = 180

const emit = defineEmits(['send'])
const chatStore = useChatStore()

const inputRef = ref(null)
const inputText = ref('')
const isListening = ref(false)
const interimText = ref('')
const speechSupported = ref(false)
const voiceNotice = ref('')

onMounted(() => {
  speechSupported.value = speechRecognition.isSupported

  speechRecognition.onStart = () => {
    isListening.value = true
    interimText.value = ''
    voiceNotice.value = ''
  }

  speechRecognition.onEnd = () => {
    isListening.value = false
  }

  speechRecognition.onResult = (result) => {
    if (result.isFinal) {
      inputText.value = result.text
      isListening.value = false
      nextTick(() => resizeTextarea())
    } else {
      interimText.value = result.text
    }
  }

  speechRecognition.onError = (error) => {
    isListening.value = false
    interimText.value = ''
    setVoiceNotice(error)
  }
})

onUnmounted(() => {
  speechRecognition.abort()
})

function handleInput() {
  resizeTextarea()
}

function resizeTextarea() {
  if (!inputRef.value) return
  inputRef.value.style.height = 'auto'
  inputRef.value.style.height = `${Math.min(inputRef.value.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.isLoading) return

  emit('send', text)
  inputText.value = ''

  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
    }
  })
}

async function startListening() {
  const hasPermission = await speechRecognition.checkPermission()
  if (!hasPermission) {
    setVoiceNotice('请先授权麦克风权限后再试。')
    return
  }

  speechRecognition.start()
}

function stopListening() {
  speechRecognition.stop()
}

function setVoiceNotice(message) {
  voiceNotice.value = message
  setTimeout(() => {
    if (voiceNotice.value === message) {
      voiceNotice.value = ''
    }
  }, 3200)
}
</script>

<style scoped>
.message-input {
  padding: 14px 18px 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0), #fff 24%);
}

.voice-status,
.input-shell {
  width: min(820px, 100%);
  margin: 0 auto;
}

.voice-status {
  min-height: 112px;
  padding: 16px;
  border: 1px solid rgba(16, 163, 127, 0.2);
  border-radius: 18px;
  display: grid;
  place-items: center;
  text-align: center;
  background: rgba(16, 163, 127, 0.06);
}

.voice-wave {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  margin-bottom: 10px;
}

.voice-wave span {
  width: 4px;
  border-radius: 999px;
  background: var(--accent-mint);
  animation: wave 1s ease-in-out infinite;
}

.voice-wave span:nth-child(1) { height: 14px; }
.voice-wave span:nth-child(2) { height: 23px; animation-delay: 0.12s; }
.voice-wave span:nth-child(3) { height: 30px; animation-delay: 0.24s; }
.voice-wave span:nth-child(4) { height: 22px; animation-delay: 0.36s; }
.voice-wave span:nth-child(5) { height: 13px; animation-delay: 0.48s; }

@keyframes wave {
  0%, 100% { transform: scaleY(0.65); }
  50% { transform: scaleY(1); }
}

.voice-status p {
  margin: 0;
  color: var(--text-main);
}

.stop-btn {
  margin-top: 10px;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  color: var(--text-main);
  background: var(--bg-elevated);
}

.input-shell {
  min-height: 58px;
  padding: 8px 8px 8px 16px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 10px;
  border: 1px solid var(--line-strong);
  border-radius: 18px;
  background: var(--bg-elevated);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.1);
}

textarea {
  width: 100%;
  min-height: 40px;
  max-height: 180px;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-main);
  padding: 9px 0;
  line-height: 1.55;
}

textarea::placeholder {
  color: var(--text-faint);
}

textarea:disabled {
  opacity: 0.68;
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.voice-btn,
.send-btn {
  height: 40px;
  border: none;
  border-radius: 12px;
  display: inline-grid;
  place-items: center;
  color: var(--text-muted);
  background: transparent;
  font-size: 0.85rem;
  transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.voice-btn {
  padding: 0 12px;
}

.voice-btn:hover:not(:disabled) {
  color: var(--text-main);
  background: var(--item-hover);
}

.send-btn {
  width: 40px;
  color: #fff;
  background: var(--accent-mint);
}

.send-btn::before {
  content: '↑';
  font-size: 1.1rem;
  font-weight: 800;
  line-height: 1;
}

.send-btn span:not(.loading-spinner) {
  display: none;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: #0d8f70;
}

.voice-btn:disabled,
.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 999px;
  animation: spin 0.75s linear infinite;
}

.send-btn:has(.loading-spinner)::before {
  content: '';
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.voice-notice {
  width: min(820px, 100%);
  margin: 8px auto 0;
  color: var(--danger);
  font-size: 0.8rem;
}

@media (max-width: 640px) {
  .message-input {
    padding: 12px;
  }

  .input-shell {
    grid-template-columns: 1fr;
    padding: 8px 10px;
  }

  .action-buttons {
    justify-content: flex-end;
  }
}
</style>
