/**
 * 聊天状态管理 - Pinia Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'changchangxiandan_chat_history'
const DEFAULT_VOICE_SETTINGS = {
  enabled: true,
  voice: 'xiaoxiao',
  autoPlay: true
}

export const useChatStore = defineStore('chat', () => {
  // 消息列表
  const messages = ref([])
  
  // 当前会话ID
  const sessionId = ref(generateSessionId())
  
  // 是否正在加载
  const isLoading = ref(false)
  
  // 当前输入
  const currentInput = ref('')
  
  // 语音设置
  const voiceSettings = ref({ ...DEFAULT_VOICE_SETTINGS })

  // 计算属性：是否有消息
  const hasMessages = computed(() => messages.value.length > 0)

  // 计算属性：最后一条消息
  const lastMessage = computed(() => {
    if (messages.value.length === 0) return null
    return messages.value[messages.value.length - 1]
  })

  /**
   * 添加用户消息
   */
  function addUserMessage(content) {
    return addMessage({ role: 'user', content })
  }

  /**
   * 添加助手消息
   */
  function addAssistantMessage(content, audioUrl = null) {
    return addMessage({ role: 'assistant', content, audioUrl })
  }

  /**
   * 添加正在输入的助手消息
   */
  function addTypingMessage() {
    return addMessage({ role: 'assistant', content: '', isTyping: true }, false)
  }

  function addMessage(payload, shouldSave = true) {
    const message = {
      id: generateMessageId(),
      timestamp: Date.now(),
      ...payload
    }
    messages.value.push(message)
    if (shouldSave) saveToStorage()
    return message
  }

  /**
   * 更新消息内容
   */
  function updateMessage(id, updates) {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      messages.value[index] = { ...messages.value[index], ...updates }
      saveToStorage()
    }
  }

  /**
   * 追加消息内容（用于流式输出）
   */
  function appendMessageContent(id, content) {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      messages.value[index].content += content
    }
  }

  /**
   * 完成打字效果
   */
  function finishTyping(id, audioUrl = null) {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      messages.value[index].isTyping = false
      if (audioUrl) {
        messages.value[index].audioUrl = audioUrl
      }
      saveToStorage()
    }
  }

  /**
   * 删除消息
   */
  function deleteMessage(id) {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      messages.value.splice(index, 1)
      saveToStorage()
    }
  }

  /**
   * 清空所有消息
   */
  function clearMessages() {
    messages.value = []
    sessionId.value = generateSessionId()
    saveToStorage()
  }

  /**
   * 保存到本地存储
   */
  function saveToStorage() {
    try {
      const data = {
        messages: messages.value,
        sessionId: sessionId.value,
        voiceSettings: voiceSettings.value,
        savedAt: Date.now()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (error) {
      console.error('保存聊天记录失败:', error)
    }
  }

  /**
   * 从本地存储加载
   */
  function loadFromStorage() {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      if (data) {
        const parsed = JSON.parse(data)
        messages.value = parsed.messages || []
        sessionId.value = parsed.sessionId || generateSessionId()
        if (parsed.voiceSettings) {
          voiceSettings.value = { ...DEFAULT_VOICE_SETTINGS, ...parsed.voiceSettings }
        }
        return true
      }
    } catch (error) {
      console.error('加载聊天记录失败:', error)
    }
    return false
  }

  /**
   * 设置加载状态
   */
  function setLoading(loading) {
    isLoading.value = loading
  }

  /**
   * 更新语音设置
   */
  function updateVoiceSettings(settings) {
    voiceSettings.value = { ...voiceSettings.value, ...settings }
    saveToStorage()
  }

  // 初始化时加载历史记录
  loadFromStorage()

  return {
    // 状态
    messages,
    sessionId,
    isLoading,
    currentInput,
    voiceSettings,
    
    // 计算属性
    hasMessages,
    lastMessage,
    
    // 方法
    addUserMessage,
    addAssistantMessage,
    addTypingMessage,
    updateMessage,
    appendMessageContent,
    finishTyping,
    deleteMessage,
    clearMessages,
    setLoading,
    updateVoiceSettings,
    loadFromStorage,
    saveToStorage
  }
})

/**
 * 生成会话ID
 */
function generateSessionId() {
  return 'session_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9)
}

/**
 * 生成消息ID
 */
function generateMessageId() {
  return 'msg_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 5)
}
