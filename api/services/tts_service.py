"""
TTS 服务 - 使用 edge-tts 实现免费语音合成
"""

import os
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 音频文件保存目录
AUDIO_DIR = Path(__file__).parent.parent.parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


class TTSService:
    """TTS 语音合成服务"""
    
    # 可用的中文语音
    VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 女声，温柔
        "xiaoyi": "zh-CN-XiaoyiNeural",          # 女声，活泼
        "yunjian": "zh-CN-YunjianNeural",        # 男声，沉稳
        "yunxi": "zh-CN-YunxiNeural",            # 男声，青年
        "yunxia": "zh-CN-YunxiaNeural",          # 女声，可爱
        "yunyang": "zh-CN-YunyangNeural",        # 男声，新闻播音
    }
    
    def __init__(self, default_voice: str = "xiaoxiao"):
        """
        初始化 TTS 服务
        
        Args:
            default_voice: 默认语音名称
        """
        self.default_voice = self.VOICES.get(default_voice, self.VOICES["xiaoxiao"])
        logger.info(f"TTS 服务初始化完成，默认语音: {self.default_voice}")
    
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        """
        将文本合成为语音
        
        Args:
            text: 要合成的文本
            voice: 语音名称（可选）
            rate: 语速调整，如 "+10%", "-20%"
            pitch: 音调调整，如 "+5Hz", "-10Hz"
            
        Returns:
            音频文件路径
        """
        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts 未安装，请运行: pip install edge-tts")
            raise ImportError("请先安装 edge-tts: pip install edge-tts")
        
        # 确定使用的语音
        voice_name = self.VOICES.get(voice, self.default_voice) if voice else self.default_voice
        
        # 生成唯一文件名
        audio_id = str(uuid.uuid4())[:8]
        audio_filename = f"{audio_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename
        
        try:
            # 创建 edge-tts 通信对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_name,
                rate=rate,
                pitch=pitch
            )
            
            # 保存音频文件
            await communicate.save(str(audio_path))
            
            logger.info(f"语音合成成功: {audio_filename}")
            return str(audio_path)
            
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            raise
    
    def synthesize_sync(
        self, 
        text: str, 
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> str:
        """
        同步版本的语音合成
        
        Args:
            text: 要合成的文本
            voice: 语音名称
            rate: 语速
            pitch: 音调
            
        Returns:
            音频文件路径
        """
        return asyncio.run(self.synthesize(text, voice, rate, pitch))
    
    async def synthesize_stream(self, text: str, voice: Optional[str] = None):
        """
        流式语音合成（用于实时播放）
        
        Args:
            text: 要合成的文本
            voice: 语音名称
            
        Yields:
            音频数据块
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError("请先安装 edge-tts: pip install edge-tts")
        
        voice_name = self.VOICES.get(voice, self.default_voice) if voice else self.default_voice
        
        communicate = edge_tts.Communicate(text=text, voice=voice_name)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    
    def clean_old_audio(self, max_age_hours: int = 1):
        """
        清理过期的音频文件
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        for audio_file in AUDIO_DIR.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    audio_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"删除音频文件失败: {audio_file}, 错误: {e}")
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个过期音频文件")
    
    @classmethod
    def get_available_voices(cls) -> dict:
        """获取可用的语音列表"""
        return cls.VOICES.copy()


# 全局 TTS 服务实例
tts_service = TTSService()
