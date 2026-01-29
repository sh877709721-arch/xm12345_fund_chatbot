from typing import List, Optional, Tuple, Dict
import logging
from sqlalchemy import update, text
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.model.guidelines import Guidelines
from app.schema.guideline import (
    GuidelinesRead,
    GuidelinesCreate,
    GuidelinesUpdate,
    GuidelinesStatusEnum,
    GuidelinesMatchResult,
    GuidelinesMatchRequest
)
from app.schema.base import PageResponse
from app.config.llm_client import embedding_client, chat_client_bot
from app.core.embeddings_utils import get_text_embeddings
from app.config.database import global_schema

logger = logging.getLogger(__name__)


# 配置
BATCH_SIZE = 2
MODEL_NAME = "bge-m3"
EMBEDDING_DIM = 1024

class GuidelinesService:
    """指南管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_guideline(self,
                         title: str,
                         condition: str,
                         action: str,
                         prompt_template: Optional[str] = None,
                         priority: int = 1,
                         status: str = GuidelinesStatusEnum.draft.value) -> GuidelinesRead:
        """
        创建指南

        Args:
            title: 指南标题
            condition: 触发条件
            action: 执行动作
            prompt_template: 提示词模板
            priority: 优先级（默认1，范围0-9999）
            status: 状态

        Returns:
            创建的指南对象
        """
        try:
            guideline = Guidelines(
                title=title,
                condition=condition,
                action=action,
                prompt_template=prompt_template,
                priority=priority,
                status=status
            )
            self.db.add(guideline)
            self.db.commit()
            self.db.refresh(guideline)
            logger.info(f"Created guideline with id: {guideline.id}, priority: {priority}")
            return GuidelinesRead.model_validate(guideline)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create guideline: {e}")
            raise e

    def get_guideline(self, guideline_id: int) -> Optional[GuidelinesRead]:
        """
        获取单个指南

        Args:
            guideline_id: 指南ID

        Returns:
            指南对象或None
        """
        guideline = self.db.query(Guidelines).filter(
            Guidelines.id == guideline_id,
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        ).first()

        if guideline:
            return GuidelinesRead.model_validate(guideline)
        return None

    def get_guidelines(self) -> List[GuidelinesRead]:
        """
        获取所有未删除的指南（按优先级降序排列）

        Returns:
            指南列表
        """
        guidelines = self.db.query(Guidelines).filter(
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        ).order_by(Guidelines.priority.desc(), Guidelines.id.desc()).all()

        return [GuidelinesRead.model_validate(g) for g in guidelines]
    
    def get_guidelines_by_id(self, guideline_id: int):
        """
        获取所有未删除的指南
        """
        guideline = self.db.query(Guidelines).filter(
            Guidelines.id == id,
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        )
        return guideline

    def update_guideline(self,
                         guideline_id: int,
                         title: Optional[str] = None,
                         condition: Optional[str] = None,
                         action: Optional[str] = None,
                         prompt_template: Optional[str] = None,
                         priority: Optional[int] = None,
                         status: Optional[str] = None) -> GuidelinesRead:
        """
        更新指南

        Args:
            guideline_id: 指南ID
            title: 标题
            condition: 条件
            action: 动作
            prompt_template: 提示词模板
            priority: 优先级（可选）
            status: 状态

        Returns:
            更新后的指南对象
        """
        try:
            guideline = self.db.query(Guidelines).filter(
                Guidelines.id == guideline_id
            ).first()

            if not guideline:
                raise ValueError(f"Guideline with id {guideline_id} not found")

            # 构建更新字典
            update_values = {}
            if title is not None:
                update_values['title'] = title
            if condition is not None:
                update_values['condition'] = condition
            if action is not None:
                update_values['action'] = action
            if prompt_template is not None:
                update_values['prompt_template'] = prompt_template
            if priority is not None:
                update_values['priority'] = priority
            if status is not None:
                update_values['status'] = status

            if update_values:
                stmt = (
                    update(Guidelines)
                    .where(Guidelines.id == guideline_id)
                    .values(**update_values)
                )
                self.db.execute(stmt)
                self.db.commit()
                self.db.refresh(guideline)
                logger.info(f"Updated guideline with id: {guideline_id}, priority change: {priority}")

            return GuidelinesRead.model_validate(guideline)
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update guideline {guideline_id}: {e}")
            raise e

    def delete_guideline(self, guideline_id: int) -> GuidelinesRead:
        """
        删除指南（软删除）

        Args:
            guideline_id: 指南ID

        Returns:
            被删除的指南对象
        """
        try:
            guideline = self.db.query(Guidelines).filter(
                Guidelines.id == guideline_id
            ).first()

            if not guideline:
                raise ValueError(f"Guideline with id {guideline_id} not found")

            stmt = (
                update(Guidelines)
                .where(Guidelines.id == guideline_id)
                .values(status=GuidelinesStatusEnum.deleted.value)
            )
            self.db.execute(stmt)
            self.db.commit()
            self.db.refresh(guideline)
            logger.info(f"Deleted guideline with id: {guideline_id}")

            return GuidelinesRead.model_validate(guideline)
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete guideline {guideline_id}: {e}")
            raise e

    def search_guidelines(self,
                          title: Optional[str] = None,
                          condition: Optional[str] = None,
                          action: Optional[str] = None,
                          status: Optional[str] = None,
                          priority_min: Optional[int] = None,
                          priority_max: Optional[int] = None,
                          orderby: Optional[str] = None,
                          order: Optional[str] = None,
                          page: int = 1,
                          size: int = 10) -> PageResponse:
        """
        搜索指南（支持分页、多条件查询和排序）

        Args:
            title: 标题（模糊匹配）
            condition: 条件（模糊匹配）
            action: 动作（模糊匹配）
            status: 状态（精确匹配）
            priority_min: 最小优先级
            priority_max: 最大优先级
            orderby: 排序字段
            order: 排序方向
            page: 页码（从1开始）
            size: 每页大小

        Returns:
            分页结果
        """
        # 构建查询
        query = self.db.query(Guidelines).filter(
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        )

        # 添加过滤条件
        if title:
            query = query.filter(Guidelines.title.contains(title))

        if condition:
            query = query.filter(Guidelines.condition.contains(condition))

        if action:
            query = query.filter(Guidelines.action.contains(action))

        if status:
            query = query.filter(Guidelines.status == status)

        # 优先级范围过滤
        if priority_min is not None:
            query = query.filter(Guidelines.priority >= priority_min)

        if priority_max is not None:
            query = query.filter(Guidelines.priority <= priority_max)

        # 计算总数
        total = query.count()

        # 验证排序字段，防止SQL注入
        valid_orderby_fields = {
            'id': Guidelines.id,
            'priority': Guidelines.priority,
            'created_time': Guidelines.created_time,
            'updated_time': Guidelines.updated_time
        }

        # 获取排序字段，默认使用 priority，无效值则使用默认值
        if orderby and orderby in valid_orderby_fields:
            order_field = valid_orderby_fields[orderby]
        else:
            order_field = Guidelines.priority

        # 验证排序方向，防止非法值
        if order and order.lower() in ['asc', 'desc']:
            order_direction = order.lower()
        else:
            order_direction = 'desc'

        # 应用分页和排序（动态选择升序或降序）
        offset = (page - 1) * size
        if order_direction == 'asc':
            paginated_query = query.order_by(order_field.asc()).offset(offset).limit(size)
        else:
            paginated_query = query.order_by(order_field.desc()).offset(offset).limit(size)

        results = paginated_query.all()
        # 防御性编程：显式处理 priority 为 None 的情况
        items = []
        for guideline in results:
            guideline_dict = {
                'id': guideline.id,
                'title': guideline.title,
                'condition': guideline.condition,
                'action': guideline.action,
                'prompt_template': guideline.prompt_template,
                'priority': guideline.priority if guideline.priority is not None else 1,  # 默认值 1
                'status': guideline.status,
                'created_time': guideline.created_time,
                'updated_time': guideline.updated_time
            }
            items.append(GuidelinesRead(**guideline_dict))

        # 构造分页信息
        has_next = page * size < total
        has_prev = page > 1

        return PageResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            has_next=has_next,
            has_prev=has_prev
        )


    def _generate_embeddings(self,texts: List[str]) -> List[List[float]]:
        """调用 embedding 服务，返回 float 列表的列表"""
        if not texts:
            return []
        try:
            response = embedding_client.embeddings.create(
                input=texts,
                model=MODEL_NAME
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            embeddings = [emb.embedding for emb in sorted_data]
            # 校验维度
            for emb in embeddings:
                if len(emb) != EMBEDDING_DIM:
                    raise ValueError(f"Embedding 维度错误：期望 {EMBEDDING_DIM}，实际 {len(emb)}")
            return embeddings
        except Exception as e:
            logger.error(f"❌ Embedding 生成失败: {e}")
            raise

    def build_index_by_guideline_id(self, guideline_id):
        """构建向量索引"""
        try:
            # 获取指南内容
            guideline = self.db.query(Guidelines).filter(
                Guidelines.id == guideline_id,
                Guidelines.status != GuidelinesStatusEnum.deleted.value
            ).first()
            
            guideline_read = GuidelinesRead.model_validate(guideline)

            if not guideline:
                raise ValueError(f"指南 {guideline_id} 不存在")
            
            
            # 构建索引项
            emb = self._generate_embeddings([guideline_read.condition])[0]
            guideline.condition_embedding = emb
            guideline.set_condition_fts()
            self.db.commit()
    
        except Exception as e:
            error_msg = f"Failed to build index for guideline {guideline_id}: {str(e)}"
            raise Exception(error_msg)

    def match_guideline_by_context(
        self,
        context: str,
        candidate_top_k: int = 5,
        vector_top_k: int = 20,
        bm25_top_k: int = 20,
        similarity_threshold: float = 0.7,
        use_llm_refinement: bool = True
    ) -> Optional[GuidelinesMatchResult]:
        """
        根据对话上下文智能匹配最合适的指南（两阶段混合检索 + LLM 精选）

        Args:
            context: 对话上下文（用户查询或对话历史）
            candidate_top_k: 返回给 LLM 精选的候选数量（默认 5）
            vector_top_k: 向量检索返回的候选数量（默认 20）
            bm25_top_k: BM25 检索返回的候选数量（默认 20）
            similarity_threshold: 向量相似度阈值（默认 0.7）
            use_llm_refinement: 是否使用 LLM 精选（默认 True）

        Returns:
            GuidelinesMatchResult 包含匹配的指南和相关信息，如果没有匹配则返回 None
        """
        try:
            logger.info(f"开始指南匹配，上下文: {context[:100]}...")

            # 阶段 1：粗粒度检索（多路召回）
            candidates_with_scores = self._hybrid_search(
                context=context,
                vector_top_k=vector_top_k,
                bm25_top_k=bm25_top_k,
                candidate_top_k=candidate_top_k,
                similarity_threshold=similarity_threshold
            )

            if not candidates_with_scores:
                logger.warning("未找到匹配的指南")
                return None

            # 提取候选指南对象
            candidates = [item['guideline'] for item in candidates_with_scores]

            # 阶段 2：细粒度精选（LLM 语义理解）
            if use_llm_refinement:
                from app.service.guideline_matcher import GuidelineMatcher

                matcher = GuidelineMatcher(self.db, chat_client_bot)
                selected_guideline, confidence, _ = matcher.refine_with_llm(
                    context=context,
                    candidates=candidates
                )

                if selected_guideline is None:
                    logger.warning("LLM 未能选择指南，使用 RRF 第一名")
                    selected_guideline = candidates[0]
                    confidence = candidates_with_scores[0]['rrf_score']
                    match_method = "rrf_fallback"
                    match_score = candidates_with_scores[0]['rrf_score']
                else:
                    match_method = "llm"
                    match_score = confidence

                logger.info(f"LLM 选择了指南 {selected_guideline.id}，置信度: {confidence}")
            else:
                # 不使用 LLM，直接返回第一名
                selected_guideline = candidates[0]
                confidence = candidates_with_scores[0]['rrf_score']
                match_method = "rrf"
                match_score = candidates_with_scores[0]['rrf_score']

                logger.info(f"未使用 LLM，直接返回 RRF 第一名: {selected_guideline.id}")

            # 构造返回结果
            result = GuidelinesMatchResult(
                guideline_id=selected_guideline.id,
                title=selected_guideline.title,
                condition=selected_guideline.condition,
                action=selected_guideline.action,
                prompt_template=selected_guideline.prompt_template,
                priority=selected_guideline.priority,
                match_score=match_score,
                match_method=match_method,
                confidence=confidence
            )

            return result

        except Exception as e:
            logger.error(f"指南匹配失败: {e}", exc_info=True)
            return None

    def _hybrid_search(
        self,
        context: str,
        vector_top_k: int = 20,
        bm25_top_k: int = 20,
        candidate_top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        混合检索：向量检索 + BM25 检索 + RRF 融合

        Args:
            context: 查询上下文
            vector_top_k: 向量检索返回数量
            bm25_top_k: BM25 检索返回数量
            candidate_top_k: 最终返回候选数量
            similarity_threshold: 向量相似度阈值

        Returns:
            候选指南列表，每个元素包含 {'guideline': Guidelines, 'rrf_score': float}
        """
        # 并行执行向量检索和 BM25 检索
        with ThreadPoolExecutor(max_workers=2) as executor:
            vector_future = executor.submit(
                self._vector_search_with_priority,
                context,
                vector_top_k,
                similarity_threshold
            )
            bm25_future = executor.submit(
                self._bm25_search_with_priority,
                context,
                bm25_top_k
            )

            vector_results = vector_future.result()
            bm25_results = bm25_future.result()

        logger.info(f"向量检索找到 {len(vector_results)} 条，BM25 检索找到 {len(bm25_results)} 条")

        # RRF 融合
        merged_results = self._merge_with_rrf(
            vector_results=vector_results,
            bm25_results=bm25_results,
            k=60,
            weight_vector=0.6,
            weight_bm25=0.4
        )

        # 按 priority 排序（RRF 分数相同时，高优先级排前面）
        merged_results.sort(key=lambda x: (x['rrf_score'], x['guideline'].priority), reverse=True)

        # 返回前 N 条
        return merged_results[:candidate_top_k]

    def _vector_search_with_priority(
        self,
        context: str,
        top_k: int = 20,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        向量语义检索（考虑 priority）

        Args:
            context: 查询文本
            top_k: 返回数量
            similarity_threshold: 相似度阈值

        Returns:
            [{'guideline': Guidelines, 'similarity': float}, ...]
        """
        try:
            # 1. 生成查询的 embedding
            embedding = get_text_embeddings(embedding_client, context)
            emb_str = f'[{",".join(map(str, embedding))}]'
            
            

            # 2. 构造 SQL 查询
            sql = text(f"""
                SELECT
                    id,
                    1 - (condition_embedding <=> :emb) AS similarity
                FROM {global_schema}.guidelines
                WHERE
                    1 - (condition_embedding <=> :emb) >= :threshold
                    AND status != 'X'
                ORDER BY similarity DESC, priority DESC
                LIMIT :top_k
            """)

            result = self.db.execute(
                sql,
                {"emb": emb_str, "threshold": similarity_threshold, "top_k": top_k}
            )
            rows = result.fetchall()

            if not rows:
                return []

            # 3. 获取完整的指南对象
            guideline_ids = [row.id for row in rows]
            guidelines = self.db.query(Guidelines).filter(
                Guidelines.id.in_(guideline_ids)
            ).all()

            # 创建 ID 到指南的映射
            guideline_map = {g.id: g for g in guidelines}

            # 4. 构造结果，保持 SQL 查询的排序
            results = []
            for row in rows:
                if row.id in guideline_map:
                    results.append({
                        'guideline': guideline_map[row.id],
                        'similarity': float(row.similarity)
                    })

            logger.info(f"向量检索完成，找到 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"向量检索失败: {e}", exc_info=True)
            return []

    def _bm25_search_with_priority(
        self,
        context: str,
        top_k: int = 20
    ) -> List[Dict]:
        """
        BM25 全文检索（考虑 priority）

        Args:
            context: 查询文本
            top_k: 返回数量

        Returns:
            [{'guideline': Guidelines, 'rank': float}, ...]
        """
        try:
            # 1. 构造 SQL 查询（使用 PostgreSQL 全文搜索）
            sql = text(f"""
                SELECT
                    id,
                    ts_rank(condition_fts, websearch_to_tsquery('zhparsercfg', :query)) AS rank
                FROM {global_schema}.guidelines
                WHERE
                    condition_fts @@ websearch_to_tsquery('zhparsercfg', :query)
                    AND status != 'X'
                ORDER BY rank DESC, priority DESC
                LIMIT :top_k
            """)

            result = self.db.execute(
                sql,
                {"query": context, "top_k": top_k}
            )
            rows = result.fetchall()

            if not rows:
                return []

            # 2. 获取完整的指南对象
            guideline_ids = [row.id for row in rows]
            guidelines = self.db.query(Guidelines).filter(
                Guidelines.id.in_(guideline_ids)
            ).all()

            # 创建 ID 到指南的映射
            guideline_map = {g.id: g for g in guidelines}

            # 3. 构造结果，保持 SQL 查询的排序
            results = []
            for row in rows:
                if row.id in guideline_map:
                    results.append({
                        'guideline': guideline_map[row.id],
                        'rank': float(row.rank) if row.rank else 0.0
                    })

            logger.info(f"BM25 检索完成，找到 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"BM25 检索失败: {e}", exc_info=True)
            return []

    def _merge_with_rrf(
        self,
        vector_results: List[Dict],
        bm25_results: List[Dict],
        k: int = 60,
        weight_vector: float = 0.6,
        weight_bm25: float = 0.4
    ) -> List[Dict]:
        """
        使用 RRF (Reciprocal Rank Fusion) 算法融合向量检索和 BM25 检索结果

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            k: RRF 平滑参数
            weight_vector: 向量检索权重
            weight_bm25: BM25 检索权重

        Returns:
            融合后的结果列表 [{'guideline': Guidelines, 'rrf_score': float}, ...]
        """
        doc_scores = {}
        doc_guidelines = {}

        # 向量结果评分
        for rank, item in enumerate(vector_results, 1):
            guideline_id = item['guideline'].id
            rrf_score = 1.0 / (k + rank)
            doc_scores[guideline_id] = doc_scores.get(guideline_id, 0) + weight_vector * rrf_score
            doc_guidelines[guideline_id] = item['guideline']

        # BM25 结果评分
        for rank, item in enumerate(bm25_results, 1):
            guideline_id = item['guideline'].id
            rrf_score = 1.0 / (k + rank)
            doc_scores[guideline_id] = doc_scores.get(guideline_id, 0) + weight_bm25 * rrf_score
            if guideline_id not in doc_guidelines:
                doc_guidelines[guideline_id] = item['guideline']

        # 排序并构造结果
        merged_results = []
        for guideline_id, rrf_score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
            merged_results.append({
                'guideline': doc_guidelines[guideline_id],
                'rrf_score': rrf_score
            })

        logger.info(f"RRF 融合完成，合并后 {len(merged_results)} 条不重复结果")
        return merged_results