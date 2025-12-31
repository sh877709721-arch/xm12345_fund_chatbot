import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 从修复后的测试文件导入函数
from tests.test_chat_para import get_chat_response

def test_single_fixed_request():
    """测试修复后的单个请求函数"""
    print("测试修复后的 get_chat_response 函数")
    print("=" * 50)

    query = "请简单介绍一下你自己"
    result = get_chat_response(query)

    print(f"请求成功: {result['success']}")
    print(f"状态码: {result['status_code']}")
    print(f"响应时间: {result['response_time']:.2f} 秒")
    print(f"Token数量: {result['token_count']}")
    print(f"生成速度: {result['tokens_per_second']:.2f} token/秒")

    if result['generated_text']:
        print(f"生成内容前100字符: {result['generated_text'][:100]}...")

    if result['error']:
        print(f"错误信息: {result['error']}")

    return result['success']

if __name__ == "__main__":
    success = test_single_fixed_request()
    if success:
        print("\n修复成功！现在可以正常处理流式响应了。")
    else:
        print("\n修复失败，需要进一步调试。")