"""
搜索服务模块
提供各种搜索功能，包括QA搜索、文档搜索、混合搜索等
"""

import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text

from app.core.rag.database_operations import DatabaseOperations
from app.core.rag.scoring_algorithms import ScoringAlgorithms, SearchConfig
from app.core.embeddings_utils import get_text_embeddings
from app.config.llm_client import embedding_client,rerank_client_instance
from app.config.database import global_schema

class RAGSearch:
    """专用于RAG的搜索策略"""
    
    def __init__(self) -> None:
        self.embedding_client = embedding_client
    


    def _vector_similarity_search(self, 
                                  query_embedding: List[float],
                                  table_name: str = f'{global_schema}.indexed_knowledge',
                                  similarity_threshold: float = 0.8, 
                                  top_k: int = 20) -> List[Dict]:
        """
        向量相似度搜索

        Args:
            query_embedding: 查询向量
            table_name: 表名
            similarity_threshold: 相似度阈值
            top_k: 返回的结果数量

        Returns:
            向量搜索结果列表
        """
        emb_str = DatabaseOperations.format_embedding_vector(query_embedding)
        sql = text(f"""
            SELECT
                knowledge_id as id,
                title as question,
                content as answer,
                reference,
                1 - (q_embedding <=> :query_vector) AS similarity_score
            FROM {table_name}
            WHERE 1 - (q_embedding <=> :query_vector) >= :threshold
            AND status <>'P'
            ORDER BY similarity_score DESC
            LIMIT :top_k
        """)

        params = {
            "query_vector": emb_str,
            "threshold": similarity_threshold,
            "top_k": top_k
        }

        result = DatabaseOperations.execute_search(sql, params)

        return [
            {
                "id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "vec_score": float(row["similarity_score"]),
                "source": "vector"
            }
            for row in result
        ]


    def _fts_search_pg(self, query):
        """FTS全文搜索"""

        sql = text(f"""
        SELECT knowledge_id as id,title as question, content as answer,reference,
                   RANK() OVER (ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC) AS fts_rank
        FROM {global_schema}.indexed_knowledge
        WHERE fts @@ websearch_to_tsquery('zhparsercfg', :query_text)
        AND status <>'P'
        ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC
        LIMIT 30
        """)

        params = {
            "query_text": query
        }

        result = DatabaseOperations.execute_search(sql, params)

        return [
            {
            "id": row["id"], 
            "question": row["question"], 
            "answer": row["answer"],
            "hybrid_score": row["hybrid_score"]
            } for row in result
            ]

    def _bm25_search_pg(self,
                        query: str,
                        table_name: str = f'{global_schema}.indexed_knowledge',
                        b: float = 0.75,
                        top_k: int = 20):
        """bm25搜索"""
        # 获取集合统计信息
        avg_doc_length, total_docs = DatabaseOperations.get_index_knowledge_collection_stats()
        # 构建查询词的 tsquery
        query_ts = f"websearch_to_tsquery('zhparsercfg', :query_text)"

        # 简化的 BM25 实现 - 使用 ts_rank_cd 作为基础，结合文档长度归一化
        sql = text(f"""
            SELECT
                knowledge_id as id,
                title as question,
                content as answer,
                reference,
                -- 简化的 BM25 评分：ts_rank_cd + 文档长度归一化
                (ts_rank_cd(fts, {query_ts}, 32) *
                 (LOG({total_docs} + 1) / (1 + LOG(1 + :b * (LENGTH(content) / {avg_doc_length}))))) AS bm25_score
            FROM {table_name}
            WHERE fts @@ {query_ts}
            AND status <>'P'
            ORDER BY bm25_score DESC
            LIMIT :top_k
        """)

        params = {
            "query_text": query,
            "top_k": top_k,
            "b": b
        }

        result = DatabaseOperations.execute_search(sql, params)

        return [
            {
                "id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "bm25_score": float(row["bm25_score"]),
                "source": "bm25"
            }
            for row in result
        ]
    
    
    def _rerank_results(self,
                        query: str,
                        search_results: List[Dict],
                        top_k: int = 10) -> List[Dict]:
        """
        使用rerank模型对搜索结果进行重新排序

        Args:
            query: 原始查询
            search_results: 搜索结果列表
            top_k: 返回前k个结果

        Returns:
            rerank后的结果列表
        """
        if not search_results:
            return []

        # 准备用于rerank的文本 - 结合问题和答案
        texts_to_rerank = []
        for result in search_results:
            # 组合问题+答案作为rerank的内容，提高相关性
            combined_text = f"问题: {result['question']}\n答案: {result['answer']}"
            texts_to_rerank.append(combined_text)

        try:
            # 调用rerank API
            rerank_results = rerank_client_instance.rerank_sync(query, texts_to_rerank)

            if not rerank_results:
                # 如果rerank失败，返回原始结果
                logging.warning("Rerank failed, returning original search results")
                return search_results[:top_k]

            # 创建原始结果到rerank分数的映射
            rerank_scores = {}
            for item in rerank_results:
                if "index" in item and "score" in item:
                    original_index = item["index"]
                    if original_index < len(search_results):
                        rerank_scores[original_index] = item["score"]

            # 重新组织结果，添加rerank分数
            reranked_results = []
            for i, result in enumerate(search_results):
                result_copy = result.copy()
                if i in rerank_scores:
                    result_copy["rerank_score"] = rerank_scores[i]
                else:
                    result_copy["rerank_score"] = 0.0
                reranked_results.append(result_copy)

            # 按rerank分数排序
            reranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)

            logging.info(f"Reranked {len(reranked_results)} results, returning top {top_k}")
            return reranked_results[:top_k]

        except Exception as e:
            logging.error(f"Rerank error: {e}")
            # 发生异常时返回原始结果
            return search_results[:top_k]

    def hybrid_search_with_rerank(self,
                                  query: str,
                                  vector_weight: float = 0.7,
                                  bm25_weight: float = 0.3,
                                  similarity_threshold: float = 0.7,
                                  top_k: int = 10) -> List[Dict]:
        """
        混合搜索 + Rerank，结合向量和BM25搜索，然后使用rerank重新排序

        Args:
            query: 查询文本
            vector_weight: 向量搜索权重
            bm25_weight: BM25搜索权重
            similarity_threshold: 向量相似度阈值
            top_k: 返回结果数量

        Returns:
            经过rerank的搜索结果
        """
        # 并行执行向量和BM25搜索
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 向量搜索
            query_embedding = get_text_embeddings(embedding_client, query)
            vector_future = executor.submit(
                self._vector_similarity_search,
                query_embedding,
                similarity_threshold=similarity_threshold,
                top_k=20
            )

            # BM25搜索
            bm25_future = executor.submit(
                self._bm25_search_pg,
                query,
                top_k=20
            )

            # 获取结果
            vector_results = vector_future.result()
            bm25_results = bm25_future.result()

        # 使用ScoringAlgorithms进行结果融合
        scorer = ScoringAlgorithms()
        hybrid_results = scorer.merge_with_rrf(
            bm25_results,
            vector_results,
            weight_bm25=bm25_weight,
            weight_vec=vector_weight
        )

        # 使用rerank重新排序
        final_results = self._rerank_results(query, hybrid_results, top_k)

        return final_results

    def _knowledge_graph_search(self,
                                query: str) -> Dict:
        """
        知识图谱搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            enable_rerank: 是否启用重排序
            reuse_context: 是否尝试复用已缓存的context

        Returns:
            知识图谱搜索结果列表
        """
        try:
            # 调用知识图谱搜索接口
            from app.core.graph.search_engine import get_local_search_context
            # 第1步：调用知识图谱搜索接口，获取原始上下文数据
            graph_context, system_prompt = get_local_search_context(query)
            
            # 第2步：从上下文中提取各类记录数据
            graph_records = graph_context.context_records

            entities = graph_records.get("entities",None)
            relationships = graph_records.get("relationships",None)
            communities = graph_records.get("communities", None)
            community_reports = graph_records.get("community_reports", None)
            sources = graph_records.get("sources", None)

            result = {
            "status": "success",
            "query": query,
            "context_info": {
                    "entities":entities,
                    "relationships":relationships,
                    "communities": communities,
                    "community_reports": community_reports,
                    "sources":sources,
                    },
            }
            return result
            

        except Exception as e:
            logging.error(f"知识图谱搜索失败: {e}")
            return {}

