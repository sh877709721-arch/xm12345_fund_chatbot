#!/usr/bin/env python3
"""
测试 GraphRAG 消息格式是否与 agent_stream_response_optimized 一致
"""

import asyncio
import aiohttp
import json
import uuid

async def test_message_format_comparison():
    """对比 GraphRAG 和 Agent 的消息格式"""

    chat_id = str(uuid.uuid4())
    test_query = "怎么交医保"
    url = "http://127.0.0.1:8000/v1/chat/completions"

    models = [
        ("default", "Agent RAG Bot"),
        ("boost", "GraphRAG Boost")
    ]

    print("🔬 GraphRAG 消息格式对比测试")
    print("=" * 60)

    for model_name, description in models:
        print(f"\n🧪 测试 {model_name} - {description}")
        print("-" * 40)

        payload = {
            "chat_id": chat_id,
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": test_query
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
                        "Accept": "text/plain",
                        "Cache-Control": "no-cache"
                    }
                ) as response:

                    if response.status != 200:
                        print(f"❌ 请求失败: {response.status}")
                        continue

                    chunk_count = 0
                    message_id_received = False
                    content_chunks = []
                    done_received = False
                    final_model = None

                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()

                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]  # 移除 "data: "
                                if data_str == "[DONE]":
                                    done_received = True
                                    print(f"   ✅ [DONE] 接收完成")
                                    break

                                data = json.loads(data_str)

                                # 检查消息ID格式
                                if data.get("object") == "chat.completion.message_id":
                                    message_id_received = True
                                    final_model = data.get("model", "unknown")
                                    print(f"   📋 消息ID: {data.get('id', '')[:20]}...")
                                    print(f"   🏷️  模型: {final_model}")
                                    print(f"   📬 消息对象: chat.completion.message_id")

                                # 检查内容块格式
                                elif data.get("object") == "chat.completion.chunk":
                                    chunk_count += 1
                                    if "choices" in data and len(data["choices"]) > 0:
                                        choice = data["choices"][0]
                                        delta = choice.get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            content_chunks.append(content)
                                            if chunk_count <= 3:  # 只显示前3个块
                                                print(f"   📦 数据块 {chunk_count}: {content[:50]}...")
                                    else:
                                        print(f"   ⚠️  异常数据块格式: {str(data)[:100]}...")

                            except json.JSONDecodeError as e:
                                print(f"   ⚠️  JSON 解析错误: {e}")

                    print(f"   📊 统计: {chunk_count} 个数据块, 消息ID: {'✓' if message_id_received else '✗'}, 完成标记: {'✓' if done_received else '✗'}")

                    if final_model:
                        expected_model = "agent_model" if model_name == "default" else "graphrag_model"
                        model_match = expected_model in final_model
                        print(f"   🔍 模型匹配: {'✓' if model_match else '✗'} (期望: {expected_model}, 实际: {final_model})")

        except Exception as e:
            print(f"   ❌ 测试异常: {e}")

    print("\n" + "=" * 60)
    print("📋 消息格式标准检查:")
    print("1. ✓ 消息ID块: object='chat.completion.message_id'")
    print("2. ✓ 内容块: object='chat.completion.chunk'")
    print("3. ✓ 完成标记: data: [DONE]")
    print("4. ✓ 标准OpenAI格式: id, created, model, choices")
    print("5. ✓ Delta格式: content in choices[0].delta")

def show_expected_format():
    """展示期望的消息格式"""
    print("\n📋 期望的消息格式:")
    print("=" * 60)

    print("\n1️⃣ 消息ID块:")
    print(json.dumps({
        "id": "user-msg-id-uuid",
        "object": "chat.completion.message_id",
        "created": 1234567890,
        "model": "agent_model 或 graphrag_model",
        "message_id": {
            "user_message_id": "user_id",
            "assistant_message_id": "assistant_id"
        }
    }, indent=2, ensure_ascii=False))

    print("\n2️⃣ 内容块:")
    print(json.dumps({
        "id": "chatcmpl-uuid",
        "object": "chat.completion.chunk",
        "created": 1234567890,
        "model": "agent_model 或 graphrag-boost",
        "choices": [
            {
                "index": 0,
                "delta": {
                    "content": "响应内容片段"
                },
                "finish_reason": None
            }
        ]
    }, indent=2, ensure_ascii=False))

    print("\n3️⃣ 完成块:")
    print("data: [DONE]")

if __name__ == "__main__":
    print("GraphRAG 消息格式一致性测试")
    print("=" * 60)

    show_expected_format()

    print("\n" + "🚀 开始格式测试...")
    input("按回车键开始测试 (确保服务器在 http://127.0.0.1:8000 运行)")

    asyncio.run(test_message_format_comparison())