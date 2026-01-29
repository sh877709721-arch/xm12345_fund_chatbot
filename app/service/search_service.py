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
from app.config.llm_client import embedding_client
from app.config.database import global_schema



class SearchService:
    """搜索服务类"""

    @staticmethod
    def get_query_embedding(query: str, model: str = 'bge-m3') -> List[float]:
        """
        获取查询文本的嵌入向量

        Args:
            query: 查询文本
            model: 嵌入模型名称，默认为 'bge-m3'

        Returns:
            嵌入向量列表
        """
        response = embedding_client.embeddings.create(
            input=query,
            model=model
        )
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return sorted_data[0].embedding

    @staticmethod
    def qa_response(query: str, score: float=0.95, top_n:int=1) -> List[Dict]:
        """
        QA知识库精确匹配搜索

        Args:
            query: 查询文本

        Returns:
            搜索结果列表
        """
        # 1. 获取嵌入
        embedding = get_text_embeddings(embedding_client, query)

        # 2. 构造 emb 字符串为 PostgreSQL vector 格式
        emb = DatabaseOperations.format_embedding_vector(embedding)

        # 3. 构造 SQL（使用单次 similarity 计算）
        sql = text(f"""
            SELECT
                knowledge_id as id,
                title as question,
                content as answer,
                reference,
                1 - (q_embedding <=> '{emb}'::vector) AS hybrid_score
            FROM {global_schema}.indexed_knowledge
            WHERE
                1 - (q_embedding <=> '{emb}'::vector) >= {score}
                AND knowledge_type = 'qa'
                AND status <>'P'
            ORDER BY hybrid_score DESC
            LIMIT {top_n}
        """)
        return DatabaseOperations.execute_search(sql)

    @staticmethod
    def qa_hybrid_search_vec_rff(query: str) -> List[Dict]:
        """
        QA知识库混合搜索（全文搜索 + 向量搜索）

        Args:
            query: 查询文本

        Returns:
            混合搜索结果列表
        """
        # 1. 获取嵌入
        embedding = SearchService.get_query_embedding(query)
        emb = DatabaseOperations.format_embedding_vector(embedding)

        # 2. 构建混合搜索SQL
        sql = text(f"""
          WITH
            fts_results AS (
              SELECT
                knowledge_id as id,title as question, content as answer,reference,
                RANK() OVER (ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC) AS fts_rank
              FROM {global_schema}.indexed_knowledge
              WHERE fts @@ websearch_to_tsquery('zhparsercfg', :query_text)
                AND knowledge_type = 'qa'
                AND status <>'P'
              ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC
              LIMIT 20
            ),
            vec_results AS (
              SELECT
                knowledge_id as id,title as question, content as answer,reference,
                RANK() OVER (ORDER BY q_embedding <=> :query_vector) AS vec_rank
              FROM {global_schema}.indexed_knowledge
                where knowledge_type = 'qa'
                AND status <>'P'
              ORDER BY q_embedding <=> :query_vector
              LIMIT 20
            ),
            combined AS (
              SELECT
                COALESCE(f.id, v.id) AS id,
                COALESCE(f.question, v.question) AS question,
                COALESCE(f.answer, v.answer) AS answer,
                COALESCE(f.reference, v.reference) AS reference,
                COALESCE((1.0 / (:rrf_k + f.fts_rank))::FLOAT, 0.0) AS fts_rrf,
                COALESCE((1.0 / (:rrf_k + v.vec_rank))::FLOAT, 0.0) AS vec_rrf
              FROM fts_results f
              FULL OUTER JOIN vec_results v ON f.id = v.id
            )
            SELECT id, question, answer,reference,
                   (:weight_fts * fts_rrf + :weight_vec * vec_rrf) /
                   NULLIF(MAX(:weight_fts * fts_rrf + :weight_vec * vec_rrf) OVER (), 0) AS hybrid_score
            FROM combined
            ORDER BY hybrid_score DESC
            LIMIT 5;
        """)

        params = {
            "query_text": query,
            "query_vector": emb,
            "rrf_k": 20,
            "weight_fts": 0.4,
            "weight_vec": 0.6
        }

        return DatabaseOperations.execute_rerank_query(sql, params)

    @staticmethod
    def doc_hybrid_search_vec_rff(query: str) -> List[Dict]:
        """
        文档知识库混合搜索（全文搜索 + 向量搜索）

        Args:
            query: 查询文本

        Returns:
            混合搜索结果列表
        """
        # 1. 获取嵌入
        embedding = get_text_embeddings(embedding_client, query)
        emb = DatabaseOperations.format_embedding_vector(embedding)

        # 2. 构建混合搜索SQL
        sql = text(f"""
           WITH
            fts_results AS (
              SELECT
                knowledge_id as id,title as question, content as answer, reference,
                RANK() OVER (ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC) AS fts_rank
              FROM {global_schema}.indexed_knowledge
              WHERE fts @@ websearch_to_tsquery('zhparsercfg', :query_text)
                AND status <>'P'
              ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC
              LIMIT 30
            ),
            vec_results AS (
              SELECT
                knowledge_id as id, title as question, content as answer, reference,
                RANK() OVER (ORDER BY
                  CASE knowledge_type
                    WHEN 'qa' THEN q_embedding <=> :query_vector
                    WHEN 'document' THEN a_embedding <=> :query_vector
                  END
                ) AS vec_rank
              FROM {global_schema}.indexed_knowledge
              WHERE status <>'P' AND knowledge_type IN ('qa', 'document')
              ORDER BY
                CASE knowledge_type
                  WHEN 'qa' THEN q_embedding <=> :query_vector
                  WHEN 'document' THEN a_embedding <=> :query_vector
                END
              LIMIT 30
            ),
            combined AS (
              SELECT
                COALESCE(f.id, v.id) AS id,
                COALESCE(f.question, v.question) AS question,
                COALESCE(f.answer, v.answer) AS answer,
                COALESCE(f.reference, v.reference) AS reference,
                COALESCE((1.0 / (:rrf_k + f.fts_rank))::FLOAT, 0.0) AS fts_rrf,
                COALESCE((1.0 / (:rrf_k + v.vec_rank))::FLOAT, 0.0) AS vec_rrf
              FROM fts_results f
              FULL OUTER JOIN vec_results v ON f.id = v.id
            )
            SELECT id, question, answer,reference,
                   (:weight_fts * fts_rrf + :weight_vec * vec_rrf) /
                   NULLIF(MAX(:weight_fts * fts_rrf + :weight_vec * vec_rrf) OVER (), 0) AS hybrid_score
            FROM combined
            ORDER BY hybrid_score DESC
            LIMIT 10;
        """)

        params = {
            "query_text": query,
            "query_vector": emb,
            "rrf_k": 30,
            "weight_fts": 0.4,
            "weight_vec": 0.6
        }

        result = DatabaseOperations.execute_search(sql, params)
        return [
            {
            "id": row["id"], 
            "question": row["question"], 
            "answer": row["answer"],
            "reference": row["reference"],
            "hybrid_score": row["hybrid_score"]
            } for row in result
            ]

    @staticmethod
    def doc_hybrid_search_vec_rff_with_rerank(query: str, top_n: int = 10) -> List[Dict]:
        """
        混合搜索 + Rerank 重排序

        Args:
            query: 查询文本
            top_n: 返回结果数量，默认10

        Returns:
            经过 rerank 重排序后的结果列表，格式与原函数一致
        """
        from app.config.llm_client import rerank_client_instance

        # 1. 执行混合搜索获取初始结果
        bm25_results = SearchService.doc_hybrid_search_bm25_vec(query)    
        fts_result = SearchService.doc_hybrid_search_vec_rff(query)
    
        initial_results = []

        # 添加BM25结果
        if bm25_results:
            initial_results.extend(bm25_results)
        if fts_result:
            initial_results.extend(fts_result)



        if not initial_results:
            return []

        # 2. 提取文档内容用于 rerank
        documents = []
        for result in initial_results:
            # 组合 title 和 answer 作为 rerank 的文本内容
            text_content = f"{result.get('title', '')} {result.get('answer', '')}".strip()
            documents.append(text_content)

        
        # 3. 调用 rerank API
        rerank_results = rerank_client_instance.rerank_sync(query, documents)

        # 4. 处理 rerank 结果
        if not rerank_results:
            # 如果 rerank 失败，返回原始结果
            print("Rerank failed, using original results")
            return initial_results[:top_n]

        # 5. 根据 rerank 结果重新排序
        reranked_docs = []
        for item in rerank_results:
            idx = item["index"]  # 原始文档的索引
            score = item.get("score", 0)

            if idx < len(initial_results):
                # 复制原始结果并更新分数
                reranked_doc = initial_results[idx].copy()
                reranked_doc["rerank_score"] = score
                reranked_docs.append(reranked_doc)

        return reranked_docs[:top_n]

    @staticmethod
    def doc_hybrid_search_vec_rff_with_fallback(query: str, top_n: int = 10, use_rerank: bool = True) -> List[Dict]:
        """
        混合搜索 + Rerank 重排序（带容错机制）

        Args:
            query: 查询文本
            top_n: 返回结果数量，默认10
            use_rerank: 是否使用 rerank，默认True

        Returns:
            经过处理后的结果列表，格式与原函数一致
        """
        try:
            if use_rerank:
                # 尝试使用 rerank
                return SearchService.doc_hybrid_search_vec_rff_with_rerank(query, top_n)
            else:
                # 直接返回混合搜索结果
                results = SearchService.doc_hybrid_search_vec_rff(query)
                return results[:top_n]

        except Exception as error:
            # 容错：如果 rerank 出现异常，返回原始搜索结果
            logging.error(f"使用rerank时发生错误: {error}")
            results = SearchService.doc_hybrid_search_vec_rff(query)
            return results[:top_n]

    @staticmethod
    def bm25_search_pg(query: str, table_name: str = f'{global_schema}.indexed_knowledge',
                       b: float = 0.75, top_k: int = 20) -> List[Dict]:
        """
        在 PostgreSQL 中实现简化版 BM25 搜索

        Args:
            query: 搜索查询
            table_name: 表名
            b: BM25 参数 b（文档长度归一化参数）
            top_k: 返回的结果数量

        Returns:
            BM25搜索结果列表
        """
        # 获取集合统计信息
        avg_doc_length, total_docs = DatabaseOperations.get_collection_stats(table_name)

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
                "reference": row["reference"],
                "bm25_score": float(row["bm25_score"]),
                "source": "bm25"
            }
            for row in result
        ]

    @staticmethod
    def vector_search(query_embedding: List[float], table_name: str = f'{global_schema}.indexed_knowledge',
                     similarity_threshold: float = 0.0, top_k: int = 20) -> List[Dict]:
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
                "reference": row["reference"],
                "vec_score": float(row["similarity_score"]),
                "source": "vector"
            }
            for row in result
        ]

    @staticmethod
    def doc_hybrid_search_bm25_vec(query: str, table_name: str = f'{global_schema}.indexed_knowledge') -> List[Dict]:
        """
        BM25 + 向量检索混合搜索（完整实现）

        Args:
            query: 搜索查询
            table_name: 表名

        Returns:
            融合后的搜索结果列表
        """
        config = SearchConfig.DOC_SEARCH_CONFIG

        # 1. 并行执行两种搜索
        with ThreadPoolExecutor(max_workers=2) as executor:
            # BM25 搜索
            bm25_future = executor.submit(
                SearchService.bm25_search_pg,
                query,
                table_name,
                config["bm25"]["b"],
                config["bm25"]["top_k"]
            )

            # 向量搜索
            embedding = get_text_embeddings(embedding_client, query)
            vec_future = executor.submit(
                SearchService.vector_search,
                embedding,
                table_name,
                config["vector"]["similarity_threshold"],
                config["vector"]["top_k"]
            )

        # 2. 获取搜索结果
        bm25_results = bm25_future.result()
        vec_results = vec_future.result()

        # 3. RRF 融合
        merged_results = ScoringAlgorithms.merge_with_rrf(
            bm25_results,
            vec_results,
            config["rrf"]["k"],
            config["rrf"]["weight_bm25"],
            config["rrf"]["weight_vec"]
        )

        # 4. 返回最终结果
        return merged_results[:config["rrf"]["final_top_k"]]


    @staticmethod
    def qa_hybrid_search_bm25_vec(query: str, table_name: str = f'{global_schema}.indexed_knowledge') -> List[Dict]:
        """
        QA 知识库的 BM25 + 向量检索混合搜索

        Args:
            query: 搜索查询
            table_name: QA 表名

        Returns:
            融合后的搜索结果列表
        """
        return SearchService.doc_hybrid_search_bm25_vec(query, table_name)