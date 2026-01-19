import requests
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def compute_tokens(input_text: str):
    """计算文本的token数量"""
    url = "http://172.21.33.8/api/llm2/v1/tokenizer"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_TOKEN"
    }

    payload = {
        "inputs": input_text,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()['token_number']
        else:
            print(f"Error computing tokens: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        print(f"Error computing tokens: {e}")
        return 0

def parse_streaming_response(response_text: str):
    """解析流式响应，提取完整内容"""
    content_parts = []
    lines = response_text.strip().split('\n')

    for line in lines:
        if line.startswith('data: '):
            try:
                json_data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                if 'choices' in json_data and len(json_data['choices']) > 0:
                    choice = json_data['choices'][0]
                    if 'delta' in choice and 'content' in choice['delta']:
                        content_parts.append(choice['delta']['content'])
            except json.JSONDecodeError:
                continue

    return ''.join(content_parts)

def get_chat_response_fixed(query: str):
    """修复后的函数，正确处理流式响应"""
    url = "http://172.21.33.8:8888/v1/chat/completions"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": "ee0dfea5-bdbd-4cd3-989e-002453b61304",
        "model": "xmtelecom",
        "messages": [
            {"role": "user", "content": query}
        ],
        "max_tokens": 8192,
        "temperature": 0.2
    }

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        end_time = time.time()

        response_time = end_time - start_time

        if response.status_code == 200:
            # 处理流式响应
            generated_text = parse_streaming_response(response.text)

            # 计算生成文本的token数
            token_count = compute_tokens(generated_text) if generated_text else 0
            # 计算token/s
            tokens_per_second = token_count / response_time if response_time > 0 else 0

            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response_time,
                'token_count': token_count,
                'tokens_per_second': tokens_per_second,
                'generated_text': generated_text,
                'error': None
            }
        else:
            return {
                'success': False,
                'status_code': response.status_code,
                'response_time': response_time,
                'token_count': 0,
                'tokens_per_second': 0,
                'generated_text': None,
                'error': f'HTTP error {response.status_code}'
            }

    except requests.exceptions.RequestException as e:
        end_time = time.time()
        return {
            'success': False,
            'status_code': None,
            'response_time': end_time - start_time,
            'token_count': 0,
            'tokens_per_second': 0,
            'generated_text': None,
            'error': str(e)
        }

def run_simple_concurrent_test():
    """运行简单的并发测试"""
    print("开始修复后的并发测试")
    print("=" * 50)

    query_template = "你好，这是第 {i} 个并发请求"
    concurrent_users = 2
    total_requests = 5

    print(f"并发用户数: {concurrent_users}")
    print(f"总请求数: {total_requests}")
    print("-" * 50)

    results = []
    start_test_time = time.time()

    # 使用线程池执行并发请求
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        for i in range(total_requests):
            query = query_template.format(i=i)
            future = executor.submit(get_chat_response_fixed, query)
            futures.append(future)

        # 收集结果
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                results.append(result)
                print(f"请求 {i+1} 完成: 成功={result['success']}, 响应时间={result['response_time']:.2f}s, Token数={result['token_count']}")
            except Exception as e:
                print(f"请求 {i+1} 异常: {e}")

    end_test_time = time.time()
    total_test_time = end_test_time - start_test_time

    # 分析结果
    successful_requests = [r for r in results if r['success']]
    failed_requests = [r for r in results if not r['success']]

    print("\n" + "=" * 50)
    print("测试结果分析")
    print("=" * 50)
    print(f"成功请求数: {len(successful_requests)}")
    print(f"失败请求数: {len(failed_requests)}")
    print(f"总测试时间: {total_test_time:.2f} 秒")
    print(f"总吞吐量: {total_requests / total_test_time:.2f} 请求/秒")

    if successful_requests:
        response_times = [r['response_time'] for r in successful_requests]
        token_counts = [r['token_count'] for r in successful_requests]
        tokens_per_second = [r['tokens_per_second'] for r in successful_requests]

        print(f"\n响应时间统计:")
        print(f"   平均响应时间: {statistics.mean(response_times):.2f} 秒")
        print(f"   最快响应时间: {min(response_times):.2f} 秒")
        print(f"   最慢响应时间: {max(response_times):.2f} 秒")

        if token_counts:
            print(f"\nToken统计:")
            print(f"   平均Token数: {statistics.mean(token_counts):.2f}")
            print(f"   总Token数: {sum(token_counts)}")

        if tokens_per_second:
            print(f"\n生成速度统计:")
            print(f"   平均生成速度: {statistics.mean(tokens_per_second):.2f} token/秒")
            print(f"   最快生成速度: {max(tokens_per_second):.2f} token/秒")

    # 显示错误信息
    if failed_requests:
        print(f"\n错误详情:")
        for i, req in enumerate(failed_requests):
            print(f"   失败请求 {i+1}: {req['error']}")

if __name__ == "__main__":
    run_simple_concurrent_test()