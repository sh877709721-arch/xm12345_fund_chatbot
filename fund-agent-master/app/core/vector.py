"""
    准备迁移到 search_service

"""

from app.config.database import SessionLocal,global_schema
from app.config.llm_client import embedding_client #,chat_client_small
from typing import Dict, List, Tuple
from app.core.embeddings_utils import get_text_embeddings
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
import logging

def execute_search(sql) -> List[Dict]:
    with SessionLocal() as session:
        result = session.execute(sql)
        rows = result.fetchall()
        if not rows:
            return []
        # 获取列名
        columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]
    


def qa_response(query: str,score: float=0.95, top_n:int=1) -> List[Dict]:
    # 1. 获取嵌入
    embedding = get_text_embeddings(embedding_client,query)


    # 2. 构造 emb 字符串为 PostgreSQL vector 格式 '[val1,val2,...]'
    emb = f'[{",".join(map(str, embedding))}]'

    # 3. 构造 SQL（使用单次 similarity 计算）
    sql = text(f"""
        SELECT 
            id, 
            title as question,
            content as answer,
            1 - (q_embedding <=> '{emb}'::vector) AS hybrid_score
        FROM {global_schema}.indexed_knowledge 
        WHERE 
            1 - (q_embedding <=> '{emb}'::vector) >= {score}
            and knowledge_type = 'qa'
            and status <>'P'
        ORDER BY hybrid_score DESC
        LIMIT {top_n}
    """)
    result = execute_search(sql)
    return result

def get_adaptive_similarity_threshold_with_fallback(
    query: str,
    used_id: int = -1,
    top_n: int = 3,
    initial_threshold: float = 0.94,
    fallback_thresholds: List[float] = [0.94, 0.90, 0.85],
    min_results: int = 1
) -> List[Dict]:
    """
    带阈值降级机制的相似度搜索

    Args:
        query: 查询文本
        used_id: 排除的ID列表
        top_n: 期望返回的结果数量
        initial_threshold: 初始相似度阈值
        fallback_thresholds: 降级阈值列表
        min_results: 最少返回结果数量

    Returns:
        搜索结果列表，包含相似度分数信息
    """
    # 1. 获取嵌入（只计算一次）
    embedding = get_text_embeddings(embedding_client, query)
    emb = f'[{",".join(map(str, embedding))}]'

    # 2. 构建所有候选阈值
    all_thresholds = [initial_threshold] + fallback_thresholds

    # 3. 记录已排除的ID，避免重复结果
    excluded_ids = set()
    if used_id:
        excluded_ids.add(used_id)

    final_results = []

    # 4. 逐步尝试不同阈值
    for threshold in all_thresholds:
        if len(final_results) >= top_n:
            break

        # 构建排除ID条件
        exclude_clause = ""
        if excluded_ids:
            exclude_clause = f"and id not in ({','.join(map(str, excluded_ids))})"

        # 计算还需要多少结果
        remaining_needed = top_n - len(final_results)

        # 构造SQL查询
        sql = text(f"""
            SELECT
                id,
                title as question,
                content as answer,
                1 - (q_embedding <=> '{emb}'::vector) AS hybrid_score
            FROM {global_schema}.indexed_knowledge
            WHERE
                1 - (q_embedding <=> '{emb}'::vector) >= {threshold}
                and knowledge_type = 'qa'
                and status <>'P'
                {exclude_clause}
            ORDER BY hybrid_score DESC
            LIMIT {remaining_needed}
        """)

        try:
            results = execute_search(sql)

            if results:
                # 添加阈值信息到结果中
                for result in results:
                    result['search_threshold'] = threshold
                    excluded_ids.add(result['id'])

                final_results.extend(results)

                logging.info(f"阈值 {threshold:.2f}: 找到 {len(results)} 个结果")

        except Exception as e:
            logging.error(f"阈值 {threshold:.2f} 查询失败: {e}")
            continue

    # 5. 如果仍然没有足够结果，执行最后兜底查询
    if len(final_results) < min_results:
        logging.warning(f"高精度查询只找到 {len(final_results)} 个结果，执行兜底查询")

        # 使用极低阈值进行兜底查询
        fallback_threshold = 0.5
        exclude_clause = f"and id not in ({','.join(map(str, excluded_ids))})" if excluded_ids else ""

        sql = text(f"""
            SELECT
                id,
                title as question,
                content as answer,
                1 - (q_embedding <=> '{emb}'::vector) AS hybrid_score
            FROM {global_schema}.indexed_knowledge
            WHERE
                1 - (q_embedding <=> '{emb}'::vector) >= {fallback_threshold}
                and knowledge_type = 'qa'
                and status <>'P'
                {exclude_clause}
            ORDER BY hybrid_score DESC
            LIMIT {min_results}
        """)

        try:
            fallback_results = execute_search(sql)
            if fallback_results:
                for result in fallback_results:
                    result['search_threshold'] = fallback_threshold
                    result['is_fallback'] = True

                final_results.extend(fallback_results)
                logging.info(f"兜底查询找到 {len(fallback_results)} 个结果")

        except Exception as e:
            logging.error(f"兜底查询失败: {e}")

    # 6. 记录最终搜索统计信息
    if final_results:
        thresholds_used = list(set(r.get('search_threshold', 0) for r in final_results))
        avg_score = sum(r['hybrid_score'] for r in final_results) / len(final_results)

        logging.info(f"搜索完成: 总计 {len(final_results)} 个结果, "
                    f"使用阈值 {thresholds_used}, "
                    f"平均相似度 {avg_score:.3f}")
    else:
        logging.warning("所有阈值查询均未找到结果")

    return final_results[:top_n]


