#!/usr/bin/env python3
"""
独立测试DataFrame到JSON的转换函数
"""

import pandas as pd
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_dataframe_to_searchable_json(data, data_type='auto'):
    """
    将pandas DataFrame转换为易于搜索的JSON格式

    Args:
        data: pandas DataFrame、list或dict数据
        data_type: 数据类型 ('text_records', 'entity_records', 'auto')

    Returns:
        dict: 标准化的JSON格式数据
    """
    if data is None or (hasattr(data, '__len__') and len(data) == 0):
        return None

    try:
        # 如果已经是字典格式，直接返回
        if isinstance(data, dict) and 'url' in data and 'text' in data:
            return data

        # 如果是JSON字符串，先解析
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return {'url': 'unknown', 'text': [str(data)]}

        # 处理DataFrame格式
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return None

            # 自动检测数据类型
            if data_type == 'auto':
                columns = data.columns.tolist()
                if 'id' in columns and 'text' in columns and len(columns) <= 3:
                    data_type = 'text_records'
                elif 'entity' in columns and 'description' in columns:
                    data_type = 'entity_records'
                else:
                    data_type = 'generic'

            if data_type == 'text_records':
                # 处理文本记录：[{id: 1, text: "..."}]
                texts = []
                for idx, row in data.iterrows():
                    if pd.notna(row.get('text')):
                        texts.append(str(row['text']))
                return {
                    'url': 'knowledge_base',
                    'type': 'text_records',
                    'count': len(texts),
                    'text': texts
                }

            elif data_type == 'entity_records':
                # 处理实体记录：[{id: 1, entity: "名称", description: "...", ...}]
                entities = []
                for idx, row in data.iterrows():
                    entity_data = {
                        'id': int(row.get('id', idx)),
                        'entity': str(row.get('entity', '')),
                        'description': str(row.get('description', ''))
                    }

                    # 添加可选字段
                    if 'number of relationships' in row and pd.notna(row['number of relationships']):
                        entity_data['relationships_count'] = int(row['number of relationships'])

                    if 'in_context' in row and pd.notna(row['in_context']):
                        entity_data['in_context'] = bool(row['in_context'])

                    entities.append(entity_data)

                return {
                    'url': 'knowledge_graph',
                    'type': 'entity_records',
                    'count': len(entities),
                    'entities': entities
                }

            else:
                # 通用处理
                texts = []
                for idx, row in data.iterrows():
                    text = " ".join([str(val) for val in row.values if pd.notna(val)])
                    texts.append(text)
                return {
                    'url': 'generic_data',
                    'type': 'generic',
                    'count': len(texts),
                    'text': texts
                }

        # 处理列表格式
        elif isinstance(data, list):
            if data is None or (hasattr(data, '__len__') and len(data) == 0):
                return None

            # 检查是否是字典列表
            if all(isinstance(item, dict) for item in data):
                # 自动检测类型
                if data_type == 'auto':
                    first_item = data[0]
                    if 'text' in first_item and 'id' in first_item:
                        data_type = 'text_records'
                    elif 'entity' in first_item and 'description' in first_item:
                        data_type = 'entity_records'
                    else:
                        data_type = 'generic'

                if data_type == 'text_records':
                    texts = [str(item.get('text', '')) for item in data if item.get('text')]
                    return {
                        'url': 'knowledge_base',
                        'type': 'text_records',
                        'count': len(texts),
                        'text': texts
                    }

                elif data_type == 'entity_records':
                    entities = []
                    for item in data:
                        entity_data = {
                            'id': item.get('id'),
                            'entity': str(item.get('entity', '')),
                            'description': str(item.get('description', ''))
                        }

                        if 'number of relationships' in item:
                            entity_data['relationships_count'] = item['number of relationships']

                        if 'in_context' in item:
                            entity_data['in_context'] = bool(item['in_context'])

                        entities.append(entity_data)

                    return {
                        'url': 'knowledge_graph',
                        'type': 'entity_records',
                        'count': len(entities),
                        'entities': entities
                    }


            # 纯文本列表
            return {
                'url': 'knowledge_base',
                'type': 'text_list',
                'count': len(data),
                'text': [str(item) for item in data]
            }

        # 处理其他格式
        else:
            return {
                'url': 'unknown',
                'type': 'raw',
                'text': [str(data)]
            }

    except Exception as e:
        logger.warning(f"转换数据格式失败: {e}")
        return {
            'url': 'error',
            'type': 'error',
            'text': [f"转换错误: {str(e)}"]
        }

