"""
嵌入相关的工具函数

这个模块包含文本嵌入相关的基础功能，避免循环导入问题
"""

import logging
from app.config.llm_client import embedding_client


def get_text_embeddings(client, text: str) -> list[float]:
    """
    获取文本的向量嵌入

    Args:
        client: 嵌入客户端
        text: 输入文本

    Returns:
        向量嵌入列表
    """
    try:
        response = client.embeddings.create(
            input=text,
            model='bge-m3'
        )
        #import pdb;pdb.set_trace()
        sorted_data = sorted(response.data, key=lambda x: x.index)
        embedding = sorted_data[0].embedding  # 直接取第一个（通常只有一个）
        return embedding
    except Exception as e:
        logging.error(f"获取文本嵌入失败: {e}")
        return []


def get_text_embeddings_default(text: str) -> list[float]:
    """
    获取文本的向量嵌入（使用默认客户端）

    Args:
        text: 输入文本

    Returns:
        向量嵌入列表
    """
    return get_text_embeddings(embedding_client, text)