def get_adaptive_similarity_threshold_with_rerank_fallback(
    query: str,
    used_id: int = -1,
    top_n: int = 3,
    enable_rerank: bool = True
) -> List[Dict]:
    """
    集成阈值降级和 Rerank 的混合搜索策略

    Args:
        query: 查询文本
        used_id: 排除的ID
        top_n: 期望返回的结果数量
        enable_rerank: 是否启用 Rerank 重排序

    Returns:
        优化后的搜索结果列表
    """
    # 1. 首先尝试阈值降级搜索
    candidates = get_adaptive_similarity_threshold_with_fallback(
        query=query,
        used_id=used_id,
        top_n=max(top_n, 5),  # 为 Rerank 准备更多候选
        initial_threshold=0.95,
        fallback_thresholds=[0.90, 0.80, 0.65],
        min_results=3
    )

    if not candidates:
        return []

    # 2. 如果启用 Rerank 且有足够候选，进行重排序
    if enable_rerank and len(candidates) >= 2:
        try:
            from app.config.llm_client import rerank_client_instance

            # 提取文档内容
            documents = []
            for result in candidates:
                text_content = f"{result.get('question', '')} {result.get('answer', '')}".strip()
                documents.append(text_content)

            # 执行 Rerank
            rerank_results = rerank_client_instance.rerank_sync(query, documents)

            if rerank_results:
                # 根据 Rerank 结果重新排序
                reranked_docs = []
                for item in rerank_results:
                    idx = item["index"]
                    score = item.get("score", 0)

                    if idx < len(candidates):
                        reranked_doc = candidates[idx].copy()
                        reranked_doc["rerank_score"] = score
                        reranked_docs.append(reranked_doc)

                return reranked_docs[:top_n]
            else:
                # Rerank 失败，返回原始结果
                logging.warning("Rerank 失败，使用原始相似度排序结果")
                return candidates[:top_n]

        except Exception as e:
            logging.error(f"Rerank 处理失败: {e}")
            return candidates[:top_n]

    # 3. 不使用 Rerank，直接返回相似度排序结果
    return candidates[:top_n]



