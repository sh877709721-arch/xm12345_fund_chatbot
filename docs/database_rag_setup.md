# 数据库RAG助手设置指南

本文档介绍如何设置和使用基于数据库检索的RAG助手。

## 概述

DatabaseAssistant是一个基于数据库检索的智能问答助手，支持以下功能：

- **多数据库支持**: MySQL、PostgreSQL、MongoDB
- **全文检索**: 支持中英文全文搜索
- **关键词匹配**: 智能关键词提取和匹配
- **连接缓存**: 数据库连接池和缓存机制
- **健康检查**: 自动监控数据库连接状态
- **配置灵活**: 支持多种配置方式

## 快速开始

### 1. 安装依赖

根据使用的数据库类型安装相应依赖：

```bash
# MySQL支持
pip install mysql-connector-python

# PostgreSQL支持
pip install psycopg2-binary

# MongoDB支持
pip install pymongo

# 或者一次性安装所有依赖
pip install mysql-connector-python psycopg2-binary pymongo
```

### 2. 数据库准备

#### MySQL

创建数据库和表：

```sql
-- 创建数据库
CREATE DATABASE medical_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE medical_db;

-- 创建文档表
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 全文索引
    FULLTEXT INDEX ft_content (content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入示例数据
INSERT INTO documents (title, content, category) VALUES
('医保报销比例', '厦门市医保政策规定，参保人员可以享受门诊和住院医疗费用报销待遇。门诊报销比例为70%，住院报销比例为85%。', '医保政策'),
('异地就医备案', '参保人员在异地就医前，需要办理异地就医备案手续。可以通过线上平台或医保经办机构办理，备案后可直接结算。', '异地就医'),
('个人账户使用', '医保个人账户资金可以用于支付门诊费用、住院费用自付部分、在定点零售药店购买符合规定的药品等。', '个人账户');
```

#### PostgreSQL

```sql
-- 创建数据库
CREATE DATABASE medical_db;

-- 连接到数据库
\c medical_db;

-- 创建文档表
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建全文搜索配置
CREATE TEXT SEARCH CONFIGURATION chinese (COPY = simple);

-- 创建用于全文搜索的列和索引
ALTER TABLE documents ADD COLUMN search_vector tsvector;
CREATE INDEX idx_documents_search ON documents USING GIN (search_vector);

-- 创建触发器自动更新search_vector
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('chinese', COALESCE(NEW.content, '') || ' ' || COALESCE(NEW.title, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_search_vector_trigger
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- 插入示例数据
INSERT INTO documents (title, content, category) VALUES
('医保报销比例', '厦门市医保政策规定，参保人员可以享受门诊和住院医疗费用报销待遇。门诊报销比例为70%，住院报销比例为85%。', '医保政策'),
('异地就医备案', '参保人员在异地就医前，需要办理异地就医备案手续。可以通过线上平台或医保经办机构办理，备案后可直接结算。', '异地就医');
```

#### MongoDB

```javascript
// 连接到MongoDB
use medical_db;

// 插入示例文档
db.documents.insertMany([
    {
        title: "医保报销比例",
        content: "厦门市医保政策规定，参保人员可以享受门诊和住院医疗费用报销待遇。门诊报销比例为70%，住院报销比例为85%。",
        category: "医保政策",
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        title: "异地就医备案",
        content: "参保人员在异地就医前，需要办理异地就医备案手续。可以通过线上平台或医保经办机构办理，备案后可直接结算。",
        category: "异地就医",
        created_at: new Date(),
        updated_at: new Date()
    }
]);

// 创建文本索引用于全文搜索
db.documents.createIndex({
    title: "text",
    content: "text"
}, {
    weights: {
        title: 10,
        content: 1
    },
    name: "content_title_text"
});

// 创建时间索引用于排序
db.documents.createIndex({
    created_at: -1
});
```

### 3. 基本使用

```python
from app.core.database import DatabaseAssistant
from qwen_agent.llm.schema import Message

# 配置数据库连接
db_config = {
    'type': 'mysql',
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'medical_db',
    'table': 'documents'
}

# 创建数据库助手
assistant = DatabaseAssistant(
    llm={'model': 'qwen-plus-latest'},
    name='医保查询助手',
    description='基于MySQL数据库的医保政策查询助手',
    db_config=db_config
)

# 进行查询
messages = [Message(role='user', content='请问医保报销比例是多少？')]

# 获取响应
responses = list(assistant._run(messages, lang='zh'))
for response_batch in responses:
    for message in response_batch:
        if message.role == 'assistant':
            print(f"助手回复: {message.content}")
```

## 配置说明

### 数据库配置

#### MySQL配置

```python
mysql_config = {
    'type': 'mysql',
    'host': 'localhost',        # 数据库主机地址
    'port': 3306,              # 端口号
    'user': 'username',        # 用户名
    'password': 'password',    # 密码
    'database': 'db_name',     # 数据库名
    'table': 'documents',      # 表名
    'content_field': 'content',    # 内容字段名
    'title_field': 'title',        # 标题字段名
    'id_field': 'id',             # ID字段名
    'timestamp_field': 'created_at'  # 时间戳字段名
}
```

#### PostgreSQL配置

```python
postgresql_config = {
    'type': 'postgresql',
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'password',
    'database': 'db_name',
    'table': 'documents',
    'content_field': 'content',
    'title_field': 'title',
    'id_field': 'id',
    'timestamp_field': 'created_at'
}
```

