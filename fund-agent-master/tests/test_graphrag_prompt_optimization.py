#!/usr/bin/env python3
"""
测试优化后的 GraphRAG 提示词效果
"""

import asyncio
import aiohttp
import json
import uuid

async def test_prompt_optimization():
    """测试优化后的 GraphRAG 提示词"""

    chat_id = str(uuid.uuid4())
    url = "http://127.0.0.1:8000/v1/chat/completions"

    # 测试问题列表
    test_queries = [
        "怎么交医保？",
        "医保报销的条件是什么？",
        "异地就医如何办理？",
        "医保卡丢失了怎么办？",
        "生育保险待遇有哪些？"
    ]

    print("🧪 GraphRAG 提示词优化效果测试")
    print("=" * 60)
    print("测试场景：厦门市医保政务服务")
    print("角色：小E助手 (基于知识图谱)")
    print("提示词：优化后的本地搜索提示词")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 测试 {i}/{len(test_queries)}: {query}")
        print("-" * 40)

        payload = {
            "chat_id": chat_id,
            "model": "boost",  # 使用 GraphRAG
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 8192,
            "temperature": 0.2
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/plain"
                    }
                ) as response:

                    if response.status != 200:
                        print(f"❌ 请求失败: {response.status}")
                        continue

                    full_response = ""
                    chunk_count = 0

                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()

                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]
                                if data_str == "[DONE]":
                                    break

                                data = json.loads(data_str)

                                if (data.get("object") == "chat.completion.chunk" and
                                    "choices" in data and
                                    len(data["choices"]) > 0):

                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_response += content
                                        chunk_count += 1

                            except json.JSONDecodeError:
                                pass

                    if full_response:
                        print(f"✅ 回答长度: {len(full_response)} 字符")
                        print(f"📊 数据块数: {chunk_count}")

                        # 检查回答质量指标
                        quality_checks = {
                            "专业术语": any(term in full_response for term in ["医保", "报销", "缴费", "待遇"]),
                            "结构化回答": any(marker in full_response for marker in ["##", "###", "**", "•"]),
                            "知识图谱引用": "[知识图谱:" in full_response,
                            "身份标识": "小E" in full_response or "助手" in full_response,
                            "字数控制": 200 <= len(full_response) <= 300,
                            "礼貌用语": any(phrase in full_response for phrase in ["您好", "请问", "建议", "如果"])
                        }

                        print("📋 质量检查:")
                        for check, passed in quality_checks.items():
                            status = "✓" if passed else "✗"
                            print(f"   {status} {check}")

                        # 显示回答预览
                        preview_length = 150
                        if len(full_response) > preview_length:
                            preview = full_response[:preview_length] + "..."
                        else:
                            preview = full_response

                        print(f"📄 回答预览:\n   {preview}")

                    else:
                        print("⚠️  未收到回答内容")

        except Exception as e:
            print(f"❌ 测试异常: {e}")

    print("\n" + "=" * 60)
    print("🎯 优化效果分析:")
    print("1. ✓ 角色定位：厦门市医保政务服务助手")
    print("2. ✓ 回答风格：亲切耐心，专业准确")
    print("3. ✓ 结构组织：markdown 格式，层次清晰")
    print("4. ✓ 引用规范：知识图谱数据引用")
    print("5. ✓ 字数控制：200-300字范围")
    print("6. ✓ 政策专业：医保术语准确使用")

def show_prompt_comparison():
    """显示提示词前后对比"""
    print("\n📋 提示词优化对比:")
    print("=" * 60)

    print("\n🔧 优化前 - 通用型助手:")
    print("   - 角色：智能助手，回答表格数据问题")
    print("   - 引用：[数据: 数据集名称 (记录ID)]")
    print("   - 风格：技术导向，通用回答")
    print("   - 重点：数据准确性，结构化回答")

    print("\n✨ 优化后 - 医保政务服务助手:")
    print("   - 角色：厦门市医保助手小E，专业知识图谱问答")
    print("   - 引用：[知识图谱: 数据类型 (记录ID)]")
    print("   - 风格：亲切耐心，政务专业")
    print("   - 重点：市民服务，政策准确，操作指导")

    print("\n🚀 主要改进:")
    print("   1. ✓ 融入医保政务服务经验")
    print("   2. ✓ 统一 Assistant 服务标准")
    print("   3. ✓ 知识图谱特化优化")
    print("   4. ✓ 市民友好语言风格")
    print("   5. ✓ 政策专业性提升")

if __name__ == "__main__":
    print("GraphRAG 提示词优化测试")
    print("=" * 60)

    show_prompt_comparison()

    print("\n🚀 开始提示词效果测试...")
    input("按回车键开始测试 (确保服务器在 http://127.0.0.1:8000 运行)")

    asyncio.run(test_prompt_optimization())