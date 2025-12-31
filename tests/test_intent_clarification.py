#!/usr/bin/env python3
"""
测试意图识别模块的反问功能
验证信息完整性判断和槽位抽取是否正常工作
"""

import sys
import os

# 添加项目路径到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.mcp.intent import MedicalInsuranceIntentRecognizer
import json5

def test_intent_clarification():
    """测试意图识别的反问功能"""
    print("🧪 开始测试意图识别反问功能...")
    print("=" * 60)

    recognizer = MedicalInsuranceIntentRecognizer()

    # 测试用例：涵盖需要反问的各种场景
    test_cases = [
        {
            "query": "怎么报销？",
            "expected_intent": "医疗费用报销办理",
            "should_clarify": True,
            "description": "缺少就医类型的报销查询"
        },
        {
            "query": "异地就医备案怎么办理？",
            "expected_intent": "异地就医备案办理",
            "should_clarify": True,
            "description": "缺少就医地的备案查询"
        },
        {
            "query": "门诊费用怎么报销？",
            "expected_intent": "医疗费用报销办理",
            "should_clarify": False,
            "description": "包含就医类型的完整报销查询"
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
            "query": "医保退休怎么办理？",
            "expected_intent": "医保退休办理",
            "should_clarify": True,
            "description": "缺少退休状态和缴费年限的医保退休查询"
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
        print(f"   改写查询: {result.rewritten_query}")
        print(f"   需要澄清: {result.needs_clarification}")
        if result.needs_clarification:
            print(f"   反问内容: {result.clarification_question}")

        # 验证结果
        success = True
        errors = []

        if test_case['should_clarify'] != result.needs_clarification:
            success = False
            errors.append(f"澄清状态不符: 期望 {test_case['should_clarify']}, 实际 {result.needs_clarification}")

        if result.third_level != test_case['expected_intent']:
            success = False
            errors.append(f"意图识别不符: 期望 {test_case['expected_intent']}, 实际 {result.third_level}")

        # 检查槽位抽取（示例）
        slots = recognizer._extract_slots(test_case['query'])
        print(f"   槽位抽取: {dict(list(slots.items())[:5])}...")  # 只显示前5个

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

    # 保存详细结果到文件
    output = {
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": f"{passed_tests/total_tests*100:.1f}%"
        },
        "test_results": [
            {
                "query": r['query'],
                "success": r['success'],
                "errors": r['errors'],
                "intent_result": {
                    "first_level": r['result'].first_level,
                    "second_level": r['result'].second_level,
                    "third_level": r['result'].third_level,
                    "confidence": r['result'].confidence,
                    "needs_clarification": r['result'].needs_clarification,
                    "clarification_question": r['result'].clarification_question,
                    "rewritten_query": r['result'].rewritten_query
                }
            }
            for r in results
        ]
    }

    with open('intent_clarification_test_results.json', 'w', encoding='utf-8') as f:
        json5.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n📝 详细测试结果已保存到: intent_clarification_test_results.json")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = test_intent_clarification()
    sys.exit(0 if success else 1)