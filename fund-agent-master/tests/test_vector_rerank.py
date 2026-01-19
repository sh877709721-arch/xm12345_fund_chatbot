import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_vector_rerank():
    """测试向量搜索 + rerank 功能"""
    print("=== 测试向量搜索 + Rerank 功能 ===")

    # 模拟原函数的返回结果格式
    def mock_doc_hybrid_search_vec_rff(query: str):
        """模拟 doc_hybrid_search_vec_rff 函数的返回结果"""
        return [
            {
                "id": 1,
                "title": "医疗保险申请流程",
                "answer": "个人可以通过线上平台或线下窗口申请医疗保险，需要准备身份证、户口本等材料。",
                "hybrid_score": 0.95
            },
            {
                "id": 2,
                "title": "医疗保险报销比例",
                "answer": "不同等级医院的报销比例不同，一级医院报销90%，二级医院85%，三级医院80%。",
                "hybrid_score": 0.88
            },
            {
                "id": 3,
                "title": "失业保险金申领条件",
                "answer": "失业保险金申领需要满足缴纳失业保险满一年、非因本人意愿中断就业等条件。",
                "hybrid_score": 0.75
            },
            {
                "id": 4,
                "title": "医疗保险异地就医",
                "answer": "参保人员在异地就医可以享受直接结算服务，需要提前办理异地就医备案。",
                "hybrid_score": 0.72
            },
            {
                "id": 5,
                "title": "养老保险缴费标准",
                "answer": "养老保险缴费基数根据社会平均工资确定，个人缴费比例为8%，单位缴费比例为16%。",
                "hybrid_score": 0.68
            }
        ]

    def mock_rerank_client(query: str, documents: list[str], top_n: int = None):
        """模拟 rerank 客户端的响应"""
        # 模拟 rerank API 返回结果
        return {
            "results": [
                {
                    "index": 0,  # 第一个文档最相关
                    "text": documents[0],
                    "relevance_score": 0.98
                },
                {
                    "index": 3,  # 第四个文档第二相关
                    "text": documents[3],
                    "relevance_score": 0.85
                },
                {
                    "index": 1,  # 第二个文档第三相关
                    "text": documents[1],
                    "relevance_score": 0.78
                },
                {
                    "index": 2,
                    "text": documents[2],
                    "relevance_score": 0.65
                },
                {
                    "index": 4,
                    "text": documents[4],
                    "relevance_score": 0.45
                }
            ]
        }

    # 重写 rerank 函数用于测试
    def doc_hybrid_search_vec_rff_with_rerank(query: str, top_n: int = 10):
        """测试版本的混合搜索 + rerank 函数"""
        # 1. 执行混合搜索获取初始结果
        initial_results = mock_doc_hybrid_search_vec_rff(query)

        if not initial_results:
            return []

        # 2. 提取文档内容用于 rerank
        documents = []
        for result in initial_results:
            # 组合 title 和 answer 作为 rerank 的文本内容
            text_content = f"{result.get('title', '')} {result.get('answer', '')}".strip()
            documents.append(text_content)

        print(f"\n原始搜索结果（{len(initial_results)}个文档）:")
        for i, doc in enumerate(initial_results):
            print(f"{i+1}. [分数: {doc['hybrid_score']:.3f}] {doc['title']}")

        print(f"\n用于 rerank 的文档内容:")
        for i, doc in enumerate(documents):
            print(f"{i}. {doc[:50]}...")

        # 3. 调用 rerank API（模拟）
        rerank_result = mock_rerank_client(query, documents)

        print(f"\nRerank API 响应:")
        for item in rerank_result["results"]:
            idx = item["index"]
            score = item["relevance_score"]
            print(f"原始索引 {idx} -> 相关度 {score:.3f}")

        # 4. 根据 rerank 结果重新排序
        if "results" in rerank_result:
            reranked_results = []

            for item in rerank_result["results"]:
                idx = item["index"]  # 原始文档的索引
                score = item.get("relevance_score", item.get("score", 0))

                if idx < len(initial_results):
                    # 复制原始结果并更新分数
                    reranked_doc = initial_results[idx].copy()
                    reranked_doc["rerank_score"] = score
                    reranked_results.append(reranked_doc)

            return reranked_results[:top_n]
        else:
            return initial_results[:top_n]

    # 测试查询
    test_query = "医疗保险如何申请？"
    print(f"测试查询: {test_query}")

    # 执行带 rerank 的搜索
    final_results = doc_hybrid_search_vec_rff_with_rerank(test_query, top_n=3)

    print(f"\n" + "="*60)
    print("Rerank 重排序后的最终结果（前3个）:")

    for i, doc in enumerate(final_results, 1):
        original_score = doc.get("hybrid_score", 0)
        rerank_score = doc.get("rerank_score", 0)
        print(f"\n{i}. {doc['title']}")
        print(f"   原始混合搜索分数: {original_score:.3f}")
        print(f"   Rerank 相关度分数: {rerank_score:.3f}")
        print(f"   内容: {doc['answer'][:100]}...")

def test_fallback_mechanism():
    """测试容错机制"""
    print("\n" + "="*60)
    print("测试容错机制:")

    def mock_rerank_with_error(query: str, documents: list[str], top_n: int = None):
        """模拟 rerank API 出错"""
        return {
            "error": "API service unavailable",
            "details": "Connection timeout"
        }

    def doc_hybrid_search_vec_rff_with_rerank_fallback(query: str):
        """带容错的 rerank 函数"""
        initial_results = [
            {
                "id": 1,
                "title": "原始搜索结果1",
                "answer": "这是第一个搜索结果",
                "hybrid_score": 0.90
            }
        ]

        documents = ["文档内容1"]

        # 模拟 API 调用失败
        rerank_result = mock_rerank_with_error(query, documents)

        if "error" in rerank_result:
            print(f"Rerank 失败: {rerank_result['error']}")
            print("回退到原始搜索结果")
            return initial_results

        return []

    # 测试容错
    query = "测试查询"
    results = doc_hybrid_search_vec_rff_with_rerank_fallback(query)
    print(f"容错结果: {results}")

if __name__ == '__main__':
    # 运行测试
    test_vector_rerank()
    test_fallback_mechanism()

    print("\n" + "="*60)
    print("使用说明:")
    print("1. doc_hybrid_search_vec_rff_with_rerank() - 基本版本，执行混合搜索+rerank")
    print("2. doc_hybrid_search_vec_rff_with_fallback() - 带容错机制的版本")
    print("3. 两个函数的返回格式与原函数完全一致，确保兼容性")
    print("4. 在 rerank 分数字段中添加了 'rerank_score' 供参考")
    print("5. 如果 rerank 失败，会自动回退到原始搜索结果")