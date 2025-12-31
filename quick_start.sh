#!/bin/bash

# AI Chat Service 快速启动脚本

set -e

echo "🚀 AI Chat Service 快速启动脚本"
echo "================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 选择启动模式
echo "请选择启动模式："
echo "1) 共享内存限流（推荐用于开发/单机）"
echo "2) Redis分布式限流（推荐用于生产环境）"
read -p "请输入选择 (1 或 2): " choice

case $choice in
    1)
        echo "📦 启动共享内存模式..."
        docker-compose -f docker-compose.shared-memory.yml up -d
        ;;
    2)
        echo "📦 启动Redis分布式模式..."
        docker-compose -f docker-compose.redis.yml up -d
        ;;
    *)
        echo "❌ 无效选择，默认使用共享内存模式"
        docker-compose -f docker-compose.shared-memory.yml up -d
        ;;
esac

echo ""
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📊 检查服务状态..."
echo ""

# 基础健康检查
echo "1. 基础健康检查："
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ 服务正常运行"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "   ❌ 服务启动失败"
    docker-compose logs
    exit 1
fi

echo ""

# 数据库健康检查
echo "2. 数据库连接池状态："
if curl -f http://localhost:8000/health/database > /dev/null 2>&1; then
    echo "   ✅ 数据库连接正常"
    curl -s http://localhost:8000/health/database | python3 -m json.tool
else
    echo "   ❌ 数据库连接失败"
fi

echo ""

# Worker统计
echo "3. Worker统计信息："
if curl -f http://localhost:8000/stats/workers > /dev/null 2>&1; then
    curl -s http://localhost:8000/stats/workers | python3 -m json.tool
else
    echo "   ⚠️ 无法获取Worker统计信息"
fi

echo ""
echo "🎉 AI Chat Service 启动完成！"
echo ""
echo "📋 服务信息："
echo "   - API地址: http://localhost:8000"
echo "   - 健康检查: http://localhost:8000/health"
echo "   - 数据库状态: http://localhost:8000/health/database"
echo "   - 限流器状态: http://localhost:8000/health/rate-limiter"
echo "   - Worker统计: http://localhost:8000/stats/workers"
echo ""
echo "🔍 测试命令："
echo "   curl http://localhost:8000/health"
echo "   python check_optimization.py"
echo ""
echo "🛑 停止服务："
echo "   docker-compose -f docker-compose.$([ "$choice" = "2" ] && echo "redis" || echo "shared-memory").yml down"