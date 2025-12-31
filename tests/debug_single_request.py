import requests
import json
import time

def test_single_request():
    """测试单个请求，详细输出调试信息"""
    url = "http://172.21.33.8:8888/v1/chat/completions"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": "ee0dfea5-bdbd-4cd3-989e-002453b61304",
        "model": "xmtelecom",
        "messages": [
            {"role": "user", "content": "你好，这是一个测试请求"}
        ],
        "max_tokens": 8192,
        "temperature": 0.2
    }

    print("调试信息:")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)

    start_time = time.time()

    try:
        print("发送请求...")
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        end_time = time.time()

        response_time = end_time - start_time
        print(f"响应时间: {response_time:.2f} 秒")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text[:500]}...")  # 只显示前500个字符

        if response.status_code == 200:
            try:
                response_data = response.json()
                print("JSON解析成功")
                print(f"响应结构: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

                # 提取生成的文本内容
                generated_text = ""
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    choice = response_data['choices'][0]
                    if 'message' in choice:
                        generated_text = choice['message']['content']
                    elif 'delta' in choice:
                        generated_text = choice['delta']['content']

                print(f"生成的文本: {generated_text}")

                return True
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                return False
        else:
            print(f"HTTP错误: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"连接错误: {e}")
        print("可能的原因:")
        print("   - 服务器地址或端口不正确")
        print("   - 网络连接问题")
        print("   - 服务器未启动")
        return False
    except requests.exceptions.Timeout as e:
        print(f"请求超时: {e}")
        print("可能的原因:")
        print("   - 服务器响应太慢")
        print("   - 网络延迟")
        return False
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False

if __name__ == "__main__":
    print("开始单个请求调试测试")
    print("=" * 50)

    success = test_single_request()

    if success:
        print("\n单个请求测试成功！")
    else:
        print("\n单个请求测试失败！")
        print("\n建议检查:")
        print("1. 服务器地址和端口是否正确")
        print("2. 网络连接是否正常")
        print("3. 服务器是否正在运行")
        print("4. 请求格式是否正确")