#### MongoDB配置

```python
mongodb_config = {
    'type': 'mongodb',
    'host': 'localhost',
    'port': 27017,
    'database': 'medical_db',
    'collection': 'documents',
    'username': '',  # 可选
    'password': '',  # 可选
    'auth_source': 'admin'  # 可选
}
```

### RAG配置

```python
rag_cfg = {
    'max_ref_token': 4000,  # 最大引用token数量
    'rag_keygen_strategy': 'SplitQueryThenGenKeyword',  # 关键词生成策略
    'rag_searchers': ['database_retrieval']  # 检索工具列表
}
```

### 环境变量配置

可以通过环境变量配置数据库连接：

```bash
# MySQL环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=username
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=db_name
export MYSQL_TABLE=documents

# PostgreSQL环境变量
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_DATABASE=db_name

# MongoDB环境变量
export MONGODB_HOST=localhost
export MONGODB_PORT=27017
export MONGODB_DATABASE=db_name
export MONGODB_COLLECTION=documents
```

使用环境变量配置：

```python
from app.core.database.config import load_config_from_env

# 从环境变量加载配置
db_config = load_config_from_env('mysql')

# 创建助手
assistant = DatabaseAssistant(db_config=db_config)
```

## 高级功能

### 1. 关键词增强搜索

```python
messages = [Message(role='user', content='查询医保相关信息')]

# 使用额外的关键词增强搜索
responses = list(assistant._run(
    messages=messages,
    keywords=['医保', '报销', '比例'],
    limit=10
))
```

### 2. 过滤条件

```python
# 使用过滤条件
responses = list(assistant._run(
    messages=messages,
    filters={
        'category': '医保政策',
        'created_at': {'$gte': '2024-01-01'}  # MongoDB格式
    }
))
```

### 3. OpenAI格式响应

```python
# 获取OpenAI格式的流式响应
for chunk in assistant._run_openai_format(messages, lang='zh'):
    print(chunk, end='')
```

### 4. 健康检查

```python
# 检查助手健康状态
health_info = assistant.health_check()
print(health_info)

# 检查数据库连接
db_connection = assistant.db_memory.function_map['database_retrieval']._get_db_connection(db_config)
is_healthy = db_connection.health_check()
```

### 5. 连接缓存管理

```python
# 获取缓存信息
cache_info = assistant.db_memory.function_map['database_retrieval'].get_cache_info()
print(cache_info)

# 清除缓存
assistant.clear_cache()
```

## Web UI集成

```python
from qwen_agent.gui.web_ui import WebUI

# 创建助手
assistant = create_mysql_assistant()

# Web UI配置
chatbot_config = {
    'prompt.suggestions': [
        {'text': '查询医保报销比例'},
        {'text': '异地就医备案流程'},
        {'text': '个人账户使用规则'}
    ]
}

# 启动Web UI
web_ui = WebUI(assistant, chatbot_config=chatbot_config)
web_ui.run()
```

## 性能优化建议

### 1. 数据库索引

- **MySQL**: 创建全文索引 `FULLTEXT INDEX`
- **PostgreSQL**: 创建GIN索引 `to_tsvector`
- **MongoDB**: 创建文本索引 `{title: "text", content: "text"}`

### 2. 连接池配置

```python
# MySQL连接池配置
db_config = {
    # ... 其他配置
    'pool_size': 10,
    'max_overflow': 20
}
```

### 3. 查询限制

- 设置合理的 `limit` 参数，避免返回过多结果
- 使用时间范围等过滤条件缩小搜索范围
- 定期清理过期数据

### 4. 缓存策略

- 启用数据库连接缓存
- 考虑添加Redis缓存层缓存查询结果
- 设置合适的缓存过期时间

## 故障排除

### 常见问题

1. **连接失败**
   - 检查数据库服务是否运行
   - 验证连接参数是否正确
   - 确认网络连接是否正常

2. **检索结果为空**
   - 检查表名和字段名是否正确
   - 确认数据库中是否有数据
   - 验证全文索引是否创建

3. **性能问题**
   - 检查数据库索引
   - 优化查询条件
   - 考虑数据分片

4. **编码问题**
   - 确保数据库使用UTF-8编码
   - 检查连接字符串中的charset设置

### 日志调试

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或者只设置特定模块的日志
logger = logging.getLogger('app.core.database')
logger.setLevel(logging.DEBUG)
```

## 扩展开发

### 自定义数据库连接器

```python
from app.core.database.connectors.base import DatabaseInterface

class CustomDBConnection(DatabaseInterface):
    def _connect(self):
        # 实现自定义连接逻辑
        pass

    def search_records(self, query, keywords=None, limit=10):
        # 实现自定义搜索逻辑
        pass

# 注册自定义连接器
# 在 retrieval.py 中添加相应的创建逻辑
```

### 自定义检索策略

```python
from app.core.database.retrieval import DatabaseRetrieval

class CustomRetrieval(DatabaseRetrieval):
    def _parse_query(self, query, extra_keywords):
        # 实现自定义查询解析逻辑
        pass
```

## 总结

DatabaseAssistant提供了一个强大而灵活的数据库检索RAG解决方案，支持多种数据库类型和高级搜索功能。通过合理配置和优化，可以构建高效的智能问答系统。