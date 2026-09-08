"""invoice pdf attachment columns

Revision ID: 0006_invoice_files
Revises: 0005_user_modules
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_invoice_files"
down_revision: Union[str, None] = "0005_user_modules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("original_name", sa.String(length=255)))
        batch.add_column(sa.Column("stored_path", sa.String(length=512)))
        batch.add_column(sa.Column("content_hash", sa.String(length=64)))
        batch.create_index("ix_invoices_content_hash", ["content_hash"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch:
        batch.drop_index("ix_invoices_content_hash")
        batch.drop_column("content_hash")
        batch.drop_column("stored_path")
        batch.drop_column("original_name")
