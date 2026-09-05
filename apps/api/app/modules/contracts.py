from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.contract import Contract
from app.models.document import ContractFile
from app.models.payment import Collection, PaymentSchedule
from app.models.user import User
from app.schemas.contract import (
    CONTRACT_STATUSES,
    OUR_ROLES,
    CollectionIn,
    CollectionOut,
    CollectionRow,
    ContractIn,
    ContractOut,
    ContractSummary,
    FileOut,
    ScheduleIn,
    ScheduleOut,
)
from app.services.extract import derive_counterparty, normalize_contract_no

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _to_out(contract: Contract) -> ContractOut:
    billed = Decimal("0") + sum(
        (item.amount or Decimal("0") for item in contract.invoices if item.status != "void"),
        Decimal("0"),
    )
    collected = Decimal("0") + sum(
        (item.amount or Decimal("0") for item in contract.collections),
        Decimal("0"),
    )
    payload = ContractOut.model_validate(contract)
    return payload.model_copy(update={"billed_amount": billed, "collected_amount": collected})


def _load(db: Session, contract_id: int) -> Contract | None:
    return db.scalars(
        select(Contract)
        .where(Contract.id == contract_id)
        .options(
            selectinload(Contract.invoices),
            selectinload(Contract.collections),
            selectinload(Contract.files),
            selectinload(Contract.schedules),
        )
    ).first()


def _schedule_for_contract(db: Session, contract_id: int, schedule_id: int | None) -> PaymentSchedule | None:
    """登记到账时可以挂到某一期；必须是这份合同自己的期次。"""
    if schedule_id is None:
        return None
    row = db.get(PaymentSchedule, schedule_id)
    if row is None or row.contract_id != contract_id:
        raise HTTPException(status_code=400, detail="回款期次不存在")
    return row


def _apply(contract: Contract, payload: ContractIn) -> None:
    if payload.status not in CONTRACT_STATUSES:
        raise HTTPException(status_code=400, detail="合同状态不合法")
    if payload.our_role not in OUR_ROLES:
        raise HTTPException(status_code=400, detail="己方角色不合法")
    data = payload.model_dump()
    data["contract_no"] = normalize_contract_no(data.get("contract_no"))
    if not data["party_a"] and not data["party_b"] and data["counterparty"]:
        data["party_b"] = data["counterparty"]
    derived = derive_counterparty(data["party_a"], data["party_b"], data["our_role"])
    if derived:
        data["counterparty"] = derived
    elif not data["counterparty"]:
        data["counterparty"] = "（待填写）"
    for key, value in data.items():
        setattr(contract, key, value)


@router.get("", response_model=list[ContractOut])
def list_contracts(
    party: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ContractOut]:
    query = select(Contract).options(selectinload(Contract.invoices), selectinload(Contract.collections))
    if party and party.strip():
        needle = f"%{party.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Contract.party_a).like(needle),
                func.lower(Contract.party_b).like(needle),
                func.lower(Contract.counterparty).like(needle),
                func.lower(Contract.title).like(needle),
            )
        )
    effective = func.coalesce(Contract.signed_at, Contract.start_date)
    if date_from is not None:
        query = query.where(effective >= date_from)
    if date_to is not None:
        query = query.where(effective <= date_to)
    rows = db.scalars(query.order_by(Contract.id.desc())).all()
    return [_to_out(item) for item in rows]


@router.get("/summary", response_model=ContractSummary)
def contract_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractSummary:
    rows = db.scalars(
        select(Contract).options(selectinload(Contract.invoices), selectinload(Contract.collections))
    ).all()
    total = sum((item.amount or Decimal("0") for item in rows), Decimal("0"))
    collected = sum(
        (sum((c.amount or Decimal("0") for c in item.collections), Decimal("0")) for item in rows),
        Decimal("0"),
    )
    return ContractSummary(
        count=len(rows),
        active_count=len([item for item in rows if item.status == "active"]),
        total_amount=total,
        collected_amount=collected,
        outstanding_amount=max(Decimal("0"), total - collected),
    )


