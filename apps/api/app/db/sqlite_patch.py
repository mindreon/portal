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
        if "contracts" in tables:
            cols = {item["name"] for item in inspector.get_columns("contracts")}
            if "subject_name" not in cols:
                conn.execute(
                    text("ALTER TABLE contracts ADD COLUMN subject_name VARCHAR(255) DEFAULT ''")
                )
        if "invoices" in tables:
            cols = {item["name"] for item in inspector.get_columns("invoices")}
            if "original_name" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN original_name VARCHAR(255)"))
            if "stored_path" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN stored_path VARCHAR(512)"))
            if "content_hash" not in cols:
                conn.execute(text("ALTER TABLE invoices ADD COLUMN content_hash VARCHAR(64)"))
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_invoices_content_hash "
                    "ON invoices (content_hash)"
                )
            )
        if "users" in tables:
            cols = {item["name"] for item in inspector.get_columns("users")}
            if "modules" not in cols:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN modules VARCHAR(255) DEFAULT 'invoices'")
                )
                conn.execute(
                    text("UPDATE users SET modules = 'contracts,invoices' WHERE role = 'admin'")
                )
