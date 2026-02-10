"""
评分算法模块
包含BM25评分、RRF融合算法等搜索评分相关算法
"""

from typing import List, Dict


class ScoringAlgorithms:
    """评分算法类"""

    @staticmethod
    def calculate_bm25_score(term_freq: int, doc_length: int, avg_doc_length: float,
                            k1: float = 1.2, b: float = 0.75) -> float:
        """
        计算 BM25 评分的核心函数

        Args:
            term_freq: 词项在文档中的频率
            doc_length: 文档长度
            avg_doc_length: 平均文档长度
            k1: 控制词频饱和度的参数
            b: 控制文档长度归一化的参数

        Returns:
            BM25评分
        """
        numerator = term_freq * (k1 + 1)
        denominator = term_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
        return numerator / denominator

    @staticmethod
    def merge_with_rrf(bm25_results: List[Dict], vec_results: List[Dict],
                      k: int = 60, weight_bm25: float = 0.4, weight_vec: float = 0.6) -> List[Dict]:
        """
        使用 RRF (Reciprocal Rank Fusion) 算法融合 BM25 和向量搜索结果

        Args:
            bm25_results: BM25 搜索结果
            vec_results: 向量搜索结果
            k: RRF 平滑参数
            weight_bm25: BM25 权重
            weight_vec: 向量搜索权重

        Returns:
            融合后的搜索结果列表
        """
        doc_scores = {}
        doc_data = {}

        # BM25 结果评分
        for rank, doc in enumerate(bm25_results, 1):
            doc_id = doc["id"]
            rrf_score = 1.0 / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + weight_bm25 * rrf_score
            doc_data[doc_id] = {
                "question": doc["question"],
                "answer": doc["answer"],
                "reference": doc.get("reference", ""),
                "bm25_score": doc["bm25_score"]
            }

        # 向量结果评分
        for rank, doc in enumerate(vec_results, 1):
            doc_id = doc["id"]
            rrf_score = 1.0 / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + weight_vec * rrf_score

            if doc_id in doc_data:
                doc_data[doc_id]["vec_score"] = doc["vec_score"]
            else:
                doc_data[doc_id] = {
                    "question": doc["question"],
                    "answer": doc["answer"],
                    "reference": doc.get("reference", ""),
                    "vec_score": doc["vec_score"]
                }

        # 合并结果并排序
        merged_results = []
        for doc_id, hybrid_score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
            result = {
                "id": doc_id,
                "question": doc_data[doc_id]["question"],
                "answer": doc_data[doc_id]["answer"],
                "reference": doc_data[doc_id]["reference"],
                "hybrid_score": 100*hybrid_score,
                "bm25_score": doc_data[doc_id].get("bm25_score", 0.0),
                "vec_score": doc_data[doc_id].get("vec_score", 0.0)
            }
            merged_results.append(result)

        return merged_results


class SearchConfig:
    """搜索配置类"""

    # 文档搜索配置
    DOC_SEARCH_CONFIG = {
        "bm25": {
            "b": 0.75,              # BM25 参数 b（文档长度归一化）
            "top_k": 20
        },
        "vector": {
            "similarity_threshold": 0.8,
            "top_k": 20
        },
        "rrf": {
            "k": 60,               # RRF 平滑参数
            "weight_bm25": 0.4,    # BM25 权重
            "weight_vec": 0.6,     # 向量搜索权重
            "final_top_k": 3
        }
    }

    # QA搜索配置
    QA_SEARCH_CONFIG = {
        "bm25": {
            "b": 0.75,
            "top_k": 20
        },
        "vector": {
            "similarity_threshold": 0.95,
            "top_k": 1
        },
        "rrf": {
            "k": 60,
            "weight_fts": 0.4,
            "weight_vec": 0.6,
            "final_top_k": 5
        }
    }