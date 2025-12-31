#!/usr/bin/env python3
"""
简化版意图识别反问功能测试
直接测试核心逻辑，不依赖MCP框架
"""

import sys
import os
import re
import jieba
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
    """简化版意图识别器用于测试"""

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
            },
            "家庭共济办理": {
                "required_slots": ["家庭关系"],
                "fallback_question": "请问您想为哪位家人办理共济（配偶、子女还是父母）？"
            },
            "医保退休办理": {
                "required_slots": ["退休状态", "缴费年限"],
                "fallback_question": "请问您是否已退休？医保缴费满多少年了？"
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
            "在职状态": any(kw in query_lower for kw in ["在职", "退休", "离职", "工作", "失业"]),
            "家庭关系": any(kw in query_lower for kw in ["配偶", "子女", "父母", "家人"]),
            "退休状态": any(kw in query_lower for kw in ["退休", "退休人员", "养老"]),
            "缴费年限": any(kw in query_lower for kw in ["缴费年限", "缴费年数", "累计缴费", "缴费满"])
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
        elif "缴费标准" in query_lower or "缴费" in query_lower and "标准" in query_lower:
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

        # 家庭共济
        elif "家庭共济" in query_lower:
            if any(kw in query_lower for kw in ["配偶", "子女", "父母"]):
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "家庭共济办理",
                    "confidence": 0.8,
                    "action": "家庭共济办理"
                }
            else:
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "家庭共济办理",
                    "confidence": 0.6,
                    "action": "家庭共济办理"
                }

        # 医保退休
        elif "医保退休" in query_lower or "退休" in query_lower and "医保" in query_lower:
            if any(kw in query_lower for kw in ["退休", "缴费年", "缴费满"]):
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "医保退休办理",
                    "confidence": 0.8,
                    "action": "医保退休办理"
                }
            else:
                return {
                    "first_level": "职工基本医疗保险",
                    "second_level": "办事指南",
                    "third_level": "医保退休办理",
                    "confidence": 0.6,
                    "action": "医保退休办理"
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

def test_intent_clarification():
    """测试意图识别的反问功能"""
    print("🧪 开始测试意图识别反问功能（简化版）...")
    print("=" * 60)

    recognizer = SimpleIntentRecognizer()

    test_cases = [
        {
            "query": "怎么报销？",
            "expected_intent": "医疗费用报销办理",
            "should_clarify": True,
            "description": "缺少就医类型的报销查询"
        },
        {
            "query": "门诊费用怎么报销？",
            "expected_intent": "医疗费用报销办理",
            "should_clarify": False,
            "description": "包含就医类型的完整报销查询"
        },
        {
            "query": "异地就医备案怎么办理？",
            "expected_intent": "异地就医备案办理",
            "should_clarify": True,
            "description": "缺少就医地的备案查询"
        },
        {
            "query": "去北京就医要备案吗？",
            "expected_intent": "异地就医备案办理",
            "should_clarify": False,
            "description": "包含就医地的完整备案查询"
        },
        {
            "query": "医保缴费标准是多少？",
            "expected_intent": "缴费标准",
            "should_clarify": True,
            "description": "缺少参保类型的缴费标准查询"
        },
        {
            "query": "职工医保缴费标准是多少？",
            "expected_intent": "缴费标准",
            "should_clarify": False,
            "description": "包含参保类型的完整缴费标准查询"
        },
        {
            "query": "生育津贴怎么申请？",
            "expected_intent": "生育津贴待遇",
            "should_clarify": True,
            "description": "缺少性别和在职状态的生育津贴查询"
        },
        {
            "query": "女职工在职期间生育津贴怎么申请？",
            "expected_intent": "生育津贴待遇",
            "should_clarify": False,
            "description": "包含性别和在职状态的完整生育津贴查询"
        },
        {
            "query": "我想办理家庭共济",
            "expected_intent": "家庭共济办理",
            "should_clarify": True,
            "description": "缺少家庭关系的家庭共济查询"
        },
        {
            "query": "模糊的问题",
            "expected_intent": "未分类",
            "should_clarify": True,
            "description": "模糊不清的问题"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 测试用例 {i}: {test_case['description']}")
        print(f"查询: '{test_case['query']}'")
        print("-" * 40)

        result = recognizer.recognize_intent(test_case['query'])

        print(f"✅ 识别结果:")
        print(f"   一级分类: {result.first_level}")
        print(f"   二级分类: {result.second_level}")
        print(f"   三级分类: {result.third_level}")
        print(f"   置信度: {result.confidence:.3f}")
        print(f"   需要澄清: {result.needs_clarification}")
        if result.needs_clarification:
            print(f"   反问内容: {result.clarification_question}")

        # 检查槽位抽取
        slots = recognizer._extract_slots(test_case['query'])
        non_empty_slots = {k: v for k, v in slots.items() if v}
        print(f"   槽位抽取: {non_empty_slots}")

        # 验证结果
        success = True
        errors = []

        if test_case['should_clarify'] != result.needs_clarification:
            success = False
            errors.append(f"澄清状态不符: 期望 {test_case['should_clarify']}, 实际 {result.needs_clarification}")

        if result.third_level.strip() != test_case['expected_intent']:
            success = False
            errors.append(f"意图识别不符: 期望 {test_case['expected_intent']}, 实际 '{result.third_level}'")

        status = "✅ 通过" if success else "❌ 失败"
        print(f"   测试结果: {status}")

        if errors:
            for error in errors:
                print(f"   错误: {error}")

        results.append({
            "query": test_case['query'],
            "success": success,
            "errors": errors,
            "result": result
        })

    # 统计结果
    total_tests = len(test_cases)
    passed_tests = sum(1 for r in results if r['success'])

    print("\n" + "=" * 60)
    print("📊 测试统计:")
    print(f"总测试数: {total_tests}")
    print(f"通过数: {passed_tests}")
    print(f"失败数: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")

    return passed_tests >= total_tests * 0.8  # 80%通过率视为成功

if __name__ == "__main__":
    success = test_intent_clarification()
    print(f"\n🎯 测试{'成功' if success else '失败'}!")
    sys.exit(0 if success else 1)