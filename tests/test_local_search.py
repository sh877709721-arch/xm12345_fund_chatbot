#!/usr/bin/env python3
"""
测试 GraphRAG local_search 功能的简单脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

from app.core.graph.query_graphrag import (
    rag_chatbot_local_search,
    rag_chatbot_local_search_stream,
    rag_chatbot_global_search,
    rag_chatbot_stream
)

async def test_local_search():
    """测试本地搜索功能"""
    try:
        query = "什么是人工智能？"
        print(f"测试查询: {query}")

        # 测试本地搜索
        print("\n=== 测试本地搜索 ===")
        response = await rag_chatbot_local_search(query)
        print(f"本地搜索响应: {response[:100]}...")

        # 测试本地搜索流式
        print("\n=== 测试本地搜索流式 ===")
        count = 0
        async for chunk in rag_chatbot_local_search_stream(query):
            print(f"块 {count}: {chunk[:50]}...")
            count += 1
            if count >= 3:  # 只显示前3个块作为演示
                break

        print("\n✅ 本地搜索功能测试成功！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

    return True

if __name__ == "__main__":
    asyncio.run(test_local_search())