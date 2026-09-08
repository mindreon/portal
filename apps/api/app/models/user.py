from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """系统用户。飞书登录成功后按 open_id 找到或创建这一行。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    feishu_open_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    feishu_union_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(32), default="member")  # admin 能打开权限页；member 不能
    # 逗号分隔的模块 id，例如 "invoices" 或 "contracts,invoices"。空字符串表示一个业务模块都不给。
    modules: Mapped[str] = mapped_column(String(255), default="invoices")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contracts: Mapped[list["Contract"]] = relationship(back_populates="owner")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="owner")  # noqa: F821
