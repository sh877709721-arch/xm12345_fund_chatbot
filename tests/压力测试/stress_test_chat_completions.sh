#!/bin/bash

# =============================================================================
# 🔧 AI Chat Completions 接口压力测试脚本
#
# 功能：测试优化后的 /chat/completions 接口性能
# 目标：验证数据库连接优化效果
# IP：172.21.33.8 (已按要求修改)
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置参数
BASE_URL="http://172.21.33.8:8888"
ENDPOINT="/v1/chat/completions"
FULL_URL="${BASE_URL}${ENDPOINT}"
TIMEOUT=30
OUTPUT_DIR="./test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}=== $1 ===${NC}"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装，请先安装 curl"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，将跳过 JSON 解析"
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi

    log_success "依赖检查完成"
}

# 生成唯一的 chat_id
generate_chat_id() {
    echo "test_$(date +%s)_$$_$RANDOM"
}

# 生成测试查询
generate_query() {
    local test_id=$1
    local timestamp=$(date +%s)

    # 不同类型的测试查询
    local queries=(
        "你好，这是压力测试请求 $test_id，时间戳: $timestamp"
        "请解释医保政策的基本概念，测试编号: $test_id"
        "详细描述AI技术在医疗领域的应用，请求ID: $test_id"
        "什么是机器学习？请详细说明，测试时间: $timestamp"
        "如何进行有效的项目管理？请求编号: $test_id，时间戳: $timestamp"
    )

    local index=$((test_id % ${#queries[@]}))
    echo "${queries[$index]}"
}

# 发送单个请求
send_request() {
    local chat_id=$(generate_chat_id)
    local query="$1"
    local request_id="$2"

    # 构造请求体
    local payload=$(cat <<EOF
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
)

    local temp_file=$(mktemp)
    local start_time=$(date +%s.%N)

    # 发送请求
    if curl -s -w "@-" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "$payload" \
        --connect-timeout $TIMEOUT \
        --max-time $TIMEOUT \
        "$FULL_URL" > "$temp_file" 2>&1 <<'CURL_FORMAT'
{
    "http_code": %{http_code},
    "time_connect": %{time_connect},
    "time_appconnect": %{time_appconnect},
    "time_pretransfer": %{time_pretransfer},
    "time_starttransfer": %{time_starttransfer},
    "time_total": %{time_total},
    "size_download": %{size_download}
}
CURL_FORMAT
    then
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc -l)

        # 解析响应
        if [ "$JQ_AVAILABLE" = true ]; then
            local http_code=$(cat "$temp_file" | tail -n 1 | jq -r '.http_code // 0')
            local response_time=$(cat "$temp_file" | tail -n 1 | jq -r '.time_total // 0')
        else
            local http_code=$(cat "$temp_file" | tail -n 1 | grep -o '"http_code": [0-9]*' | cut -d: -f2 | tr -d ' ')
            local response_time=$(cat "$temp_file" | tail -n 1 | grep -o '"time_total": [0-9.]*' | cut -d: -f2 | tr -d ' ')
        fi

        # 判断请求是否成功
        if [ "$http_code" = "200" ]; then
            echo "SUCCESS,$request_id,$duration,$response_time,$query"
        else
            echo "FAILED,$request_id,$duration,$response_time,HTTP_$http_code"
        fi
    else
        echo "ERROR,$request_id,0,0,CURL_ERROR"
    fi

    rm -f "$temp_file"
}

# 并发压力测试
run_stress_test() {
    local concurrent_users=$1
    local total_requests=$2
    local test_name=$3

    log_header "开始压力测试: $test_name"
    log_info "目标URL: $FULL_URL"
    log_info "并发线程数: $concurrent_users"
    log_info "总请求数: $total_requests"
    log_info "预计QPS: $(echo "scale=2; $total_requests / 30" | bc -l)"

    local temp_result=$(mktemp)
    local start_time=$(date +%s)

    log_info "发送并发请求..."

    # 使用 xargs 进行并发请求
    seq 1 $total_requests | xargs -I {} -P $concurrent_users bash -c "
        query=\"$(generate_query {})\"
        send_request \"\$query\" {}
    " >> "$temp_result"

    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    # 分析结果
    analyze_results "$temp_result" "$concurrent_users" "$total_requests" "$total_time" "$test_name"

    rm -f "$temp_result"
}

# 分析测试结果
analyze_results() {
    local result_file=$1
    local concurrent_users=$2
    local total_requests=$3
    local total_time=$4
    local test_name=$5

    log_header "测试结果分析: $test_name"

    # 统计成功和失败请求
    local success_count=$(grep "^SUCCESS" "$result_file" | wc -l)
    local failed_count=$(grep "^FAILED\|^ERROR" "$result_file" | wc -l)
    local actual_qps=$(echo "scale=2; $success_count / $total_time" | bc -l)

    echo "📊 测试统计:"
    echo "  ✅ 成功请求: $success_count"
    echo "  ❌ 失败请求: $failed_count"
    echo "  🎯 成功率: $(echo "scale=2; $success_count * 100 / $total_requests" | bc -l)%"
    echo "  ⏱️  总耗时: ${total_time}s"
    echo "  🚀 实际QPS: $actual_qps"
    echo "  🧵 并发线程: $concurrent_users"

    # 响应时间统计（如果使用了jq且curl格式化）
    if [ "$JQ_AVAILABLE" = true ]; then
        local response_times=$(grep "^SUCCESS" "$result_file" | cut -d, -f4)
        if [ -n "$response_times" ]; then
            echo ""
            echo "⏱️  响应时间统计:"
            echo "  📏 平均响应时间: $(echo "$response_times" | awk '{sum+=$1} END {print sum/NR}' | bc -l)s"
            echo "  🚀 最快响应时间: $(echo "$response_times" | sort -n | head -1)s"
            echo "  🐢 最慢响应时间: $(echo "$response_times" | sort -n | tail -1)s"
        fi
    fi

    # 保存详细结果
    local output_file="${OUTPUT_DIR}/stress_test_${test_name}_${TIMESTAMP}.csv"
    cp "$result_file" "$output_file"
    log_success "详细结果已保存到: $output_file"

    echo ""
}

# 数据库连接优化效果测试
test_db_optimization() {
    log_header "🔧 数据库连接优化效果测试"

    log_info "此测试专门验证数据库连接优化效果"
    log_info "优化前预期：连接占用时间长，QPS较低"
    log_info "优化后预期：连接占用时间短，QPS显著提升"

    echo ""

    # 测试1：轻负载测试（验证基本功能）
    run_stress_test 5 50 "light_load"
    sleep 5

    # 测试2：中等负载测试（验证优化效果）
    run_stress_test 20 200 "medium_load"
    sleep 5

    # 测试3：高负载测试（验证并发处理能力）
    run_stress_test 50 500 "high_load"
}

# 稳定性测试
test_stability() {
    log_header "🛡️ 系统稳定性测试"

    log_info "进行长时间稳定性测试..."
    log_info "持续发送请求，监控系统稳定性"

    local duration=300  # 5分钟
    local requests_per_second=10

    log_info "测试时长: ${duration}秒"
    log_info "目标QPS: $requests_per_second"

    local end_time=$(($(date +%s) + duration))
    local temp_result=$(mktemp)
    local request_count=0

    while [ $(date +%s) -lt $end_time ]; do
        for i in $(seq 1 $requests_per_second); do
            query="$(generate_query $request_count)"
            send_request "$query" $request_count >> "$temp_result" &
            request_count=$((request_count + 1))
        done
        wait
        sleep 1
    done

    local total_time=$duration
    analyze_results "$temp_result" $requests_per_second $request_count $total_time "stability"

    rm -f "$temp_result"
}

# 单连接性能测试
test_single_connection() {
    log_header "🔍 单连接性能基准测试"

    log_info "测试单个请求的性能基准"

    local temp_result=$(mktemp)
    local test_requests=10

    for i in $(seq 1 $test_requests); do
        query="$(generate_query $i)"
        send_request "$query" $i >> "$temp_result"
        sleep 1
    done

    analyze_results "$temp_result" 1 $test_requests $test_requests "single_connection"

    rm -f "$temp_result"
}

# 主菜单
show_menu() {
    echo ""
    log_header "🚀 AI Chat Completions 压力测试工具"
    echo "目标服务器: $BASE_URL"
    echo "测试接口: $ENDPOINT"
    echo ""
    echo "请选择测试类型:"
    echo "1) 🔧 数据库连接优化效果测试 (推荐)"
    echo "2) 🛡️ 系统稳定性测试"
    echo "3) 🔍 单连接性能基准测试"
    echo "4) 🎯 自定义压力测试"
    echo "5) 📋 运行所有测试"
    echo "0) 退出"
    echo ""
}

# 自定义测试
custom_test() {
    log_header "🎯 自定义压力测试"

    read -p "请输入并发线程数 (默认10): " concurrent_users
    read -p "请输入总请求数 (默认100): " total_requests

    concurrent_users=${concurrent_users:-10}
    total_requests=${total_requests:-100}

    read -p "请输入测试名称: " test_name
    test_name=${test_name:-"custom_test"}

    run_stress_test $concurrent_users $total_requests $test_name
}

# 主函数
main() {
    echo ""
    log_header "🧪 AI Chat Completions 接口压力测试"
    echo "🔧 数据库连接优化效果验证"
    echo "📊 性能基准测试工具"
    echo ""

    check_dependencies

    while true; do
        show_menu
        read -p "请输入选项 [0-5]: " choice

        case $choice in
            1)
                test_db_optimization
                ;;
            2)
                test_stability
                ;;
            3)
                test_single_connection
                ;;
            4)
                custom_test
                ;;
            5)
                test_single_connection
                sleep 3
                test_db_optimization
                sleep 3
                test_stability
                ;;
            0)
                log_info "退出测试工具"
                exit 0
                ;;
            *)
                log_error "无效选项，请重新选择"
                ;;
        esac

        echo ""
        read -p "按 Enter 键继续..."
    done
}

# 检查参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help, -h     显示帮助信息"
    echo "  --quick        快速测试（轻负载 + 中负载）"
    echo "  --full         完整测试（所有测试）"
    echo ""
    echo "示例:"
    echo "  $0             # 交互式菜单"
    echo "  $0 --quick     # 快速测试"
    echo "  $0 --full      # 完整测试"
    exit 0
fi

if [ "$1" = "--quick" ]; then
    check_dependencies
    test_single_connection
    sleep 3
    test_db_optimization
    exit 0
fi

if [ "$1" = "--full" ]; then
    check_dependencies
    test_single_connection
    sleep 3
    test_db_optimization
    sleep 3
    test_stability
    exit 0
fi

# 启动主程序
main