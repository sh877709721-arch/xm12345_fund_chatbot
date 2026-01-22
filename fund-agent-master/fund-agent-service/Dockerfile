# 使用 Python 3.11 基础镜像
FROM alibaba-cloud-linux-3-registry.cn-hangzhou.cr.aliyuncs.com/alinux3/python:3.11.1

#RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/
#https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip install --no-cache-dir --progress-bar off uv -i https://mirrors.aliyun.com/pypi/simple/

# 设置非root用户
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# 配置国内镜像源
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
#https://pypi.tuna.tsinghua.edu.cn/simple/
ENV PIP_FIND_LINKS=https://mirrors.aliyun.com/pypi/simple/
#https://pypi.tuna.tsinghua.edu.cn/simple/
ENV TZ=Asia/Shanghai

# 复制依赖文件
COPY --chown=app:app pyproject.toml uv.lock uv.toml ./

# 创建虚拟环境并激活
RUN uv venv .venv

ENV VIRTUAL_ENV=/home/app/.venv
ENV PATH="/home/app/.venv/bin:$PATH"

# 安装依赖
RUN uv sync
RUN uv pip install gunicorn==23.0.0

# 复制代码  图谱
COPY --chown=app:app . ./api
RUN chmod 755 /home/app/api/app/core/graph/chatbot_zh/output/lancedb
WORKDIR /home/app/api

EXPOSE 8200

# 启动命令
CMD ["gunicorn", "main:app", "-w", "8", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8200"]
