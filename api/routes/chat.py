"""
聊天路由 - 处理聊天相关的 API 请求
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.rag_service import rag_service
from ..services.tts_service import tts_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["聊天"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: Optional[str] = None
    enable_tts: bool = True
    voice: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    answer: str
    audio_url: Optional[str] = None
    session_id: Optional[str] = None


class InitResponse(BaseModel):
    """初始化响应模型"""
    status: str
    message: str
    statistics: Optional[dict] = None


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
        result = rag_service.initialize()
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
    if not rag_service.is_ready:
        raise HTTPException(
            status_code=503, 
            detail="RAG 系统未初始化，请先调用 /api/chat/init"
        )
    
    try:
        # 获取 RAG 系统回答
        answer = rag_service.ask_question(request.message, stream=False)
        
        # 生成语音（如果启用）
        audio_url = None
        if request.enable_tts and answer:
            try:
                audio_path = await tts_service.synthesize(
                    text=answer,
                    voice=request.voice
                )
                # 返回相对 URL
                from pathlib import Path
                audio_filename = Path(audio_path).name
                audio_url = f"/api/tts/audio/{audio_filename}"
            except Exception as e:
                logger.warning(f"TTS 合成失败，但不影响文本回复: {e}")
        
        return ChatResponse(
            answer=answer,
            audio_url=audio_url,
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
    if not rag_service.is_ready:
        raise HTTPException(
            status_code=503, 
            detail="RAG 系统未初始化，请先调用 /api/chat/init"
        )
    
    async def generate():
        try:
            # 获取流式回答生成器
            stream_generator = rag_service.ask_question(request.message, stream=True)
            
            # 如果返回的是字符串（非流式），直接返回
            if isinstance(stream_generator, str):
                yield f"data: {stream_generator}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 流式输出
            for chunk in stream_generator:
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"流式处理失败: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"
    
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