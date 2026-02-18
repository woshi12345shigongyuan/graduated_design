"""
API 路由模块
"""
from .chat import router as chat_router
from .tts import router as tts_router

__all__ = ['chat_router', 'tts_router']
