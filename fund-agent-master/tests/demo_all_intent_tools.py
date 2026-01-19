#!/usr/bin/env python3
"""
演示所有意图识别工具的使用
包含4个MCP工具的完整功能演示
"""

import json5
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_all_intent_tools():
    """演示所有4个意图识别工具"""
    print("🎯 意图识别工具完整功能演示")
    print("=" * 60)
    print("📋 可用的4个工具:")
    print("   1. recognize_user_intent - 意图识别")
    print("   2. rewrite_medical_query - 问题改写")
    print("   3. get_intent_taxonomy - 获取分类体系")
    print("   4. batch_intent_recognition - 批量意图识别")
    print("=" * 60)

    # 方式一：直接调用MCP工具（推荐方式）
    print("\n📞 方式一：直接调用MCP工具")
    print("-" * 40)

    try:
        # 导入MCP工具
        from app.core.mcp.intent import (
            recognize_user_intent,
            rewrite_medical_query,
            get_intent_taxonomy,
            batch_intent_recognition
        )

        print("✅ MCP工具导入成功")

        # 1. 演示意图识别工具
        print("\n1️⃣ 演示 recognize_user_intent:")
        test_query = "灵活就业人员医保缴费标准"
        print(f"   📝 查询: {test_query}")

        intent_result = recognize_user_intent(test_query)
        intent_data = json5.loads(intent_result)

        if intent_data.get("success"):
            data = intent_data["data"]
            print(f"   🎯 分类: {data['first_level']} > {data['second_level']} > {data['third_level']}")
            print(f"   📊 置信度: {data['confidence']}")
            print(f"   ✏️  改写: {data['rewritten_query']}")
        else:
            print(f"   ❌ 失败: {intent_data.get('error')}")

        # 2. 演示问题改写工具
        print("\n2️⃣ 演示 rewrite_medical_query:")
        rewrite_query = "生孩子能领多少钱"
        print(f"   📝 原始: {rewrite_query}")

        rewrite_result = rewrite_medical_query(rewrite_query)
        rewrite_data = json5.loads(rewrite_result)

        if rewrite_data.get("success"):
            data = rewrite_data["data"]
            print(f"   ✨ 改写: {data['rewritten_query']}")
            print(f"   🎯 意图: {data['intent']['first_level']}")
        else:
            print(f"   ❌ 失败: {rewrite_data.get('error')}")

        # 3. 演示获取分类体系
        print("\n3️⃣ 演示 get_intent_taxonomy:")
        taxonomy_result = get_intent_taxonomy()
        taxonomy_data = json5.loads(taxonomy_result)

        if taxonomy_data.get("success"):
            data = taxonomy_data["data"]
            print(f"   📚 分类总数: {data['total_categories']}")
            print("   🏷️  一级分类:")
            for i, category in enumerate(data['taxonomy'].keys(), 1):
                print(f"      {i}. {category}")
        else:
            print(f"   ❌ 失败: {taxonomy_data.get('error')}")

        # 4. 演示批量意图识别
        print("\n4️⃣ 演示 batch_intent_recognition:")
        batch_queries = [
            "医保卡丢了怎么办",
            "异地就医备案流程",
            "生育津贴申请条件",
            "大病保险报销比例"
        ]
        print(f"   📦 批量查询: {len(batch_queries)} 个")

        batch_result = batch_intent_recognition(batch_queries)
        batch_data = json5.loads(batch_result)

        if batch_data.get("success"):
            data = batch_data["data"]
            print(f"   ✅ 成功识别: {data['successful_recognition']}/{data['total_queries']}")
            for i, result in enumerate(data["results"][:2], 1):  # 只显示前2个
                print(f"      {i}. {result['query'][:20]}... -> {result['first_level']}")
        else:
            print(f"   ❌ 失败: {batch_data.get('error')}")

        return True

    except Exception as e:
        print(f"❌ MCP工具调用失败: {str(e)}")
        return False

def demo_agent_with_all_tools():
    """演示Agent使用所有意图识别工具"""
    print("\n\n🤖 Agent使用所有意图识别工具")
    print("=" * 60)

    try:
        from app.core.agent import bot

        print("✅ Agent实例创建成功")

        # 检查工具列表
        if hasattr(bot, 'function_list'):
            intent_tools = [
                'recognize_user_intent',
                'rewrite_medical_query',
                'get_intent_taxonomy',
                'batch_intent_recognition'
            ]

            available_tools = []
            for tool in bot.function_list:
                if tool in intent_tools:
                    available_tools.append(tool)

            print(f"📋 意图识别工具: {len(available_tools)}/{len(intent_tools)} 已配置")
            print("🛠️ 可用工具:")
            for tool in available_tools:
                print(f"   ✓ {tool}")

            missing_tools = set(intent_tools) - set(available_tools)
            if missing_tools:
                print("❌ 缺失工具:")
                for tool in missing_tools:
                    print(f"   ✗ {tool}")

            return len(missing_tools) == 0

        return False

    except Exception as e:
        print(f"❌ Agent测试失败: {str(e)}")
        return False

