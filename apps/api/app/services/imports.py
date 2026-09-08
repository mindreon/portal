"""
合同上传批次：先把 zip 解成单独的 PDF 落盘并建占位合同，再在后台识别。

同一份文件（内容哈希相同）不会再生成一条合同/附件。
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.contract import Contract
from app.models.document import ContractFile, ImportBatch
from app.models.invoice import Invoice
from app.models.payment import Collection, PaymentSchedule
from app.models.user import User
from app.services.extract import (
    ExtractedFields,
    build_schedules,
    derive_counterparty,
    derive_our_role,
    identity_key,
    merge_extracted_fields,
    normalize_contract_no,
    unnumbered_fingerprint,
)
from app.services.pdf_parse import parse_pdf_bytes

MAX_FILE_MB = 200
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+")
logger = logging.getLogger(__name__)


def _safe_name(name: str) -> str:
    base = Path(name.replace("\\", "/")).name
    cleaned = UNSAFE_NAME.sub("_", base).strip("._") or "file.pdf"
    return cleaned[:180]


def _write_bytes(batch_id: int, original_name: str, data: bytes) -> Path:
    """每个 PDF 写成批次目录里的独立文件，zip 本身不保留。"""
    folder = Path(get_settings().upload_dir) / str(batch_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex[:10]}_{_safe_name(original_name)}"
    path.write_bytes(data)
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expand_uploads(files: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    """把 zip 拆成内部的 PDF；其它文件原样保留。真正写盘在 stage 里按文件做。"""
    expanded: list[tuple[str, bytes]] = []
    for name, data in files:
        lower = name.lower()
        if lower.endswith(".zip"):
            expanded.extend(_unzip_pdfs(name, data))
            continue
        expanded.append((name, data))
    return expanded


def _unzip_pdfs(zip_name: str, data: bytes) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            for info in archive.infolist():
                member = info.filename.replace("\\", "/")
                if info.is_dir() or ".." in Path(member).parts:
                    continue
                if not member.lower().endswith(".pdf"):
                    continue
                if info.file_size > MAX_FILE_BYTES:
                    continue
                original = f"{Path(zip_name).stem}/{Path(member).name}"
                out.append((original, archive.read(info)))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{zip_name} 不是有效的 zip") from exc
    if not out:
        raise ValueError(f"{zip_name} 里没有 PDF")
    return out


def _placeholder_contract(filename: str, owner_id: int, batch_id: int) -> Contract:
    title = Path(filename.replace("\\", "/")).stem or "未编号合同"
    return Contract(
        title=title[:255],
        contract_no=None,
        party_a="",
        party_b="",
        our_role="",
        counterparty="（待填写）",
        subject_name="",
        amount=0,
        status="draft",
        owner_id=owner_id,
        import_batch_id=batch_id,
    )


def _prepare_contract(payload: ExtractedFields, filename: str, owner_id: int, batch_id: int) -> Contract:
    contract = _placeholder_contract(filename, owner_id, batch_id)
    _fill_contract(contract, payload, filename)
    return contract


def _fill_contract(contract: Contract, payload: ExtractedFields, filename: str) -> None:
    party_a = payload.party_a
    party_b = payload.party_b
    our_role = derive_our_role(party_a, party_b)
    title = payload.title or Path(filename.replace("\\", "/")).stem or contract.title or "未编号合同"
    contract.title = title[:255]
    contract.contract_no = normalize_contract_no(payload.contract_no)
    contract.party_a = party_a
    contract.party_b = party_b
    contract.our_role = our_role
    contract.counterparty = derive_counterparty(party_a, party_b, our_role) or "（待填写）"
    contract.subject_name = (payload.subject_name or "")[:255]
    contract.amount = payload.amount or 0
    contract.signed_at = payload.signed_at
    contract.start_date = payload.start_date
    contract.end_date = payload.end_date
    contract.notes = "；".join(payload.warnings) or None


def _find_existing_file(db: Session, digest: str, seen: dict[str, ContractFile]) -> ContractFile | None:
    if digest in seen:
        return seen[digest]
    return db.scalar(select(ContractFile).where(ContractFile.content_hash == digest))


def _find_existing_contract(
    db: Session,
    fields: ExtractedFields,
    existing_by_no: dict[str, Contract],
    exclude_id: int | None = None,
) -> tuple[Contract | None, str | None]:
    numbered = normalize_contract_no(fields.contract_no)
    if numbered and numbered in existing_by_no:
        found = existing_by_no[numbered]
        if exclude_id is None or found.id != exclude_id:
            return found, f"编号 {numbered} 已在库中，附件并入已有合同。"
    if unnumbered_fingerprint(fields):
        query = select(Contract).where(
            Contract.contract_no.is_(None),
            Contract.party_a == fields.party_a,
            Contract.party_b == fields.party_b,
            Contract.amount == fields.amount,
            Contract.signed_at == fields.signed_at,
        )
        if exclude_id is not None:
            query = query.where(Contract.id != exclude_id)
        twin = db.scalar(query.order_by(Contract.id))
        if twin is not None:
            return twin, f"甲方/乙方/金额/签订日与已有合同「{twin.title}」相同，已并入，避免重复草稿。"
    return None, None


def _absorb(db: Session, target: Contract, source: Contract | None) -> None:
    """把占位合同上的附件/发票并进真正的那一份，再删掉占位。"""
    if source is None or target.id == source.id:
        return
    for item in db.scalars(select(ContractFile).where(ContractFile.contract_id == source.id)):
        item.contract_id = target.id
    for item in db.scalars(select(Invoice).where(Invoice.contract_id == source.id)):
        item.contract_id = target.id
    for item in db.scalars(select(PaymentSchedule).where(PaymentSchedule.contract_id == source.id)):
        item.contract_id = target.id
    for item in db.scalars(select(Collection).where(Collection.contract_id == source.id)):
        item.contract_id = target.id
    db.delete(source)
    db.flush()


def _numbered_contracts(db: Session) -> dict[str, Contract]:
    return {
        item.contract_no: item
        for item in db.scalars(select(Contract).where(Contract.contract_no.is_not(None))).all()
        if item.contract_no
    }


def _append_warning(batch: ImportBatch, line: str) -> None:
    existing = [item for item in (batch.warning_text or "").split("\n") if item]
    if line not in existing:
        existing.append(line)
        batch.warning_text = "\n".join(existing)


def _touch(batch: ImportBatch, contract_id: int | None) -> None:
    if not contract_id:
        return
    ids = [item for item in (batch.affected_contract_ids or "").split(",") if item]
    token = str(contract_id)
    if token not in ids:
        ids.append(token)
        batch.affected_contract_ids = ",".join(ids)


def run_import(db: Session, user: User, uploads: list[tuple[str, bytes]]) -> ImportBatch:
    """先落盘、建占位合同并提交。识别由调用方丢到后台，避免占用这次请求的数据库连接。"""
    batch = stage_import(db, user, uploads)
    if not import_needs_processing(db, batch):
        batch.status = "review"
        db.commit()
        db.refresh(batch)
    return batch


def import_needs_processing(db: Session, batch: ImportBatch) -> bool:
    pending = db.scalars(
        select(ContractFile).where(
            ContractFile.batch_id == batch.id,
            ContractFile.parse_status.in_(("pending", "processing")),
        )
    ).first()
    return pending is not None


def stage_import(db: Session, user: User, uploads: list[tuple[str, bytes]]) -> ImportBatch:
    if not uploads:
        raise ValueError("请至少选择一个 PDF 或 zip")
    for name, data in uploads:
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"{name} 超过 {MAX_FILE_MB}MB")

    batch = ImportBatch(status="processing", owner_id=user.id)
    db.add(batch)
    db.flush()

    pdfs = _expand_uploads(uploads)
    warnings: list[str] = []
    touched_ids: list[int] = []
    seen_hashes: dict[str, ContractFile] = {}

    for original_name, data in pdfs:
        if not original_name.lower().endswith(".pdf"):
            warnings.append(f"已跳过非 PDF：{original_name}")
            continue
        digest = _sha256(data)
        existing_file = _find_existing_file(db, digest, seen_hashes)
        if existing_file is not None:
            warnings.append(
                f"{original_name} 与已有附件「{existing_file.original_name}」内容相同，已跳过，避免重复记录。"
            )
            if existing_file.contract_id:
                touched_ids.append(existing_file.contract_id)
            continue
        stored = _write_bytes(batch.id, original_name, data)
        contract = _placeholder_contract(original_name, user.id, batch.id)
        db.add(contract)
        db.flush()
        row = ContractFile(
            batch_id=batch.id,
            contract_id=contract.id,
            original_name=original_name[:255],
            stored_path=str(stored),
            content_hash=digest,
            source="electronic",
            doc_type="contract",
            parse_status="pending",
        )
        db.add(row)
        db.flush()
        seen_hashes[digest] = row
        touched_ids.append(contract.id)

    batch.warning_text = "\n".join(dict.fromkeys(warnings)) or None
    batch.affected_contract_ids = ",".join(str(item) for item in dict.fromkeys(touched_ids)) or None
    db.commit()
    db.refresh(batch)
    return batch


def process_import_batch(batch_id: int) -> None:
    """后台入口：自己开数据库会话，按文件提交，列表轮询才能看到进度。"""
    db = SessionLocal()
    try:
        _process_import_batch(db, batch_id)
    except Exception:
        logger.exception("导入批次 %s 处理失败", batch_id)
        batch = db.get(ImportBatch, batch_id)
        if batch is not None:
            _append_warning(batch, "后台识别失败，请打开合同手工核对。")
            batch.status = "failed"
            db.commit()
        raise
    finally:
        db.close()


def _process_import_batch(db: Session, batch_id: int) -> None:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        return
    user = db.get(User, batch.owner_id)
    if user is None:
        batch.status = "failed"
        _append_warning(batch, "找不到上传人，无法继续识别。")
        db.commit()
        return

    pending = list(
        db.scalars(
            select(ContractFile)
            .where(
                ContractFile.batch_id == batch_id,
                ContractFile.parse_status.in_(("pending", "processing")),
            )
            .order_by(ContractFile.id)
        )
    )
    parsed_rows: list[tuple[ContractFile, ExtractedFields]] = []
    for row in pending:
        parsed = _parse_stored_file(db, row)
        if parsed is None:
            continue
        parsed_rows.append((row, parsed))

    _apply_parsed_rows(db, batch, user, parsed_rows)
    if not parsed_rows:
        _ensure_schedules(db, batch_id)
    if batch.status == "processing":
        batch.status = "review"
    db.commit()


def _parse_stored_file(db: Session, row: ContractFile) -> ExtractedFields | None:
    row.parse_status = "processing"
    db.commit()
    try:
        data = Path(row.stored_path).read_bytes()
        parsed = parse_pdf_bytes(data)
    except Exception as exc:  # noqa: BLE001 — 单份失败不能拖死整批
        row.parse_status = "failed"
        row.error_message = f"识别失败：{exc}"
        db.commit()
        return None
    row.source = parsed.source
    row.extracted_text = parsed.text or None
    row.error_message = parsed.error
    row.parse_status = "failed" if parsed.error and not parsed.text else "done"
    fields = parsed.fields
    row.doc_type = "invoice" if fields.doc_type == "invoice" else "contract"
    db.commit()
    return fields


def _apply_parsed_rows(
    db: Session,
    batch: ImportBatch,
    user: User,
    parsed_rows: list[tuple[ContractFile, ExtractedFields]],
) -> None:
    if not parsed_rows:
        return

    warnings: list[str] = []
    contract_piles: dict[str, Contract] = {}
    pile_fields: dict[str, ExtractedFields] = {}
    existing = _numbered_contracts(db)
    invoice_only: list[tuple[ContractFile, ExtractedFields]] = []

    for row, fields in parsed_rows:
        warnings.extend(fields.warnings)
        placeholder = db.get(Contract, row.contract_id) if row.contract_id else None
        if fields.doc_type == "invoice" and not fields.contract_no and not fields.party_a:
            invoice_only.append((row, fields))
            continue
        key = identity_key(fields, row.id)
        contract = contract_piles.get(key)
        if contract is None:
            found, reason = _find_existing_contract(
                db, fields, existing, exclude_id=placeholder.id if placeholder else None
            )
            if found is not None:
                contract = found
                _absorb(db, found, placeholder)
                if reason:
                    warnings.append(reason)
            else:
                contract = placeholder or _prepare_contract(fields, row.original_name, user.id, batch.id)
                if placeholder is None:
                    db.add(contract)
                    db.flush()
                _fill_contract(contract, fields, row.original_name)
                numbered = normalize_contract_no(fields.contract_no)
                if numbered:
                    existing[numbered] = contract
            contract_piles[key] = contract
            pile_fields[key] = fields
        else:
            pile_fields[key], _ = merge_extracted_fields(pile_fields[key], fields)
            _absorb(db, contract, placeholder)
        row.contract_id = contract.id
        row.doc_type = "invoice" if fields.doc_type == "invoice" else "contract"
        _touch(batch, contract.id)
        for extracted in fields.invoices:
            _add_invoice_draft(db, user, contract, extracted.invoice_code, extracted.invoice_no, extracted.amount)
        db.commit()

    contract_list = list(contract_piles.values())
    for row, fields in invoice_only:
        placeholder = db.get(Contract, row.contract_id) if row.contract_id else None
        target = contract_list[0] if len(contract_list) == 1 else None
        row.contract_id = target.id if target else None
        row.doc_type = "invoice"
        if target:
            _absorb(db, target, placeholder)
            _touch(batch, target.id)
        elif placeholder is not None:
            db.delete(placeholder)
            db.flush()
        for extracted in fields.invoices:
            _add_invoice_draft(
                db, user, target, extracted.invoice_code, extracted.invoice_no, extracted.amount, user_id=user.id
            )
        db.commit()

    for key, contract in contract_piles.items():
        already = db.scalars(select(PaymentSchedule).where(PaymentSchedule.contract_id == contract.id)).first()
        if already:
            continue
        combined = pile_fields.get(key) or ExtractedFields()
        for index, item in enumerate(build_schedules(contract.amount, combined.schedules), start=1):
            db.add(
                PaymentSchedule(
                    contract_id=contract.id,
                    period_no=index,
                    name=item.name,
                    amount=item.amount or 0,
                    due_date=contract.signed_at or contract.start_date,
                )
            )

    if warnings:
        for line in dict.fromkeys(warnings):
            _append_warning(batch, line)


def _ensure_schedules(db: Session, batch_id: int) -> None:
    """恢复中断的批次时，已识别完的合同也补上回款计划。"""
    contracts = db.scalars(select(Contract).where(Contract.import_batch_id == batch_id)).all()
    for contract in contracts:
        already = db.scalars(select(PaymentSchedule).where(PaymentSchedule.contract_id == contract.id)).first()
        if already:
            continue
        if not contract.amount:
            continue
        for index, item in enumerate(build_schedules(contract.amount, []), start=1):
            db.add(
                PaymentSchedule(
                    contract_id=contract.id,
                    period_no=index,
                    name=item.name,
                    amount=item.amount or 0,
                    due_date=contract.signed_at or contract.start_date,
                )
            )


def _add_invoice_draft(
    db: Session,
    user: User,
    contract: Contract | None,
    invoice_code: str,
    invoice_no: str,
    amount,
    user_id: int | None = None,
) -> None:
    number = (invoice_no or "").strip() or f"DRAFT-{uuid.uuid4().hex[:10]}"
    exists = db.scalar(select(Invoice).where(Invoice.invoice_no == number))
    if exists:
        if contract and exists.contract_id is None:
            exists.contract_id = contract.id
        return
    db.add(
        Invoice(
            title="识别发票草稿" if invoice_code or invoice_no else "发票草稿",
            invoice_code=invoice_code or None,
            invoice_no=number,
            counterparty=(contract.counterparty if contract else "") or "（待填写）",
            amount=amount or 0,
            status="draft",
            contract_id=contract.id if contract else None,
            owner_id=user_id or user.id,
        )
    )
