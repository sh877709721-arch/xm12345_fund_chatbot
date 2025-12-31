# 用户认证中间件使用说明

## 概述

`AuthLoggingMiddleware` 是一个用于FastAPI应用的认证中间件，提供以下功能：

1. **自动用户认证解析**：从Authorization header解析JWT token
2. **登录有效期计算**：计算token剩余有效时间和使用进度
3. **详细日志记录**：记录认证成功、失败、错误等详细信息
4. **用户信息注入**：将用户信息注入到请求状态中，方便其他路由使用

## 功能特性

### 🔐 认证功能
- 自动解析Bearer token
- JWT token验证和解码
- 用户信息从数据库获取
- token有效期计算

### 📝 日志功能
- **认证成功日志**：记录用户信息、token有效期、请求路径等
- **认证失败日志**：记录失败原因和请求信息
- **无token日志**：记录未携带token的请求
- **异常日志**：记录认证过程中的异常
- **请求完成日志**：记录请求处理时间和状态

### ⏱️ 时间计算
- Token签发时间 (`iat`)
- Token过期时间 (`exp`)
- 剩余有效时间（小时、秒）
- 已使用时间（小时、秒）
- 使用进度百分比
- 是否已过期检查

### 🛡️ 安全特性
- 支持排除特定路径（如健康检查、静态资源）
- 获取真实客户端IP（支持代理）
- 用户代理记录
- 请求追踪和审计

## 安装和配置

### 1. 添加中间件到应用

```python
from app.middleware.auth_logging import AuthLoggingMiddleware

app.add_middleware(
    AuthLoggingMiddleware,
    exclude_paths=[
        "/health",
        "/debug-now",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
        "/assets/",
        "/workspace/",
        "/v1/auth/token",  # 登录接口
        "/v1/auth/front_token"  # 前端登录接口
    ]
)
```

### 2. 日志配置

中间件会自动创建以下日志输出：

- **文件日志**：`logs/auth_middleware.log`
- **控制台日志**：实时输出到控制台

日志格式：
```
2025-11-30 10:30:45 - auth.middleware - INFO - ✅ 用户认证成功: admin | 路径: /api/users | IP: 127.0.0.1 | Token剩余: 0.5小时
```

## 使用方法

### 获取当前用户信息

#### 方法1：从请求状态获取
```python
from app.middleware.auth_logging import get_current_user_from_request

@app.get("/profile")
async def get_profile(request: Request):
    current_user = get_current_user_from_request(request)

    if not current_user:
        return {"message": "未认证用户"}

    return {
        "user_id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"]
    }
```

#### 方法2：使用依赖项（可选认证）
```python
from app.middleware.auth_logging import get_current_user_optional

@app.get("/optional-auth")
async def optional_route(request: Request):
    current_user = await get_current_user_optional(request)

    if current_user:
        return {"message": f"欢迎 {current_user['username']}"}
    else:
        return {"message": "你好，访客"}
```

#### 方法3：使用依赖项（必须认证）
```python
from app.middleware.auth_logging import get_current_user_required

@app.get("/protected-route")
async def protected_route(request: Request):
    # 如果用户未认证，会自动抛出401异常
    current_user = await get_current_user_required(request)
    return {"message": f"认证成功: {current_user['username']}"}
```

### 获取Token信息

```python
from app.middleware.auth_logging import get_token_info_from_request

@app.get("/token-info")
async def token_info_route(request: Request):
    token_info = get_token_info_from_request(request)

    if not token_info:
        return {"message": "无有效token"}

    return {
        "token_data": token_info,
        "current_user": get_current_user_from_request(request)
    }
```

## 日志级别和格式

### 日志级别
- **INFO**：认证成功、请求完成、无token请求
- **WARNING**：认证失败
- **ERROR**：认证过程中的异常

### 日志格式示例

#### 认证成功
```
✅ 用户认证成功: admin | 路径: /api/users | IP: 127.0.0.1 | Token剩余: 0.5小时
```

#### 认证失败
```
❌ 用户认证失败: Token verification failed | 路径: /api/users | IP: 127.0.0.1
```

