#!/bin/bash

# =============================================================================
# 🧪 压力测试脚本验证工具
# =============================================================================

echo "🧪 验证压力测试脚本..."
echo ""

# 检查脚本语法
echo "1. 检查 shell 脚本语法:"
if bash -n stress_test_chat_completions.sh; then
    echo "✅ stress_test_chat_completions.sh 语法正确"
else
    echo "❌ stress_test_chat_completions.sh 语法错误"
fi

if bash -n quick_stress_test.sh; then
    echo "✅ quick_stress_test.sh 语法正确"
else
    echo "❌ quick_stress_test.sh 语法错误"
fi

echo ""

# 检查关键配置
echo "2. 检查服务器配置:"
if grep -q "172.21.33.8" stress_test_chat_completions.sh; then
    echo "✅ 服务器IP配置正确: 172.21.33.8"
else
    echo "❌ 服务器IP配置错误"
fi

if grep -q "v1/chat/completions" stress_test_chat_completions.sh; then
    echo "✅ API端点配置正确: /v1/chat/completions"
else
    echo "❌ API端点配置错误"
fi

echo ""

# 检查关键功能
echo "3. 检查关键功能:"
if grep -q "数据库连接优化" stress_test_chat_completions.sh; then
    echo "✅ 包含数据库连接优化测试"
else
    echo "❌ 缺少数据库连接优化测试"
fi

if grep -q "QPS" stress_test_chat_completions.sh; then
    echo "✅ 包含QPS性能指标"
else
    echo "❌ 缺少QPS性能指标"
fi

echo ""

# 检查依赖
echo "4. 检查系统依赖:"
if command -v curl &> /dev/null; then
    echo "✅ curl 已安装"
else
    echo "❌ curl 未安装"
fi

if command -v bc &> /dev/null; then
    echo "✅ bc 已安装"
else
    echo "❌ bc 未安装"
fi

echo ""
echo "🎉 验证完成！"
echo ""
echo "📋 可用测试脚本:"
echo "  - stress_test_chat_completions.sh  (完整功能)"
echo "  - quick_stress_test.sh           (快速测试)"
echo "  - stress_test_chat_completions.bat (Windows版本)"
echo ""
echo "🚀 使用方法:"
echo "  ./stress_test_chat_completions.sh --quick"
echo "  ./quick_stress_test.sh"