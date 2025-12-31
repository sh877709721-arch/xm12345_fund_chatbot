import logging
import time
import sys
import os
import requests
import json

import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 已有数据库连接 URL（请确保已定义）
# 示例: DB_URL = "postgresql://user:password@host:port/dbname"
# 请在外部配置或环境变量中提供
from app.config.settings import settings
from app.config.llm_client import embedding_client

DB_URL = settings.ETL_POSTGRES_URL



# 配置
BATCH_SIZE = 32
MODEL_NAME = "bge-m3"
EMBEDDING_DIM = 1024

def compute_tokens(input_text: str):
    import requests
    import json

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

def get_chat_response(query: str):
    """修改后的函数，正确处理流式响应，返回结构化结果用于并发测试"""
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
                'response_data': response.text,
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
                'response_data': response.text,
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
            'response_data': None,
            'generated_text': None,
            'error': str(e)
        }

def run_concurrent_test(query_template: str, concurrent_users: int, total_requests: int, max_workers: int):
    """
    运行并发测试
    
    Args:
        query_template: 查询模板，可以用{}占位符
        concurrent_users: 并发用户数
        total_requests: 总请求数
        max_workers: 最大工作线程数，如果不指定则使用concurrent_users
    """
    print(f"🚀 开始并发测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 目标URL: http://172.21.33.8:8888/v1/chat/completions")
    print(f"👥 并发用户数: {concurrent_users}")
    print(f"📊 总请求数: {total_requests}")
    print(f"🧵 线程池大小: {max_workers if max_workers else concurrent_users}")
    print("-" * 60)
    
    if max_workers is None:
        max_workers = concurrent_users
    
    results = []
    start_test_time = time.time()
    
    # 使用线程池执行并发请求
    with ThreadPoolExecutor(max_workers=max_workers) as executor:  # [[4]]
        futures = []
        for i in range(total_requests):
            # 生成不同的查询内容以避免缓存
            query = query_template.format(i=i, timestamp=int(time.time()))
            future = executor.submit(get_chat_response, query)
            futures.append(future)
        
        # 收集结果
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                results.append(result)
                
                # 每完成10%显示进度
                if (i + 1) % max(1, total_requests // 10) == 0:
                    progress = ((i + 1) / total_requests) * 100
                    print(f"📈 进度: {progress:.1f}% ({i+1}/{total_requests})")
                    
            except Exception as e:
                results.append({
                    'success': False,
                    'status_code': None,
                    'response_time': 0,
                    'token_count': 0,
                    'tokens_per_second': 0,
                    'response_data': None,
                    'error': f'Future exception: {str(e)}'
                })
    
    end_test_time = time.time()
    total_test_time = end_test_time - start_test_time
    
    # 分析结果
    successful_requests = [r for r in results if r['success']]
    failed_requests = [r for r in results if not r['success']]
    
    response_times = [r['response_time'] for r in results if r['response_time'] > 0]
    token_counts = [r['token_count'] for r in successful_requests if r['token_count'] > 0]
    tokens_per_second = [r['tokens_per_second'] for r in successful_requests if r['tokens_per_second'] > 0]
    
    print("\n" + "=" * 60)
    print("📊 测试结果分析")
    print("=" * 60)
    print(f"✅ 成功请求数: {len(successful_requests)}")
    print(f"❌ 失败请求数: {len(failed_requests)}")
    print(f"🎯 总吞吐量: {total_requests / total_test_time:.2f} 请求/秒")
    print(f"⏱️  总测试时间: {total_test_time:.2f} 秒")
    
    if response_times:
        print(f"\n⏱️  响应时间统计:")
        print(f"   📏 平均响应时间: {statistics.mean(response_times):.2f} 秒")
        print(f"   📊 中位数响应时间: {statistics.median(response_times):.2f} 秒")
        print(f"   🚀 最快响应时间: {min(response_times):.2f} 秒")
        print(f"   🐢 最慢响应时间: {max(response_times):.2f} 秒")
        
        if len(response_times) >= 2:
            print(f"   📈 标准差: {statistics.stdev(response_times):.2f} 秒")
    
    if token_counts:
        print(f"\n🔤 Token统计:")
        print(f"   📏 平均Token数: {statistics.mean(token_counts):.2f}")
        print(f"   📊 中位数Token数: {statistics.median(token_counts):.2f}")
        print(f"   🚀 最少Token数: {min(token_counts)}")
        print(f"   🐢 最多Token数: {max(token_counts)}")
        
    if tokens_per_second:
        print(f"\n⚡ 生成速度统计:")
        print(f"   📏 平均生成速度: {statistics.mean(tokens_per_second):.2f} token/秒")
        print(f"   📊 中位数生成速度: {statistics.median(tokens_per_second):.2f} token/秒")
        print(f"   🚀 最快生成速度: {max(tokens_per_second):.2f} token/秒")
        print(f"   🐢 最慢生成速度: {min(tokens_per_second):.2f} token/秒")
        
        if len(tokens_per_second) >= 2:
            print(f"   📈 标准差: {statistics.stdev(tokens_per_second):.2f} token/秒")
    
    # 显示错误类型统计
    if failed_requests:
        print(f"\n🚨 错误分析:")
        error_counts = {}
        for req in failed_requests:
            error_type = req['error'] or 'Unknown error'
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            print(f"   ❌ {error_type}: {count} 次")
    
    # 保存详细结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"concurrent_test_results_{timestamp}.json"
    
    detailed_results = {
        'test_metadata': {
            'start_time': start_test_time,
            'end_time': end_test_time,
            'total_time': total_test_time,
            'concurrent_users': concurrent_users,
            'total_requests': total_requests,
            'max_workers': max_workers
        },
        'summary': {
            'success_count': len(successful_requests),
            'failure_count': len(failed_requests),
            'throughput': total_requests / total_test_time,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'avg_token_count': statistics.mean(token_counts) if token_counts else 0,
            'total_token_count': sum(token_counts),
            'avg_tokens_per_second': statistics.mean(tokens_per_second) if tokens_per_second else 0,
            'max_tokens_per_second': max(tokens_per_second) if tokens_per_second else 0,
            'min_tokens_per_second': min(tokens_per_second) if tokens_per_second else 0
        },
        'results': results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细结果已保存到: {filename}")
    print("=" * 60)

def main():
    """主函数，配置和运行测试"""
    
    # 配置测试参数
    TEST_CONFIGS = [
        {
            'name': '轻度负载测试',
            'query_template': '你好，这是第 {i} 个并发请求，时间戳: {timestamp}',
            'concurrent_users': 5,
            'total_requests': 50,
            'max_workers': 10
        },
        {
            'name': '中度负载测试',
            'query_template': '请解释人工智能的基本概念，请求编号: {i}',
            'concurrent_users': 20,
            'total_requests': 200,
            'max_workers': 40
        },
        {
            'name': '重度负载测试',
            'query_template': '详细描述医保政策的各个方面，包括报销流程、比例和限制条件，请求编号: {i}',
            'concurrent_users': 50,
            'total_requests': 500,
            'max_workers': 100
        }
    ]
    
    print("🚀 AI模型性能测试工具")
    print("=" * 50)
    print("请选择要运行的测试:")
    
    for i, config in enumerate(TEST_CONFIGS):
        print(f"{i+1}. {config['name']}")
    
    print(f"{len(TEST_CONFIGS)+1}. 运行所有测试")
    print(f"{len(TEST_CONFIGS)+2}. 自定义测试")
    
    try:
        choice = int(input("\n请输入选项编号: "))
        
        if choice == len(TEST_CONFIGS) + 1:
            # 运行所有测试
            for config in TEST_CONFIGS:
                print(f"\n\n🔥 开始运行: {config['name']}")
                print("-" * 40)
                
                run_concurrent_test(
                    query_template=config['query_template'],
                    concurrent_users=config['concurrent_users'],
                    total_requests=config['total_requests'],
                    max_workers=config['max_workers']
                )
                
                # 每次测试之间等待一段时间，让服务器恢复
                if config != TEST_CONFIGS[-1]:
                    print(f"\n⏳ 等待 10 秒后进行下一轮测试...")
                    time.sleep(10)
                    
        elif choice == len(TEST_CONFIGS) + 2:
            # 自定义测试
            print("\n🛠️  自定义测试配置")
            name = input("测试名称: ") or "自定义测试"
            query_template = input("查询模板 (可使用 {i} 和 {timestamp} 占位符): ") or "这是一个自定义查询 {i}"
            concurrent_users = int(input("并发用户数 (默认10): ") or "10")
            total_requests = int(input("总请求数 (默认100): ") or "100")
            max_workers = int(input("最大工作线程数 (默认20): ") or "20")
            
            config = {
                'name': name,
                'query_template': query_template,
                'concurrent_users': concurrent_users,
                'total_requests': total_requests,
                'max_workers': max_workers
            }
            
            print(f"\n\n🔥 开始运行: {config['name']}")
            print("-" * 40)
            run_concurrent_test(
                query_template=config['query_template'],
                concurrent_users=config['concurrent_users'],
                total_requests=config['total_requests'],
                max_workers=config['max_workers']
            )
            
        elif 1 <= choice <= len(TEST_CONFIGS):
            # 运行选定的测试
            config = TEST_CONFIGS[choice-1]
            print(f"\n\n🔥 开始运行: {config['name']}")
            print("-" * 40)
            run_concurrent_test(
                query_template=config['query_template'],
                concurrent_users=config['concurrent_users'],
                total_requests=config['total_requests'],
                max_workers=config['max_workers']
            )
        else:
            print("❌ 无效选项")
            return
            
    except ValueError:
        print("❌ 请输入有效的数字")
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    # 确保安装了必要的依赖
    print("🔧 检查依赖...")
    try:
        import requests
        import statistics
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("💡 请安装: pip install requests")
        exit(1)
    
    main()
