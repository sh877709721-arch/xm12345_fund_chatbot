import pandas as pd
import os
import glob
import re

# 配置路径
INPUT_DIR = "./"  # Excel 文件所在的目录（通常就是当前根目录）
OUTPUT_RAG_DIR = "./app/core/graph/chatbot_zh/input" # GraphRAG 的输入目录

print(f"Debug: INPUT_DIR = {INPUT_DIR}")
print(f"Debug: OUTPUT_RAG_DIR = {OUTPUT_RAG_DIR}")

# 确保输出目录存在
print("Debug: Creating output directory...")
os.makedirs(OUTPUT_RAG_DIR, exist_ok=True)
print("Debug: Output directory created successfully")

def clean_text(text):
    """清洗文本：去除换行、空值转字符串"""
    if pd.isna(text):
        return ""
    # 转为字符串并去除首尾空格
    text = str(text).strip()
    # 将换行符替换为为空格，避免破坏 RAG 的分块
    text = text.replace("\n", " ").replace("\r", " ")
    return text

def process_qa_files():
    """处理问答日志和聚类问题 (.xlsx)"""
    print("Debug: Entering process_qa_files()")
    # 匹配所有的 xlsx 文件
    xlsx_files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    print(f"Debug: Found xlsx files: {xlsx_files}")
    
    combined_text = []
    
    for file_path in xlsx_files:
        filename = os.path.basename(file_path)
        
        # 跳过分类文件，稍后在 process_taxonomy_files 中处理
        if "分类" in filename:
            print(f"Debug: Skipping taxonomy file: {filename}")
            continue
            
        print(f"正在读取问答文件: {filename}...")
        try:
            # 读取 Excel (默认读取第一个 Sheet)
            print(f"Debug: Reading Excel file: {file_path}")
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"Debug: Successfully read Excel file, shape: {df.shape}")
            print(f"Debug: Columns: {df.columns.tolist()}")
            
            # 自动识别列名（兼容您的不同文件格式）
            cols = df.columns.tolist()
            
            # 1. 寻找"问题"列
            question_col = next((c for c in cols if "问题" in str(c)), None)
            print(f"Debug: Found question_col: {question_col}")
            # 2. 寻找"回答"列
            answer_col = next((c for c in cols if "回答" in str(c)), None)
            print(f"Debug: Found answer_col: {answer_col}")
            # 3. (可选) 寻找"评价"列，用于过滤差评
            vote_col = next((c for c in cols if "投票" in str(c) or "反馈" in str(c)), None)
            print(f"Debug: Found vote_col: {vote_col}")

            if not question_col or not answer_col:
                print(f"  -> 跳过: 在 {filename} 中未找到'问题'或'回答'列")
                continue

            count = 0
            for _, row in df.iterrows():
                # 过滤逻辑：如果有投票列，且标记为"差评"，则跳过（防止学习错误知识）
                if vote_col and "差评" in str(row[vote_col]):
                    continue

                q = clean_text(row[question_col])
                a = clean_text(row[answer_col])
                
                # 有效性检查：内容不能为空且长度合理
                if len(q) > 2 and len(a) > 2:
                    # 构建知识条目格式
                    # 使用明确的陈述句格式，帮助 GraphRAG 提取实体关系
                    entry = f"用户通常咨询的问题是："{q}"。针对该问题的标准政策解答或办理方式为：{a}"
                    combined_text.append(entry)
                    count += 1
            
            print(f"  -> 成功提取 {count} 条问答")
                    
        except Exception as e:
            print(f"  -> 处理文件 {filename} 出错: {e}")

    # 保存为 txt
    if combined_text:
        out_path = os.path.join(OUTPUT_RAG_DIR, "processed_qa_knowledge.txt")
        print(f"Debug: Saving QA knowledge to: {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(combined_text))
        print(f"✅ [问答库] 生成完毕: {out_path} (共 {len(combined_text)} 条)")
    else:
        print("⚠️ 未提取到任何问答数据，请检查 Excel 文件列名。")

def process_taxonomy_files():
    """处理三级分类目录 (.xlsx)"""
    print("Debug: Entering process_taxonomy_files()")
    # 仅匹配文件名包含"分类"的 xlsx 文件
    files = [f for f in glob.glob(os.path.join(INPUT_DIR, "*分类*.xlsx"))]
    print(f"Debug: Found taxonomy files: {files}")
    
    taxonomy_text = []
    
    for file_path in files:
        print(f"正在读取分类文件: {os.path.basename(file_path)}...")
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"Debug: Successfully read taxonomy file, shape: {df.shape}")
            print(f"Debug: Columns: {df.columns.tolist()}")
            cols = df.columns.tolist()
            
            # 寻找 一级、二级、三级 列
            l1_col = next((c for c in cols if "一级" in str(c)), None)
            print(f"Debug: Found l1_col: {l1_col}")
            l2_col = next((c for c in cols if "二级" in str(c)), None)
            print(f"Debug: Found l2_col: {l2_col}")
            l3_col = next((c for c in cols if "三级" in str(c)), None)
            print(f"Debug: Found l3_col: {l3_col}")
            
            if l1_col and l2_col and l3_col:
                for _, row in df.iterrows():
                    v1 = clean_text(row[l1_col])
                    v2 = clean_text(row[l2_col])
                    v3 = clean_text(row[l3_col])
                    
                    if v1 and v2 and v3:
                        # 构建层级关系描述
                        # 这种句式有助于 GraphRAG 建立 (v3) -> 属于 -> (v2) 的关系
                        desc = f""{v3}"是公积金业务中的具体事项，它属于"{v2}"分类，归纳在"{v1}"的大类下。"
                        taxonomy_text.append(desc)
        except Exception as e:
            print(f"  -> 出错: {e}")

    # 保存
    if taxonomy_text:
        out_path = os.path.join(OUTPUT_RAG_DIR, "processed_taxonomy.txt")
        print(f"Debug: Saving taxonomy to: {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(taxonomy_text))
        print(f"✅ [分类树] 生成完毕: {out_path} (共 {len(taxonomy_text)} 条)")

if __name__ == "__main__":
    print("🚀 开始转换 Excel 数据为 GraphRAG 格式...")
    try:
        print("Debug: Calling process_qa_files()")
        process_qa_files()
        print("Debug: Calling process_taxonomy_files()")
        process_taxonomy_files()
        print("\n🎉 所有转换完成！")
        print(f"请检查输出目录: {OUTPUT_RAG_DIR}")
        print("下一步：运行 python -m graphrag.index --root ./app/core/graph/chatbot_zh")
    except Exception as e:
        print(f"Debug: Main exception: {e}")
        import traceback
        traceback.print_exc()