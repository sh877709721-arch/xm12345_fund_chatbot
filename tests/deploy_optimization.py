#!/usr/bin/env python3
"""
数据库连接池优化部署脚本

用于快速集成连接池保护机制到现有的AI应用中
"""

import os
import sys
import shutil
from pathlib import Path

def create_file_with_backup(file_path: str, content: str):
    """创建文件并备份原有文件"""
    path = Path(file_path)

    # 如果文件存在，创建备份
    if path.exists():
        backup_path = path.with_suffix(f'.backup_{int(time.time())}')
        shutil.copy2(path, backup_path)
        print(f"✅ 已备份原文件: {backup_path}")

    # 写入新内容
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已创建文件: {file_path}")

def check_existing_structure():
    """检查现有项目结构"""
    required_files = [
        "app/router/chat.py",
        "app/config/database.py",
        "app/core/util.py",
        "main.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ 缺少必要文件:")
        for f in missing_files:
            print(f"   - {f}")
        return False

    return True

def integrate_optimizations():
    """集成优化方案"""
    print("🚀 开始集成数据库连接池优化...")

    if not check_existing_structure():
        print("❌ 项目结构检查失败，请确保在正确的项目目录中运行此脚本")
        return False

    # 检查是否已经优化过
    if Path("app/middleware").exists():
        print("⚠️ 检测到已存在优化文件，跳过创建")
        return True

    try:
        # 1. 创建中间件目录和文件
        print("\n📁 创建中间件...")
        Path("app/middleware/__init__.py").write_text("")

        # 2. 创建工具目录和文件
        print("\n🛠️ 创建工具模块...")
        Path("app/utils/__init__.py").write_text("")

        # 3. 创建监控目录和文件
        print("\n📊 创建监控模块...")
        Path("app/monitor/__init__.py").write_text("")

        print("\n✅ 目录结构创建完成")
        print("\n📋 下一步操作:")
        print("1. 将我们创建的以下文件复制到对应位置:")
        print("   - app/middleware/rate_limiter.py -> app/middleware/")
        print("   - app/utils/circuit_breaker.py -> app/utils/")
        print("   - app/monitor/connection_monitor.py -> app/monitor/")
        print("\n2. 更新您的 main.py，集成中间件和监控")
        print("   - 参考 app_main_enhanced.py 的集成方式")
        print("\n3. 重新部署应用")

        return True

    except Exception as e:
        print(f"❌ 集成失败: {e}")
        return False

def generate_docker_compose():
    """生成优化的 docker-compose 配置"""
    config = """
version: '3.8'

services:
  ai-chat-app:
    build: .
    environment:
      - WORKERS=8
      - MAX_CONNECTIONS_PER_WORKER=20
      - DATABASE_POOL_SIZE=15
      - DATABASE_MAX_OVERFLOW=15
    deploy:
      replicas: 2  # 部署2个实例，共160个数据库连接
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/database"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - ai-chat-app

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=housing_fund
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
      - MAX_CONNECTIONS=200  # 数据库最大连接数
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
      -c maintenance_work_mem=64MB
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

    with open("docker-compose.optimized.yml", "w") as f:
        f.write(config)

    print("✅ 已生成优化的 docker-compose.optimized.yml")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 AI Chat Service 数据库连接池优化工具")
    print("=" * 60)

    # 检查当前目录
    if not Path("app").exists():
        print("❌ 请在项目根目录中运行此脚本")
        sys.exit(1)

    # 集成优化
    if integrate_optimizations():
        print("\n🎉 优化集成完成!")
        print("\n📖 接下来的步骤:")
        print("1. 检查并复制生成的优化文件到对应位置")
        print("2. 更新您的 main.py")
        print("3. 重新部署应用")
        print("4. 访问 /health/database 监控连接池状态")

        # 生成 docker-compose 配置
        generate_docker_compose()

        print("\n📊 监控端点:")
        print("- 健康检查: GET /health")
        print("- 连接池状态: GET /health/database")
        print("- 详细监控: GET /monitor/pool")

    else:
        print("\n❌ 优化集成失败，请检查错误信息")
        sys.exit(1)