def qa_hybrid_search_vec_rff(query: str) -> List[Dict]:


        # 1. 获取嵌入
    response = embedding_client.embeddings.create(
        input=query,
        model='bge-m3'
    )
    sorted_data = sorted(response.data, key=lambda x: x.index)
    embedding = sorted_data[0].embedding  # 直接取第一个（通常只有一个）


    # 2. 构造 emb 字符串为 PostgreSQL vector 格式 '[val1,val2,...]'
    emb = f'[{",".join(map(str, embedding))}]'


    # Improved RRF query as text
    sql = text(f"""
      WITH 
        fts_results AS (
          SELECT 
            id,title as question, content as answer,
            RANK() OVER (ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC) AS fts_rank
          FROM {global_schema}.indexed_knowledge
          WHERE fts @@ websearch_to_tsquery('zhparsercfg', :query_text)
            and knowledge_type = 'qa'
            and status <>'P'
          ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC
          LIMIT 20
        ),
        vec_results AS (
          SELECT 
            id,title as question, content as answer,
            RANK() OVER (ORDER BY q_embedding <=> :query_vector) AS vec_rank
          FROM {global_schema}.indexed_knowledge
            where knowledge_type = 'qa'
            and status <>'P'
          ORDER BY q_embedding <=> :query_vector
          LIMIT 20
        ),
        combined AS (
          SELECT 
            COALESCE(f.id, v.id) AS id,
            COALESCE(f.question, v.question) AS question,
            COALESCE(f.answer, v.answer) AS answer,
            COALESCE((1.0 / (:rrf_k + f.fts_rank))::FLOAT, 0.0) AS fts_rrf,
            COALESCE((1.0 / (:rrf_k + v.vec_rank))::FLOAT, 0.0) AS vec_rrf
          FROM fts_results f
          FULL OUTER JOIN vec_results v ON f.id = v.id
        )
        SELECT id, question, answer, 
               (:weight_fts * fts_rrf + :weight_vec * vec_rrf) / 
               NULLIF(MAX(:weight_fts * fts_rrf + :weight_vec * vec_rrf) OVER (), 0) AS hybrid_score
        FROM combined
        ORDER BY hybrid_score DESC
        LIMIT 5;
    """)


    with SessionLocal() as session:
        result = session.execute(sql, {"query_text": query, "query_vector": emb, "rrf_k": 20, "weight_fts":0.4, "weight_vec":0.6})
        rows = result.fetchall()
    return [{"id": row[0], "question": row[1], "answer": row[2], "hybrid_score": row[3]} for row in rows]



