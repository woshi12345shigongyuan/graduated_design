"""
RAG系统配置文件
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class RAGConfig:
    """RAG系统配置类"""

    # 路径配置
    data_path: str = "dishes"
    index_save_path: str = "./vector_index"

    # 模型配置
    embedding_model: str =  "models/BAAI-bge-small-zh-v1.5"
    llm_model: str = "qwen3:8b"
    
    # 本地模型配置
    local_model_path: str = "models/qwen3-4b-instruct"
    use_local_model: bool = False
    model_device: str = "cuda"  # 可选: "cuda" 或 "cpu"

    # 检索配置
    top_k: int = 3

    # 生成配置
    temperature: float = 0.1
    max_tokens: int = 2048

    def __post_init__(self):
        """初始化后的处理"""
        pass
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGConfig':
        """从字典创建配置对象"""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data_path': self.data_path,
            'index_save_path': self.index_save_path,
            'embedding_model': self.embedding_model,
            'llm_model': self.llm_model,
            'top_k': self.top_k,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'local_model_path': self.local_model_path,
            'use_local_model': self.use_local_model,
            'model_device': self.model_device
        }

# 默认配置实例
DEFAULT_CONFIG = RAGConfig()