"""
数字人基础图上传/删除与状态接口
"""

import base64
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/digital_human", tags=["数字人"])

# 当前使用的数字人基础图存储路径（单例，仅保留最新一张）- 使用绝对路径便于多进程一致
AVATAR_DIR = (Path(__file__).resolve().parent.parent.parent / "uploads" / "avatar")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
CURRENT_AVATAR_FILE = AVATAR_DIR / "current.jpg"
# 进程内缓存 base64，减少重复读文件；聊天请求若在其它 worker 会从文件重新读
_current_avatar_base64: Optional[str] = None


def get_current_avatar_path() -> Optional[Path]:
    p = CURRENT_AVATAR_FILE.resolve()
    if p.exists():
        return p
    return None


def get_current_avatar_base64() -> Optional[str]:
    global _current_avatar_base64
    path = get_current_avatar_path()
    if not path:
        _current_avatar_base64 = None
        return None
    try:
        # 始终以磁盘文件为准，避免上传在 A 进程、聊天在 B 进程时拿不到图
        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        _current_avatar_base64 = b64
        return b64
    except Exception as e:
        logger.warning("read avatar base64 error: %s", e)
        return None


def clear_current_avatar() -> None:
    global _current_avatar_base64
    _current_avatar_base64 = None
    if CURRENT_AVATAR_FILE.exists():
        try:
            CURRENT_AVATAR_FILE.unlink()
        except Exception as e:
            logger.warning("delete avatar file error: %s", e)


class AvatarStatusResponse(BaseModel):
    has_avatar: bool
    avatar_url: Optional[str] = None


@router.get("/avatar/status", response_model=AvatarStatusResponse)
async def get_avatar_status():
    """获取当前是否已设置数字人基础图"""
    path = get_current_avatar_path()
    if not path:
        return AvatarStatusResponse(has_avatar=False, avatar_url=None)
    return AvatarStatusResponse(
        has_avatar=True,
        avatar_url="/api/digital_human/avatar/image"
    )


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    """上传数字人基础图（单张，会覆盖）"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件（如 JPG、PNG）")
    try:
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")
        CURRENT_AVATAR_FILE.write_bytes(data)
        global _current_avatar_base64
        _current_avatar_base64 = base64.b64encode(data).decode("utf-8")
        return {"status": "success", "message": "上传成功", "has_avatar": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("upload_avatar error: %s", e)
        raise HTTPException(status_code=500, detail="上传失败")


@router.delete("/avatar")
async def delete_avatar():
    """删除当前数字人基础图（即不再使用数字人功能）"""
    clear_current_avatar()
    return {"status": "success", "message": "已删除", "has_avatar": False}


@router.get("/avatar/image")
async def get_avatar_image():
    """获取当前基础图（用于前端展示）"""
    from fastapi.responses import FileResponse
    path = get_current_avatar_path()
    if not path:
        raise HTTPException(status_code=404, detail="未设置数字人基础图")
    return FileResponse(path, media_type="image/jpeg")
