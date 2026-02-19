/**
 * 唇形同步 - 基于 Web Audio API 的振幅驱动口型开合
 * 用于真人化数字人嘴部与语音同步，过渡自然、完全免费
 */
import { ref, watch, onUnmounted } from 'vue'

const SMOOTHING = 0.35
const SENSITIVITY = 1.8
const MIN_OPEN = 0.02
const MAX_OPEN = 0.95

/**
 * @param {import('vue').Ref<boolean>} isSpeaking
 * @param {() => HTMLAudioElement | null} getAudioElement - 返回当前播放的音频元素
 * @returns {{ mouthOpenness: import('vue').Ref<number> }}
 */
export function useLipSync(isSpeaking, getAudioElement) {
  const mouthOpenness = ref(0)
  let audioContext = null
  let analyser = null
  let source = null
  let rafId = null
  let smoothed = 0

  function connectAudio(audioEl) {
    if (!audioEl || audioContext) return
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)()
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = SMOOTHING
      source = audioContext.createMediaElementSource(audioEl)
      source.connect(analyser)
      analyser.connect(audioContext.destination)
    } catch (e) {
      console.warn('LipSync: AudioContext 不可用', e)
    }
  }

  function getAmplitude() {
    if (!analyser || !audioContext) return 0
    const data = new Uint8Array(analyser.frequencyBinCount)
    analyser.getByteFrequencyData(data)
    let sum = 0
    for (let i = 0; i < data.length; i++) sum += data[i]
    const avg = sum / data.length
    return Math.min(1, (avg / 128) * SENSITIVITY)
  }

  function tick() {
    rafId = null
    if (!isSpeaking.value) {
      mouthOpenness.value = 0
      return
    }
    // 播放可能晚于 isSpeaking 置 true，每帧尝试连接
    if (!analyser) {
      const el = typeof getAudioElement === 'function' ? getAudioElement() : null
      if (el) connectAudio(el)
      mouthOpenness.value = MIN_OPEN
      rafId = requestAnimationFrame(tick)
      return
    }
    const raw = getAmplitude()
    smoothed = smoothed * 0.6 + raw * 0.4
    const open = MIN_OPEN + smoothed * (MAX_OPEN - MIN_OPEN)
    mouthOpenness.value = Math.min(MAX_OPEN, Math.max(MIN_OPEN, open))
    rafId = requestAnimationFrame(tick)
  }

  watch(
    isSpeaking,
    (speaking) => {
      if (speaking) {
        smoothed = 0
        if (!rafId) rafId = requestAnimationFrame(tick)
      } else {
        mouthOpenness.value = 0
        smoothed = 0
        if (rafId) {
          cancelAnimationFrame(rafId)
          rafId = null
        }
      }
    },
    { immediate: true }
  )

  onUnmounted(() => {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = null
    if (source && audioContext) {
      try {
        source.disconnect()
      } catch (_) {}
    }
    analyser = null
    source = null
    audioContext = null
  })

  return { mouthOpenness }
}
