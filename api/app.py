"""
尝尝咸淡 API - FastAPI 应用入口
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# 尽早加载 .env，保证数字人等服务能读到 VOLC_ACCESS_KEY_ID / VOLC_SECRET_ACCESS_KEY
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置 Hugging Face 镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from .routes import chat_router, tts_router, digital_human_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("尝尝咸淡 API 启动中...")
    
    # 确保音频目录存在
    audio_dir = PROJECT_ROOT / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    yield
    
    logger.info("尝尝咸淡 API 关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="尝尝咸淡 API",
    description="食谱 RAG 系统 API，支持智能问答和语音合成",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加 ngrok 警告跳过中间件
@app.middleware("https")
async def add_ngrok_skip_header(request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "1"
    return response

# 注册路由
app.include_router(chat_router)
app.include_router(tts_router)
app.include_router(digital_human_router)

# 挂载静态文件（音频、数字人视频）
audio_dir = PROJECT_ROOT / "audio"
if audio_dir.exists():
    app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")
video_dir = PROJECT_ROOT / "video"
video_dir.mkdir(exist_ok=True)
app.mount("/api/digital_human/video", StaticFiles(directory=str(video_dir)), name="digital_human_video")


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "尝尝咸淡 API",
        "version": "1.0.0",
        "description": "食谱 RAG 智能问答系统",
        "endpoints": {
            "chat": "/api/chat",
            "tts": "/api/tts",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    from .services.rag_service import rag_service
    
    return {
        "status": "healthy",
        "rag_ready": rag_service.is_ready
    }


if __name__ == "__main__":
    import uvicorn
    
    # 切换到项目目录
    os.chdir(str(PROJECT_ROOT))
    
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )