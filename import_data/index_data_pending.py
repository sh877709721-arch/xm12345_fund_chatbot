#!/usr/bin/env python3
import json
import subprocess
import sys

def update_knowledge_entries():
    # 读取JSON文件
    with open('data/response_1765545240718.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # API端点和认证token
    base_url = "http://127.0.0.1:8000/v1/admin/knowledge/entries"
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2NTU0NzM4Nn0.lb_2O0S0wk8YtuXL4Q0UNbg0UZMKdQQDpSyColD7JN8"


    success_count = 0
    error_count = 0

    # 遍历所有知识条目
    for item in data['data']['items']:
        entry_id = item['id']

        # 构建更新数据
        update_data = {
            "knowledge_type": item['knowledge_type'],
            "knowledge_catalog_id": item['knowledge_catalog_id'],
            "name": item['name'],
            "details": {
                "content": item['details']['content'],
                "role": item['details']['role'],
                "reference": item['details']['reference'],
                "status": "active",  # 将pending改为active
                "created_by": 0,  # 使用默认值
                "version": item['details']['version']
            }
        }

        # 构建curl命令
        curl_command = [
            'curl', '-X', 'PUT',
            f'{base_url}/{entry_id}',
            '-H', f'accept: application/json',
            '-H', f'Authorization: Bearer {auth_token}',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(update_data, ensure_ascii=False)
        ]

        print(f"正在更新条目 ID: {entry_id}")

        try:
            # 执行curl命令
            result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                print(f"✓ 成功更新条目 {entry_id}: {item['name'][:50]}...")
                success_count += 1
            else:
                print(f"✗ 更新条目 {entry_id} 失败:")
                print(f"  错误信息: {result.stderr}")
                error_count += 1

        except Exception as e:
            print(f"✗ 更新条目 {entry_id} 时发生异常: {str(e)}")
            error_count += 1

    print(f"\n更新完成:")
    print(f"成功: {success_count} 个条目")
    print(f"失败: {error_count} 个条目")

    return success_count, error_count



def create_knowledge_entries_txts():
    import os

    # 检查 txts 目录是否存在
    txts_dir = 'data/txts'
    if not os.path.exists(txts_dir):
        print(f"错误: 目录 '{txts_dir}' 不存在")
        return 0, 0

    # 获取 txts 目录下的所有 .txt 文件
    txt_files = [f for f in os.listdir(txts_dir) if f.endswith('.txt')]
    if not txt_files:
        print(f"错误: 目录 '{txts_dir}' 中没有找到 .txt 文件")
        return 0, 0

    # API端点和认证token
    base_url = "http://127.0.0.1:8000/v1/admin/knowledge/entries"
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2NTU0NzM4Nn0.lb_2O0S0wk8YtuXL4Q0UNbg0UZMKdQQDpSyColD7JN8"

    success_count = 0
    error_count = 0

    # 按字母顺序排序文件，确保每次执行的顺序一致
    txt_files.sort()

    # 遍历所有txt文件
    for txt_file in txt_files:
        try:
            # 读取txt文件内容
            file_path = os.path.join(txts_dir, txt_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用文件名（去掉扩展名）作为name
            name = os.path.splitext(txt_file)[0]

            # 创建操作不需要匹配现有的entry_id，直接为每个文件创建新条目
            # 这意味着每个txt文件都会创建一个全新的知识条目

            # 构建创建数据
            create_data = {
                "knowledge_type": "document",
                "knowledge_catalog_id": 53,
                "name": name,
                "details": {
                    "content": content,
                    "role": "system",
                    "reference": "",
                    "status": "pending",
                    "created_by": 0,
                    "version": 1
                },
                "created_by": 0
            }

            # 构建curl命令
            curl_command = [
                'curl', '-X', 'POST',
                f'{base_url}',
                '-H', f'accept: application/json',
                '-H', f'Authorization: Bearer {auth_token}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(create_data, ensure_ascii=False)
            ]

            print(f"正在创建条目: {name}")

            # 执行curl命令
            result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                print(f"✓ 成功创建条目: {name[:50]}...")
                success_count += 1
            else:
                print(f"✗ 创建条目 {name} 失败:")
                print(f"  错误信息: {result.stderr}")
                error_count += 1

        except Exception as e:
            print(f"✗ 处理文件 {txt_file} 时发生异常: {str(e)}")
            error_count += 1

    print(f"\n更新完成:")
    print(f"成功: {success_count} 个条目")
    print(f"失败: {error_count} 个条目")

    return success_count, error_count

if __name__ == "__main__":
    print("开始创建知识条目...")
    success, errors = update_knowledge_entries()

    if errors > 0:
        print(f"\n警告: 有 {errors} 个条目创建失败")
        sys.exit(1)
    else:
        print("\n所有条目创建成功!")
        sys.exit(0)