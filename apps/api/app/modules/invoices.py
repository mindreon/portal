from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.access import require_module
from app.core.deps import get_current_user
from app.core.paging import clamp_page
from app.db.session import get_db
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.invoice import (
    INVOICE_STATUSES,
    InvoiceIn,
    InvoiceOut,
    InvoiceSummary,
    InvoiceUploadOut,
)
from app.schemas.page import PageOut
from app.services.file_serve import original_file_response
from app.services.invoice_files import (
    MAX_FILE_BYTES,
    MAX_FILE_MB,
    is_pdf,
    remove_stored_file,
    sha256,
    write_invoice_pdf,
)

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    dependencies=[Depends(require_module("invoices"))],
)


def _invoice_text_filter(text: str | None) -> ColumnElement[bool] | None:
    if not text or not text.strip():
        return None
    needle = f"%{text.strip().lower()}%"
    return or_(
        func.lower(Invoice.title).like(needle),
        func.lower(Invoice.invoice_no).like(needle),
        func.lower(func.coalesce(Invoice.invoice_code, "")).like(needle),
        func.lower(Invoice.counterparty).like(needle),
        func.lower(func.coalesce(Invoice.original_name, "")).like(needle),
    )


def _filtered_invoices(q: str | None, contract_id: int | None) -> Select[tuple[Invoice]]:
    query = select(Invoice)
    cond = _invoice_text_filter(q)
    if cond is not None:
        query = query.where(cond)
    if contract_id is not None:
        query = query.where(Invoice.contract_id == contract_id)
    return query


def _get_invoice(db: Session, invoice_id: int) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="发票不存在")
    return invoice


def _contract_or_400(db: Session, contract_id: int | None) -> Contract | None:
    if contract_id is None:
        return None
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=400, detail="关联的合同不存在")
    return contract


