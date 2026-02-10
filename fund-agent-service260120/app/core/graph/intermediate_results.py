"""
GraphRAG 中间结果提取模块

用于提取调用大模型前的各种中间结果，包括：
1. 向量检索结果
2. 实体映射结果
3. 上下文构建结果
4. 最终Prompt内容
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
from graphrag.data_model.entity import Entity
from graphrag.data_model.community_report import CommunityReport
from graphrag.data_model.relationship import Relationship
from graphrag.data_model.text_unit import TextUnit
from graphrag.query.context_builder.builders import ContextBuilderResult


@dataclass
class VectorSearchResult:
    """向量检索结果"""
    query: str
    query_embedding: List[float]  # 查询向量
    matched_entities: List[Dict]  # 匹配的实体信息
    similarity_scores: List[float]  # 相似度分数
    search_time: float  # 检索耗时


@dataclass
class EntityMappingResult:
    """实体映射结果"""
    original_query: str
    processed_query: str  # 处理后的查询（可能包含历史对话）
    selected_entities: List[Dict]  # 选中的实体
    excluded_entities: List[str]  # 被排除的实体
    included_entities: List[Dict]  # 强制包含的实体
    entity_count: int  # 最终实体数量


@dataclass
class ContextBuildResult:
    """上下文构建结果"""
    community_context: str  # 社区报告上下文
    local_context: str  # 实体关系上下文
    text_unit_context: str  # 文本单元上下文
    conversation_context: str  # 对话历史上下文
    final_context: str  # 最终整合的上下文
    context_tokens: Dict[str, int]  # 各部分token数量
    context_data: Dict[str, pd.DataFrame]  # 上下文数据


@dataclass
class IntermediateResults:
    """完整的中间结果"""
    query_id: str
    timestamp: float
    original_query: str

    # 各阶段结果
    vector_search: Optional[VectorSearchResult] = None
    entity_mapping: Optional[EntityMappingResult] = None
    context_building: Optional[ContextBuildResult] = None

    # 统计信息
    total_time: float = 0.0
    llm_prompt: Optional[str] = None  # 最终发送给LLM的prompt

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class IntermediateResultsCollector:
    """中间结果收集器"""

    def __init__(self, output_dir: str = "./intermediate_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.current_results: Optional[IntermediateResults] = None
        self.start_time = 0.0

    def start_collection(self, query_id: str, original_query: str) -> None:
        """开始收集中间结果"""
        self.start_time = time.time()
        self.current_results = IntermediateResults(
            query_id=query_id,
            timestamp=self.start_time,
            original_query=original_query
        )

    def collect_vector_search(
        self,
        query: str,
        query_embedding: List[float],
        search_results: List[Any],
        search_time: float
    ) -> None:
        """收集向量检索结果"""
        if not self.current_results:
            return

        # 提取匹配的实体信息
        matched_entities = []
        similarity_scores = []

        for result in search_results:
            entity_info = {
                "id": result.document.id if hasattr(result.document, 'id') else "unknown",
                "title": getattr(result.document, 'title', "unknown"),
                "description": getattr(result.document, 'description', ""),
                "rank": getattr(result.document, 'rank', 0)
            }
            matched_entities.append(entity_info)
            similarity_scores.append(result.score if hasattr(result, 'score') else 0.0)

        self.current_results.vector_search = VectorSearchResult(
            query=query,
            query_embedding=query_embedding,
            matched_entities=matched_entities,
            similarity_scores=similarity_scores,
            search_time=search_time
        )

    def collect_entity_mapping(
        self,
        original_query: str,
        processed_query: str,
        selected_entities: List[Entity],
        excluded_entities: List[str] = None,
        included_entities: List[Entity] = None
    ) -> None:
        """收集实体映射结果"""
        if not self.current_results:
            return

        # 转换实体为字典格式
        def entity_to_dict(entity: Entity) -> Dict:
            return {
                "id": entity.id,
                "title": entity.title,
                "description": entity.description,
                "rank": entity.rank,
                "category": getattr(entity, 'category', 'unknown')
            }

        selected_entities_dict = [entity_to_dict(e) for e in selected_entities]
        included_entities_dict = [entity_to_dict(e) for e in (included_entities or [])]

        self.current_results.entity_mapping = EntityMappingResult(
            original_query=original_query,
            processed_query=processed_query,
            selected_entities=selected_entities_dict,
            excluded_entities=excluded_entities or [],
            included_entities=included_entities_dict,
            entity_count=len(selected_entities_dict)
        )

    def collect_context_building(
        self,
        community_context: str,
        local_context: str,
        text_unit_context: str,
        conversation_context: str,
        final_context: str,
        context_tokens: Dict[str, int],
        context_data: Dict[str, pd.DataFrame]
    ) -> None:
        """收集上下文构建结果"""
        if not self.current_results:
            return

        # 将DataFrame转换为可序列化的格式
        serializable_context_data = {}
        for key, df in context_data.items():
            if isinstance(df, pd.DataFrame):
                serializable_context_data[key] = df.to_dict('records')
            else:
                serializable_context_data[key] = df

        self.current_results.context_building = ContextBuildResult(
            community_context=community_context,
            local_context=local_context,
            text_unit_context=text_unit_context,
            conversation_context=conversation_context,
            final_context=final_context,
            context_tokens=context_tokens,
            context_data=serializable_context_data
        )

    def collect_final_prompt(self, prompt: str) -> None:
        """收集最终发送给LLM的prompt"""
        if not self.current_results:
            return
        self.current_results.llm_prompt = prompt

    def finish_collection(self) -> IntermediateResults:
        """完成收集并返回结果"""
        if not self.current_results:
            raise ValueError("No collection in progress")

        self.current_results.total_time = time.time() - self.start_time
        return self.current_results

    def save_results(self, results: IntermediateResults = None) -> str:
        """保存中间结果到文件"""
        if results is None:
            results = self.finish_collection()

        filename = f"intermediate_results_{results.query_id}_{int(results.timestamp)}.json"
        filepath = self.output_dir / filename

        # 准备可序列化的数据
        results_dict = results.to_dict()

        # 处理DataFrame等不可序列化的对象
        if results.context_building:
            # context_data已经在collect_context_building中处理
            pass

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def get_summary(self, results: IntermediateResults = None) -> Dict[str, Any]:
        """获取中间结果的摘要信息"""
        if results is None:
            results = self.current_results

        if not results:
            return {}

        summary = {
            "query_id": results.query_id,
            "total_time": results.total_time,
            "original_query": results.original_query
        }

        if results.vector_search:
            summary.update({
                "vector_search_time": results.vector_search.search_time,
                "matched_entities_count": len(results.vector_search.matched_entities),
                "avg_similarity_score": sum(results.vector_search.similarity_scores) / len(results.vector_search.similarity_scores) if results.vector_search.similarity_scores else 0
            })

        if results.entity_mapping:
            summary.update({
                "selected_entities_count": results.entity_mapping.entity_count,
                "excluded_entities_count": len(results.entity_mapping.excluded_entities)
            })

        if results.context_building:
            summary.update({
                "final_context_length": len(results.context_building.final_context),
                "context_tokens_total": sum(results.context_building.context_tokens.values())
            })

        if results.llm_prompt:
            summary.update({
                "final_prompt_length": len(results.llm_prompt)
            })

        return summary


class EnhancedLocalSearchMixedContext:
    """增强的本地搜索混合上下文构建器，带中间结果收集功能"""

    def __init__(self, original_context, results_collector: IntermediateResultsCollector):
        self.original_context = original_context
        self.results_collector = results_collector

    def build_context_with_intermediate_results(self, *args, **kwargs) -> ContextBuilderResult:
        """构建上下文并收集中间结果"""
        start_time = time.time()

        # 执行原始的上下文构建
        result = self.original_context.build_context(*args, **kwargs)

        build_time = time.time() - start_time

        # 尝试从kwargs中提取相关信息
        query = kwargs.get('query', args[0] if args else '')

        # 收集上下文构建结果
        if hasattr(result, 'context_chunks'):
            # 由于无法直接访问各部分上下文，这里做简化处理
            self.results_collector.collect_context_building(
                community_context="Community context extracted from final result",
                local_context="Local context extracted from final result",
                text_unit_context="Text unit context extracted from final result",
                conversation_context="Conversation context extracted from final result",
                final_context=result.context_chunks,
                context_tokens={"total": len(str(result.context_chunks))},
                context_data=result.context_records or {}
            )

        return result


# 使用示例代码
if __name__ == "__main__":
    # 创建收集器
    collector = IntermediateResultsCollector()

    # 模拟查询流程
    query_id = "test_query_001"
    original_query = "什么是人工智能？"

    # 开始收集
    collector.start_collection(query_id, original_query)

    # 模拟向量检索结果
    collector.collect_vector_search(
        query=original_query,
        query_embedding=[0.1, 0.2, 0.3],  # 模拟向量
        search_results=[],  # 模拟搜索结果
        search_time=0.05
    )

    # 模拟实体映射结果
    collector.collect_entity_mapping(
        original_query=original_query,
        processed_query=original_query,
        selected_entities=[],  # 模拟选中的实体
        excluded_entities=[],
        included_entities=[]
    )

    # 模拟上下文构建结果
    collector.collect_context_building(
        community_context="社区报告内容...",
        local_context="本地实体关系内容...",
        text_unit_context="文本单元内容...",
        conversation_context="对话历史内容...",
        final_context="最终整合的上下文内容...",
        context_tokens={"community": 1000, "local": 800, "text_unit": 600},
        context_data={}
    )

    # 收集最终prompt
    collector.collect_final_prompt("最终发送给LLM的完整prompt...")

    # 保存结果
    filepath = collector.save_results()
    print(f"中间结果已保存到: {filepath}")

    # 获取摘要
    summary = collector.get_summary()
    print(f"中间结果摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")