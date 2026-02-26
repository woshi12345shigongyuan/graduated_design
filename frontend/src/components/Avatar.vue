<template>
  <div class="avatar-container" :class="[status, emotion]">
    <!-- 背景装饰 -->
    <div class="avatar-background">
      <div class="decoration-circle c1"></div>
      <div class="decoration-circle c2"></div>
      <div class="decoration-circle c3"></div>
    </div>

    <!-- 数字人主体：有视频时播视频，否则展示基础图或默认 SVG -->
    <div class="avatar-body">
      <video
        v-if="videoUrl"
        ref="videoEl"
        class="avatar-video"
        :src="videoUrl"
        autoplay
        playsinline
        @ended="onVideoEnded"
        @error="onVideoError"
      />
      <img
        v-else-if="avatarImageUrl"
        :src="avatarImageUrl"
        alt="数字人基础图"
        class="avatar-uploaded-img"
      />
      <svg v-else viewBox="0 0 200 240" class="avatar-svg">
        <!-- 身体 -->
        <ellipse cx="100" cy="220" rx="60" ry="30" class="body" />
        
        <!-- 脖子 -->
        <rect x="85" y="150" width="30" height="30" rx="5" class="neck" />
        
        <!-- 头部 -->
        <ellipse cx="100" cy="100" rx="55" ry="60" class="head" />
        
        <!-- 头发 -->
        <path d="M45 90 Q50 30 100 25 Q150 30 155 90 Q150 70 100 65 Q50 70 45 90" class="hair" />
        <path d="M55 75 Q60 55 80 50" class="hair-strand" />
        <path d="M145 75 Q140 55 120 50" class="hair-strand" />
        
        <!-- 眉毛 -->
        <path :d="leftEyebrowPath" class="eyebrow" />
        <path :d="rightEyebrowPath" class="eyebrow" />
        
        <!-- 眼睛 -->
        <g class="eyes" :class="{ blinking: isBlinking }">
          <!-- 左眼 -->
          <ellipse cx="75" cy="95" rx="12" ry="14" class="eye-white" />
          <ellipse :cx="leftPupilX" :cy="pupilY" rx="6" ry="7" class="pupil" />
          <ellipse :cx="leftPupilX - 2" :cy="pupilY - 3" rx="2" ry="2" class="eye-highlight" />
          
          <!-- 右眼 -->
          <ellipse cx="125" cy="95" rx="12" ry="14" class="eye-white" />
          <ellipse :cx="rightPupilX" :cy="pupilY" rx="6" ry="7" class="pupil" />
          <ellipse :cx="rightPupilX - 2" :cy="pupilY - 3" rx="2" ry="2" class="eye-highlight" />
        </g>
        
        <!-- 眼睛闭合 (眨眼时显示) -->
        <g v-if="isBlinking" class="closed-eyes">
          <path d="M63 95 Q75 100 87 95" class="closed-eye" />
          <path d="M113 95 Q125 100 137 95" class="closed-eye" />
        </g>
        
        <!-- 腮红 -->
        <ellipse cx="55" cy="115" rx="10" ry="6" class="blush" />
        <ellipse cx="145" cy="115" rx="10" ry="6" class="blush" />
        
        <!-- 鼻子 -->
        <path d="M100 105 L97 118 Q100 120 103 118 L100 105" class="nose" />
        
        <!-- 嘴巴 -->
        <path :d="mouthPath" class="mouth" :class="{ speaking: isSpeaking }" />
        
        <!-- 厨师帽 -->
        <g class="chef-hat">
          <ellipse cx="100" cy="35" rx="40" ry="15" fill="white" stroke="#ddd" stroke-width="1" />
          <path d="M60 35 Q60 0 100 0 Q140 0 140 35" fill="white" stroke="#ddd" stroke-width="1" />
          <rect x="55" y="30" width="90" height="12" fill="white" stroke="#ddd" stroke-width="1" />
        </g>
      </svg>

      <!-- 说话动画指示器 -->
      <div v-if="isSpeaking" class="speaking-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <!-- 状态文字 -->
    <div class="status-text">
      <span v-if="status === 'idle'">等待您的提问...</span>
      <span v-else-if="status === 'thinking'">思考中...</span>
      <span v-else-if="status === 'speaking'">正在回答</span>
    </div>

    <!-- 表情标签 -->
    <div class="emotion-badge" :class="emotion">
      <span v-if="emotion === 'happy'">😊</span>
      <span v-else-if="emotion === 'confused'">🤔</span>
      <span v-else-if="emotion === 'sorry'">😅</span>
      <span v-else>👨‍🍳</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'idle',
    validator: (v) => ['idle', 'thinking', 'speaking'].includes(v)
  },
  isSpeaking: {
    type: Boolean,
    default: false
  },
  emotion: {
    type: String,
    default: 'neutral',
    validator: (v) => ['neutral', 'happy', 'confused', 'sorry'].includes(v)
  },
  videoUrl: { type: String, default: null },
  avatarImageUrl: { type: String, default: null }
})

