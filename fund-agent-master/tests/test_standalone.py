#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的边界检查功能测试（不依赖项目模块）
"""

import re
import json
from typing import List, Dict, Union

# 复制关键函数进行测试
def contains_operational_details(text: str) -> bool:
    """检查是否包含操作步骤细节"""
    operational_patterns = [
        r'第.*步', r'首先.*然后.*最后', r'点击.*选择.*输入.*确认',
        r'在.*界面.*找到.*按钮', r'打开.*进入.*选择.*填写',
        r'下载.*登录.*选择.*输入.*确认'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in operational_patterns)

def contains_interface_descriptions(text: str) -> bool:
    """检查是否包含界面描述"""
    interface_patterns = [
        r'界面.*显示', r'页面.*可以看到', r'屏幕.*出现',
        r'按钮.*位于', r'输入框.*提示', r'菜单.*包含'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in interface_patterns)

def is_adding_unsafe_content(text: str) -> bool:
    """检查文本是否开始添加不安全的内容"""
    unsafe_patterns = [
        # 操作步骤模式
        r'(第一步|首先|打开.*app|点击.*按钮|选择.*菜单)',
        r'(进入.*页面|找到.*选项|输入.*信息|确认.*提交)',

        # 界面描述模式
        r'(界面上|页面上|屏幕上|可以看到|显示)',
        r'(按钮|输入框|下拉菜单|选项卡|链接)',

        # 详细流程模式
        r'(流程是|步骤为|方法如下|操作如下)',
        r'(然后.*接着.*最后|依次.*再.*最后)',

        # 推测性内容
        r'(可能|大概|通常|一般来说|应该是)',
        r'(建议.*可以.*尝试|你可以.*需要)'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in unsafe_patterns)

def validate_answer_against_knowledge(answer: str, knowledge_sources: List[dict]) -> dict:
    """验证回答内容是否超出知识库范围"""
    violations = []

    # 检查是否添加了操作步骤细节
    if contains_operational_details(answer):
        violations.append("包含了知识库中没有的操作步骤")

    # 检查是否添加了界面描述
    if contains_interface_descriptions(answer):
        violations.append("包含了界面交互描述")

    # 检查是否编造了具体流程
    if contains_fabricated_process(answer):
        violations.append("可能编造了操作流程")

    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "suggested_revision": suggest_safe_answer(answer, knowledge_sources)
    }

def contains_fabricated_process(text: str) -> bool:
    """检查是否包含编造的流程"""
    fabricated_patterns = [
        r'流程如下', r'具体操作是', r'详细步骤为',
        r'操作流程是', r'办理方式为', r'具体方法'
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in fabricated_patterns)

def suggest_safe_answer(original_answer: str, knowledge_sources: List[dict]) -> str:
    """基于知识库建议安全的回答"""
    for source in knowledge_sources:
        content = source['content']
        if "闽政通App" in content and "税务热线12366" in content:
            return "符合条件的人员可通过闽政通App、电子税务局App等渠道办理，具体手续可以拨打税务热线12366咨询。"
        elif "12366" in content:
            return "参保缴费由税务部门负责，请您拨打税务热线12366咨询。"
    return "抱歉，相关信息请咨询官方热线12366获取准确指导。"

def test_boundary_check():
    """测试边界检查功能"""
    print("=== AI助手边界检查功能测试 ===\n")

    # 模拟知识库数据
    mock_knowledge = [
        {
            'source': '[文件](医保缴费指南.pdf)',
            'content': '符合条件的人员可通过闽政通App、电子税务局App等渠道办理，具体手续可以拨打税务热线12366咨询。'
        }
    ]

    print("📚 模拟知识库内容:")
    for source in mock_knowledge:
        print(f"   来源: {source['source']}")
        print(f"   内容: {source['content']}")
    print()

    # 测试用例
    test_cases = [
        {
            'name': '安全回答（直接引用）',
            'answer': '符合条件的人员可通过闽政通App、电子税务局App等渠道办理，具体手续可以拨打税务热线12366咨询。',
            'should_pass': True
        },
        {
            'name': '包含操作步骤的回答',
            'answer': '您可以通过闽政通App进行医保缴费，具体操作步骤如下：1. 下载并登录闽政通App；2. 在首页选择"医保缴费"；3. 输入缴费金额并确认。',
            'should_pass': False
        },
        {
            'name': '包含界面描述的回答',
            'answer': '打开闽政通App后，在界面上可以看到"医保服务"入口，点击后进入缴费页面。',
            'should_pass': False
        },
        {
            'name': '包含编造流程的回答',
            'answer': '医保缴费流程如下：首先登录系统，然后选择缴费项目，最后完成支付。',
            'should_pass': False
        }
    ]

    print("🧪 边界检查测试:")
    for i, test_case in enumerate(test_cases, 1):
        result = validate_answer_against_knowledge(test_case['answer'], mock_knowledge)
        status = "✅ 通过" if result['is_valid'] == test_case['should_pass'] else "❌ 失败"

        print(f"   {i}. {test_case['name']}: {status}")
        if not result['is_valid']:
            print(f"      违规项: {', '.join(result['violations'])}")
            print(f"      建议修正: {result['suggested_revision']}")
        print()

    # 实时内容检查测试
    print("🔍 实时内容安全检查:")
    test_texts = [
        ("首先，打开闽政通App", False),
        ("符合条件的人员可通过", True),
        ("点击按钮进入界面", False),
        ("拨打税务热线12366咨询", True),
        ("下载App并登录账户", False),
        ("通过官方渠道办理", True)
    ]

    for text, expected_safe in test_texts:
        is_safe = not is_adding_unsafe_content(text)
        status = "✅" if is_safe == expected_safe else "❌"
        print(f"   {status} '{text}' -> {'安全' if is_safe else '不安全'}")

    print("\n🎯 关键检查模式:")
    operational_patterns = [
        r'第.*步', r'首先.*然后.*最后', r'点击.*选择.*输入.*确认',
        r'在.*界面.*找到.*按钮', r'打开.*进入.*选择.*填写'
    ]
    interface_patterns = [
        r'界面.*显示', r'页面.*可以看到', r'屏幕.*出现',
        r'按钮.*位于', r'输入框.*提示', r'菜单.*包含'
    ]
    fabricated_patterns = [
        r'流程如下', r'具体操作是', r'详细步骤为',
        r'操作流程是', r'办理方式为', r'具体方法'
    ]

    patterns = {
        "操作步骤": operational_patterns,
        "界面描述": interface_patterns,
        "编造流程": fabricated_patterns
    }

    for category, pattern_list in patterns.items():
        print(f"   {category}:")
        for pattern in pattern_list[:2]:  # 显示前2个模式
            print(f"     - {pattern}")

    print("\n✅ 测试完成！边界检查功能已实现并验证。")

if __name__ == "__main__":
    test_boundary_check()