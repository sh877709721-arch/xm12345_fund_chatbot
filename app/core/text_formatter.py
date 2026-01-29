"""
文本格式化工具
处理Markdown格式的文本换行和格式优化
"""

import re
from typing import List, Tuple


class TextFormatter:
    """文本格式化工具类"""

    @staticmethod
    def normalize_newlines_for_markdown(text: str) -> str:
        """
        将文本中的单个换行符转换为双换行符，以便于Markdown格式显示

        规则：
        1. 连续的单个换行符 \n 替换为双换行符 \n\n
        2. 已经是双换行符的 \n\n 保持不变
        3. 三个及以上换行符简化为双换行符
        4. 跳过文本首尾的换行符处理

        Args:
            text: 原始文本

        Returns:
            格式化后的文本
        """
        if not text or not isinstance(text, str):
            return text

        # 1. 清理首尾空白
        text = text.strip()

        # 2. 处理中间的换行符
        # 使用正则表达式匹配：
        # - \n{1} 匹配单个换行符
        # - ?<!\n{2} 负向后瞻，确保前面不是双换行符
        # - ?!\n{2} 负向前瞻，确保后面不是双换行符

        # 先将连续3个及以上换行符替换为双换行符
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 然后将单个换行符替换为双换行符，但不影响已有的双换行符
        # 使用更精确的正则表达式
        text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)
        
        return text

    @staticmethod
    def format_reference_text(text: str) -> str:
        """
        专门处理包含参考来源的文本格式化

        Args:
            text: 包含reference的原始文本

        Returns:
            格式化后的文本，确保reference部分有合适的换行
        """
        if not text:
            return text

        # 先标准化换行符
        text = TextFormatter.normalize_newlines_for_markdown(text)

        # 确保reference部分前后都有合适的换行
        # if '[来源:' in text:
        #     # 在来源信息前添加双换行
        #     text = re.sub(r'([^\n])\s*(\[来源:)', r'\1\n\n\2', text)
        #     # 在来源信息后添加双换行
        #     text = re.sub(r'(\[来源:[^\]]+\])([^\n])', r'\1\n\n\2', text)

        return text

    @staticmethod
    def optimize_markdown_paragraphs(text: str) -> str:
        """
        优化Markdown段落格式

        Args:
            text: 原始文本

        Returns:
            优化后的Markdown文本
        """
        if not text:
            return text

        # 标准化换行符
        text = TextFormatter.normalize_newlines_for_markdown(text)

        # 确保段落之间有适当的间距
        # 检查列表项、标题等特殊格式
        lines = text.split('\n\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 保持列表项的格式
            if line.startswith(('-', '*', '+', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                formatted_lines.append(line)
            # 保持标题格式
            elif line.startswith('#'):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        return '\n\n'.join(formatted_lines)

    @staticmethod
    def clean_excessive_newlines(text: str) -> str:
        """
        清理过度的换行符

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return text

        # 将连续2个以上换行符替换为双换行符
        return re.sub(r'\n{2,}', '\n\n', text.strip())

    @staticmethod
    def smart_newline_replacement(text: str, preserve_code_blocks: bool = True) -> str:
        """
        智能换行符替换，保护代码块等特殊格式

        Args:
            text: 原始文本
            preserve_code_blocks: 是否保护代码块内的换行符

        Returns:
            处理后的文本
        """
        if not text:
            return text

        if preserve_code_blocks:
            # 提取并保护代码块
            code_blocks = []
            def replace_code_block(match):
                code_blocks.append(match.group(0))
                return f"__CODE_BLOCK_{len(code_blocks)-1}__"

            # 匹配三个反引号的代码块
            text = re.sub(r'```[\s\S]*?```', replace_code_block, text)

        # 执行标准换行符处理
        text = TextFormatter.normalize_newlines_for_markdown(text)

        if preserve_code_blocks:
            # 恢复代码块
            for i, code_block in enumerate(code_blocks):
                text = text.replace(f"__CODE_BLOCK_{i}__", code_block)

        return text




# 便捷函数
def format_text_for_markdown(text: str) -> str:
    """
    便捷函数：为Markdown格式化文本

    Args:
        text: 原始文本

    Returns:
        格式化后的文本
    """
    return TextFormatter.optimize_markdown_paragraphs(text)


def format_reference_text(text:str)->str:
    return TextFormatter.format_reference_text(text)

def normalize_newlines(text: str) -> str:
    """
    便捷函数：标准化换行符

    Args:
        text: 原始文本

    Returns:
        标准化后的文本
    """
    return TextFormatter.normalize_newlines_for_markdown(text)


# 测试用例
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "单个换行\n测试\n文本",
        "双换行\n\n保持\n\n不变",
        "混合\n换行\n\n测试\n文本",
        "开头\n中间\n结尾",
        "1. 列表项1\n2. 列表项2",
        "```代码块\n内容```",
        "标题\n\n段落内容",
        "多换行\n\n\n\n清理\n\n测试"
    ]

    print("文本格式化测试结果：")
    print("="*60)

    for i, test in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"原文: {repr(test)}")
        formatted = TextFormatter.normalize_newlines_for_markdown(test)
        print(f"格式化: {repr(formatted)}")
        print("-" * 40)

    # 测试reference格式化
    print("\nReference格式化测试:")
    print("="*40)
    reference_test = "这是答案内容[来源: 测试来源]"
    print(f"原文: {reference_test}")
    print(f"格式化: {TextFormatter.format_reference_text(reference_test)}")