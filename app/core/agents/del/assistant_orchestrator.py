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
        enable_guideline_match: bool = True,
        **kwargs
    ) -> Dict:
        """
        处理用户查询的完整流程（重构版 - 集成 Guideline）

        流程：
        1. IntentAgent.call(query) → 意图 + Guideline + 搜索结果
        2. _merge_search_results() 合并 top_k_results + graph_sources
        3. get_prompt_by_intent() → 获取提示词
        4. WorkerAgent.run_with_sources(query, sources, intent, custom_prompt) → 生成答案
        5. 返回完整结果

        Args:
            query: 用户查询
            strategy: 搜索策略（None 则使用默认策略）
            top_k: 返回结果数量（None 则使用默认值）
            enable_guideline_match: 是否启用 Guideline 匹配
            **kwargs: 其他参数（传递给 IntentAgent 和 WorkerAgent）

        Returns:
            Dict: 包含意图分类、Guideline 和生成答案的完整结果
        """
        strategy = strategy or self.default_strategy
        top_k = top_k or self.default_top_k

        self.logger.info(f"处理查询: {query}, 策略: {strategy}")

        # Step 1: 意图识别 + Guideline 匹配 + 搜索
        intent_result = self.intent_agent.call(
            query=query,
            strategy=strategy,
            top_k=top_k,
            enable_guideline_match=enable_guideline_match,
            **kwargs
        )

        self.logger.info(
            f"意图识别结果: {intent_result['main_category']}, "
            f"Guideline匹配: {intent_result['matched']}, "
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

        # Step 3: 获取提示词（新增）
        prompt = self.get_prompt_by_intent(intent_result)

        # Step 4: WorkerAgent 生成答案（传递 custom_prompt）
        answer_result = self.worker_agent.run_with_sources(
            query=query,
            sources=knowledge_sources,
            intent=intent_result,
            custom_prompt=prompt,
            **kwargs
        )

        # Step 5: 返回完整结果
        return {
            "query": query,
            "guideline": intent_result.get("guideline_match"),  # 新增
            "intent": {
                "main_category": intent_result["main_category"],
                "sub_category": intent_result["sub_category"],
                "detail_category": intent_result["detail_category"],
                "confidence": intent_result["confidence"],
                "matched": intent_result["matched"],  # 新增
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
        enable_guideline_match: bool = True,
        **kwargs
    ) -> Iterator[Dict]:
        """
        流式处理查询（重构版 - 集成 Guideline）

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
            enable_guideline_match=enable_guideline_match,
            **kwargs
        )

        yield {
            "type": "intent",
            "data": {
                "main_category": intent_result["main_category"],
                "sub_category": intent_result["sub_category"],
                "confidence": intent_result["confidence"],
                "matched": intent_result["matched"],  # 新增
                "guideline": intent_result.get("guideline_match")  # 新增
            }
        }

        # Step 2: 答案生成（流式）
        yield {"type": "status", "data": "正在生成答案..."}

        search_results = intent_result["search_results"]
        knowledge_sources = self._merge_search_results(
            search_results["top_k_results"],
            search_results["graph_sources"]
        )

        # 获取提示词
        prompt = self.get_prompt_by_intent(intent_result)

        # 流式调用 WorkerAgent（传递 custom_prompt）
        for chunk in self.worker_agent.run_stream_with_sources(
            query=query,
            sources=knowledge_sources,
            intent=intent_result,
            custom_prompt=prompt,
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


    
    def get_prompt_by_intent(self, intent_result: Dict) -> str:
        """
        根据意图识别结果获取对应的提示词

        优先级：
        1. guideline.prompt_template
        2. guideline.action
        3. 默认提示词

        Args:
            intent_result: 意图识别结果字典（来自 IntentAssistant.call()）

        Returns:
            提示词字符串
        """
        # 检查是否匹配到 Guideline
        if intent_result.get("matched") and intent_result.get("guideline_match"):
            guideline_match = intent_result["guideline_match"]

            # 优先使用 prompt_template
            if guideline_match.get("prompt_template"):
                self.logger.info(f"使用 Guideline 自定义提示词: {guideline_match['title']}")
                return guideline_match["prompt_template"]

            # 否则基于 action 构建提示词
            action = guideline_match.get("action", "")
            if action:
                self.logger.info(f"使用 Guideline action 构建提示词: {guideline_match['title']}")
                return f"""# 操作指南
{action}

请严格按照上述指南回答用户问题。"""

        # 降级：使用默认提示词
        self.logger.warning("未匹配到 Guideline，使用默认提示词")
        return """你是厦门市公积金政务服务助手。请基于提供的知识库内容准确回答用户问题。

注意事项：
1. 如果知识库中没有相关信息，请直接说明无法回答
2. 不要编造超出知识库范围的信息
3. 回答要准确、清晰、有条理
4. 必要时引用知识库来源"""
