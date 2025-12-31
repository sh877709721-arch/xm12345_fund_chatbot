#!/usr/bin/env python3
"""
测试IntentOptimizer集成增强分类器功能
验证知识图谱增强的意图分类是否正常工作
"""

import time
import logging
from app.core.agents.intent_optimizer import IntentOptimizer, ClassificationConfig

# 设置日志级别
logging.basicConfig(level=logging.INFO)


def test_optimizer_with_enhanced_classifier():
    """测试优化器使用增强分类器"""
    print("=" * 80)
    print("测试IntentOptimizer集成增强分类器")
    print("=" * 80)

    # 配置1: 启用增强分类器
    config_enhanced = ClassificationConfig(
        enable_enhanced_classifier=True,
        use_graph=True,
        max_graph_entities=10,
        max_graph_relationships=15
    )

    # 配置2: 禁用增强分类器
    config_traditional = ClassificationConfig(
        enable_enhanced_classifier=False,
        use_graph=True
    )

    test_queries = [
        "医保退休怎么办理？",
        "医保报销比例是多少？",
        "一次性补足缴费年限的条件",
        "市医保中心集美管理部地址",
        "职工医保退休待遇包括什么？"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 测试查询 {i}/{len(test_queries)}: {query}")
        print("-" * 60)

        # 测试增强分类器
        optimizer_enhanced = IntentOptimizer(config_enhanced)
        print("🚀 增强分类器测试:")
        start_time = time.time()
        try:
            result_enhanced = optimizer_enhanced.ensemble_classification(
                query,
                strategies=['conservative', 'balanced', 'graph_enhanced'],
                include_confidence=True,
                use_graph=True
            )
            enhanced_time = time.time() - start_time

            print(f"   ✅ 处理成功，耗时: {enhanced_time*1000:.2f}ms")
            print(f"   主要分类: {result_enhanced.get('main_category', 'N/A')}")
            print(f"   置信度: {result_enhanced.get('confidence', 0.0):.3f}")
            print(f"   分类器类型: {result_enhanced.get('ensemble_classifier_type', 'N/A')}")
            print(f"   搜索模式: {result_enhanced.get('ensemble_search_mode', 'N/A')}")
            print(f"   使用策略: {result_enhanced.get('ensemble_strategies', [])}")

            # 置信度分析
            confidence = result_enhanced.get('confidence_analysis', {})
            if confidence:
                print(f"   一致性分数: {confidence.get('consistency_score', 0.0):.3f}")
                print(f"   推荐等级: {confidence.get('recommendation', 'N/A')}")

        except Exception as e:
            print(f"   ❌ 处理失败: {e}")

        time.sleep(1)

        # 测试传统分类器
        optimizer_traditional = IntentOptimizer(config_traditional)
        print("📊 传统分类器测试:")
        start_time = time.time()
        try:
            result_traditional = optimizer_traditional.ensemble_classification(
                query,
                strategies=['conservative', 'balanced'],
                include_confidence=True,
                use_graph=True
            )
            traditional_time = time.time() - start_time

            print(f"   ✅ 处理成功，耗时: {traditional_time*1000:.2f}ms")
            print(f"   主要分类: {result_traditional.get('main_category', 'N/A')}")
            print(f"   置信度: {result_traditional.get('confidence', 0.0):.3f}")
            print(f"   分类器类型: {result_traditional.get('ensemble_classifier_type', 'N/A')}")

            # 性能对比
            if enhanced_time > 0 and traditional_time > 0:
                time_diff = enhanced_time - traditional_time
                print(f"   📈 性能差异: {time_diff*1000:+.1f}ms ({(time_diff/traditional_time)*100:+.1f}%)")

        except Exception as e:
            print(f"   ❌ 处理失败: {e}")


def test_force_enhanced_mode():
    """测试强制增强模式"""
    print("\n" + "=" * 80)
    print("测试强制增强模式")
    print("=" * 80)

    query = "医保转移接续需要什么材料？"
    print(f"查询: {query}")
    print("-" * 60)

    # 创建默认配置的优化器（应该启用增强分类器）
    optimizer = IntentOptimizer()

    print("🔧 默认配置（启用增强分类器）:")
    start_time = time.time()
    result_default = optimizer.ensemble_classification(query, include_confidence=True)
    default_time = time.time() - start_time

    print(f"   分类结果: {result_default.get('main_category', 'N/A')}")
    print(f"   分类器类型: {result_default.get('ensemble_classifier_type', 'N/A')}")
    print(f"   耗时: {default_time*1000:.2f}ms")

    # 测试强制传统模式
    print("\n🔄 强制传统模式:")
    start_time = time.time()
    result_traditional = optimizer.ensemble_classification(
        query,
        include_confidence=True,
        force_enhanced=False
    )
    traditional_time = time.time() - start_time

    print(f"   分类结果: {result_traditional.get('main_category', 'N/A')}")
    print(f"   分类器类型: {result_traditional.get('ensemble_classifier_type', 'N/A')}")
    print(f"   耗时: {traditional_time*1000:.2f}ms")

    # 测试强制增强模式
    print("\n⚡ 强制增强模式:")
    start_time = time.time()
    result_enhanced = optimizer.ensemble_classification(
        query,
        include_confidence=True,
        force_enhanced=True
    )
    enhanced_time = time.time() - start_time

    print(f"   分类结果: {result_enhanced.get('main_category', 'N/A')}")
    print(f"   分类器类型: {result_enhanced.get('ensemble_classifier_type', 'N/A')}")
    print(f"   耗时: {enhanced_time*1000:.2f}ms")


def test_graph_knowledge_impact():
    """测试图谱知识对分类的影响"""
    print("\n" + "=" * 80)
    print("测试图谱知识对分类的影响")
    print("=" * 80)

    test_cases = [
        {
            "query": "医保退休办理流程",
            "expected_knowledge": True,
            "description": "应该能从图谱获取相关知识"
        },
        {
            "query": "天气怎么样",
            "expected_knowledge": False,
            "description": "与医保无关，图谱知识少"
        },
        {
            "query": "一次性补足缴费年限",
            "expected_knowledge": True,
            "description": "图谱中应该有相关实体"
        }
    ]

    for case in test_cases:
        print(f"\n📋 {case['description']}")
        print(f"查询: {case['query']}")
        print("-" * 60)

        # 创建增强分类器配置
        config = ClassificationConfig(
            enable_enhanced_classifier=True,
            use_graph=True,
            max_graph_entities=8,
            max_graph_relationships=12
        )

        optimizer = IntentOptimizer(config)

        start_time = time.time()
        result = optimizer.ensemble_classification(
            case['query'],
            strategies=['balanced', 'graph_enhanced'],
            include_confidence=True
        )
        execution_time = time.time() - start_time

        print(f"✅ 分类完成，耗时: {execution_time*1000:.2f}ms")
        print(f"   主要分类: {result.get('main_category', 'N/A')}")
        print(f"   置信度: {result.get('confidence', 0.0):.3f}")
        print(f"   图谱使用: {'是' if result.get('graph_knowledge_used', False) else '否'}")

        # 检查图谱统计
        graph_stats = result.get('confidence_analysis', {}).get('graph_stats', {})
        if graph_stats.get('knowledge_available'):
            print(f"   图谱实体: {graph_stats.get('entity_count', 0)}")
            print(f"   图谱关系: {graph_stats.get('relationship_count', 0)}")
            print(f"   上下文实体: {graph_stats.get('in_context_entities', 0)}")
        else:
            print(f"   图谱状态: 不可用或出错")

        # 验证预期
        knowledge_used = result.get('graph_knowledge_used', False)
        if case['expected_knowledge'] and not knowledge_used:
            print("   ⚠️  警告: 预期应该使用图谱知识但未使用")
        elif not case['expected_knowledge'] and knowledge_used:
            print("   💡 信息: 未预期使用图谱知识但实际使用了")
        else:
            print(f"   ✅ 符合预期: 图谱知识使用情况正常")


def test_configuration_flexibility():
    """测试配置灵活性"""
    print("\n" + "=" * 80)
    print("测试配置灵活性")
    print("=" * 80)

    # 不同配置组合
    configs = [
        {
            "name": "完整增强配置",
            "config": ClassificationConfig(
                enable_enhanced_classifier=True,
                use_graph=True,
                max_graph_entities=15,
                max_graph_relationships=20,
                graph_knowledge_weight=0.8
            )
        },
        {
            "name": "最小配置",
            "config": ClassificationConfig(
                enable_enhanced_classifier=True,
                use_graph=False,
                max_graph_entities=5,
                max_graph_relationships=8,
                graph_knowledge_weight=0.5
            )
        },
        {
            "name": "禁用增强",
            "config": ClassificationConfig(
                enable_enhanced_classifier=False,
                use_graph=True
            )
        }
    ]

    test_query = "医保报销比例和条件"
    print(f"测试查询: {test_query}")
    print("-" * 60)

    for config_info in configs:
        print(f"\n🔧 配置: {config_info['name']}")
        optimizer = IntentOptimizer(config_info['config'])

        start_time = time.time()
        try:
            result = optimizer.ensemble_classification(
                test_query,
                include_confidence=True
            )
            execution_time = time.time() - start_time

            print(f"   ✅ 处理成功，耗时: {execution_time*1000:.2f}ms")
            print(f"   分类结果: {result.get('main_category', 'N/A')}")
            print(f"   置信度: {result.get('confidence', 0.0):.3f}")

            if result.get('ensemble_classifier_type') == 'enhanced':
                graph_used = result.get('graph_knowledge_used', False)
                print(f"   图谱知识: {'使用' if graph_used else '未使用'}")

                if config_info['config'].use_graph and not graph_used:
                    print(f"   ⚠️  配置启用图谱但未使用知识")
            else:
                print(f"   使用传统分类器")

        except Exception as e:
            print(f"   ❌ 处理失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试IntentOptimizer集成功能\n")

    try:
        test_optimizer_with_enhanced_classifier()
        test_force_enhanced_mode()
        test_graph_knowledge_impact()
        test_configuration_flexibility()

        print("\n" + "=" * 80)
        print("✅ 所有集成测试完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()