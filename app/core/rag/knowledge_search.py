"""
知识检索统一封装模块
提供文档检索、知识图谱处理和数据整合的统一接口
"""

import logging
from typing import List, Dict
import json
from qwen_agent.llm.schema import Message 
#from app.core.rag.del_vector_wrapper import doc_hybrid_search_vec_rff_with_fallback
from app.core.graph.search_engine import get_local_search_context
from app.service.search_service import SearchService

logger = logging.getLogger(__name__)

def df_to_json_no_ascii(df, orient='records', **kwargs):
    return json.dumps(df.to_dict(orient=orient), ensure_ascii=False, **kwargs)

def format_knowledge_to_source_and_content(result):
    """
    将知识数据转换为源码和内容格式

    Args:
        result: 知识数据，可能是字符串或字典列表

    Returns:
        List[dict]: 包含source和content的字典列表
    """
    knowledge = []
    if isinstance(result, str):
        result = f'{result}'.strip()
        try:
            docs = json.loads(result)
        except Exception:
            from qwen_agent.utils.utils import print_traceback
            print_traceback()
            knowledge.append({'source': '上传的文档', 'content': result})
            return knowledge
    else:
        docs = result
    try:
        _tmp_knowledge = []
        assert isinstance(docs, list)
        for doc in docs:
            url, snippets = doc['url'], doc['text']
            assert isinstance(snippets, list)
            from qwen_agent.utils.utils import get_basename_from_url
            _tmp_knowledge.append({
                'source': f'[文件]({get_basename_from_url(url)})',
                'content': '\n\n...\n\n'.join(snippets)
            })
        knowledge.extend(_tmp_knowledge)
    except Exception:
        from qwen_agent.utils.utils import print_traceback
        print_traceback()
        knowledge.append({'source': '上传的文档', 'content': result})
    return knowledge


def format_knowledge_context(data, url_identifier, limit=None):
    """
    将知识图谱内容转换为字符串格式，确保JSON序列化兼容性

    Args:
        data: 知识图谱数据（可能是DataFrame、dict、list、string等类型）
        url_identifier: 用于标识数据源的URL字符串
        limit: 可选，限制数据条数（仅对DataFrame、list、dict类型有效）

    Returns:
        dict: 包含url和text字段的字典，text字段为字符串列表
    """
    if not data:
        return None

    # 导入必要的库
    import pandas as pd
    import json

    try:
        # 检查类型并转换为字符串
        if isinstance(data, pd.DataFrame):
            # 如果有limit限制，只取前N条
            if limit is not None and len(data) > limit:
                data = data.head(limit)
            data_str = data.to_string()
        elif isinstance(data, dict):
            # 如果是字典，检查是否包含DataFrame
            processed_dict = {}
            for key, value in data.items():
                if isinstance(value, pd.DataFrame):
                    # 如果有limit限制，只取前N条
                    if limit is not None and len(value) > limit:
                        value = value.head(limit)
                    processed_dict[key] = value.to_string()
                else:
                    processed_dict[key] = str(value)
            data_str = json.dumps(processed_dict, ensure_ascii=False, indent=2)
        elif isinstance(data, list):
            # 处理列表，确保所有元素都是可序列化的
            processed_list = []
            # 如果有limit限制，只取前N条
            if limit is not None and len(data) > limit:
                data = data[:limit]
            for item in data:
                if isinstance(item, pd.DataFrame):
                    processed_list.append(item.to_string())
                elif isinstance(item, dict):
                    processed_list.append(json.dumps(item, ensure_ascii=False, default=str))
                elif hasattr(item, '__iter__') and not isinstance(item, str):
                    # 处理其他可迭代对象（如set、tuple等）
                    processed_list.append(str(item))
                else:
                    processed_list.append(str(item))
            data_str = json.dumps(processed_list, ensure_ascii=False, indent=2)
        elif isinstance(data, str):
            data_str = data
        else:
            # 其他类型直接转换为字符串
            data_str = str(data)

        return {
            'url': url_identifier,
            'text': [data_str.split('-----Sources-----')[-1]]
        }

    except Exception as e:
        # 如果转换失败，返回错误信息
        logger.warning(f"Failed to format knowledge context for {url_identifier}: {e}")
        return {
            'url': url_identifier,
            'text': [f"Error formatting knowledge data: {str(e)}"]
        }




