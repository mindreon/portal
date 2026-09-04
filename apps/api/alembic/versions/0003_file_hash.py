"""file content hash and import affected contract ids

Revision ID: 0003_file_hash
Revises: 0002_contract_workspace
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_file_hash"
down_revision: Union[str, None] = "0002_contract_workspace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("import_batches", sa.Column("affected_contract_ids", sa.Text()))
    with op.batch_alter_table("contract_files") as batch:
        batch.add_column(sa.Column("content_hash", sa.String(length=64)))
        batch.create_index("ix_contract_files_content_hash", ["content_hash"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("contract_files") as batch:
        batch.drop_index("ix_contract_files_content_hash")
        batch.drop_column("content_hash")
    op.drop_column("import_batches", "affected_contract_ids")
