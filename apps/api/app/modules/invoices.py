from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.invoice import INVOICE_STATUSES, InvoiceIn, InvoiceOut

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Invoice]:
    return list(db.scalars(select(Invoice).order_by(Invoice.id.desc())))


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
