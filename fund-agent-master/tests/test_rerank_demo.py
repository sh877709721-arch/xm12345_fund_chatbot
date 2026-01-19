"""
Rerank 客户端使用示例
展示如何封装和使用 rerank API
"""

import json
from typing import List, Dict, Any

class RerankClientDemo:
    """Rerank 客户端演示类"""

    def __init__(self, base_url: str = "http://127.0.0.1/api/bge-reranker/v1", api_key: str = ""):
        """
        初始化 Rerank 客户端

        Args:
            base_url: API 基础URL
            api_key: API密钥（可选）
        """
        self.base_url = base_url
        self.api_key = api_key

    def rerank(self, query: str, texts: List[str], top_n: int = None) -> Dict[str, Any]:
        """
        调用 rerank API 对文本进行重新排序

        Args:
            query: 查询文本
            texts: 待排序的文本列表
            top_n: 返回前N个结果，可选

        Returns:
            包含重新排序结果的字典
        """
        # 构建请求URL
        url = f"{self.base_url}/rerank"

        # 构建请求头
        headers = {
            "Content-Type": "application/json"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 构建请求数据
        request_data = {
            "query": query,
            "texts": texts
        }

        if top_n is not None:
            request_data["top_n"] = top_n

        # 打印请求信息（用于演示）
        print(f"请求URL: {url}")
        print(f"请求头: {headers}")
        print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

        # 这里应该是实际的HTTP请求代码
        # response = requests.post(url, json=request_data, headers=headers)
        # return response.json()

        # 模拟返回结果（用于演示）
        mock_response = {
            "results": [
                {
                    "index": 0,
                    "text": texts[0],
                    "relevance_score": 0.95
                },
                {
                    "index": 2,
                    "text": texts[2],
                    "relevance_score": 0.87
                },
                {
                    "index": 4,
                    "text": texts[4],
                    "relevance_score": 0.82
                }
            ]
        }

        return mock_response

    def get_top_texts(self, query: str, texts: List[str], top_n: int = 5) -> List[str]:
        """
        获取重新排序后的前N个文本

        Args:
            query: 查询文本
            texts: 待排序的文本列表
            top_n: 返回前N个结果，默认5

        Returns:
            重新排序后的文本列表
        """
        result = self.rerank(query, texts, top_n)

        # 提取排序后的文本
        if "results" in result:
            return [item["text"] for item in result["results"]]
        elif "data" in result:
            return [item["text"] for item in result["data"]]
        else:
            # 如果返回格式不符合预期，返回原始文本列表
            return texts[:top_n]

def demonstrate_rerank_usage():
    """演示 rerank 客户端的使用"""
    print("=== Rerank 客户端使用演示 ===\n")

    # 创建客户端实例
    client = RerankClientDemo()

    # 示例查询和文本
    query = "什么是深度学习？"
    texts = [
        "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的复杂模式。",
        "深度学习不是什么神奇的技术，它只是统计学的一个应用分支。",
        "深度学习依赖于大量标注数据和强大的计算资源来训练模型。",
        "传统的机器学习算法需要手动设计特征，而深度学习可以自动学习特征表示。",
        "深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。"
    ]

    print(f"查询: {query}")
    print(f"文本数量: {len(texts)}")
    print("\n原始文本:")
    for i, text in enumerate(texts, 1):
        print(f"{i}. {text}")

    print("\n" + "="*60)
    print("调用 rerank API:")

    # 调用 rerank API
    result = client.rerank(query, texts, top_n=3)

    print("\nAPI 响应:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n" + "="*60)
    print("获取排序后的文本:")

    # 获取排序后的文本
    sorted_texts = client.get_top_texts(query, texts, top_n=3)

    print("\n重新排序后的文本 (前3个):")
    for i, text in enumerate(sorted_texts, 1):
        print(f"{i}. {text}")

def show_curl_equivalent():
    """展示等效的 curl 命令"""
    print("\n" + "="*60)
    print("等效的 curl 命令:")

    curl_command = '''curl http://127.0.0.1/api/bge-reranker/v1/rerank \\
    -X POST \\
    -d '{"query": "什么是深度学习？", "texts": ["深度学习是机器学习的一个子领域...", "深度学习依赖于大量标注数据..."]}' \\
    -H 'Content-Type: application/json'

# 如果有API密钥，添加认证头：
curl http://127.0.0.1/api/bge-reranker/v1/rerank \\
    -X POST \\
    -d '{"query": "什么是深度学习？", "texts": ["深度学习是机器学习的一个子领域..."]}' \\
    -H 'Content-Type: application/json' \\
    -H 'Authorization: Bearer YOUR_API_KEY'
'''

    print(curl_command)

def show_python_requests_equivalent():
    """展示等效的 Python requests 代码"""
    print("\n" + "="*60)
    print("等效的 Python requests 代码:")

    python_code = '''
import requests

# 基本请求
url = "http://127.0.0.1/api/bge-reranker/v1/rerank"
headers = {"Content-Type": "application/json"}
data = {
    "query": "什么是深度学习？",
    "texts": [
        "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的复杂模式。",
        "深度学习不是什么神奇的技术，它只是统计学的一个应用分支。"
    ]
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result)

# 带API密钥的请求
headers_with_auth = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.post(url, json=data, headers=headers_with_auth)
result = response.json()
print(result)
'''

    print(python_code)

if __name__ == '__main__':
    # 运行演示
    demonstrate_rerank_usage()
    show_curl_equivalent()
    show_python_requests_equivalent()

    print("\n" + "="*60)
    print("实际使用说明:")
    print("1. 确保 rerank API 服务在指定地址运行")
    print("2. 在 app/config/llm_client.py 中已提供了完整的客户端实现")
    print("3. 使用 rerank_client_instance.rerank_sync() 进行同步调用")
    print("4. 使用 rerank_client_instance.rerank_async() 进行异步调用")
    print("5. 使用 rerank_client_instance.get_top_results() 直接获取排序结果")