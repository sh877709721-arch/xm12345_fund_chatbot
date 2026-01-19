# GraphRAG 集成到 Completions 接口使用指南

## 概述

GraphRAG 已成功集成到 `/v1/chat/completions` 接口中，通过设置 `model` 参数为 `"boost"` 来启用 GraphRAG 增强搜索功能。

## 使用方式

### 1. API 调用示例

#### GraphRAG Boost 模式

```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "your-chat-id",
    "model": "boost",
    "messages": [
      {"role": "user", "content": "怎么交医保"}
    ],
    "max_tokens": 8192,
    "temperature": 0.2
  }'
```

#### 标准 RAG 模式

```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "your-chat-id",
    "model": "default",
    "messages": [
      {"role": "user", "content": "怎么交医保"}
    ],
    "max_tokens": 8192,
    "temperature": 0.2
  }'
```

### 2. 模型选择

| 模型值 | 描述 | 功能特点 |
|--------|------|----------|
| `"default"` | 标准 RAG Bot | 基于向量的相似性搜索 |
| `"boost"` | GraphRAG 增强 | 基于知识图谱的精确搜索 |
| 其他值 | 其他 Agent | 根据 agent_factory 配置 |

### 3. 响应格式

所有模式都返回相同格式的流式响应：

```
data: {"type": "start", "content": ""}
data: {"type": "content", "content": "响应内容片段"}
data: {"type": "content", "content": "更多响应内容"}
data: {"type": "end", "content": ""}
```

## GraphRAG 特性

### 搜索方式
- **本地搜索**: 专注于特定实体和关系的精确查询
- **知识图谱**: 利用实体、关系和社区结构进行推理
- **流式响应**: 实时返回搜索结果

### 适用场景
- 精确查询特定概念
- 实体间关系分析
- 专业领域问题解答
- 需要高准确性的查询

### 技术优势
- **SOLID 原则**: 代码结构清晰，易于维护
- **DRY 原则**: 复用现有基础设施
- **KISS 原则**: 简单直观的接口设计
- **性能优化**: 使用后台任务，避免数据库连接阻塞

## 代码实现

### 核心文件
- [`app/router/chat.py:53-129`](app/router/chat.py#L53): GraphRAG 流式响应函数
- [`app/router/chat.py:240-249`](app/router/chat.py#L240): completions 接口集成逻辑
- [`app/core/graph/query_graphrag.py`](app/core/graph/query_graphrag.py): GraphRAG 核心实现

### 关键函数
```python
def graphrag_stream_response_optimized(
    chat_id: str,
    query: str,
    user_message_id: str,
    assistant_message_id: str,
    background_tasks: BackgroundTasks
) -> StreamingResponse
```

## 测试工具

### Python 测试脚本
```bash
# 运行集成测试
python test_graphrag_integration.py
```

### 功能测试
```bash
# 运行功能测试
python test_local_search.py

# 运行 API 测试
python test_local_search_api.py
```

## 监控和日志

### 日志记录
- GraphRAG 查询开始和完成
- 响应长度和处理时间
- 错误信息和异常处理
- 后台任务执行状态

### 性能指标
- 查询响应时间
- 数据块数量和大小
- 数据库操作耗时
- 内存和 CPU 使用率

## 配置选项

### GraphRAG 配置
- `community_level`: 社区级别 (默认: 2)
- `response_type`: 响应类型 (默认: "Multiple Paragraphs")
- `dynamic_community_selection`: 动态社区选择 (默认: false)

### 数据文件路径
```python
PROJECT_DIRECTORY = "./app/core/graph/chatbot_zh"
```
- `output/entities.parquet`: 实体数据
- `output/communities.parquet`: 社区数据
- `output/community_reports.parquet`: 社区报告
- `output/relationships.parquet`: 关系数据
- `output/text_units.parquet`: 文本单元

## 错误处理

### 常见错误
1. **数据文件缺失**: 确保所有必需的 parquet 文件存在
2. **配置错误**: 检查 settings.yaml 配置
3. **内存不足**: GraphRAG 需要较多内存处理知识图谱
4. **网络问题**: 检查 API 服务状态

### 错误响应
```json
{
  "detail": "GraphRAG 处理失败: 具体错误信息"
}
```

## 最佳实践

### 查询优化
- 使用明确、具体的问题
- 包含相关关键词和实体名称
- 避免过于宽泛或模糊的查询

### 性能优化
- 合理设置 `community_level` 参数
- 使用流式响应处理长内容
- 监控内存和 CPU 使用情况

### 集成建议
- 在需要高准确性查询时使用 GraphRAG
- 对于简单查询可以使用标准 RAG
- 根据业务需求动态选择模型类型

## 版本信息

- **集成版本**: v1.0
- **GraphRAG 版本**: 2.7.0
- **最后更新**: 2024年11月21日

## 支持

如有问题或需要帮助，请检查：
1. 服务器日志文件
2. GraphRAG 数据文件状态
3. API 服务运行状态
4. 数据库连接状况