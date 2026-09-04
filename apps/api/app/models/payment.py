from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentSchedule(Base):
    """回款计划：答应怎么付。一次性 = 一期；分期 = 多期。"""

    __tablename__ = "payment_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    period_no: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(64), default="一次性")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contract: Mapped["Contract"] = relationship(back_populates="schedules")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="schedule")  # noqa: F821
    collections: Mapped[list["Collection"]] = relationship(back_populates="schedule")


class Collection(Base):
    """实际回款：钱到没到。"""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("payment_schedules.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    received_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contract: Mapped["Contract"] = relationship(back_populates="collections")  # noqa: F821
    schedule: Mapped[PaymentSchedule | None] = relationship(back_populates="collections")
