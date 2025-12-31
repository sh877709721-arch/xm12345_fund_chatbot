# GraphRAG 中间结果提取指南

本指南介绍如何使用 GraphRAG 中间结果提取功能来分析和优化 RAG 系统的性能。

## 📋 目录

- [功能概述](#功能概述)
- [核心概念](#核心概念)
- [快速开始](#快速开始)
- [API 使用](#api-使用)
- [数据结构](#数据结构)
- [性能优化](#性能优化)
- [故障排除](#故障排除)

## 🎯 功能概述

GraphRAG 中间结果提取功能可以捕获调用大模型前的关键处理步骤，包括：

1. **向量检索阶段**
   - 查询向量化结果
   - 匹配实体列表及相似度分数
   - 检索耗时统计

2. **实体映射阶段**
   - 原始查询和处理后查询
   - 选中、排除、包含的实体信息
   - 实体过滤结果

3. **上下文构建阶段**
   - 社区报告上下文
   - 实体关系上下文
   - 文本单元上下文
   - 对话历史上下文
   - 最终整合的 prompt

4. **执行统计**
   - 各阶段耗时
   - Token 使用量
   - 最终 prompt 内容

## 🔧 核心概念

### 中间结果类型

#### VectorSearchResult
```python
@dataclass
class VectorSearchResult:
    query: str  # 原始查询
    query_embedding: List[float]  # 查询向量
    matched_entities: List[Dict]  # 匹配的实体信息
    similarity_scores: List[float]  # 相似度分数
    search_time: float  # 检索耗时
```

#### EntityMappingResult
```python
@dataclass
class EntityMappingResult:
    original_query: str  # 原始查询
    processed_query: str  # 处理后的查询
    selected_entities: List[Dict]  # 选中的实体
    excluded_entities: List[str]  # 被排除的实体
    included_entities: List[Dict]  # 强制包含的实体
    entity_count: int  # 最终实体数量
```

#### ContextBuildResult
```python
@dataclass
class ContextBuildResult:
    community_context: str  # 社区报告上下文
    local_context: str  # 实体关系上下文
    text_unit_context: str  # 文本单元上下文
    conversation_context: str  # 对话历史上下文
    final_context: str  # 最终整合的上下文
    context_tokens: Dict[str, int]  # 各部分token数量
    context_data: Dict[str, pd.DataFrame]  # 上下文数据
```

## 🚀 快速开始

### 1. 基本使用

```python
from app.core.enhanced_util import graphrag_stream_response_with_intermediate_results

# 在你的 FastAPI 路由中使用
@app.post("/chat/enhanced")
async def enhanced_chat(request: ChatRequest):
    user_query = request.messages[-1].content if request.messages else ""

    return graphrag_stream_response_with_intermediate_results(
        chat_id="user_session_123",
        query=user_query,
        user_message_id="msg_456",
        assistant_message_id="msg_789",
        enable_intermediate_collection=True
    )
```

### 2. 获取中间结果

```python
from app.core.graph.enhanced_query_graphrag import get_intermediate_results_summary

# 获取特定查询的中间结果摘要
summary = get_intermediate_results_summary("query_123")
print(f"查询耗时: {summary['total_time']}秒")
print(f"匹配实体数: {summary['entity_mapping']['selected_entities_count']}")
```

### 3. 列出所有结果

```python
from app.core.graph.enhanced_query_graphrag import list_all_intermediate_results

# 获取所有查询的中间结果
all_results = list_all_intermediate_results()
print(f"总查询数: {len(all_results)}")

for result in all_results:
    print(f"查询ID: {result['query_id']}, 耗时: {result['total_time']}秒")
```

## 📡 API 使用

### 主要 API 端点

#### 1. 增强聊天接口
```http
POST /api/v1/chat/enhanced
Content-Type: application/json

{
    "messages": [
        {
            "role": "user",
            "content": "什么是人工智能？"
        }
    ]
}
```

响应中会包含 `query_id`，用于后续查询中间结果。

#### 2. 获取所有中间结果
```http
GET /api/v1/intermediate-results
```

响应示例：
```json
{
    "success": true,
    "statistics": {
        "total_queries": 15,
        "average_response_time": 2.34,
        "total_entities_retrieved": 142,
        "total_context_tokens": 156789
    },
    "results": [
        {
            "query_id": "chat_123_1699876543210_abc12345",
            "timestamp": 1699876543210,
            "total_time": 2.1,
            "original_query": "什么是机器学习？",
            "vector_search": {
                "matched_entities_count": 8,
                "search_time": 0.15,
                "avg_similarity_score": 0.78
            },
            "entity_mapping": {
                "selected_entities_count": 6,
                "excluded_entities_count": 2,
                "included_entities_count": 0
            },
            "context_building": {
                "final_context_length": 2341,
                "context_tokens_total": 4567,
                "context_sections": ["community", "local", "text_unit"]
            }
        }
    ]
}
```

#### 3. 获取特定查询的详细结果
```http
GET /api/v1/intermediate-results/{query_id}
```

#### 4. 获取可视化数据
```http
GET /api/v1/intermediate-results/visualization
```

### 客户端处理示例

```javascript
// 处理包含中间结果元数据的流式响应
async function handleEnhancedChatResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let queryId = null;
    let intermediateResultsSummary = null;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));

                    // 处理消息ID（包含query_id）
                    if (data.object === 'chat.completion.message_id') {
                        queryId = data.message_id.query_id;
                        console.log('查询ID:', queryId);
                    }

                    // 处理中间结果摘要
                    if (data.object === 'chat.completion.metadata' &&
                        data.metadata.type === 'intermediate_results_summary') {
                        intermediateResultsSummary = data.metadata.summary;
                        console.log('中间结果摘要:', intermediateResultsSummary);

                        // 可以显示性能指标给用户
                        showPerformanceMetrics(intermediateResultsSummary);
                    }

                    // 处理普通响应内容
                    if (data.object === 'chat.completion.chunk' &&
                        data.choices &&
                        data.choices[0].delta.content) {
                        appendToChat(data.choices[0].delta.content);
                    }

                } catch (e) {
                    console.error('解析响应块失败:', e);
                }
            }
        }
    }
}

function showPerformanceMetrics(summary) {
    const metrics = `
        ⚡ 性能指标:
        - 总响应时间: ${summary.total_time.toFixed(2)}秒
        - 匹配实体数: ${summary.entity_mapping?.selected_entities_count || 0}
        - 上下文长度: ${summary.context_building?.final_context_length || 0}字符
        - 向量搜索耗时: ${summary.vector_search?.search_time || 0}秒
    `;

    // 在UI中显示性能指标
    const metricsElement = document.getElementById('performance-metrics');
    if (metricsElement) {
        metricsElement.textContent = metrics;
        metricsElement.style.display = 'block';
    }
}
```

## 📊 数据结构

### 完整中间结果文件结构

每个中间结果都保存为独立的 JSON 文件：

```json
{
    "query_id": "chat_123_1699876543210_abc12345",
    "timestamp": 1699876543210.0,
    "original_query": "什么是机器学习？",
    "total_time": 2.156,
    "vector_search": {
        "query": "什么是机器学习？",
        "query_embedding": [0.1, 0.2, 0.3, ...],
        "matched_entities": [
            {
                "id": "entity_123",
                "title": "机器学习",
                "description": "人工智能的一个分支",
                "rank": 1,
                "category": "technology"
            }
        ],
        "similarity_scores": [0.95, 0.87, 0.78, ...],
        "search_time": 0.156
    },
    "entity_mapping": {
        "original_query": "什么是机器学习？",
        "processed_query": "什么是机器学习？",
        "selected_entities": [
            {
                "id": "entity_123",
                "title": "机器学习",
                "description": "人工智能的一个分支",
                "rank": 1,
                "category": "technology"
            }
        ],
        "excluded_entities": [],
        "included_entities": [],
        "entity_count": 6
    },
    "context_building": {
        "community_context": "社区报告内容...",
        "local_context": "实体关系内容...",
        "text_unit_context": "文本单元内容...",
        "conversation_context": "",
        "final_context": "整合后的最终上下文...",
        "context_tokens": {
            "community": 1200,
            "local": 800,
            "text_unit": 600,
            "total": 2600
        },
        "context_data": {
            "entities": [...],
            "communities": [...],
            "text_units": [...]
        }
    },
    "llm_prompt": "最终发送给LLM的完整prompt内容..."
}
```

### 文件命名规则

- **完整结果文件**: `intermediate_results_{query_id}_{timestamp}.json`
- **摘要文件**: `intermediate_results_{query_id}_{timestamp}_summary.json`

## 📈 性能优化

### 1. 缓存策略

```python
from app.core.graph.intermediate_results import IntermediateResultsCollector

# 可以复用collector实例
collector = IntermediateResultsCollector()

# 对于相似查询，可以设置缓存
cached_results = collector.get_cached_results(query_hash)
if cached_results:
    return cached_results
```

### 2. 异步保存

中间结果保存采用异步方式，不会阻塞主响应流程：

```python
# 异步保存已实现，无需手动处理
# 结果会在后台保存，不影响用户响应时间
```

### 3. 存储优化

- 定期清理旧的结果文件
- 使用压缩存储
- 考虑使用数据库替代文件存储

### 4. 性能监控

```python
from app.core.enhanced_util import create_intermediate_results_visualization_data

# 获取性能监控数据
visualization_data = create_intermediate_results_visualization_data()

# 分析性能趋势
avg_response_time = visualization_data['statistics']['response_time']['avg']
if avg_response_time > 3.0:
    print("⚠️ 响应时间过长，建议优化")
```

## 🔍 故障排除

### 常见问题

#### 1. 中间结果文件未生成

**可能原因:**
- `enable_intermediate_collection` 设置为 `False`
- 文件权限问题
- 磁盘空间不足

**解决方案:**
```python
# 确保启用结果收集
enable_intermediate_collection=True

# 检查目录权限
import os
os.makedirs("./intermediate_results", exist_ok=True)
```

#### 2. 查询ID无法找到结果

**可能原因:**
- 查询ID格式不匹配
- 结果文件损坏
- 时间戳不匹配

**解决方案:**
```python
# 列出所有可用的查询ID
all_results = list_all_intermediate_results()
available_ids = [r['query_id'] for r in all_results]
print("可用的查询ID:", available_ids)

# 或使用部分匹配
def find_results_by_partial_id(partial_id):
    all_results = list_all_intermediate_results()
    return [r for r in all_results if partial_id in r['query_id']]
```

#### 3. 内存使用过高

**可能原因:**
- 同时处理大量查询
- 中间结果数据量过大

**解决方案:**
```python
# 限制并发收集的数量
import asyncio
semaphore = asyncio.Semaphore(5)  # 最多同时5个收集任务

async def limited_collection(query_id, query):
    async with semaphore:
        return await rag_chatbot_local_search_stream_with_results(
            query=query,
            query_id=query_id,
            collect_results=True
        )
```

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 在代码中添加调试信息
collector = IntermediateResultsCollector()
collector.start_collection(query_id, query)
# ... 执行查询
results = collector.finish_collection()

# 打印详细调试信息
print(f"收集到的结果类型: {type(results)}")
print(f"各阶段耗时: {results.total_time}")
```

## 📝 最佳实践

1. **生产环境建议:**
   - 设置合理的文件清理策略
   - 监控磁盘空间使用
   - 考虑使用数据库存储

2. **开发环境建议:**
   - 启用详细日志
   - 定期分析性能数据
   - 测试不同查询类型的效果

3. **数据分析建议:**
   - 定期分析响应时间分布
   - 识别性能瓶颈
   - 优化向量检索和上下文构建

## 🔗 相关文档

- [GraphRAG 官方文档](https://microsoft.github.io/graphrag/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [性能优化指南](./performance_optimization.md)
- [API 参考文档](./api_reference.md)

---

如有问题或建议，请联系开发团队或提交 Issue。