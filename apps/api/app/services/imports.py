"""
合同上传批次：解压 zip、解析 PDF、按编号分堆（没编号则一文件一份草稿）。
同一份文件（内容哈希相同）不会再生成一条合同/附件。
"""

from __future__ import annotations

import hashlib
import re
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.contract import Contract
from app.models.document import ContractFile, ImportBatch
from app.models.invoice import Invoice
from app.models.payment import PaymentSchedule
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

MAX_FILE_BYTES = 50 * 1024 * 1024
UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+")


def _safe_name(name: str) -> str:
    base = Path(name.replace("\\", "/")).name
    cleaned = UNSAFE_NAME.sub("_", base).strip("._") or "file.pdf"
    return cleaned[:180]


def _write_bytes(batch_id: int, original_name: str, data: bytes) -> Path:
    folder = Path(get_settings().upload_dir) / str(batch_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex[:10]}_{_safe_name(original_name)}"
    path.write_bytes(data)
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expand_uploads(files: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    """把 zip 拆成内部的 PDF；其它文件原样保留。"""
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
                out.append((f"{Path(zip_name).stem}/{Path(member).name}", archive.read(info)))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{zip_name} 不是有效的 zip") from exc
    if not out:
        raise ValueError(f"{zip_name} 里没有 PDF")
    return out


def _prepare_contract(payload: ExtractedFields, filename: str, owner_id: int, batch_id: int) -> Contract:
    party_a = payload.party_a
    party_b = payload.party_b
    our_role = derive_our_role(party_a, party_b)
    title = payload.title or Path(filename).stem or "未编号合同"
    return Contract(
        title=title[:255],
        contract_no=normalize_contract_no(payload.contract_no),
        party_a=party_a,
        party_b=party_b,
        our_role=our_role,
        counterparty=derive_counterparty(party_a, party_b, our_role) or "（待填写）",
        subject_name=(payload.subject_name or "")[:255],
        amount=payload.amount or 0,
        signed_at=payload.signed_at,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes="；".join(payload.warnings) or None,
        status="draft",
        owner_id=owner_id,
        import_batch_id=batch_id,
    )


def _find_existing_file(db: Session, digest: str, seen: dict[str, ContractFile]) -> ContractFile | None:
    if digest in seen:
        return seen[digest]
    return db.scalar(select(ContractFile).where(ContractFile.content_hash == digest))


def _find_existing_contract(
    db: Session,
    fields: ExtractedFields,
    existing_by_no: dict[str, Contract],
) -> tuple[Contract | None, str | None]:
    numbered = normalize_contract_no(fields.contract_no)
    if numbered and numbered in existing_by_no:
        return existing_by_no[numbered], f"编号 {numbered} 已在库中，附件并入已有合同。"
    if unnumbered_fingerprint(fields):
        twin = db.scalar(
            select(Contract)
            .where(
                Contract.contract_no.is_(None),
                Contract.party_a == fields.party_a,
                Contract.party_b == fields.party_b,
                Contract.amount == fields.amount,
                Contract.signed_at == fields.signed_at,
            )
            .order_by(Contract.id)
        )
        if twin is not None:
            return twin, f"甲方/乙方/金额/签订日与已有合同「{twin.title}」相同，已并入，避免重复草稿。"
    return None, None


def run_import(db: Session, user: User, uploads: list[tuple[str, bytes]]) -> ImportBatch:
    if not uploads:
        raise ValueError("请至少选择一个 PDF 或 zip")
    for name, data in uploads:
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"{name} 超过 50MB")

    batch = ImportBatch(status="processing", owner_id=user.id)
    db.add(batch)
    db.flush()

    pdfs = _expand_uploads(uploads)
    parsed_rows: list[tuple[ContractFile, ExtractedFields]] = []
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
        parsed = parse_pdf_bytes(data)
        fields = parsed.fields
        row = ContractFile(
            batch_id=batch.id,
            original_name=original_name[:255],
            stored_path=str(stored),
            content_hash=digest,
            source=parsed.source,
            doc_type=fields.doc_type if fields.doc_type != "unknown" else "contract",
            parse_status="failed" if parsed.error and not parsed.text else "done",
            extracted_text=parsed.text or None,
            error_message=parsed.error,
        )
        db.add(row)
        db.flush()
        seen_hashes[digest] = row
        parsed_rows.append((row, fields))
        warnings.extend(fields.warnings)

    contract_piles: dict[str, Contract] = {}
    pile_fields: dict[str, ExtractedFields] = {}
    existing = {
        item.contract_no: item
        for item in db.scalars(select(Contract).where(Contract.contract_no.is_not(None))).all()
        if item.contract_no
    }

    invoice_only: list[tuple[ContractFile, ExtractedFields]] = []

    for row, fields in parsed_rows:
        if fields.doc_type == "invoice" and not fields.contract_no and not fields.party_a:
            invoice_only.append((row, fields))
            continue
        key = identity_key(fields, row.id)
        contract = contract_piles.get(key)
        if contract is None:
            found, reason = _find_existing_contract(db, fields, existing)
            if found is not None:
                contract = found
                if reason:
                    warnings.append(reason)
            else:
                contract = _prepare_contract(fields, row.original_name, user.id, batch.id)
                db.add(contract)
                db.flush()
                numbered = normalize_contract_no(fields.contract_no)
                if numbered:
                    existing[numbered] = contract
            contract_piles[key] = contract
            pile_fields[key] = fields
        else:
            pile_fields[key], _ = merge_extracted_fields(pile_fields[key], fields)
        row.contract_id = contract.id
        row.doc_type = "invoice" if fields.doc_type == "invoice" else "contract"
        touched_ids.append(contract.id)

        for extracted in fields.invoices:
            _add_invoice_draft(db, user, contract, extracted.invoice_code, extracted.invoice_no, extracted.amount)

    contract_list = list(contract_piles.values())
    for row, fields in invoice_only:
        target = contract_list[0] if len(contract_list) == 1 else None
        row.contract_id = target.id if target else None
        row.doc_type = "invoice"
        if target:
            touched_ids.append(target.id)
        for extracted in fields.invoices:
            _add_invoice_draft(db, user, target, extracted.invoice_code, extracted.invoice_no, extracted.amount, user_id=user.id)

    for key, contract in contract_piles.items():
        already = db.scalars(
            select(PaymentSchedule).where(PaymentSchedule.contract_id == contract.id)
        ).first()
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

    batch.warning_text = "\n".join(dict.fromkeys(warnings)) or None
    batch.affected_contract_ids = ",".join(str(item) for item in dict.fromkeys(touched_ids)) or None
    batch.status = "review"
    db.commit()
    db.refresh(batch)
    return batch


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
