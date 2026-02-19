/**
 * 虚拟数字人实时渲染 - Canvas 2D 每帧绘制
 * 完全免费、60fps、唇形/微表情/情感一体
 */
import { watch, onUnmounted } from 'vue'

const W = 320
const H = 380
const CENTER_X = W / 2
const FACE_TOP = 48
const FACE_H = 280
const FACE_W = 200

export function useAvatarRenderer(
  canvasRef,
  {
    mouthOpenness,
    emotion,
    status,
    isBlinking,
    headOffsetX,
    headOffsetY,
    imageLoaded,
    imageRef
  }
) {
  let rafId = null
  let img = null

  function drawFrame() {
    rafId = null
    const canvas = canvasRef.value
    if (!canvas) {
      rafId = requestAnimationFrame(drawFrame)
      return
    }
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      rafId = requestAnimationFrame(drawFrame)
      return
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.clearRect(0, 0, W, H)

    const ox = CENTER_X + (headOffsetX?.value ?? 0)
    const oy = FACE_TOP + FACE_H / 2 + (headOffsetY?.value ?? 0)
    ctx.save()
    ctx.translate(ox, oy)
    ctx.rotate(((headOffsetX?.value ?? 0) * 0.3 * Math.PI) / 180)
    ctx.translate(-ox, -oy)

    const faceLeft = (W - FACE_W) / 2
    const faceTop = FACE_TOP

    if (imageLoaded?.value && imageRef?.value?.complete && imageRef.value.naturalWidth) {
      ctx.save()
      ctx.beginPath()
      roundRect(ctx, faceLeft, faceTop, FACE_W, FACE_H, 24)
      ctx.clip()
      ctx.drawImage(imageRef.value, faceLeft, faceTop, FACE_W, FACE_H)
      ctx.restore()
    } else {
      drawProceduralFace(ctx, faceLeft, faceTop, FACE_W, FACE_H)
    }

    drawEyes(ctx, faceLeft, faceTop, FACE_W, FACE_H, isBlinking?.value)
    drawEyebrows(ctx, faceLeft, faceTop, FACE_W, FACE_H, emotion?.value ?? 'neutral')
    drawMouth(ctx, faceLeft, faceTop, FACE_W, FACE_H, mouthOpenness?.value ?? 0, emotion?.value ?? 'neutral')
    if (isBlinking?.value) {
      drawEyelids(ctx, faceLeft, faceTop, FACE_W, FACE_H)
    }

    ctx.restore()
    rafId = requestAnimationFrame(drawFrame)
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y)
    ctx.lineTo(x + w - r, y)
    ctx.quadraticCurveTo(x + w, y, x + w, y + r)
    ctx.lineTo(x + w, y + h - r)
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
    ctx.lineTo(x + r, y + h)
    ctx.quadraticCurveTo(x, y + h, x, y + h - r)
    ctx.lineTo(x, y + r)
    ctx.quadraticCurveTo(x, y, x + r, y)
  }

  function drawProceduralFace(ctx, x, y, w, h) {
    ctx.save()
    ctx.beginPath()
    roundRect(ctx, x, y, w, h, 24)
    ctx.clip()
    const g = ctx.createRadialGradient(
      x + w * 0.4, y + h * 0.25, 0,
      x + w / 2, y + h / 2, w * 0.8
    )
    g.addColorStop(0, '#fce8e0')
    g.addColorStop(0.5, '#f5d5c8')
    g.addColorStop(1, '#e8c4b4')
    ctx.fillStyle = g
    ctx.fillRect(x, y, w, h)
    ctx.restore()
    ctx.strokeStyle = 'rgba(0,0,0,0.06)'
    ctx.lineWidth = 1
    ctx.beginPath()
    roundRect(ctx, x, y, w, h, 24)
    ctx.stroke()
  }

  function drawEyes(ctx, x, y, w, h, blinking) {
    const cx = x + w / 2
    const eyeY = y + h * 0.38
    const eyeSpacing = w * 0.22
    const eyeW = 14
    const eyeH = blinking ? 2 : 12
    ctx.save()
    ctx.fillStyle = '#fff'
    ctx.strokeStyle = 'rgba(0,0,0,0.08)'
    ctx.lineWidth = 0.8
    for (const sign of [-1, 1]) {
      const ex = cx + sign * eyeSpacing
      ctx.beginPath()
      ctx.ellipse(ex, eyeY, eyeW, eyeH, 0, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
      if (!blinking) {
        ctx.fillStyle = '#2c1810'
        ctx.beginPath()
        ctx.arc(ex, eyeY, 5, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillStyle = 'rgba(255,255,255,0.9)'
        ctx.beginPath()
        ctx.arc(ex - 1.5, eyeY - 1.5, 1.5, 0, Math.PI * 2)
        ctx.fill()
      }
    }
    ctx.restore()
  }

  function drawEyelids(ctx, x, y, w, h) {
    const cx = x + w / 2
    const eyeY = y + h * 0.38
    const eyeSpacing = w * 0.22
    const lidW = 28
    const lidH = 18
    const g = ctx.createLinearGradient(0, eyeY - lidH, 0, eyeY + lidH)
    g.addColorStop(0, '#e8d5c8')
    g.addColorStop(1, '#d5c4b8')
    ctx.fillStyle = g
    for (const sign of [-1, 1]) {
      const ex = cx + sign * eyeSpacing
      ctx.beginPath()
      ctx.ellipse(ex, eyeY - 2, lidW, lidH, 0, Math.PI * 0.5, Math.PI * 1.5)
      ctx.fill()
    }
  }

  function drawEyebrows(ctx, x, y, w, h, emotion) {
    const cx = x + w / 2
    const by = y + h * 0.30
    const span = w * 0.2
    const lift = { neutral: 0, happy: -4, confused: -2, sorry: 1 }[emotion] ?? 0
    const tilt = { neutral: 0, happy: -0.1, confused: 0.08, sorry: 0.05 }[emotion] ?? 0
    ctx.save()
    ctx.strokeStyle = '#5c4a3a'
    ctx.lineWidth = 2.2
    ctx.lineCap = 'round'
    for (const sign of [-1, 1]) {
      ctx.beginPath()
      const x1 = cx + sign * (span * 0.6)
      const x2 = cx + sign * (span * 1.4)
      const y1 = by + lift + tilt * sign * 10
      const y2 = by + lift - tilt * sign * 10
      ctx.moveTo(x1, y1)
      ctx.quadraticCurveTo((x1 + x2) / 2, (y1 + y2) / 2 - 3 * sign, x2, y2)
      ctx.stroke()
    }
    ctx.restore()
  }

  function drawMouth(ctx, x, y, w, h, openness, emotion) {
    const cx = x + w / 2
    const my = y + h * 0.72
    const smile = { neutral: 0, happy: 1, confused: 0.2, sorry: 0.3 }[emotion] ?? 0
    const rx = Math.min(24, 18 + openness * 14)
    const ry = Math.max(2, 2 + openness * 12 * (1 - smile * 0.3))
    const dy = emotion === 'happy' ? 2 : emotion === 'sorry' ? -1 : 0
    ctx.save()
    const mg = ctx.createRadialGradient(cx, my, 0, cx, my, rx * 1.5)
    mg.addColorStop(0, '#a05a4a')
    mg.addColorStop(0.6, '#8b5a4a')
    mg.addColorStop(1, '#6b4035')
    ctx.fillStyle = mg
    ctx.strokeStyle = '#6b4035'
    ctx.lineWidth = 0.8
    ctx.beginPath()
    ctx.ellipse(cx, my + dy, rx, ry, 0, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
    ctx.restore()
  }

  function start() {
    if (canvasRef.value && !rafId) {
      rafId = requestAnimationFrame(drawFrame)
    }
  }

  function stop() {
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
  }

  watch(
    [canvasRef, imageRef],
    ([c, imgEl]) => {
      if (c && c.width !== W) {
        c.width = W
        c.height = H
      }
      if (imgEl && imgEl instanceof HTMLImageElement) img = imgEl
      if (c && !rafId) start()
    },
    { immediate: true }
  )

  onUnmounted(stop)

  return { start, stop }
}
