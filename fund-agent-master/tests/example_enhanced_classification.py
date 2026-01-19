#!/usr/bin/env python3
"""
增强意图分类器使用示例
演示如何使用知识图谱增强的意图分类功能
"""

from app.core.agents.enhanced_intent_classifier import (
    EnhancedIntentClassifier,
    classify_with_graph_knowledge,
    compare_intent_methods
)
import json


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 方式1: 使用便捷函数
    query = "医保退休怎么办理需要什么材料？"
    print(f"查询: {query}")

    result = classify_with_graph_knowledge(query)
    print("分类结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n" + "="*60 + "\n")


def example_advanced_usage():
    """高级使用示例"""
    print("=== 高级使用示例 ===")

    # 创建分类器实例
    classifier = EnhancedIntentClassifier(enable_graph_knowledge=True)

    test_cases = [
        {
            "query": "医保报销比例是多少？",
            "description": "待遇查询类查询"
        },
        {
            "query": "一次性补足缴费年限的具体流程",
            "description": "业务办理类查询"
        },
        {
            "query": "职工医保和居民医保有什么区别？",
            "description": "政策咨询类查询"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"案例 {i}: {case['description']}")
        print(f"查询: {case['query']}")

        result = classifier.classify_intent_with_graph(case['query'])

        print("关键信息:")
        print(f"  主要分类: {result.get('main_category')}")
        print(f"  置信度: {result.get('confidence', 0):.3f}")
        print(f"  使用图谱知识: {'是' if result.get('graph_knowledge_used') else '否'}")

        # 显示图谱统计
        graph_stats = result.get('graph_stats', {})
        if graph_stats.get('knowledge_available'):
            print(f"  图谱实体数: {graph_stats.get('entity_count')}")
            print(f"  图谱关系数: {graph_stats.get('relationship_count')}")

        print(f"  分类理由: {result.get('reasoning', '无')}")
        print("\n")


def example_performance_comparison():
    """性能对比示例"""
    print("=== 性能对比示例 ===")

    test_queries = [
        "医保退休办理流程",
        "医疗费用报销材料",
        "异地就医备案手续"
    ]

    for query in test_queries:
        print(f"查询: {query}")
        comparison = compare_intent_methods(query)

        # 提取关键信息
        traditional_time = comparison.get('traditional_method', {}).get('execution_time_ms', 0)
        enhanced_time = comparison.get('enhanced_method', {}).get('execution_time_ms', 0)
        enhanced_result = comparison.get('enhanced_method', {}).get('classification', {})

        print(f"传统方法: {traditional_time:.2f}ms")
        print(f"增强方法: {enhanced_time:.2f}ms")
        print(f"分类结果: {enhanced_result.get('main_category')} (置信度: {enhanced_result.get('confidence', 0):.2f})")
        print(f"图谱使用: {'是' if comparison.get('enhanced_method', {}).get('graph_knowledge_used') else '否'}")

        # 性能差异
        time_diff = enhanced_time - traditional_time
        if time_diff > 0:
            print(f"性能影响: 慢 {time_diff:.2f}ms ({(time_diff/traditional_time*100):.1f}%)")
        else:
            print(f"性能影响: 快 {abs(time_diff):.2f}ms ({(abs(time_diff)/traditional_time*100):.1f}%)")

        print("\n")


def example_error_handling():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    classifier = EnhancedIntentClassifier(enable_graph_knowledge=True)

    # 测试各种边界情况
    edge_cases = [
        "",  # 空查询
        "?????",  # 无意义查询
        "一个不相关的查询内容",  # 不相关查询
        "医保" * 100,  # 超长查询
    ]

    for i, query in enumerate(edge_cases, 1):
        print(f"边界测试 {i}: '{query[:30]}{'...' if len(query) > 30 else ''}'")

        try:
            result = classifier.classify_intent_with_graph(query)
            print(f"  处理成功: {result.get('main_category', '未知')}")
            print(f"  降级使用: {'是' if result.get('fallback_used') else '否'}")
        except Exception as e:
            print(f"  处理失败: {str(e)}")

        print()


def example_batch_classification():
    """批量分类示例"""
    print("=== 批量分类示例 ===")

    queries = [
        "医保报销需要什么材料？",
        "如何办理医保转移？",
        "医保退休的条件是什么？",
        "异地就医怎么报销？",
        "医保个人账户怎么查询？"
    ]

    print(f"批量处理 {len(queries)} 个查询:")

    # 创建分类器
    classifier = EnhancedIntentClassifier(enable_graph_knowledge=True)

    # 批量处理
    results = []
    for query in queries:
        try:
            result = classifier.classify_intent_with_graph(query)
            results.append({
                'query': query,
                'success': True,
                'result': result
            })
        except Exception as e:
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })

    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    print(f"处理成功: {success_count}/{len(queries)}")

    # 显示分类统计
    category_count = {}
    for result in results:
        if result['success']:
            category = result['result'].get('main_category', '未知')
            category_count[category] = category_count.get(category, 0) + 1

    print("分类分布:")
    for category, count in category_count.items():
        print(f"  {category}: {count}")

    # 显示详细结果
    print("\n详细结果:")
    for i, result in enumerate(results, 1):
        query = result['query']
        if result['success']:
            classification = result['result']
            print(f"{i}. {query}")
            print(f"   -> {classification.get('main_category')} "
                  f"(置信度: {classification.get('confidence', 0):.2f})")
        else:
            print(f"{i}. {query}")
            print(f"   -> 失败: {result['error']}")


if __name__ == "__main__":
    print("🚀 增强意图分类器使用示例\n")

    try:
        # 基本使用
        example_basic_usage()

        # 高级使用
        example_advanced_usage()

        # 性能对比
        example_performance_comparison()

        # 错误处理
        example_error_handling()

        # 批量处理
        example_batch_classification()

        print("✅ 所有示例执行完成！")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()