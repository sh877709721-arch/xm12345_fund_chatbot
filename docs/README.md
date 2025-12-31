#### 知识管理

文档类知识

QA 类知识

#### 知识检索

构建索引

检索

#### 知识标注

批量导入
AI 生成\AI 语料校验

#### TTS/ASR 引擎

# 假设你的镜像是 my-web-app:latest，容器监听 8000 端口

docker service create \
 --name agent-service \
 --publish published=8888,target=8000 \
 --replicas=5 \
 api-agent-service:latest

docker service scale agent-service=5

docker service scale myweb=3

# 强制退出 Swarm（清理当前配置）

docker swarm leave --force

# 重新初始化

docker swarm init --advertise-addr 172.21.33.8
