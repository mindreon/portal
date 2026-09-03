from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


CONTRACT_STATUSES = ("draft", "active", "expired", "terminated")


class ContractIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    contract_no: str = Field(min_length=1, max_length=64)
    counterparty: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="CNY", max_length=8)
    status: str = Field(default="draft")
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class ContractOut(ContractIn):
    id: int
    owner_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
