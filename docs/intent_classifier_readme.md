# RAG意图分类器

基于RAG（检索增强生成）和OpenAI API的智能意图分类器，专门用于医保政策领域的用户查询意图识别。

## 功能特性

### 🎯 核心功能
- **RAG增强分类**：结合向量检索和文本搜索提供分类上下文
- **多级分类体系**：支持三级分类结构（主类别→子类别→详细类别）
- **智能提示词**：基于搜索结果动态构建分类提示词
- **置信度评估**：提供分类置信度和推理过程

### 🚀 高级功能
- **集成分类**：多策略投票机制提高分类准确性
- **参数优化**：自动搜索最优分类参数组合
- **批量处理**：支持批量查询分类和统计分析
- **错误处理**：完善的异常处理和降级策略

## 类别体系

### 职工基本医疗保险
- **参保缴费**：参保对象、缴费标准、参保缴费方式、参保缴费纠纷处理、重复参保处理、退费
- **医疗待遇**：待遇生效时间、连续参保机制、医保账户划拨、大病医保、医疗救助、待遇标准、就医使用
- **办事指南**：转移接续手续办理、医疗费用报销办理、异地就医备案办理、家庭共济办理、医保退休办理、个人账户一次性支取办理

### 城乡居民医疗保险
- **参保缴费**：参保对象、缴费标准、参保缴费方式、重复参保、退费
- **医疗待遇**：待遇生效时间、参保长效机制、医保账户划拨、大病医保、医疗救助、待遇标准、就医使用
- **办事指南**：医疗费用报销办理、异地就医备案办理、家庭共济办理、转移接续手续办理

### 生育保险
- **参保缴费**：参保对象、缴费标准、参保缴费方式、参保缴费纠纷处理
- **生育待遇**：生育津贴待遇、男职工未就业配偶生育医疗费用待遇、其他待遇
- **办事指南**：生育津贴办理、男职工未就业配偶生育医疗费用办理

### 其他医药政策
- **药品（含项目、耗材）政策**：药品目录、医疗服务项目目录、医用耗材目录
- **DRG收费及按病种收费政策**：厦门市定点医疗机构就医、省内异地定点医疗机构就医
- **辅助生殖政策**：福建省辅助生殖类医疗服务价格项目及省属公立医院项目价格表、辅助生殖医保支付政策
- **补充医疗保险**：惠厦保
- **长期护理险政策**：未分类

## 快速开始

### 基本使用

```python
from app.core.agents.bot_intent import IntentClassifier

# 创建分类器实例
classifier = IntentClassifier()

# 单个查询分类
query = "我想了解职工医保的参保条件"
result = classifier.classify_intent(query)

print(f"主分类: {result['main_category']}")
print(f"子分类: {result['sub_category']}")
print(f"详细分类: {result['detail_category']}")
print(f"置信度: {result['confidence']}")
print(f"推理原因: {result['reason']}")
```

### 使用兼容接口

```python
from app.core.agents.bot_intent import BotIntent

# 兼容旧版本接口
bot_intent = BotIntent()
result = bot_intent.classify("生育津贴怎么申请？")
```

### 批量分类

```python
queries = [
    "职工医保退费流程",
    "异地就医怎么备案？",
    "生育保险缴费方式"
]

results = classifier.batch_classify(queries)

# 统计分析
stats = classifier.get_category_stats(results)
print(stats)
```

## 高级功能

### 集成分类

```python
from app.core.agents.intent_optimizer import IntentOptimizer

optimizer = IntentOptimizer()

# 使用多种策略进行集成分类
result = optimizer.ensemble_classification(
    query="我想了解医保报销比例",
    strategies=['conservative', 'balanced', 'aggressive']
)

print(f"集成分类结果: {result}")
print(f"投票数: {result['vote_count']}/{result['total_votes']}")
```

### 参数优化

```python
# 准备测试数据
test_queries = ["查询1", "查询2", "查询3"]
expected_results = [
    {"main_category": "职工基本医疗保险", "sub_category": "参保缴费"},
    # ...
]

# 自动优化参数
best_params = optimizer.optimize_search_weights(test_queries, expected_results)
print(f"最优参数: {best_params}")
```

