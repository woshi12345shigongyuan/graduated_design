<template>
  <div class="app-shell">
    <div class="ambient-layer" aria-hidden="true">
      <span
        v-for="particle in particles"
        :key="particle.id"
        class="particle"
        :style="particle.style"
      ></span>
    </div>

    <header class="hero glass-panel">
      <div class="hero-main">
        <p class="hero-kicker">NEURAL CULINARY INTERFACE</p>
        <h1>尝尝咸淡 · 智能烹饪中枢</h1>
        <p class="hero-subtitle">
          极简未来主义对话界面，融合 RAG 检索、语音播报与数字人视频回放，
          以低干扰的信息层级提供高效问答体验。
        </p>
      </div>

      <div class="hero-metrics">
        <article class="metric-card">
          <span class="metric-label">系统状态</span>
          <strong>{{ systemStateText }}</strong>
          <span class="metric-indicator" :class="{ ready: isReady }">
            <i class="pulse-dot"></i>
          </span>
        </article>

        <article class="metric-card">
          <span class="metric-label">数字人引擎</span>
          <strong>{{ hasAvatar ? '已加载真人基底' : '默认全息形象' }}</strong>
        </article>
      </div>
    </header>

    <main class="workspace">
      <section class="avatar-panel glass-panel">
        <header class="panel-header">
          <div>
            <p class="panel-kicker">Avatar Node</p>
            <h2>数字人交互舱</h2>
          </div>
          <span class="state-chip" :class="{ active: hasAvatar }">
            {{ hasAvatar ? '已绑定头像' : '未绑定头像' }}
          </span>
        </header>

        <div class="avatar-view">
          <Avatar
            :status="avatarStatus"
            :is-speaking="isSpeaking"
            :emotion="currentEmotion"
            :video-url="videoUrlToPlay"
            :avatar-image-url="hasAvatar ? avatarImageUrl : null"
            @playback-ended="onPlaybackEnded"
          />
        </div>

        <div class="avatar-actions">
          <label class="action-btn upload-btn neon-btn">
            <input type="file" accept="image/*" @change="onAvatarFileChange" hidden>
            {{ hasAvatar ? '更换数字人图片' : '上传数字人图片' }}
          </label>
          <button v-if="hasAvatar" type="button" class="action-btn danger-btn" @click="deleteAvatar">
            移除图片
          </button>
        </div>

        <p class="panel-note">提示：上传正面清晰头像后，系统可生成语音驱动视频回答。</p>
      </section>

      <section class="chat-panel-wrapper glass-panel">
        <ChatPanel />
      </section>
    </main>

    <transition name="fade-up">
      <div v-if="!isReady" class="loading-overlay">
        <div class="loading-card glass-panel">
          <p class="loading-kicker">SYSTEM BOOTSTRAP</p>
          <h3>智能检索系统尚未就绪</h3>
          <p class="loading-message">{{ loadingMessage }}</p>

          <div v-if="isInitializing" class="loading-progress">
            <span class="loader-ring"></span>
            <span>正在构建知识索引...</span>
          </div>

          <button v-else class="boot-btn" @click="initSystem">启动系统</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import Avatar from './components/Avatar.vue'
import { chatApi, digitalHumanApi } from './services/api'

const isReady = ref(false)
const isInitializing = ref(false)
const loadingMessage = ref('点击下方按钮启动 RAG 初始化流程。')

const avatarStatus = ref('idle')
const isSpeaking = ref(false)
const currentEmotion = ref('neutral')

const hasAvatar = ref(false)
const avatarImageUrl = ref('')
const videoUrlToPlay = ref(null)

const systemStateText = computed(() => {
  if (isReady.value) return '在线'
  if (isInitializing.value) return '初始化中'
  return '待启动'
})

const particles = Array.from({ length: 20 }, (_, id) => ({
  id,
  style: createParticleStyle(id)
}))

provide('avatarStatus', avatarStatus)
provide('isSpeaking', isSpeaking)
provide('currentEmotion', currentEmotion)
provide('videoUrlToPlay', videoUrlToPlay)
provide('onPlaybackEnded', onPlaybackEnded)

