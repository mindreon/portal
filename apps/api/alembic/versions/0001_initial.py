"""initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feishu_open_id", sa.String(length=64), unique=True),
        sa.Column("feishu_union_id", sa.String(length=64), unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("avatar_url", sa.String(length=512)),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("contract_no", sa.String(length=64), nullable=False, unique=True),
        sa.Column("counterparty", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("invoice_no", sa.String(length=64), nullable=False, unique=True),
        sa.Column("counterparty", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("issued_at", sa.Date()),
        sa.Column("due_at", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("contracts")
    op.drop_table("users")
