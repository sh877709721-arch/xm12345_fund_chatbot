#!/usr/bin/env python3
"""
测试增强的意图分类器功能
"""

import time
import json
import logging
from app.core.agents.enhanced_intent_classifier import (
    EnhancedIntentClassifier,
    classify_with_graph_knowledge,
    compare_intent_methods
)

# 设置日志级别
logging.basicConfig(level=logging.INFO)


def test_graph_knowledge_processing():
    """测试知识图谱数据处理功能"""
    print("=" * 80)
    print("测试知识图谱数据处理功能")
    print("=" * 80)

    # 模拟图谱数据（基于PDB输出）
    import pandas as pd

    # 模拟实体数据
    entities_data = {
        'id': ['2550', '2812', '14081', '2827', '1373', '1093', '1065', '1375'],
        'entity': [
            '一次性补足缴费年限', '医保退休办理', '办理补缴', '办理医保退休',
            '医保退休', '市医保中心集美管理部', '职工医保退休待遇', '补缴'
        ],
        'description': [
            '一次性补足缴费年限是指参保人员在申报职工医保退休待遇时，若其医疗保险缴费年限未达到规定要求，则需按规定一次性补缴相应的医疗保险费。',
            '参保人达到法定退休年龄后，为满足缴费年限条件以享受退休医保待遇而进行的申请和补缴流程',
            '指参保人员按规定一次性补足基本医疗保险缴费年限的行为',
            '办理医保退休是指达到法定退休年龄的参保人员申请享受退休人员基本医疗保险待遇的过程。',
            '医保退休是指参保人员在达到法定退休年龄并办结养老保险退休后，申报职工基本医疗保险退休待遇的资格确认过程。',
            '市医保中心集美管理部是厦门市医疗保障中心的分支机构，负责集美区的各项医保业务办理。',
            '职工医保退休待遇是指职工在达到法定退休年龄并满足规定的医疗保险缴费年限后，可以享受的医疗保障待遇。',
            '补缴是指参保人员在特定情况下对医疗保险费用进行事后缴纳的行为。'
        ],
        'number of relationships': [2, 1, 1, 12, 4, 4, 2, 2],
        'in_context': [True] * 8
    }

    # 模拟关系数据
    relationships_data = {
        'id': ['10089', '1824', '1881', '10071', '1638', '10088', '1860'],
        'source': ['厦门市', '厦门市', '参保人', '参保人员', '职工医保', '医保经办机构', '厦门市职工医疗保险实施细则'],
        'target': [
            '办理医保退休', '医保退休办理', '办理医保退休', '办理补缴',
            '一次性补足缴费年限', '办理医保退休', '办理医保退休'
        ],
        'description': [
            '厦门市是本医保退休办理政策的适用地理范围',
            '医保退休办理是厦门市参保人达到退休年龄后需要在本市满足特定缴费年限的重要事件',
            '参保人是办理医保退休这一事件的行为主体',
            '参保人员是执行补缴行为的主体',
            '一次性补足缴费年限是职工医保退休待遇申报中的关键步骤，用于满足累计缴费年限要求',
            '医保经办机构是具体受理并办理医保退休手续的窗口单位',
            '《厦门市职工医疗保险实施细则》中规定了办理医保退休的具体条件和流程'
        ],
        'weight': [1.0, 1.0, 1.0, 8.0, 1.0, 9.0, 8.0],
        'links': [2, 2, 1, 1, 1, 1, 1],
        'in_context': [True] * 7
    }

    entities_df = pd.DataFrame(entities_data)
    relationships_df = pd.DataFrame(relationships_data)

    # 测试结构化处理
    from app.core.rag.rag_search import structure_graph_knowledge, graph_to_llm_prompt

    test_query = "医保退休怎么办理"
    print(f"测试查询: {test_query}")
    print("-" * 60)

    # 结构化图谱知识
    structured_data = structure_graph_knowledge(entities_df, relationships_df, test_query)
    print(f"✅ 结构化处理完成")
    print(f"   实体数量: {len(structured_data['entities'])}")
    print(f"   关系数量: {len(structured_data['relationships'])}")
    print(f"   查询相关性: {bool(structured_data['entity_scores'])}")

    # 转换为LLM提示词
    llm_prompt = graph_to_llm_prompt(structured_data, max_entities=5, max_relationships=10)
    print(f"✅ LLM提示词生成完成，长度: {len(llm_prompt)} 字符")

    # 显示提示词预览
    print("\n📋 LLM提示词预览:")
    preview_lines = llm_prompt.split('\n')[:15]
    for line in preview_lines:
        print(f"   {line}")
    if len(llm_prompt.split('\n')) > 15:
        print(f"   ... (还有 {len(llm_prompt.split('\n')) - 15} 行)")


