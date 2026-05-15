<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-card">
        <div class="brand-icon">食</div>
        <div>
          <p class="brand-kicker">Recipe GPT</p>
          <h1>智能食谱助手</h1>
        </div>
      </div>

      <button type="button" class="new-chat-btn" title="清空当前聊天并开始新对话" @click="startNewChat">
        <span class="btn-icon">＋</span>
        <span>新对话</span>
      </button>



      <section class="sidebar-section status-card">
        <p class="sidebar-title">状态</p>
        <div class="status-row">
          <span>RAG</span>
          <strong :class="{ online: isReady }">{{ systemStateText }}</strong>
        </div>
        <div class="status-row">
          <span>数字人</span>
          <strong :class="{ online: hasAvatar }">{{ hasAvatar ? '已绑定' : '默认形象' }}</strong>
        </div>
      </section>

      <section class="sidebar-section avatar-card">
        <div class="sidebar-title-row">
          <p class="sidebar-title">数字人</p>
          <span class="mini-chip" :class="{ active: hasAvatar }">{{ hasAvatar ? 'ON' : 'OFF' }}</span>
        </div>

        <div class="avatar-compact">
          <Avatar
            :status="avatarStatus"
            :is-speaking="isSpeaking"
            :emotion="currentEmotion"
            :video-url="videoUrlToPlay"
            :avatar-image-url="hasAvatar ? avatarImageUrl : null"
            @playback-ended="onPlaybackEnded"
          />
        </div>

        <div class="compact-actions">
          <label class="sidebar-btn primary upload-avatar-btn" :class="{ disabled: isAvatarUploading }">
            <input type="file" accept="image/*" @change="onAvatarFileChange" hidden>
            <span class="btn-icon">🖼️</span>
            <span>{{ isAvatarUploading ? '上传中...' : (hasAvatar ? '更换数字人图片' : '上传数字人图片') }}</span>
          </label>
          <button v-if="hasAvatar" type="button" class="sidebar-btn ghost danger" @click="deleteAvatar">
            移除
          </button>
        </div>
      </section>

      <section class="sidebar-section docs-card">
        <div class="sidebar-title-row">
          <p class="sidebar-title">知识库</p>
          <span class="mini-chip">{{ uploadedDocuments.length }}</span>
        </div>

        <label class="sidebar-btn primary" :class="{ disabled: isDocumentUploading }">
          <input
            type="file"
            accept=".md,.txt,.pdf,.docx,text/markdown,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            :disabled="isDocumentUploading"
            @change="onKnowledgeFileChange"
            hidden
          >
          {{ isDocumentUploading ? '上传中...' : '上传文档' }}
        </label>

        <p v-if="documentNotice" class="doc-notice" :class="{ error: isDocumentNoticeError }">
          {{ documentNotice }}
        </p>

        <div class="doc-list-wrapper">
          <p v-if="isDocumentsLoading" class="doc-placeholder">正在加载...</p>
          <p v-else-if="uploadedDocuments.length === 0" class="doc-placeholder">暂无文档</p>
          <ul v-else class="doc-list">
            <li v-for="doc in uploadedDocuments" :key="doc.filename" class="doc-item">
              <button type="button" class="doc-name-btn" :title="doc.filename">
                {{ doc.filename }}
              </button>
              <button
                type="button"
                class="doc-delete-btn"
                :disabled="isDocumentUploading || deletingDocumentName === doc.filename"
                @click="deleteKnowledgeDocument(doc.filename)"
              >
                {{ deletingDocumentName === doc.filename ? '...' : '×' }}
              </button>
            </li>
          </ul>
        </div>
      </section>
    </aside>

    <main class="chat-main">
      <header class="topbar">
        <div>
          <p class="topbar-kicker">GPT-style culinary assistant</p>
          <h2>今天想吃点什么？</h2>
        </div>
        <div class="topbar-actions">
          <span class="topbar-chip" :class="{ ready: isReady }">
            <i class="pulse-dot"></i>
            {{ systemStateText }}
          </span>
          <span class="topbar-chip">RAG + TTS</span>
        </div>
      </header>

      <section class="chat-panel-wrapper">
        <ChatPanel />
      </section>

      <transition name="fade-up">
        <div v-if="!isReady" class="loading-overlay">
          <div class="loading-card">
            <div class="loading-logo">咸</div>
            <p class="loading-kicker">系统启动</p>
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
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import Avatar from './components/Avatar.vue'
import { chatApi, digitalHumanApi, knowledgeApi } from './services/api'
import { useChatStore } from './stores/chat'