### 置信度分析

```python
# 分析分类置信度的详细信息
analysis = optimizer.analyze_classification_confidence("医保报销比例是多少？")
print(f"一致性分数: {analysis['consistency_score']}")
print(f"是否可靠: {analysis['is_reliable']}")
```

## 配置选项

### ClassificationConfig 参数

```python
from app.core.agents.intent_optimizer import ClassificationConfig

config = ClassificationConfig(
    model_name="gpt-3.5-turbo",      # 使用的模型
    temperature=0.1,                 # 温度参数，控制随机性
    max_tokens=500,                  # 最大生成token数
    vector_weight=0.6,               # 向量搜索权重
    bm25_weight=0.4,                 # BM25搜索权重
    similarity_threshold=0.6,        # 相似度阈值
    top_k=5,                         # 返回结果数量
    use_rerank=True,                 # 是否使用rerank
    confidence_threshold=0.7         # 置信度阈值
)
```

## API响应格式

```json
{
    "main_category": "职工基本医疗保险",
    "sub_category": "参保缴费",
    "detail_category": "参保对象",
    "confidence": 0.95,
    "reason": "用户询问的是职工基本医疗保险的参保对象问题，关键词匹配度高",
    "search_results_count": 5,
    "search_context": [
        {
            "question": "问题文本",
            "answer": "答案文本",
            "similarity_score": 0.88
        }
    ],
    "ensemble_strategies": ["conservative", "balanced"],
    "vote_count": 2,
    "total_votes": 3
}
```

## 错误处理

系统提供了完善的错误处理机制：

1. **JSON解析错误**：当LLM返回非JSON格式时，返回默认结构
2. **API调用错误**：当OpenAI API不可用时，降级到基础分类
3. **搜索错误**：当RAG搜索失败时，使用纯LLM分类
4. **空查询处理**：对空或无意义查询进行特殊处理

## 性能优化建议

### 搜索参数调优
- 对于长查询，提高 `similarity_threshold` 到 0.7-0.8
- 对于短查询，降低 `vector_weight` 到 0.5，提高 `bm25_weight`
- 根据数据集大小调整 `top_k` 参数

### 缓存策略
```python
# 可以添加缓存层减少重复计算
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_classify(query_hash: str):
    return classifier.classify_intent(query)
```

### 并行处理
```python
from concurrent.futures import ThreadPoolExecutor

def parallel_classify(queries: List[str]):
    with ThreadPoolExecutor(max_workers=4) as executor:
        return list(executor.map(classifier.classify_intent, queries))
```

## 测试

运行单元测试：
```bash
cd d:\dev\ai_app
python -m pytest tests/test_intent_classifier.py -v
```

运行示例代码：
```bash
python examples/intent_classifier_example.py
```

## 依赖关系

- `openai`: OpenAI API客户端
- `sqlalchemy`: 数据库操作
- `numpy`: 数值计算
- `pydantic`: 数据验证（可选）
- `logging`: 日志记录

## 注意事项

1. **API配额**：注意OpenAI API的调用频率限制
2. **数据质量**：RAG搜索效果依赖于知识库的数据质量
3. **语言支持**：当前主要针对中文查询优化
4. **更新维护**：类别体系需要根据业务变化定期更新

## 扩展开发

### 添加新的类别

```python
# 在IntentClassifier类中更新intent_categories
self.intent_categories["新类别"] = {
    "子类别1": ["详细类别1", "详细类别2"],
    "子类别2": ["详细类别3"]
}
```

### 自定义分类逻辑

```python
class CustomIntentClassifier(IntentClassifier):
    def custom_preprocessing(self, query: str) -> str:
        # 自定义查询预处理
        return processed_query

    def custom_postprocessing(self, result: Dict) -> Dict:
        # 自定义结果后处理
        return enhanced_result
```

## 联系方式

如有问题或建议，请联系开发团队。