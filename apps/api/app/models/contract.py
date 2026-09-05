from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Contract(Base):
    """合同。附件、回款计划另表存放，避免把这张表撑太宽。编号可空。"""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    # 扫描件常常没有编号；空值用 NULL，多份未编号可以共存
    contract_no: Mapped[str | None] = mapped_column(String(64), unique=True)
    party_a: Mapped[str] = mapped_column(String(255), default="")
    party_b: Mapped[str] = mapped_column(String(255), default="")
    our_role: Mapped[str] = mapped_column(String(16), default="")  # party_a | party_b | ""
    counterparty: Mapped[str] = mapped_column(String(255), default="")
    subject_name: Mapped[str] = mapped_column(String(255), default="")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    signed_at: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="contracts")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="contract")  # noqa: F821
    files: Mapped[list["ContractFile"]] = relationship(back_populates="contract")  # noqa: F821
    schedules: Mapped[list["PaymentSchedule"]] = relationship(back_populates="contract")  # noqa: F821
    collections: Mapped[list["Collection"]] = relationship(back_populates="contract")  # noqa: F821
    import_batch: Mapped["ImportBatch | None"] = relationship(back_populates="contracts")  # noqa: F821
