# AI Chat Service 启动指南

## 📋 前置要求

- Python 3.9+
- Redis (可选，用于分布式限流)
- PostgreSQL with pgvector
- Docker & Docker Compose (推荐)

## 🚀 启动方式

### 方式一：共享内存限流（推荐用于单机）

适用于单机部署，无需Redis依赖。

#### 1. 直接启动（开发环境）
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（8 workers）
gunicorn main_multi_worker:app \
  -w 8 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

#### 2. Docker启动
```bash
# 构建镜像
docker build -t ai-chat-service:latest .

# 启动容器（共享内存模式）
docker run -d \
  --name ai-chat \
  -p 8000:8000 \
  -e USE_REDIS_RATE_LIMIT=false \
  ai-chat-service:latest

# 或使用 docker-compose
docker-compose -f docker-compose.shared-memory.yml up -d
```

### 方式二：Redis分布式限流（推荐用于生产环境）

适用于生产环境，支持多实例部署。

#### 1. 启动Redis
```bash
# 使用Docker启动Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes

# 或使用现有的Redis服务
```

#### 2. 启动应用
```bash
# 设置环境变量
export REDIS_URL="redis://localhost:6379"
export USE_REDIS_RATE_LIMIT="true"

# 启动服务（8 workers）
gunicorn main_multi_worker:app \
  -w 8 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --env REDIS_URL="redis://localhost:6379" \
  --env USE_REDIS_RATE_LIMIT="true" \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

#### 3. Docker Compose启动（推荐）
```bash
# 使用Redis模式的docker-compose
docker-compose -f docker-compose.redis.yml up -d
```

## 📊 配置验证

### 健康检查端点
```bash
# 基础健康检查
curl http://localhost:8000/health

# 数据库连接池状态
curl http://localhost:8000/health/database

# 限流器状态
curl http://localhost:8000/health/rate-limiter

# Worker统计信息
curl http://localhost:8000/stats/workers
```

### 并发测试
```bash
# 使用提供的检查脚本
python check_optimization.py

# 或手动测试并发限流
for i in {1..150}; do
  curl -X POST http://localhost:8000/api/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "chat_id": "test-chat-'$i'",
      "model": "test",
      "messages": [{"role": "user", "content": "测试消息'$i'"}],
      "max_tokens": 100
    }' &
done

wait
```

## ⚙️ 配置说明

### 并发控制配置
```python
# 共享内存模式
app.add_middleware(
    DistributedConnectionLimiter,
    max_concurrent_per_worker=15  # 每个worker最多15个并发
)

# Redis模式
app.add_middleware(
    RedisConnectionLimiter,
    redis_url="redis://localhost:6379",
    max_concurrent_per_worker=15,
    global_concurrent_limit=120
)
```

### 数据库连接配置
- **8 workers** × **20 connections** = **160 最大连接**
- **全局并发限制**: 120个请求（留40连接余量）
- **每worker并发**: 15个请求
- **安全系数**: 1.33 (160/120)

### 环境变量
```bash
# Redis配置
REDIS_URL="redis://localhost:6379"
USE_REDIS_RATE_LIMIT="true"  # 或 "false"

# 数据库配置
DATABASE_URL="postgresql://user:pass@localhost/chatbot"
CHAT_POSTGRES_URL="postgresql://user:pass@localhost/chatbot"

# 日志配置
LOG_LEVEL="info"
```

## 🐳 Docker配置文件

### docker-compose.shared-memory.yml
```yaml
version: '3.8'

services:
  ai-chat-app:
    build: .
    environment:
      - USE_REDIS_RATE_LIMIT=false
    ports:
      - "8000:8000"
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=chatbot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
      - MAX_CONNECTIONS=200
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### docker-compose.redis.yml
```yaml
version: '3.8'

services:
  ai-chat-app:
    build: .
    environment:
      - USE_REDIS_RATE_LIMIT=true
      - REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/database"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=chatbot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
      - MAX_CONNECTIONS=200
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
  redis_data:
```

## 🔍 监控和告警

### 关键指标监控
- **并发请求数**: 不应超过120个
- **数据库连接**: 不应超过160个
- **响应时间**: 流式响应正常，无503错误
- **限流触发**: 正常触发限流保护

### 日志监控
```bash
# 查看启动日志
docker logs ai-chat-app

# 查看限流日志
grep "限流触发" /var/log/ai-chat/app.log

# 查看连接池日志
grep "连接池" /var/log/ai-chat/app.log
```

### 告警阈值
- 连接池使用率 > 75%: 警告
- 连接池使用率 > 90%: 严重告警
- 限流触发频率 > 10次/分钟: 警告
- 503错误率 > 5%: 严重告警

## 🛠️ 故障排除

### 常见问题

#### 1. 共享内存权限问题
```bash
# 错误: Permission denied
# 解决: 确保容器有权限创建共享内存文件
docker run --tmpfs /tmp:exec,mode=777 ai-chat-service
```

#### 2. Redis连接失败
```bash
# 检查Redis状态
curl http://localhost:8000/health/rate-limiter

# 查看Redis日志
docker logs redis
```

#### 3. 数据库连接池耗尽
```bash
# 检查连接池状态
curl http://localhost:8000/health/database

# 查看数据库连接数
SELECT count(*) FROM pg_stat_activity;
```

## 📈 性能调优

### 1. 调整并发限制
```python
# 根据数据库连接数调整
max_concurrent_per_worker = max_connections // workers // 1.33
```

### 2. 优化连接池配置
```python
# database.py 中调整
pool_size=15,          # 基础连接数
max_overflow=15,       # 溢出连接数
pool_timeout=30,       # 连接超时
pool_recycle=1800,     # 连接回收时间
```

### 3. 监控和调优
- 定期检查连接池使用率
- 监控限流触发频率
- 根据业务量调整参数

---

**推荐**: 生产环境使用Redis分布式限流，开发测试环境使用共享内存限流。