@router.get("", response_model=PageOut[InvoiceOut])
def list_invoices(
    q: str | None = None,
    contract_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PageOut[InvoiceOut]:
    page, page_size, offset = clamp_page(page, page_size)
    filtered = _filtered_invoices(q, contract_id)
    total = db.scalar(select(func.count()).select_from(filtered.subquery())) or 0
    rows = list(db.scalars(filtered.order_by(Invoice.id.desc()).offset(offset).limit(page_size)))
    return PageOut(items=rows, total=total, page=page, page_size=page_size)


@router.get("/summary", response_model=InvoiceSummary)
def invoice_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> InvoiceSummary:
    count = db.scalar(select(func.count()).select_from(Invoice)) or 0
    issued_count = db.scalar(select(func.count()).select_from(Invoice).where(Invoice.status == "issued")) or 0
    return InvoiceSummary(count=count, issued_count=issued_count)


@router.post("/upload", response_model=InvoiceUploadOut, status_code=201)
def upload_invoices(
    files: list[UploadFile] = File(...),
    contract_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvoiceUploadOut:
    """合同页或发票页都可以一次传多张 PDF。每张 PDF 变成一条发票草稿。"""
    if not files:
        raise HTTPException(status_code=400, detail="请选择至少一张发票 PDF")
    contract = _contract_or_400(db, contract_id)
    created: list[Invoice] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for item in files:
        original_name = item.filename or "invoice.pdf"
        data = item.file.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(status_code=400, detail=f"{original_name} 超过 {MAX_FILE_MB}MB")
        if not is_pdf(original_name, data):
            warnings.append(f"已跳过非 PDF：{original_name}")
            continue
        digest = sha256(data)
        if digest in seen:
            warnings.append(f"{original_name} 和这次一起传的另一份内容相同，已跳过。")
            continue
        existing = db.scalar(select(Invoice).where(Invoice.content_hash == digest))
        if existing is not None:
            warnings.append(f"{original_name} 已经上传过，已跳过，避免重复记录。")
            continue
        seen.add(digest)
        invoice = _draft_from_pdf(db, user, contract, original_name, digest)
        db.add(invoice)
        db.flush()
        stored = write_invoice_pdf(invoice.id, original_name, data)
        invoice.stored_path = str(stored)
        created.append(invoice)

    if not created and warnings:
        raise HTTPException(status_code=400, detail="；".join(warnings))
    if not created:
        raise HTTPException(status_code=400, detail="请选择至少一张发票 PDF")

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        for invoice in created:
            remove_stored_file(invoice.stored_path)
        raise HTTPException(status_code=409, detail="发票编号已存在") from exc
    for invoice in created:
        db.refresh(invoice)
    return InvoiceUploadOut(items=created, warning_text="\n".join(warnings) or None)


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(
    payload: InvoiceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Invoice:
    _validate(db, payload)
    invoice = Invoice(**payload.model_dump(), owner_id=user.id)
    db.add(invoice)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="发票编号已存在") from exc
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Invoice:
    return _get_invoice(db, invoice_id)


@router.get("/{invoice_id}/preview", response_model=None)
def preview_invoice_file(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse | Response:
    return _file_response(db, invoice_id, request, inline=True)


@router.get("/{invoice_id}/download", response_model=None)
def download_invoice_file(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse | Response:
    return _file_response(db, invoice_id, request, inline=False)


@router.post("/{invoice_id}/file", response_model=InvoiceOut)
def attach_invoice_file(
    invoice_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Invoice:
    """已经填过要素的发票，后补一张 PDF；有旧文件会换掉。"""
    invoice = _get_invoice(db, invoice_id)
    original_name = file.filename or "invoice.pdf"
    data = file.file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail=f"{original_name} 超过 {MAX_FILE_MB}MB")
    if not is_pdf(original_name, data):
        raise HTTPException(status_code=400, detail="只接受 PDF 发票")
    digest = sha256(data)
    existing = db.scalar(select(Invoice).where(Invoice.content_hash == digest, Invoice.id != invoice.id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="这份 PDF 已经上传过")
    old_path = invoice.stored_path
    stored = write_invoice_pdf(invoice.id, original_name, data)
    invoice.original_name = original_name[:255]
    invoice.stored_path = str(stored)
    invoice.content_hash = digest
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        remove_stored_file(str(stored))
        raise HTTPException(status_code=409, detail="这份 PDF 已经上传过") from exc
    remove_stored_file(old_path)
    db.refresh(invoice)
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    payload: InvoiceIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Invoice:
    invoice = _get_invoice(db, invoice_id)
    _validate(db, payload)
    for key, value in payload.model_dump().items():
        setattr(invoice, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="发票编号已存在") from exc
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    invoice = _get_invoice(db, invoice_id)
    stored_path = invoice.stored_path
    db.delete(invoice)
    db.commit()
    remove_stored_file(stored_path)


def _file_response(db: Session, invoice_id: int, request: Request, *, inline: bool) -> FileResponse | Response:
    invoice = _get_invoice(db, invoice_id)
    if not invoice.stored_path or not Path(invoice.stored_path).is_file():
        raise HTTPException(status_code=404, detail="这张发票还没有 PDF")
    return original_file_response(
        invoice.stored_path,
        invoice.original_name or "invoice.pdf",
        inline=inline,
        content_hash=invoice.content_hash,
        request=request,
    )


def _draft_from_pdf(
    db: Session,
    user: User,
    contract: Contract | None,
    original_name: str,
    digest: str,
) -> Invoice:
    title = Path(original_name.replace("\\", "/")).stem or "发票"
    number = _unique_upload_no(db, digest)
    return Invoice(
        title=title[:255],
        invoice_no=number,
        counterparty=(contract.counterparty if contract else "") or "（待填写）",
        amount=0,
        tax_amount=0,
        status="draft",
        contract_id=contract.id if contract else None,
        owner_id=user.id,
        original_name=original_name[:255],
        content_hash=digest,
    )


def _unique_upload_no(db: Session, digest: str) -> str:
    """上传时还没有发票号码，用文件指纹占位，保存后可以改成真正的号码。"""
    for length in (10, 12, 16, 24, 32, 64):
        number = f"UP-{digest[:length].upper()}"
        exists = db.scalar(select(Invoice.id).where(Invoice.invoice_no == number))
        if exists is None:
            return number
    return f"UP-{digest.upper()}"


def _validate(db: Session, payload: InvoiceIn) -> None:
    if payload.status not in INVOICE_STATUSES:
        raise HTTPException(status_code=400, detail="发票状态不合法")
    if payload.contract_id is not None and db.get(Contract, payload.contract_id) is None:
        raise HTTPException(status_code=400, detail="关联的合同不存在")
    if payload.schedule_id is not None:
        from app.models.payment import PaymentSchedule

        schedule = db.get(PaymentSchedule, payload.schedule_id)
        if schedule is None:
            raise HTTPException(status_code=400, detail="回款期次不存在")
        if payload.contract_id and schedule.contract_id != payload.contract_id:
            raise HTTPException(status_code=400, detail="期次不属于这份合同")
