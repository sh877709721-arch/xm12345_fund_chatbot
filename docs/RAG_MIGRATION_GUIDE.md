# RAG 模块迁移指南

## 🎯 新的目录结构

重构后的RAG功能已全部迁移到 `app/core/rag/` 目录下：

```
app/core/
├── rag/                          # RAG功能统一目录
│   ├── __init__.py              # 统一出口和新接口
│   ├── query_service.py         # 查询处理服务
│   ├── search_service.py        # 搜索服务
│   ├── database_operations.py   # 数据库操作
│   ├── scoring_algorithms.py    # 评分算法
│   ├── performance_utils.py     # 性能优化工具
│   └── vector_wrapper.py        # 兼容性包装层
├── rag_api.py                   # 兼容性入口
└── vector.py                    # 原始文件（保持不变）
```

## 🔄 使用方式对比

### 1. 新推荐用法（通过统一入口）

```python
# 高级RAG引擎 - 推荐用法
from app.core.rag import RAGEngine

engine = RAGEngine(
    default_search_type="doc",
    enable_rerank=True,
    enable_fallback=True
)

# 统一搜索接口
results = engine.search("查询内容", search_type="hybrid", top_k=10)
stats = engine.get_stats()
suggestions = engine.get_search_suggestions()

# 便捷函数
from app.core.rag import quick_search, qa_search, doc_search

results = quick_search("查询内容", search_type="doc", top_k=5)
qa_results = qa_search("问题内容")
doc_results = doc_search("文档内容", use_rerank=True)
```

### 2. 原始接口兼容（零修改迁移）

```python
# 方式一：通过RAG API入口（推荐用于现有代码）
from app.core.rag_api import *
# 或（等效的）
from app.core.rag import *

# 所有原始函数调用保持不变
results = doc_hybrid_search_vec_rff("查询")
rewritten = query_rewrite_with_chat_client("查询")
qa_results = qa_response("问题")

# 方式二：直接使用原始接口（保持不变）
from app.core import vector
results = vector.doc_hybrid_search_vec_rff("查询")
```

### 3. 模块化用法（适合新开发）

```python
# 使用具体的服务类
from app.core.rag import SearchService, QueryService, ScoringAlgorithms

# 直接调用服务方法
results = SearchService.doc_hybrid_search_vec_rff_with_rerank("查询", top_k=10)
rewritten_queries = QueryService.rewrite_query_with_chat_client("查询")
bm25_score = ScoringAlgorithms.calculate_bm25_score(5, 100, 80)
```

## 📋 接口对照表

### 原始接口 → 新接口

| 原始函数 | 新接口调用方式 | 说明 |
|---------|---------------|------|
| `vector.doc_hybrid_search_vec_rff(query)` | `from app.core.rag import doc_search<br>doc_search(query)` | 更简洁的接口 |
| `vector.qa_response(query)` | `from app.core.rag import qa_search<br>qa_search(query)` | 更语义化的命名 |
| `vector.doc_hybrid_search_vec_rff_with_rerank(query, top_n)` | `doc_search(query, top_k=top_n, use_rerank=True)` | 参数更清晰 |
| | `from app.core.rag import RAGEngine<br>RAGEngine().search(query, "doc", top_k)` | 统一搜索接口 |
| `vector.query_rewrite_with_chat_client(query)` | `from app.core.rag import QueryService<br>QueryService.rewrite_query_with_chat_client(query)` | 更明确的服务归属 |

## 🛠️ 迁移步骤

### 阶段一：零修改迁移（推荐用于生产环境）

```python
# 只需要修改导入语句
# 原来：
# from app.core import vector

# 改为：
from app.core.rag_api import *  # 或 from app.core.rag import *

# 其他所有代码保持不变
results = doc_hybrid_search_vec_rff("查询")
```

### 阶段二：逐步迁移到新接口

```python
# 逐步使用新的更简洁的接口
from app.core.rag import quick_search, qa_search, doc_search

# 替换原有调用
# 原来：results = doc_hybrid_search_vec_rff_with_rerank(query, 10)
# 改为：results = doc_search(query, top_k=10)
```

### 阶段三：完全使用新架构

```python
# 使用高级RAG引擎
from app.core.rag import RAGEngine

engine = RAGEngine(default_search_type="hybrid")
results = engine.search(query)
stats = engine.get_stats()
```

## 🎨 新功能特性

### 1. 高级RAG引擎

