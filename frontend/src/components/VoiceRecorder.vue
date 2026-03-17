<template>
  <div class="voice-recorder" :class="{ recording: isRecording }">
    <button
      class="record-btn"
      :disabled="disabled || !isSupported"
      :title="buttonTitle"
      @mousedown="startRecording"
      @mouseup="stopRecording"
      @mouseleave="stopRecording"
      @touchstart.prevent="startRecording"
      @touchend.prevent="stopRecording"
    >
      <span class="mic-label">MIC</span>
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>

      <span v-if="isRecording" class="recording-wave" aria-hidden="true">
        <i v-for="i in 5" :key="i"></i>
      </span>
    </button>

    <p v-if="interimResult" class="interim-text">{{ interimResult }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { speechRecognition } from '../services/speech'

const CLEAR_ERROR_DELAY = 3000

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

let clearErrorTimer = null

const buttonTitle = computed(() => {
  if (!isSupported.value) return '浏览器不支持语音识别'
  if (props.disabled) return '语音输入不可用'
  return '按住说话'
})

onMounted(() => {
  isSupported.value = speechRecognition.isSupported

  speechRecognition.onStart = () => {
    isRecording.value = true
    error.value = ''
    clearErrorTimeout()
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
    isRecording.value = false
    error.value = err
    emit('error', err)
    queueClearError()
  }
})

onUnmounted(() => {
  clearErrorTimeout()
  speechRecognition.abort()
})

async function startRecording() {
  if (props.disabled || !isSupported.value) return

  const hasPermission = await speechRecognition.checkPermission()
  if (!hasPermission) {
    error.value = '请允许使用麦克风'
    emit('error', error.value)
    queueClearError()
    return
  }

  speechRecognition.start()
}

function stopRecording() {
  if (isRecording.value) {
    speechRecognition.stop()
  }
}

function queueClearError() {
  clearErrorTimeout()
  clearErrorTimer = setTimeout(() => {
    error.value = ''
    clearErrorTimer = null
  }, CLEAR_ERROR_DELAY)
}

function clearErrorTimeout() {
  if (clearErrorTimer) {
    clearTimeout(clearErrorTimer)
    clearErrorTimer = null
  }
}
</script>

<style scoped>
.voice-recorder {
  display: grid;
  gap: 8px;
  justify-items: center;
}

.record-btn {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 18px;
  border: 1px solid rgba(132, 167, 205, 0.44);
  background: linear-gradient(140deg, rgba(13, 24, 39, 0.82), rgba(10, 18, 30, 0.66));
  color: #cfe7ff;
  box-shadow: 0 14px 26px rgba(4, 11, 22, 0.36);
  display: grid;
  place-items: center;
  overflow: hidden;
  transition: transform 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease;
}

.record-btn svg {
  width: 24px;
  height: 24px;
}

.record-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(127, 190, 251, 0.74);
  box-shadow: 0 18px 30px rgba(25, 62, 106, 0.34);
}

.record-btn:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.mic-label {
  position: absolute;
  top: 5px;
  left: 7px;
  font-size: 0.55rem;
  letter-spacing: 0.14em;
  color: rgba(175, 207, 239, 0.78);
}

.voice-recorder.recording .record-btn {
  border-color: rgba(130, 229, 204, 0.88);
  color: #d6fff3;
  background: linear-gradient(140deg, rgba(20, 56, 78, 0.82), rgba(21, 44, 65, 0.72));
}

.recording-wave {
  position: absolute;
  inset: auto 0 6px;
  display: inline-flex;
  justify-content: center;
  align-items: flex-end;
  gap: 2px;
}

.recording-wave i {
  width: 3px;
  height: 8px;
  border-radius: 999px;
  background: rgba(179, 246, 231, 0.95);
  animation: wave 0.7s ease-in-out infinite;
}

.recording-wave i:nth-child(2) {
  animation-delay: 0.1s;
}

.recording-wave i:nth-child(3) {
  animation-delay: 0.2s;
}

.recording-wave i:nth-child(4) {
  animation-delay: 0.3s;
}

.recording-wave i:nth-child(5) {
  animation-delay: 0.4s;
}

@keyframes wave {
  0%,
  100% {
    transform: scaleY(0.5);
  }
  50% {
    transform: scaleY(1.3);
  }
}

.interim-text,
.error-text {
  margin: 0;
  max-width: 220px;
  text-align: center;
  font-size: 0.8rem;
  line-height: 1.5;
}

.interim-text {
  color: var(--text-muted);
}

.error-text {
  color: #ffb2c5;
}
</style>
