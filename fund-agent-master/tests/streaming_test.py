import requests
import json
import time

def parse_streaming_response(response_text):
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
                # 忽略解析失败的行
                continue

    return ''.join(content_parts)

def test_streaming_request():
    """测试流式响应处理"""
    url = "http://121.41.44.149:8888/v1/chat/completions"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": "ee0dfea5-bdbd-4cd3-989e-002453b61304",
        "model": "xmtelecom",
        "messages": [
            {"role": "user", "content": "请介绍一下你自己"}
        ],
        "max_tokens": 8192,
        "temperature": 0.2
    }

    print("发送流式请求...")
    start_time = time.time()

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        end_time = time.time()

        print(f"响应时间: {end_time - start_time:.2f} 秒")
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            # 解析流式响应（不是JSON格式）
            full_content = parse_streaming_response(response.text)
            print(f"完整响应内容:\n{full_content}")

            # 计算token数量（简单估算：中文字符数）
            char_count = len(full_content)
            print(f"字符数: {char_count}")
            print(f"生成速度: {char_count / (end_time - start_time):.2f} 字符/秒")

            return True
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"请求异常: {e}")
        return False

if __name__ == "__main__":
    print("测试流式响应处理")
    print("=" * 50)
    test_streaming_request()