"""
vector.py 的兼容性包装文件
保持与原始 vector.py 文件的接口兼容性，同时使用重构后的模块化代码

这个文件提供了一个兼容层，使得原有代码无需修改即可使用重构后的功能。
原有的 vector.py 文件保持不变，所有功能通过此包装文件调用新模块。

20260115 这个文件不久之后将会删除，注意使用
"""

from typing import List, Dict

# 从重构后的模块导入所有功能
from app.service.search_service import SearchService
from app.core.rag.database_operations import DatabaseOperations
from app.core.rag.scoring_algorithms import ScoringAlgorithms



# ================== 数据库操作功能 ==================

def execute_search(sql) -> List[Dict]:
    """兼容性包装：执行搜索查询"""
    return DatabaseOperations.execute_search(sql)


# ================== QA 搜索功能 ==================

def qa_response(query: str) -> List[Dict]:
    """兼容性包装：QA精确匹配搜索"""
    return SearchService.qa_response(query)


def qa_hybrid_search_vec_rff(query: str) -> List[Dict]:
    """兼容性包装：QA混合搜索"""
    return SearchService.qa_hybrid_search_vec_rff(query)


# ================== 文档搜索功能 ==================

def doc_hybrid_search_vec_rff(query: str) -> List[Dict]:
    """兼容性包装：文档混合搜索"""
    return SearchService.doc_hybrid_search_vec_rff(query)


def doc_hybrid_search_vec_rff_with_rerank(query: str, top_n: int = 10) -> List[Dict]:
    """兼容性包装：文档混合搜索+Rerank"""
    return SearchService.doc_hybrid_search_vec_rff_with_rerank(query, top_n)


def doc_hybrid_search_vec_rff_with_fallback(query: str, top_n: int = 10, use_rerank: bool = True) -> List[Dict]:
    """兼容性包装：文档混合搜索+Rerank（带容错）"""
    return SearchService.doc_hybrid_search_vec_rff_with_fallback(query, top_n, use_rerank)


# ================== BM25 搜索功能 ==================

def calculate_bm25_score(term_freq: int, doc_length: int, avg_doc_length: float,
                        k1: float = 1.2, b: float = 0.75) -> float:
    """兼容性包装：BM25评分计算"""
    return ScoringAlgorithms.calculate_bm25_score(term_freq, doc_length, avg_doc_length, k1, b)


def get_collection_stats(table_name: str = 'chatbot.indexed_knowledge') -> tuple:
    """兼容性包装：获取集合统计信息"""
    return DatabaseOperations.get_collection_stats(table_name)


def bm25_search_pg(query: str, table_name: str = 'chatbot.indexed_knowledge',
                   b: float = 0.75, top_k: int = 20) -> List[Dict]:
    """兼容性包装：BM25搜索"""
    return SearchService.bm25_search_pg(query, table_name, b, top_k)


def vector_search(query_embedding: List[float], table_name: str = 'chatbot.indexed_knowledge',
                 similarity_threshold: float = 0.0, top_k: int = 20) -> List[Dict]:
    """兼容性包装：向量搜索"""
    return SearchService.vector_search(query_embedding, table_name, similarity_threshold, top_k)


def merge_with_rrf(bm25_results: List[Dict], vec_results: List[Dict],
                  k: int = 60, weight_bm25: float = 0.4, weight_vec: float = 0.6) -> List[Dict]:
    """兼容性包装：RRF融合"""
    return ScoringAlgorithms.merge_with_rrf(bm25_results, vec_results, k, weight_bm25, weight_vec)


def doc_hybrid_search_bm25_vec(query: str, table_name: str = 'chatbot.indexed_knowledge') -> List[Dict]:
    """兼容性包装：文档BM25+向量混合搜索"""
    return SearchService.doc_hybrid_search_bm25_vec(query, table_name)


def qa_hybrid_search_bm25_vec(query: str, table_name: str = 'chatbot.indexed_knowledge') -> List[Dict]:
    """兼容性包装：QA BM25+向量混合搜索"""
    return SearchService.qa_hybrid_search_bm25_vec(query, table_name)






# ================== 导出兼容性信息 ==================

__all__ = [

    # 数据库操作
    'execute_search',

    # QA搜索
    'qa_response',
    'qa_hybrid_search_vec_rff',

    # 文档搜索
    'doc_hybrid_search_vec_rff',
    'doc_hybrid_search_vec_rff_with_rerank',
    'doc_hybrid_search_vec_rff_with_fallback',
    'doc_hybrid_search_with_query_rewrite_and_rerank',
    'qa_hybrid_search_with_query_rewrite_and_rerank',

    # BM25和向量搜索
    'calculate_bm25_score',
    'get_collection_stats',
    'bm25_search_pg',
    'vector_search',
    'merge_with_rrf',
    'doc_hybrid_search_bm25_vec',
    'qa_hybrid_search_bm25_vec',

    # 性能优化
    'create_indexes',
    'cache_optimization',
]

# 版本兼容性信息
COMPATIBILITY_VERSION = "1.0.0"
REFACTORED_MODULES = [
    'app.core.query_service',
    'app.core.search_service',
    'app.core.database_operations',
    'app.core.scoring_algorithms',
    'app.core.performance_utils'
]

def get_compatibility_info():
    """获取兼容性信息"""
    return {
        "version": COMPATIBILITY_VERSION,
        "description": "vector.py 兼容性包装层",
        "refactored_modules": REFACTORED_MODULES,
        "note": "原始 vector.py 文件已重构为多个模块化组件，此文件提供完全兼容的接口"
    }