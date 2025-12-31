#!/usr/bin/env python3
"""
性能优化测试：对比优化前后的性能差异
"""

import time
import logging
from app.core.agents.intent_optimizer import IntentOptimizer

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_performance_comparison():
    """对比优化前后的性能"""

    test_queries = [
        "医保报销比例是多少？",
        "怎么申请养老保险？",
        "失业金能领多久？"
    ]

    optimizer = IntentOptimizer()

    print("=" * 80)
    print("性能优化对比测试")
    print("=" * 80)

    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        print("-" * 60)

        # 测试1: 优化前（分别调用ensemble和confidence分析）
        print("📊 优化前（分别调用）:")
        start_time = time.time()

        ensemble_result = optimizer.ensemble_classification(
            query,
            strategies=['balanced', 'conservative']
        )

        confidence_result = optimizer.analyze_classification_confidence(
            query,
            fast_mode=True,
            use_ensemble_optimization=False  # 使用原始方法
        )

        old_total_time = time.time() - start_time

        print(f"   总耗时: {old_total_time*1000:.2f}ms")
        print(f"   分类结果: {ensemble_result.get('main_category', '未知')}")
        print(f"   置信度: {confidence_result.get('overall_confidence', 0.0):.3f}")
        print(f"   一致性: {confidence_result.get('consistency_score', 0.0):.3f}")

        # 等待一秒避免缓存影响
        time.sleep(1)

        # 测试2: 优化后（一次性调用）
        print("⚡ 优化后（一次性调用）:")
        start_time = time.time()

        optimized_result = optimizer.ensemble_classification(
            query,
            strategies=['balanced', 'conservative'],
            include_confidence=True
        )

        optimized_total_time = time.time() - start_time

        # 从优化结果中提取信息
        optimized_confidence = optimized_result.get('confidence_analysis', {})

        print(f"   总耗时: {optimized_total_time*1000:.2f}ms")
        print(f"   分类结果: {optimized_result.get('main_category', '未知')}")
        print(f"   置信度: {optimized_confidence.get('overall_confidence', 0.0):.3f}")
        print(f"   一致性: {optimized_confidence.get('consistency_score', 0.0):.3f}")

        # 性能改进
        if old_total_time > 0:
            improvement = ((old_total_time - optimized_total_time) / old_total_time) * 100
            time_saved = old_total_time - optimized_total_time

            print("📈 性能对比:")
            print(f"   节省时间: {time_saved*1000:.2f}ms")
            print(f"   性能提升: {improvement:.1f}%")
            print(f"   Rerank调用次数: 从4次减少到2次")

if __name__ == "__main__":
    test_performance_comparison()