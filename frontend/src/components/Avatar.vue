<template>
  <div class="avatar-shell" :class="[status, emotion]">
    <div class="holo-ring" aria-hidden="true"></div>

    <div class="avatar-card">
      <div class="avatar-head">
        <span class="status-chip" :class="status">
          <i class="status-dot"></i>
          {{ statusText }}
        </span>
        <span class="emotion-chip">{{ emotionText }}</span>
      </div>

      <div class="avatar-stage">
        <video
          v-if="videoUrl"
          ref="videoRef"
          class="avatar-video"
          :src="videoUrl"
          :muted="isMutedAutoplay"
          autoplay
          playsinline
          webkit-playsinline="true"
          @loadeddata="ensureVideoAutoPlay"
          @ended="onVideoEnded"
          @error="onVideoError"
        ></video>

        <img
          v-else-if="avatarImageUrl"
          :src="avatarImageUrl"
          alt="数字人基础图"
          class="avatar-uploaded-img"
        >

        <svg v-else viewBox="0 0 200 240" class="avatar-svg" role="img" aria-label="数字人默认形象">
          <ellipse cx="100" cy="220" rx="60" ry="30" class="body" />
          <rect x="85" y="150" width="30" height="30" rx="5" class="neck" />
          <ellipse cx="100" cy="100" rx="55" ry="60" class="head" />
          <path d="M45 90 Q50 30 100 25 Q150 30 155 90 Q150 70 100 65 Q50 70 45 90" class="hair" />
          <path d="M55 75 Q60 55 80 50" class="hair-strand" />
          <path d="M145 75 Q140 55 120 50" class="hair-strand" />

          <path :d="leftEyebrowPath" class="eyebrow" />
          <path :d="rightEyebrowPath" class="eyebrow" />

          <g class="eyes" :class="{ blinking: isBlinking }">
            <ellipse cx="75" cy="95" rx="12" ry="14" class="eye-white" />
            <ellipse :cx="leftPupilX" :cy="pupilY" rx="6" ry="7" class="pupil" />
            <ellipse :cx="leftPupilX - 2" :cy="pupilY - 3" rx="2" ry="2" class="eye-highlight" />

            <ellipse cx="125" cy="95" rx="12" ry="14" class="eye-white" />
            <ellipse :cx="rightPupilX" :cy="pupilY" rx="6" ry="7" class="pupil" />
            <ellipse :cx="rightPupilX - 2" :cy="pupilY - 3" rx="2" ry="2" class="eye-highlight" />
          </g>

          <g v-if="isBlinking" class="closed-eyes">
            <path d="M63 95 Q75 100 87 95" class="closed-eye" />
            <path d="M113 95 Q125 100 137 95" class="closed-eye" />
          </g>

          <ellipse cx="55" cy="115" rx="10" ry="6" class="blush" />
          <ellipse cx="145" cy="115" rx="10" ry="6" class="blush" />

          <path d="M100 105 L97 118 Q100 120 103 118 L100 105" class="nose" />
          <path :d="mouthPath" class="mouth" :class="{ speaking: isSpeaking }" />

          <g class="chef-hat">
            <ellipse cx="100" cy="35" rx="40" ry="15" fill="white" stroke="#d7deec" stroke-width="1" />
            <path d="M60 35 Q60 0 100 0 Q140 0 140 35" fill="white" stroke="#d7deec" stroke-width="1" />
            <rect x="55" y="30" width="90" height="12" fill="white" stroke="#d7deec" stroke-width="1" />
          </g>
        </svg>

        <div class="scan-line" aria-hidden="true"></div>

        <div v-if="isSpeaking" class="speaking-indicator" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <p class="status-text">{{ statusHint }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'idle',
    validator: (value) => ['idle', 'thinking', 'speaking'].includes(value)
  },
  isSpeaking: {
    type: Boolean,
    default: false
  },
  emotion: {
    type: String,
    default: 'neutral',
    validator: (value) => ['neutral', 'happy', 'confused', 'sorry'].includes(value)
  },
  videoUrl: {
    type: String,
    default: null
  },
  avatarImageUrl: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['playback-ended'])

const isBlinking = ref(false)
const pupilOffsetX = ref(0)
const pupilOffsetY = ref(0)
const mouthOpenness = ref(0)
const videoRef = ref(null)
const isMutedAutoplay = ref(false)

let blinkInterval = null
let speakingInterval = null

const leftPupilX = computed(() => 75 + pupilOffsetX.value)
const rightPupilX = computed(() => 125 + pupilOffsetX.value)
const pupilY = computed(() => 95 + pupilOffsetY.value)

const statusText = computed(() => {
  if (props.status === 'thinking') return '分析中'
  if (props.status === 'speaking') return '播报中'
  return '待命'
})

