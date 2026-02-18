"""
RAG 服务封装 - 将 RecipeRAGSystem 封装为可复用的服务
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Generator

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DEFAULT_CONFIG, RAGConfig
from rag_modules import (
    DataPreparationModule,
    IndexConstructionModule,
    RetrievalOptimizationModule,
    GenerationIntegrationModule
)

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 服务类 - 单例模式封装 RAG 系统"""
    
    _instance: Optional['RAGService'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: RAGConfig = None):
        """初始化 RAG 服务（仅首次调用时执行）"""
        if RAGService._initialized:
            return
            
        self.config = config or DEFAULT_CONFIG
        self.data_module = None
        self.index_module = None
        self.retrieval_module = None
        self.generation_module = None
        self._ready = False
        
        # 设置 Hugging Face 镜像
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        RAGService._initialized = True
        logger.info("RAG 服务实例已创建")
    
    @property
    def is_ready(self) -> bool:
        """检查服务是否已准备就绪"""
        return self._ready
    
    def initialize(self) -> Dict[str, Any]:
        """
        初始化 RAG 系统所有模块
        
        Returns:
            初始化状态信息
        """
        if self._ready:
            return {"status": "already_initialized", "message": "RAG 系统已经初始化"}
        
        try:
            logger.info("正在初始化 RAG 系统...")
            
            # 检查数据路径
            if not Path(self.config.data_path).exists():
                raise FileNotFoundError(f"数据路径不存在: {self.config.data_path}")
            
            # 1. 初始化数据准备模块
            logger.info("初始化数据准备模块...")
            self.data_module = DataPreparationModule(self.config.data_path)
            
            # 2. 初始化索引构建模块
            logger.info("初始化索引构建模块...")
            self.index_module = IndexConstructionModule(
                model_name=self.config.embedding_model,
                index_save_path=self.config.index_save_path
            )
            
            # 3. 初始化生成集成模块
            logger.info("初始化生成集成模块...")
            self.generation_module = GenerationIntegrationModule(
                model_name=self.config.llm_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                use_local_model=self.config.use_local_model,
                local_model_path=self.config.local_model_path,
                model_device=self.config.model_device
            )
            
            # 4. 构建知识库
            self._build_knowledge_base()
            
            self._ready = True
            logger.info("RAG 系统初始化完成")
            
            return {
                "status": "success",
                "message": "RAG 系统初始化成功",
                "statistics": self.data_module.get_statistics()
            }
            
        except Exception as e:
            logger.error(f"RAG 系统初始化失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _build_knowledge_base(self):
        """构建知识库"""
        logger.info("正在构建知识库...")
        
        # 尝试加载已保存的索引
        vectorstore = self.index_module.load_index()
        
        if vectorstore is not None:
            logger.info("成功加载已保存的向量索引")
            self.data_module.load_documents()
            chunks = self.data_module.chunk_documents()
        else:
            logger.info("未找到已保存的索引，开始构建新索引...")
            self.data_module.load_documents()
            chunks = self.data_module.chunk_documents()
            vectorstore = self.index_module.build_vector_index(chunks)
            self.index_module.save_index()
        
        # 初始化检索优化模块
        self.retrieval_module = RetrievalOptimizationModule(vectorstore, chunks)
        logger.info("知识库构建完成")
    
    def ask_question(self, question: str, stream: bool = False):
        """
        回答用户问题
        
        Args:
            question: 用户问题
            stream: 是否流式输出
            
        Returns:
            生成的回答或生成器
        """
        if not self._ready:
            raise RuntimeError("RAG 系统未初始化，请先调用 initialize()")
        
        logger.info(f"收到问题: {question}")
        
        # 1. 查询路由
        route_type = self.generation_module.query_router(question)
        logger.info(f"查询类型: {route_type}")
        
        # 2. 智能查询重写
        if route_type == 'list':
            rewritten_query = question
        else:
            rewritten_query = self.generation_module.query_rewrite(question)
        
        # 3. 检索相关文档
        filters = self._extract_filters_from_query(question)
        if filters:
            relevant_chunks = self.retrieval_module.metadata_filtered_search(
                rewritten_query, filters, top_k=self.config.top_k
            )
        else:
            relevant_chunks = self.retrieval_module.hybrid_search(
                rewritten_query, top_k=self.config.top_k
            )
        
        # 4. 检查是否找到相关内容
        if not relevant_chunks:
            return "抱歉，没有找到相关的食谱信息。请尝试其他菜品名称或关键词。"
        
        # 5. 获取父文档
        relevant_docs = self.data_module.get_parent_documents(relevant_chunks)
        
        # 6. 生成回答
        if route_type == 'list':
            return self.generation_module.generate_list_answer(question, relevant_docs)
        elif route_type == 'detail':
            if stream:
                return self.generation_module.generate_step_by_step_answer_stream(question, relevant_docs)
            else:
                return self.generation_module.generate_step_by_step_answer(question, relevant_docs)
        else:
            if stream:
                return self.generation_module.generate_basic_answer_stream(question, relevant_docs)
            else:
                return self.generation_module.generate_basic_answer(question, relevant_docs)
    
    def _extract_filters_from_query(self, query: str) -> dict:
        """从用户问题中提取元数据过滤条件"""
        filters = {}
        
        category_keywords = DataPreparationModule.get_supported_categories()
        for cat in category_keywords:
            if cat in query:
                filters['category'] = cat
                break
        
        difficulty_keywords = DataPreparationModule.get_supported_difficulties()
        for diff in sorted(difficulty_keywords, key=len, reverse=True):
            if diff in query:
                filters['difficulty'] = diff
                break
        
        return filters
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        if not self._ready:
            return {"status": "not_initialized"}
        
        return self.data_module.get_statistics()


# 全局单例实例
rag_service = RAGService()
