"""
意图识别 Agent
集成图谱搜索和 baseline 搜索策略，支持策略选择
"""
import time
import logging
import json
from typing import Dict, List, Literal
from dataclasses import dataclass

from app.config.llm_client import chat_client_bot


@dataclass
class IntentResult:
    """意图识别结果"""
    main_category: str          # 一级分类
    sub_category: str           # 二级分类
    detail_category: str        # 三级分类
    confidence: float           # 置信度
    reason: str                 # 分类理由
    search_strategy: str        # 使用的搜索策略

    # 搜索结果
    top_k_results: List[Dict]   # Top-K 搜索结果(向量+BM25)
    graph_sources: List[Dict]   # 图谱 sources 文本片段

    # 元数据
    metadata: Dict              # 包含 entities_count, relationships_count, search_time 等


class IntentAssistant:
    """
    意图识别 Agent

    功能：
    1. 支持两种搜索策略：graph / baseline
    2. 返回意图分类 + 搜索结果
    3. 封装搜索逻辑，保持简单
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = chat_client_bot

        # 意图分类体系
        self.intent_categories = {
            "职工基本医疗保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "参保缴费纠纷处理", "重复参保处理", "退费"],
                "医疗待遇": ["待遇生效时间", "连续参保机制", "医保账户划拨", "大病医保", "医疗救助", "待遇标准", "就医使用"],
                "办事指南": ["转移接续手续办理", "医疗费用报销办理", "异地就医备案办理", "家庭共济办理", "医保退休办理", "个人账户一次性支取办理"]
            },
            "城乡居民医疗保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "重复参保", "退费"],
                "医疗待遇": ["待遇生效时间", "参保长效机制", "医保账户划拨", "大病医保", "医疗救助", "待遇标准", "就医使用"],
                "办事指南": ["医疗费用报销办理", "异地就医备案办理", "家庭共济办理", "转移接续手续办理"]
            },
            "生育保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "参保缴费纠纷处理"],
                "生育待遇": ["生育津贴待遇", "男职工未就业配偶生育医疗费用待遇", "其他待遇"],
                "办事指南": ["生育津贴办理", "男职工未就业配偶生育医疗费用办理"]
            },
            "其他医药政策": {
                "药品（含项目、耗材）政策": ["药品目录", "医疗服务项目目录", "医用耗材目录"],
                "DRG收费及按病种收费政策": ["厦门市定点医疗机构就医", "省内异地定点医疗机构就医"],
                "辅助生殖政策": ["福建省辅助生殖类医疗服务价格项目及省属公立医院项目价格表", "辅助生殖医保支付政策"],
                "补充医疗保险": ["惠厦保"],
                "长期护理险政策": ["未分类"]
            }
        }

    def call(
        self,
        query: str,
        strategy: Literal["graph", "baseline"] = "graph",
        top_k: int = 10,
        **kwargs
    ) -> Dict:
        """
        意图识别调用接口（给 OrchestratorAgent 使用）

        Args:
            query: 用户查询
            strategy: 搜索策略 "graph" | "baseline"
            top_k: 返回结果数量
            **kwargs: 其他搜索参数

        Returns:
            Dict: 包含意图分类和搜索结果的字典（JSON可序列化）
        """
        try:
            result = self.recognize(
                query=query,
                strategy=strategy,
                top_k=top_k,
                **kwargs
            )

            # 转换 IntentResult 为字典
            return {
                "main_category": result.main_category,
                "sub_category": result.sub_category,
                "detail_category": result.detail_category,
                "confidence": result.confidence,
                "reason": result.reason,
                "search_strategy": result.search_strategy,

                # 搜索结果（给 WorkerAgent 使用）
                "search_results": {
                    "top_k_results": result.top_k_results,
                    "graph_sources": result.graph_sources,
                    "metadata": result.metadata
                }
            }

        except Exception as e:
            self.logger.error(f"意图识别失败: {e}")
            return {
                "main_category": "错误",
                "sub_category": "错误",
                "detail_category": "错误",
                "confidence": 0.0,
                "reason": f"意图识别异常: {str(e)}",
                "search_strategy": strategy,
                "search_results": {
                    "top_k_results": [],
                    "graph_sources": [],
                    "metadata": {"error": str(e)}
                }
            }

    def recognize(
        self,
        query: str,
        strategy: Literal["graph", "baseline"] = "graph",
        top_k: int = 10,
        **kwargs
    ) -> IntentResult:
        """
        意图识别主方法

        Args:
            query: 用户查询
            strategy: 搜索策略 "graph" | "baseline"
            top_k: 返回结果数量
            **kwargs: 其他参数

        Returns:
            IntentResult: 包含意图分类和搜索结果的完整对象
        """
        start_time = time.time()

        # 1. 根据策略执行搜索
        if strategy == "graph":
            search_results = self._graph_search_strategy(query, top_k, **kwargs)
        else:  # baseline
            search_results = self._baseline_search_strategy(query, top_k, **kwargs)

        # 2. 执行意图分类（基于搜索结果）
        classification = self._classify_intent(
            query,
            search_results["context_for_classification"],
            strategy
        )

        # 3. 构建返回结果
        search_time = time.time() - start_time

        return IntentResult(
            main_category=classification["main_category"],
            sub_category=classification["sub_category"],
            detail_category=classification["detail_category"],
            confidence=classification["confidence"],
            reason=classification["reason"],
            search_strategy=strategy,
            top_k_results=search_results["top_k_results"],
            graph_sources=search_results["graph_sources"],
            metadata={
                "entities_count": search_results.get("entities_count", 0),
                "relationships_count": search_results.get("relationships_count", 0),
                "total_search_time": search_time,
                **search_results.get("extra_metadata", {})
            }
        )

    def _graph_search_strategy(
        self,
        query: str,
        top_k: int,
        **kwargs
    ) -> Dict:
        """
        图谱搜索策略

        流程：
        1. 调用 RAGSearch._knowledge_graph_search()
        2. 从图谱结果提取 sources
        3. 基于 sources 扩大搜索范围 + rerank
        4. 返回 Top-K 结果 + 图谱 sources
        """
        from app.core.rag.rag_search import RAGSearch

        search_service = RAGSearch()

        # 1. 图谱搜索
        graph_result = search_service._knowledge_graph_search(query)

        # 2. 提取图谱 sources
        graph_sources = []
        entities_count = 0
        relationships_count = 0

        if graph_result.get("status") == "success":
            context_info = graph_result.get("context_info", {})
            entities = context_info.get("entities", [])
            relationships = context_info.get("relationships", [])
            sources = context_info.get("sources", [])

            entities_count = len(entities)
            relationships_count = len(relationships)

            # 提取 sources 文本片段
            graph_sources = [
                {
                    "id": s.get("id", s.get("text_unit_id", "")),
                    "text": s.get("text", ""),
                    "title": s.get("title", ""),
                    "source": "graph"
                }
                for s in sources[:top_k]
            ]

        # 3. 基于 graph_sources 扩大搜索范围
        if graph_sources:
            expanded_results = search_service.expand_and_rerank(
                query=query,
                initial_sources=graph_sources,
                top_k=top_k,
                **kwargs
            )
        else:
            # 降级到 baseline 搜索
            self.logger.warning("图谱搜索未返回 sources，降级到 baseline 搜索")
            expanded_results = search_service.hybrid_search_with_rerank(
                query=query,
                top_k=top_k,
                **kwargs
            )

        # 4. 构建分类上下文
        context_for_classification = {
            "graph_knowledge": graph_result,
            "expanded_results": expanded_results
        }

        return {
            "top_k_results": expanded_results,
            "graph_sources": graph_sources,
            "entities_count": entities_count,
            "relationships_count": relationships_count,
            "context_for_classification": context_for_classification,
            "extra_metadata": {
                "graph_search_success": graph_result.get("status") == "success"
            }
        }

    def _baseline_search_strategy(
        self,
        query: str,
        top_k: int,
        **kwargs
    ) -> Dict:
        """
        Baseline 搜索策略（向量+BM25混合）

        流程：
        1. 调用 RAGSearch.hybrid_search_with_rerank()
        2. 返回 Top-K 结果（无图谱 sources）
        """
        from app.core.rag.rag_search import RAGSearch

        search_service = RAGSearch()

        # 执行混合搜索
        top_k_results = search_service.hybrid_search_with_rerank(
            query=query,
            top_k=top_k,
            **kwargs
        )

        return {
            "top_k_results": top_k_results,
            "graph_sources": [],
            "entities_count": 0,
            "relationships_count": 0,
            "context_for_classification": {
                "baseline_results": top_k_results
            },
            "extra_metadata": {}
        }

    def _classify_intent(
        self,
        query: str,
        search_context: Dict,
        strategy: str
    ) -> Dict:
        """
        基于搜索结果进行意图分类
        """
        # 构建分类提示词
        if strategy == "graph" and "graph_knowledge" in search_context:
            graph_knowledge = search_context["graph_knowledge"]
            prompt = self._build_classification_prompt(query, graph_knowledge)
        else:
            # Baseline 策略使用简化提示词
            prompt = self._build_baseline_classification_prompt(query)

        # 调用 LLM 分类
        try:
            response = self.client.chat.completions.create(
                model="glm-4.5-air",
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的医保政策意图分类专家"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                stream=False,
                extra_body={
                    'enable_thinking': False,
                    "thinking": {
                        "type": "disabled",
                    }
                }
            )

            result_text = response.choices[0].message.content.strip()
            classification = json.loads(result_text)

            return classification

        except Exception as e:
            self.logger.error(f"LLM分类失败: {e}")
            return {
                "main_category": "未识别",
                "sub_category": "未识别",
                "detail_category": "未识别",
                "confidence": 0.0,
                "reason": f"LLM分类异常: {str(e)}"
            }

    def _format_graph_knowledge(self, graph_knowledge: Dict) -> str:
        """
        格式化图谱知识为可读文本

        Args:
            graph_knowledge: 图谱搜索结果字典

        Returns:
            格式化后的文本
        """
        if not graph_knowledge or graph_knowledge.get("status") != "success":
            return ""

        context_info = graph_knowledge.get("context_info", {})
        context = "\n\n相关图谱知识：\n"

        # 格式化实体
        entities = context_info.get("entities", [])
        if entities:
            context += f"\n相关实体（共 {len(entities)} 个）：\n"
            for i, entity in enumerate(entities[:10], 1):
                entity_name = entity.get('title', entity.get('name', ''))
                entity_desc = entity.get('description', '')[:100]
                context += f"{i}. {entity_name}: {entity_desc}...\n"

        # 格式化关系
        relationships = context_info.get("relationships", [])
        if relationships:
            context += f"\n相关关系（共 {len(relationships)} 个）：\n"
            for i, rel in enumerate(relationships[:10], 1):
                source = rel.get('source', '')
                target = rel.get('target', '')
                rel_type = rel.get('label', rel.get('type', ''))
                context += f"{i}. {source} --[{rel_type}]--> {target}\n"

        # 格式化社区报告
        community_reports = context_info.get("community_reports", [])
        if community_reports:
            context += f"\n相关社区报告（共 {len(community_reports)} 个）：\n"
            for i, report in enumerate(community_reports[:5], 1):
                title = report.get('title', '')
                summary = report.get('summary', '')[:150]
                context += f"{i}. {title}: {summary}...\n"

        return context

    def _build_classification_prompt(self, query: str, graph_knowledge: Dict) -> str:
        """
        构建意图分类的提示词

        Args:
            query: 用户查询
            graph_knowledge: 图谱知识数据

        Returns:
            构建好的提示词
        """
        # 格式化图谱知识
        context = self._format_graph_knowledge(graph_knowledge)

        # 格式化类别体系
        category_str = self._format_categories()

        prompt = f"""你是一个专业的医保政策意图分类专家。请根据用户查询和相关参考信息，准确识别用户意图所属的类别。