const chatStore = useChatStore()

const isReady = ref(false)
const isInitializing = ref(false)
const loadingMessage = ref('点击下方按钮启动 RAG 初始化流程。')

const avatarStatus = ref('idle')
const isSpeaking = ref(false)
const currentEmotion = ref('neutral')

const hasAvatar = ref(false)
const avatarImageUrl = ref('')
const isAvatarUploading = ref(false)
const videoUrlToPlay = ref(null)
const uploadedDocuments = ref([])
const isDocumentsLoading = ref(false)
const isDocumentUploading = ref(false)
const deletingDocumentName = ref('')
const documentNotice = ref('')
const isDocumentNoticeError = ref(false)

const systemStateText = computed(() => {
  if (isReady.value) return '在线'
  if (isInitializing.value) return '初始化中'
  return '待启动'
})

provide('avatarStatus', avatarStatus)
provide('isSpeaking', isSpeaking)
provide('currentEmotion', currentEmotion)
provide('videoUrlToPlay', videoUrlToPlay)
provide('onPlaybackEnded', onPlaybackEnded)

function startNewChat() {
  chatStore.clearMessages()
  isSpeaking.value = false
  avatarStatus.value = 'idle'
  currentEmotion.value = 'neutral'
  videoUrlToPlay.value = null
}

function withCacheBuster(url) {
  const joiner = url.includes('?') ? '&' : '?'
  return `${url}${joiner}t=${Date.now()}`
}

