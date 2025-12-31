#!/usr/bin/env python3
import json
import subprocess
import sys

def update_knowledge_entries():
    # 读取JSON文件
    with open('data/response_1765256327393.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # API端点和认证token
    base_url = "http://127.0.0.1:8000/v1/admin/knowledge/entries"
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2NTI1OTg4OH0.JDTHtufq3yUHhn3kcLu58eUzi-83ySnUf1UYzyl4tFQ"

    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }

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

if __name__ == "__main__":
    print("开始更新知识条目状态...")
    success, errors = update_knowledge_entries()

    if errors > 0:
        print(f"\n警告: 有 {errors} 个条目更新失败")
        sys.exit(1)
    else:
        print("\n所有条目更新成功!")
        sys.exit(0)