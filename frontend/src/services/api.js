/**
 * API 服务 - 与后端通信
 */

import axios from 'axios'

const DEFAULT_CHAT_TIMEOUT = 700000

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2分钟超时（RAG 系统响应可能较慢）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API 错误:', message, error)
    throw new Error(message)
  }
)

function parseSseDataBlock(block) {
  return block
    .split('\n')
    .filter(line => line.startsWith('data:'))
    .map(line => line.slice(5).trimStart())
    .join('\n')
}

/**
 * 聊天相关 API
 */
export const chatApi = {
  /**
   * 获取系统状态
   */
  async getStatus() {
    return api.get('/chat/status')
  },

  /**
   * 初始化 RAG 系统
   */
  async init() {
    return api.post('/chat/init')
  },

  /**
   * 发送消息
   * @param {string} message - 用户消息
   * @param {Object} options - 配置选项
   */
  async sendMessage(message, options = {}) {
    // 数字人视频生成 + 下载可能较耗时，这里为聊天发送单独设置更长超时时间
    const timeout = options.timeout ?? DEFAULT_CHAT_TIMEOUT
    return api.post(
      '/chat/send',
      {
        message,
        enable_tts: options.enableTts ?? true,
        voice: options.voice,
        session_id: options.sessionId
      },
      { timeout }
    )
  },

  /**
   * 流式发送消息
   * @param {string} message - 用户消息
   * @param {Function} onChunk - 接收数据块的回调
   */
  async sendMessageStream(message, onChunk) {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message, enable_tts: false })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `请求失败：${response.status}`)
    }

    if (!response.body) {
      throw new Error('当前浏览器不支持流式响应')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let fullText = ''
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() || ''

      for (const block of blocks) {
        const data = parseSseDataBlock(block)
        if (!data) continue
        if (data === '[DONE]') {
          return fullText
        }
        if (data.startsWith('[ERROR]')) {
          throw new Error(data.slice(8))
        }
        fullText += data
        onChunk(data)
      }
    }

    const rest = parseSseDataBlock(buffer)
    if (rest && rest !== '[DONE]') {
      if (rest.startsWith('[ERROR]')) {
        throw new Error(rest.slice(8))
      }
      fullText += rest
      onChunk(rest)
    }

    return fullText
  },

  /**
   * 获取可用语音列表
   */
  async getVoices() {
    return api.get('/chat/voices')
  }
}

/**
 * TTS 相关 API
 */
export const ttsApi = {
  /**
   * 合成语音
   * @param {string} text - 要合成的文本
   * @param {Object} options - 语音选项
   */
  async synthesize(text, options = {}) {
    return api.post('/tts/synthesize', {
      text,
      voice: options.voice,
      rate: options.rate || '+0%',
      pitch: options.pitch || '+0Hz'
    })
  },

  /**
   * 获取音频文件 URL
   * @param {string} filename - 音频文件名
   */
  getAudioUrl(filename) {
    return `/api/tts/audio/${filename}`
  },

  /**
   * 获取可用语音列表
   */
  async getVoices() {
    return api.get('/tts/voices')
  }
}

/**
 * 数字人基础图 API
 */
export const digitalHumanApi = {
  async getAvatarStatus() {
    return api.get('/digital_human/avatar/status')
  },
  async uploadAvatar(file) {
    const form = new FormData()
    form.append('file', file)
    return api.post('/digital_human/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  async deleteAvatar() {
    return api.delete('/digital_human/avatar')
  },
  getAvatarImageUrl() {
    return '/api/digital_human/avatar/image'
  }
}

/**
 * RAG 知识库文档管理 API
 */
export const knowledgeApi = {
  async listDocuments() {
    return api.get('/knowledge/documents')
  },
  async uploadDocument(file) {
    const form = new FormData()
    form.append('file', file)
    return api.post('/knowledge/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  async deleteDocument(filename) {
    return api.delete(`/knowledge/documents/${encodeURIComponent(filename)}`)
  }
}

export default api