function setDocumentNotice(message, isError = false) {
  documentNotice.value = message
  isDocumentNoticeError.value = isError
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

async function fetchKnowledgeDocuments() {
  isDocumentsLoading.value = true
  try {
    const result = await knowledgeApi.listDocuments()
    uploadedDocuments.value = Array.isArray(result.documents) ? result.documents : []
  } catch (error) {
    console.error('获取文档列表失败:', error)
    setDocumentNotice('获取文档列表失败，请检查后端服务是否运行。', true)
  } finally {
    isDocumentsLoading.value = false
  }
}

function onAvatarFileChange(event) {
  const file = event.target?.files?.[0]
  if (!file || !file.type.startsWith('image/')) return

  isAvatarUploading.value = true
  digitalHumanApi
    .uploadAvatar(file)
    .then(() => fetchAvatarStatus())
    .catch((error) => {
      console.error('上传数字人基础图失败:', error)
    })
    .finally(() => {
      isAvatarUploading.value = false
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

async function onKnowledgeFileChange(event) {
  const file = event.target?.files?.[0]
  if (!file) return

  const lowerName = file.name.toLowerCase()
  const isAllowed =
    lowerName.endsWith('.md') ||
    lowerName.endsWith('.txt') ||
    lowerName.endsWith('.pdf') ||
    lowerName.endsWith('.docx')
  if (!isAllowed) {
    setDocumentNotice('仅支持上传 .md/.txt/.pdf/.docx 文件。', true)
    event.target.value = ''
    return
  }

  isDocumentUploading.value = true
  setDocumentNotice('正在上传文档并更新知识库...')

  try {
    const response = await knowledgeApi.uploadDocument(file)
    setDocumentNotice(response.message || '文档上传成功。')
    await fetchKnowledgeDocuments()
  } catch (error) {
    console.error('上传知识库文档失败:', error)
    const detail = error?.response?.data?.detail
    setDocumentNotice(detail ? `上传失败：${detail}` : '上传失败，请稍后重试。', true)
  } finally {
    isDocumentUploading.value = false
    event.target.value = ''
  }
}

async function deleteKnowledgeDocument(filename) {
  if (!filename) return

  const confirmed = window.confirm(`确认删除文档「${filename}」吗？`)
  if (!confirmed) return

  deletingDocumentName.value = filename
  setDocumentNotice('正在删除文档并更新知识库...')

  try {
    const response = await knowledgeApi.deleteDocument(filename)
    setDocumentNotice(response.message || '文档删除成功。')
    await fetchKnowledgeDocuments()
  } catch (error) {
    console.error('删除知识库文档失败:', error)
    const detail = error?.response?.data?.detail
    setDocumentNotice(detail ? `删除失败：${detail}` : '删除失败，请稍后重试。', true)
  } finally {
    deletingDocumentName.value = ''
  }
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
  fetchKnowledgeDocuments()
})
</script>

<style scoped>
.app-shell {
  min-height: 100dvh;
  display: grid;
  grid-template-columns: 380px minmax(0, 1fr);
  background: var(--bg-base);
  color: var(--text-main);
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100dvh;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--line-soft);
  overflow-y: auto;
}

.brand-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px 14px;
}

.brand-icon,
.loading-logo {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #10a37f, #37b5ff);
  box-shadow: 0 10px 24px rgba(16, 163, 127, 0.28);
}

.brand-kicker,
.topbar-kicker,
.loading-kicker,
.sidebar-title {
  margin: 0;
  color: var(--text-faint);
  font-size: 0.76rem;
  letter-spacing: 0.04em;
}

.brand-card h1 {
  margin: 2px 0 0;
  font-size: 1.02rem;
  letter-spacing: 0;
}

.new-chat-btn,
.nav-item,
.sidebar-btn {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-main);
  background: transparent;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.new-chat-btn {
  justify-content: flex-start;
  padding: 0 12px;
  font-weight: 650;
  color: var(--text-main);
  background: #ffffff;
}

.btn-icon {
  flex: 0 0 auto;
  display: inline-grid;
  place-items: center;
  min-width: 20px;
}

.new-chat-btn:hover,
.nav-item:hover,
.sidebar-btn:hover:not(.disabled) {
  background: var(--item-hover);
  border-color: rgba(255, 255, 255, 0.18);
}

.sidebar-section {
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.025);
}



.status-card,
.docs-card,
.avatar-card {
  display: grid;
  gap: 10px;
}

.status-row,
.sidebar-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.status-row {
  color: var(--text-muted);
  font-size: 0.88rem;
}

.status-row strong {
  color: var(--text-faint);
  font-size: 0.82rem;
}

.status-row strong.online,
.mini-chip.active {
  color: var(--accent-mint);
}

.mini-chip {
  border-radius: 999px;
  padding: 3px 8px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.06);
  font-size: 0.72rem;
}

.avatar-compact {
  height: 400px;
  border-radius: 14px;
  overflow: hidden;
  background: var(--bg-elevated);
  border: 1px solid var(--line-soft);
}

.compact-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.sidebar-btn {
  min-height: 36px;
  padding: 0 10px;
  font-size: 0.84rem;
  white-space: nowrap;
}

.sidebar-btn.primary {
  border-color: rgba(16, 163, 127, 0.38);
  background: #10a37f;
  color: #ffffff;
  font-weight: 650;
}

.upload-avatar-btn {
  min-height: 40px;
  overflow: hidden;
}

.upload-avatar-btn span:last-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-btn.ghost {
  width: auto;
}

.sidebar-btn.danger,
.doc-delete-btn {
  color: #ffb7c8;
  border-color: rgba(248, 113, 146, 0.35);
  background: rgba(248, 113, 146, 0.08);
}

