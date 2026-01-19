#!/usr/bin/env python3
"""
测试知识图谱上下文保存为JSON的功能
"""

import os
import json
import glob
from app.core.rag.rag_search import RAGSearch

def test_graph_context_save():
    """测试知识图谱搜索并保存上下文为JSON"""
    print("=" * 60)
    print("测试知识图谱上下文JSON保存功能")
    print("=" * 60)

    rag_search = RAGSearch()
    test_queries = [
        "医保报销比例是多少？",
        "养老保险如何申请？",
        "失业保险金领取条件"
    ]

    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        print("-" * 40)

        try:
            # 调用知识图谱搜索（会触发JSON保存）
            results = rag_search._knowledge_graph_search(query, top_k=3, enable_rerank=True)

            print(f"✅ 搜索完成")
            print(f"   返回结果数量: {len(results)}")

            if results:
                print(f"   第一个结果类型: {results[0].get('source', 'Unknown')}")
                print(f"   第一个问题: {results[0].get('question', 'N/A')[:50]}...")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

def analyze_saved_json():
    """分析已保存的JSON文件"""
    print("\n" + "=" * 60)
    print("分析已保存的JSON文件")
    print("=" * 60)

    temp_dir = "temp_graph_context_analysis"
    if not os.path.exists(temp_dir):
        print("📁 没有找到临时文件目录")
        return

    # 获取所有JSON文件
    json_files = glob.glob(os.path.join(temp_dir, "graph_context_*.json"))
    print(f"📄 找到 {len(json_files)} 个JSON文件")

    if json_files:
        # 分析最新的文件
        latest_file = max(json_files, key=os.path.getmtime)
        print(f"\n📋 分析最新文件: {os.path.basename(latest_file)}")

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"   查询: {data.get('query', 'N/A')}")
            print(f"   时间戳: {data.get('timestamp', 'N/A')}")

            # 分析提取的数据
            extracted_data = data.get('extracted_data', {})
            sources_count = extracted_data.get('sources_count', 0)
            print(f"   Sources数量: {sources_count}")

            if extracted_data.get('sources_structure'):
                structure = extracted_data['sources_structure']
                print(f"   Sources结构:")
                print(f"     键: {structure.get('keys', [])}")
                print(f"     类型: {structure.get('sample_types', {})}")

            # 分析原始上下文属性
            raw_context = data.get('raw_context', {})
            attributes = raw_context.get('attributes', {})
            print(f"   Graph Context属性数量: {len(attributes)}")

            # 显示一些关键属性
            key_attrs = ['context_chunks', 'context_records']
            for attr in key_attrs:
                if attr in attributes:
                    attr_data = attributes[attr]
                    if isinstance(attr_data, dict) and 'type' in attr_data:
                        print(f"   {attr}: {attr_data['type']}")
                    else:
                        print(f"   {attr}: {type(attr_data).__name__}")

        except Exception as e:
            print(f"❌ 分析文件失败: {e}")

def show_json_structure_sample():
    """显示JSON结构示例"""
    print("\n" + "=" * 60)
    print("JSON文件结构说明")
    print("=" * 60)

    structure_info = """
每个JSON文件包含以下结构：

{
  "query": "原始查询文本",
  "timestamp": "20241217_143022_123",
  "raw_context": {
    "context_chunks": "...",
    "context_records": "...",
    "attributes": {
      "attr1": {...},
      "attr2": {...},
      // graph_context的所有非私有属性
    }
  },
  "extracted_data": {
    "sources_count": 10,
    "sources_sample": [...],
    "sources_structure": {
      "keys": ["id", "text", "score", ...],
      "sample_types": {"id": "str", "text": "str", ...}
    }
  }
}

用途：
1. 了解graph_context的完整结构
2. 分析sources数据的字段类型
3. 为后续结构化数据转换提供参考
4. 调试和优化搜索结果
"""
    print(structure_info)

def cleanup_test_files():
    """清理测试生成的文件"""
    print("\n" + "=" * 60)
    print("清理测试文件")
    print("=" * 60)

    temp_dir = "temp_graph_context_analysis"
    if os.path.exists(temp_dir):
        import shutil
        file_count = len([f for f in os.listdir(temp_dir) if f.endswith('.json')])
        print(f"🗑️  清理 {file_count} 个JSON文件...")
        shutil.rmtree(temp_dir)
        print("✅ 清理完成")
    else:
        print("📁 没有找到临时文件目录")

if __name__ == "__main__":
    test_graph_context_save()
    analyze_saved_json()
    show_json_structure_sample()

    # 询问是否清理文件
    print("\n" + "=" * 60)
    response = input("是否要清理测试生成的JSON文件？(y/n): ").lower().strip()
    if response in ['y', 'yes', '是']:
        cleanup_test_files()
    else:
        print("💡 测试文件已保留在 temp_graph_context_analysis/ 目录中")
        print("   你可以用这些文件来分析graph_context的结构和数据格式")