@router.get("/payments", response_model=list[CollectionRow])
def list_all_payments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CollectionRow]:
    rows = db.scalars(
        select(Collection)
        .options(selectinload(Collection.contract), selectinload(Collection.schedule))
        .order_by(Collection.received_at.desc(), Collection.id.desc())
    ).all()
    result: list[CollectionRow] = []
    for item in rows:
        contract = item.contract
        result.append(
            CollectionRow(
                id=item.id,
                amount=item.amount,
                received_at=item.received_at,
                notes=item.notes,
                schedule_id=item.schedule_id,
                contract_id=item.contract_id,
                contract_title=contract.title if contract else "",
                contract_no=contract.contract_no if contract else None,
                party_a=contract.party_a if contract else "",
                party_b=contract.party_b if contract else "",
                schedule_name=item.schedule.name if item.schedule else None,
            )
        )
    return result


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(
    payload: ContractIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContractOut:
    contract = Contract(owner_id=user.id)
    _apply(contract, payload)
    db.add(contract)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="合同编号已存在") from exc
    loaded = _load(db, contract.id)
    assert loaded is not None
    return _to_out(loaded)


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractOut:
    contract = _load(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    return _to_out(contract)


@router.put("/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: int,
    payload: ContractIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractOut:
    contract = _load(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    _apply(contract, payload)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="合同编号已存在") from exc
    loaded = _load(db, contract_id)
    assert loaded is not None
    return _to_out(loaded)


@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    contract = _load(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.invoices:
        raise HTTPException(status_code=409, detail="请先处理关联发票，再删除合同")
    for item in contract.files:
        Path(item.stored_path).unlink(missing_ok=True)
        db.delete(item)
    for item in contract.collections:
        db.delete(item)
    for item in contract.schedules:
        db.delete(item)
    db.delete(contract)
    db.commit()


@router.get("/{contract_id}/files", response_model=list[FileOut])
def list_files(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ContractFile]:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    return list(db.scalars(select(ContractFile).where(ContractFile.contract_id == contract_id)))


@router.get("/{contract_id}/schedules", response_model=list[ScheduleOut])
def list_schedules(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ScheduleOut]:
    if db.get(Contract, contract_id) is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    rows = list(
        db.scalars(
            select(PaymentSchedule)
            .where(PaymentSchedule.contract_id == contract_id)
            .options(selectinload(PaymentSchedule.collections))
            .order_by(PaymentSchedule.period_no)
        )
    )
    return [
        ScheduleOut.model_validate(item).model_copy(
            update={"collected_amount": sum((c.amount or Decimal("0") for c in item.collections), Decimal("0"))}
        )
        for item in rows
    ]


@router.post("/{contract_id}/schedules", response_model=ScheduleOut, status_code=201)
def add_schedule(
    contract_id: int,
    payload: ScheduleIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ScheduleOut:
    if db.get(Contract, contract_id) is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    count = len(list(db.scalars(select(PaymentSchedule).where(PaymentSchedule.contract_id == contract_id))))
    row = PaymentSchedule(contract_id=contract_id, period_no=count + 1, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ScheduleOut.model_validate(row).model_copy(update={"collected_amount": Decimal("0")})


@router.put("/{contract_id}/schedules/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    contract_id: int,
    schedule_id: int,
    payload: ScheduleIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ScheduleOut:
    row = db.get(PaymentSchedule, schedule_id)
    if row is None or row.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="回款计划不存在")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    collected = sum((item.amount or Decimal("0") for item in row.collections), Decimal("0"))
    return ScheduleOut.model_validate(row).model_copy(update={"collected_amount": collected})


@router.delete("/{contract_id}/schedules/{schedule_id}", status_code=204)
def delete_schedule(
    contract_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    row = db.get(PaymentSchedule, schedule_id)
    if row is None or row.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="回款计划不存在")
    if row.invoices or row.collections:
        raise HTTPException(status_code=409, detail="该期已有发票或回款，不能直接删除")
    db.delete(row)
    db.commit()


@router.get("/{contract_id}/collections", response_model=list[CollectionOut])
def list_collections(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Collection]:
    if db.get(Contract, contract_id) is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    return list(
        db.scalars(
            select(Collection).where(Collection.contract_id == contract_id).order_by(Collection.id.desc())
        )
    )


@router.post("/{contract_id}/collections", response_model=CollectionOut, status_code=201)
def add_collection(
    contract_id: int,
    payload: CollectionIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Collection:
    if db.get(Contract, contract_id) is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    _schedule_for_contract(db, contract_id, payload.schedule_id)
    row = Collection(contract_id=contract_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{contract_id}/collections/{collection_id}", response_model=CollectionOut)
def update_collection(
    contract_id: int,
    collection_id: int,
    payload: CollectionIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Collection:
    row = db.get(Collection, collection_id)
    if row is None or row.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="回款记录不存在")
    _schedule_for_contract(db, contract_id, payload.schedule_id)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{contract_id}/collections/{collection_id}", status_code=204)
def delete_collection(
    contract_id: int,
    collection_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    row = db.get(Collection, collection_id)
    if row is None or row.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="回款记录不存在")
    db.delete(row)
    db.commit()


@router.post("/{contract_id}/merge/{source_id}", response_model=ContractOut)
def merge_contracts(
    contract_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractOut:
    """把另一份草稿并进来。没编号的扫描件核对后可以用。"""
    if contract_id == source_id:
        raise HTTPException(status_code=400, detail="不能并入自己")
    target = _load(db, contract_id)
    source = _load(db, source_id)
    if target is None or source is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    for item in source.files:
        item.contract_id = target.id
    for item in source.invoices:
        item.contract_id = target.id
    for item in source.schedules:
        item.contract_id = target.id
    for item in source.collections:
        item.contract_id = target.id
    db.delete(source)
    db.commit()
    loaded = _load(db, contract_id)
    assert loaded is not None
    return _to_out(loaded)
