#!/usr/bin/env python3
"""
最终演示：医疗保险意图识别反问功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 将简化版识别器代码直接包含在此文件中
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class IntentResult:
    """意图识别结果"""
    first_level: str
    second_level: str
    third_level: str
    confidence: float
    action: str
    rewritten_query: str
    needs_clarification: bool
    clarification_question: str

class SimpleIntentRecognizer:
    """简化版意图识别器用于演示"""

    def __init__(self):
        self.completeness_rules = self._build_completeness_rules()

    def _build_completeness_rules(self) -> Dict:
        """构建信息完整性规则字典"""
        return {
            "医疗费用报销办理": {
                "required_slots": ["就医类型"],
                "fallback_question": "请问您需要报销的是门诊还是住院费用？"
            },
            "异地就医备案办理": {
                "required_slots": ["就医地"],
                "fallback_question": "请问您计划去哪个城市就医？"
            },
            "缴费标准": {
                "required_slots": ["参保类型"],
                "fallback_question": "请问您想了解职工医保还是居民医保的缴费标准？"
            },
            "生育津贴待遇": {
                "required_slots": ["性别", "在职状态"],
                "fallback_question": "请问您是男职工还是女职工？目前是否在职？"
            }
        }

    def _extract_slots(self, query: str) -> Dict[str, bool]:
        """从查询中抽取关键槽位是否存在"""
        query_lower = query.lower()
        return {
            "就医类型": any(kw in query_lower for kw in ["门诊", "住院", "急诊", "门急诊"]),
            "就医地": any(kw in query_lower for kw in [
                "北京", "上海", "厦门", "外地", "城市", "某地", "哪个城市", "广州", "深圳", "杭州"
            ]),
            "参保类型": any(kw in query_lower for kw in [
                "职工", "灵活就业", "居民", "学生", "老人", "城乡居民", "单位职工", "在职人员"
            ]),
            "性别": any(kw in query_lower for kw in ["男", "女", "男性", "女性", "先生", "女士"]),
            "在职状态": any(kw in query_lower for kw in ["在职", "退休", "离职", "工作", "失业"])
        }

    def _simple_intent_match(self, query: str) -> Dict:
        """简单的意图匹配逻辑"""
        query_lower = query.lower()

        # 报销相关
        if "报销" in query_lower:
            if "门诊" in query_lower or "住院" in query_lower:
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "医疗费用报销办理",
                    "confidence": 0.8,
                    "action": "医疗费用报销办理"
                }
            else:
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "医疗费用报销办理",
                    "confidence": 0.7,
                    "action": "医疗费用报销办理"
                }

        # 异地就医备案
        elif ("就医" in query_lower and any(kw in query_lower for kw in ["异地", "外地"])) or \
             (any(city in query_lower for city in ["北京", "上海", "厦门", "广州", "深圳"]) and "就医" in query_lower):
            if any(city in query_lower for city in ["北京", "上海", "厦门", "广州", "深圳"]):
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "异地就医备案办理",
                    "confidence": 0.8,
                    "action": "异地就医备案办理"
                }
            else:
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "异地就医备案办理",
                    "confidence": 0.7,
                    "action": "异地就医备案办理"
                }

        # 缴费标准
        elif "缴费标准" in query_lower or ("缴费" in query_lower and "标准" in query_lower):
            if any(kw in query_lower for kw in ["职工", "居民", "灵活就业"]):
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "参保缴费",
                    "third_level": "缴费标准",
                    "confidence": 0.8,
                    "action": "缴费标准"
                }
            else:
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "参保缴费",
                    "third_level": "缴费标准",
                    "confidence": 0.6,
                    "action": "缴费标准"
                }

        # 生育津贴
        elif "生育津贴" in query_lower:
            if any(kw in query_lower for kw in ["男", "女"]) and any(kw in query_lower for kw in ["在职", "工作"]):
                return {
                    "first_level": "生育保险",
                    "second_level": "生育待遇",
                    "third_level": "生育津贴待遇",
                    "confidence": 0.8,
                    "action": "生育津贴待遇"
                }
            else:
                return {
                    "first_level": "生育保险",
                    "second_level": "生育待遇",
                    "third_level": "生育津贴待遇",
                    "confidence": 0.7,
                    "action": "生育津贴待遇"
                }

        # 默认未分类
        else:
            return {
                "first_level": "未分类",
                "second_level": "",
                "third_level": "",
                "confidence": 0.0,
                "action": ""
            }

    def recognize_intent(self, query: str) -> IntentResult:
        """识别用户意图"""
        # 简单意图匹配
        intent_result = self._simple_intent_match(query)

        # 完整性判断
        needs_clarification = False
        clarification_question = ""

        # 获取当前三级意图
        third_level_key = intent_result.get("third_level") or intent_result.get("second_level")
        completeness_rule = self.completeness_rules.get(third_level_key)

        if completeness_rule:
            slots = self._extract_slots(query)
            missing = [slot for slot in completeness_rule["required_slots"] if not slots.get(slot, False)]
            if missing:
                needs_clarification = True
                clarification_question = completeness_rule["fallback_question"]

        # 低置信度也视为需澄清
        if not needs_clarification and intent_result["confidence"] < 0.3:
            needs_clarification = True
            clarification_question = "您的问题不够明确，请具体说明您想了解的医保事项（如缴费、报销、异地就医等）。"

        return IntentResult(
            first_level=intent_result["first_level"],
            second_level=intent_result["second_level"],
            third_level=intent_result["third_level"],
            confidence=intent_result["confidence"],
            action=intent_result["action"],
            rewritten_query=f"[改写] {query}",
            needs_clarification=needs_clarification,
            clarification_question=clarification_question
        )

def demo_intent_with_clarification():
    """演示意图识别的反问功能"""
    print("🎯 医保意图识别系统演示")
    print("展示信息完整性判断和智能反问功能")
    print("=" * 60)

    recognizer = SimpleIntentRecognizer()

    # 示例查询
    test_queries = [
        {
            "query": "怎么报销？",
            "scenario": "信息不足 - 需要澄清就医类型"
        },
        {
            "query": "门诊费用怎么报销？",
            "scenario": "信息完整 - 可以直接回答"
        },
        {
            "query": "异地就医备案怎么办理？",
            "scenario": "信息不足 - 需要澄清就医地"
        },
        {
            "query": "去北京就医要备案吗？",
            "scenario": "信息完整 - 可以直接回答"
        },
        {
            "query": "医保缴费标准是多少？",
            "scenario": "信息不足 - 需要澄清参保类型"
        },
        {
            "query": "生育津贴怎么申请？",
            "scenario": "信息不足 - 需要澄清性别和在职状态"
        }
    ]

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🔍 示例 {i}: {test_case['scenario']}")
        print(f"用户问题: '{test_case['query']}'")
        print("-" * 40)

        # 调用意图识别
        result = recognizer.recognize_intent(test_case['query'])

        # 显示识别结果
        print(f"📍 意图识别:")
        print(f"   路径: {result.first_level} > {result.second_level} > {result.third_level}")
        print(f"   置信度: {result.confidence:.3f}")
        print(f"   改写查询: {result.rewritten_query}")

        # 显示完整性判断结果
        print(f"\n🤖 信息完整性:")
        if result.needs_clarification:
            print(f"   ❌ 信息不足")
            print(f"   💬 反问: {result.clarification_question}")
        else:
            print(f"   ✅ 信息充足")
            print(f"   💡 可以直接回答用户问题")

        # 显示槽位提取结果
        slots = recognizer._extract_slots(test_case['query'])
        filled_slots = {k: v for k, v in slots.items() if v}
        print(f"   🔍 槽位提取: {filled_slots}")

        print("\n" + "=" * 60)

    print("\n📋 功能总结:")
    print("✅ 意图分类 - 准确识别用户医保需求")
    print("✅ 信息完整性判断 - 检测关键信息是否缺失")
    print("✅ 智能反问 - 生成针对性澄清问题")
    print("✅ 槽位抽取 - 识别用户提供的具体信息")
    print("✅ 查询改写 - 优化查询以便后续处理")

    print("\n🎯 ReAct框架集成价值:")
    print("• Agent可根据needs_clarification字段决定是否反问")
    print("• clarification_question提供预设的反问内容")
    print("• 避免重复询问用户已提供的信息")
    print("• 提高对话系统的专业性和用户体验")

if __name__ == "__main__":
    demo_intent_with_clarification()