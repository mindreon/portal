"""
FastAPI 入口。

新业务模块怎么加：
1. 在 app/models 建表
2. 在 app/schemas 写请求/响应形状
3. 在 app/modules 写路由
4. 在这里 include_router
5. 生成 Alembic 迁移
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.modules import auth, contracts, imports, invoices

# 导入模型，确保 Base.metadata 里有所有表
from app import models as _models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    开发 / SQLite 场景直接建表，省掉第一次跑迁移。
    生产 Docker 启动脚本会先执行 alembic upgrade head。
    """
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(imports.router, prefix="/api/v1")
app.include_router(contracts.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
