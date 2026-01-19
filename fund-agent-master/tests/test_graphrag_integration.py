#!/usr/bin/env python3
"""
测试 GraphRAG 集成到 completions 接口的功能
"""

import asyncio
import aiohttp
import json
import uuid

async def test_graphrag_completion():
    """测试 GraphRAG completion 接口"""

    # 测试数据
    chat_id = str(uuid.uuid4())
    test_query = "怎么交医保"

    url = "http://127.0.0.1:8000/v1/chat/completions"

    # 请求体格式
    payload = {
        "chat_id": chat_id,
        "model": "boost",  # 使用 boost 模式触发 GraphRAG
        "messages": [
            {
                "role": "user",
                "content": test_query
            }
        ],
        "max_tokens": 8192,
        "temperature": 0.2
    }

    print("🚀 开始测试 GraphRAG 集成到 completions 接口")
    print(f"📝 查询: {test_query}")
    print(f"💬 聊天ID: {chat_id}")
    print(f"🔧 模型: boost (GraphRAG)")
    print("-" * 50)

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
                    print(f"错误信息: {await response.text()}")
                    return

                print("✅ 连接成功，开始接收流式数据...")
                print("-" * 50)

                chunk_count = 0
                total_content = ""

                async for line in response.content:
                    line_str = line.decode('utf-8').strip()

                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # 移除 "data: " 前缀
                            msg_type = data.get('type')
                            content = data.get('content', '')

                            if msg_type == 'start':
                                print(f"🔍 开始 GraphRAG 增强搜索")
                            elif msg_type == 'content':
                                chunk_count += 1
                                print(f"📦 数据块 {chunk_count}: {content}")
                                total_content += content
                            elif msg_type == 'done':
                                print(f"✅ GraphRAG 搜索完成!")
                                print(f"📈 总共收到 {chunk_count} 个数据块")
                                print(f"📝 总内容长度: {len(total_content)} 字符")
                                break
                            elif msg_type == 'error':
                                print(f"❌ GraphRAG 搜索错误: {content}")
                                break

                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON 解析错误: {e}")
                            print(f"原始数据: {line_str}")

                print("-" * 50)
                print("🎉 GraphRAG 集成测试完成!")

                # 显示完整响应
                if total_content:
                    print("\n📋 完整 GraphRAG 响应内容:")
                    print(total_content)

    except aiohttp.ClientError as e:
        print(f"❌ 网络错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

async def test_model_comparison():
    """对比不同模型的效果"""

    chat_id = str(uuid.uuid4())
    test_query = "怎么交医保"
    url = "http://127.0.0.1:8000/v1/chat/completions"

    models = [
        ("default", "标准 RAG Bot"),
        ("boost", "GraphRAG 增强搜索")
    ]

    print("🔬 模型对比测试")
    print("-" * 50)

    for model_name, description in models:
        print(f"\n🧪 测试模型: {model_name} - {description}")

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
                        "Accept": "text/plain"
                    }
                ) as response:

                    if response.status == 200:
                        content_parts = []
                        chunk_count = 0

                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()

                            if line_str.startswith('data: '):
                                try:
                                    data = json.loads(line_str[6:])
                                    if data.get('type') == 'content':
                                        content_parts.append(data.get('content', ''))
                                        chunk_count += 1
                                        if chunk_count <= 3:  # 只显示前3个块
                                            print(f"   📦 {data.get('content', '')[:100]}...")
                                    elif data.get('type') == 'done':
                                        break
                                except:
                                    pass

                        full_content = ''.join(content_parts)
                        print(f"   ✅ {model_name} 响应完成: {len(full_content)} 字符")

                    else:
                        print(f"   ❌ {model_name} 请求失败: {response.status}")

        except Exception as e:
            print(f"   ❌ {model_name} 测试异常: {e}")

def test_curl_example():
    """提供 curl 命令示例"""

    chat_id = str(uuid.uuid4())

    print("\n" + "="*50)
    print("🔧 curl 测试命令示例")
    print("="*50)

    print(f"\n📋 GraphRAG Boost 模式测试:")
    print(f"curl -X POST \"http://127.0.0.1:8000/v1/chat/completions\" \\")
    print(f"  -H \"Content-Type: application/json\" \\")
    print(f"  -d '{{")
    print(f"    \"chat_id\": \"{chat_id}\",")
    print(f"    \"model\": \"boost\",")
    print(f"    \"messages\": [")
    print(f"      {{\"role\": \"user\", \"content\": \"怎么交医保\"}}")
    print(f"    ],")
    print(f"    \"max_tokens\": 8192,")
    print(f"    \"temperature\": 0.2")
    print(f"  }}'")

    print(f"\n📋 标准 RAG 模式测试:")
    print(f"curl -X POST \"http://127.0.0.1:8000/v1/chat/completions\" \\")
    print(f"  -H \"Content-Type: application/json\" \\")
    print(f"  -d '{{")
    print(f"    \"chat_id\": \"{chat_id}\",")
    print(f"    \"model\": \"default\",")
    print(f"    \"messages\": [")
    print(f"      {{\"role\": \"user\", \"content\": \"怎么交医保\"}}")
    print(f"    ],")
    print(f"    \"max_tokens\": 8192,")
    print(f"    \"temperature\": 0.2")
    print(f"  }}'")

if __name__ == "__main__":
    print("GraphRAG 集成测试选项:")
    print("1. 测试 GraphRAG Boost 模式")
    print("2. 模型对比测试")
    print("3. 显示 curl 命令示例")

    choice = input("\n请选择测试方式 (1/2/3): ").strip()

    if choice == "1":
        asyncio.run(test_graphrag_completion())
    elif choice == "2":
        asyncio.run(test_model_comparison())
    elif choice == "3":
        test_curl_example()
    else:
        print("使用默认测试...")
        asyncio.run(test_graphrag_completion())