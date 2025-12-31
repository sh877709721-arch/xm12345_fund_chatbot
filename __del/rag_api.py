"""
RAG API 统一入口

提供向后兼容的接口，同时支持新的模块化RAG功能
"""

# 从统一入口导入所有功能
from app.core.rag import *

# 保持与原始 vector.py 完全兼容
# 这样现有的导入语句可以无缝切换
def __getattr__(name):
    """动态属性访问，确保完全兼容性"""
    if hasattr(SearchService, name):
        return getattr(SearchService, name)
    elif hasattr(QueryService, name):
        return getattr(QueryService, name)
    elif hasattr(DatabaseOperations, name):
        return getattr(DatabaseOperations, name)
    elif hasattr(ScoringAlgorithms, name):
        return getattr(ScoringAlgorithms, name)
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")