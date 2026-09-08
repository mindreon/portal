from fastapi import APIRouter, Depends, HTTPException
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
from app.schemas.invoice import INVOICE_STATUSES, InvoiceIn, InvoiceOut, InvoiceSummary
from app.schemas.page import PageOut

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
    )


def _filtered_invoices(q: str | None, contract_id: int | None) -> Select[tuple[Invoice]]:
    query = select(Invoice)
    cond = _invoice_text_filter(q)
    if cond is not None:
        query = query.where(cond)
    if contract_id is not None:
        query = query.where(Invoice.contract_id == contract_id)
    return query


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
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="发票不存在")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    payload: InvoiceIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="发票不存在")
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
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="发票不存在")
    db.delete(invoice)
    db.commit()


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
