import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__)))

from app.core.rule.rules import medical_retirement_rule, medical_region_rule
from app.core.rule.rule_set import RuleSet, Rule

print("=== 调试测试 ===")

rule_set = RuleSet()
rule_set.add_rule(medical_retirement_rule)
rule_set.add_rule(medical_region_rule)

print(f"规则总数: {rule_set.get_rule_count()}")
print(f"激活规则数: {rule_set.get_active_rule_count()}")

# 检查规则详情
for rule in rule_set.rules:
    print(f"规则: {rule.name}")
    print(f"  激活状态: {rule.is_active}")
    print(f"  查询数量: {len(rule.querys)}")
    print(f"  向量数量: {len(rule.vec_querys)}")
    print(f"  向量已构建: {rule._vector_built}")
    print()

# 测试查询
query = '我在泉州交医保，能不能在厦门办理医保退休'
print(f"查询: {query}")
matches = rule_set.find_matching_rules(query)

print(f"匹配结果: {matches}")