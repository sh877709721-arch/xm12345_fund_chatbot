#!/usr/bin/env python3
"""
测试修改后的rerank函数，展示保留id和rerank信息的结果结构
"""

import pandas as pd
import json

def mock_rerank_results():
    """模拟rerank API返回的结果"""
    return [
        {"index": 1, "text": "我在厦门参保，年度要回省外，能不能在省外用厦门的职工医保。", "relevance_score": 0.95},
        {"index": 0, "text": "前提交退费申请，逾期不予办理。注：由税务部门受理退费申请。", "relevance_score": 0.78},
        {"index": 2, "text": "政通APP-医保服务-异地就医备案登记-有效备案记录", "relevance_score": 0.65}
    ]

def demonstrate_rerank_structure():
    """演示修改后的rerank结构"""

    # 模拟原始DataFrame数据
    original_data = [
        {"id": 25, "text": "前提交退费申请，逾期不予办理。注：由税务部门受理退费申请。"},
        {"id": 133, "text": "我在厦门参保，年度要回省外，能不能在省外用厦门的职工医保。在省外就医，办理异地就医备案后，在备案地全国联网定点医药机构可以直接使用厦门医保。"},
        {"id": 43, "text": "政通APP-医保服务-异地就医备案登记-有效备案记录（备案取消入口）；2.厦门医疗保障小程序"}
    ]

    df = pd.DataFrame(original_data)

    print("=== 原始DataFrame数据 ===")
    print(df)
    print()

    # 模拟rerank处理过程
    query = "厦门医保异地就医"

    # 提取文本用于rerank（模拟）
    texts = [str(row['text']) for idx, row in df.iterrows()]
    original_items = [
        {"id": row['id'], "text": str(row['text']), "original_row": row}
        for idx, row in df.iterrows()
    ]

    print("=== 提取用于rerank的文本 ===")
    for i, text in enumerate(texts):
        print(f"[{i}] ID:{original_items[i]['id']} - {text[:50]}...")
    print()

    # 模拟rerank结果
    rerank_results = mock_rerank_results()

    print("=== Rerank API返回结果 ===")
    print(json.dumps(rerank_results, ensure_ascii=False, indent=2))
    print()

    # 模拟重排序过程
    reordered_items = []
    for item in rerank_results:
        idx = item.get("index", 0)
        if 0 <= idx < len(original_items):
            reordered_items.append(original_items[idx])

    print("=== 重排序后的原始数据 ===")
    for i, item in enumerate(reordered_items):
        print(f"[{i}] ID:{item['id']} - Rerank Score:{rerank_results[i]['relevance_score']}")
        print(f"    Text: {item['text'][:100]}...")
    print()

    # 构建最终返回结果（模拟修改后的函数返回）
    result_texts = []
    result_metadata = []

    for i, item in enumerate(reordered_items):
        text_content = item.get('text', str(item))
        result_texts.append(text_content)
        result_metadata.append({
            'id': item.get('id'),
            'rerank_score': rerank_results[i].get('relevance_score', 0) if i < len(rerank_results) else 0,
            'original_index': rerank_results[i].get('index', -1) if i < len(rerank_results) else -1
        })

    final_result = {
        'url': 'graph_records',
        'text': result_texts,
        'type': 'reranked_records',
        'metadata': result_metadata,
        'rerank_info': {
            'total_items': len(original_items),
            'returned_items': len(reordered_items),
            'query': query
        }
    }

    print("=== 修改后函数返回的最终结构 ===")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))
    print()

    print("=== 结构优势分析 ===")
    print("1. ✅ 保留原始ID：可以追溯到原始数据源")
    print("2. ✅ Rerank评分：了解每个结果的相关性分数")
    print("3. ✅ 原始索引：知道重排序前的位置")
    print("4. ✅ 结构化数据：便于前端展示和处理")
    print("5. ✅ 元数据丰富：包含查询和统计信息")
    print()

    print("=== 使用示例 ===")
    print("如何访问rerank后的结果：")
    print("```python")
    print("result = rerank_knowledge_records(data, query, top_n=3)")
    print("")
    print("# 获取rerank后的文本")
    print("texts = result['text']")
    print("")
    print("# 获取对应的元数据（包含ID和评分）")
    print("metadata = result['metadata']")
    print("for i, meta in enumerate(metadata):")
    print("    print(f\"ID: {meta['id']}, Score: {meta['rerank_score']}\")")
    print("    print(f\"Text: {texts[i]}\")")
    print("```")

if __name__ == "__main__":
    demonstrate_rerank_structure()