"""
指南智能匹配器 - 使用 LLM 进行语义理解和精选
"""
import logging
import re
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.model.guidelines import Guidelines
from app.schema.guideline import GuidelinesMatchResult,GuidelinesRead

logger = logging.getLogger(__name__)


class GuidelineMatcher:
    """指南智能匹配器 - 使用 LLM 从候选列表中选择最匹配的指南"""

    # LLM 选择 Prompt 模板
    MATCH_PROMPT_TEMPLATE = """你是一个医疗指南匹配专家。请根据用户对话上下文，从以下候选指南中选择最合适的一条。

【用户对话上下文】
{context}

【候选指南列表】
{guidelines}

请分析每个候选指南与用户问题的相关度，并返回最合适的一条指南。

思考过程要求：
1. 分析用户的核心需求
2. 评估每个指南的匹配程度
3. 考虑指南的优先级

返回格式：
- 思考过程：[你的分析过程]
- 选择指南ID：[数字ID]
- 置信度：[0.0-1.0之间的数字]
"""

    def __init__(self, db: Session, llm_client):
        """
        初始化指南匹配器

        Args:
            db: 数据库会话
            llm_client: LLM 客户端（用于语义理解）
        """
        self.db = db
        self.llm_client = llm_client

    def refine_with_llm(
        self,
        context: str,
        candidates: List[GuidelinesRead]
    ) -> Tuple[Optional[GuidelinesRead], float, str]:
        """
        使用 LLM 从候选列表中选择最匹配的指南

        Args:
            context: 用户对话上下文
            candidates: 候选指南列表

        Returns:
            (选择的指南, 置信度, 思考过程)
            如果选择失败，返回 (None, 0.0, "")
        """
        if not candidates:
            logger.warning("候选指南列表为空，无法进行 LLM 精选")
            return None, 0.0, ""

        if len(candidates) == 1:
            logger.info(f"只有一条候选指南，直接返回: {candidates[0].id}")
            return candidates[0], 1.0, "只有一条候选，直接返回"

        try:
            # 构造指南列表描述
            guidelines_desc = self._format_guidelines(candidates)

            # 构造 Prompt
            prompt = self.MATCH_PROMPT_TEMPLATE.format(
                context=context,
                guidelines=guidelines_desc
            )

            # 调用 LLM
            logger.info(f"调用 LLM 进行指南精选，候选数量: {len(candidates)}")

            # 这里需要根据项目的 LLM 客户端 API 进行调用
            response = self._call_llm(prompt)

            # 解析 LLM 返回结果
            guideline_id, confidence, thinking = self._parse_llm_response(response)

            if guideline_id is None:
                logger.warning("LLM 未能返回有效的指南 ID，使用第一条候选")
                return candidates[0], 0.5, thinking or "LLM 返回无效，使用默认"

            # 查找选中的指南
            selected_guideline = None
            for candidate in candidates:
                if candidate.id == guideline_id:
                    selected_guideline = candidate
                    break

            if selected_guideline is None:
                logger.warning(f"LLM 返回的指南 ID {guideline_id} 不在候选列表中，使用第一条候选")
                return candidates[0], 0.3, thinking or "LLM 选择无效，使用默认"

            logger.info(f"LLM 选择了指南 {guideline_id}，置信度: {confidence}")
            return selected_guideline, confidence, thinking

        except Exception as e:
            logger.error(f"LLM 精选失败: {e}", exc_info=True)
            # 降级策略：返回第一条候选
            return candidates[0], 0.3, f"LLM 调用失败: {str(e)}，使用默认"

    def _format_guidelines(self, candidates: List[GuidelinesRead]) -> str:
        """
        格式化候选指南列表为文本

        Args:
            candidates: 候选指南列表

        Returns:
            格式化后的文本
        """
        lines = []
        for idx, guideline in enumerate(candidates, 1):
            lines.append(f"{idx}. 指南ID: {guideline.id}")
            lines.append(f"   标题: {guideline.title}")
            lines.append(f"   触发条件: {guideline.condition}")
            lines.append(f"   优先级: {guideline.priority}")
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM API

        Args:
            prompt: 提示词

        Returns:
            LLM 的响应文本
        """
        try:
            # 使用项目的 LLM 客户端
            # 这里需要根据实际项目配置调用
            response = self.llm_client.chat.completions.create(
                model="glm-4.5-air",  # 或者配置中的模型
                messages=[
                    {"role": "system", "content": "你是一个专业的AI行动指南匹配助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低温度以获得更稳定的结果
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")
            raise

    def _parse_llm_response(self, response: str) -> Tuple[Optional[int], float, str]:
        """
        解析 LLM 返回的结果

        Args:
            response: LLM 返回的文本

        Returns:
            (指南ID, 置信度, 思考过程)
        """
        try:
            # 提取思考过程
            thinking = ""
            thinking_match = re.search(r'思考过程[：:]\s*(.*?)(?=\n|$)', response, re.DOTALL)
            if thinking_match:
                thinking = thinking_match.group(1).strip()

            # 提取指南 ID
            guideline_id = None
            id_match = re.search(r'选择指南ID[：:]\s*(\d+)', response)
            if id_match:
                guideline_id = int(id_match.group(1))

            # 提取置信度
            confidence = 0.5
            confidence_match = re.search(r'置信度[：:]\s*([0-9.]+)', response)
            if confidence_match:
                try:
                    confidence = float(confidence_match.group(1))
                    confidence = max(0.0, min(1.0, confidence))  # 限制在 0-1 之间
                except ValueError:
                    pass

            return guideline_id, confidence, thinking

        except Exception as e:
            logger.error(f"解析 LLM 响应失败: {e}")
            return None, 0.0, ""

    def get_top_candidates_by_priority(
        self,
        candidates: List[Guidelines],
        top_k: int
    ) -> List[Guidelines]:
        """
        按 priority 降序排序并返回前 K 条

        Args:
            candidates: 候选指南列表
            top_k: 返回数量

        Returns:
            排序后的指南列表
        """
        # 按优先级降序，ID 降序排序
        sorted_candidates = sorted(
            candidates,
            key=lambda g: (g.priority, g.id),
            reverse=True
        )
        return sorted_candidates[:top_k]
