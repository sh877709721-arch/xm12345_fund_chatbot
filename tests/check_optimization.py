#!/usr/bin/env python3
"""
数据库连接池优化效果检查脚本
"""

import requests
import time
import json
import concurrent.futures
from typing import Dict, List

class OptimizationChecker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def check_health(self) -> Dict:
        """检查基础健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return {
                "status": "success",
                "data": response.json(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "status_code": None
            }

    def check_database_health(self) -> Dict:
        """检查数据库连接池健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health/database", timeout=5)
            return {
                "status": "success",
                "data": response.json(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "status_code": None
            }

    def check_pool_status(self) -> Dict:
        """检查详细的连接池状态"""
        try:
            response = requests.get(f"{self.base_url}/monitor/pool", timeout=5)
            return {
                "status": "success",
                "data": response.json(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "status_code": None
            }

    def test_rate_limiting(self, concurrent_requests: int = 25) -> Dict:
        """测试限流效果"""
        def make_request():
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/chat/completions",
                    json={
                        "chat_id": "test-chat",
                        "model": "test",
                        "messages": [{"role": "user", "content": "测试消息"}],
                        "max_tokens": 100
                    },
                    timeout=10
                )
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code != 503
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "response_time": 10,
                    "success": False,
                    "error": str(e)
                }

        print(f"🧪 测试并发请求处理能力 ({concurrent_requests} 个请求)...")

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in futures]
        end_time = time.time()

        # 统计结果
        successful_requests = [r for r in results if r["success"]]
        rate_limited_requests = [r for r in results if r["status_code"] == 503]
        failed_requests = [r for r in results if not r["success"] and r["status_code"] != 503]

        return {
            "total_requests": concurrent_requests,
            "successful": len(successful_requests),
            "rate_limited": len(rate_limited_requests),
            "failed": len(failed_requests),
            "total_time": end_time - start_time,
            "success_rate": len(successful_requests) / concurrent_requests * 100,
            "rate_limiting_active": len(rate_limited_requests) > 0,
            "details": {
                "successful_requests": successful_requests[:5],  # 只保留前5个示例
                "rate_limited_requests": rate_limited_requests[:3],
                "failed_requests": failed_requests[:3]
            }
        }

    def run_full_check(self) -> Dict:
        """运行完整的优化效果检查"""
        print("🔍 开始检查数据库连接池优化效果...")
        print("=" * 50)

        results = {
            "timestamp": time.time(),
            "checks": {}
        }

        # 1. 基础健康检查
        print("\n1️⃣ 基础健康检查...")
        results["checks"]["health"] = self.check_health()

        # 2. 数据库连接池健康检查
        print("\n2️⃣ 数据库连接池健康检查...")
        results["checks"]["database_health"] = self.check_database_health()

        # 3. 详细连接池状态
        print("\n3️⃣ 详细连接池状态...")
        results["checks"]["pool_status"] = self.check_pool_status()

        # 4. 限流效果测试
        print("\n4️⃣ 限流效果测试...")
        results["checks"]["rate_limiting"] = self.test_rate_limiting()

        return results

    def generate_report(self, results: Dict):
        """生成优化效果报告"""
        print("\n" + "=" * 50)
        print("📊 数据库连接池优化效果报告")
        print("=" * 50)

        # 基础健康状态
        health = results["checks"]["health"]
        if health["status"] == "success":
            print("✅ 服务正常运行")
        else:
            print(f"❌ 服务异常: {health['error']}")

        # 数据库连接池状态
        db_health = results["checks"]["database_health"]
        if db_health["status"] == "success":
            data = db_health["data"]
            if isinstance(data, tuple):
                data = data[0]  # 如果返回了(status_code, data)元组

            print(f"✅ 数据库连接池状态: {data.get('status', 'unknown')}")
            print(f"📈 连接池使用率: {data.get('utilization', 'N/A')}")
            print(f"🔧 最大连接数: {data.get('max_connections', 'N/A')}")
            print(f"⚡ 工作进程数: {data.get('workers', 'N/A')}")

            # 检查安全余量
            if data.get('status') == 'healthy':
                print("✅ 连接池状态健康，安全余量充足")
            else:
                print("⚠️ 连接池状态需要注意")
                if 'alert' in data:
                    print(f"⚠️ {data['alert']}")
        else:
            print(f"❌ 无法获取数据库状态: {db_health['error']}")

        # 限流效果
        rate_limit = results["checks"]["rate_limiting"]
        print(f"\n🚦 限流效果测试结果:")
        print(f"   总请求数: {rate_limit['total_requests']}")
        print(f"   成功请求: {rate_limit['successful']}")
        print(f"   被限流请求: {rate_limit['rate_limited']}")
        print(f"   失败请求: {rate_limit['failed']}")
        print(f"   成功率: {rate_limit['success_rate']:.1f}%")

        if rate_limit['rate_limiting_active']:
            print("✅ 限流机制正常工作，保护了数据库连接池")
        else:
            print("⚠️ 未触发限流，可能当前负载较低")

        # 优化建议
        print(f"\n💡 优化建议:")
        if rate_limit['success_rate'] < 80:
            print("- 考虑调整限流参数，提高并发处理能力")
        if db_health["status"] == "success" and isinstance(db_health["data"], tuple):
            data = db_health["data"][0]
            if data.get('status') != 'healthy':
                print("- 监控连接池使用情况，考虑增加数据库连接数或优化查询")

        print("- 定期检查 /health/database 端点监控连接池状态")

if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    checker = OptimizationChecker(base_url)

    try:
        results = checker.run_full_check()
        checker.generate_report(results)
    except KeyboardInterrupt:
        print("\n⏹️ 检查被用户中断")
    except Exception as e:
        print(f"\n❌ 检查过程中出现错误: {e}")