# 简化版用户认证中间件

## 概述

这是一个简化的用户认证中间件，专注于核心功能：
- 拦截HTTP请求
- 解析JWT token
- 计算token有效期
- 记录用户信息到请求状态

## 功能特性

### ✅ 核心功能
1. **Token解析**：从Authorization header解析JWT token
2. **有效期计算**：实时计算token剩余有效时间
3. **状态注入**：将用户信息注入到request.state中
4. **简单日志**：记录认证成功、失败和缺失token的情况

### 🚫 移除的复杂功能
- 复杂的数据库查询
- 详细的文件日志系统
- 异步日志处理
- 复杂的用户信息结构

## 使用方法

### 1. 中间件已自动添加到应用

```python
# 在main.py中已配置
app.add_middleware(
    AuthLoggingMiddleware,
    exclude_paths=[
        "/health",
        "/debug-now",
        "/docs",
        "/v1/auth/token",
        "/v1/auth/front_token"
    ]
)
```

### 2. 获取用户信息

#### 获取用户名
```python
from app.middleware.auth_logging import get_username_from_request

@app.get("/profile")
async def profile(request: Request):
    username = get_username_from_request(request)
    if username:
        return {"username": username}
    return {"message": "未认证"}
```

#### 获取完整用户信息
```python
from app.middleware.auth_logging import get_current_user_from_request

@app.get("/user-info")
async def user_info(request: Request):
    user_data = get_current_user_from_request(request)
    return {"user": user_data}
```

#### 获取token有效期
```python
from app.middleware.auth_logging import get_token_validity_from_request

@app.get("/token-expiry")
async def token_expiry(request: Request):
    validity = get_token_validity_from_request(request)
    return {"validity": validity}
```

### 3. 访问测试接口

应用提供了几个测试接口：

- `/user-profile` - 获取用户信息
- `/optional-auth` - 可选认证示例
- `/token-status` - 查看token有效期

## Token有效期信息

中间件计算以下信息：

```json
{
    "expires_at": "2025-11-30T10:00:00+00:00",
    "current_time": "2025-11-30T09:30:00+00:00",
    "expires_in_hours": 0.5,
    "is_expired": false,
    "remaining_minutes": 30.0
}
```

## 日志输出

中间件会在控制台输出简单的认证日志：

### 认证成功
```
✅ 用户 admin 认证成功 | 路径: /api/users | Token剩余: 0.5小时 | IP: 127.0.0.1
```

### 认证失败
```
❌ 认证失败: Token无效 | 路径: /api/users | IP: 127.0.0.1
```

### 缺少Token（仅对需要认证的路径）
```
⚠️ 需要认证的请求缺少Token: GET /api/admin/users
```

## 响应头

中间件会自动添加以下响应头：

```
X-User-Name: admin
X-Token-Expires-In: 0.5
```

## React客户端集成

### 1. 登录获取token
```javascript
// 登录后获取token
const response = await fetch('/v1/auth/token', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'username=admin&password=yourpassword'
});

const {access_token} = await response.json();
localStorage.setItem('token', access_token);
```

### 2. 请求时携带token
```javascript
// 在请求头中携带token
const token = localStorage.getItem('token');
const response = await fetch('/api/protected-route', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 3. 检查token状态
```javascript
// 获取token有效期信息
const response = await fetch('/token-status', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const {token_validity} = await response.json();
console.log(`Token剩余时间: ${token_validity.expires_in_hours}小时`);

// 检查是否需要刷新token
if (token_validity.expires_in_hours < 0.1) {
  console.log('Token即将过期，需要重新登录');
}
```

## 中间件工作流程

1. **拦截请求**：所有请求都会被中间件拦截
2. **排除路径检查**：排除健康检查、文档、登录等路径
3. **Token解析**：尝试从Authorization header解析JWT token
4. **计算有效期**：实时计算token剩余有效时间
5. **状态注入**：将用户信息注入到request.state
6. **日志记录**：记录认证状态到控制台
7. **处理请求**：继续处理原始请求
8. **响应头添加**：在响应中添加用户和有效期信息

## 配置说明

### 环境变量
确保在`.env`文件中配置：

```env
NEXTAUTH_SECRET=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 排除路径配置
中间件已配置排除以下路径：
- `/health` - 健康检查
- `/debug-now` - 调试接口
- `/docs`, `/openapi.json`, `/redoc` - API文档
- `/v1/auth/token`, `/v1/auth/front_token` - 登录接口

可以根据需要添加更多排除路径：

```python
app.add_middleware(
    AuthLoggingMiddleware,
    exclude_paths=[
        "/health",
        "/debug-now",
        "/public-api"  # 新增公共API路径
    ]
)
```

## 故障排除

### 常见问题

1. **Token解析失败**
   - 检查token格式是否正确
   - 确认NEXTAUTH_SECRET配置正确

2. **日志不显示**
   - 确认日志级别配置
   - 检查路径是否被排除

3. **用户信息为空**
   - 确认请求头包含Authorization
   - 检查token是否过期

### 调试模式

启用详细日志：

```python
import logging
logging.getLogger("auth.middleware").setLevel(logging.DEBUG)
```

这个简化版的中间件提供了您需要的核心功能：拦截请求、解析token、计算有效期，并且代码简单易维护。React客户端可以轻松获取token有效期信息，用于决定何时需要重新登录。