#!/usr/bin/env python3
"""
IntentOptimizer集成增强分类器使用示例
展示如何在实际应用中使用知识图谱增强的意图分类
"""

from app.core.agents.intent_optimizer import IntentOptimizer, ClassificationConfig
import json


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 创建默认配置的优化器（自动启用增强分类器）
    optimizer = IntentOptimizer()

    query = "医保退休需要什么材料？"
    print(f"查询: {query}")

    # 使用集成分类，默认会使用增强分类器
    result = optimizer.ensemble_classification(
        query,
        strategies=['conservative', 'balanced', 'graph_enhanced'],
        include_confidence=True
    )

    print("分类结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def example_configuration_options():
    """配置选项示例"""
    print("\n=== 配置选项示例 ===")

    # 1. 完整增强配置
    config_full = ClassificationConfig(
        enable_enhanced_classifier=True,  # 启用增强分类器
        use_graph=True,                # 启用知识图谱
        max_graph_entities=15,          # 最大实体数量
        max_graph_relationships=20,      # 最大关系数量
        graph_knowledge_weight=0.8      # 图谱知识权重
    )

    # 2. 最小化配置
    config_minimal = ClassificationConfig(
        enable_enhanced_classifier=True,
        use_graph=False,               # 不使用知识图谱
        max_graph_entities=5,
        max_graph_relationships=8,
        graph_knowledge_weight=0.5
    )

    # 3. 禁用增强分类器
    config_disabled = ClassificationConfig(
        enable_enhanced_classifier=False,  # 禁用增强分类器
        use_graph=True                  # 仍可使用传统搜索
    )

    # 测试不同配置
    query = "医保报销比例是多少？"
    print(f"测试查询: {query}")

    configs = [
        ("完整增强配置", config_full),
        ("最小化配置", config_minimal),
        ("禁用增强", config_disabled)
    ]

    for name, config in configs:
        print(f"\n📋 {name}:")
        optimizer = IntentOptimizer(config)

        result = optimizer.ensemble_classification(query, include_confidence=True)
        print(f"   分类结果: {result.get('main_category')}")
        print(f"   置信度: {result.get('confidence', 0):.3f}")
        print(f"   分类器类型: {result.get('ensemble_classifier_type', 'unknown')}")

        if result.get('ensemble_classifier_type') == 'enhanced':
            graph_used = result.get('graph_knowledge_used', False)
            print(f"   图谱知识: {'使用' if graph_used else '未使用'}")


def example_strategy_combinations():
    """策略组合示例"""
    print("\n=== 策略组合示例 ===")

    query = "如何办理医保转移接续？"
    print(f"查询: {query}")

    # 创建增强分类器配置
    config = ClassificationConfig(
        enable_enhanced_classifier=True,
        use_graph=True,
        max_graph_entities=10
    )

    optimizer = IntentOptimizer(config)

    # 不同的策略组合
    strategy_sets = [
        {
            "name": "基础策略",
            "strategies": ['conservative', 'balanced']
        },
        {
            "name": "包含图谱策略",
            "strategies": ['conservative', 'balanced', 'graph_priority']
        },
        {
            "name": "图谱增强策略",
            "strategies": ['conservative', 'balanced', 'graph_enhanced']
        },
        {
            "name": "全覆盖策略",
            "strategies": ['conservative', 'balanced', 'graph_priority', 'graph_enhanced']
        }
    ]

    for strategy_info in strategy_sets:
        print(f"\n🎯 {strategy_info['name']}: {strategy_info['strategies']}")

        start_time = __import__('time').time()
        result = optimizer.ensemble_classification(
            query,
            strategies=strategy_info['strategies'],
            include_confidence=True
        )
        execution_time = __import__('time').time() - start_time

        print(f"   主要分类: {result.get('main_category')}")
        print(f"   置信度: {result.get('confidence', 0):.3f}")
        print(f"   执行时间: {execution_time*1000:.2f}ms")
        print(f"   使用策略: {result.get('ensemble_strategies', [])}")


def example_force_mode():
    """强制模式示例"""
    print("\n=== 强制模式示例 ===")

    query = "职工医保退休待遇标准"
    print(f"查询: {query}")

    # 创建默认配置
    config = ClassificationConfig(enable_enhanced_classifier=True, use_graph=True)
    optimizer = IntentOptimizer(config)

    print(f"默认配置（增强分类器）: {config.enable_enhanced_classifier}")

    # 1. 默认模式
    result_default = optimizer.ensemble_classification(query, include_confidence=True)
    print(f"\n📊 默认模式:")
    print(f"   分类器类型: {result_default.get('ensemble_classifier_type')}")
    print(f"   主要分类: {result_default.get('main_category')}")

    # 2. 强制传统模式
    result_traditional = optimizer.ensemble_classification(
        query,
        include_confidence=True,
        force_enhanced=False
    )
    print(f"\n🔄 强制传统模式:")
    print(f"   分类器类型: {result_traditional.get('ensemble_classifier_type')}")
    print(f"   主要分类: {result_traditional.get('main_category')}")

    # 3. 强制增强模式
    result_enhanced = optimizer.ensemble_classification(
        query,
        include_confidence=True,
        force_enhanced=True
    )
    print(f"\n⚡ 强制增强模式:")
    print(f"   分类器类型: {result_enhanced.get('ensemble_classifier_type')}")
    print(f"   主要分类: {result_enhanced.get('main_category')}")


def example_graph_vs_no_graph():
    """图谱知识对比示例"""
    print("\n=== 图谱知识对比示例 ===")

    test_cases = [
        {
            "query": "医保退休办理流程",
            "description": "应该有丰富的图谱知识"
        },
        {
            "query": "今天的天气如何",
            "description": "与医保无关，图谱知识少"
        },
        {
            "query": "补缴医保费用条件",
            "description": "图谱中应该有相关实体"
        }
    ]

    config = ClassificationConfig(
        enable_enhanced_classifier=True,
        use_graph=True,
        max_graph_entities=8,
        max_graph_relationships=12
    )

    optimizer = IntentOptimizer(config)

    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 案例 {i}: {case['description']}")
        print(f"查询: {case['query']}")

        result = optimizer.ensemble_classification(
            case['query'],
            strategies=['balanced', 'graph_enhanced'],
            include_confidence=True
        )

        print(f"主要分类: {result.get('main_category')}")
        print(f"置信度: {result.get('confidence', 0):.3f}")
        print(f"图谱知识使用: {'是' if result.get('graph_knowledge_used') else '否'}")

        # 详细分析
        confidence = result.get('confidence_analysis', {})
        graph_stats = confidence.get('graph_stats', {})
        if graph_stats.get('knowledge_available'):
            print(f"图谱统计:")
            print(f"  - 实体数量: {graph_stats.get('entity_count')}")
            print(f"  - 关系数量: {graph_stats.get('relationship_count')}")
            print(f"  - 上下文实体: {graph_stats.get('in_context_entities')}")


def example_batch_processing():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")

    queries = [
        "医保报销需要哪些材料？",
        "如何申请医保退休？",
        "医保转移接续流程",
        "一次性补足缴费年限标准",
        "职工医保和居民医保区别",
        "医保个人账户查询方法"
    ]

    # 配置批处理优化
    config = ClassificationConfig(
        enable_enhanced_classifier=True,
        use_graph=True,
        max_graph_entities=8,  # 限制实体数量以提高批量性能
        max_graph_relationships=12
    )

    optimizer = IntentOptimizer(config)

    print(f"批量处理 {len(queries)} 个查询:")
    print("-" * 60)

    results = []
    start_time = __import__('time').time()

    for i, query in enumerate(queries, 1):
        print(f"处理 {i}/{len(queries)}: {query[:30]}{'...' if len(query) > 30 else ''}")

        try:
            result = optimizer.ensemble_classification(
                query,
                strategies=['balanced', 'graph_enhanced'],
                include_confidence=True
            )
            results.append({
                'query': query,
                'success': True,
                'result': result,
                'main_category': result.get('main_category'),
                'confidence': result.get('confidence', 0),
                'graph_knowledge_used': result.get('graph_knowledge_used', False),
                'classifier_type': result.get('ensemble_classifier_type')
            })
        except Exception as e:
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })

    total_time = __import__('time').time() - start_time

    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    avg_time = total_time / len(queries) if queries else 0

    print(f"\n📊 批量处理统计:")
    print(f"   成功处理: {success_count}/{len(queries)}")
    print(f"   平均耗时: {avg_time*1000:.2f}ms")
    print(f"   总耗时: {total_time*1000:.2f}ms")

    # 分类统计
    category_count = {}
    graph_usage_count = 0

    for result in results:
        if result['success']:
            category = result['main_category']
            category_count[category] = category_count.get(category, 0) + 1

            if result['graph_knowledge_used']:
                graph_usage_count += 1

    print(f"\n📈 分类分布:")
    for category, count in category_count.items():
        print(f"   {category}: {count}")

    print(f"\n🔗 图谱知识使用:")
    print(f"   使用次数: {graph_usage_count}/{success_count}")
    print(f"   使用率: {graph_usage_count/success_count*100:.1f}%")


if __name__ == "__main__":
    print("🚀 IntentOptimizer集成增强分类器使用示例\n")

    try:
        example_basic_usage()
        example_configuration_options()
        example_strategy_combinations()
        example_force_mode()
        example_graph_vs_no_graph()
        example_batch_processing()

        print("\n" + "=" * 80)
        print("✅ 所有示例执行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()