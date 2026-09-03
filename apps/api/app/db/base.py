"""SQLAlchemy 声明式基类。所有模型都继承 Base，Alembic 才能发现表结构。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
