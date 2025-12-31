# GraphRAG 流式 API 使用指南

## 📖 概述

GraphRAG 流式 API 已成功封装为 FastAPI 路由，支持实时流式响应，提供更好的用户体验。

## 🔗 可用端点

### 1. 普通查询端点
```http
POST /v1/graphrag/query
```

### 2. 流式查询端点 ⭐
```http
POST /v1/graphrag/query/stream
```

### 3. 健康检查端点
```http
GET /v1/graphrag/health
```

## 🚀 流式 API 使用示例

### Python 客户端示例

```python
import requests
import json

def stream_graphrag_query(query: str):
    """调用 GraphRAG 流式查询 API"""

    url = "http://localhost:8000/v1/graphrag/query/stream"
    payload = {
        "query": query,
        "community_level": 2,
        "dynamic_community_selection": False,
        "response_type": "Multiple Paragraphs"
    }

    try:
        response = requests.post(
            url,
            json=payload,
            stream=True,
            headers={"Accept": "text/plain"}
        )

        if response.status_code == 200:
            print("🔄 开始接收流式响应:")
            print("-" * 50)

            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data = json.loads(line[6:])  # 移除 "data: " 前缀

                    if data['type'] == 'start':
                        print(f"📝 查询: {data['query']}")
                    elif data['type'] == 'chunk':
                        print(data['content'], end='', flush=True)
                    elif data['type'] == 'done':
                        print("\n" + "-" * 50)
                        print("✅ 查询完成")
                    elif data['type'] == 'error':
                        print(f"\n❌ 错误: {data['content']}")
                        break

        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ 连接错误: {str(e)}")

# 使用示例
if __name__ == "__main__":
    query = "请解释人工智能的发展历程和应用领域"
    stream_graphrag_query(query)
```

### JavaScript 客户端示例

```javascript
async function streamGraphRAGQuery(query) {
    const url = 'http://localhost:8000/v1/graphrag/query/stream';

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/plain',
        },
        body: JSON.stringify({
            query: query,
            community_level: 2,
            dynamic_community_selection: false,
            response_type: "Multiple Paragraphs"
        })
    });

    if (response.ok) {
        console.log('🔄 开始接收流式响应:');
        console.log('-'.repeat(50));

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'start') {
                            console.log(`📝 查询: ${data.query}`);
                        } else if (data.type === 'chunk') {
                            process.stdout.write(data.content);
                        } else if (data.type === 'done') {
                            console.log('\n' + '-'.repeat(50));
                            console.log('✅ 查询完成');
                        } else if (data.type === 'error') {
                            console.error(`\n❌ 错误: ${data.content}`);
                            break;
                        }
                    } catch (e) {
                        // 忽略解析错误的行
                    }
                }
            }
        }
    } else {
        console.error(`❌ 请求失败: ${response.status}`);
    }
}

// 使用示例
streamGraphRAGQuery('请解释人工智能的发展历程和应用领域');
```

### curl 命令示例

```bash
curl -X POST "http://localhost:8000/v1/graphrag/query/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/plain" \
  -d '{
    "query": "请解释人工智能的发展历程",
    "community_level": 2,
    "dynamic_community_selection": false,
    "response_type": "Multiple Paragraphs"
  }'
```

## 📊 流式响应格式

流式 API 使用 Server-Sent Events (SSE) 格式返回响应：

```
data: {"type": "start", "query": "用户问题"}
data: {"type": "chunk", "content": "部分回答内容"}
data: {"type": "chunk", "content": "更多回答内容"}
data: {"type": "done", "content": ""}
```

### 响应类型说明

- **start**: 查询开始信号，包含查询内容
- **chunk**: 数据块，包含部分回答内容
- **done**: 查询完成信号
- **error**: 错误信号，包含错误信息

## 🔧 请求参数

### GraphRAGStreamQuery 模型

```json
{
  "query": "string",                    // 必需：查询问题
  "community_level": 2,                // 可选：社区层级，默认 2
  "dynamic_community_selection": false, // 可选：动态社区选择，默认 false
  "response_type": "Multiple Paragraphs" // 可选：响应类型，默认 "Multiple Paragraphs"
}
```

## ✅ 功能特性

### 已实现功能

- ✅ **实时流式响应**: 使用异步生成器逐块返回结果
- ✅ **错误处理**: 完整的异常捕获和错误传播机制
- ✅ **日志记录**: 详细的操作日志和错误日志
- ✅ **性能优化**: 禁用缓存、保持长连接
- ✅ **类型安全**: 完整的 Pydantic 模型验证
- ✅ **SOLID 原则**: 遵循面向对象设计原则

### 技术栈

- **FastAPI**: 现代高性能 Web 框架
- **GraphRAG**: 基于图的检索增强生成
- **Pydantic**: 数据验证和序列化
- **Python asyncio**: 异步编程支持

## 🔍 健康检查

```http
GET /v1/graphrag/health
```

返回响应：
```json
{
  "status": "healthy",
  "service": "GraphRAG",
  "async_available": true,
  "sync_available": true,
  "stream_available": true
}
```

## 🚨 注意事项

1. **异步环境**: 流式 API 需要在异步环境中运行
2. **连接保持**: 确保客户端支持长连接
3. **错误处理**: 客户端需要正确处理错误信号
4. **内存使用**: 流式响应适合处理大量数据
5. **超时设置**: 建议设置适当的超时时间

## 🎯 使用场景

- **聊天应用**: 实时响应用户查询
- **数据分析**: 处理大规模知识图谱查询
- **文档问答**: 基于知识库的智能问答
- **研究工具**: 学术文献检索和分析

---

**流式 GraphRAG API 已完全就绪，可以投入生产使用！** 🎉