```python
from app.core.rag import RAGEngine

# 可配置的RAG引擎
engine = RAGEngine(
    default_search_type="hybrid",  # 默认搜索类型
    enable_rerank=True,            # 启用重排序
    enable_fallback=True           # 启用容错机制
)

# 支持多种搜索类型
results = engine.search(query, search_type="qa")      # QA搜索
results = engine.search(query, search_type="doc")     # 文档搜索
results = engine.search(query, search_type="hybrid")  # 混合搜索
results = engine.search(query, search_type="bm25")    # BM25搜索
results = engine.search(query, search_type="vector")  # 向量搜索

# 获取系统统计和优化建议
stats = engine.get_stats()
suggestions = engine.get_search_suggestions()
```

### 2. 配置化的搜索策略

```python
from app.core.rag import SearchConfig

# 使用预定义配置
config = SearchConfig.DOC_SEARCH_CONFIG
custom_config = config.copy()
custom_config["rrf"]["weight_bm25"] = 0.3
custom_config["rrf"]["weight_vec"] = 0.7
```

### 3. 性能优化工具

```python
from app.core.rag import PerformanceOptimizer

# 获取索引创建建议
PerformanceOptimizer.create_indexes()

# 获取缓存优化建议
PerformanceOptimizer.cache_optimization()

# 获取性能优化建议
PerformanceOptimizer.get_search_tips()
```

## 🔧 开发者工具

### 1. 统一的错误处理和日志

所有新模块都包含：
- 统一的异常处理机制
- 结构化的日志记录
- 详细的错误信息

### 2. 类型提示和文档

```python
from typing import List, Dict, Optional

def search(query: str,
           search_type: Optional[str] = None,
           top_k: int = 10,
           **kwargs) -> List[Dict]:
    """
    统一搜索接口

    Args:
        query: 查询文本
        search_type: 搜索类型 ('qa', 'doc', 'hybrid', 'bm25', 'vector')
        top_k: 返回结果数量
        **kwargs: 其他搜索参数

    Returns:
        搜索结果列表

    Raises:
        ValueError: 当搜索类型不支持时
    """
```

### 3. 测试友好设计

```python
# 易于模拟和测试
from unittest.mock import Mock

# 模拟搜索服务
mock_search_service = Mock(spec=SearchService)
mock_search_service.doc_hybrid_search_vec_rff.return_value = mock_results
```

## 📈 性能提升

### 1. 并行搜索优化

```python
# 自动使用并行搜索
with ThreadPoolExecutor(max_workers=2) as executor:
    bm25_future = executor.submit(bm25_search, query)
    vec_future = executor.submit(vector_search, query)
    # 并行执行，显著减少总搜索时间
```

### 2. 智能缓存策略

- 嵌入向量缓存
- 搜索结果缓存
- 统计信息缓存

### 3. 数据库优化

- 预编译的SQL语句
- 连接池管理
- 索引优化建议

## 🚀 最佳实践

### 1. 推荐的导入方式

```python
# 新项目推荐
from app.core.rag import RAGEngine, quick_search

# 现有项目迁移
from app.core.rag_api import *  # 或 from app.core.rag import *
```

### 2. 配置管理

```python
# 使用环境变量或配置文件管理搜索参数
import os

DEFAULT_SEARCH_TYPE = os.getenv("RAG_SEARCH_TYPE", "hybrid")
ENABLE_RERANK = os.getenv("RAG_ENABLE_RERANK", "true").lower() == "true"

engine = RAGEngine(
    default_search_type=DEFAULT_SEARCH_TYPE,
    enable_rerank=ENABLE_RERANK
)
```

### 3. 错误处理

```python
try:
    results = engine.search(query)
    return results
except ValueError as e:
    logger.error(f"搜索类型错误: {e}")
    return []
except Exception as e:
    logger.error(f"搜索失败: {e}")
    # 降级到简单搜索
    return quick_search(query, "basic")
```

## 📝 总结

这次重构提供了：

1. **完全的向后兼容性** - 现有代码可以零修改迁移
2. **清晰的模块化架构** - 职责分离，便于维护和扩展
3. **统一的高级接口** - `RAGEngine` 提供简单易用的统一API
4. **丰富的配置选项** - 支持灵活的搜索策略配置
5. **完整的开发工具** - 类型提示、文档、测试友好设计

通过新的 `app.core.rag` 统一入口，您可以：
- 保持现有代码不变
- 逐步迁移到新接口
- 使用更强大的高级功能
- 享受更好的性能和维护性