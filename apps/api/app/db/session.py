"""
数据库引擎和会话工厂。

Session 可以理解成「一次对话」：在这次请求里查询、修改，结束时提交或回滚。
FastAPI 用 Depends(get_db) 把会话注入到每个接口。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

settings = get_settings()

# SQLite 需要 check_same_thread=False，否则 FastAPI 多线程会报错
connect_args = {}
engine_kwargs: dict = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
    # 内存库必须共用连接池，否则「建表」和「查询」会看到两份空库
    if settings.database_url in {"sqlite://", "sqlite:///:memory:"}:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