def demo_workflow_with_all_tools():
    """演示完整的工作流程"""
    print("\n\n🔄 完整工作流程演示")
    print("=" * 60)

    try:
        from app.core.mcp.intent import (
            recognize_user_intent,
            rewrite_medical_query,
            get_intent_taxonomy
        )

        print("📋 模拟Agent处理用户问题的完整流程:")

        # 用户问题
        user_query = "我想了解医保报销流程"
        print(f"\n👤 用户问题: {user_query}")

        # 步骤1: 获取分类体系（用于上下文理解）
        print("\n1️⃣ 获取分类体系:")
        taxonomy_result = get_intent_taxonomy()
        taxonomy_data = json5.loads(taxonomy_result)

        if taxonomy_data.get("success"):
            categories = list(taxonomy_data["data"]["taxonomy"].keys())
            print(f"   📚 可用分类: {', '.join(categories[:3])}...")

        # 步骤2: 意图识别
        print("\n2️⃣ 意图识别:")
        intent_result = recognize_user_intent(user_query)
        intent_data = json5.loads(intent_result)

        if intent_data.get("success"):
            data = intent_data["data"]
            confidence = data["confidence"]
            print(f"   🎯 分类: {data['first_level']} > {data['second_level']} > {data['third_level']}")
            print(f"   📊 置信度: {confidence}")

            if confidence < 0.6:
                print("   ❓ 置信度较低，需要向用户确认")
                return False
        else:
            print("   ❌ 意图识别失败")
            return False

        # 步骤3: 问题改写
        print("\n3️⃣ 问题改写:")
        rewrite_result = rewrite_medical_query(user_query)
        rewrite_data = json5.loads(rewrite_result)

        if rewrite_data.get("success"):
            rewritten_query = rewrite_data["data"]["rewritten_query"]
            print(f"   ✨ 改写后: {rewritten_query}")
        else:
            print("   ❌ 问题改写失败")
            return False

        # 步骤4: 信息完整性检查
        print("\n4️⃣ 信息完整性检查:")
        print("   🔍 检查参保身份: 需要确认")
        print("   🔍 检查报销类型: 医疗费用报销 ✓")
        print("   ❓ 缺失信息: 建议询问参保类型")

        # 步骤5: 生成追问
        print("\n5️⃣ 智能追问:")
        clarification = """您好！关于医保报销流程，为了给您提供准确的信息，请问：
• 您参加的是职工基本医疗保险还是城乡居民医疗保险？
• 您是想了解门诊报销还是住院报销？
• 您是在厦门市内就医还是需要异地报销？"""
        print(f"   💬 追问: {clarification}")

        return True

    except Exception as e:
        print(f"❌ 工作流程演示失败: {str(e)}")
        return False

def main():
    """主演示函数"""
    print("🚀 意图识别工具完整功能演示")
    print("基于 app/core/mcp/intent.py 中的4个MCP工具")
    print("=" * 80)

    demos = [
        ("MCP工具功能演示", demo_all_intent_tools),
        ("Agent工具配置检查", demo_agent_with_all_tools),
        ("完整工作流程演示", demo_workflow_with_all_tools)
    ]

    results = {}
    for demo_name, demo_func in demos:
        try:
            results[demo_name] = demo_func()
        except Exception as e:
            print(f"❌ {demo_name}演示异常: {str(e)}")
            results[demo_name] = False

    # 演示结果汇总
    print("\n\n📊 演示结果汇总")
    print("=" * 50)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for demo_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{demo_name}: {status}")

    print(f"\n总计: {passed}/{total} 演示成功")

    if passed == total:
        print("\n🎉 所有演示成功！")
        print("\n🎯 现在您的Agent拥有完整的意图识别能力:")
        print("   • 精准识别用户意图（4级分类体系）")
        print("   • 智能改写口语化问题")
        print("   • 获取完整分类体系信息")
        print("   • 批量处理多个问题")
        print("   • 置信度评估和主动确认")
        print("\n🚀 Agent工作流程:")
        print("   1. 用户输入 → 2. 意图识别 → 3. 问题改写")
        print("   4. 信息检查 → 5. 智能追问 → 6. 文档检索 → 7. 专业解答")
    else:
        print("\n⚠️ 部分演示失败，请检查:")
        print("   • MCP服务是否正确启动")
        print("   • 工具配置是否正确")
        print("   • 依赖包是否完整")

if __name__ == "__main__":
    main()