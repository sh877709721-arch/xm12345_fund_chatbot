# 开发指南

#### 权限管理

目前权限采用如下两种

```python
from app.service.rbac import require_admin,require_any_role
```

admin 拥有全部权限
require_any_role 只读

# Docker 部署

目前在算力机的路径为:
/data01/xmit/workspace/agent_service/api

```cmd
docker stack deploy -c docker-compose.swarm.yml medicial-agent-app


docker stack deploy -c docker-compose.swarm.yml medicial-agent-app-10888
```

# 注意

/app/config/database.py 内，如迁移其他场景请修改 schema

```python
global_schema = "medical_insurance" # TODO: 注意要修改这里 chatbot
Base = declarative_base(metadata=MetaData(schema=global_schema))
```
