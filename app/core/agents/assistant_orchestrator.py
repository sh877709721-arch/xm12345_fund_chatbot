"""
Orchestrator-Worker 架构重构

OrchestratorAgent 负责协调 IntentAgent 和 WorkerAgent
"""
import logging
from typing import Dict, List, Iterator, Literal, Optional

from app.core.agents.assistant_intent import IntentAssistant,IntentResult
from app.core.agents.assistant_worker import WorkerAgent
from app.core.agents.prompts import INTENT_PROMPT_MAPPING

class OrchestratorAgent:
    """Orchestrator 协调器 - 整合意图识别和答案生成"""

    def __init__(
        self,
        default_strategy: Literal["graph", "baseline"] = "graph",
        default_top_k: int = 10
    ):
        """
        初始化 Orchestrator

        Args:
            default_strategy: 默认搜索策略
            default_top_k: 默认返回结果数量
        """
        self.intent_agent = IntentAssistant()
        self.worker_agent = WorkerAgent()
        self.default_strategy = default_strategy
        self.default_top_k = default_top_k
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        query: str,
        strategy: Literal["graph", "baseline"] = "graph",
        top_k: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        处理用户查询的完整流程

        流程：
        1. IntentAgent.call(query, strategy) → 意图 + 搜索结果
        2. _merge_search_results() 合并 top_k_results + graph_sources
        3. WorkerAgent.run_with_sources(query, sources, intent) → 生成答案
        4. 返回完整结果

        Args:
            query: 用户查询
            strategy: 搜索策略（None 则使用默认策略）
            top_k: 返回结果数量（None 则使用默认值）
            **kwargs: 其他参数（传递给 IntentAgent 和 WorkerAgent）

        Returns:
            Dict: 包含意图分类和生成答案的完整结果
        """
        strategy = strategy or self.default_strategy
        top_k = top_k or self.default_top_k

        self.logger.info(f"处理查询: {query}, 策略: {strategy}")

        # Step 1: 意图识别 + 搜索
        intent_result = self.intent_agent.call(
            query=query,
            strategy=strategy,
            top_k=top_k,
            **kwargs
        )

        self.logger.info(
            f"意图识别结果: {intent_result['main_category']}/"
            f"{intent_result['sub_category']}, "
            f"置信度: {intent_result['confidence']}"
        )

        # Step 2: 合并搜索结果
        search_results = intent_result["search_results"]
        top_k_results = search_results["top_k_results"]
        graph_sources = search_results["graph_sources"]

        # 合并搜索结果作为知识语料
        knowledge_sources = self._merge_search_results(
            top_k_results, graph_sources
        )

        self.logger.info(f"合并后搜索结果数量: {len(knowledge_sources)}")

        # Step 3: WorkerAgent 生成答案
        answer_result = self.worker_agent.run_with_sources(
            query=query,
            sources=knowledge_sources,
            intent=intent_result,
            **kwargs
        )

        # Step 4: 返回完整结果
        return {
            "query": query,
            "intent": {
                "main_category": intent_result["main_category"],
                "sub_category": intent_result["sub_category"],
                "detail_category": intent_result["detail_category"],
                "confidence": intent_result["confidence"],
                "reason": intent_result["reason"],
                "search_strategy": intent_result["search_strategy"]
            },
            "search_metadata": search_results["metadata"],
            "answer": answer_result
        }

    def process_stream(
        self,
        query: str,
        strategy: Literal["graph", "baseline"] = None,
        top_k: Optional[int] = None,
        **kwargs
    ) -> Iterator[Dict]:
        """
        流式处理查询（支持流式输出）

        Yields:
            Dict: 包含状态更新的流式数据
                - {"type": "intent", "data": {...}}
                - {"type": "answer_chunk", "data": "..."}
                - {"type": "done", "data": {...}}
        """
        strategy = strategy or self.default_strategy
        top_k = top_k or self.default_top_k

        # Step 1: 意图识别
        yield {"type": "status", "data": "正在进行意图识别..."}

        intent_result = self.intent_agent.call(
            query=query,
            strategy=strategy,
            top_k=top_k,
            **kwargs
        )

        yield {
            "type": "intent",
            "data": {
                "main_category": intent_result["main_category"],
                "sub_category": intent_result["sub_category"],
                "confidence": intent_result["confidence"]
            }
        }

        # Step 2: 答案生成（流式）
        yield {"type": "status", "data": "正在生成答案..."}

        search_results = intent_result["search_results"]
        knowledge_sources = self._merge_search_results(
            search_results["top_k_results"],
            search_results["graph_sources"]
        )

        # 流式调用 WorkerAgent
        for chunk in self.worker_agent.run_stream_with_sources(
            query=query,
            sources=knowledge_sources,
            intent=intent_result,
            **kwargs
        ):
            yield {"type": "answer_chunk", "data": chunk}

        # Step 3: 完成
        yield {"type": "done", "data": {"status": "completed"}}

    def _merge_search_results(
        self,
        top_k_results: List[Dict],
        graph_sources: List[Dict]
    ) -> List[Dict]:
        """
        合并 Top-K 结果和图谱 sources

        策略：
        1. 去重（按 ID）
        2. graph_sources 优先（如果有）
        3. 限制总数不超过 default_top_k
        """
        merged = {}

        # 优先添加 graph_sources
        for source in graph_sources:
            source_id = source.get("id")
            if source_id:
                merged[source_id] = {**source, "priority": "graph"}

        # 添加 top_k_results（去重）
        for result in top_k_results:
            result_id = result.get("id")
            if result_id and result_id not in merged:
                merged[result_id] = {**result, "priority": "top_k"}

        # 转换为列表并排序（graph 优先）
        merged_list = list(merged.values())
        merged_list.sort(
            key=lambda x: (
                x.get("priority") == "graph",
                x.get("rerank_score", x.get("merged_score", 0))
            ),
            reverse=True
        )

        return merged_list[:self.default_top_k]


    
    def get_prompt_by_intent(self, intent_result: IntentResult) -> str:
        """
        根据意图分类结果获取对应的提示词

        Args:
            intent_result: 意图分类结果

        Returns:
            对应的提示词字符串
        """
        # 根据置信度选择最合适的意图
        pass