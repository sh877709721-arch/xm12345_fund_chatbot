#!/usr/bin/env python3
"""
测试 GraphRAG Local Search 流式 API 的客户端
"""

import asyncio
import aiohttp
import json
import sys

async def test_local_search_stream():
    """测试本地搜索流式 API"""

    url = "http://127.0.0.1:8000/v1/graphrag/local-search/stream"
    payload = {
        "query": "怎么交医保",
        "community_level": 2,
        "response_type": "Multiple Paragraphs"
    }

    print("🚀 开始测试 GraphRAG Local Search 流式 API")
    print(f"📝 查询: {payload['query']}")
    print(f"🌐 URL: {url}")
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
                                print(f"🔍 开始搜索: {data.get('query', '')}")
                                print(f"📊 搜索类型: {data.get('search_type', '')}")
                            elif msg_type == 'chunk':
                                chunk_count += 1
                                print(f"📦 数据块 {chunk_count}: {content}")
                                total_content += content
                            elif msg_type == 'done':
                                print(f"✅ 搜索完成!")
                                print(f"📈 总共收到 {chunk_count} 个数据块")
                                print(f"📝 总内容长度: {len(total_content)} 字符")
                                break
                            elif msg_type == 'error':
                                print(f"❌ 搜索错误: {content}")
                                break

                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON 解析错误: {e}")
                            print(f"原始数据: {line_str}")

                print("-" * 50)
                print("🎉 流式测试完成!")

                # 显示完整响应
                if total_content:
                    print("\n📋 完整响应内容:")
                    print(total_content)

    except aiohttp.ClientError as e:
        print(f"❌ 网络错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def test_with_requests():
    """使用 requests 库的同步版本（需要安装 requests-toolbelt）"""
    import requests
    from requests_toolbelt import SSEDecoder

    url = "http://127.0.0.1:8000/v1/graphrag/local-search/stream"
    payload = {
        "query": "怎么交医保",
        "community_level": 2,
        "response_type": "Multiple Paragraphs"
    }

    print("🔄 使用 requests 库测试...")

    try:
        response = requests.post(
            url,
            json=payload,
            stream=True,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/plain",
                "Cache-Control": "no-cache"
            }
        )

        if response.status_code == 200:
            print("✅ 连接成功")

            for event in SSEDecoder(response.iter_lines()).events():
                if event.event == 'message':
                    try:
                        data = json.loads(event.data)
                        msg_type = data.get('type')

                        if msg_type == 'start':
                            print(f"🔍 开始: {data.get('query')}")
                        elif msg_type == 'chunk':
                            print(f"📦 {data.get('content')}")
                        elif msg_type == 'done':
                            print("✅ 完成")
                            break
                        elif msg_type == 'error':
                            print(f"❌ 错误: {data.get('content')}")
                            break
                    except json.JSONDecodeError:
                        pass
        else:
            print(f"❌ 请求失败: {response.status_code}")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    print("选择测试方式:")
    print("1. 异步 aiohttp (推荐)")
    print("2. 同步 requests")

    choice = input("请输入选择 (1 或 2): ").strip()

    if choice == "1":
        asyncio.run(test_local_search_stream())
    elif choice == "2":
        test_with_requests()
    else:
        print("使用默认的异步方式...")
        asyncio.run(test_local_search_stream())