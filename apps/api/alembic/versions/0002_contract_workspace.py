"""contract import tables and nullable contract_no

Revision ID: 0002_contract_workspace
Revises: 0001_initial
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_contract_workspace"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="review"),
        sa.Column("warning_text", sa.Text()),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    with op.batch_alter_table("contracts") as batch:
        batch.alter_column("contract_no", existing_type=sa.String(length=64), nullable=True)
        batch.add_column(sa.Column("party_a", sa.String(length=255), server_default=""))
        batch.add_column(sa.Column("party_b", sa.String(length=255), server_default=""))
        batch.add_column(sa.Column("our_role", sa.String(length=16), server_default=""))
        batch.add_column(sa.Column("signed_at", sa.Date()))
        batch.add_column(sa.Column("import_batch_id", sa.Integer(), sa.ForeignKey("import_batches.id")))
    op.create_table(
        "payment_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("period_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(length=64), nullable=False, server_default="一次性"),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("invoice_code", sa.String(length=32)))
        batch.add_column(sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("payment_schedules.id")))
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("payment_schedules.id")),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("received_at", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "contract_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("import_batches.id")),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id")),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.String(length=512), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="electronic"),
        sa.Column("doc_type", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("parse_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("contract_files")
    op.drop_table("collections")
    with op.batch_alter_table("invoices") as batch:
        batch.drop_column("schedule_id")
        batch.drop_column("invoice_code")
    op.drop_table("payment_schedules")
    with op.batch_alter_table("contracts") as batch:
        batch.drop_column("import_batch_id")
        batch.drop_column("signed_at")
        batch.drop_column("our_role")
        batch.drop_column("party_b")
        batch.drop_column("party_a")
        batch.alter_column("contract_no", existing_type=sa.String(length=64), nullable=False)
    op.drop_table("import_batches")