def doc_hybrid_search_vec_rff(query: str) -> List[Dict]:


        # 1. 获取嵌入
    embedding = get_text_embeddings(embedding_client,query)


    # 2. 构造 emb 字符串为 PostgreSQL vector 格式 '[val1,val2,...]'
    emb = f'[{",".join(map(str, embedding))}]'


    # Improved RRF query as text
    sql = text(f"""
       WITH 
        fts_results AS (
          SELECT 
            id,title as question, content as answer,
            RANK() OVER (ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC) AS fts_rank
          FROM {global_schema}.indexed_knowledge
          WHERE fts @@ websearch_to_tsquery('zhparsercfg', :query_text)
               and status <>'P'
          ORDER BY ts_rank(fts, websearch_to_tsquery('zhparsercfg', :query_text)) DESC
          LIMIT 50
        ),
        vec_results AS (
          SELECT 
            id,title as question, content as answer,
            RANK() OVER (ORDER BY q_embedding <=> :query_vector) AS vec_rank
          FROM {global_schema}.doc_knowledge
          where status <>'P'
          ORDER BY q_embedding <=> :query_vector
          LIMIT 50
        ),
        combined AS (
          SELECT 
            COALESCE(f.id, v.id) AS id,
            COALESCE(f.question, v.question) AS question,
            COALESCE(f.answer, v.answer) AS answer,
            COALESCE((1.0 / (:rrf_k + f.fts_rank))::FLOAT, 0.0) AS fts_rrf,
            COALESCE((1.0 / (:rrf_k + v.vec_rank))::FLOAT, 0.0) AS vec_rrf
          FROM fts_results f
          FULL OUTER JOIN vec_results v ON f.id = v.id
        )
        SELECT id, question, answer, 
               (:weight_fts * fts_rrf + :weight_vec * vec_rrf) / 
               NULLIF(MAX(:weight_fts * fts_rrf + :weight_vec * vec_rrf) OVER (), 0) AS hybrid_score
        FROM combined
        ORDER BY hybrid_score DESC
        LIMIT 10;
    """)


    with SessionLocal() as session:
        result = session.execute(sql, {"query_text": query, "query_vector": emb, "rrf_k": 20, "weight_fts":0.4, "weight_vec":0.6})
        rows = result.fetchall()
    return [{"id": row[0], "title": row[1], "answer": row[2], "hybrid_score": row[3]} for row in rows]

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
    initial_results = doc_hybrid_search_vec_rff(query)

    if not initial_results:
        return []

    # 2. 提取文档内容用于 rerank
    documents = []
    for result in initial_results:
        # 组合 title 和 answer 作为 rerank 的文本内容
        text_content = f"{result.get('title', '')} {result.get('answer', '')}".strip()
        documents.append(text_content)

    # 2.1 查询改写

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
            logging.info("使用rerank")
            return doc_hybrid_search_vec_rff_with_rerank(query, top_n)
        else:
            # 直接返回混合搜索结果
            results = doc_hybrid_search_vec_rff(query)
            return results[:top_n]

    except Exception as e:
        # 容错：如果 rerank 出现异常，返回原始搜索结果
        logging.error("使用rerank")
        results = doc_hybrid_search_vec_rff(query)
        return results[:top_n]




