"""
测试文本格式化工具
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.core.text_formatter import TextFormatter

def test_reference_formatting():
    """测试reference格式化"""

    print("测试Reference文本格式化:")
    print("="*50)

    test_cases = [
        "这是答案内容[来源: 测试来源]",
        "答案内容\n[来源: 测试来源]更多内容",
        "段落1\n\n段落2[来源: 来源1]继续内容",
        "内容1[来源: 来源1]\n\n内容2",
        "只有来源信息[来源: 单独来源]"
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"原文: {repr(test)}")
        formatted = TextFormatter.format_reference_text(test)
        print(f"格式化: {repr(formatted)}")
        print("-" * 40)

def test_newline_normalization():
    """测试换行符标准化"""

    print("\n\n测试换行符标准化:")
    print("="*50)

    test_cases = [
        "单个换行\n测试\n文本",
        "双换行\n\n保持\n\n不变",
        "混合\n换行\n\n测试\n文本",
        "开头\n中间\n结尾",
        "多换行\n\n\n\n清理\n\n测试"
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"原文: {repr(test)}")
        formatted = TextFormatter.normalize_newlines_for_markdown(test)
        print(f"格式化: {repr(formatted)}")
        print("-" * 40)

if __name__ == "__main__":
    test_reference_formatting()
    test_newline_normalization()