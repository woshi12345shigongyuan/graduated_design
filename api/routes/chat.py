"""
聊天路由 - 处理聊天相关的 API 请求
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from pydantic import BaseModel, Field

from ..services.rag_service import rag_service
from ..services.tts_service import tts_service
from ..services.omnihuman_service import omnihuman_service
from .digital_human import get_current_avatar_path

logger = logging.getLogger(__name__)

# 约 15 秒语音对应的中文字数（约 4 字/秒），用于数字人视频经济控制
MAX_TTS_CHARS_FOR_VIDEO = 60

router = APIRouter(prefix="/api/chat", tags=["聊天"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    enable_tts: bool = True
    voice: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    answer: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None  # 数字人视频 URL（有基础图且生成成功时返回）
    session_id: Optional[str] = None


class InitResponse(BaseModel):
    """初始化响应模型"""
    status: str
    message: str
    statistics: Optional[dict] = None


def _ensure_rag_ready() -> None:
    """确保 RAG 已初始化。"""
    if not rag_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="RAG 系统未初始化，请先调用 /api/chat/init"
        )


def _truncate_for_video(text: str) -> str:
    """限制数字人口播长度，控制外部服务调用成本。"""
    if len(text) <= MAX_TTS_CHARS_FOR_VIDEO:
        return text

    truncated = text[:MAX_TTS_CHARS_FOR_VIDEO].rstrip()
    if truncated and not truncated.endswith(("。", "！", "？")):
        truncated += "。"
    return truncated


async def _synthesize_audio_url(text: str, voice: Optional[str]) -> Optional[str]:
    """合成语音并返回可访问 URL；失败时仅记录日志。"""
    try:
        audio_path = await tts_service.synthesize(text=text, voice=voice)
        return f"/api/tts/audio/{Path(audio_path).name}"
    except Exception as e:
        logger.warning(f"TTS 合成失败，但不影响文本回复: {e}")
        return None


async def _create_video_url(audio_url: str) -> Optional[str]:
    """调用数字人服务生成视频；失败时保留音频回复。"""
    try:
        logger.info("正在调用即梦数字人 API 生成视频（使用上传基础图 + 语音 URL）...")
        video_url = await run_in_threadpool(
            omnihuman_service.create_digital_human_video,
            "/api/digital_human/avatar/image",
            audio_url,
        )
        if video_url:
            logger.info("数字人视频生成成功: %s", video_url)
        else:
            logger.warning("数字人 API 返回无视频，将仅播放音频")
        return video_url
    except Exception as e:
        logger.warning("数字人视频生成失败，将仅播放音频: %s", e)
        return None


async def _build_reply_media(answer: str, request: ChatRequest) -> tuple[Optional[str], Optional[str]]:
    """根据请求和数字人配置生成回复音频/视频。"""
    if not request.enable_tts or not answer:
        return None, None

    has_avatar = get_current_avatar_path() is not None
    can_create_video = has_avatar and omnihuman_service.is_available

    if not has_avatar:
        logger.info("数字人未调用: 未上传基础图或基础图已删除")
    elif not omnihuman_service.is_available:
        logger.warning("数字人未调用: 未配置火山引擎 AK/SK，请在 .env 中设置 VOLC_ACCESS_KEY_ID 与 VOLC_SECRET_ACCESS_KEY")

    text_for_tts = _truncate_for_video(answer) if can_create_video else answer
    audio_url = await _synthesize_audio_url(text_for_tts, request.voice)
    if not audio_url or not can_create_video:
        return audio_url, None

    return audio_url, await _create_video_url(audio_url)


@router.get("/status")
async def get_status():
    """获取 RAG 系统状态"""
    return {
        "ready": rag_service.is_ready,
        "statistics": rag_service.get_statistics() if rag_service.is_ready else None
    }


@router.post("/init", response_model=InitResponse)
async def initialize_system():
    """
    初始化 RAG 系统
    
    首次调用会加载模型和构建知识库，可能需要较长时间
    """
    try:
        result = await run_in_threadpool(rag_service.initialize)
        return InitResponse(**result)
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    发送消息并获取回复
    
    Args:
        request: 聊天请求，包含消息内容和配置选项
        
    Returns:
        ChatResponse: 包含回答文本和可选的音频URL
    """
    _ensure_rag_ready()
    
    try:
        # 获取 RAG 系统回答
        answer = await run_in_threadpool(rag_service.ask_question, request.message, False)
        audio_url, video_url = await _build_reply_media(answer, request)
        
        return ChatResponse(
            answer=answer,
            audio_url=audio_url,
            video_url=video_url,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"处理消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """
    流式发送消息（打字机效果）
    
    Args:
        request: 聊天请求
        
    Returns:
        StreamingResponse: 流式文本响应
    """
    _ensure_rag_ready()
    
    async def generate():
        # 关键：RAG 的 stream 生成器是同步阻塞的；若直接在 async 里迭代会卡住事件循环，
        # 导致其它请求（如数字人拉取图片/音频）无法响应。这里把生成放到后台线程，通过队列转发。
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def producer():
            try:
                stream_generator = rag_service.ask_question(request.message, stream=True)
                if isinstance(stream_generator, str):
                    loop.call_soon_threadsafe(queue.put_nowait, stream_generator)
                    loop.call_soon_threadsafe(queue.put_nowait, None)
                    return
                for chunk in stream_generator:
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
                loop.call_soon_threadsafe(queue.put_nowait, None)
            except Exception as e:
                logger.error(f"流式处理失败: {e}")
                loop.call_soon_threadsafe(queue.put_nowait, f"[ERROR] {str(e)}")
                loop.call_soon_threadsafe(queue.put_nowait, None)

        producer_task = asyncio.create_task(asyncio.to_thread(producer))
        try:
            while True:
                item = await queue.get()
                if item is None:
                    yield "data: [DONE]\n\n"
                    return
                yield f"data: {item}\n\n"
                if item.startswith("[ERROR]"):
                    yield "data: [DONE]\n\n"
                    return
        finally:
            # 尽量等待 producer 收尾，避免线程池任务泄露（不强制阻塞太久）
            if not producer_task.done():
                try:
                    await asyncio.wait_for(producer_task, timeout=1)
                except Exception:
                    pass
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/voices")
async def get_available_voices():
    """获取可用的语音列表"""
    return tts_service.get_available_voices()
