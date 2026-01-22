#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 批量导入qa对，包含自动匹配目录
import json
import subprocess
import sys
import pandas as pd
import psycopg2

# API端点和认证token
BASE_URL = "http://121.41.44.149:8200/znkfzs/v1/admin/knowledge/entries"
auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2OTA1MTcxMX0.lxE4_VXo9TcvuKYBY73MublMTE8hy7XbeHMVoIxIFIo"

# 数据库配置
DB_CONFIG = {
    'host': '121.41.44.149',
    'port': 6432,
    'database': 'etl_data',
    'user': 'chatbot',
    'password': 'dw2We3GoMaRT4y'
}

# 数据文件配置
EXCEL_FILE = "/home/hello/fund-agent/import_data/公积金聚类问题1951最新1.21.xlsx"
SHEET_NAME = "Sheet1"

# 连接到数据库
conn = psycopg2.connect(
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port'],
    database=DB_CONFIG['database'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password']
)

cur = conn.cursor()

def get_catalog_map():
    """获取所有知识目录并构建映射关系"""
    # 构建目录URL，应该在knowledge级别，不是entries级别
    catalog_url = BASE_URL.rsplit("/entries", 1)[0] + "/catalogs"
    
    # 构建curl命令获取目录
    curl_command = [
        'curl', '-X', 'GET',
        catalog_url,
        '-H', 'accept: application/json',
        '-H', f'Authorization: Bearer {auth_token}',
        '-s'  # 静默模式
    ]
    
    result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8')
    
    catalog_map = {}
    
    if result.returncode == 0:
        try:
            catalogs = json.loads(result.stdout).get("data", [])
            for catalog in catalogs:
                key = (
                    catalog.get("category_level_1", "").strip(),
                    catalog.get("category_level_2", "").strip(),
                    catalog.get("category_level_3", "").strip()
                )
                catalog_map[key] = catalog.get("id")
            print(f"✓ 成功获取 {len(catalog_map)} 个目录")
        except Exception as e:
            print(f"✗ 解析目录失败: {str(e)}")
    else:
        print(f"✗ 获取目录失败: {result.stderr}")
    
    # 如果目录映射为空，使用默认映射
    if not catalog_map:
        print("✗ 使用默认目录映射")
        catalog_map = {
            ("", "", ""): 1  # 默认目录ID
        }
    
    return catalog_map

def check_knowledge_exists(question):
    """检查知识条目是否已存在于数据库中"""
    try:
        cur.execute(
            "SELECT id FROM housing_fund.knowledge WHERE name = %s",
            (question,)
        )
        return cur.fetchone() is not None
    except Exception as e:
        print(f"✗ 检查知识库存在性失败: {str(e)}")
        return False

def create_knowledge_entries():
    """从Excel创建知识条目"""
    # 读取Excel文件
    print(f"正在读取Excel文件: {EXCEL_FILE}")
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        print(f"✓ 成功读取Excel文件，共 {len(df)} 条数据")
    except Exception as e:
        print(f"✗ 读取Excel文件失败: {str(e)}")
        return 0, 0
    
    # 获取目录映射
    catalog_map = get_catalog_map()
    
    success_count = 0
    error_count = 0
    
    # 遍历所有数据
    for index, row in df.iterrows():
        try:
            # 跳过空行
            if pd.isna(row.get("问题")):
                continue
            
            # 获取数据
            question = str(row.get("问题", "")).strip() if not pd.isna(row.get("问题")) else ""
            if not question:
                continue
            
            # 检查知识条目是否已存在
            if check_knowledge_exists(question):
                print(f"\n正在处理条目 {index+1}: {question[:50]}...")
                print(f"✗ 条目已存在，跳过导入")
                continue
                
            level1 = str(row.get("一级分类", "")).strip() if not pd.isna(row.get("一级分类")) else ""
            level2 = str(row.get("二级分类", "")).strip() if not pd.isna(row.get("二级分类")) else ""
            level3 = str(row.get("三级分类", "")).strip() if not pd.isna(row.get("三级分类")) else ""
            answer = str(row.get("回答", "")).strip() if not pd.isna(row.get("回答")) else ""
            reference = str(row.get("依据出处", "")).strip() if not pd.isna(row.get("依据出处")) else ""
            
            print(f"\n正在处理条目 {index+1}: {question[:50]}...")
            
            # 查找目录ID
            catalog_id = None
            
            # 尝试不同级别的匹配
            for key_pattern in [
                (level1, level2, level3),  # 完整匹配
                (level1, level2, ""),  # 一级+二级
                (level1, "", ""),  # 仅一级
                ("", "", "")  # 默认
            ]:
                if key_pattern in catalog_map:
                    catalog_id = catalog_map[key_pattern]
                    print(f"✓ 找到匹配目录: {level1} -> {level2} -> {level3} -> ID={catalog_id}")
                    break
            
            if not catalog_id:
                error_msg = f"未找到匹配目录: {level1} -> {level2} -> {level3}"
                print(f"✗ {error_msg}")
                # 记录详细日志
                with open("import_errors.log", "a", encoding="utf-8") as f:
                    f.write(f"条目 {index+1}: {question[:100]}...\n")
                    f.write(f"  错误类型: 未找到匹配目录\n")
                    f.write(f"  分类信息: {level1} -> {level2} -> {level3}\n")
                    f.write("-" * 50 + "\n")
                error_count += 1
                continue
            
            # 构建创建数据
            create_data = {
                "knowledge_type": "qa",
                "knowledge_catalog_id": catalog_id,
                "name": question,
                "details": {
                    "content": answer,
                    "role": "user",
                    "reference": reference,
                    "status": "pending",
                    "created_by": 0,
                    "version": 1
                },
                "created_by": 0
            }
            
            # 构建curl命令 - BASE_URL already includes /entries
            create_url = BASE_URL
            curl_command = [
                'curl', '-X', 'POST',
                create_url,
                '-H', 'accept: application/json',
                '-H', f'Authorization: Bearer {auth_token}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(create_data, ensure_ascii=False)
            ]
            
            # 执行curl命令
            result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8')
            
            # 打印完整响应，用于调试
            print(f"  API响应: {result.stdout[:200]}...")
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    # 检查API响应中的成功标志
                    if response.get("code") == 200 or response.get("success") or "data" in response:
                        print(f"✓ 成功创建条目 {index+1}: {question[:50]}...")
                        success_count += 1
                    else:
                        error_msg = f"API返回错误: {result.stdout}"
                        print(f"✗ {error_msg}")
                        print(f"✗ 创建条目 {index+1} 失败")
                        # 记录详细日志
                        with open("import_errors.log", "a", encoding="utf-8") as f:
                            f.write(f"条目 {index+1}: {question[:100]}...\n")
                            f.write(f"  错误类型: API返回错误\n")
                            f.write(f"  响应内容: {result.stdout[:200]}...\n")
                            f.write(f"  分类信息: {level1} -> {level2} -> {level3}\n")
                            f.write(f"  目录ID: {catalog_id}\n")
                            f.write("-" * 50 + "\n")
                        error_count += 1
                except json.JSONDecodeError:
                    error_msg = f"无法解析API响应: {result.stdout}"
                    print(f"✗ {error_msg}")
                    print(f"✗ 创建条目 {index+1} 失败")
                    # 记录详细日志
                    with open("import_errors.log", "a", encoding="utf-8") as f:
                        f.write(f"条目 {index+1}: {question[:100]}...\n")
                        f.write(f"  错误类型: 无法解析API响应\n")
                        f.write(f"  响应内容: {result.stdout[:200]}...\n")
                        f.write(f"  分类信息: {level1} -> {level2} -> {level3}\n")
                        f.write(f"  目录ID: {catalog_id}\n")
                        f.write("-" * 50 + "\n")
                    error_count += 1
            else:
                error_msg = f"curl命令执行失败: {result.stderr}"
                print(f"✗ {error_msg}")
                print(f"✗ 创建条目 {index+1} 失败")
                # 记录详细日志
                with open("import_errors.log", "a", encoding="utf-8") as f:
                    f.write(f"条目 {index+1}: {question[:100]}...\n")
                    f.write(f"  错误类型: curl命令执行失败\n")
                    f.write(f"  错误信息: {result.stderr}\n")
                    f.write(f"  分类信息: {level1} -> {level2} -> {level3}\n")
                    f.write(f"  目录ID: {catalog_id}\n")
                    f.write("-" * 50 + "\n")
                error_count += 1
            
            # 避免请求过快
            subprocess.run(['sleep', '0.3'])
            
        except Exception as e:
            print(f"✗ 处理条目 {index+1} 时发生异常: {str(e)}")
            error_count += 1
    
    return success_count, error_count

def main():
    """主函数"""
    print("=" * 60)
    print("公积金知识批量导入工具")
    print("=" * 60)
    print(f"目标地址: {BASE_URL}")
    print(f"数据源: {EXCEL_FILE}")
    print("=" * 60)
    
    print("开始创建知识条目...")
    success, errors = create_knowledge_entries()
    
    print(f"\n更新完成:")
    print(f"成功: {success} 个条目")
    print(f"失败: {errors} 个条目")
    print(f"成功率: {success / (success + errors) * 100:.2f}%" if (success + errors) > 0 else "无有效数据")
    
    if errors > 0:
        print(f"\n警告: 有 {errors} 个条目创建失败")
        sys.exit(1)
    else:
        print("\n所有条目创建成功!")
        sys.exit(0)

if __name__ == "__main__":
    main()
    # 关闭数据库连接
    cur.close()
    conn.close()
