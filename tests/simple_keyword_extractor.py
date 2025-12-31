def extract_subdict(statement, dictionary):
    """
    根据语句从字典中提取包含关键字的子字典

    Args:
        statement (str): 输入语句
        dictionary (dict): 原始字典 {key: [value_keywords]}

    Returns:
        dict: 匹配的子字典
    """
    result = {}

    # 转换为小写进行匹配，提高匹配率
    statement_lower = statement.lower()

    for key, keywords in dictionary.items():
        # 检查语句中是否包含当前value列表中的任意关键字
        for keyword in keywords:
            # 支持双向匹配：语句包含关键字 或 关键字包含语句中的词汇
            keyword_lower = keyword.lower()
            if (keyword_lower in statement_lower or
                any(word in statement_lower for word in keyword_lower.split())):
                result[key] = keywords
                break  # 找到一个匹配就跳到下一个key

    return result


# 使用您选择的部分代码示例
if __name__ == "__main__":
    # 您选择的部分字典
    test_dict = {
        "职工基本医疗保险": ["职工医保", "单位医保", "职工基本医疗"],
        "城乡居民医疗保险": ["居民医保", "城乡医保", "新农合"],
        "待遇生效时间": ["生效时间", "开始时间", "等待期", "何时享受"]
    }

    # 测试语句
    statements = [
        "职工医保的等待期是多久？",
        "城乡居民医保什么时候开始生效？",
        "这个月开始享受待遇",
        "我什么时候可以享受医保待遇？",
        "医保生效时间是什么时候？"
    ]

    for statement in statements:
        matched = extract_subdict(statement, test_dict)
        print(f"语句: {statement}")
        print(f"匹配结果: {matched}\n")