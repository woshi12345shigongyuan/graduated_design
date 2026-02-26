<template>
  <div class="app-container">
    <!-- 头部 -->
    <header class="app-header">
      <h1>🍽️ 尝尝咸淡</h1>
      <p class="subtitle">智能食谱助手 - 解决您的选择困难症</p>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <!-- 虚拟数字人区域 -->
      <div class="avatar-section">
        <div class="avatar-actions">
          <label class="upload-btn">
            <input type="file" accept="image/*" @change="onAvatarFileChange" hidden />
            {{ hasAvatar ? '更换图片' : '上传数字人基础图' }}
          </label>
          <button v-if="hasAvatar" type="button" class="delete-btn" @click="deleteAvatar">删除</button>
        </div>
        <Avatar 
          :status="avatarStatus" 
          :is-speaking="isSpeaking"
          :emotion="currentEmotion"
          :video-url="videoUrlToPlay"
          :avatar-image-url="hasAvatar ? avatarImageUrl : null"
          @playback-ended="onPlaybackEnded"
        />
      </div>

      <!-- 聊天区域 -->
      <div class="chat-section">
        <ChatPanel />
      </div>
    </main>

    <!-- 初始化遮罩 -->
    <div v-if="!isReady" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <p>{{ loadingMessage }}</p>
        <button v-if="!isInitializing" @click="initSystem" class="init-btn">
          开始初始化系统
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import { useChatStore } from './stores/chat'
import ChatPanel from './components/ChatPanel.vue'
import Avatar from './components/Avatar.vue'
import { chatApi, digitalHumanApi } from './services/api'

const chatStore = useChatStore()

// 系统状态
const isReady = ref(false)
const isInitializing = ref(false)
const loadingMessage = ref('点击按钮初始化 RAG 系统')

// 数字人状态
const avatarStatus = ref('idle') // idle, thinking, speaking
const isSpeaking = ref(false)
const currentEmotion = ref('neutral') // neutral, happy, confused, sorry

// 数字人基础图：有图时才会调用即梦 API 生成视频
const hasAvatar = ref(false)
const avatarImageUrl = ref('')
const videoUrlToPlay = ref(null) // 当前要播放的数字人视频 URL，由 ChatPanel 设置

// 提供给子组件的状态
provide('avatarStatus', avatarStatus)
provide('isSpeaking', isSpeaking)
provide('currentEmotion', currentEmotion)
provide('videoUrlToPlay', videoUrlToPlay)
provide('onPlaybackEnded', onPlaybackEnded)

async function fetchAvatarStatus() {
  try {
    const res = await digitalHumanApi.getAvatarStatus()
    hasAvatar.value = res.has_avatar === true
    avatarImageUrl.value = res.has_avatar ? (res.avatar_url || digitalHumanApi.getAvatarImageUrl()) : ''
  } catch (_) {
    hasAvatar.value = false
    avatarImageUrl.value = ''
  }
}

function onAvatarFileChange(e) {
  const file = e.target?.files?.[0]
  if (!file || !file.type.startsWith('image/')) return
  digitalHumanApi.uploadAvatar(file).then(() => {
    fetchAvatarStatus()
  }).catch(err => {
    console.error('上传数字人基础图失败:', err)
  })
  e.target.value = ''
}

function deleteAvatar() {
  digitalHumanApi.deleteAvatar().then(() => {
    hasAvatar.value = false
    avatarImageUrl.value = ''
  }).catch(err => console.error('删除失败:', err))
}

function onPlaybackEnded() {
  isSpeaking.value = false
  avatarStatus.value = 'idle'
  videoUrlToPlay.value = null
}

// 初始化系统
async function initSystem() {
  isInitializing.value = true
  loadingMessage.value = '正在初始化 RAG 系统，首次加载可能需要几分钟...'
  
  try {
    const result = await chatApi.init()
    if (result.status === 'success' || result.status === 'already_initialized') {
      isReady.value = true
      loadingMessage.value = '系统准备就绪！'
    } else {
      loadingMessage.value = `初始化失败: ${result.message}`
      isInitializing.value = false
    }
  } catch (error) {
    loadingMessage.value = `初始化失败: ${error.message}`
    isInitializing.value = false
  }
}

// 检查系统状态
async function checkStatus() {
  try {
    const status = await chatApi.getStatus()
    if (status.ready) {
      isReady.value = true
    }
  } catch (error) {
    console.log('后端服务未启动')
  }
}

onMounted(() => {
  checkStatus()
  fetchAvatarStatus()
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.app-header {
  text-align: center;
  color: white;
  padding: 20px 0;
}

.app-header h1 {
  font-size: 2.5rem;
  margin-bottom: 8px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
}

.app-main {
  flex: 1;
  display: flex;
  gap: 24px;
  margin-top: 20px;
}

.avatar-section {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.avatar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.upload-btn, .delete-btn {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  border: none;
}

.upload-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.upload-btn:hover { opacity: 0.9; }

.delete-btn {
  background: rgba(200, 80, 80, 0.9);
  color: white;
}

.delete-btn:hover { opacity: 0.9; }

.chat-section {
  flex: 1;
  min-width: 0;
}

/* 加载遮罩 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
  color: white;
  padding: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-content p {
  font-size: 1.2rem;
  margin-bottom: 20px;
}

.init-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 32px;
  font-size: 1.1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.init-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* 响应式布局 */
@media (max-width: 900px) {
  .app-main {
    flex-direction: column;
  }
  
  .avatar-section {
    flex: none;
    display: flex;
    justify-content: center;
  }
}
</style>
