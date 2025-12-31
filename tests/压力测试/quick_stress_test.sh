#!/bin/bash

# =============================================================================
# 🚀 Chat Completions 快速压力测试脚本
#
# 专门用于验证数据库连接优化效果
# 目标服务器：172.21.33.8:8888
# =============================================================================

# 配置参数
SERVER_IP="172.21.33.8:8888"
URL="http://$SERVER_IP/v1/chat/completions"
TIMEOUT=30

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Chat Completions 压力测试 - 数据库连接优化验证${NC}"
echo "目标服务器: $SERVER_IP"
echo "================================================="

# 生成唯一Chat ID和查询内容
generate_request() {
    local id=$1
    local chat_id="test_${id}_$(date +%s)_$$"
    local query="这是压力测试请求 $id，时间戳 $(date +%s)"

    cat <<EOF
{
    "chat_id": "$chat_id",
    "model": "xmtelecom",
    "messages": [
        {"role": "user", "content": "$query"}
    ],
    "max_tokens": 8192,
    "temperature": 0.2
}
EOF
}

# 发送单个请求
send_request() {
    local request_id=$1
    local payload=$(generate_request $request_id)

    start_time=$(date +%s.%N)

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}\n" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT \
        "$URL" 2>/dev/null)

    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    curl_time=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)

    if [ "$http_code" = "200" ]; then
        echo "SUCCESS,$request_id,$duration,$curl_time"
    else
        echo "FAILED,$request_id,$duration,$curl_time,HTTP_$http_code"
    fi
}

# 压力测试函数
run_stress_test() {
    local threads=$1
    local requests=$2
    local test_name=$3

    echo -e "${YELLOW}🔥 测试: $test_name${NC}"
    echo "🧵 线程数: $threads"
    echo "📊 总请求: $requests"
    echo "🎯 预期QPS: $(echo "scale=1; $requests / 30" | bc -l)"
    echo "----------------------------------------"

    temp_file=$(mktemp)
    start_time=$(date +%s)

    # 并发执行请求
    seq 1 $requests | xargs -I {} -P $threads bash -c '
        request_id=$1
        send_request "$request_id"
    ' _ {} > "$temp_file" 2>&1

    end_time=$(date +%s)
    total_time=$((end_time - start_time))

    # 统计结果
    success_count=$(grep "^SUCCESS" "$temp_file" | wc -l)
    failed_count=$(grep "^FAILED" "$temp_file" | wc -l)
    actual_qps=$(echo "scale=1; $success_count / $total_time" | bc -l)
    success_rate=$(echo "scale=1; $success_count * 100 / $requests" | bc -l)

    # 计算平均响应时间
    if [ $success_count -gt 0 ]; then
        avg_response_time=$(grep "^SUCCESS" "$temp_file" | cut -d, -f4 | awk '{sum+=$1} END {print sum/NR}')
        echo "📏 平均响应时间: ${avg_response_time}s"
    fi

    echo "✅ 成功请求: $success_count"
    echo "❌ 失败请求: $failed_count"
    echo "🎯 成功率: ${success_rate}%"
    echo "⏱️  总耗时: ${total_time}s"
    echo "🚀 实际QPS: $actual_qps"
    echo ""

    rm -f "$temp_file"
}

# 检查依赖
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl 未安装，请先安装 curl${NC}"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    echo -e "${RED}❌ bc 未安装，请先安装 bc${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 依赖检查通过${NC}"
echo ""

# 数据库连接优化效果测试场景
echo -e "${BLUE}🔧 数据库连接优化效果验证测试${NC}"
echo ""

# 场景1: 轻负载测试 (验证基本功能)
echo "📋 场景1: 轻负载测试 - 验证基本功能"
run_stress_test 5 50 "light_load"

# 场景2: 中等负载测试 (验证优化效果)
echo "📋 场景2: 中等负载测试 - 验证连接优化效果"
run_stress_test 20 200 "medium_load"

# 场景3: 高负载测试 (验证并发处理能力)
echo "📋 场景3: 高负载测试 - 验证并发处理能力提升"
run_stress_test 50 500 "high_load"

# 场景4: 极限负载测试 (验证数据库连接池优化)
echo "📋 场景4: 极限负载测试 - 验证连接池优化效果"
run_stress_test 100 1000 "extreme_load"

echo -e "${GREEN}🎉 压力测试完成！${NC}"
echo ""
echo "📊 优化效果分析:"
echo "  - 优化前预期：连接占用时间长，QPS较低"
echo "  - 优化后预期：连接占用时间短，QPS显著提升"
echo "  - 关键指标：QPS提升、响应时间减少、成功率保持"
echo ""
echo "🔍 如果QPS显著提升且响应时间稳定，说明数据库连接优化生效！"