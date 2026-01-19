# GraphRAG Local Search API 使用指南

## 概述

GraphRAG Local Search API 提供了基于知识图谱的本地搜索功能，适合精确查询特定实体和关系的场景。与全局搜索不同，本地搜索更加关注查询上下文中的特定实体和它们之间的关系。

## API 端点

### 1. 本地搜索查询

**端点**: `POST /graphrag/local-search`

**描述**: 执行 GraphRAG 本地搜索并返回完整响应

**请求体**:
```json
{
  "query": "查询问题",
  "community_level": 2,
  "response_type": "Multiple Paragraphs"
}
```

**响应**:
```json
{
  "response": "搜索结果内容",
  "success": true,
  "metadata": {
    "query_length": 20,
    "response_length": 1500,
    "search_type": "local",
    "community_level": 2,
    "response_type": "Multiple Paragraphs"
  }
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/graphrag/local-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能的应用领域有哪些？",
    "community_level": 2,
    "response_type": "Multiple Paragraphs"
  }'
```

### 2. 本地搜索流式查询

**端点**: `POST /graphrag/local-search/stream`

**描述**: 流式执行 GraphRAG 本地搜索，实时返回搜索结果

**请求体**:
```json
{
  "query": "查询问题",
  "community_level": 2,
  "response_type": "Multiple Paragraphs"
}
```

**响应格式**: Server-Sent Events (SSE)

**事件类型**:
- `start`: 搜索开始
- `chunk`: 搜索结果数据块
- `done`: 搜索完成
- `error`: 错误信息

**JavaScript 示例**:
```javascript
const response = await fetch('/graphrag/local-search/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '人工智能的发展历史',
    community_level: 2,
    response_type: 'Multiple Paragraphs'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n').filter(line => line.trim());

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const data = JSON.parse(line.slice(6));

        switch (data.type) {
          case 'start':
            console.log('开始搜索:', data.query);
            break;
          case 'chunk':
            console.log('数据块:', data.content);
            break;
          case 'done':
            console.log('搜索完成');
            break;
          case 'error':
            console.error('搜索错误:', data.content);
            break;
        }
      } catch (e) {
        // 忽略解析错误
      }
    }
  }
}
```

## 参数说明

### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 用户查询问题 |
| `community_level` | int | 否 | 2 | 社区级别，控制搜索的粒度 |
| `response_type` | string | 否 | "Multiple Paragraphs" | 响应类型 |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `response` | string | 搜索结果内容 |
| `success` | boolean | 搜索是否成功 |
| `metadata` | object | 元数据信息 |
| `metadata.search_type` | string | 搜索类型，固定为 "local" |
| `metadata.query_length` | int | 查询字符串长度 |
| `metadata.response_length` | int | 响应内容长度 |

## 使用场景

### 适合使用本地搜索的场景

1. **实体关系查询**: 查询特定实体之间的关系
   - 例如: "人工智能和机器学习有什么关系？"

2. **精确定位**: 查询特定概念的详细信息
   - 例如: "深度学习的基本原理是什么？"

3. **上下文分析**: 分析特定领域的相关知识
   - 例如: "计算机视觉在自动驾驶中的应用"

### 与全局搜索的区别

| 特性 | 本地搜索 | 全局搜索 |
|------|----------|----------|
| 搜索范围 | 特定实体和关系 | 整个知识图谱 |
| 响应速度 | 较快 | 相对较慢 |
| 精确度 | 高 | 中等 |
| 适用场景 | 精确查询 | 综合性查询 |

## 错误处理

### 常见错误码

- `400`: 请求参数错误
- `500`: 服务器内部错误
- `503`: 服务不可用

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 性能优化建议

1. **合理设置社区级别**:
   - `community_level=1`: 更细粒度的搜索
   - `community_level=2-3`: 平衡精度和性能
   - `community_level>3`: 更宏观的搜索

2. **查询优化**:
   - 使用具体、明确的问题
   - 避免过于宽泛的查询
   - 合理利用流式接口处理长响应

3. **缓存策略**:
   - 对重复查询进行缓存
   - 使用流式接口提升用户体验

## 健康检查

**端点**: `GET /graphrag/health`

检查 Local Search 功能的可用性：

```json
{
  "status": "healthy",
  "service": "GraphRAG",
  "async_available": true,
  "sync_available": true,
  "stream_available": true,
  "local_search_available": true,
  "local_search_stream_available": true
}
```

## 开发工具

### 测试脚本

项目提供了完整的测试脚本：

```bash
# 运行 API 测试
python test_local_search_api.py

# 运行功能测试
python test_local_search.py
```

### 监控和日志

- 所有请求都会记录详细的日志
- 支持性能监控和错误追踪
- 提供查询统计和分析功能

## 最佳实践

1. **查询设计**
   - 使用清晰、具体的问题
   - 包含相关的关键词
   - 避免歧义和模糊表达

2. **错误处理**
   - 实现完善的错误处理机制
   - 提供友好的错误提示
   - 支持重试机制

3. **用户体验**
   - 优先使用流式接口
   - 提供加载状态指示
   - 实现结果缓存

4. **性能监控**
   - 监控响应时间
   - 跟踪错误率
   - 分析查询模式

## 版本信息

- **API 版本**: v1.0
- **GraphRAG 版本**: 2.7.0
- **最后更新**: 2024年11月