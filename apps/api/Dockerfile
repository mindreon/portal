# 用公司 Harbor 的 uv Alpine 镜像安装依赖，最终只留运行所需文件
FROM harbor.mindreon.com/ops/astral/uv:python3.12-alpine

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

# 先跑数据库迁移，再启动接口
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