function createParticleStyle(index) {
  const duration = 10 + (index % 5) * 2 + Math.random() * 1.8
  return {
    '--x': `${Math.round(Math.random() * 100)}%`,
    '--delay': `-${Math.random() * duration}s`,
    '--duration': `${duration}s`,
    '--size': `${Math.floor(Math.random() * 3) + 2}px`,
    '--travel': `${Math.round(Math.random() * 30) - 15}px`,
    '--opacity': (0.25 + Math.random() * 0.55).toFixed(2)
  }
}

function withCacheBuster(url) {
  const joiner = url.includes('?') ? '&' : '?'
  return `${url}${joiner}t=${Date.now()}`
}

async function fetchAvatarStatus() {
  try {
    const res = await digitalHumanApi.getAvatarStatus()
    hasAvatar.value = res.has_avatar === true
    avatarImageUrl.value = res.has_avatar
      ? withCacheBuster(res.avatar_url || digitalHumanApi.getAvatarImageUrl())
      : ''
  } catch (_) {
    hasAvatar.value = false
    avatarImageUrl.value = ''
  }
}

function onAvatarFileChange(event) {
  const file = event.target?.files?.[0]
  if (!file || !file.type.startsWith('image/')) return

  digitalHumanApi
    .uploadAvatar(file)
    .then(() => fetchAvatarStatus())
    .catch((error) => {
      console.error('上传数字人基础图失败:', error)
    })
    .finally(() => {
      event.target.value = ''
    })
}

function deleteAvatar() {
  digitalHumanApi
    .deleteAvatar()
    .then(() => {
      hasAvatar.value = false
      avatarImageUrl.value = ''
    })
    .catch((error) => {
      console.error('删除数字人基础图失败:', error)
    })
}

function onPlaybackEnded() {
  isSpeaking.value = false
  avatarStatus.value = 'idle'
  videoUrlToPlay.value = null
}

async function initSystem() {
  if (isInitializing.value) return

  isInitializing.value = true
  loadingMessage.value = '正在初始化 RAG 系统，首次加载可能需要几分钟...'

  try {
    const result = await chatApi.init()

    if (result.status === 'success' || result.status === 'already_initialized') {
      isReady.value = true
      loadingMessage.value = '系统准备就绪。'
      return
    }

    loadingMessage.value = `初始化失败：${result.message || '未知错误'}`
  } catch (error) {
    loadingMessage.value = `初始化失败：${error.message || '网络错误'}`
  } finally {
    isInitializing.value = false
  }
}

async function checkStatus() {
  try {
    const status = await chatApi.getStatus()
    if (status.ready) {
      isReady.value = true
      loadingMessage.value = '系统准备就绪。'
    }
  } catch (_) {
    console.log('后端服务未启动')
  }
}

onMounted(() => {
  checkStatus()
  fetchAvatarStatus()
})
</script>

<style scoped>
.app-shell {
  position: relative;
  z-index: 0;
  min-height: 100dvh;
  padding: clamp(16px, 2.2vw, 32px);
  display: flex;
  flex-direction: column;
  gap: clamp(16px, 2vw, 24px);
}

.ambient-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  overflow: hidden;
}

.particle {
  position: absolute;
  left: var(--x);
  bottom: -20px;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  opacity: var(--opacity);
  background: radial-gradient(circle at 30% 30%, rgba(154, 217, 255, 0.95), rgba(84, 161, 231, 0.4) 45%, transparent 70%);
  box-shadow: 0 0 12px rgba(119, 190, 255, 0.65);
  animation: floatUp var(--duration) linear infinite;
  animation-delay: var(--delay);
}

@keyframes floatUp {
  0% {
    transform: translate3d(0, 0, 0) scale(0.9);
  }
  100% {
    transform: translate3d(var(--travel), -105vh, 0) scale(1.15);
  }
}

.hero {
  padding: clamp(20px, 2.5vw, 32px);
  border-radius: var(--radius-lg);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 320px);
  gap: clamp(16px, 2vw, 28px);
  overflow: hidden;
  position: relative;
}

.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: linear-gradient(120deg, rgba(130, 185, 251, 0.08), transparent 45%, rgba(140, 129, 255, 0.1));
}

.hero-main {
  position: relative;
  z-index: 1;
}

.hero-kicker {
  margin: 0;
  font-size: 0.8rem;
  letter-spacing: 0.2em;
  color: var(--text-faint);
}

.hero h1 {
  margin: 10px 0 12px;
  font-size: clamp(1.45rem, 2.2vw, 2.35rem);
  line-height: 1.15;
}

