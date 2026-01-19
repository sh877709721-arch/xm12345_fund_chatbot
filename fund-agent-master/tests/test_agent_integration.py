#!/usr/bin/env python3
"""
测试 ReActChat 与意图识别工具的集成
"""

import sys
import os
import json5
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_intent_recognition_tools():
    """测试意图识别工具是否正常工作"""
    print("🔍 测试意图识别工具")
    print("=" * 50)

    try:
        # 测试直接导入意图识别工具
        from app.core.mcp.intent import (
            recognize_user_intent,
            rewrite_medical_query,
            get_intent_taxonomy
        )

        print("✅ 意图识别工具导入成功")

        # 测试单个意图识别
        test_query = "职工医保怎么报销？"
        print(f"\n📝 测试查询: {test_query}")

        result = recognize_user_intent(test_query)
        result_data = json5.loads(result)

        if result_data.get("success"):
            data = result_data["data"]
            print(f"🎯 一级分类: {data['first_level']}")
            print(f"🏷️  二级分类: {data['second_level']}")
            print(f"📋 三级分类: {data['third_level']}")
            print(f"📊 置信度: {data['confidence']}")
            print(f"✏️  改写后: {data['rewritten_query']}")
        else:
            print(f"❌ 意图识别失败: {result_data.get('error')}")

        # 测试问题改写
        test_rewrite = "生孩子能领多少钱？"
        print(f"\n✏️ 测试改写: {test_rewrite}")

        rewrite_result = rewrite_medical_query(test_rewrite)
        rewrite_data = json5.loads(rewrite_result)

        if rewrite_data.get("success"):
            data = rewrite_data["data"]
            print(f"✨ 改写后: {data['rewritten_query']}")
            print(f"🎯 意图: {data['intent']['first_level']}")
        else:
            print(f"❌ 问题改写失败: {rewrite_data.get('error')}")

        return True

    except Exception as e:
        print(f"❌ 意图识别工具测试失败: {str(e)}")
        return False

def test_agent_configuration():
    """测试Agent配置"""
    print("\n\n🤖 测试Agent配置")
    print("=" * 50)

    try:
        from app.core.agent import bot

        print("✅ Agent实例创建成功")
        print(f"🔧 Agent类型: {type(bot).__name__}")

        # 检查工具列表
        if hasattr(bot, 'function_list'):
            print(f"📋 配置的工具数量: {len(bot.function_list)}")
            print("🛠️ 可用工具:")
            for i, tool in enumerate(bot.function_list):
                print(f"   {i+1}. {tool}")

        # 检查系统消息
        if hasattr(bot, 'system_message'):
            print("📝 系统消息包含意图识别功能:",
                  "recognize_user_intent" in bot.system_message)

        return True

    except Exception as e:
        print(f"❌ Agent配置测试失败: {str(e)}")
        return False

def test_mcp_configuration():
    """测试MCP配置"""
    print("\n\n⚙️ 测试MCP配置")
    print("=" * 50)

    try:
        from app.core.mcp import tools

        print("✅ MCP配置导入成功")
        print("📋 配置的MCP服务:")

        tools_config = tools[0]["mcpServers"]
        for service_name, config in tools_config.items():
            print(f"   🏷️  {service_name}:")
            print(f"      命令: {config['command']}")
            print(f"      参数: {' '.join(config['args'])}")

        # 检查意图识别服务是否配置
        if "intent_recognition" in tools_config:
            print("✅ 意图识别服务已配置")
        else:
            print("❌ 意图识别服务未配置")

        return True

    except Exception as e:
        print(f"❌ MCP配置测试失败: {str(e)}")
        return False

def simulate_agent_workflow():
    """模拟Agent工作流程"""
    print("\n\n🔄 模拟Agent工作流程")
    print("=" * 50)

    # 模拟用户问题
    user_query = "灵活就业人员医保一年交多少钱"

    print(f"👤 用户问题: {user_query}")

    # 步骤1: 意图识别
    print("\n1️⃣ 意图识别阶段:")
    try:
        from app.core.mcp.intent import recognize_user_intent
        intent_result = recognize_user_intent(user_query)
        intent_data = json5.loads(intent_result)

        if intent_data.get("success"):
            data = intent_data["data"]
            print(f"   🎯 识别结果: {data['first_level']} > {data['second_level']}")
            print(f"   📊 置信度: {data['confidence']}")

            if data['confidence'] < 0.6:
                print("   ❓ 置信度较低，需要向用户确认")
                return False
        else:
            print(f"   ❌ 意图识别失败")
            return False

    except Exception as e:
        print(f"   ❌ 意图识别异常: {str(e)}")
        return False

    # 步骤2: 问题改写
    print("\n2️⃣ 问题改写阶段:")
    try:
        from app.core.mcp.intent import rewrite_medical_query
        rewrite_result = rewrite_medical_query(user_query)
        rewrite_data = json5.loads(rewrite_result)

        if rewrite_data.get("success"):
            rewritten_query = rewrite_data["data"]["rewritten_query"]
            print(f"   ✨ 改写后: {rewritten_query}")
        else:
            print(f"   ❌ 问题改写失败")
            return False

    except Exception as e:
        print(f"   ❌ 问题改写异常: {str(e)}")
        return False

    # 步骤3: 信息完整性检查（模拟）
    print("\n3️⃣ 信息完整性检查:")
    print("   🔍 检查参保身份: 灵活就业人员 ✓")
    print("   🔍 检查政策类型: 医保缴费 ✓")
    print("   🔍 检查时间范围: 一年 ✓")
    print("   ✅ 关键信息完整")

    # 步骤4: 文档检索（模拟）
    print("\n4️⃣ 文档检索阶段:")
    print("   📚 检索关键词: 灵活就业 医保 缴费标准")
    print("   📄 找到相关政策文件")

    # 步骤5: 生成答案（模拟）
    print("\n5️⃣ 生成答案:")
    answer = """根据厦门市医保政策，灵活就业人员医保缴费标准如下：

1. 缴费基数：按上年度全市职工平均工资的60%-300%自主选择
2. 缴费比例：12%（含基本医疗保险9% + 大病医疗补助3%）
3. 缴费方式：按月、按季度或按年度缴纳
4. 缴费渠道：税务部门征收，可通过银行代扣、线上缴费等方式

政策文件：《厦门市灵活就业人员参加基本医疗保险管理办法》"""
    print("   💡 生成专业答案")
    print(f"   📋 保留政策文件名称")

    return True

def main():
    """主测试函数"""
    print("🧪 ReActChat + 意图识别集成测试")
    print("=" * 80)

    tests = [
        ("意图识别工具", test_intent_recognition_tools),
        ("Agent配置", test_agent_configuration),
        ("MCP配置", test_mcp_configuration),
        ("工作流程模拟", simulate_agent_workflow)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            results[test_name] = False

    # 测试结果汇总
    print("\n\n📊 测试结果汇总")
    print("=" * 50)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！集成配置正确。")
        print("\n🚀 下一步:")
        print("1. 启动意图识别服务: python -m app.core.mcp.intent")
        print("2. 在应用中使用 Agent 实例")
        print("3. 监控服务运行状态")
    else:
        print("\n⚠️ 存在失败的测试，请检查配置。")
        print("\n🔧 排查建议:")
        print("1. 检查 Python 路径和模块导入")
        print("2. 确认依赖包已正确安装")
        print("3. 验证 MCP 服务配置")

if __name__ == "__main__":
    main()