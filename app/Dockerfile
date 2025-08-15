FROM ubuntu:22.04

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive
    ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    tzdata \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    build-essential \
    libpq-dev \
    unixodbc-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 创建软链接
RUN ln -s /usr/bin/python3 /usr/bin/python

# 复制并安装Python依赖
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://mirrors.cloud.tencent.com/pypi/simple/ \
    --extra-index-url https://mirrors.huaweicloud.com/repository/pypi/simple/ \
    --extra-index-url https://pypi.douban.com/simple/ \
    --extra-index-url https://pypi.mirrors.ustc.edu.cn/simple/ \
    --timeout 300 --retries 5 \
    --trusted-host mirrors.aliyun.com \
    --trusted-host mirrors.cloud.tencent.com \
    --trusted-host mirrors.huaweicloud.com \
    --trusted-host pypi.douban.com \
    --trusted-host pypi.mirrors.ustc.edu.cn \
    --no-cache-dir --default-timeout=300

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs
# 设置权限
RUN chmod +x main.py

# 暴露端口
EXPOSE 8088

# 健康检查
HEALTHCHECK --interval=1h --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8088/ || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088", "--workers", "1", "--log-level", "info"] 