#!/usr/bin/env python3
"""
GraphRAG 流式路由测试脚本
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from app.router.graphrag import router
from app.core.graph.query_graphrag import rag_chatbot_stream

async def test_stream_function():
    """测试流式函数本身"""
    print("🧪 测试 GraphRAG 流式函数...")

    try:
        query = "请简单介绍一下人工智能"
        print(f"📝 查询问题: {query}")
        print("🔄 开始流式响应:")
        print("-" * 50)

        response_parts = []
        async for chunk in rag_chatbot_stream(query):
            if chunk:
                print(chunk, end='', flush=True)
                response_parts.append(chunk)

        print("\n" + "-" * 50)
        print("✅ 流式函数测试完成")
        return True

    except Exception as e:
        print(f"❌ 流式函数测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_router_import():
    """测试路由导入"""
    print("🧪 测试 GraphRAG 路由导入...")

    try:
        from app.router.graphrag import router, graphrag_stream_query, GraphRAGStreamQuery
        print("✅ 路由导入成功")

        # 检查路由端点
        for route in router.routes:
            if hasattr(route, 'path'):
                print(f"📍 端点: {route.methods} {route.path}")

        return True

    except Exception as e:
        print(f"❌ 路由导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始 GraphRAG 流式功能测试")
    print("=" * 60)

    # 测试路由导入
    router_ok = await test_router_import()
    print()

    # 测试流式函数（仅在路由导入成功时执行）
    if router_ok:
        function_ok = await test_stream_function()
        print()

        if function_ok:
            print("🎉 所有测试通过！流式 GraphRAG 功能正常工作")
            print("\n📋 可用的端点:")
            print("   POST /v1/graphrag/query      - 普通查询")
            print("   POST /v1/graphrag/query/stream - 流式查询")
            print("   GET  /v1/graphrag/health     - 健康检查")
        else:
            print("⚠️  部分测试失败，请检查 GraphRAG 配置")
    else:
        print("❌ 路由测试失败，无法继续测试流式功能")

if __name__ == "__main__":
    asyncio.run(main())