def test_text_records_conversion():
    """测试文本记录转换"""
    print("=== 测试文本记录转换 ===")

    # 模拟文本记录数据（从用户数据中提取）
    text_data = [
        {"id": 25, "text": "前提交退费申请，逾期不予办理。注：由税务部门受理退费申请。五、城乡居民医疗保险历年缴费标准"},
        {"id": 133, "text": "我在厦门参保，年度要回省外，能不能在省外用厦门的职工医保。在省外就医，办理异地就医备案后，在备案地全国联网定点医药机构可以直接使用厦门医保。"}
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

    # 模拟实体记录数据（从用户数据中提取）
    entity_data = [
        {
            "id": 4,
            "entity": "厦门",
            "description": "厦门是中国福建省下辖的一个计划单列市，设有独立的医疗保障体系，是文本中多次提及的医保政策实施地区。",
            "number of relationships": 132,
            "in_context": True
        },
        {
            "id": 389,
            "entity": "医疗费用报销",
            "description": "医疗费用报销是指医疗保险参保人员为补偿医疗支出而遵循的规范化流程。该流程涵盖各类医疗费用的报销申请。",
            "number of relationships": 13,
            "in_context": True
        }
    ]

    # 转换为DataFrame
    df = pd.DataFrame(entity_data)
    print("原始DataFrame:")
    print(df[['id', 'entity', 'number of relationships', 'in_context']])
    print()

    # 转换为JSON
    result = convert_dataframe_to_searchable_json(df, data_type='entity_records')
    print("转换后的JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()

def demonstrate_search_benefits():
    """展示搜索优势"""
    print("=== 搜索优势演示 ===")

    # 创建示例数据
    sample_data = {
        "url": "knowledge_graph",
        "type": "entity_records",
        "count": 3,
        "entities": [
            {
                "id": 4,
                "entity": "厦门",
                "description": "厦门是中国福建省下辖的一个计划单列市，设有独立的医疗保障体系",
                "relationships_count": 132,
                "in_context": True
            },
            {
                "id": 389,
                "entity": "医疗费用报销",
                "description": "医疗费用报销是指医疗保险参保人员为补偿医疗支出而遵循的规范化流程",
                "relationships_count": 13,
                "in_context": True
            },
            {
                "id": 20,
                "entity": "厦门市",
                "description": "厦门市是中国福建省下辖的地级市，作为一个具体的医疗保障统筹区",
                "relationships_count": 205,
                "in_context": True
            }
        ]
    }

    print("转换后的JSON数据结构:")
    print(json.dumps(sample_data, ensure_ascii=False, indent=2))
    print()

    print("搜索优势:")
    print("1. ✅ 结构化访问：可以按 entity、description 等字段精确搜索")
    print("2. ✅ 关系计数：可以根据 relationships_count 排序")
    print("3. ✅ 上下文标识：可以根据 in_context 过滤相关实体")
    print("4. ✅ 类型安全：明确的数据类型，减少解析错误")
    print("5. ✅ 统计信息：知道实体总数，便于分页")
    print("6. ✅ API友好：标准JSON格式，易于前后端交互")
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

if __name__ == "__main__":
    test_text_records_conversion()
    test_entity_records_conversion()
    test_auto_detection()
    demonstrate_search_benefits()

    print("🎉 转换测试完成！")
    print("这个转换函数可以很好地处理pandas DataFrame数据，")
    print("将其转换为结构化的JSON格式，便于搜索和API使用。")