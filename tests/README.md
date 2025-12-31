# 测试文档

## 概述

本目录包含 AI 应用的单元测试，目前主要测试连接池监控功能。

## 测试覆盖率

当前测试覆盖率：

- **连接池监控器**：90% (88/69 statements)
- **断路器**：100% (69/69 statements)
- **综合覆盖率**：约 95%

**测试覆盖的功能**：
- 连接池监控器功能：全面测试
- 断路器状态管理：完整测试
- 事件监听器：基础功能测试
- 错误处理：覆盖异常情况
- 熔断机制：全流程测试

## 运行测试

### 方法 1：使用测试运行脚本（推荐）

```bash
python run_tests.py
```

这将运行：
1. 所有测试（详细输出）
2. 覆盖率报告（终端 + HTML）
3. 性能基准测试（如果安装了 pytest-benchmark）

### 方法 2：直接使用 pytest

```bash
# 运行所有测试
.venv/Scripts/python.exe -m pytest tests/ -v

# 运行特定测试文件
.venv/Scripts/python.exe -m pytest tests/test_connection_monitor.py -v

# 运行特定测试方法
.venv/Scripts/python.exe -m pytest tests/test_connection_monitor.py::TestConnectionPoolMonitor::test_collect_stats -v
```

### 方法 3：生成覆盖率报告

```bash
# 终端覆盖率报告
.venv/Scripts/python.exe -m pytest tests/test_connection_monitor.py --cov=app.monitor.connection_monitor --cov-report=term-missing

# HTML覆盖率报告
.venv/Scripts/python.exe -m pytest tests/test_connection_monitor.py --cov=app.monitor.connection_monitor --cov-report=html:htmlcov
```

## 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest配置和共享fixtures
├── test_connection_monitor.py  # 连接池监控器测试
├── test_circuit_breaker.py  # 断路器测试
└── README.md               # 本文档
```

## 测试内容

### TestConnectionPoolMonitor

测试连接池监控器的各种功能：

- **初始化测试**：验证监控器正确初始化
- **统计收集测试**：验证连接池统计信息正确获取
- **错误处理测试**：测试连接池方法不存在时的回退机制
- **健康检查测试**：验证连接池健康状态判断逻辑
- **监控循环测试**：测试后台监控线程的正常运行和异常处理
- **日志记录测试**：验证不同使用率下的日志级别
- **线程管理测试**：测试监控线程的启动和停止

### TestConnectionListeners

测试连接池事件监听器：

- **监听器设置测试**：验证事件监听器正确注册

### TestDatabaseCircuitBreaker

测试数据库断路器的各种功能：

- **初始化测试**：验证断路器正确初始化
- **状态转换测试**：测试关闭、开启、半开状态之间的转换
- **熔断机制测试**：验证失败阈值触发和恢复超时机制
- **错误处理测试**：测试数据库连接错误和超时错误的处理
- **重试时间计算测试**：验证熔断状态下的重试时间计算
- **恢复机制测试**：测试半开状态下的成功恢复和失败回退
- **装饰器功能测试**：验证断路器装饰器的完整功能

## 添加新测试

1. 在 `tests/` 目录下创建新的测试文件，命名格式为 `test_*.py`
2. 编写测试类，继承 `unittest.TestCase` 或使用 pytest 风格
3. 使用 `@patch` 装饰器模拟外部依赖
4. 在 `conftest.py` 中添加共享的 fixtures（如需要）

## 最佳实践

1. **命名规范**：测试方法名应描述测试内容，如 `test_method_should_return_true_when_condition_met`
2. **隔离性**：每个测试应该独立，不依赖其他测试的状态
3. **Mock使用**：使用 mock 对象隔离外部依赖（数据库、网络等）
4. **断言清晰**：使用明确的断言消息说明期望结果
5. **边界测试**：测试正常情况、边界情况和异常情况

## 持续集成

测试可以在以下环境中自动运行：
- 开发环境：`python run_tests.py`
- CI/CD环境：配置在 GitHub Actions 或其他CI工具中
- 代码提交前：建议本地运行测试确保代码质量

## 故障排除

### 常见问题

1. **导入错误**：确保虚拟环境已激活，依赖已安装
2. **权限问题**：确保脚本有执行权限
3. **端口冲突**：如果测试涉及网络端口，确保端口未被占用

### 调试技巧

```bash
# 运行测试时显示详细输出
pytest -v -s tests/

# 运行特定测试并在失败时停止
pytest -x tests/

# 显示本地变量
pytest -l tests/
```