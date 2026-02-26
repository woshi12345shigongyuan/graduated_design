"""
即梦AI数字人快速模式 OmniHuman 1.0 服务（精简版：仅使用视频生成接口）
参考火山引擎/BytePlus 官方文档：
- 数字人快速模式-调用步骤2：视频生成 https://www.volcengine.com/docs/85621/1810471
- OmniHuman-1.0 Quick Mode API Document（BytePlus）

接口关键点：
- 只调用「视频生成」一步，直接传入 image_url（人物图片）和 audio_url（语音），由服务端完成主体识别与驱动。
- image_url / audio_url 必须是公网可访问的 URL，不能是 base64 本地数据。
"""

import os
import time
import logging
from typing import Optional
import socket
# 设置全局默认超时时间为120秒
socket.setdefaulttimeout(120)
logger = logging.getLogger(__name__)

# OmniHuman1.0 快速模式 - 视频生成 req_key（以官方文档为准）
REQ_KEY_VIDEO = "jimeng_realman_avatar_picture_omni_v2"

# 轮询配置
POLL_INTERVAL = 2
POLL_MAX_WAIT = 300  # 最多等 5 分钟

# 数字人接口 HTTP 超时（秒）。SDK 默认 30 秒，经代理时易超时，适当调大
VOLC_HTTP_TIMEOUT = int(os.getenv("VOLC_HTTP_TIMEOUT", "120"))


class OmniHumanService:
    """只负责：给定图片 URL + 音频 URL，生成数字人视频并返回 video_url。"""

    def __init__(self):
        self._client = None
        self._ak = os.getenv("VOLC_ACCESS_KEY_ID") or os.getenv("ACCESS_KEY_ID")
        self._sk = os.getenv("VOLC_SECRET_ACCESS_KEY") or os.getenv("SECRET_ACCESS_KEY")
        # PUBLIC_BASE_URL 用于把本地相对路径（/api/...）拼成公网 URL，如 https://your-domain.com
        self._public_base_url = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._ak or not self._sk:
            raise ValueError("请配置 VOLC_ACCESS_KEY_ID 与 VOLC_SECRET_ACCESS_KEY（或 ACCESS_KEY_ID / SECRET_ACCESS_KEY）")
        try:
            from volcengine.visual.VisualService import VisualService
        except ImportError:
            raise ImportError("请安装: pip install volcengine-python-sdk")
        self._client = VisualService()
        self._client.set_ak(self._ak)
        self._client.set_sk(self._sk)
        # SDK 默认 connection_timeout/socket_timeout=30，经代理(如 127.0.0.1:10810)时易读超时，此处调大
        if hasattr(self._client, "service_info") and self._client.service_info is not None:
            self._client.service_info.connection_timeout = VOLC_HTTP_TIMEOUT
            self._client.service_info.socket_timeout = VOLC_HTTP_TIMEOUT
            logger.info("数字人 Visual 客户端 HTTP 超时已设为 %s 秒", VOLC_HTTP_TIMEOUT)

        return self._client

    @property
    def is_available(self) -> bool:
        return bool(self._ak and self._sk)

    def _build_public_url(self, path_or_url: str) -> str:
        """
        将相对路径拼成公网 URL：
        - 若已是 http(s) URL，则直接返回；
        - 若是 /api/xxx，则依赖 PUBLIC_BASE_URL。
        """
        if not path_or_url:
            return path_or_url
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not self._public_base_url:
            raise ValueError(
                "调用数字人视频生成需要 PUBLIC_BASE_URL，例如：https://your-domain.com，"
                "以便把 /api/digital_human/avatar/image / /api/tts/audio/... 拼成公网 URL"
            )
        if not path_or_url.startswith("/"):
            path_or_url = "/" + path_or_url
        return f"{self._public_base_url}{path_or_url}"

    def create_digital_human_video(self, image_url: str, audio_url: str) -> Optional[str]:
        """
        直接调用视频生成：传入人物图片 URL 和语音 URL，轮询直到返回视频 URL 或失败。

        Args:
            image_url: 人物图片的 URL（本地上传的图片在后端暴露为 /api/digital_human/avatar/image，
                       本方法会自动拼成完整公网 URL）。
            audio_url: 语音文件 URL（如 /api/tts/audio/xxx.mp3）。

        Returns:
            公网可访问的视频 URL（由即梦/BytePlus 返回），或 None（失败/超时）。
        """
        client = self._get_client()

        form = {
            "req_key": REQ_KEY_VIDEO,
            "image_url": self._build_public_url(image_url),
            "audio_url": self._build_public_url(audio_url),
        }

        try:
            resp = client.cv_sync2async_submit_task(form)
            if not resp:
                logger.warning("数字人视频生成 submit 返回为空")
                return None

            data = resp.get("data") if isinstance(resp, dict) else None
            task_id = data.get("task_id") if isinstance(data, dict) else None
            if not task_id:
                logger.warning("数字人视频生成 submit 中没有 task_id: %s", resp)
                return None

            # 轮询任务结果
            for _ in range(POLL_MAX_WAIT // POLL_INTERVAL):
                time.sleep(POLL_INTERVAL)
                get_form = {"req_key": REQ_KEY_VIDEO, "task_id": task_id}
                result = client.cv_sync2async_get_result(get_form)
                if not result:
                    continue
                res_data = result.get("data") if isinstance(result, dict) else None
                if not isinstance(res_data, dict):
                    continue

                status = res_data.get("status")
                if status in ("success", "done"):
                    video_url = (
                        res_data.get("video_url")
                        or (res_data.get("result") or {}).get("video_url")
                        or res_data.get("url")
                    )
                    if video_url:
                        logger.info("数字人视频生成成功，video_url=%s", video_url)
                        return video_url
                    logger.warning("数字人接口成功但未返回 video_url: %s", result)
                    return None
                if status == "failed":
                    logger.warning("数字人视频生成失败: %s", result)
                    return None

            logger.warning("数字人视频生成超时（未在 %s 秒内完成）", POLL_MAX_WAIT)
            return None
        except Exception as e:
            logger.exception("调用数字人视频生成: %s", e)
            return None


omnihuman_service = OmniHumanService()
