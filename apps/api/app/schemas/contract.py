from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


CONTRACT_STATUSES = ("draft", "active", "expired", "terminated")
OUR_ROLES = ("", "party_a", "party_b")


class ContractIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    contract_no: str | None = Field(default=None, max_length=64)
    party_a: str = Field(default="", max_length=255)
    party_b: str = Field(default="", max_length=255)
    our_role: str = Field(default="")
    counterparty: str = Field(default="", max_length=255)
    amount: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="CNY", max_length=8)
    status: str = Field(default="draft")
    signed_at: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None

    @field_validator("contract_no", mode="before")
    @classmethod
    def empty_no_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ContractOut(ContractIn):
    id: int
    owner_id: int
    billed_amount: Decimal = Decimal("0")
    collected_amount: Decimal = Decimal("0")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class FileOut(BaseModel):
    id: int
    original_name: str
    source: str
    doc_type: str
    parse_status: str
    extracted_text: str | None = None
    error_message: str | None = None
    contract_id: int | None = None

    model_config = {"from_attributes": True}


class ScheduleIn(BaseModel):
    name: str = Field(default="一次性", max_length=64)
    amount: Decimal = Field(default=Decimal("0"), ge=0)
    due_date: date | None = None
    notes: str | None = None


class ScheduleOut(ScheduleIn):
    id: int
    contract_id: int
    period_no: int
    collected_amount: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


class CollectionIn(BaseModel):
    amount: Decimal = Field(ge=0)
    received_at: date | None = None
    schedule_id: int | None = None
    notes: str | None = None


class CollectionOut(CollectionIn):
    id: int
    contract_id: int

    model_config = {"from_attributes": True}