const statusHint = computed(() => {
  if (props.status === 'thinking') return '正在检索知识库并组织回答。'
  if (props.status === 'speaking') return '已生成结果，正在进行语音或视频回放。'
  return '准备接收下一条问题。'
})

const emotionText = computed(() => {
  if (props.emotion === 'happy') return '情绪：愉悦'
  if (props.emotion === 'confused') return '情绪：思索'
  if (props.emotion === 'sorry') return '情绪：抱歉'
  return '情绪：中性'
})

const leftEyebrowPath = computed(() => {
  switch (props.emotion) {
    case 'happy':
      return 'M60 78 Q70 72 85 78'
    case 'confused':
      return 'M60 82 Q70 75 85 78'
    case 'sorry':
      return 'M60 82 Q70 78 85 82'
    default:
      return 'M60 80 Q70 76 85 80'
  }
})

const rightEyebrowPath = computed(() => {
  switch (props.emotion) {
    case 'happy':
      return 'M115 78 Q130 72 140 78'
    case 'confused':
      return 'M115 78 Q130 75 140 82'
    case 'sorry':
      return 'M115 82 Q130 78 140 82'
    default:
      return 'M115 80 Q130 76 140 80'
  }
})

const mouthPath = computed(() => {
  const openness = mouthOpenness.value

  switch (props.emotion) {
    case 'happy':
      return props.isSpeaking
        ? `M80 135 Q100 ${145 + openness} 120 135`
        : 'M80 135 Q100 150 120 135'
    case 'confused':
      return 'M85 138 Q100 138 115 140'
    case 'sorry':
      return 'M85 140 Q100 145 115 140'
    default:
      return props.isSpeaking
        ? `M85 135 Q100 ${140 + openness} 115 135`
        : 'M85 135 Q100 140 115 135'
  }
})

function onVideoEnded() {
  emit('playback-ended')
}

function onVideoError() {
  emit('playback-ended')
}

async function ensureVideoAutoPlay() {
  const videoEl = videoRef.value
  if (!videoEl || !props.videoUrl || !videoEl.paused) return

  try {
    await videoEl.play()
  } catch (error) {
    try {
      isMutedAutoplay.value = true
      await nextTick()
      const retryVideoEl = videoRef.value
      if (!retryVideoEl) return
      retryVideoEl.muted = true
      await retryVideoEl.play()
    } catch (retryError) {
      console.error('视频自动播放失败:', retryError)
      emit('playback-ended')
    }
  }
}

function startBlinking() {
  blinkInterval = setInterval(() => {
    if (Math.random() > 0.7) {
      isBlinking.value = true
      setTimeout(() => {
        isBlinking.value = false
      }, 130)
    }
  }, 1900)
}

function stopBlinking() {
  if (blinkInterval) {
    clearInterval(blinkInterval)
    blinkInterval = null
  }
}

function startSpeaking() {
  speakingInterval = setInterval(() => {
    mouthOpenness.value = Math.random() * 8 + 2
  }, 100)
}

function stopSpeaking() {
  if (speakingInterval) {
    clearInterval(speakingInterval)
    speakingInterval = null
  }
  mouthOpenness.value = 0
}

watch(
  () => props.status,
  (value) => {
    if (value === 'thinking') {
      pupilOffsetX.value = 3
      pupilOffsetY.value = -2
    } else {
      pupilOffsetX.value = 0
      pupilOffsetY.value = 0
    }
  }
)

watch(
  () => props.isSpeaking,
  (speaking) => {
    if (speaking) {
      startSpeaking()
    } else {
      stopSpeaking()
    }
  }
)

watch(
  () => props.videoUrl,
  async (newVideoUrl) => {
    isMutedAutoplay.value = false
    if (!newVideoUrl) return
    await nextTick()
    await ensureVideoAutoPlay()
  }
)

onMounted(() => {
  startBlinking()
})

onUnmounted(() => {
  stopBlinking()
  stopSpeaking()
})
</script>

<style scoped>
.avatar-shell {
  position: relative;
  width: 100%;
}

.holo-ring {
  position: absolute;
  inset: -20px -8px;
  border-radius: 32px;
  background:
    radial-gradient(circle at 70% 12%, rgba(125, 175, 244, 0.24), transparent 44%),
    radial-gradient(circle at 12% 86%, rgba(119, 224, 196, 0.2), transparent 42%);
  filter: blur(16px);
  z-index: 0;
}

.avatar-card {
  position: relative;
  z-index: 1;
  border-radius: 18px;
  border: 1px solid rgba(137, 171, 208, 0.3);
  background: linear-gradient(160deg, rgba(11, 20, 33, 0.82), rgba(9, 15, 27, 0.68));
  padding: 12px;
}

