<template>
  <div class="message-input">
    <!-- 语音输入状态 -->
    <div v-if="isListening" class="voice-status">
      <div class="voice-wave">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </div>
      <p>{{ interimText || '正在聆听...' }}</p>
      <button @click="stopListening" class="stop-btn">停止</button>
    </div>

    <!-- 输入区域 -->
    <div v-else class="input-container">
      <textarea
        ref="inputRef"
        v-model="inputText"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.exact="handleNewLine"
        placeholder="输入您的问题... (Enter 发送, Shift+Enter 换行)"
        :disabled="chatStore.isLoading"
        rows="1"
      ></textarea>

      <div class="action-buttons">
        <!-- 语音输入按钮 -->
        <button 
          @click="startListening" 
          class="voice-btn"
          :disabled="chatStore.isLoading || !speechSupported"
          :title="speechSupported ? '语音输入' : '浏览器不支持语音识别'"
        >
          🎤
        </button>

        <!-- 发送按钮 -->
        <button 
          @click="handleSend" 
          class="send-btn"
          :disabled="!inputText.trim() || chatStore.isLoading"
        >
          <span v-if="chatStore.isLoading" class="loading-spinner"></span>
          <span v-else>发送</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { speechRecognition } from '../services/speech'

const emit = defineEmits(['send'])
const chatStore = useChatStore()

const inputRef = ref(null)
const inputText = ref('')
const isListening = ref(false)
const interimText = ref('')
const speechSupported = ref(false)

// 检查语音识别支持
onMounted(() => {
  speechSupported.value = speechRecognition.isSupported

  // 设置语音识别回调
  speechRecognition.onStart = () => {
    isListening.value = true
    interimText.value = ''
  }

  speechRecognition.onEnd = () => {
    isListening.value = false
  }

  speechRecognition.onResult = (result) => {
    if (result.isFinal) {
      inputText.value = result.text
      isListening.value = false
      // 自动发送（可选）
      // handleSend()
    } else {
      interimText.value = result.text
    }
  }

  speechRecognition.onError = (error) => {
    console.error('语音识别错误:', error)
    isListening.value = false
    interimText.value = error
  }
})

onUnmounted(() => {
  speechRecognition.abort()
})

// 发送消息
function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.isLoading) return

  emit('send', text)
  inputText.value = ''
  
  // 重置输入框高度
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
    }
  })
}

// 换行
function handleNewLine(event) {
  const textarea = event.target
  inputText.value += '\n'
  
  // 自动调整高度
  nextTick(() => {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
  })
}

// 开始语音输入
async function startListening() {
  // 先检查权限
  const hasPermission = await speechRecognition.checkPermission()
  if (!hasPermission) {
    alert('请允许使用麦克风')
    return
  }

  speechRecognition.start()
}

// 停止语音输入
function stopListening() {
  speechRecognition.stop()
}
</script>

<style scoped>
.message-input {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  background: white;
}

/* 语音输入状态 */
.voice-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.voice-wave {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 40px;
  margin-bottom: 12px;
}

.voice-wave span {
  width: 4px;
  background: white;
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

.voice-wave span:nth-child(1) { height: 20px; animation-delay: 0s; }
.voice-wave span:nth-child(2) { height: 30px; animation-delay: 0.1s; }
.voice-wave span:nth-child(3) { height: 40px; animation-delay: 0.2s; }
.voice-wave span:nth-child(4) { height: 30px; animation-delay: 0.3s; }
.voice-wave span:nth-child(5) { height: 20px; animation-delay: 0.4s; }

@keyframes wave {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1); }
}

.voice-status p {
  margin-bottom: 12px;
  font-size: 1rem;
}

.stop-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 8px 24px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.2s;
}

.stop-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 输入区域 */
.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

textarea {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  min-height: 48px;
  max-height: 150px;
  transition: border-color 0.2s;
  line-height: 1.5;
}

textarea:focus {
  outline: none;
  border-color: #667eea;
}

textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.voice-btn {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 12px;
  background: #f0f0f0;
  font-size: 1.3rem;
  cursor: pointer;
  transition: all 0.2s;
}

.voice-btn:hover:not(:disabled) {
  background: #e0e0e0;
  transform: scale(1.05);
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  height: 48px;
  padding: 0 24px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
