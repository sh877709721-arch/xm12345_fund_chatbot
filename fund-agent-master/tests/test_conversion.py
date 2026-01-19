#!/usr/bin/env python3
"""
测试DataFrame到JSON的转换函数
"""

import pandas as pd
import json
from app.core.rag.knowledge_search import convert_dataframe_to_searchable_json

def test_text_records_conversion():
    """测试文本记录转换"""
    print("=== 测试文本记录转换 ===")

    # 模拟文本记录数据
    text_data = [
        {"id": 25, "text": "前提交退费申请，逾期不予办理。注：由税务部门受理退费申请。"},
        {"id": 133, "text": "我在厦门参保，年度要回省外，能不能在省外用厦门的职工医保。"},
        {"id": 43, "text": "政通APP-医保服务-异地就医备案登记-有效备案记录。"}
    ]

    # 转换为DataFrame
    df = pd.DataFrame(text_data)
    print("原始DataFrame:")
    print(df)
    print()

    # 转换为JSON
    result = convert_dataframe_to_searchable_json(df, data_type='text_records')
    print("转换后的JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()

def test_entity_records_conversion():
    """测试实体记录转换"""
    print("=== 测试实体记录转换 ===")

    # 模拟实体记录数据（简化版）
    entity_data = [
        {
            "id": 4,
            "entity": "厦门",
            "description": "厦门是中国福建省下辖的一个计划单列市，设有独立的医疗保障体系。",
            "number of relationships": 132,
            "in_context": True
        },
        {
            "id": 20,
            "entity": "厦门市",
            "description": "厦门市是中国福建省下辖的地级市，作为一个具体的医疗保障统筹区。",
            "number of relationships": 205,
            "in_context": True
        },
        {
            "id": 389,
            "entity": "医疗费用报销",
            "description": "医疗费用报销是指医疗保险参保人员为补偿医疗支出而遵循的规范化流程。",
            "number of relationships": 13,
            "in_context": True
        }
    ]

    # 转换为DataFrame
    df = pd.DataFrame(entity_data)
    print("原始DataFrame:")
    print(df[['id', 'entity', 'number of relationships', 'in_context']].head())
    print()

    # 转换为JSON
    result = convert_dataframe_to_searchable_json(df, data_type='entity_records')
    print("转换后的JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()

def test_auto_detection():
    """测试自动类型检测"""
    print("=== 测试自动类型检测 ===")

    # 文本记录
    text_df = pd.DataFrame([
        {"id": 1, "text": "测试文本1"},
        {"id": 2, "text": "测试文本2"}
    ])

    result1 = convert_dataframe_to_searchable_json(text_df, data_type='auto')
    print("自动检测结果(文本记录):", result1['type'])

    # 实体记录
    entity_df = pd.DataFrame([
        {"id": 1, "entity": "实体1", "description": "描述1"},
        {"id": 2, "entity": "实体2", "description": "描述2"}
    ])

    result2 = convert_dataframe_to_searchable_json(entity_df, data_type='auto')
    print("自动检测结果(实体记录):", result2['type'])
    print()

def test_string_input():
    """测试字符串输入"""
    print("=== 测试字符串输入 ===")

    # JSON字符串
    json_str = json.dumps([
        {"id": 1, "text": "字符串测试"},
        {"id": 2, "text": "另一个测试"}
    ])

    result = convert_dataframe_to_searchable_json(json_str, data_type='auto')
    print("字符串输入转换结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()

if __name__ == "__main__":
    test_text_records_conversion()
    test_entity_records_conversion()
    test_auto_detection()
    test_string_input()

    print("=== 转换优势总结 ===")
    print("1. 结构化数据：清晰的层次结构，易于解析")
    print("2. 类型标识：明确标识数据类型（text_records, entity_records等）")
    print("3. 统计信息：包含记录数量统计")
    print("4. 字段标准化：统一字段名称和格式")
    print("5. 搜索友好：适合全文搜索和关键词匹配")
    print("6. API兼容：标准的JSON格式，适合API传输")