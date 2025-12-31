#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保领域意图判断测试用例
"""
from app.core.rule.domain_rule import match_domain_intent, batch_match_domain_intent, get_domain_intent_statistics, get_intent_matcher


def test_intent_matching():
    """测试意图匹配功能"""
    test_cases = [
        # 职工基本医疗保险测试
        ("职工医疗保险怎么缴费", "职工基本医疗保险", "参保缴费", "缴费标准"),
        ("单位职工的参保条件是什么", "职工基本医疗保险", "参保缴费", "参保对象"),
        ("医保缴费基数是多少", "职工基本医疗保险", "参保缴费", "缴费标准"),
        ("医疗保险费用怎么交", "职工基本医疗保险", "参保缴费", "参保缴费方式"),
        ("重复参保了怎么办", "职工基本医疗保险", "参保缴费", "重复参保处理"),
        ("医保退费流程", "职工基本医疗保险", "参保缴费", "退费"),

        # 医疗待遇测试
        ("医保什么时候生效", "职工基本医疗保险", "医疗待遇", "待遇生效时间"),
        ("医保断缴了还能用吗", "职工基本医疗保险", "医疗待遇", "连续参保机制"),
        ("个人账户返钱比例", "职工基本医疗保险", "医疗待遇", "医保账户划拨"),
        ("大病保险报销比例", "职工基本医疗保险", "医疗待遇", "大病医保"),
        ("困难群众医疗救助", "职工基本医疗保险", "医疗待遇", "医疗救助"),
        ("医保报销标准", "职工基本医疗保险", "医疗待遇", "待遇标准"),

        # 办事指南测试
        ("医疗费用怎么报销", "职工基本医疗保险", "办事指南", "医疗费用报销办理"),
        ("异地就医需要备案吗", "职工基本医疗保险", "办事指南", "异地就医备案办理"),
        ("家庭共济账户怎么开通", "职工基本医疗保险", "办事指南", "家庭共济办理"),
        ("医保退休要缴多少年", "职工基本医疗保险", "办事指南", "医保退休办理"),
        ("医保账户一次性支取", "职工基本医疗保险", "办事指南", "个人账户一次性支取办理"),

        # 城乡居民医疗保险测试
        ("居民医保缴费标准", "城乡居民医疗保险", "参保缴费", "缴费标准"),
        ("学生怎么参保医保", "城乡居民医疗保险", "参保缴费", "参保对象"),
        ("城乡医保怎么缴费", "城乡居民医疗保险", "参保缴费", "参保缴费方式"),
        ("居民医保等待期", "城乡居民医疗保险", "医疗待遇", "待遇生效时间"),
        ("居民医保报销比例", "城乡居民医疗保险", "医疗待遇", "待遇标准"),
        ("居民医保怎么报销", "城乡居民医疗保险", "办事指南", "医疗费用报销办理"),

        # 生育保险测试
        ("生育保险参保条件", "生育保险", "参保缴费", "参保对象"),
        ("生育保险缴费比例", "生育保险", "参保缴费", "缴费标准"),
        ("生育津贴怎么申请", "生育保险", "办事指南", "生育津贴办理"),
        ("产假工资标准", "生育保险", "生育待遇", "生育津贴待遇"),
        ("男方配偶生育费用报销", "生育保险", "办事指南", "男职工未就业配偶生育医疗费用办理"),
        ("产检费用报销", "生育保险", "生育待遇", "其他待遇"),

        # 其他医药政策测试
        ("医保药品目录查询", "其他医药政策", "药品（含项目、耗材）政策", "药品目录"),
        ("甲类乙类药品区别", "其他医药政策", "药品（含项目、耗材）政策", "药品目录"),
        ("医保诊疗项目目录", "其他医药政策", "药品（含项目、耗材）政策", "医疗服务项目目录"),
        ("医用耗材报销", "其他医药政策", "药品（含项目、耗材）政策", "医用耗材目录"),
        ("惠厦保怎么买", "其他医药政策", "补充医疗保险", "惠厦保"),
        ("长期护理保险申请", "其他医药政策", "长期护理险政策", "长期护理险政策"),

        # 边界情况测试
        ("今天天气不错", None, None, None),
        ("我想了解一下医保政策", None, None, None),
        ("", None, None, None),
    ]

    print("=== 医保意图匹配测试 ===")
    correct_count = 0
    total_count = len(test_cases)

    for text, expected_domain, expected_category, expected_intent in test_cases:
        results = match_domain_intent(text, top_k=1)

        if results:
            match = results[0]
            domain_match = match.domain == expected_domain if expected_domain else True
            category_match = match.category == expected_category if expected_category else True
            intent_match = match.intent == expected_intent if expected_intent else True

            if domain_match and category_match and intent_match:
                status = "✓"
                correct_count += 1
            else:
                status = "✗"

            print(f"{status} 文本: '{text}'")
            print(f"  预期: {expected_domain}/{expected_category}/{expected_intent}")
            print(f"  实际: {match.domain}/{match.category}/{match.intent} (置信度: {match.confidence:.2f})")
        else:
            if expected_domain is None:
                status = "✓"
                correct_count += 1
            else:
                status = "✗"
            print(f"{status} 文本: '{text}'")
            print(f"  预期: {expected_domain}/{expected_category}/{expected_intent}")
            print(f"  实际: 未匹配到意图")
        print()

    accuracy = correct_count / total_count * 100
    print(f"总体准确率: {accuracy:.1f}% ({correct_count}/{total_count})")
    return accuracy


def test_batch_matching():
    """测试批量匹配"""
    print("\n=== 批量匹配测试 ===")

    test_texts = [
        "职工医保缴费基数是多少",
        "生育津贴申请流程",
        "居民医保报销比例",
        "医保药品目录查询",
        "异地就医备案需要什么材料",
        "长期护理保险待遇"
    ]

    results = batch_match_domain_intent(test_texts, top_k=1)

    for text, matches in zip(test_texts, results):
        if matches:
            match = matches[0]
            print(f"文本: '{text}'")
            print(f"  -> {match.domain}/{match.category}/{match.intent} (置信度: {match.confidence:.2f})")
        else:
            print(f"文本: '{text}' -> 未匹配到意图")


def test_domain_grouping():
    """测试按领域分组"""
    print("\n=== 按领域分组测试 ===")

    text = "我想了解职工医保缴费标准，还有生育津贴怎么申请，以及医保药品目录"
    matcher = get_intent_matcher()
    domain_matches = matcher.get_domain_matches(text)

    print(f"文本: '{text}'")
    for domain, matches in domain_matches.items():
        print(f"\n{domain}:")
        for match in matches:
            print(f"  - {match.intent}: '{match.matched_text}' (置信度: {match.confidence:.2f})")


def test_statistics():
    """测试统计功能"""
    print("\n=== 统计功能测试 ===")

    texts = [
        "职工医保缴费",
        "职工医保报销",
        "居民医保缴费",
        "生育津贴申请",
        "医保药品目录",
        "职工医保缴费标准",
        "异地就医备案",
        "大病保险报销",
        "长期护理保险"
    ]

    stats = get_domain_intent_statistics(texts)

    print("意图分布统计:")
    for intent, count in sorted(stats.items()):
        print(f"  {intent}: {count}次")


def test_performance():
    """性能测试"""
    import time
    import random

    # 构建测试数据
    keywords = [
        "缴费", "报销", "参保", "职工", "居民", "生育", "津贴",
        "药品", "目录", "异地", "就医", "备案", "大病", "救助",
        "费用", "标准", "比例", "申请", "办理", "账户", "等待期"
    ]
    actions = ["怎么", "如何", "什么", "多少", "什么时候", "需要", "可以"]

    test_texts = []
    for _ in range(500):
        keyword = random.choice(keywords)
        action = random.choice(actions)
        test_texts.append(f"{action}{keyword}")

    print("\n=== 性能测试 ===")
    print(f"测试文本数量: {len(test_texts)}")

    # 测试单个匹配性能
    start_time = time.time()
    for text in test_texts:
        match_domain_intent(text, top_k=1)
    single_time = time.time() - start_time

    # 测试批量匹配性能
    start_time = time.time()
    batch_match_domain_intent(test_texts, top_k=1)
    batch_time = time.time() - start_time

    print(f"单个匹配总耗时: {single_time:.4f}秒")
    print(f"平均单个文本: {single_time/len(test_texts)*1000:.2f}毫秒")
    print(f"批量匹配总耗时: {batch_time:.4f}秒")
    print(f"批量匹配加速比: {single_time/batch_time:.2f}x")


def demonstrate_usage():
    """演示使用方法"""
    print("\n=== 使用示例演示 ===")

    # 示例1：单个意图识别
    print("示例1: 单个意图识别")
    results = match_domain_intent("职工医保缴费标准是多少", top_k=3)
    for i, match in enumerate(results, 1):
        print(f"  {i}. {match.domain} -> {match.category} -> {match.intent}")
        print(f"     匹配词: '{match.matched_text}', 置信度: {match.confidence:.2f}")

    # 示例2：业务路由
    print("\n示例2: 业务路由应用")
    text = "我想申请生育津贴"
    results = match_domain_intent(text, top_k=1)
    if results:
        match = results[0]
        print(f"用户查询: {text}")
        print(f"识别意图: {match.intent}")
        print(f"路由到: {match.category} 服务模块")

        # 根据不同意图进行路由
        if match.domain == "职工基本医疗保险":
            print("→ 连接到职工医保服务")
        elif match.domain == "城乡居民医疗保险":
            print("→ 连接到居民医保服务")
        elif match.domain == "生育保险":
            print("→ 连接到生育保险服务")
        elif match.domain == "其他医药政策":
            print("→ 连接到医药政策服务")

    # 示例3：多意图检测
    print("\n示例3: 多意图检测")
    text = "职工医保缴费标准和生育津贴申请"
    results = match_domain_intent(text, top_k=5)
    print(f"文本: {text}")
    for match in results:
        print(f"  - {match.domain}/{match.intent}: '{match.matched_text}'")


if __name__ == "__main__":
    # 运行所有测试
    accuracy = test_intent_matching()
    test_batch_matching()
    test_domain_grouping()
    test_statistics()
    test_performance()
    demonstrate_usage()

    print(f"\n=== 测试完成，总体准确率: {accuracy:.1f}% ===")