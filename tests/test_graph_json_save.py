#!/usr/bin/env python3
"""
测试知识图谱上下文保存为JSON的功能
"""

import os
import json
from app.core.rag.knowledge_search import KnowledgeSearchService

def test_graph_json_save():
    """测试知识图谱搜索并保存JSON"""
    print("=" * 60)
    print("测试知识图谱JSON保存功能")
    print("=" * 60)

    test_queries = [
        "医保报销比例是多少？",
        "养老保险如何申请？"
    ]

    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        print("-" * 40)

        try:
            # 调用知识图谱搜索
            knowledge_data, keywords = KnowledgeSearchService.search_and_integrate_knowledge(
                query=query,
                doc_top_n=3,
                graph_top_n=3,
                enable_graph_search=True
            )

            print(f"✅ 搜索完成")
            print(f"   知识数据条数: {len(knowledge_data)}")
            print(f"   关键词数量: {len(keywords)}")

            # 检查临时JSON文件是否生成
            temp_dir = "temp_graph_context"
            if os.path.exists(temp_dir):
                files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
                print(f"   生成的JSON文件: {len(files)}个")

                # 显示最新的摘要文件
                summary_files = [f for f in files if f.startswith('summary_')]
                if summary_files:
                    latest_summary = max(summary_files)
                    summary_path = os.path.join(temp_dir, latest_summary)

                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary = json.load(f)

                    print(f"   最新摘要文件: {latest_summary}")
                    print(f"   查询: {summary.get('query', 'N/A')}")
                    print(f"   时间戳: {summary.get('timestamp', 'N/A')}")
                    print(f"   统计信息: {summary.get('stats', {})}")

                    # 检查相关文件
                    files_info = summary.get('files', {})
                    if files_info.get('context_chunks'):
                        print(f"   Context chunks 文件: ✅")
                    if files_info.get('context_records'):
                        print(f"   Context records 文件: ✅")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

def cleanup_test_files():
    """清理测试生成的文件"""
    print("\n" + "=" * 60)
    print("清理测试文件")
    print("=" * 60)

    temp_dir = "temp_graph_context"
    if os.path.exists(temp_dir):
        import shutil
        file_count = len([f for f in os.listdir(temp_dir) if f.endswith('.json')])
        print(f"🗑️  清理 {file_count} 个JSON文件...")
        shutil.rmtree(temp_dir)
        print("✅ 清理完成")
    else:
        print("📁 没有找到临时文件目录")

if __name__ == "__main__":
    test_graph_json_save()

    # 询问是否清理文件
    print("\n" + "=" * 60)
    response = input("是否要清理测试生成的JSON文件？(y/n): ").lower().strip()
    if response in ['y', 'yes', '是']:
        cleanup_test_files()
    else:
        print("💡 测试文件已保留在 temp_graph_context/ 目录中")