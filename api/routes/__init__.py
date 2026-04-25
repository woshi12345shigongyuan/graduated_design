"""
API 路由模块
"""
from .chat import router as chat_router
from .tts import router as tts_router
from .digital_human import router as digital_human_router
from .knowledge import router as knowledge_router

__all__ = ['chat_router', 'tts_router', 'digital_human_router', 'knowledge_router']
