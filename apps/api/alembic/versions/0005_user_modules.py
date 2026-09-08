"""user modules column

Revision ID: 0005_user_modules
Revises: 0004_subject_name
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_user_modules"
down_revision: Union[str, None] = "0004_subject_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("modules", sa.String(length=255), nullable=False, server_default="invoices"),
    )
    op.execute("UPDATE users SET modules = 'contracts,invoices' WHERE role = 'admin'")


def downgrade() -> None:
    op.drop_column("users", "modules")