#### 无认证Token
```
ℹ️ 无认证Token: GET /api/public | IP: 127.0.0.1
```

#### 请求完成
```
📋 请求完成: GET /api/users | 用户: admin | 状态码: 200 | 处理时间: 0.123s
```

#### 异常情况
```
🔥 认证过程异常: Database connection error | 路径: /api/users | IP: 127.0.0.1
```

## Token有效期信息

中间件会计算详细的token有效期信息：

```json
{
    "issued_at": "2025-11-30T09:00:00Z",
    "expires_at": "2025-11-30T10:00:00Z",
    "current_time": "2025-11-30T09:30:00Z",
    "time_remaining_seconds": 1800,
    "time_used_seconds": 1800,
    "total_valid_seconds": 3600,
    "usage_percentage": 50.0,
    "is_expired": false,
    "expires_in_hours": 0.5,
    "used_for_hours": 0.5
}
```

## 响应头

中间件会自动在响应中添加以下头信息：

```
X-Process-Time: 0.123
X-User-ID: 550e8400-e29b-41d4-a716-446655440000
X-User-Name: admin
```

## 环境变量配置

确保在 `.env` 文件中配置以下变量：

```env
# JWT配置
NEXTAUTH_SECRET=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 数据库配置（用于获取用户信息）
CHAT_POSTGRES_URL=postgresql://user:password@localhost/dbname
```

## 排除路径配置

中间件会自动排除以下路径：

- **健康检查**：`/health`
- **调试接口**：`/debug-now`
- **API文档**：`/docs`, `/openapi.json`, `/redoc`
- **静态资源**：`/favicon.ico`, `/assets/`, `/workspace/`
- **登录接口**：`/v1/auth/token`, `/v1/auth/front_token`

可以通过 `exclude_paths` 参数自定义排除路径：

```python
app.add_middleware(
    AuthLoggingMiddleware,
    exclude_paths=[
        "/custom-path",
        "/api/public"
    ]
)
```

## 安全注意事项

1. **敏感信息保护**：确保日志文件不被未授权访问
2. **Token安全**：始终使用HTTPS传输token
3. **数据库连接**：确保数据库连接池配置合理
4. **日志轮转**：配置日志轮转避免日志文件过大
5. **监控告警**：设置认证失败监控和告警

## 故障排除

### 常见问题

1. **日志文件权限问题**
   ```bash
   chmod 755 logs/
   ```

2. **数据库连接失败**
   - 检查数据库连接字符串
   - 确认数据库服务正常运行
   - 验证用户权限

3. **JWT解析失败**
   - 检查 `NEXTAUTH_SECRET` 配置
   - 确认token格式正确
   - 验证token未过期

4. **日志不显示**
   - 检查日志级别配置
   - 确认日志文件路径正确
   - 验证文件写入权限

### 调试模式

启用详细日志：

```python
import logging
logging.getLogger("auth.middleware").setLevel(logging.DEBUG)
```

## 性能优化建议

1. **数据库查询优化**：考虑添加用户信息缓存
2. **日志异步写入**：使用异步日志处理器
3. **连接池配置**：合理配置数据库连接池大小
4. **排除路径优化**：精确配置排除路径减少不必要的处理

## 示例完整路由

```python
from fastapi import Request, HTTPException
from app.middleware.auth_logging import (
    get_current_user_from_request,
    get_current_user_optional,
    get_current_user_required,
    get_token_info_from_request
)

# 1. 可选认证路由
@app.get("/profile")
async def get_profile(request: Request):
    user = get_current_user_from_request(request)
    if user:
        return {"user": user}
    return {"message": "请登录"}

# 2. 必须认证路由
@app.get("/dashboard")
async def dashboard(request: Request):
    user = await get_current_user_required(request)
    return {"dashboard": f"欢迎 {user['username']}"}

# 3. Token信息路由
@app.get("/token-status")
async def token_status(request: Request):
    user = get_current_user_from_request(request)
    token = get_token_info_from_request(request)

    return {
        "user": user,
        "token_valid": bool(token),
        "token_info": token
    }
```

通过以上配置和使用方法，您可以充分利用认证中间件提供的功能，实现完善的用户认证和日志记录系统。