@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM 🚀 Chat Completions 压力测试脚本 (Windows版本)
REM
REM 专门用于验证数据库连接优化效果
REM 目标服务器：172.21.33.8:8888
REM =============================================================================

REM 配置参数
set SERVER_IP=172.21.33.8:8888
set URL=http://%SERVER_IP%/v1/chat/completions
set TIMEOUT=30

REM 颜色输出 (Windows 10+)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

echo %BLUE%🧪 Chat Completions 压力测试 - 数据库连接优化验证%NC%
echo 目标服务器: %SERVER_IP%
echo =================================================

REM 检查依赖
echo %BLUE%检查系统依赖...%NC%

where curl >nul 2>nul
if %errorlevel% neq 0 (
    echo %RED%❌ curl 未安装，请先安装 curl%NC%
    echo 💡 下载地址: https://curl.se/windows/
    pause
    exit /b 1
)

echo %GREEN%✅ 依赖检查完成%NC%
echo.

REM 数据库连接优化效果测试
echo %BLUE%🔧 数据库连接优化效果验证测试%NC%
echo.

REM 场景1: 轻负载测试
echo 📋 场景1: 轻负载测试 - 验证基本功能
echo 🧵 线程数: 5
echo 📊 总请求: 50
echo 🎯 预期QPS: ~2
echo ----------------------------------------

set /a success_count=0
set /a failed_count=0
set start_time=%time%

REM 使用PowerShell进行并发请求
powershell -Command "
$ErrorActionPreference = 'SilentlyContinue';
$jobs = @();
for ($i = 1; $i -le 50; $i++) {
    $job = Start-Job -ScriptBlock {
        param($url, $id)
        $chatId = \"test_${id}_$([int][double]::Parse((Get-Date -UFormat %s)))_$$\"
        $query = \"这是压力测试请求 $id，时间戳 $([int][double]::Parse((Get-Date -UFormat %s)))\"
        $body = @{
            chat_id = $chatId
            model = 'xmtelecom'
            messages = @(@{
                role = 'user'
                content = $query
            })
            max_tokens = 8192
            temperature = 0.2
        } | ConvertTo-Json -Depth 10

        try {
            $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 30
            return 'SUCCESS'
        } catch {
            return 'FAILED'
        }
    } -ArgumentList '%URL%', $i
    $jobs += $job
}

# 等待所有任务完成
$success = 0
$failed = 0
foreach ($job in $jobs) {
    $result = Receive-Job -Job $job -Wait
    if ($result -eq 'SUCCESS') {
        $success++
    } else {
        $failed++
    }
    Remove-Job -Job $job
}

Write-Host \"SUCCESS:$success,FAILED:$failed\"
"

set end_time=%time%
echo ✅ 完成轻负载测试
echo.

REM 场景2: 中等负载测试
echo 📋 场景2: 中等负载测试 - 验证连接优化效果
echo 🧵 线程数: 20
echo 📊 总请求: 200
echo 🎯 预期QPS: ~7
echo ----------------------------------------

powershell -Command "
$ErrorActionPreference = 'SilentlyContinue';
$jobs = @();
$batchSize = 20
$totalRequests = 200

for ($batch = 0; $batch -lt [math]::Ceiling($totalRequests / $batchSize); $batch++) {
    $currentJobs = @()
    for ($i = 0; $i -lt $batchSize -and ($batch * $batchSize + $i) -lt $totalRequests; $i++) {
        $requestId = $batch * $batchSize + $i + 1
        $job = Start-Job -ScriptBlock {
            param($url, $id)
            $chatId = \"test_${id}_$([int][double]::Parse((Get-Date -UFormat %s)))_$$\"
            $query = \"请解释医保政策的基本概念，测试编号: $id\"
            $body = @{
                chat_id = $chatId
                model = 'xmtelecom'
                messages = @(@{
                    role = 'user'
                    content = $query
                })
                max_tokens = 8192
                temperature = 0.2
            } | ConvertTo-Json -Depth 10

            try {
                $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 30
                return 'SUCCESS'
            } catch {
                return 'FAILED'
            }
        } -ArgumentList '%URL%', $requestId
        $currentJobs += $job
    }

    # 等待当前批次完成
    foreach ($job in $currentJobs) {
        $result = Receive-Job -Job $job -Wait
        if ($result -eq 'SUCCESS') {
            Write-Host \"SUCCESS\"
        } else {
            Write-Host \"FAILED\"
        }
        Remove-Job -Job $job
    }
}
"

echo ✅ 完成中等负载测试
echo.

REM 场景3: 高负载测试
echo 📋 场景3: 高负载测试 - 验证并发处理能力提升
echo 🧵 线程数: 50
echo 📊 总请求: 500
echo 🎯 预期QPS: ~15
echo ----------------------------------------

echo ⚠️ 高负载测试需要较长时间，请耐心等待...

powershell -Command "
$ErrorActionPreference = 'SilentlyContinue';
$jobs = @();
$batchSize = 50
$totalRequests = 500

for ($batch = 0; $batch -lt [math]::Ceiling($totalRequests / $batchSize); $batch++) {
    Write-Host \"批次 $([math]::Floor($batch * $batchSize / 50 + 1))/10\"
    $currentJobs = @()
    for ($i = 0; $i -lt $batchSize -and ($batch * $batchSize + $i) -lt $totalRequests; $i++) {
        $requestId = $batch * $batchSize + $i + 1
        $job = Start-Job -ScriptBlock {
            param($url, $id)
            $chatId = \"test_${id}_$([int][double]::Parse((Get-Date -UFormat %s)))_$$\"
            $query = \"详细描述AI技术在医疗领域的应用，请求ID: $id\"
            $body = @{
                chat_id = $chatId
                model = 'xmtelecom'
                messages = @(@{
                    role = 'user'
                    content = $query
                })
                max_tokens = 8192
                temperature = 0.2
            } | ConvertTo-Json -Depth 10

            try {
                $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 60
                return 'SUCCESS'
            } catch {
                return 'FAILED'
            }
        } -ArgumentList '%URL%', $requestId
        $currentJobs += $job
    }

    # 等待当前批次完成
    foreach ($job in $currentJobs) {
        $result = Receive-Job -Job $job -Wait
        if ($result -eq 'SUCCESS') {
            Write-Host \"S\" -NoNewline
        } else {
            Write-Host \"F\" -NoNewline
        }
        Remove-Job -Job $job
    }
    Write-Host \"\"
}
"

echo ✅ 完成高负载测试
echo.

echo %GREEN%🎉 压力测试完成！%NC%
echo.
echo 📊 优化效果分析:
echo   - 优化前预期：连接占用时间长，QPS较低
echo   - 优化后预期：连接占用时间短，QPS显著提升
echo   - 关键指标：QPS提升、响应时间减少、成功率保持
echo.
echo 🔍 如果测试结果显示高QPS且响应稳定，说明数据库连接优化生效！
echo.
echo 💡 提示:
echo   - S = 成功请求，F = 失败请求
echo   - 观察S的比例，成功率应保持在95%以上
echo   - 如果失败率较高，可能需要调整服务器配置或减少并发数
echo.

pause