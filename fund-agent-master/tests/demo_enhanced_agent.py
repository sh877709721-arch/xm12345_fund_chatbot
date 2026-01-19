#!/usr/bin/env python3
"""
增强型医疗保险智能助手演示
集成意图识别功能的 ReActChat 示例
"""

import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.agent import bot

def demo_conversation():
    """演示对话流程"""
    print("🤖 厦门市医保智能助手 - 增强版演示")
    print("=" * 60)
    print("✨ 集成意图识别功能，提供更精准的医保政策解答")
    print("📋 支持的功能:")
    print("   - 智能意图识别和分类")
    print("   - 问题自动改写和优化")
    print("   - 关键信息完整性检查")
    print("   - 政策文档精准检索")
    print("   - 主动追问缺失信息")
    print("=" * 60)

    # 示例对话
    test_conversations = [
        {
            "user": "我想知道医保怎么用",
            "description": "模糊问题 - 需要意图识别和信息补充"
        },
        {
            "user": "生孩子能领多少钱",
            "description": "口语化问题 - 需要改写和分类"
        },
        {
            "user": "外地看病能不能报销",
            "description": "复杂场景 - 需要确认具体信息"
        },
        {
            "user": "灵活就业人员医保缴费标准",
            "description": "具体问题 - 相对明确"
        }
    ]

    for i, conv in enumerate(test_conversations, 1):
        print(f"\n🎯 示例对话 {i}")
        print(f"📝 场景描述: {conv['description']}")
        print(f"👤 用户问题: {conv['user']}")
        print("-" * 40)

        # 模拟对话流程
        print("🔄 处理流程:")

        # 1. 意图识别
        print("   1️⃣ 意图识别阶段...")
        print("      🎯 识别用户真实意图和分类")
        print("      📊 计算置信度，评估识别准确性")

        # 2. 问题改写
        print("   2️⃣ 问题改写阶段...")
        print("      ✏️ 将口语化问题转为专业术语")
        print("      🔍 补充医保相关的专业词汇")

        # 3. 信息检查
        print("   3️⃣ 信息完整性检查...")
        print("      🔍 检查参保身份、地域等关键信息")
        print("      ❓ 识别需要追问的缺失信息")

        # 4. 文档检索
        print("   4️⃣ 政策文档检索...")
        print("      📚 从医保政策库中检索相关内容")
        print("      📄 返回权威政策文件内容")

        # 5. 答案整理
        print("   5️⃣ 答案整理阶段...")
        print("      💡 基于检索结果整理专业答案")
        print("      📋 保留政策文件名称和出处")

        print("\n💡 智能助手会根据识别结果:")
        if i == 1:
            print("   - 询问您是职工医保还是居民医保")
            print("   - 了解您具体的查询需求")
        elif i == 2:
            print("   - 识别为生育保险咨询")
            print("   - 改写为'生育津贴待遇标准'查询")
        elif i == 3:
            print("   - 询问您的参保地和就医地")
            print("   - 确认是否已办理异地就医备案")
        elif i == 4:
            print("   - 直接提供灵活就业人员缴费标准")
            print("   - 说明缴费基数和比例")

def demo_intent_recognition_workflow():
    """演示意图识别工作流程"""
    print("\n\n🔍 意图识别工作流程详解")
    print("=" * 60)

    print("""
1️⃣ **接收用户问题**
   - 原始输入: "医保卡丢了怎么办"
   - 问题类型: 口语化、缺少具体信息

2️⃣ **调用意图识别工具**
   ```python
   recognize_user_intent(query="医保卡丢了怎么办")
   ```

   🎯 识别结果:
   - 一级分类: 职工基本医疗保险
   - 二级分类: 办事指南
   - 三级分类: 未明确识别
   - 置信度: 0.75
   - 推荐操作: 需要确认具体问题类型

3️⃣ **问题改写优化**
   ```python
   rewrite_medical_query(query="医保卡丢了怎么办")
   ```

   ✨ 改写结果: "职工基本医疗保险：医保卡丢失处理 办事指南"

4️⃣ **信息完整性检查**
   ❓ 需要追问的关键信息:
   - 参保类型（职工医保/居民医保）
   - 卡丢失的具体情况（挂失/补办）
   - 是否需要临时就医凭证

5️⃣ **智能追问**
   "您好！我理解您的医保卡丢失了。为了给您提供准确的帮助，请问：
   • 您参加的是职工基本医疗保险还是城乡居民医疗保险？
   • 您是需要办理挂失手续还是补办新卡？
   • 您现在急需使用医保卡就医吗？"

6️⃣ **文档检索和解答**
   根据用户补充信息，检索相应的政策文件并提供准确解答。
    """)

