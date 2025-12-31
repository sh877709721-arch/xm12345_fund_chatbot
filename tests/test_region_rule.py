#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地区意图判断测试用例
"""
from app.core.rule.region_rule import detect_region_intent, batch_detect_region_intent, RegionIntent


def test_single_detection():
    """测试单个文本的地区意图检测"""
    test_cases = [
        # 厦门本地测试
        ("我想去思明区办事", RegionIntent.LOCAL, "思明", "厦门"),
        ("湖里区有个很好的地方", RegionIntent.LOCAL, "湖里", "厦门"),
        ("海沧的朋友约我吃饭", RegionIntent.LOCAL, "海沧", "厦门"),
        ("集美大学很漂亮", RegionIntent.LOCAL, "集美", "厦门"),
        ("同安区的发展很快", RegionIntent.LOCAL, "同安", "厦门"),
        ("翔安新机场建设", RegionIntent.LOCAL, "翔安", "厦门"),
        ("在厦门市内活动", RegionIntent.LOCAL, "厦门", "福建"),

        # 省内异地测试
        ("去福州出差几天", RegionIntent.PROVINCE, "福州", "福建"),
        ("泉州经济发达", RegionIntent.PROVINCE, "泉州", "福建"),
        ("漳州土楼很著名", RegionIntent.PROVINCE, "漳州", "福建"),
        ("莆田的鞋子便宜", RegionIntent.PROVINCE, "莆田", "福建"),
        ("三明环境很好", RegionIntent.PROVINCE, "三明", "福建"),
        ("南平武夷山风景美", RegionIntent.PROVINCE, "南平", "福建"),
        ("龙岩古田会议旧址", RegionIntent.PROVINCE, "龙岩", "福建"),
        ("宁德时代新能源", RegionIntent.PROVINCE, "宁德", "福建"),

        # 省外异地测试
        ("去北京旅游", RegionIntent.NATIONWIDE, "北京", "北京"),
        ("上海工作机会多", RegionIntent.NATIONWIDE, "上海", "上海"),
        ("广州美食丰富", RegionIntent.NATIONWIDE, "广州", "广东"),
        ("深圳科技发达", RegionIntent.NATIONWIDE, "深圳", "广东"),
        ("成都火锅好吃", RegionIntent.NATIONWIDE, "成都", "四川"),
        ("杭州西湖美景", RegionIntent.NATIONWIDE, "杭州", "浙江"),
        ("西安历史古迹", RegionIntent.NATIONWIDE, "西安", "陕西"),

        # 边界情况测试
        ("", RegionIntent.UNKNOWN, None, None),
        ("今天天气不错", RegionIntent.UNKNOWN, None, None),
        ("我想去个地方", RegionIntent.UNKNOWN, None, None),
    ]

    print("=== 单个文本地区意图检测测试 ===")
    for text, expected_intent, expected_location, expected_province in test_cases:
        intent, location, province = detect_region_intent(text)
        status = "✓" if (intent == expected_intent and
                         location == expected_location and
                         province == expected_province) else "✗"

        print(f"{status} 文本: '{text}'")
        print(f"  预期: {expected_intent.value}, {expected_location}, {expected_province}")
        print(f"  实际: {intent.value if intent else None}, {location}, {province}")
        print()


def test_batch_detection():
    """测试批量检测"""
    test_texts = [
        "我要去思明区",
        "福州出差",
        "北京旅游",
        "今天天气好",
        "泉州办事",
        "上海工作"
    ]

    print("=== 批量检测测试 ===")
    results = batch_detect_region_intent(test_texts)

    for text, (intent, location, province) in zip(test_texts, results):
        print(f"文本: '{text}' -> {intent.value}, {location}, {province}")


def test_performance():
    """性能测试"""
    import time
    import random

    # 构建测试数据
    locations = ["思明", "湖里", "海沧", "福州", "泉州", "北京", "上海", "广州", "深圳", "杭州"]
    actions = ["去", "到", "去...办事", "出差", "旅游", "工作", "学习"]

    test_texts = []
    for _ in range(1000):
        location = random.choice(locations)
        action = random.choice(actions)
        test_texts.append(f"{action}{location}")

    print("=== 性能测试 ===")
    print(f"测试文本数量: {len(test_texts)}")

    # 测试单个检测性能
    start_time = time.time()
    for text in test_texts:
        detect_region_intent(text)
    single_time = time.time() - start_time

    # 测试批量检测性能
    start_time = time.time()
    batch_detect_region_intent(test_texts)
    batch_time = time.time() - start_time

    print(f"单个检测总耗时: {single_time:.4f}秒")
    print(f"平均单个文本: {single_time/len(test_texts)*1000:.2f}毫秒")
    print(f"批量检测总耗时: {batch_time:.4f}秒")
    print(f"批量检测加速比: {single_time/batch_time:.2f}x")


def demonstrate_usage():
    """演示使用方法"""
    print("=== 使用示例演示 ===")

    # 示例1：简单使用
    print("示例1: 基本用法")
    intent, location, province = detect_region_intent("我想去思明区办业务")
    print(f"地区意图: {intent.value}")
    print(f"匹配地点: {location}")
    print(f"所属省份: {province}")
    print()

    # 示例2：业务逻辑判断
    print("示例2: 业务逻辑应用")
    text = "准备去福州出差"
    intent, location, province = detect_region_intent(text)

    if intent == RegionIntent.LOCAL:
        print("本地业务，可享受本地优惠政策")
    elif intent == RegionIntent.PROVINCE:
        print("省内业务，可享受省内通办服务")
    elif intent == RegionIntent.NATIONWIDE:
        print("跨省业务，需要额外手续")
    else:
        print("未识别到具体地区，需要进一步确认")
    print()

    # 示例3：批量处理
    print("示例3: 批量处理")
    user_queries = [
        "我想去集美区看看",
        "要去漳州见客户",
        "准备到北京开会"
    ]
    results = batch_detect_region_intent(user_queries)

    for query, (intent, location, province) in zip(user_queries, results):
        print(f"用户查询: {query}")
        print(f"分析结果: {intent.value} - {location} ({province})")
    print()


if __name__ == "__main__":
    # 运行所有测试
    test_single_detection()
    test_batch_detection()
    test_performance()
    demonstrate_usage()

    print("=== 测试完成 ===")