.disabled {
  opacity: 0.55;
  pointer-events: none;
}

.doc-notice {
  margin: 0;
  padding: 9px 10px;
  border-radius: 12px;
  color: #cfe9ff;
  background: rgba(55, 181, 255, 0.1);
  border: 1px solid rgba(55, 181, 255, 0.2);
  font-size: 0.78rem;
  line-height: 1.45;
}

.doc-notice.error {
  color: #ffd0dc;
  background: rgba(248, 113, 146, 0.1);
  border-color: rgba(248, 113, 146, 0.25);
}

.doc-list-wrapper {
  max-height: 188px;
  overflow-y: auto;
}

.doc-placeholder {
  margin: 0;
  color: var(--text-faint);
  font-size: 0.82rem;
}

.doc-list {
  margin: 0;
  padding: 0;
  display: grid;
  gap: 4px;
  list-style: none;
}

.doc-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 28px;
  gap: 6px;
  align-items: center;
}

.doc-name-btn,
.doc-delete-btn {
  min-height: 30px;
  border: none;
  border-radius: 9px;
}

.doc-name-btn {
  min-width: 0;
  padding: 0 9px;
  color: var(--text-muted);
  text-align: left;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  background: transparent;
}

.doc-name-btn:hover {
  color: var(--text-main);
  background: var(--item-hover);
}



.chat-main {
  position: relative;
  min-width: 0;
  height: 100dvh;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  background: var(--chat-bg);
}

.topbar {
  min-height: 64px;
  padding: 12px clamp(18px, 3vw, 34px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.topbar h2 {
  margin: 2px 0 0;
  font-size: 1.05rem;
  color: var(--text-main);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.topbar-chip {
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-muted);
  background: var(--bg-elevated);
  border: 1px solid var(--line-soft);
  font-size: 0.8rem;
}

.topbar-chip.ready {
  color: #0f7a62;
  border-color: rgba(16, 163, 127, 0.24);
  background: rgba(16, 163, 127, 0.08);
}

.topbar-chip .pulse-dot,
.topbar-chip .pulse-dot::after {
  background: currentColor;
}

.chat-panel-wrapper {
  min-height: 0;
}

.loading-overlay {
  position: absolute;
  inset: 64px 0 0;
  z-index: 10;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(247, 247, 248, 0.82);
  backdrop-filter: blur(12px);
}

.loading-card {
  width: min(440px, 100%);
  padding: 28px;
  border-radius: 24px;
  text-align: center;
  background: var(--bg-panel-strong);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-soft);
}

.loading-logo {
  margin: 0 auto 14px;
}

.loading-card h3 {
  margin: 8px 0 10px;
  color: var(--text-main);
}

.loading-message {
  margin: 0 0 18px;
  color: var(--text-muted);
  line-height: 1.65;
}

.loading-progress {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-muted);
}

.loader-ring {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(16, 163, 127, 0.18);
  border-top-color: #10a37f;
  animation: spin 0.85s linear infinite;
}

.boot-btn {
  min-height: 42px;
  min-width: 128px;
  border: none;
  border-radius: 999px;
  color: #fff;
  background: #10a37f;
  box-shadow: 0 10px 24px rgba(16, 163, 127, 0.24);
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: relative;
    height: auto;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
  }

  .brand-card,
  .new-chat-btn,
  .quick-nav {
    grid-column: span 2;
  }

  .chat-main {
    height: 78dvh;
  }

  .avatar-compact {
    height: 320px;
  }
}

@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: relative;
    height: auto;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
  }

  .brand-card,
  .new-chat-btn,
  .quick-nav {
    grid-column: span 2;
  }

  .chat-main {
    height: 78dvh;
  }
}

@media (max-width: 640px) {
  .sidebar {
    grid-template-columns: 1fr;
  }

  .brand-card,
  .new-chat-btn,
  .quick-nav {
    grid-column: auto;
  }

  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .chat-main {
    height: 82dvh;
  }
}
</style>