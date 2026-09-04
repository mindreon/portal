"""开发用 SQLite 不会跑 Alembic 时，给已有库补上新列。"""

from sqlalchemy import inspect, text

from app.db.session import engine


def ensure_sqlite_columns() -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        if "contract_files" in tables:
            cols = {item["name"] for item in inspector.get_columns("contract_files")}
            if "content_hash" not in cols:
                conn.execute(text("ALTER TABLE contract_files ADD COLUMN content_hash VARCHAR(64)"))
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_contract_files_content_hash "
                    "ON contract_files (content_hash)"
                )
            )
        if "import_batches" in tables:
            cols = {item["name"] for item in inspector.get_columns("import_batches")}
            if "affected_contract_ids" not in cols:
                conn.execute(text("ALTER TABLE import_batches ADD COLUMN affected_contract_ids TEXT"))