用户查询：{query}
{context}

可选类别体系：{category_str}

请按照以下要求进行分类：
1. 分析用户查询的主要意图和关键词
2. 参考相关信息的上下文内容
3. 选择最匹配的一级分类、二级分类和三级分类
4. 如果你判断无法匹配，请返回未分类
5. 返回JSON格式的分类结果

返回格式示例：
{{
    "main_category": "职工基本医疗保险",
    "sub_category": "参保缴费",
    "detail_category": "参保对象",
    "confidence": 0.95,
    "reason": "用户询问的是职工基本医疗保险的参保对象问题，关键词匹配度高"
}}

请直接返回JSON结果，不要包含其他说明文字。"""

        return prompt

    def _build_baseline_classification_prompt(self, query: str) -> str:
        """构建 baseline 分类提示词（简化版，不依赖图谱）"""
        category_str = self._format_categories()

        prompt = f"""你是医保政策意图分类专家。请根据用户查询识别意图类别。

用户查询：{query}

可选类别体系：{category_str}

请返回JSON格式的分类结果：
{{
    "main_category": "职工基本医疗保险",
    "sub_category": "参保缴费",
    "detail_category": "参保对象",
    "confidence": 0.95,
    "reason": "关键词匹配度高"
}}

请直接返回JSON，不要包含其他说明文字。"""

        return prompt

    def _format_categories(self) -> str:
        """格式化类别体系为字符串"""
        category_str = ""
        for main_cat, sub_cats in self.intent_categories.items():
            category_str += f"\n{main_cat}：\n"
            for sub_cat, details in sub_cats.items():
                category_str += f"  - {sub_cat}：{', '.join(details)}\n"
        return category_str




