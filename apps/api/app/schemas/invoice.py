from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

INVOICE_STATUSES = ("draft", "issued", "paid", "void")


class InvoiceIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    invoice_code: str | None = Field(default=None, max_length=32)
    invoice_no: str = Field(min_length=1, max_length=64)
    counterparty: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="CNY", max_length=8)
    status: str = Field(default="draft")
    issued_at: date | None = None
    due_at: date | None = None
    notes: str | None = None
    contract_id: int | None = None
    schedule_id: int | None = None


class InvoiceOut(InvoiceIn):
    id: int
    owner_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
