import asyncio
from pathlib import Path
import pandas as pd
import graphrag.api as api
from graphrag.config.load_config import load_config
from .query_graphrag import rag_chatbot_global_search

PROJECT_DIRECTORY = "./app/core/graph/chatbot_zh"
graphrag_config = load_config(Path(PROJECT_DIRECTORY))


def rag_chatbot_sync(query: str) -> str:
    """
    同步版本的 GraphRAG 聊天机器人
    适用于需要在同步环境中调用的情况

    KISS原则：简单直接的同步包装器
    DRY原则：复用已实现的异步逻辑
    """
    # 检查是否已经在事件循环中
    try:
        loop = asyncio.get_running_loop()
        # 如果已经在事件循环中，使用 create_task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, rag_chatbot_global_search(query))
            return future.result()
    except RuntimeError:
        # 没有事件循环，直接使用 asyncio.run
        return asyncio.run(rag_chatbot_global_search(query))


def rag_chatbot_threaded(query: str) -> str:
    """
    线程版本：适用于已有事件循环但不想阻塞的情况
    YAGNI原则：只在真正需要时使用线程
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return executor.submit(asyncio.run, rag_chatbot_global_search(query)).result()