#!/usr/bin/env python3
"""
测试 GraphRAG Local Search API 的脚本
"""

import requests
import json
import asyncio
import sys
from pathlib import Path

# API 基础 URL
BASE_URL = "http://localhost:8000"

def test_local_search_api():
    """测试本地搜索 API 端点"""

    print("🧪 测试 GraphRAG Local Search API\n")

    # 测试数据
    test_query = "什么是人工智能？"

    print(f"📝 测试查询: {test_query}\n")

    # 1. 测试健康检查端点
    print("1️⃣ 测试健康检查端点...")
    try:
        response = requests.get(f"{BASE_URL}/graphrag/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ 健康检查通过")
            print(f"   - 服务状态: {health_data.get('status')}")
            print(f"   - 本地搜索可用: {health_data.get('local_search_available')}")
            print(f"   - 本地搜索流式可用: {health_data.get('local_search_stream_available')}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return

    print("\n" + "="*50 + "\n")

    # 2. 测试本地搜索普通查询
    print("2️⃣ 测试本地搜索普通查询...")
    try:
        payload = {
            "query": test_query,
            "community_level": 2,
            "response_type": "Multiple Paragraphs"
        }

        response = requests.post(
            f"{BASE_URL}/graphrag/local-search",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 本地搜索查询成功")
            print(f"   - 成功状态: {data.get('success')}")
            print(f"   - 响应长度: {data.get('metadata', {}).get('response_length', 0)} 字符")
            print(f"   - 搜索类型: {data.get('metadata', {}).get('search_type')}")
            print(f"   - 响应预览: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ 本地搜索查询失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 本地搜索查询异常: {e}")

    print("\n" + "="*50 + "\n")

    # 3. 测试本地搜索流式查询
    print("3️⃣ 测试本地搜索流式查询...")
    try:
        payload = {
            "query": test_query,
            "community_level": 2,
            "response_type": "Multiple Paragraphs"
        }

        response = requests.post(
            f"{BASE_URL}/graphrag/local-search/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True
        )

        if response.status_code == 200:
            print("✅ 本地搜索流式查询连接成功")

            chunk_count = 0
            content_parts = []

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # 移除 "data: " 前缀
                            msg_type = data.get('type')
                            content = data.get('content', '')

                            if msg_type == 'start':
                                print(f"   🚀 开始搜索: {data.get('query', '')[:50]}...")
                            elif msg_type == 'chunk':
                                content_parts.append(content)
                                chunk_count += 1
                                if chunk_count <= 3:  # 只显示前3个块
                                    print(f"   📦 块 {chunk_count}: {content[:50]}...")
                            elif msg_type == 'done':
                                print(f"   ✅ 搜索完成，共 {chunk_count} 个数据块")
                            elif msg_type == 'error':
                                print(f"   ❌ 搜索错误: {content}")
                        except json.JSONDecodeError:
                            pass

            total_content = ''.join(content_parts)
            print(f"   📊 总内容长度: {len(total_content)} 字符")
        else:
            print(f"❌ 本地搜索流式查询失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 本地搜索流式查询异常: {e}")

    print("\n🎉 API 测试完成！")

def print_api_endpoints():
    """打印所有可用的 API 端点"""
    print("📋 GraphRAG API 端点列表:\n")

    endpoints = [
        ("POST", "/graphrag/query", "全局搜索查询"),
        ("POST", "/graphrag/query/stream", "全局搜索流式查询"),
        ("POST", "/graphrag/local-search", "本地搜索查询"),
        ("POST", "/graphrag/local-search/stream", "本地搜索流式查询"),
        ("GET", "/graphrag/health", "健康检查")
    ]

    for method, path, description in endpoints:
        print(f"  {method:<6} {path:<35} - {description}")

    print()

if __name__ == "__main__":
    print_api_endpoints()

    # 检查服务器是否运行
    print("⚠️  请确保 FastAPI 服务器在 http://localhost:8000 运行")
    print("   启动命令: uvicorn app.main:app --reload\n")

    input("按回车键开始测试...")
    test_local_search_api()