import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.llm_client import rerank_client_instance, RerankClient

def test_rerank_client():
    """测试 rerank 客户端功能"""
    print("=== 测试 Rerank 客户端 ===")

    # 测试数据
    query = "什么是深度学习？"
    texts = [
        "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的复杂模式。",
        "深度学习不是什么神奇的技术，它只是统计学的一个应用分支。",
        "深度学习依赖于大量标注数据和强大的计算资源来训练模型。",
        "传统的机器学习算法需要手动设计特征，而深度学习可以自动学习特征表示。",
        "深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。"
    ]

    print(f"\n查询: {query}")
    print(f"待排序文本数量: {len(texts)}")
    print("\n原始文本顺序:")
    for i, text in enumerate(texts, 1):
        print(f"{i}. {text}")

    # 测试同步调用
    print("\n" + "="*60)
    print("测试同步调用:")
    try:
        result = rerank_client_instance.rerank_sync(query, texts, top_n=3)
        print("同步调用结果:")
        print(f"状态: {'成功' if 'error' not in result else '失败'}")

        if 'error' not in result:
            print("完整响应:", result)

            # 提取排序后的文本
            if "results" in result:
                sorted_texts = [item["text"] for item in result["results"]]
                scores = [item.get("relevance_score", item.get("score", 0)) for item in result["results"]]
                print("\n重新排序后的文本:")
                for i, (text, score) in enumerate(zip(sorted_texts, scores), 1):
                    print(f"{i}. [相关度: {score:.4f}] {text}")
        else:
            print("错误信息:", result)
    except Exception as e:
        print(f"同步调用异常: {e}")

    # 测试便捷方法
    print("\n" + "="*60)
    print("测试便捷方法 get_top_results:")
    try:
        top_texts = rerank_client_instance.get_top_results(query, texts, top_n=3)
        print("获取前3个最相关的文本:")
        for i, text in enumerate(top_texts, 1):
            print(f"{i}. {text}")
    except Exception as e:
        print(f"便捷方法调用异常: {e}")

    # 测试自定义客户端
    print("\n" + "="*60)
    print("测试自定义客户端:")
    try:
        custom_client = RerankClient(
            base_url="http://127.0.0.1/api/bge-reranker/v1",
            api_key="test_key"
        )
        print(f"自定义客户端基础URL: {custom_client.base_url}")
        print(f"自定义客户端API密钥: {custom_client.api_key[:10]}...")

        # 这里只是测试配置，不实际调用API
        print("自定义客户端配置成功")
    except Exception as e:
        print(f"自定义客户端配置异常: {e}")

def test_curl_equivalent():
    """展示与 curl 命令等效的Python代码"""
    print("\n" + "="*60)
    print("等效 curl 命令的 Python 实现:")

    print("\n原始 curl 命令:")
    print('''curl http://127.0.0.1/api/bge-reranker/v1/rerank \\
    -X POST \\
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \\
    -H 'Content-Type: application/json' ''')

    print("\n等效的 Python 代码:")
    print('''import requests

url = "http://127.0.0.1/api/bge-reranker/v1/rerank"
headers = {"Content-Type": "application/json"}
data = {
    "query": "What is Deep Learning?",
    "texts": [
        "Deep Learning is not...",
        "Deep learning is..."
    ]
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result)''')

if __name__ == '__main__':
    # 注意：实际运行需要API服务可用
    # 这里主要展示客户端的使用方法
    test_rerank_client()
    test_curl_equivalent()

    print("\n" + "="*60)
    print("使用说明:")
    print("1. 确保API服务在 http://127.0.0.1/api/bge-reranker/v1 可用")
    print("2. 根据实际情况修改 settings.BASE_URL")
    print("3. 可以使用 rerank_client_instance.rerank_sync() 进行同步调用")
    print("4. 可以使用 rerank_client_instance.rerank_async() 进行异步调用")
    print("5. 使用 get_top_results() 方法直接获取排序后的文本列表")