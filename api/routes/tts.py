"""
TTS 路由 - 处理语音合成相关的 API 请求
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ..services.tts_service import tts_service, AUDIO_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["语音合成"])


class TTSRequest(BaseModel):
    """TTS 请求模型"""
    text: str
    voice: Optional[str] = None
    rate: str = "+0%"
    pitch: str = "+0Hz"


class TTSResponse(BaseModel):
    """TTS 响应模型"""
    audio_url: str
    voice: str


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_text(request: TTSRequest):
    """
    将文本合成为语音
    
    Args:
        request: TTS 请求，包含文本和语音配置
        
    Returns:
        TTSResponse: 包含音频文件 URL
    """
    try:
        audio_path = await tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch
        )
        
        # 获取文件名
        filename = Path(audio_path).name
        
        return TTSResponse(
            audio_url=f"/api/tts/audio/{filename}",
            voice=request.voice or "xiaoxiao"
        )
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"TTS 合成失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    获取音频文件
    
    Args:
        filename: 音频文件名
        
    Returns:
        FileResponse: 音频文件
    """
    audio_path = AUDIO_DIR / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename
    )


@router.post("/stream")
async def stream_synthesize(request: TTSRequest):
    """
    流式语音合成（实时播放）
    
    Args:
        request: TTS 请求
        
    Returns:
        StreamingResponse: 音频流
    """
    async def generate():
        try:
            async for chunk in tts_service.synthesize_stream(
                text=request.text,
                voice=request.voice
            ):
                yield chunk
        except Exception as e:
            logger.error(f"流式 TTS 失败: {e}")
            raise
    
    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        }
    )


@router.get("/voices")
async def get_voices():
    """获取可用的语音列表"""
    voices = tts_service.get_available_voices()
    return {
        "voices": [
            {"id": key, "name": value, "description": _get_voice_description(key)}
            for key, value in voices.items()
        ]
    }


@router.delete("/cleanup")
async def cleanup_audio():
    """清理过期的音频文件"""
    try:
        tts_service.clean_old_audio(max_age_hours=1)
        return {"status": "success", "message": "过期音频已清理"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_voice_description(voice_id: str) -> str:
    """获取语音描述"""
    descriptions = {
        "xiaoxiao": "女声，温柔亲切",
        "xiaoyi": "女声，活泼可爱",
        "yunjian": "男声，沉稳大气",
        "yunxi": "男声，青年阳光",
        "yunxia": "女声，甜美可爱",
        "yunyang": "男声，新闻播音风格",
    }
    return descriptions.get(voice_id, "")