.avatar-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.status-chip,
.emotion-chip {
  min-height: 26px;
  border-radius: 999px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(136, 169, 205, 0.34);
  color: var(--text-muted);
  font-size: 0.74rem;
  white-space: nowrap;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8ca0b8;
  box-shadow: 0 0 0 4px rgba(133, 160, 189, 0.2);
}

.status-chip.thinking .status-dot {
  background: #9dd5ff;
  box-shadow: 0 0 0 4px rgba(115, 187, 248, 0.25);
}

.status-chip.speaking .status-dot {
  background: #82e2c6;
  box-shadow: 0 0 0 4px rgba(124, 225, 198, 0.24);
}

.avatar-stage {
  position: relative;
  min-height: 260px;
  border-radius: 14px;
  border: 1px solid rgba(129, 164, 202, 0.3);
  background:
    radial-gradient(circle at 18% 20%, rgba(119, 174, 239, 0.14), transparent 55%),
    radial-gradient(circle at 78% 80%, rgba(109, 207, 182, 0.12), transparent 56%),
    rgba(8, 15, 26, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.avatar-video,
.avatar-uploaded-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-svg {
  width: min(220px, 95%);
  height: auto;
  max-height: 250px;
}

.scan-line {
  position: absolute;
  inset: -30% 0 auto;
  height: 40%;
  background: linear-gradient(180deg, transparent, rgba(160, 211, 255, 0.2), transparent);
  animation: scanDown 4.5s linear infinite;
  pointer-events: none;
}

@keyframes scanDown {
  0% {
    transform: translateY(-170%);
  }
  100% {
    transform: translateY(250%);
  }
}

.speaking-indicator {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: flex-end;
  gap: 4px;
}

.speaking-indicator span {
  width: 4px;
  height: 14px;
  border-radius: 999px;
  background: rgba(132, 216, 192, 0.95);
  animation: barWave 0.7s ease-in-out infinite;
}

.speaking-indicator span:nth-child(2) {
  animation-delay: 0.12s;
}

.speaking-indicator span:nth-child(3) {
  animation-delay: 0.24s;
}

.speaking-indicator span:nth-child(4) {
  animation-delay: 0.36s;
}

@keyframes barWave {
  0%,
  100% {
    transform: scaleY(0.45);
  }
  50% {
    transform: scaleY(1);
  }
}

.status-text {
  margin: 10px 0 0;
  font-size: 0.8rem;
  color: var(--text-faint);
  line-height: 1.55;
}

.avatar-shell.thinking .avatar-stage {
  animation: thinkingTilt 2.2s ease-in-out infinite;
}

.avatar-shell.speaking .avatar-stage {
  animation: speakingPulse 0.9s ease-in-out infinite;
}

@keyframes thinkingTilt {
  0%,
  100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-1.2deg);
  }
  75% {
    transform: rotate(1.2deg);
  }
}

@keyframes speakingPulse {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

.body {
  fill: #7ba9ff;
}

.neck {
  fill: #ffd5c8;
}

.head {
  fill: #ffe0d0;
  stroke: #f6c6bc;
  stroke-width: 1;
}

.hair {
  fill: #473325;
}

.hair-strand {
  fill: none;
  stroke: #322114;
  stroke-width: 2;
}

.eyebrow {
  fill: none;
  stroke: #3b291c;
  stroke-width: 2.5;
  stroke-linecap: round;
}

.eye-white {
  fill: #ffffff;
  stroke: #dde3ee;
  stroke-width: 0.6;
}

.pupil {
  fill: #2d1a12;
  transition: cx 0.24s ease, cy 0.24s ease;
}

.eye-highlight {
  fill: #ffffff;
}

.eyes.blinking .eye-white,
.eyes.blinking .pupil,
.eyes.blinking .eye-highlight {
  opacity: 0;
}

.closed-eye {
  fill: none;
  stroke: #3b291c;
  stroke-width: 2;
  stroke-linecap: round;
}

.blush {
  fill: #ffb9ba;
  opacity: 0.5;
}

.avatar-shell.happy .blush {
  opacity: 0.72;
}

.nose {
  fill: #f7c8bc;
}

.mouth {
  fill: none;
  stroke: #cf6f67;
  stroke-width: 3;
  stroke-linecap: round;
  transition: d 0.1s ease;
}

.mouth.speaking {
  fill: #cf6f67;
  stroke: #bb5d56;
}

@media (max-width: 1080px) {
  .avatar-stage {
    min-height: 320px;
  }
}

@media (max-width: 760px) {
  .avatar-stage {
    min-height: 260px;
  }

  .emotion-chip {
    display: none;
  }
}
</style>
