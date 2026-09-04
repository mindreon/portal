from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ImportBatch(Base):
    """一次上传（多个 PDF 或一个 zip）是一个批次，只是这次干活的筐。"""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="review")  # processing | review | confirmed
    warning_text: Mapped[str | None] = mapped_column(Text)
    # 这次批次真正碰到的合同（含并入已有、内容重复跳过），逗号分隔 id
    affected_contract_ids: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    files: Mapped[list["ContractFile"]] = relationship(back_populates="batch")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="import_batch")  # noqa: F821


class ContractFile(Base):
    """合同附件。解析出的原文也存在这里，方便人对照。"""

    __tablename__ = "contract_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    # SHA-256，用来拦住「同一份 PDF 又传一遍」
    content_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(32), default="electronic")  # electronic | scanned
    doc_type: Mapped[str] = mapped_column(String(32), default="unknown")  # contract | invoice | unknown
    parse_status: Mapped[str] = mapped_column(String(32), default="pending")
    extracted_text: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    batch: Mapped[ImportBatch | None] = relationship(back_populates="files")
    contract: Mapped["Contract | None"] = relationship(back_populates="files")  # noqa: F821