.hero-subtitle {
  margin: 0;
  max-width: 64ch;
  color: var(--text-muted);
  font-size: clamp(0.94rem, 1.25vw, 1.08rem);
}

.hero-metrics {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 12px;
}

.metric-card {
  background: rgba(8, 16, 27, 0.6);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  display: grid;
  gap: 6px;
}

.metric-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-faint);
}

.metric-card strong {
  font-size: 1.08rem;
  font-family: var(--font-display);
  letter-spacing: 0.06em;
}

.metric-indicator {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  color: var(--danger);
}

.metric-indicator .pulse-dot,
.metric-indicator .pulse-dot::after {
  background: currentColor;
}

.metric-indicator.ready {
  color: var(--accent-mint);
}

.workspace {
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
  gap: clamp(16px, 1.8vw, 24px);
  align-items: stretch;
  perspective: 1200px;
}

.avatar-panel,
.chat-panel-wrapper {
  border-radius: var(--radius-lg);
}

.avatar-panel {
  padding: clamp(14px, 1.5vw, 20px);
  display: flex;
  flex-direction: column;
  gap: 14px;
  transform: rotateX(1.6deg);
  transform-origin: top;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.panel-kicker {
  margin: 0;
  color: var(--text-faint);
  text-transform: uppercase;
  font-size: 0.74rem;
  letter-spacing: 0.18em;
}

.panel-header h2 {
  margin: 7px 0 0;
  font-size: 1.3rem;
}

.state-chip {
  border-radius: 999px;
  padding: 5px 10px;
  border: 1px solid rgba(181, 197, 218, 0.35);
  color: var(--text-muted);
  font-size: 0.75rem;
  white-space: nowrap;
}

.state-chip.active {
  border-color: rgba(117, 214, 191, 0.55);
  color: #a9eedf;
  box-shadow: 0 0 0 1px rgba(117, 214, 191, 0.18);
}

.avatar-view {
  min-height: 0;
}

.avatar-actions {
  display: grid;
  gap: 10px;
}

.action-btn {
  width: 100%;
  border-radius: 12px;
  min-height: 42px;
  border: 1px solid transparent;
  padding: 0 14px;
  font-size: 0.9rem;
  letter-spacing: 0.02em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.upload-btn {
  color: var(--text-main);
}

.danger-btn {
  background: rgba(246, 97, 127, 0.12);
  border-color: rgba(246, 125, 151, 0.38);
  color: #ffbfd0;
  transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease;
}

.danger-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(250, 147, 171, 0.65);
  background: rgba(246, 97, 127, 0.18);
}

.panel-note {
  margin: 0;
  color: var(--text-faint);
  font-size: 0.83rem;
  line-height: 1.55;
}

.chat-panel-wrapper {
  padding: clamp(10px, 1.3vw, 14px);
  min-height: clamp(540px, 74vh, 900px);
  transform: rotateX(0.7deg);
  transform-origin: top;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(3, 6, 12, 0.74);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 20;
  padding: 20px;
}

.loading-card {
  width: min(460px, 100%);
  border-radius: 20px;
  padding: 24px;
  text-align: center;
  border: 1px solid var(--line-strong);
}

.loading-kicker {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.72rem;
  color: var(--text-faint);
}

.loading-card h3 {
  margin: 12px 0 10px;
  font-size: 1.4rem;
}

.loading-message {
  margin: 0 0 18px;
  color: var(--text-muted);
  line-height: 1.6;
}

.loading-progress {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #b9d8ff;
}

.loader-ring {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid rgba(130, 184, 244, 0.28);
  border-top-color: rgba(130, 184, 244, 0.95);
  animation: spin 0.85s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.boot-btn {
  border: 1px solid rgba(147, 191, 240, 0.55);
  border-radius: 999px;
  min-height: 42px;
  min-width: 148px;
  color: #dff1ff;
  background: linear-gradient(120deg, rgba(73, 125, 190, 0.62), rgba(102, 78, 188, 0.52));
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.boot-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(61, 109, 173, 0.35);
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 1080px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .avatar-panel,
  .chat-panel-wrapper {
    transform: none;
  }
}

@media (max-width: 720px) {
  .app-shell {
    padding: 12px;
  }

  .hero,
  .avatar-panel,
  .chat-panel-wrapper {
    border-radius: 18px;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chat-panel-wrapper {
    min-height: clamp(460px, 68vh, 800px);
  }
}
</style>
