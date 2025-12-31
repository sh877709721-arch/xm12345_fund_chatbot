#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI助手边界检查功能的简单脚本
"""

import json
from app.core.agents.assistant import (
    validate_answer_against_knowledge,
    is_adding_unsafe_content,
    contains_operational_details,
    contains_interface_descriptions,
    format_knowledge_with_source_isolation,
    extract_key_constraints_from_knowledge
)

def test_boundary_check():
    """测试边界检查功能"""
    print("=== 测试AI助手边界检查功能 ===\n")

    # 模拟知识库数据
    mock_knowledge = [
        {
            'source': '[文件](医保缴费指南.pdf)',
            'content': '符合条件的人员可通过闽政通App、电子税务局App等渠道办理，具体手续可以拨打税务热线12366咨询。'
        }
    ]

    # 测试用例1：安全回答
    safe_answer = "符合条件的人员可通过闽政通App、电子税务局App等渠道办理，具体手续可以拨打税务热线12366咨询。"
    result1 = validate_answer_against_knowledge(safe_answer, mock_knowledge)
    print("✅ 测试安全回答:")
    print(f"   回答: {safe_answer}")
    print(f"   验证结果: {'通过' if result1['is_valid'] else '失败'}")
    if not result1['is_valid']:
        print(f"   违规项: {result1['violations']}")
    print()

    # 测试用例2：包含操作步骤的回答
    unsafe_answer = "您可以通过闽政通App进行医保缴费，具体操作步骤如下：1. 下载并登录闽政通App；2. 在首页选择'医保缴费'；3. 输入缴费金额并确认。"
    result2 = validate_answer_against_knowledge(unsafe_answer, mock_knowledge)
    print("❌ 测试包含操作步骤的回答:")
    print(f"   回答: {unsafe_answer[:50]}...")
    print(f"   验证结果: {'通过' if result2['is_valid'] else '失败'}")
    if not result2['is_valid']:
        print(f"   违规项: {result2['violations']}")
        print(f"   建议修正: {result2['suggested_revision']}")
    print()

    # 测试用例3：实时内容检查
    test_texts = [
        "首先，打开闽政通App",  # 应该被检测到
        "符合条件的人员可通过",  # 应该安全
        "点击按钮进入界面",     # 应该被检测到
        "拨打税务热线12366咨询"  # 应该安全
    ]

    print("🔍 实时内容安全检查:")
    for i, text in enumerate(test_texts, 1):
        is_safe = not is_adding_unsafe_content(text)
        status = "✅ 安全" if is_safe else "❌ 不安全"
        print(f"   {i}. '{text}' -> {status}")
    print()

    # 测试知识库约束提取
    print("📋 知识库约束提取:")
    constraints = extract_key_constraints_from_knowledge(mock_knowledge)
    print(f"   允许的渠道: {list(constraints['allowed_channels'])}")
    print(f"   联系方式: {list(constraints['contact_methods'])}")
    print(f"   标准回答数量: {len(constraints['standard_responses'])}")
    if constraints['standard_responses']:
        print(f"   标准回答: {constraints['standard_responses'][0]}")
    print()

if __name__ == "__main__":
    test_boundary_check()