def test_enhanced_classification():
    """测试增强的意图分类"""
    print("\n" + "=" * 80)
    print("测试增强的意图分类功能")
    print("=" * 80)

    classifier = EnhancedIntentClassifier(enable_graph_knowledge=True)

    test_queries = [
        "医保退休怎么办理？",
        "医保报销比例是多少？",
        "一次性补足缴费年限的条件",
        "市医保中心集美管理部地址",
        "职工医保退休待遇包括什么？",
        "如何办理医保转移接续？"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 测试 {i}/{len(test_queries)}: {query}")
        print("-" * 60)

        try:
            start_time = time.time()
            result = classifier.classify_intent_with_graph(query, top_k=3)
            execution_time = time.time() - start_time

            print(f"✅ 分类完成，耗时: {execution_time*1000:.2f}ms")
            print(f"   主要分类: {result.get('main_category', 'N/A')}")
            print(f"   子分类: {result.get('sub_category', 'N/A')}")
            print(f"   置信度: {result.get('confidence', 0.0):.3f}")
            print(f"   图谱知识使用: {'✅' if result.get('graph_knowledge_used') else '❌'}")
            print(f"   搜索结果数量: {result.get('search_results_count', 0)}")

            # 图谱统计
            graph_stats = result.get('graph_stats', {})
            if graph_stats.get('knowledge_available'):
                print(f"   图谱实体数: {graph_stats.get('entity_count', 0)}")
                print(f"   图谱关系数: {graph_stats.get('relationship_count', 0)}")
                print(f"   上下文实体数: {graph_stats.get('in_context_entities', 0)}")

            # 理由
            reasoning = result.get('reasoning', '')
            if reasoning and len(reasoning) > 100:
                reasoning = reasoning[:100] + "..."
            print(f"   分类理由: {reasoning}")

        except Exception as e:
            print(f"❌ 分类失败: {e}")
            import traceback
            traceback.print_exc()


def test_method_comparison():
    """测试方法比较"""
    print("\n" + "=" * 80)
    print("测试传统方法 vs 增强方法对比")
    print("=" * 80)

    comparison_queries = [
        "医保退休办理流程",
        "补缴医保费用的条件",
        "职工医保退休待遇标准"
    ]

    for query in comparison_queries:
        print(f"\n🔍 查询: {query}")
        print("-" * 60)

        try:
            comparison_result = compare_intent_methods(query)

            # 传统方法
            traditional = comparison_result.get('traditional_method', {})
            print(f"📊 传统方法:")
            print(f"   搜索结果: {traditional.get('search_results_count', 0)}")
            print(f"   执行时间: {traditional.get('execution_time_ms', 0):.2f}ms")

            # 增强方法
            enhanced = comparison_result.get('enhanced_method', {})
            print(f"⚡ 增强方法:")
            classification = enhanced.get('classification', {})
            print(f"   主要分类: {classification.get('main_category', 'N/A')}")
            print(f"   置信度: {classification.get('confidence', 0.0):.3f}")
            print(f"   图谱使用: {'✅' if enhanced.get('graph_knowledge_used') else '❌'}")
            print(f"   执行时间: {enhanced.get('execution_time_ms', 0):.2f}ms")

            graph_stats = enhanced.get('graph_stats', {})
            if graph_stats.get('knowledge_available'):
                print(f"   图谱实体: {graph_stats.get('entity_count', 0)}")
                print(f"   图谱关系: {graph_stats.get('relationship_count', 0)}")

            # 性能对比
            perf_comp = comparison_result.get('performance_comparison', {})
            time_diff = perf_comp.get('time_difference_ms', 0)
            print(f"📈 性能对比:")
            print(f"   时间差异: {time_diff:+.2f}ms")
            if time_diff > 0:
                print(f"   增强方法慢 {abs(time_diff):.2f}ms")
            else:
                print(f"   增强方法快 {abs(time_diff):.2f}ms")

        except Exception as e:
            print(f"❌ 比较失败: {e}")


def test_fallback_mechanism():
    """测试降级机制"""
    print("\n" + "=" * 80)
    print("测试降级机制")
    print("=" * 80)

    # 创建禁用图谱的分类器
    classifier_no_graph = EnhancedIntentClassifier(enable_graph_knowledge=False)

    # 创建启用图谱的分类器
    classifier_with_graph = EnhancedIntentClassifier(enable_graph_knowledge=True)

    test_query = "医保报销比例是多少？"

    print(f"测试查询: {test_query}")
    print("-" * 60)

    # 测试无图谱版本
    print("📊 无图谱版本:")
    try:
        start_time = time.time()
        result_no_graph = classifier_no_graph.classify_intent_with_graph(test_query)
        time_no_graph = time.time() - start_time
        print(f"   执行时间: {time_no_graph*1000:.2f}ms")
        print(f"   主要分类: {result_no_graph.get('main_category', 'N/A')}")
        print(f"   图谱使用: {result_no_graph.get('graph_knowledge_used', False)}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

    # 测试有图谱版本
    print("\n⚡ 有图谱版本:")
    try:
        start_time = time.time()
        result_with_graph = classifier_with_graph.classify_intent_with_graph(test_query)
        time_with_graph = time.time() - start_time
        print(f"   执行时间: {time_with_graph*1000:.2f}ms")
        print(f"   主要分类: {result_with_graph.get('main_category', 'N/A')}")
        print(f"   图谱使用: {result_with_graph.get('graph_knowledge_used', False)}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试增强意图分类器")

    try:
        # 测试图谱数据处理
        test_graph_knowledge_processing()

        # 测试增强分类
        test_enhanced_classification()

        # 测试方法比较
        test_method_comparison()

        # 测试降级机制
        test_fallback_mechanism()

        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()