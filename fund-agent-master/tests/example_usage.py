#!/usr/bin/env python3
"""
动态提示词匹配系统使用示例
演示Rule和RuleSet的基本用法
"""

from app.core.rule.rule_set import Rule, RuleSet

def demo_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===\n")

    # 创建规则集合
    rule_set = RuleSet()

    # 创建一些规则
    python_rule = Rule(
        name="Python编程规范",
        content="请遵循Python PEP 8编码规范，使用有意义的变量名，编写清晰的注释。",
        querys=[
            "如何写Python代码",
            "Python编码标准",
            "写出Python函数",
            "Python最佳实践"
        ],
        tags=["python", "编码规范"],
        is_active=True,
        threshold=0.6
    )

    test_rule = Rule(
        name="测试用例编写",
        content="为每个功能编写单元测试，使用AAA模式（Arrange, Act, Assert），确保测试覆盖率。",
        querys=[
            "写测试用例",
            "如何测试",
            "单元测试",
            "测试代码"
        ],
        tags=["测试", "质量保证"],
        is_active=True,
        threshold=0.7
    )

    code_review_rule = Rule(
        name="代码审查要点",
        content="代码审查时关注：可读性、性能、安全性、可维护性。",
        querys=[
            "代码审查",
            "代码质量检查",
            "review代码",
            "代码评审"
        ],
        tags=["代码审查", "质量"],
        is_active=False,  # 这个规则默认不激活
        threshold=0.5
    )

    # 添加规则到集合
    rule_set.add_rule(python_rule)
    rule_set.add_rule(test_rule)
    rule_set.add_rule(code_review_rule)

    print(f"规则集合信息: {rule_set}")
    print(f"激活的规则数量: {rule_set.get_active_rule_count()}")
    print(f"所有标签: {rule_set.get_all_tags()}\n")

def demo_matching():
    """演示匹配功能"""
    print("=== 匹配功能演示 ===\n")

    rule_set = RuleSet()

    # 添加一些规则
    react_rule = Rule(
        name="React组件开发",
        content="使用函数式组件和Hooks，遵循React最佳实践，确保组件职责单一。",
        querys=[
            "React组件",
            "前端开发",
            "React最佳实践",
            "组件设计"
        ],
        tags=["react", "前端"],
        is_active=True
    )

    database_rule = Rule(
        name="数据库设计",
        content="设计数据库时遵循第三范式，合理使用索引，确保数据一致性和性能。",
        querys=[
            "数据库设计",
            "SQL优化",
            "数据库性能",
            "数据建模"
        ],
        tags=["数据库", "后端"],
        is_active=True
    )

    rule_set.add_rule(react_rule)
    rule_set.add_rule(database_rule)

    # 测试查询匹配
    test_queries = [
        "如何创建React组件",
        "数据库表设计原则",
        "前端界面开发",
        "SQL查询优化"
    ]

    for query in test_queries:
        print(f"查询: '{query}'")
        matches = rule_set.find_matching_rules(query, max_results=2)

        if matches:
            for rule, similarity in matches:
                print(f"  ✅ 匹配规则: {rule.name} (相似度: {similarity:.3f})")
                print(f"     内容预览: {rule.content[:50]}...")
        else:
            print("  ❌ 没有找到匹配的规则")
        print()

def demo_tag_filtering():
    """演示标签过滤功能"""
    print("=== 标签过滤演示 ===\n")

    rule_set = RuleSet()

    # 添加带不同标签的规则
    rules = [
        Rule("Python基础", "Python编程基础知识", ["python", "基础"], is_active=True),
        Rule("Java进阶", "Java高级编程技巧", ["java", "进阶"], is_active=True),
        Rule("前端框架", "React/Vue/Angular框架对比", ["前端", "框架"], is_active=True),
        Rule("后端API", "RESTful API设计规范", ["后端", "API"], is_active=True),
        Rule("算法优化", "常见算法优化技巧", ["算法", "优化"], is_active=False),  # 未激活
    ]

    for rule in rules:
        rule_set.add_rule(rule)

    # 测试标签过滤
    tag_filters = [["python"], ["前端"], ["后端", "API"], ["算法"], []]

    for tags in tag_filters:
        filtered_rules = rule_set.get_active_rules_by_tags(tags)
        print(f"标签过滤 {tags}: 找到 {len(filtered_rules)} 个规则")
        for rule in filtered_rules:
            print(f"  - {rule.name} (激活: {rule.is_active})")
        print()

def demo_rule_management():
    """演示规则管理功能"""
    print("=== 规则管理演示 ===\n")

    rule_set = RuleSet()

    # 添加规则
    rule = Rule(
        name="示例规则",
        content="这是一个示例规则",
        tags=["示例"],
        is_active=False
    )
    rule_set.add_rule(rule)

    print(f"初始状态: {rule_set}")

    # 激活规则
    rule_set.activate_rule("示例规则")
    print(f"激活后: {rule_set}")

    # 停用规则
    rule_set.deactivate_rule("示例规则")
    print(f"停用后: {rule_set}")

    # 演示序列化
    dict_list = rule_set.to_dict_list()
    print(f"序列化结果: {dict_list}")

if __name__ == "__main__":
    demo_basic_usage()
    print("\n" + "="*50 + "\n")
    demo_matching()
    print("\n" + "="*50 + "\n")
    demo_tag_filtering()
    print("\n" + "="*50 + "\n")
    demo_rule_management()