class KnowledgeSearchService:
    """知识检索服务统一封装类"""

    @staticmethod
    def search_and_integrate_knowledge(
        query: str,
        doc_top_n: int = 5,
        graph_top_n: int = 3,
        enable_graph_search: bool = True,
        enable_data_search: bool = True
    ) -> tuple[List[Dict], List[str], List[str]]:
        """
        统一的知识检索和数据整合接口

        Args:
            query: 原始查询文本
            doc_top_n: 文档检索返回的最大数量
            graph_top_n: 知识图谱重排序后的最大数量
            enable_graph_search: 是否启用知识图谱搜索
            enable_data_search: 是否启用 Excel 数据搜索

        Returns:
            tuple: (整合后的知识数据列表, 响应关键词列表)
        """
        knowledge_data = []
        graph_data = []
        excel_data = []


        # 1. 文档检索
        doc_results, doc_keywords = KnowledgeSearchService._search_documents(
            query, doc_top_n
        )
        knowledge_data.extend(doc_results)


        # 2. Excel 数据检索
        if enable_data_search:
            data_results, _ = KnowledgeSearchService._search_knowledge_data(
                query, top_n=10
            )
            excel_data.extend(data_results)

        # 3. 知识图谱检索
        if enable_graph_search:
            graph_results, graph_keywords = KnowledgeSearchService._search_knowledge_graph(
                query, graph_top_n
            )
            graph_data.extend(graph_results)


        return knowledge_data, graph_data,excel_data

    @staticmethod
    def _search_documents(
        query: str,
        top_n: int = 5
    ) -> tuple[List[Dict], List[str]]:
        """
        执行文档检索（包括查询改写）

        Args:
            query: 查询文本
            top_n: 返回结果数量
            enable_query_rewrite: 是否启用查询改写

        Returns:
            tuple: (文档知识数据列表, 关键词列表)
        """
        knowledge_data = []
        response_keywords = []
        search_results = []

        try:
            # 查询改写
            search_results = SearchService.doc_hybrid_search_vec_rff_with_fallback(query, top_n=top_n)

            # 最后的 search_results 也要重排
            # 提取文档内容用于重排
            documents = []
            for result in search_results:
                # 组合 title 和 answer 作为重排的文本内容
                text_content = f"{result.get('title', '')} {result.get('answer', '')}".strip()
                documents.append(text_content)

            # 调用重排API
            try:
                from app.config.llm_client import rerank_client_instance
                rerank_results = rerank_client_instance.rerank_sync(query, documents)
                if rerank_results:
                    # 根据重排结果重新排序
                    reranked_results = []
                    for item in rerank_results:
                        idx = item["index"]
                        score = item.get("score", 0)

                        if idx < len(search_results):
                            # 复制原始结果并更新分数
                            reranked_result = search_results[idx].copy()
                            reranked_result["rerank_score"] = score
                            reranked_results.append(reranked_result)

                    search_results = reranked_results[:top_n]
                    #logger.info(f"文档重排完成，重排了 {len(search_results)} 个结果")
                else:
                    logger.warning("文档重排失败，使用原始搜索结果")
            except Exception as e:
                logger.error(f"文档重排过程出错: {e}，使用原始搜索结果")
            # 转换文档检索结果为标准格式
            for result in search_results:
                reference = f'doc_{result["id"]}' #result['reference'] if result['reference'] else f'doc_{result["id"]}'
                knowledge_data.append({
                    'url':reference,
                    'text': [result.get('title', '') + result.get('question', '') + '\n' + result.get('answer', '')],
                    'reference':result.get('reference', ''),
                    'reference_id':result["id"],
                })

        except Exception as e:
            logger.error(f"文档检索失败: {e}")

        return knowledge_data, response_keywords

    @staticmethod
    def _search_knowledge_graph(
        query: str,
        top_n: int = 3
    ) -> tuple[List[Dict], List[str]]:
        """
        执行知识图谱检索和数据处理

        Args:
            query: 查询文本
            top_n: 重排序后的最大返回数量

        Returns:
            tuple: (图谱知识数据列表, 关键词列表)
        """
        knowledge_data = []
        response_keywords = []

        try:
            # 获取知识图谱上下文
            graph_context,system_prompt = get_local_search_context(query)
            graph_contenxt_chunk = graph_context.context_chunks
            graph_context_records = graph_context.context_records
            
            #import pdb;pdb.set_trace()
            search_results = graph_context_records["sources"].to_dict(orient="records")
            documents = []
            for result in search_results:
                # 组合 title 和 answer 作为重排的文本内容
                text_content = f"{result.get('text', '')}".strip()
                documents.append(text_content)

            # 调用重排API
            # try:
            #     from app.config.llm_client import rerank_client_instance
            #     rerank_results = rerank_client_instance.rerank_sync(query, documents)
            #     if rerank_results:
            #         # 根据重排结果重新排序
            #         reranked_results = []
            #         for item in rerank_results:
            #             idx = item["index"]
            #             score = item.get("score", 0)

            #             if idx < len(search_results):
            #                 # 复制原始结果并更新分数
            #                 reranked_result = search_results[idx].copy()
            #                 reranked_result["rerank_score"] = score
            #                 reranked_results.append(reranked_result)

            #         search_results = reranked_results[:top_n]
            #         #logger.info(f"文档重排完成，重排了 {len(search_results)} 个结果")
            #     else:
            #         logger.warning("文档重排失败，使用原始搜索结果")
            # except Exception as e:
            #     logger.error(f"文档重排过程出错: {e}，使用原始搜索结果")

            # 转换文档检索结果为标准格式
            for result in search_results:
                reference = result.get('reference') if result.get('reference') else f'graph_{result["id"]}'
                knowledge_data.append({
                    'url': reference,
                    'text': [result.get('title', '') + result.get('question', '') + '\n' + result.get('text', '')]
                })
            
            knowledge_data.append({
                'url': f'graph_chunk',
                'text': [graph_contenxt_chunk]
            })


        except Exception as e:
            logger.error(f"知识图谱检索失败: {e}")

        return knowledge_data, response_keywords

    @staticmethod
    def _search_knowledge_data(
        query: str,
        top_n: int = 3
    ) -> tuple[List[Dict], List[str]]:
        """
        搜索 Excel 数据表（knowledge_data）

        流程：
        1. 使用 KnowledgeDataIndexService.search_knowledge_data_vector 进行向量搜索
        2. 提取搜索结果的 knowledge_id 列表
        3. 使用 KnowledgeService.get_knowledge_details 获取知识详情
        4. 将每个搜索结果构造为结构化格式（table_data + knowledge_detail）

        Args:
            query: 查询文本
            top_n: 返回结果数量

        Returns:
            tuple: (知识数据列表, 关键词列表)
            格式：
            [{
                'url': 'data_xxx',  # knowledge_data 记录 ID
                'text': [content_str],  # Excel 行数据 + 知识详情
                'table_data': {
                    'row': {...},  # 原始行数据
                    'score': 0.95,
                    'knowledge_data_id': 123
                },
                'knowledge_detail': {
                    'knowledge_id': 1,
                    'content': '...',
                    'reference': '...',
                    'version': 2
                },
                'reference': detail.reference,
                'knowledge_id': knowledge_id,
                'knowledge_data_id': data_id
            }]
        """
        knowledge_data = []
        response_keywords = []

        try:
            from app.config.database import SessionLocal
            from app.service.knowledge_data_index import KnowledgeDataIndexService
            from app.service.knowledge_entries import KnowledgeService

            # 创建独立的数据库 session
            with SessionLocal() as db:
                # 1. 向量搜索 knowledge_data 表
                index_service = KnowledgeDataIndexService(db)
                search_results = index_service.search_knowledge_data_vector(
                    knowledge_id=None,  # 搜索所有 knowledge_id
                    query=query,
                    threshold=0.65,
                    top_n=top_n
                )

                if not search_results:
                    logger.info(f"Excel 数据向量搜索未找到结果: {query}")
                    return knowledge_data, response_keywords

                # 2. 提取所有唯一的 knowledge_id
                unique_knowledge_ids = list(set(
                    result['knowledge_id'] for result in search_results
                ))

                # 3. 批量获取知识详情
                knowledge_service = KnowledgeService(db)
                knowledge_detail_map = {}  # {knowledge_id: detail}

                for kid in unique_knowledge_ids:
                    try:
                        details = knowledge_service.get_knowledge_details(kid)
                        if details:
                            # 取最新版本的详情
                            knowledge_detail_map[kid] = details[0]
                        else:
                            knowledge_detail_map[kid] = None
                    except Exception as e:
                        logger.error(f"获取 knowledge_id={kid} 的详情失败: {e}")
                        knowledge_detail_map[kid] = None

                # 4. 为每个搜索结果构造返回数据
                for result in search_results:
                    kid = result['knowledge_id']
                    detail = knowledge_detail_map.get(kid)

                    # 提取行数据
                    row_data = result['row']
                    score = result['score']
                    data_id = result['knowledge_data_id']

                    # 将行数据转换为 KV 格式字符串（用于 text 字段）
                    row_text = "\n".join(
                        f"{k}: {v}"
                        for k, v in row_data.items()
                        if k != 'knowledge_id'  # 排除 knowledge_id 字段
                    )

                    # 拼装文本内容（用于 LLM 提示）
                    if detail and detail.content:
                        content_str = f"{row_text}\n\n相似度: {score:.2f}\n\n知识详情：\n{detail.content}"
                        reference = detail.reference or ""
                    else:
                        content_str = f"{row_text}\n\n相似度: {score:.2f}"
                        reference = ""

                    # 构造结构化的 table_data
                    table_data = {
                        'row': row_data,
                        'score': score,
                        'knowledge_data_id': data_id
                    }

                    # 构造结构化的 knowledge_detail
                    knowledge_detail = {
                        'knowledge_id': kid,
                        'content': detail.content if detail else None,
                        'reference': detail.reference if detail else None,
                        'version': detail.version if detail else None
                    }

                    # 构造返回结果
                    knowledge_data.append({
                        'url': f'data_{data_id}',
                        'text': [content_str],
                        'table_data': table_data,
                        'knowledge_detail': knowledge_detail,
                        'reference': reference,
                        'knowledge_id': kid,
                        'knowledge_data_id': data_id
                    })

                logger.info(f"Excel 数据搜索完成: 找到 {len(knowledge_data)} 条记录")

        except Exception as e:
            logger.error(f"Excel 数据检索失败: {e}")

        return knowledge_data, response_keywords

    @staticmethod
    def format_knowledge_for_prompt(knowledge_data: List[Dict]) -> str:
        """
        将知识数据格式化为提示词可用的格式

        Args:
            knowledge_data: 知识数据列表

        Returns:
            str: 格式化后的知识JSON字符串
        """
        return json.dumps(knowledge_data, ensure_ascii=False)

    @staticmethod
    def extract_query_from_messages(messages: List[Message]) -> str:
        """
        从消息列表中提取查询内容

        Args:
            messages: 消息列表

        Returns:
            str: 提取的查询文本
        """
        from qwen_agent.llm.schema import ContentItem, Message, ROLE, CONTENT

        query = ""
        for msg in reversed(messages):
            if msg.get(ROLE) == 'user':
                content = msg.get(CONTENT, '')
                if isinstance(content, str):
                    query = content.strip()
                elif isinstance(content, list):
                    # 处理 ContentItem 列表
                    query = ""
                    for item in content:
                        if hasattr(item, 'text'):
                            query += item.text
                    query = query.strip()
                break
        return query

