"""
RAG (Retrieval-Augmented Generation) 模块统一出口

这个模块提供了完整的RAG功能，包括：
- 查询处理和改写
- 多种搜索策略（QA、文档、混合搜索）
- 数据库操作和统计
- 评分算法（BM25、RRF等）
- 性能优化工具

使用方式：
from app.core.rag import SearchService, RAGEngine
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "MINGTAI"

# 数据库
from app.config.database import global_schema

# 核心服务类
from app.service.search_service import SearchService
from app.core.rag.database_operations import DatabaseOperations
from app.core.rag.scoring_algorithms import ScoringAlgorithms, SearchConfig


# 高级RAG引擎类
from typing import List, Dict, Optional
from app.config.llm_client import embedding_client
from app.core.embeddings_utils import get_text_embeddings


class RAGEngine:
    """
    统一的RAG引擎类，提供高级搜索和检索功能

    这个类整合了所有RAG相关的功能，提供一个简单易用的统一接口。
    """

    def __init__(self,
                 default_search_type: str = "hybrid",
                 enable_rerank: bool = True,
                 enable_fallback: bool = True):
        """
        初始化RAG引擎

        Args:
            default_search_type: 默认搜索类型 ('qa', 'doc', 'hybrid', 'bm25_vec')
            enable_rerank: 是否启用重排序
            enable_fallback: 是否启用容错机制
        """
        self.default_search_type = default_search_type
        self.enable_rerank = enable_rerank
        self.enable_fallback = enable_fallback

        # 初始化服务
        self.search_service = SearchService
        self.db_ops = DatabaseOperations
        self.scoring = ScoringAlgorithms

    def intent_detection(self, query):
        """
        意图识别
        :param self
        :param query: 原始提问
        """



    def search(self,
               query: str,
               search_type: Optional[str] = None,
               top_k: int = 10,
               **kwargs) -> List[Dict]:
        """
        统一搜索接口

        Args:
            query: 查询文本
            search_type: 搜索类型，如果不指定则使用默认类型
            top_k: 返回结果数量
            **kwargs: 其他搜索参数

        Returns:
            搜索结果列表
        """
        search_type = search_type or self.default_search_type

        if search_type == "qa":
            return self.search_service.qa_hybrid_search_vec_rff(query)

        elif search_type == "doc":
            if self.enable_fallback:
                return self.search_service.doc_hybrid_search_vec_rff_with_fallback(
                    query, top_k, self.enable_rerank
                )
            elif self.enable_rerank:
                return self.search_service.doc_hybrid_search_vec_rff_with_rerank(query, top_k)
            else:
                return self.search_service.doc_hybrid_search_vec_rff(query)

        elif search_type == "hybrid":
            return self.search_service.doc_hybrid_search_bm25_vec(query)

        elif search_type == "bm25_vec":
            return self.search_service.qa_hybrid_search_bm25_vec(query)

        elif search_type == "bm25":
            return self.search_service.bm25_search_pg(query, **kwargs)

        elif search_type == "vector":
            embedding = get_text_embeddings(embedding_client, query)
            return self.search_service.vector_search(embedding, **kwargs)

        else:
            raise ValueError(f"不支持的搜索类型: {search_type}")



    def get_stats(self) -> Dict:
        """获取RAG系统统计信息"""
        qa_stats = {
            "table": f"{global_schema}.indexed_knowledge",
            **dict(zip(
                ["avg_doc_length", "total_docs"],
                self.db_ops.get_collection_stats(f"{global_schema}.indexed_knowledge")
            ))
        }

        return {
            "qa_knowledge": qa_stats,
            "version": __version__,
            "default_search_type": self.default_search_type,
            "features": {
                "rerank": self.enable_rerank,
                "fallback": self.enable_fallback
            }
        }


# 便捷的搜索函数
def quick_search(query: str, search_type: str = "doc", top_k: int = 10) -> List[Dict]:
    """
    快速搜索函数，提供简单的搜索接口

    Args:
        query: 查询文本
        search_type: 搜索类型 ('qa', 'doc', 'hybrid')
        top_k: 返回结果数量

    Returns:
        搜索结果列表
    """
    engine = RAGEngine()
    return engine.search(query, search_type, top_k)


def qa_search(query: str) -> List[Dict]:
    """QA知识库搜索"""

    return SearchService.qa_hybrid_search_vec_rff(query)


def doc_search(query: str, top_k: int = 10, use_rerank: bool = True) -> List[Dict]:
    """文档知识库搜索"""
    if use_rerank:
        return SearchService.doc_hybrid_search_vec_rff_with_rerank(query, top_k)
    else:
        return SearchService.doc_hybrid_search_vec_rff(query)


# 导出公共接口
__all__ = [
    # 版本信息
    "__version__",

    # 核心服务类
    "SearchService",
    "DatabaseOperations",
    "ScoringAlgorithms",
    "SearchConfig",

    # 高级引擎类
    "RAGEngine",

    # 便捷函数
    "quick_search",
    "qa_search",
    "doc_search",
]