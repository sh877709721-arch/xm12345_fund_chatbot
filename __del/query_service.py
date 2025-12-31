"""
查询处理服务
负责查询改写、嵌入向量生成等查询相关的处理逻辑
"""

from typing import List
from app.config.llm_client import embedding_client


class QueryService:
    """查询处理服务类"""

    @staticmethod
    def get_query_embedding(query: str, model: str = 'bge-m3') -> List[float]:
        """
        获取查询文本的嵌入向量

        Args:
            query: 查询文本
            model: 嵌入模型名称，默认为 'bge-m3'

        Returns:
            嵌入向量列表
        """
        response = embedding_client.embeddings.create(
            input=query,
            model=model
        )
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return sorted_data[0].embedding