
class RerankClient:
    """Rerank 客户端封装类"""

    def __init__(self, base_url: str = None, api_key: str = None):
        """
        初始化 Rerank 客户端

        Args:
            base_url: API 基础URL，默认使用 localhost:9000
            api_key: API密钥，默认使用 settings.API_KEY
        """
        self.base_url = base_url or "http://localhost:9000"
        self.api_key = api_key or ""

    async def rerank_async(self, query: str, texts: list[str]) -> list:
        """
        异步调用 rerank API

        Args:
            query: 查询文本
            texts: 待排序的文本列表

        Returns:
            重新排序结果列表，格式：[{"index": int, "score": float}, ...]
        """
        import aiohttp

        url = f"{self.base_url}/rerank"
        headers = {
            "Content-Type": "application/json"
        }

        request_data = {
            "query": query,
            "texts": texts
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Request failed with status {response.status}")
                        print(f"Response: {await response.text()}")
                        return []

        except Exception as e:
            print(f"Rerank async request error: {e}")
            return []

    def rerank_sync(self, query: str, texts: list[str]) -> list:
        """
        同步调用 rerank API

        Args:
            query: 查询文本
            texts: 待排序的文本列表

        Returns:
            重新排序结果列表，格式：[{"index": int, "score": float}, ...]
        """
        import requests

        url = f"{self.base_url}/rerank"
        headers = {
            "Content-Type": "application/json"
        }

        request_data = {
            "query": query,
            "texts": texts
        }

        try:
            response = requests.post(url, json=request_data, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return []

        except Exception as e:
            print(f"Rerank sync request error: {e}")
            return []

    def get_top_results(self, query: str, texts: list[str], top_n: int = 5) -> list[str]:
        """
        获取重新排序后的前N个文本

        Args:
            query: 查询文本
            texts: 待排序的文本列表
            top_n: 返回前N个结果，默认5

        Returns:
            重新排序后的文本列表
        """
        rerank_results = self.rerank_sync(query, texts)

        if not rerank_results:
            # 如果 rerank 失败，返回原始文本列表
            return texts[:top_n]

        # 根据API返回格式提取排序后的文本
        sorted_texts = []
        for item in rerank_results:
            if item["index"] < len(texts):
                sorted_texts.append(texts[item["index"]])

        return sorted_texts[:top_n]