"""contract subject name (product / service)

Revision ID: 0004_subject_name
Revises: 0003_file_hash
Create Date: 2026-09-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_subject_name"
down_revision: Union[str, None] = "0003_file_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column("subject_name", sa.String(length=255), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("contracts", "subject_name")
