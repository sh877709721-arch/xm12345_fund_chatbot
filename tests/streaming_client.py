import requests
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def compute_tokens(input_text: str):
    """计算文本的token数量"""
    url = "http://172.16.2.167/api/llm2/v1/tokenizer"
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

def parse_sse_response(response_text: str):
    """解析SSE格式响应，提取完整内容"""
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
                    elif 'message' in choice and 'content' in choice['message']:
                        content_parts.append(choice['message']['content'])
            except json.JSONDecodeError:
                continue

    return ''.join(content_parts)

def get_chat_response_fixed(query: str):
    """修复后的函数，正确处理流式响应"""
    url = "http://121.41.44.149:8888/v1/chat/completions"
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
            # 解析流式响应
            generated_text = parse_sse_response(response.text)

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

def test_single_fixed_request():
    """测试修复后的单个请求"""
    print("测试修复后的单个请求处理")
    print("=" * 50)

    result = get_chat_response_fixed("你好，请简单介绍一下自己")

    print(f"请求成功: {result['success']}")
    print(f"响应时间: {result['response_time']:.2f} 秒")
    print(f"Token数量: {result['token_count']}")
    print(f"生成速度: {result['tokens_per_second']:.2f} token/秒")

    if result['generated_text']:
        print(f"生成内容: {result['generated_text'][:200]}...")

    if result['error']:
        print(f"错误信息: {result['error']}")

    return result['success']

if __name__ == "__main__":
    test_single_fixed_request()