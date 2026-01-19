#!/usr/bin/env python3
"""
测试意图优化器的知识图谱集成功能
"""

import time
import logging
from app.core.agents.intent_optimizer import IntentOptimizer, ClassificationConfig

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_graph_enhanced_classification():
    """测试知识图谱增强的分类功能"""

    test_queries = [
        "医保报销比例是多少？",
        "养老保险怎么申请？",
        "失业保险金领取条件",
        "医疗保险报销范围"
    ]

    print("=" * 80)
    print("意图优化器知识图谱集成测试")
    print("=" * 80)

    # 创建优化器实例
    config_with_graph = ClassificationConfig(
        vector_weight=0.4,
        bm25_weight=0.3,
        graph_weight=0.3,
        use_graph=True,
        top_k=5
    )

    config_without_graph = ClassificationConfig(
        vector_weight=0.6,
        bm25_weight=0.4,
        graph_weight=0.0,
        use_graph=False,
        top_k=5
    )

    optimizer_with_graph = IntentOptimizer(config_with_graph)
    optimizer_without_graph = IntentOptimizer(config_without_graph)

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 测试查询 {i}/4: {query}")
        print("-" * 60)

        try:
            # 测试1: 不使用知识图谱的集成分类
            print("📊 传统搜索集成分类:")
            start_time = time.time()
            result_traditional = optimizer_without_graph.ensemble_classification(
                query,
                strategies=['conservative', 'balanced'],
                include_confidence=True,
                use_graph=False
            )
            traditional_time = time.time() - start_time

            print(f"   耗时: {traditional_time*1000:.2f}ms")
            print(f"   主分类: {result_traditional.get('main_category', '未知')}")
            print(f"   置信度: {result_traditional.get('confidence', 0.0):.3f}")
            print(f"   搜索模式: {result_traditional.get('ensemble_search_mode', '未知')}")

            confidence_traditional = result_traditional.get('confidence_analysis', {})
            print(f"   一致性分数: {confidence_traditional.get('consistency_score', 0.0):.3f}")
            print(f"   推荐等级: {confidence_traditional.get('recommendation', '未知')}")

            time.sleep(1)

            # 测试2: 使用知识图谱的集成分类
            print("⚡ 知识图谱增强集成分类:")
            start_time = time.time()
            result_graph = optimizer_with_graph.ensemble_classification(
                query,
                strategies=['conservative', 'balanced', 'graph_priority'],
                include_confidence=True,
                use_graph=True
            )
            graph_time = time.time() - start_time

            print(f"   耗时: {graph_time*1000:.2f}ms")
            print(f"   主分类: {result_graph.get('main_category', '未知')}")
            print(f"   置信度: {result_graph.get('confidence', 0.0):.3f}")
            print(f"   搜索模式: {result_graph.get('ensemble_search_mode', '未知')}")

            confidence_graph = result_graph.get('confidence_analysis', {})
            print(f"   一致性分数: {confidence_graph.get('consistency_score', 0.0):.3f}")
            print(f"   推荐等级: {confidence_graph.get('recommendation', '未知')}")

            # 搜索优化信息
            optimization = confidence_graph.get('search_optimization', {})
            if optimization:
                print(f"   搜索优化: 节省{optimization.get('rerank_calls_saved', 0)}次rerank调用")

            # 性能对比
            if traditional_time > 0:
                time_diff = graph_time - traditional_time
                time_diff_pct = (time_diff / traditional_time) * 100
                print(f"   📈 性能对比: {time_diff_pct:+.1f}% ({time_diff*1000:+.1f}ms)")

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()

def test_confidence_analysis_with_graph():
    """测试带知识图谱的置信度分析"""
    print("\n" + "=" * 80)
    print("知识图谱置信度分析测试")
    print("=" * 80)

    query = "医保报销比例是多少？"

    # 创建两种配置的优化器
    optimizer = IntentOptimizer()

    print(f"\n🔍 测试查询: {query}")

    # 测试1: 传统模式的置信度分析
    print("\n📊 传统模式置信度分析:")
    start_time = time.time()
    confidence_traditional = optimizer.analyze_classification_confidence(
        query,
        fast_mode=True,
        use_ensemble_optimization=True,
        use_graph=False
    )
    traditional_time = time.time() - start_time

    print(f"   耗时: {traditional_time*1000:.2f}ms")
    print(f"   一致性分数: {confidence_traditional.get('consistency_score', 0.0):.3f}")
    print(f"   测试变体数: {confidence_traditional.get('variations_count', 0)}")
    print(f"   可靠性: {confidence_traditional.get('is_reliable', False)}")

    time.sleep(1)

    # 测试2: 知识图谱模式的置信度分析
    print("\n⚡ 知识图谱模式置信度分析:")
    start_time = time.time()
    confidence_graph = optimizer.analyze_classification_confidence(
        query,
        fast_mode=True,
        use_ensemble_optimization=True,
        use_graph=True
    )
    graph_time = time.time() - start_time

    print(f"   耗时: {graph_time*1000:.2f}ms")
    print(f"   一致性分数: {confidence_graph.get('consistency_score', 0.0):.3f}")
    print(f"   测试变体数: {confidence_graph.get('variations_count', 0)}")
    print(f"   可靠性: {confidence_graph.get('is_reliable', False)}")

    # 搜索优化信息
    optimization = confidence_graph.get('search_optimization', {})
    if optimization:
        print(f"   🚀 搜索优化: 节省{optimization.get('rerank_calls_saved', 0)}次rerank调用")
        print(f"   📈 性能提升: {optimization.get('performance_improvement', '0%')}")

def test_different_strategies():
    """测试不同的集成策略"""
    print("\n" + "=" * 80)
    print("集成策略对比测试")
    print("=" * 80)

    query = "医保报销比例是多少？"
    optimizer = IntentOptimizer()

    strategies_sets = [
        (['conservative', 'balanced'], "传统策略"),
        (['conservative', 'balanced', 'graph_priority'], "包含图谱策略"),
        (['graph_priority', 'balanced'], "图谱优先策略")
    ]

    for strategies, description in strategies_sets:
        print(f"\n📋 {description}: {strategies}")

        try:
            start_time = time.time()
            result = optimizer.ensemble_classification(
                query,
                strategies=strategies,
                include_confidence=True,
                use_graph=True
            )
            exec_time = time.time() - start_time

            print(f"   耗时: {exec_time*1000:.2f}ms")
            print(f"   主分类: {result.get('main_category', '未知')}")
            print(f"   投票数: {result.get('vote_count', 0)}/{result.get('total_votes', 0)}")
            print(f"   搜索上下文数: {result.get('search_results_count', 0)}")
            print(f"   使用的策略: {result.get('ensemble_strategies', [])}")

            confidence = result.get('confidence_analysis', {})
            if confidence:
                print(f"   置信度分析: {confidence.get('recommendation', '未知')}")

        except Exception as e:
            print(f"   ❌ 错误: {e}")

if __name__ == "__main__":
    test_graph_enhanced_classification()
    test_confidence_analysis_with_graph()
    test_different_strategies()