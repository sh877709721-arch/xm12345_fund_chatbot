import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config.settings import Settings
import logging
# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


from app.core.vector import doc_hybrid_search_bm25_vec,qa_hybrid_search_bm25_vec

def example_usage():
    """
    使用示例
    """
    # 示例查询
    query = "异地就医备案"

    # 使用 BM25 + 向量混合搜索（文档知识库）
    doc_results = doc_hybrid_search_bm25_vec(query, 'chatbot.doc_knowledge')
    print("文档知识库搜索结果:")
    for i, result in enumerate(doc_results, 1):
        print(f"{i}. 标题: {result['question']}")
        print(f"   混合评分: {result['hybrid_score']:.4f}")
        print(f"   BM25评分: {result['bm25_score']:.4f}")
        print(f"   向量评分: {result['vec_score']:.4f}")
        print(f"   回答: {result['answer'][:100]}...")
        print()

    # 使用 BM25 + 向量混合搜索（QA知识库）
    # qa_results = qa_hybrid_search_bm25_vec(query, 'chatbot.qa_knowledge')
    # print("QA知识库搜索结果:")
    # for i, result in enumerate(qa_results, 1):
    #     print(f"{i}. 问题: {result['question']}")
    #     print(f"   混合评分: {result['hybrid_score']:.4f}")
    #     print(f"   BM25评分: {result['bm25_score']:.4f}")
    #     print(f"   向量评分: {result['vec_score']:.4f}")
    #     print(f"   回答: {result['answer'][:100]}...")
    #     print()


if __name__ == "__main__":
    example_usage()