const emit = defineEmits(['playback-ended'])
const videoEl = ref(null)

function onVideoEnded() {
  emit('playback-ended')
}

function onVideoError() {
  emit('playback-ended')
}

// 眨眼状态
const isBlinking = ref(false)
let blinkInterval = null

// 瞳孔位置
const pupilOffsetX = ref(0)
const pupilOffsetY = ref(0)

// 嘴型状态（用于说话动画）
const mouthOpenness = ref(0)
let speakingInterval = null

// 计算瞳孔位置
const leftPupilX = computed(() => 75 + pupilOffsetX.value)
const rightPupilX = computed(() => 125 + pupilOffsetX.value)
const pupilY = computed(() => 95 + pupilOffsetY.value)

// 眉毛路径（根据表情变化）
const leftEyebrowPath = computed(() => {
  switch (props.emotion) {
    case 'happy':
      return 'M60 78 Q70 72 85 78' // 弯曲向上
    case 'confused':
      return 'M60 82 Q70 75 85 78' // 一边高一边低
    case 'sorry':
      return 'M60 82 Q70 78 85 82' // 担忧的眉毛
    default:
      return 'M60 80 Q70 76 85 80' // 正常
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

// 嘴巴路径（根据表情和说话状态变化）
const mouthPath = computed(() => {
  const openAmount = mouthOpenness.value
  
  switch (props.emotion) {
    case 'happy':
      // 微笑
      if (props.isSpeaking) {
        return `M80 135 Q100 ${145 + openAmount} 120 135`
      }
      return 'M80 135 Q100 150 120 135'
    case 'confused':
      // 困惑的嘴型
      return 'M85 138 Q100 138 115 140'
    case 'sorry':
      // 抱歉的微笑
      return 'M85 140 Q100 145 115 140'
    default:
      // 正常
      if (props.isSpeaking) {
        return `M85 135 Q100 ${140 + openAmount} 115 135`
      }
      return 'M85 135 Q100 140 115 135'
  }
})

// 眨眼动画
function startBlinking() {
  blinkInterval = setInterval(() => {
    if (Math.random() > 0.7) {
      isBlinking.value = true
      setTimeout(() => {
        isBlinking.value = false
      }, 150)
    }
  }, 2000)
}

function stopBlinking() {
  if (blinkInterval) {
    clearInterval(blinkInterval)
    blinkInterval = null
  }
}

// 说话动画
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

// 思考时眼睛看向一侧
watch(() => props.status, (newStatus) => {
  if (newStatus === 'thinking') {
    pupilOffsetX.value = 3
    pupilOffsetY.value = -2
  } else {
    pupilOffsetX.value = 0
    pupilOffsetY.value = 0
  }
})

// 说话动画控制
watch(() => props.isSpeaking, (speaking) => {
  if (speaking) {
    startSpeaking()
  } else {
    stopSpeaking()
  }
})

onMounted(() => {
  startBlinking()
})

onUnmounted(() => {
  stopBlinking()
  stopSpeaking()
})
</script>

<style scoped>
.avatar-container {
  position: relative;
  width: 100%;
  max-width: 320px;
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 背景装饰 */
.avatar-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.c1 {
  width: 150px;
  height: 150px;
  background: #667eea;
  top: -50px;
  right: -50px;
}

.c2 {
  width: 100px;
  height: 100px;
  background: #764ba2;
  bottom: -30px;
  left: -30px;
}

.c3 {
  width: 60px;
  height: 60px;
  background: #f093fb;
  top: 50%;
  left: 10%;
}

/* 数字人主体 */
.avatar-body {
  position: relative;
  display: flex;
  justify-content: center;
  transition: transform 0.3s ease;
}

.avatar-svg {
  width: 200px;
  height: 240px;
}

.avatar-video,
.avatar-uploaded-img {
  width: 200px;
  height: 240px;
  object-fit: cover;
  border-radius: 12px;
}

.avatar-video {
  background: #000;
}

/* 头部动画 */
.avatar-container.thinking .avatar-body {
  animation: thinking 2s ease-in-out infinite;
}

@keyframes thinking {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-3deg); }
  75% { transform: rotate(3deg); }
}

.avatar-container.speaking .avatar-body {
  animation: speaking-nod 0.8s ease-in-out infinite;
}

@keyframes speaking-nod {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* SVG 样式 */
.body {
  fill: #667eea;
}

.neck {
  fill: #ffd5c8;
}

.head {
  fill: #ffe0d0;
  stroke: #f5c4b8;
  stroke-width: 1;
}

.hair {
  fill: #4a3728;
}

.hair-strand {
  fill: none;
  stroke: #3a2718;
  stroke-width: 2;
}

.eyebrow {
  fill: none;
  stroke: #4a3728;
  stroke-width: 2.5;
  stroke-linecap: round;
  transition: d 0.3s ease;
}

.eye-white {
  fill: white;
  stroke: #ddd;
  stroke-width: 0.5;
}

.pupil {
  fill: #2c1810;
  transition: cx 0.3s ease, cy 0.3s ease;
}

.eye-highlight {
  fill: white;
}

/* 眨眼 */
.eyes.blinking .eye-white,
.eyes.blinking .pupil,
.eyes.blinking .eye-highlight {
  opacity: 0;
}

.closed-eye {
  fill: none;
  stroke: #4a3728;
  stroke-width: 2;
  stroke-linecap: round;
}

.blush {
  fill: #ffb8b8;
  opacity: 0.5;
}

.avatar-container.happy .blush {
  opacity: 0.7;
}

.nose {
  fill: #f5c4b8;
}

.mouth {
  fill: none;
  stroke: #d4726a;
  stroke-width: 3;
  stroke-linecap: round;
  transition: d 0.1s ease;
}

.mouth.speaking {
  fill: #d4726a;
  stroke: #c4625a;
}

.avatar-container.happy .mouth {
  stroke: #e07a72;
  stroke-width: 3.5;
}

/* 说话指示器 */
.speaking-indicator {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
}

.speaking-indicator span {
  width: 6px;
  height: 6px;
  background: #667eea;
  border-radius: 50%;
  animation: bounce 0.6s ease-in-out infinite;
}

.speaking-indicator span:nth-child(2) {
  animation-delay: 0.1s;
}

.speaking-indicator span:nth-child(3) {
  animation-delay: 0.2s;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* 状态文字 */
.status-text {
  text-align: center;
  margin-top: 16px;
  font-size: 0.95rem;
  color: #666;
  min-height: 24px;
}

.avatar-container.thinking .status-text {
  color: #667eea;
}

.avatar-container.speaking .status-text {
  color: #764ba2;
}

/* 表情标签 */
.emotion-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.emotion-badge.happy {
  animation: happy-bounce 0.5s ease;
}

@keyframes happy-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.emotion-badge.confused {
  animation: confused-tilt 0.5s ease;
}

@keyframes confused-tilt {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-10deg); }
  75% { transform: rotate(10deg); }
}

/* 呼吸动画 (空闲状态) */
.avatar-container.idle .avatar-body {
  animation: breathing 3s ease-in-out infinite;
}

@keyframes breathing {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}
</style>
