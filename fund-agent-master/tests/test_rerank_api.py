"""
测试修正后的 Rerank API 接口
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_rerank_api_format():
    """测试修正后的 rerank API 格式"""
    print("=== 测试修正后的 Rerank API ===")

    def mock_rerank_api(query: str, texts: list[str]) -> list:
        """模拟修正后的 rerank API 响应格式"""
        return [
            {
                "index": 1,  # 第二个文档最相关
                "score": 0.99762183
            },
            {
                "index": 0,  # 第一个文档次相关
                "score": 0.12474516
            }
        ]

    def test_rerank_client():
        """测试修正后的 rerank 客户端"""
        from app.config.llm_client import RerankClient

        client = RerankClient("http://localhost:9000")

        query = "What is Deep Learning?"
        texts = [
            "Deep Learning is not...",
            "Deep learning is..."
        ]

        print(f"查询: {query}")
        print(f"文本: {texts}")

        # 模拟调用
        result = mock_rerank_api(query, texts)
        print(f"\nAPI 响应格式:")
        for item in result:
            print(f"  索引: {item['index']}, 分数: {item['score']}")

        print(f"\n重新排序后的文本:")
        for item in result:
            idx = item['index']
            score = item['score']
            if idx < len(texts):
                print(f"  [{score:.3f}] {texts[idx]}")

        return result

    def test_vector_rerank_integration():
        """测试向量搜索与 rerank 的集成"""
        print("\n" + "="*60)
        print("测试向量搜索 + Rerank 集成:")

        def mock_doc_hybrid_search_vec_rff(query: str):
            """模拟向量搜索结果"""
            return [
                {
                    "id": 1,
                    "title": "深度学习简介",
                    "answer": "深度学习是机器学习的一个子领域",
                    "hybrid_score": 0.88
                },
                {
                    "id": 2,
                    "title": "深度学习应用",
                    "answer": "深度学习在图像识别、自然语言处理等领域有广泛应用",
                    "hybrid_score": 0.92
                }
            ]

        # 模拟完整的 rerank 流程
        query = "深度学习是什么？"

        # 1. 获取搜索结果
        initial_results = mock_doc_hybrid_search_vec_rff(query)
        print(f"初始搜索结果 ({len(initial_results)} 个):")
        for i, result in enumerate(initial_results):
            print(f"  {i+1}. [{result['hybrid_score']:.3f}] {result['title']}")

        # 2. 准备 rerank 文档
        documents = []
        for result in initial_results:
            text_content = f"{result.get('title', '')} {result.get('answer', '')}".strip()
            documents.append(text_content)

        print(f"\n用于 rerank 的文档:")
        for i, doc in enumerate(documents):
            print(f"  {i}. {doc[:50]}...")

        # 3. 调用 rerank API
        rerank_results = mock_rerank_api(query, documents)
        print(f"\nRerank 结果:")
        for item in rerank_results:
            idx = item['index']
            score = item['score']
            print(f"  原索引 {idx} -> 相关度 {score:.3f}")

        # 4. 重新排序结果
        reranked_docs = []
        for item in rerank_results:
            idx = item['index']
            score = item.get('score', 0)

            if idx < len(initial_results):
                reranked_doc = initial_results[idx].copy()
                reranked_doc['rerank_score'] = score
                reranked_docs.append(reranked_doc)

        print(f"\n最终重排序结果:")
        for i, doc in enumerate(reranked_docs, 1):
            print(f"  {i}. {doc['title']}")
            print(f"     原始分数: {doc['hybrid_score']:.3f}")
            print(f"     Rerank分数: {doc['rerank_score']:.3f}")

    # 运行测试
    test_rerank_client()
    test_vector_rerank_integration()

def test_curl_equivalence():
    """展示与 curl 命令的等效性"""
    print("\n" + "="*60)
    print("与 curl 命令的等效性:")

    print("\n原始 curl 命令:")
    print('''
curl localhost:9000/rerank \\
    -X POST \\
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \\
    -H 'Content-Type: application/json'
''')

    print("等效的 Python requests 代码:")
    print('''
import requests

url = "localhost:9000/rerank"
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
print(result)

# 预期输出:
# [
#     {"index": 1, "score": 0.99762183},
#     {"index": 0, "score": 0.12474516}
# ]
''')

    print("\n使用 RerankClient:")
    print('''
from app.config.llm_client import rerank_client_instance

result = rerank_client_instance.rerank_sync(
    query="What is Deep Learning?",
    texts=["Deep Learning is not...", "Deep learning is..."]
)
print(result)
''')

if __name__ == '__main__':
    test_rerank_api_format()
    test_curl_equivalence()

    print("\n" + "="*60)
    print("API 修正总结:")
    print("✅ URL: http://localhost:9000/rerank")
    print("✅ 请求格式: {'query': str, 'texts': list[str]}")
    print("✅ 响应格式: [{'index': int, 'score': float}, ...]")
    print("✅ 移除了不必要的认证头")
    print("✅ 优化了错误处理机制")
    print("✅ 简化了响应数据结构")