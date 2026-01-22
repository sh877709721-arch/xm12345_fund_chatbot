#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 批量启用知识条目
import json
import subprocess
import sys

# API端点和认证token (从import_knowledge_fixed.py复制)
BASE_URL = "http://121.41.44.149:8200/znkfzs/v1/admin/knowledge/entries"
auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2OTA1MTcxMX0.lxE4_VXo9TcvuKYBY73MublMTE8hy7XbeHMVoIxIFIo"


def get_all_knowledge_entries():
    """获取所有知识条目"""
    print("正在获取所有知识条目...")
    
    # 构建搜索URL
    search_url = BASE_URL + "/search"
    
    # 构建搜索请求数据，获取所有条目
    search_data = {
        "page": 1,
        "size": 1000,  # 设置一个足够大的值来获取所有条目
        "status": "pending"  # 只获取待启用的条目
    }
    
    # 构建curl命令
    curl_command = [
        'curl', '-X', 'POST',
        search_url,
        '-H', 'accept: application/json',
        '-H', f'Authorization: Bearer {auth_token}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(search_data, ensure_ascii=False),
        '-s'  # 静默模式
    ]
    
    try:
        # 执行curl命令
        result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("code") == 200:
                data = response.get("data", {})
                items = data.get("items", [])
                total = data.get("total", 0)
                print(f"✓ 成功获取 {len(items)} 个知识条目 (共 {total} 个)")
                return items
            else:
                print(f"✗ 获取知识条目失败: {response.get('message', '未知错误')}")
                return []
        else:
            print(f"✗ 获取知识条目失败: {result.stderr}")
            return []
    except Exception as e:
        print(f"✗ 获取知识条目时发生异常: {str(e)}")
        return []


def activate_knowledge_entries():
    """启用所有知识条目"""
    # 获取所有知识条目
    entries = get_all_knowledge_entries()
    
    if not entries:
        print("没有找到需要启用的知识条目")
        return 0, 0
    
    success_count = 0
    error_count = 0
    
    # 遍历所有知识条目
    for item in entries:
        knowledge_id = item['id']
        
        # 打印第一条数据的结构，用于调试
        if success_count == 0 and error_count == 0:
            print(f"\n调试信息 - 第一条数据结构:")
            print(f"  ID: {knowledge_id}")
            print(f"  Name: {item['name'][:50]}")
            print(f"  Details类型: {type(item['details'])}")
            print(f"  Details内容: {item['details']}")
        
        # 根据details的类型构建更新数据
        details = item['details']
        if isinstance(details, list):
            # 如果details是列表，取第一个元素
            detail_item = details[0] if details else {}
        else:
            # 如果details是字典，直接使用
            detail_item = details
        
        # 构建更新数据
        update_data = {
            "knowledge_type": item['knowledge_type'],
            "knowledge_catalog_id": item['knowledge_catalog_id'],
            "name": item['name'],
            "details": {
                "content": detail_item.get('content', ''),
                "role": detail_item.get('role', 'user'),
                "reference": detail_item.get('reference', ''),
                "status": "active",  # 将pending改为active
                "created_by": detail_item.get('created_by') or 0,
                "version": detail_item.get('version') or 1
            }
        }
        
        # 构建curl命令
        curl_command = [
            'curl', '-X', 'PUT',
            f'{BASE_URL}/{knowledge_id}',
            '-H', 'accept: application/json',
            '-H', f'Authorization: Bearer {auth_token}',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(update_data, ensure_ascii=False)
        ]
        
        print(f"\n正在启用知识条目 ID: {knowledge_id} - {item['name'][:50]}...")
        
        try:
            # 执行curl命令
            result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    if response.get("code") == 200:
                        print(f"✓ 成功启用知识条目 {knowledge_id}")
                        success_count += 1
                    else:
                        print(f"✗ 启用知识条目 {knowledge_id} 失败: {response.get('message', '未知错误')}")
                        error_count += 1
                except json.JSONDecodeError:
                    print(f"✗ 无法解析API响应: {result.stdout}")
                    error_count += 1
            else:
                print(f"✗ 启用知识条目 {knowledge_id} 失败: {result.stderr}")
                error_count += 1
            
            # 避免请求过快
            subprocess.run(['sleep', '0.3'])
            
        except Exception as e:
            print(f"✗ 启用知识条目 {knowledge_id} 时发生异常: {str(e)}")
            error_count += 1
    
    return success_count, error_count


def main():
    """主函数"""
    print("=" * 60)
    print("知识条目批量启用工具")
    print("=" * 60)
    print(f"目标地址: {BASE_URL}")
    print("=" * 60)
    
    print("开始启用知识条目...")
    success, errors = activate_knowledge_entries()
    
    print(f"\n启用完成:")
    print(f"成功: {success} 个条目")
    print(f"失败: {errors} 个条目")
    print(f"成功率: {success / (success + errors) * 100:.2f}%" if (success + errors) > 0 else "无有效数据")
    
    if errors > 0:
        print(f"\n警告: 有 {errors} 个条目启用失败")
        sys.exit(1)
    else:
        print("\n所有条目启用成功!")
        sys.exit(0)


if __name__ == "__main__":
    main()