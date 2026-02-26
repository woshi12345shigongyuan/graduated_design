<template>
  <div class="chat-panel">
    <!-- 头部工具栏 -->
    <div class="chat-header">
      <div class="header-left">
        <span class="chat-title">对话</span>
        <span v-if="chatStore.hasMessages" class="message-count">
          {{ chatStore.messages.length }} 条消息
        </span>
      </div>
      <div class="header-right">
        <button 
          v-if="chatStore.hasMessages" 
          @click="confirmClear" 
          class="clear-btn"
          title="清空对话"
        >
          🗑️ 清空
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <MessageList ref="messageListRef" />

    <!-- 输入区域 -->
    <MessageInput @send="handleSend" />

    <!-- 清空确认对话框 -->
    <div v-if="showClearConfirm" class="confirm-overlay" @click="showClearConfirm = false">
      <div class="confirm-dialog" @click.stop>
        <p>确定要清空所有对话记录吗？</p>
        <div class="confirm-buttons">
          <button @click="showClearConfirm = false" class="cancel-btn">取消</button>
          <button @click="handleClear" class="confirm-btn">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { chatApi } from '../services/api'
import { audioPlayer } from '../services/speech'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'

const chatStore = useChatStore()
const messageListRef = ref(null)
const showClearConfirm = ref(false)

// 注入数字人状态控制
const avatarStatus = inject('avatarStatus')
const isSpeaking = inject('isSpeaking')
const currentEmotion = inject('currentEmotion')
const videoUrlToPlay = inject('videoUrlToPlay')
const onPlaybackEnded = inject('onPlaybackEnded')

// 确认清空
function confirmClear() {
  showClearConfirm.value = true
}

// 执行清空
function handleClear() {
  chatStore.clearMessages()
  showClearConfirm.value = false
}

// 发送消息
async function handleSend(message) {
  if (!message.trim() || chatStore.isLoading) return

  // 添加用户消息
  chatStore.addUserMessage(message)
  chatStore.setLoading(true)

  // 设置数字人为思考状态
  avatarStatus.value = 'thinking'
  currentEmotion.value = 'neutral'

  // 添加助手正在输入的占位消息
  const typingMessage = chatStore.addTypingMessage()

  // 滚动到底部
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollToBottom()
  }

  try {
    // 调用 API 获取回复
    const response = await chatApi.sendMessage(message, {
      enableTts: chatStore.voiceSettings.enabled,
      voice: chatStore.voiceSettings.voice,
      sessionId: chatStore.sessionId
    })

    // 更新消息内容
    chatStore.updateMessage(typingMessage.id, {
      content: response.answer,
      audioUrl: response.audio_url,
      isTyping: false
    })

    // 根据回复内容设置表情
    setEmotionFromAnswer(response.answer)

    // 设置数字人为说话状态
    avatarStatus.value = 'speaking'

    // 有数字人视频时在 Avatar 区播放视频（结束后由 Avatar 触发 onPlaybackEnded），否则仅播放音频
    if (response.video_url && chatStore.voiceSettings.autoPlay) {
      isSpeaking.value = true
      if (videoUrlToPlay) videoUrlToPlay.value = response.video_url
    } else if (response.audio_url && chatStore.voiceSettings.autoPlay) {
      try {
        isSpeaking.value = true
        audioPlayer.onEnded = () => {
          isSpeaking.value = false
          avatarStatus.value = 'idle'
          if (onPlaybackEnded) onPlaybackEnded()
        }
        await audioPlayer.play(response.audio_url)
      } catch (error) {
        console.error('播放语音失败:', error)
        isSpeaking.value = false
        avatarStatus.value = 'idle'
      }
    } else {
      avatarStatus.value = 'idle'
    }

  } catch (error) {
    console.error('发送消息失败:', error)
    
    // 更新为错误消息
    chatStore.updateMessage(typingMessage.id, {
      content: '抱歉，发生了错误，请稍后重试。',
      isTyping: false,
      isError: true
    })

    currentEmotion.value = 'sorry'
    avatarStatus.value = 'idle'
  } finally {
    chatStore.setLoading(false)
    
    // 滚动到底部
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollToBottom()
    }
  }
}

// 根据回复内容设置表情
function setEmotionFromAnswer(answer) {
  if (answer.includes('抱歉') || answer.includes('没有找到') || answer.includes('无法')) {
    currentEmotion.value = 'sorry'
  } else if (answer.includes('推荐') || answer.includes('美味') || answer.includes('好吃')) {
    currentEmotion.value = 'happy'
  } else if (answer.includes('？') || answer.includes('请问') || answer.includes('是否')) {
    currentEmotion.value = 'confused'
  } else {
    currentEmotion.value = 'neutral'
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 500px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-title {
  font-size: 1.2rem;
  font-weight: 600;
}

.message-count {
  font-size: 0.85rem;
  opacity: 0.8;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 10px;
  border-radius: 10px;
}

.clear-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 确认对话框 */
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-dialog {
  background: white;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
  min-width: 280px;
}

.confirm-dialog p {
  margin-bottom: 20px;
  font-size: 1.1rem;
  color: #333;
}

.confirm-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.cancel-btn, .confirm-btn {
  padding: 8px 24px;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: #f0f0f0;
  border: none;
  color: #666;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.confirm-btn {
  background: #e74c3c;
  border: none;
  color: white;
}

.confirm-btn:hover {
  background: #c0392b;
}
</style>
