"""
向量搜索 + Rerank 集成使用示例
展示如何无缝集成到现有代码中
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def demonstrate_usage():
    """演示如何在实际代码中使用"""
    print("=== 向量搜索 + Rerank 集成使用示例 ===\n")

    print("1. 原始使用方式:")
    print("""
from app.core.vector import doc_hybrid_search_vec_rff

# 原始调用
results = doc_hybrid_search_vec_rff("医疗保险如何申请？")
print(f"搜索到 {len(results)} 个结果")
""")

    print("2. 带 Rerank 的使用方式:")
    print("""
from app.core.vector import doc_hybrid_search_vec_rff_with_rerank

# 带 rerank 的调用（返回格式完全相同）
results = doc_hybrid_search_vec_rff_with_rerank("医疗保险如何申请？", top_n=5)
print(f"Rerank 后有 {len(results)} 个结果")

# 每个结果现在多了一个 rerank_score 字段
for i, result in enumerate(results, 1):
    original_score = result.get('hybrid_score', 0)
    rerank_score = result.get('rerank_score', 0)
    print(f"{i}. 原始分数: {original_score:.3f}, Rerank分数: {rerank_score:.3f}")
""")

    print("3. 带容错机制的使用方式:")
    print("""
from app.core.vector import doc_hybrid_search_vec_rff_with_fallback

# 推荐使用：带容错机制
results = doc_hybrid_search_vec_rff_with_fallback(
    "医疗保险如何申请？",
    top_n=5,
    use_rerank=True  # 可以设为 False 来禁用 rerank
)

# 即使 rerank 服务故障，也能返回搜索结果
""")

    print("4. 在现有服务中集成:")
    print("""
class SearchService:
    def __init__(self):
        self.use_rerank = True  # 可以配置是否使用 rerank

    def search(self, query: str, top_n: int = 10):
        if self.use_rerank:
            return doc_hybrid_search_vec_rff_with_fallback(query, top_n, use_rerank=True)
        else:
            return doc_hybrid_search_vec_rff(query)[:top_n]
""")

def demonstrate_api_response_format():
    """演示 API 响应格式"""
    print("\n" + "="*60)
    print("响应格式对比:\n")

    print("原始函数返回格式:")
    print("""
[
    {
        "id": 1,
        "title": "文档标题",
        "answer": "文档内容",
        "hybrid_score": 0.95
    },
    ...
]
""")

    print("带 Rerank 后的返回格式:")
    print("""
[
    {
        "id": 1,
        "title": "文档标题",
        "answer": "文档内容",
        "hybrid_score": 0.95,      # 原始混合搜索分数
        "rerank_score": 0.98       # 新增：rerank 相关度分数
    },
    ...
]
""")

    print("兼容性说明:")
    print("- ✅ 完全向后兼容，现有代码无需修改")
    print("- ✅ 新增 rerank_score 字段，不影响现有逻辑")
    print("- ✅ 排序顺序可能改变，但结果结构保持一致")

def demonstrate_performance_benefits():
    """演示性能优势"""
    print("\n" + "="*60)
    print("Rerank 的优势:\n")

    print("1. 提升相关性:")
    print("   - 基于语义理解的精确匹配")
    print("   - 考虑查询意图和文档上下文")
    print("   - 减少关键词匹配的局限性")

    print("\n2. 动态排序:")
    print("   - 根据用户查询实时调整排序")
    print("   - 突出最相关的结果")
    print("   - 提升用户满意度")

    print("\n3. 容错机制:")
    print("   - API 故障时自动回退")
    print("   - 保证服务可用性")
    print("   - 无缝降级体验")

if __name__ == '__main__':
    demonstrate_usage()
    demonstrate_api_response_format()
    demonstrate_performance_benefits()

    print("\n" + "="*60)
    print("集成建议:")
    print("1. 使用 doc_hybrid_search_vec_rff_with_fallback() 作为主要搜索函数")
    print("2. 在配置中控制是否启用 rerank")
    print("3. 监控 rerank API 的性能和可用性")
    print("4. 可以比较 rerank 前后的效果来优化参数")