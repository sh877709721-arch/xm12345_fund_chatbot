#!/usr/bin/env python3
"""
意图识别MCP工具测试脚本
演示如何使用各种意图识别功能
"""

import json
import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.mcp.intent import (
    recognize_user_intent,
    rewrite_medical_query,
    get_intent_taxonomy,
    batch_intent_recognition
)

def test_single_intent_recognition():
    """测试单个意图识别"""
    print("=" * 60)
    print("🔍 单个意图识别测试")
    print("=" * 60)

    test_queries = [
        "职工医保怎么报销？",
        "灵活就业人员医保缴费标准是多少？",
        "城乡居民医保的参保对象包括哪些人？",
        "生育津贴如何申请？",
        "异地就医备案需要什么材料？",
        "医保个人账户余额怎么查询？",
        "大病保险的报销比例是多少？",
        "家庭共济账户怎么绑定家人？",
        "医保关系转移怎么办理？",
        "惠厦保是什么保险？"
    ]

    for query in test_queries:
        print(f"\n📝 原始问题: {query}")
        result = recognize_user_intent(query)

        try:
            result_data = json.loads(result)
            if result_data.get("success"):
                data = result_data["data"]
                print(f"🎯 一级分类: {data['first_level']}")
                print(f"🏷️  二级分类: {data['second_level']}")
                print(f"📋 三级分类: {data['third_level']}")
                print(f"📊 置信度: {data['confidence']}")
                print(f"⚡ 推荐操作: {data['action']}")
                print(f"✏️  改写后: {data['rewritten_query']}")
            else:
                print(f"❌ 识别失败: {result_data.get('error')}")
        except json.JSONDecodeError:
            print(f"❌ 结果解析失败")

def test_query_rewrite():
    """测试问题改写"""
    print("\n" + "=" * 60)
    print("✏️ 问题改写测试")
    print("=" * 60)

    test_queries = [
        "我想知道医保怎么用",
        "生孩子有什么补贴",
        "外地看病能不能报销",
        "老人医保要交多少钱",
        "医保卡里没钱了怎么办"
    ]

    for query in test_queries:
        print(f"\n📝 原始问题: {query}")
        result = rewrite_medical_query(query)

        try:
            result_data = json.loads(result)
            if result_data.get("success"):
                data = result_data["data"]
                print(f"✨ 改写后: {data['rewritten_query']}")
                print(f"🎯 识别意图: {data['intent']['first_level']} > {data['intent']['second_level']} > {data['intent']['third_level']}")
                print(f"📊 置信度: {data['confidence']}")
            else:
                print(f"❌ 改写失败: {result_data.get('error')}")
        except json.JSONDecodeError:
            print(f"❌ 结果解析失败")

def test_batch_recognition():
    """测试批量意图识别"""
    print("\n" + "=" * 60)
    print("📦 批量意图识别测试")
    print("=" * 60)

    test_queries = [
        "职工医保缴费",
        "居民医保报销",
        "生育津贴申请",
        "异地就医备案",
        "大病保险待遇"
    ]

    print(f"📋 批量识别 {len(test_queries)} 个问题...")
    result = batch_intent_recognition(test_queries)

    try:
        result_data = json.loads(result)
        if result_data.get("success"):
            data = result_data["data"]
            print(f"✅ 成功识别: {data['successful_recognition']}/{data['total_queries']}")

            for i, item in enumerate(data["results"]):
                print(f"\n{i+1}. 问题: {item['query']}")
                if item["success"]:
                    print(f"   🎯 分类: {item['first_level']} > {item['second_level']} > {item['third_level']}")
                    print(f"   📊 置信度: {item['confidence']}")
                else:
                    print(f"   ❌ 失败: {item['error']}")
        else:
            print(f"❌ 批量识别失败: {result_data.get('error')}")
    except json.JSONDecodeError:
        print(f"❌ 结果解析失败")

def test_taxonomy_info():
    """测试分类体系信息"""
    print("\n" + "=" * 60)
    print("📚 分类体系信息")
    print("=" * 60)

    result = get_intent_taxonomy()

    try:
        result_data = json.loads(result)
        if result_data.get("success"):
            data = result_data["data"]
            taxonomy = data["taxonomy"]
            print(f"📊 总分类数: {data['total_categories']}")

            for first_level, second_level_data in taxonomy.items():
                print(f"\n🏷️  一级: {first_level}")
                if isinstance(second_level_data, dict):
                    for second_level, third_level_data in second_level_data.items():
                        print(f"  └─ 二级: {second_level}")
                        if isinstance(third_level_data, dict):
                            for third_level in third_level_data.keys():
                                print(f"    └─ 三级: {third_level}")
                        else:
                            print(f"    └─ 直接分类")
                else:
                    print(f"  └─ 直接分类")
        else:
            print(f"❌ 获取分类体系失败: {result_data.get('error')}")
    except json.JSONDecodeError:
        print(f"❌ 结果解析失败")

def main():
    """主测试函数"""
    print("🚀 意图识别MCP工具测试开始")
    print("测试时间:", "2025-11-14")
    print("工具版本:", "v1.0")

    try:
        # 运行各项测试
        test_single_intent_recognition()
        test_query_rewrite()
        test_batch_recognition()
        test_taxonomy_info()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

        print("\n📝 使用建议:")
        print("1. 使用 recognize_user_intent() 进行单个意图识别")
        print("2. 使用 rewrite_medical_query() 优化用户问题")
        print("3. 使用 batch_intent_recognition() 批量处理多个问题")
        print("4. 使用 get_intent_taxonomy() 获取完整分类体系")

        print("\n🔧 MCP服务器启动:")
        print("python -m app.core.mcp.intent")

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()