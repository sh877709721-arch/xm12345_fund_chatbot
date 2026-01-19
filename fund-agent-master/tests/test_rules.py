
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.rule.rules import medical_retirement_rule,medical_region_rule
from app.core.rule.rule_set import RuleSet,Rule


rule = RuleSet()

rule.add_rule(medical_retirement_rule)
rule.add_rule(medical_region_rule)

matches = rule.find_matching_rules('刚在闽政通办理孩子厦门医保停保，什么时候可以在泉州参保。')

print(matches)

