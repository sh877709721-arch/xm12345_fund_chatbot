#!/usr/bin/env python3
"""
测试新的知识图谱搜索封装功能
"""

import time
import logging
from app.core.rag.rag_search import RAGSearch

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_knowledge_graph_search():
    """测试知识图谱搜索功能"""

    test_queries = [
        "医保报销比例是多少？",
        "养老保险怎么申请？",
        "失业保险金领取条件",
        "医疗保险报销范围"
    ]

    rag_search = RAGSearch()

    print("=" * 80)
    print("知识图谱搜索功能测试")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 测试 {i}/4: {query}")
        print("-" * 60)

        try:
            # 测试1: 单独的知识图谱搜索
            print("📊 知识图谱搜索:")
            start_time = time.time()
            graph_results = rag_search._knowledge_graph_search(query, top_k=5, enable_rerank=True)
            graph_time = time.time() - start_time

            print(f"   耗时: {graph_time*1000:.2f}ms")
            print(f"   结果数量: {len(graph_results)}")

            for j, result in enumerate(graph_results[:3], 1):
                print(f"   {j}. 问题: {result.get('question', 'N/A')[:50]}...")
                print(f"      答案: {result.get('answer', 'N/A')[:100]}...")
                print(f"      来源: {result.get('source', 'N/A')}")
                print(f"      图谱分数: {result.get('graph_score', 0):.3f}")
                print(f"      Rerank分数: {result.get('rerank_score', 0):.3f}")
                print()

            # 等待一秒
            time.sleep(1)

            # 测试2: 综合搜索（包含知识图谱）
            print("⚡ 综合搜索（向量+BM25+知识图谱）:")
            start_time = time.time()
            comprehensive_results = rag_search.comprehensive_search_with_graph(
                query,
                vector_weight=0.4,
                bm25_weight=0.3,
                graph_weight=0.3,
                top_k=5,
                enable_rerank=True
            )
            comprehensive_time = time.time() - start_time

            print(f"   耗时: {comprehensive_time*1000:.2f}ms")
            print(f"   结果数量: {len(comprehensive_results)}")

            # 统计不同来源的结果数量
            source_count = {}
            for result in comprehensive_results:
                source = result.get('source', 'unknown')
                source_count[source] = source_count.get(source, 0) + 1

            print(f"   来源分布: {source_count}")

            for j, result in enumerate(comprehensive_results[:3], 1):
                print(f"   {j}. 问题: {result.get('question', 'N/A')[:50]}...")
                print(f"      来源: {result.get('source', 'N/A')}")
                print(f"      综合分数: {result.get('hybrid_score', 0) or result.get('graph_score', 0) or result.get('vec_score', 0) or result.get('bm25_score', 0):.3f}")
                print()

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()

def test_performance_comparison():
    """测试性能对比"""
    print("\n" + "=" * 80)
    print("性能对比测试")
    print("=" * 80)

    query = "医保报销比例是多少？"
    rag_search = RAGSearch()

    # 多次测试取平均值
    times = {
        'hybrid_search': [],
        'graph_search': [],
        'comprehensive_search': []
    }

    for i in range(3):
        print(f"\n第 {i+1} 轮测试:")

        # 混合搜索
        start_time = time.time()
        rag_search.hybrid_search_with_rerank(query, top_k=5)
        times['hybrid_search'].append(time.time() - start_time)

        # 知识图谱搜索
        start_time = time.time()
        rag_search._knowledge_graph_search(query, top_k=5, enable_rerank=True)
        times['graph_search'].append(time.time() - start_time)

        # 综合搜索
        start_time = time.time()
        rag_search.comprehensive_search_with_graph(query, top_k=5)
        times['comprehensive_search'].append(time.time() - start_time)

    # 计算平均时间
    avg_times = {method: sum(times[method]) / len(times[method]) * 1000
                for method in times}

    print("\n📈 平均耗时对比:")
    print(f"   混合搜索: {avg_times['hybrid_search']:.2f}ms")
    print(f"   知识图谱搜索: {avg_times['graph_search']:.2f}ms")
    print(f"   综合搜索: {avg_times['comprehensive_search']:.2f}ms")

if __name__ == "__main__":
    test_knowledge_graph_search()
    test_performance_comparison()