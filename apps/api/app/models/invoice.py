from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Invoice(Base):
    """发票。可选关联到某份合同，方便以后对账。"""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    invoice_code: Mapped[str | None] = mapped_column(String(32))
    invoice_no: Mapped[str] = mapped_column(String(64), unique=True)
    counterparty: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    issued_at: Mapped[date | None] = mapped_column(Date)
    due_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"))
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("payment_schedules.id"))
    # 人工上传的发票 PDF。没有文件时三列都是空的，兼容以前只填表单的发票。
    original_name: Mapped[str | None] = mapped_column(String(255))
    stored_path: Mapped[str | None] = mapped_column(String(512))
    content_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="invoices")  # noqa: F821
    contract: Mapped["Contract | None"] = relationship(back_populates="invoices")  # noqa: F821
    schedule: Mapped["PaymentSchedule | None"] = relationship(back_populates="invoices")  # noqa: F821

    @property
    def has_file(self) -> bool:
        """前端用来决定要不要显示预览 / 下载。盘上的路径不对外暴露。"""
        return bool(self.stored_path)