def demo_mcp_integration():
    """演示MCP工具集成"""
    print("\n\n🔧 MCP工具集成说明")
    print("=" * 60)

    print("""
📋 已集成的MCP工具:

1️⃣ **intent_recognition** (意图识别服务)
   - recognize_user_intent(): 智能识别用户问题意图
   - rewrite_medical_query(): 改写和优化医保问题
   - get_intent_taxonomy(): 获取分类体系
   - batch_intent_recognition(): 批量意图识别

2️⃣ **base_tools** (基础工具服务)
   - get_current_time(): 获取当前时间

🔄 工作流程集成:

```python
# ReActChat 中的处理流程
def process_user_query(query):
    # 1. 意图识别
    intent_result = recognize_user_intent(query)

    # 2. 检查置信度
    if intent_result.confidence < 0.6:
        return ask_for_clarification()

    # 3. 问题改写
    rewritten_query = rewrite_medical_query(query)

    # 4. 信息检查
    missing_info = check_completeness(rewritten_query)
    if missing_info:
        return ask_followup_questions(missing_info)

    # 5. 文档检索
    docs = medical_insurance_doc_retrieval(rewritten_query)

    # 6. 生成答案
    return generate_response(docs)
```

⚡ 性能优化:
- 意图识别响应时间: < 100ms
- 支持批量处理多个问题
- 缓存常用意图模式
- 降级机制保证服务可用性
    """)

def usage_examples():
    """使用示例"""
    print("\n\n💡 实际使用示例")
    print("=" * 60)

    examples = [
        {
            "用户输入": "我在外地看病能不能报销",
            "意图识别": "异地就医备案",
            "问题改写": "职工基本医疗保险：外地看病报销 异地就医备案",
            "智能追问": "请告诉我您的参保地和就医城市"
        },
        {
            "用户输入": "生孩子有什么补贴",
            "意图识别": "生育津贴待遇",
            "问题改写": "生育保险：生育补贴标准 生育津贴待遇",
            "智能追问": "请问您是职工参保还是居民参保？"
        },
        {
            "用户输入": "医保卡里没钱了",
            "意图识别": "医保账户划拨",
            "问题改写": "职工基本医疗保险：个人账户余额 医保账户划拨",
            "智能追问": "需要查看您的医保账户缴费记录和划拨情况"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n📝 示例 {i}:")
        print(f"   👤 用户输入: {example['用户输入']}")
        print(f"   🎯 意图识别: {example['意图识别']}")
        print(f"   ✨ 问题改写: {example['问题改写']}")
        print(f"   ❓ 智能追问: {example['智能追问']}")

def main():
    """主演示函数"""
    print("🚀 医疗保险智能助手 - 意图识别集成演示")
    print("基于 ReActChat + MCP 意图识别工具")
    print(f"演示时间: 2025-11-14")
    print("=" * 80)

    # 运行各项演示
    demo_conversation()
    demo_intent_recognition_workflow()
    demo_mcp_integration()
    usage_examples()

    print("\n\n" + "=" * 80)
    print("✅ 演示完成！")
    print("\n🔧 启动方式:")
    print("1. 确保 MCP 配置正确 (app/core/mcp/__init__.py)")
    print("2. 启动意图识别服务: python -m app.core.mcp.intent")
    print("3. 在您的应用中导入并使用 bot 实例")

    print("\n📞 联系方式:")
    print("- 如有问题请联系技术支持")
    print("- 医保政策咨询请拨打: 12345")

if __name__ == "__main__":
    main()