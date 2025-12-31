#!/usr/bin/env python3
"""
测试运行脚本
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """运行命令并处理结果"""
    print(f"🚀 运行命令: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print(result.stdout)
        if result.stderr:
            print("⚠️ 警告信息:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败 (退出码: {e.returncode})")
        print("错误输出:")
        print(e.stderr)
        return False


def main():
    """主函数"""
    print("🧪 AI App 测试运行器")
    print("=" * 60)

    # 确定虚拟环境的Python路径
    venv_python = Path(".venv/Scripts/python.exe")
    if not venv_python.exists():
        print("❌ 找不到虚拟环境，请确保 .venv 目录存在")
        sys.exit(1)

    # 测试命令列表
    test_commands = [
        # 1. 运行所有测试（详细输出）
        [
            str(venv_python), "-m", "pytest",
            "tests/", "-v", "--tb=short"
        ],
        # 2. 生成连接池监控器覆盖率报告
        [
            str(venv_python), "-m", "pytest",
            "tests/test_connection_monitor.py",
            "--cov=app.monitor.connection_monitor",
            "--cov-report=term-missing"
        ],
        # 3. 生成断路器覆盖率报告
        [
            str(venv_python), "-m", "pytest",
            "tests/test_circuit_breaker.py",
            "--cov=app.utils.circuit_breaker",
            "--cov-report=term-missing"
        ],
        # 4. 生成综合HTML覆盖率报告
        [
            str(venv_python), "-m", "pytest",
            "tests/",
            "--cov=app.monitor.connection_monitor",
            "--cov=app.utils.circuit_breaker",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ],
        # 5. 生成性能分析报告（如果安装了 pytest-benchmark）
        [
            str(venv_python), "-m", "pytest",
            "tests/test_connection_monitor.py::TestConnectionPoolMonitor::test_collect_stats",
            "--benchmark-only"
        ] if "--benchmark" in sys.argv else None
    ]

    # 过滤掉None的命令
    test_commands = [cmd for cmd in test_commands if cmd is not None]

    # 运行测试
    success_count = 0
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n📋 测试 {i}/{len(test_commands)}")

        if run_command(cmd):
            success_count += 1
            print(f"✅ 测试 {i} 完成")
        else:
            print(f"❌ 测试 {i} 失败")

        print("=" * 60)

    # 总结
    print(f"\n📊 测试总结: {success_count}/{len(test_commands)} 个测试成功")

    if success_count == len(test_commands):
        print("🎉 所有测试通过！")

        # 如果生成了HTML覆盖率报告，提醒用户查看
        if Path("htmlcov").exists():
            print("📈 HTML覆盖率报告已生成，请打开 htmlcov/index.html 查看")

        return 0
    else:
        print("💥 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())