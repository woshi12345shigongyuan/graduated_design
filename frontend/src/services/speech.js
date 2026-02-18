/**
 * 语音识别服务 - 使用 Web Speech API
 */

class SpeechRecognitionService {
  constructor() {
    this.recognition = null
    this.isSupported = false
    this.isListening = false
    this.onResult = null
    this.onError = null
    this.onStart = null
    this.onEnd = null

    this._init()
  }

  _init() {
    // 检查浏览器支持
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      console.warn('当前浏览器不支持语音识别')
      this.isSupported = false
      return
    }

    this.isSupported = true
    this.recognition = new SpeechRecognition()

    // 配置语音识别
    this.recognition.lang = 'zh-CN'
    this.recognition.continuous = false
    this.recognition.interimResults = true
    this.recognition.maxAlternatives = 1

    // 绑定事件
    this.recognition.onstart = () => {
      this.isListening = true
      if (this.onStart) this.onStart()
    }

    this.recognition.onend = () => {
      this.isListening = false
      if (this.onEnd) this.onEnd()
    }

    this.recognition.onresult = (event) => {
      const results = event.results
      const lastResult = results[results.length - 1]
      
      if (lastResult.isFinal) {
        const transcript = lastResult[0].transcript
        const confidence = lastResult[0].confidence
        
        if (this.onResult) {
          this.onResult({
            text: transcript,
            confidence,
            isFinal: true
          })
        }
      } else {
        // 临时结果（用于实时显示）
        const transcript = lastResult[0].transcript
        
        if (this.onResult) {
          this.onResult({
            text: transcript,
            confidence: 0,
            isFinal: false
          })
        }
      }
    }

    this.recognition.onerror = (event) => {
      this.isListening = false
      console.error('语音识别错误:', event.error)
      
      if (this.onError) {
        let errorMessage = '语音识别出错'
        
        switch (event.error) {
          case 'no-speech':
            errorMessage = '未检测到语音，请重试'
            break
          case 'audio-capture':
            errorMessage = '无法访问麦克风'
            break
          case 'not-allowed':
            errorMessage = '麦克风权限被拒绝'
            break
          case 'network':
            errorMessage = '网络错误'
            break
          case 'aborted':
            errorMessage = '语音识别被中止'
            break
        }
        
        this.onError(errorMessage)
      }
    }
  }

  /**
   * 开始语音识别
   */
  start() {
    if (!this.isSupported) {
      if (this.onError) {
        this.onError('当前浏览器不支持语音识别，请使用 Chrome 浏览器')
      }
      return false
    }

    if (this.isListening) {
      return false
    }

    try {
      this.recognition.start()
      return true
    } catch (error) {
      console.error('启动语音识别失败:', error)
      return false
    }
  }

  /**
   * 停止语音识别
   */
  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop()
    }
  }

  /**
   * 中止语音识别
   */
  abort() {
    if (this.recognition) {
      this.recognition.abort()
      this.isListening = false
    }
  }

  /**
   * 检查麦克风权限
   */
  async checkPermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      return true
    } catch (error) {
      console.error('麦克风权限检查失败:', error)
      return false
    }
  }
}

// 单例实例
export const speechRecognition = new SpeechRecognitionService()

/**
 * 音频播放服务
 */
class AudioPlayerService {
  constructor() {
    this.audio = null
    this.isPlaying = false
    this.onPlay = null
    this.onPause = null
    this.onEnded = null
    this.onError = null
  }

  /**
   * 播放音频
   * @param {string} url - 音频 URL
   */
  play(url) {
    return new Promise((resolve, reject) => {
      // 停止当前播放
      this.stop()

      this.audio = new Audio(url)
      
      this.audio.onplay = () => {
        this.isPlaying = true
        if (this.onPlay) this.onPlay()
      }

      this.audio.onpause = () => {
        this.isPlaying = false
        if (this.onPause) this.onPause()
      }

      this.audio.onended = () => {
        this.isPlaying = false
        if (this.onEnded) this.onEnded()
        resolve()
      }

      this.audio.onerror = (error) => {
        this.isPlaying = false
        if (this.onError) this.onError(error)
        reject(error)
      }

      this.audio.play().catch(reject)
    })
  }

  /**
   * 暂停播放
   */
  pause() {
    if (this.audio && this.isPlaying) {
      this.audio.pause()
    }
  }

  /**
   * 继续播放
   */
  resume() {
    if (this.audio && !this.isPlaying) {
      this.audio.play()
    }
  }

  /**
   * 停止播放
   */
  stop() {
    if (this.audio) {
      this.audio.pause()
      this.audio.currentTime = 0
      this.audio = null
      this.isPlaying = false
    }
  }

  /**
   * 设置音量
   * @param {number} volume - 音量 (0-1)
   */
  setVolume(volume) {
    if (this.audio) {
      this.audio.volume = Math.max(0, Math.min(1, volume))
    }
  }
}

// 单例实例
export const audioPlayer = new AudioPlayerService()

export default {
  speechRecognition,
  audioPlayer
}
