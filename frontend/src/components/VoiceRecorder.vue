<template>
  <div class="voice-recorder" :class="{ recording: isRecording }">
    <button 
      @mousedown="startRecording"
      @mouseup="stopRecording"
      @mouseleave="stopRecording"
      @touchstart.prevent="startRecording"
      @touchend.prevent="stopRecording"
      :disabled="disabled || !isSupported"
      class="record-btn"
      :title="buttonTitle"
    >
      <div class="mic-icon">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      </div>
      <div v-if="isRecording" class="recording-wave">
        <span v-for="i in 5" :key="i"></span>
      </div>
    </button>

    <div v-if="interimResult" class="interim-text">
      {{ interimResult }}
    </div>

    <div v-if="error" class="error-text">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { speechRecognition } from '../services/speech'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['result', 'error', 'start', 'end'])

const isRecording = ref(false)
const isSupported = ref(false)
const interimResult = ref('')
const error = ref('')

const buttonTitle = computed(() => {
  if (!isSupported.value) {
    return '浏览器不支持语音识别'
  }
  if (props.disabled) {
    return '语音输入不可用'
  }
  return '按住说话'
})

onMounted(() => {
  isSupported.value = speechRecognition.isSupported

  speechRecognition.onStart = () => {
    isRecording.value = true
    error.value = ''
    emit('start')
  }

  speechRecognition.onEnd = () => {
    isRecording.value = false
    interimResult.value = ''
    emit('end')
  }

  speechRecognition.onResult = (result) => {
    if (result.isFinal) {
      emit('result', result.text)
      interimResult.value = ''
    } else {
      interimResult.value = result.text
    }
  }

  speechRecognition.onError = (err) => {
    error.value = err
    isRecording.value = false
    emit('error', err)
    
    // 3秒后清除错误
    setTimeout(() => {
      error.value = ''
    }, 3000)
  }
})

onUnmounted(() => {
  speechRecognition.abort()
})

async function startRecording() {
  if (props.disabled || !isSupported.value) return

  const hasPermission = await speechRecognition.checkPermission()
  if (!hasPermission) {
    error.value = '请允许使用麦克风'
    emit('error', error.value)
    return
  }

  speechRecognition.start()
}

function stopRecording() {
  if (isRecording.value) {
    speechRecognition.stop()
  }
}
</script>

<style scoped>
.voice-recorder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.record-btn {
  position: relative;
  width: 56px;
  height: 56px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.record-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5);
}

.record-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-recorder.recording .record-btn {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  animation: pulse-recording 1s ease-in-out infinite;
}

@keyframes pulse-recording {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.mic-icon {
  width: 24px;
  height: 24px;
}

.mic-icon svg {
  width: 100%;
  height: 100%;
}

.recording-wave {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.recording-wave span {
  width: 3px;
  height: 12px;
  background: white;
  border-radius: 2px;
  animation: wave-animation 0.6s ease-in-out infinite;
}

.recording-wave span:nth-child(1) { animation-delay: 0s; }
.recording-wave span:nth-child(2) { animation-delay: 0.1s; }
.recording-wave span:nth-child(3) { animation-delay: 0.2s; }
.recording-wave span:nth-child(4) { animation-delay: 0.3s; }
.recording-wave span:nth-child(5) { animation-delay: 0.4s; }

@keyframes wave-animation {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1.5); }
}

.interim-text {
  font-size: 0.9rem;
  color: #667eea;
  text-align: center;
  max-width: 200px;
  animation: fade-in 0.2s ease;
}

.error-text {
  font-size: 0.85rem;
  color: #e74c3c;
  text-align: center;
  animation: shake 0.3s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}
</style>
