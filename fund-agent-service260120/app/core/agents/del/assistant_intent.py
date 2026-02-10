"""
意图识别 Agent
集成图谱搜索和 baseline 搜索策略，支持策略选择
"""
import time
import logging
import json
from typing import Dict, List, Literal, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.config.llm_client import chat_client_bot


@dataclass
class IntentResult:
    """意图识别结果（重构版 - 集成 Guideline 匹配）"""

    # ===== 新增字段：Guideline 匹配 =====
    guideline_match: Optional[Dict]  # Guideline 匹配结果（如果成功）
    matched: bool                    # 是否成功匹配到 Guideline
    fallback_mode: bool              # 是否使用降级模式

    # ===== 保留字段：向后兼容 =====
    main_category: str          # 一级分类（映射 guideline.title）
    sub_category: str           # 二级分类（映射 guideline.title）
    detail_category: str        # 三级分类（映射 guideline.action）
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
    意图识别 Agent（重构版 - 集成 Guideline 匹配）

    功能：
    1. 支持 Guideline 智能匹配
    2. 支持两种搜索策略：graph / baseline
    3. 返回意图分类 + 搜索结果
    4. 封装搜索逻辑，保持简单
    """

    def __init__(self, db: Optional[Session] = None):
        """
        初始化 IntentAgent

        Args:
            db: 数据库会话（可选，延迟初始化）
        """
        self.logger = logging.getLogger(__name__)
        self.client = chat_client_bot
        self._db = db  # 数据库会话（延迟初始化）
        self._guideline_service = None  # GuidelinesService（延迟初始化）

        # 意图分类体系（降级时使用）
        self.intent_categories = {
            "公积金缴存业务": {
                "缴存管理": ["缴存对象", "缴存基数与比例", "缴存方式（单位/个人）", "缴存变更（增员/减员）", "补缴与缓缴规定", "缴存纠纷处理"],
                "缴存相关": ["缴存明细查询", "缴存证明开具", "汇缴托收办理", "退费办理", "重复缴存处理"],
                "缴存办理指南": ["单位缴存登记", "个人自愿缴存申请", "缴存基数调整办理", "单位缴存信息变更"]
            },
            "公积金提取业务": {
                "提取类型": ["购房提取", "租房提取", "离职提取", "退休提取", "代际互助提取", "其他提取（出境/大病等）"],
                "提取管理": ["提取条件", "提取额度", "提取频次", "提取限制"],
                "提取办理指南": ["提取材料准备", "线上提取办理", "线下提取办理", "提取进度查询", "提取到账查询"]
            },
            "公积金贷款业务": {
                "贷款申请": ["贷款条件", "贷款额度计算", "贷款期限规定", "贷款利率标准", "贷款申请材料"],
                "贷款管理": ["还款方式", "还款额度调整", "提前还款规定", "贷款展期办理", "贷款变更（还款账户/方式）"],
                "贷款办理指南": ["贷款申请流程", "贷款审批时限", "异地贷款办理", "商转公贷款办理", "贷款进度查询"]
            },
            "公积金账户管理业务": {
                "账户维护": ["个人账户设立", "账户封存与启封", "账户信息变更", "账户注销", "异地转移接续"],
                "账户查询": ["账户余额查询", "账户状态查询", "业务办理记录查询", "个人缴存证明打印"],
                "账户办理指南": ["单位账户管理", "个人账户异地转入", "账户信息更正办理", "家庭共济账户绑定"]
            },
            "其他公积金政策": {
                "专项业务政策": ["代际互助业务", "老旧住宅加装电梯提取", "保障性住房相关公积金政策"],
                "补充政策": ["公积金政策法规解读", "便民服务（上门/预约）", "线上渠道操作指引", "受托银行业务网点查询"]
            }
        }

    @property
    def db(self) -> Session:
        """延迟获取数据库连接"""
        if self._db is None:
            from app.config.database import SessionLocal
            self._db = SessionLocal()
        return self._db

    @property
    def guideline_service(self):
        """延迟初始化 GuidelinesService"""
        if self._guideline_service is None:
            from app.service.guidelines import GuidelinesService
            self._guideline_service = GuidelinesService(self.db)
        return self._guideline_service

    def close(self):
        """关闭数据库连接"""
        if self._db:
            self._db.close()
            self._db = None
            self._guideline_service = None

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭连接"""
        self.close()

    def call(
        self,
        query: str,
        strategy: Literal["graph", "baseline"] = "graph",
        top_k: int = 10,
        enable_guideline_match: bool = True,
        **kwargs
    ) -> Dict:
        """
        意图识别调用接口（给 OrchestratorAgent 使用）

        Args:
            query: 用户查询
            strategy: 搜索策略 "graph" | "baseline"
            top_k: 返回结果数量
            enable_guideline_match: 是否启用 Guideline 匹配
            **kwargs: 其他搜索参数

        Returns:
            Dict: 包含意图分类和搜索结果的字典（JSON可序列化）
        """
        try:
            result = self.recognize(
                query=query,
                strategy=strategy,
                top_k=top_k,
                enable_guideline_match=enable_guideline_match,
                **kwargs
            )

            # 转换 IntentResult 为字典
            return {
                # Guideline 相关（新增）
                "guideline_match": result.guideline_match,
                "matched": result.matched,
                "fallback_mode": result.fallback_mode,

                # 向后兼容字段
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
                "guideline_match": None,
                "matched": False,
                "fallback_mode": True,
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
        enable_guideline_match: bool = True,
        guideline_threshold: float = 0.7,
        **kwargs
    ) -> IntentResult:
        """
        意图识别主方法（重构版 - 集成 Guideline 匹配）

        Args:
            query: 用户查询
            strategy: 搜索策略 "graph" | "baseline"
            top_k: 返回结果数量
            enable_guideline_match: 是否启用 Guideline 匹配
            guideline_threshold: Guideline 匹配置信度阈值
            **kwargs: 其他参数

        Returns:
            IntentResult: 包含意图分类和搜索结果的完整对象
        """
        start_time = time.time()

        # Step 1: 根据策略执行搜索
        if strategy == "graph":
            search_results = self._graph_search_strategy(query, top_k, **kwargs)
        else:  # baseline
            search_results = self._baseline_search_strategy(query, top_k, **kwargs)

        # Step 2: Guideline 匹配（新增）
        guideline_match = None
        matched = False

        if enable_guideline_match:
            try:
                guideline_match = self.guideline_service.match_guideline_by_context(
                    context=query,
                    similarity_threshold=guideline_threshold,
                    use_llm_refinement=True
                )

                if guideline_match and guideline_match.confidence >= guideline_threshold:
                    matched = True
                    self.logger.info(
                        f"Guideline匹配成功: {guideline_match.title} "
                        f"(置信度: {guideline_match.confidence:.3f})"
                    )
                else:
                    confidence_val = guideline_match.confidence if guideline_match else 0.0
                    self.logger.warning(
                        f"Guideline匹配失败或置信度过低 "
                        f"({confidence_val:.3f} < {guideline_threshold})"
                    )
            except Exception as e:
                self.logger.error(f"Guideline匹配异常: {e}", exc_info=True)

        # Step 3: 构建分类信息
        if matched and guideline_match:
            classification = self._build_classification_from_guideline(guideline_match)
        else:
            # 降级：使用原有的 LLM 分类
            classification = self._classify_intent(
                query,
                search_results["context_for_classification"],
                strategy
            )

        # Step 4: 构建返回结果
        search_time = time.time() - start_time

        return IntentResult(
            # 新增字段
            guideline_match=guideline_match.model_dump() if guideline_match else None,
            matched=matched,
            fallback_mode=not matched,

            # 向后兼容字段
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
                "guideline_matched": matched,
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

    def _build_classification_from_guideline(
        self,
        guideline_match
    ) -> Dict:
        """
        从 Guideline 匹配结果构建向后兼容的分类信息

        Args:
            guideline_match: Guideline 匹配结果对象

        Returns:
            分类信息字典
        """
        return {
            "main_category": guideline_match.title,
            "sub_category": guideline_match.title[:50],  # 截断
            "detail_category": guideline_match.action[:50] if guideline_match.action else "",
            "confidence": guideline_match.confidence,
            "reason": f"Guideline匹配成功 (方法: {guideline_match.match_method}, "
                      f"分数: {guideline_match.match_score:.3f})"
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
                        "content": "你是专业的公积金政策意图分类专家"
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

        prompt = f"""你是一个专业的公积金政策意图分类专家。请根据用户查询和相关参考信息，准确识别用户意图所属的类别。

        用户查询：{query}
        {context}

        可选类别体系：{category_str}

        请按照以下要求进行分类：
        1. 分析用户查询的主要意图和关键词（如缴存、提取、贷款、转移等）
        2. 参考相关信息的上下文内容，匹配公积金业务场景
        3. 选择最匹配的一级分类、二级分类和三级分类
        4. 如果你判断无法匹配任何类别，请返回"未分类"
        5. 返回JSON格式的分类结果，置信度范围0-1

        返回格式示例：
        {{
            "main_category": "公积金缴存业务",
            "sub_category": "缴存管理",
            "detail_category": "缴存对象",
            "confidence": 0.95,
            "reason": "用户询问的是公积金缴存对象相关问题，关键词与三级分类匹配度高"
        }}

        请直接返回JSON结果，不要包含其他说明文字。"""

        return prompt

    def _build_baseline_classification_prompt(self, query: str) -> str:
        """构建 baseline 分类提示词（简化版，不依赖图谱）"""
        category_str = self._format_categories()

        prompt = f"""你是公积金政策意图分类专家。请根据用户查询识别意图类别。

        用户查询：{query}

        可选类别体系：{category_str}

        请返回JSON格式的分类结果，置信度范围0-1：
        {{
            "main_category": "公积金缴存业务",
            "sub_category": "缴存管理",
            "detail_category": "缴存对象",
            "confidence": 0.95,
            "reason": "关键词与分类匹配度高"
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




