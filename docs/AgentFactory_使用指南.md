# AgentFactory 使用指南

## 概述

`AgentFactory` 是一个统一的机器人实例工厂类，用于替代原来的直接导入方式，提供更好的代码组织和扩展性。

## 主要特性

- **统一入口**: 通过单一工厂管理所有机器人实例
- **Key-Value 访问**: 支持字符串键名访问对应的机器人
- **工厂模式**: 使用单例模式确保工厂实例唯一性
- **向后兼容**: 保持原有导入方式仍然可用
- **语义化命名**: 提供易于理解的机器人别名
- **错误处理**: 提供安全的获取方法和友好的错误信息

## 基本使用

### 导入方式

```python
from app.core.agent import agent_factory
```

### 获取机器人实例

```python
# 方式1: 使用 get_agent 方法
bot = agent_factory.get_agent('bot')
rag_bot = agent_factory.get_agent('rag_bot')
qwen_rag_bot = agent_factory.get_agent('qwen_rag_bot')

# 方式2: 使用字典式访问
bot = agent_factory['bot']
rag_bot = agent_factory['rag_bot']
qwen_rag_bot = agent_factory['qwen_rag_bot']

# 方式3: 使用语义化别名
medical_agent = agent_factory['medical_agent']  # 同 bot
assistant = agent_factory['assistant']          # 同 rag_bot
qwen_agent = agent_factory['qwen_agent']      # 同 qwen_rag_bot
```

## 可用机器人列表

| 键名 | 机器人类型 | 描述 |
|------|------------|------|
| `bot` | ReActChat | 主要的医保政务服务助手 |
| `rag_bot` | Assistant | 基础对话助手 |
| `qwen_rag_bot` | QwenRagAssistant | RAG增强助手 |
| `medical_agent` | ReActChat | 医保专用助手（别名） |
| `assistant` | Assistant | 通用助手（别名） |
| `qwen_agent` | QwenRagAssistant | Qwen版助手（别名） |
| `main` | ReActChat | 主要助手（别名） |
| `default` | ReActChat | 默认助手（别名） |
| `primary` | ReActChat | 首要助手（别名） |

## 高级功能

### 安全获取机器人

```python
# 如果机器人不存在，返回指定的默认机器人
agent = agent_factory.get_agent_safe('unknown_agent', 'bot')
```

### 查看可用机器人

```python
# 获取所有可用机器人键名
agents = agent_factory.list_agents()
print(agents)

# 获取机器人详细信息
info = agent_factory.get_agent_info('bot')
print(info)
```

### 检查机器人是否存在

```python
if 'bot' in agent_factory:
    bot = agent_factory['bot']
```

### 错误处理

```python
try:
    agent = agent_factory.get_agent('nonexistent')
except KeyError as e:
    print(f"错误: {e}")
    # 输出: 错误: 机器人 'nonexistent' 不存在。可用的机器人: ['bot', 'rag_bot', ...]
```

## 与原有方式的对比

### 原有方式（仍然支持）

```python
from app.core.agent import bot, rag_bot, qwen_rag_bot

# 直接使用
response = bot.answer("医保报销流程是什么？")
```

### 新的统一方式

```python
from app.core.agent import agent_factory

# 通过工厂获取
bot = agent_factory.get_agent('bot')
response = bot.answer("医保报销流程是什么？")

# 或者更灵活的方式
def get_response(query: str, agent_type: str = 'bot'):
    agent = agent_factory.get_agent(agent_type)
    return agent.answer(query)

response = get_response("医保报销流程是什么？", 'medical_agent')
```

## 优势

1. **代码清晰**: 通过语义化键名，代码更容易理解
2. **易于扩展**: 添加新机器人只需在工厂中注册
3. **类型安全**: 支持 IDE 的自动补全和类型检查
4. **灵活配置**: 可以根据需要动态选择机器人
5. **统一管理**: 所有机器人在一个地方管理，便于维护

## 实际应用场景

### 根据用户类型选择机器人

```python
def get_assistant_for_user(user_role: str):
    """根据用户角色选择合适的助手"""
    role_mapping = {
        'medical_staff': 'bot',
        'general_user': 'assistant',
        'researcher': 'qwen_agent'
    }

    agent_type = role_mapping.get(user_role, 'default')
    return agent_factory.get_agent(agent_type)
```

### 动态机器人选择

```python
def process_query(query: str):
    """根据查询内容动态选择机器人"""
    if '医保' in query or '医疗' in query:
        agent = agent_factory.get_agent('medical_agent')
    elif len(query.split()) > 10:  # 长查询使用RAG
        agent = agent_factory.get_agent('qwen_agent')
    else:
        agent = agent_factory.get_agent('assistant')

    return agent.process(query)
```

## 迁移指南

### 现有代码迁移

1. **替换导入**:
   ```python
   # 旧方式
   from app.core.agent import bot, rag_bot, qwen_rag_bot

   # 新方式
   from app.core.agent import agent_factory
   ```

2. **替换使用**:
   ```python
   # 旧方式
   response = bot.answer(query)

   # 新方式
   bot = agent_factory.get_agent('bot')
   response = bot.answer(query)
   ```

### 渐进式迁移

- 新的 `AgentFactory` 与原有方式完全兼容
- 可以逐步迁移现有代码，无需一次性全部修改
- 建议新代码优先使用 `AgentFactory`

## 注意事项

1. `AgentFactory` 使用单例模式，全局只有一个实例
2. 所有机器人在工厂初始化时就已创建，不是延迟加载
3. 键名区分大小写
4. 不存在的键名会抛出 `KeyError` 异常，建议使用 `get_agent_safe` 进行安全获取

## 示例代码

完整的使用示例请参考 `examples/agent_factory_usage.py` 文件。