# ================== BM25 + 向量检索混合搜索实现 ==================

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
    """
    numerator = term_freq * (k1 + 1)
    denominator = term_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
    return numerator / denominator


def get_collection_stats(table_name: str = f'{global_schema}.indexed_knowledge') -> Tuple[float, int]:
    """
    获取文档集合的统计信息

    Returns:
        (avg_doc_length, total_docs): 平均文档长度和总文档数
    """
    sql = text(f"""
        SELECT
            AVG(LENGTH(content)) as avg_doc_length,
            COUNT(*) as total_docs
        FROM {table_name}
        WHERE content IS NOT NULL
        AND status <>'P'
    """)

    with SessionLocal() as session:
        result = session.execute(sql)
        row = result.fetchone()
        if row is None or row[0] is None:
            return 0.0, 0
        return float(row[0]), int(row[1])


def bm25_search_pg(query: str, table_name: str = f'{global_schema}.indexed_knowledge',
                   b: float = 0.75, top_k: int = 20) -> List[Dict]:
    """
    在 PostgreSQL 中实现简化版 BM25 搜索

    Args:
        query: 搜索查询
        table_name: 表名
        b: BM25 参数 b（文档长度归一化参数）
        top_k: 返回的结果数量
    """
    # 获取集合统计信息
    avg_doc_length, total_docs = get_collection_stats(table_name)

    # 构建查询词的 tsquery
    query_ts = f"websearch_to_tsquery('zhparsercfg', :query_text)"

    # 简化的 BM25 实现 - 使用 ts_rank_cd 作为基础，结合文档长度归一化
    sql = text(f"""
        SELECT
            id,
            title as question,
            content as answer,
            -- 简化的 BM25 评分：ts_rank_cd + 文档长度归一化
            (ts_rank_cd(fts, {query_ts}, 32) *
             (LOG({total_docs} + 1) / (1 + LOG(1 + :b * (LENGTH(content) / {avg_doc_length}))))) AS bm25_score
        FROM {table_name}
        WHERE fts @@ {query_ts}
        AND status <>'P'
        ORDER BY bm25_score DESC
        LIMIT :top_k
    """)

    with SessionLocal() as session:
        result = session.execute(sql, {
            "query_text": query,
            "top_k": top_k,
            "b": b
        })
        rows = result.fetchall()

    return [
        {
            "id": row[0],
            "question": row[1],
            "answer": row[2],
            "bm25_score": float(row[3]),
            "source": "bm25"
        }
        for row in rows
    ]


def vector_search(query_embedding: List[float], table_name: str = f'{global_schema}.indexed_knowledge',
                 similarity_threshold: float = 0.0, top_k: int = 20) -> List[Dict]:
    """
    向量相似度搜索

    Args:
        query_embedding: 查询向量
        table_name: 表名
        similarity_threshold: 相似度阈值
        top_k: 返回的结果数量
    """
    emb_str = f'[{",".join(map(str, query_embedding))}]'

    sql = text(f"""
        SELECT
            id,
            title as question,
            content as answer,
            1 - (q_embedding <=> :query_vector) AS similarity_score
        FROM {table_name}
        WHERE 1 - (q_embedding <=> :query_vector) >= :threshold
        AND status <>'P'
        ORDER BY similarity_score DESC
        LIMIT :top_k
    """)

    with SessionLocal() as session:
        result = session.execute(sql, {
            "query_vector": emb_str,
            "threshold": similarity_threshold,
            "top_k": top_k
        })
        rows = result.fetchall()

    return [
        {
            "id": row[0],
            "question": row[1],
            "answer": row[2],
            "vec_score": float(row[3]),
            "source": "vector"
        }
        for row in rows
    ]


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
                "vec_score": doc["vec_score"]
            }

    # 合并结果并排序
    merged_results = []
    for doc_id, hybrid_score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
        result = {
            "id": doc_id,
            "question": doc_data[doc_id]["question"],
            "answer": doc_data[doc_id]["answer"],
            "hybrid_score": 100*hybrid_score,
            "bm25_score": doc_data[doc_id].get("bm25_score", 0.0),
            "vec_score": doc_data[doc_id].get("vec_score", 0.0)
        }
        merged_results.append(result)

    return merged_results


def doc_hybrid_search_bm25_vec(query: str, table_name: str = f'{global_schema}.indexed_knowledge') -> List[Dict]:
    """
    BM25 + 向量检索混合搜索（完整实现）

    Args:
        query: 搜索查询
        table_name: 表名

    Returns:
        融合后的搜索结果列表
    """
    # 搜索配置参数
    SEARCH_CONFIG = {
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
            "final_top_k": 5
        }
    }

    # 1. 并行执行两种搜索
    with ThreadPoolExecutor(max_workers=2) as executor:
        # BM25 搜索
        bm25_future = executor.submit(
            bm25_search_pg,
            query,
            table_name,
            SEARCH_CONFIG["bm25"]["b"],
            SEARCH_CONFIG["bm25"]["top_k"]
        )

        # 向量搜索
        embedding = get_text_embeddings(embedding_client, query)
        vec_future = executor.submit(
            vector_search,
            embedding,
            table_name,
            SEARCH_CONFIG["vector"]["similarity_threshold"],
            SEARCH_CONFIG["vector"]["top_k"]
        )

    # 2. 获取搜索结果
    bm25_results = bm25_future.result()
    vec_results = vec_future.result()

    # 3. RRF 融合
    merged_results = merge_with_rrf(
        bm25_results,
        vec_results,
        SEARCH_CONFIG["rrf"]["k"],
        SEARCH_CONFIG["rrf"]["weight_bm25"],
        SEARCH_CONFIG["rrf"]["weight_vec"]
    )

    # 4. 返回最终结果
    return merged_results[:SEARCH_CONFIG["rrf"]["final_top_k"]]


def qa_hybrid_search_bm25_vec(query: str, table_name: str = f'{global_schema}.indexed_knowledge') -> List[Dict]:
    """
    QA 知识库的 BM25 + 向量检索混合搜索

    Args:
        query: 搜索查询
        table_name: QA 表名

    Returns:
        融合后的搜索结果列表
    """
    return doc_hybrid_search_bm25_vec(query, table_name)
