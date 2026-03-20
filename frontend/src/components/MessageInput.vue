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
  border-top: 1px solid rgba(127, 160, 196, 0.24);
  background: linear-gradient(180deg, rgba(11, 19, 32, 0.72), rgba(8, 14, 23, 0.78));
  padding: 12px;
  display: grid;
  gap: 8px;
}

.voice-status {
  border-radius: 12px;
  border: 1px solid rgba(128, 177, 230, 0.45);
  background: linear-gradient(145deg, rgba(26, 56, 92, 0.55), rgba(38, 31, 90, 0.42));
  min-height: 120px;
  display: grid;
  place-items: center;
  text-align: center;
  padding: 14px;
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
  background: #d8edff;
  animation: wave 1s ease-in-out infinite;
}

.voice-wave span:nth-child(1) {
  height: 16px;
}

.voice-wave span:nth-child(2) {
  height: 24px;
  animation-delay: 0.12s;
}

.voice-wave span:nth-child(3) {
  height: 30px;
  animation-delay: 0.24s;
}

.voice-wave span:nth-child(4) {
  height: 22px;
  animation-delay: 0.36s;
}

.voice-wave span:nth-child(5) {
  height: 14px;
  animation-delay: 0.48s;
}

@keyframes wave {
  0%,
  100% {
    transform: scaleY(0.6);
  }
  50% {
    transform: scaleY(1);
  }
}

.voice-status p {
  margin: 0;
  color: #d5e9ff;
  line-height: 1.5;
}

.stop-btn {
  margin-top: 10px;
  min-height: 34px;
  border: 1px solid rgba(151, 188, 228, 0.45);
  border-radius: 999px;
  padding: 0 14px;
  color: var(--text-main);
  background: rgba(12, 24, 39, 0.75);
}

.input-shell {
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: flex-end;
}

textarea {
  width: 100%;
  min-height: 44px;
  max-height: 180px;
  resize: none;
  border-radius: 12px;
  border: 1px solid rgba(130, 161, 196, 0.34);
  background: rgba(8, 16, 28, 0.72);
  color: var(--text-main);
  padding: 11px 13px;
  line-height: 1.6;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

textarea::placeholder {
  color: rgba(141, 165, 191, 0.78);
}

textarea:focus {
  outline: none;
  border-color: rgba(131, 188, 246, 0.72);
  box-shadow: 0 0 0 2px rgba(116, 174, 236, 0.2);
}

textarea:disabled {
  opacity: 0.74;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-btn,
.send-btn {
  min-height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(132, 165, 200, 0.4);
  background: rgba(12, 22, 35, 0.78);
  color: #d6ebff;
  padding: 0 14px;
  font-size: 0.84rem;
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease;
}

.voice-btn:hover:not(:disabled),
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(130, 190, 248, 0.74);
  background: rgba(16, 30, 48, 0.84);
}

.send-btn {
  min-width: 72px;
  background: linear-gradient(140deg, rgba(72, 119, 176, 0.6), rgba(87, 72, 170, 0.52));
  border-color: rgba(138, 186, 239, 0.58);
}

.voice-btn:disabled,
.send-btn:disabled {
  opacity: 0.52;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(219, 237, 255, 0.38);
  border-top-color: rgba(219, 237, 255, 0.95);
  border-radius: 999px;
  display: inline-block;
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.voice-notice {
  margin: 0;
  color: #ffb0c4;
  font-size: 0.78rem;
  line-height: 1.45;
}

@media (max-width: 760px) {
  .input-shell {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    justify-content: flex-end;
  }
}
</style>
