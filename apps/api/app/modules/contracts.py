from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.core.access import require_module
from app.core.deps import get_current_user
from app.core.paging import clamp_page
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
    CollectionPageOut,
    CollectionRow,
    ContractIn,
    ContractOut,
    ContractSummary,
    FileOut,
    ScheduleIn,
    ScheduleOut,
)
from app.schemas.page import PageOut
from app.services.extract import (
    OUR_COMPANY_MARKERS,
    derive_account_kind,
    derive_counterparty,
    derive_our_role,
    normalize_contract_no,
)

router = APIRouter(
    prefix="/contracts",
    tags=["contracts"],
    dependencies=[Depends(require_module("contracts"))],
)


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
    return payload.model_copy(
        update={
            "billed_amount": billed,
            "collected_amount": collected,
            "account_kind": derive_account_kind(contract.party_a, contract.party_b, contract.our_role),
        }
    )


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
    inferred_role = derive_our_role(data["party_a"], data["party_b"])
    if inferred_role:
        data["our_role"] = inferred_role
    derived = derive_counterparty(data["party_a"], data["party_b"], data["our_role"])
    if derived:
        data["counterparty"] = derived
    elif not data["counterparty"]:
        data["counterparty"] = "（待填写）"
    for key, value in data.items():
        setattr(contract, key, value)


def _contract_text_filter(text: str | None) -> ColumnElement[bool] | None:
    """按关键字搜编号、名称、甲乙方、文件名。搜索框和列表筛选共用。"""
    if not text or not text.strip():
        return None
    needle = f"%{text.strip().lower()}%"
    return or_(
        func.lower(func.coalesce(Contract.contract_no, "")).like(needle),
        func.lower(Contract.party_a).like(needle),
        func.lower(Contract.party_b).like(needle),
        func.lower(Contract.counterparty).like(needle),
        func.lower(Contract.subject_name).like(needle),
        func.lower(Contract.title).like(needle),
        Contract.id.in_(
            select(ContractFile.contract_id).where(
                ContractFile.contract_id.is_not(None),
                func.lower(ContractFile.original_name).like(needle),
            )
        ),
    )


def _account_kind_sql(kind: str | None) -> ColumnElement[bool] | None:
    """
    应收账款：我方是乙方；应付账款：我方是甲方。
    已写入 our_role 的合同直接按角色分；老数据角色为空时，再用名称里有没有「迈能同行」兜底。
    """
    if kind not in {"receivable", "payable"}:
        return None
    marker = OUR_COMPANY_MARKERS[0]
    empty_role = func.coalesce(Contract.our_role, "") == ""
    if kind == "receivable":
        return or_(
            Contract.our_role == "party_b",
            and_(
                empty_role,
                Contract.party_b.contains(marker),
                ~Contract.party_a.contains(marker),
            ),
        )
    return or_(
        Contract.our_role == "party_a",
        and_(
            empty_role,
            Contract.party_a.contains(marker),
            ~Contract.party_b.contains(marker),
        ),
    )


def _as_money(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _outstanding(total: Decimal, settled: Decimal) -> Decimal:
    return max(Decimal("0"), total - settled)


def _sum_contract_amount(db: Session, kind: str) -> Decimal:
    cond = _account_kind_sql(kind)
    if cond is None:
        return Decimal("0")
    return _as_money(db.scalar(select(func.coalesce(func.sum(Contract.amount), 0)).where(cond)))


def _sum_settled_amount(db: Session, kind: str) -> Decimal:
    cond = _account_kind_sql(kind)
    if cond is None:
        return Decimal("0")
    return _as_money(
        db.scalar(
            select(func.coalesce(func.sum(Collection.amount), 0))
            .join(Contract, Collection.contract_id == Contract.id)
            .where(cond)
        )
    )


def _filtered_contracts(
    q: str | None,
    party: str | None,
    date_from: date | None,
    date_to: date | None,
    account_kind: str | None = None,
) -> Select[tuple[Contract]]:
    query = select(Contract)
    for text in (q, party):
        cond = _contract_text_filter(text)
        if cond is not None:
            query = query.where(cond)
    kind_cond = _account_kind_sql(account_kind)
    if kind_cond is not None:
        query = query.where(kind_cond)
    effective = func.coalesce(Contract.signed_at, Contract.start_date)
    if date_from is not None:
        query = query.where(effective >= date_from)
    if date_to is not None:
        query = query.where(effective <= date_to)
    return query


def _payment_text_filter(text: str | None) -> ColumnElement[bool] | None:
    if not text or not text.strip():
        return None
    needle = f"%{text.strip().lower()}%"
    return or_(
        func.lower(Contract.title).like(needle),
        func.lower(func.coalesce(Contract.contract_no, "")).like(needle),
        func.lower(Contract.party_a).like(needle),
        func.lower(Contract.party_b).like(needle),
        func.lower(Contract.counterparty).like(needle),
    )


def _collection_row(item: Collection) -> CollectionRow:
    contract = item.contract
    party_a = contract.party_a if contract else ""
    party_b = contract.party_b if contract else ""
    our_role = contract.our_role if contract else ""
    return CollectionRow(
        id=item.id,
        amount=item.amount,
        received_at=item.received_at,
        notes=item.notes,
        schedule_id=item.schedule_id,
        contract_id=item.contract_id,
        contract_title=contract.title if contract else "",
        contract_no=contract.contract_no if contract else None,
        party_a=party_a,
        party_b=party_b,
        schedule_name=item.schedule.name if item.schedule else None,
        account_kind=derive_account_kind(party_a, party_b, our_role),
    )


def _collections_stmt(q: str | None, kind: str | None = None) -> Select[tuple[Collection]]:
    query = select(Collection).join(Contract, Collection.contract_id == Contract.id)
    cond = _payment_text_filter(q)
    if cond is not None:
        query = query.where(cond)
    kind_cond = _account_kind_sql(kind)
    if kind_cond is not None:
        query = query.where(kind_cond)
    return query


def _collection_count(db: Session, stmt: Select[tuple[Collection]]) -> int:
    return db.scalar(select(func.count()).select_from(stmt.with_only_columns(Collection.id).subquery())) or 0


def _collection_sum(db: Session, stmt: Select[tuple[Collection]]) -> Decimal:
    return _as_money(db.scalar(stmt.with_only_columns(func.coalesce(func.sum(Collection.amount), 0)).order_by(None)))


@router.get("", response_model=PageOut[ContractOut])
def list_contracts(
    q: str | None = None,
    party: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    account_kind: str | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PageOut[ContractOut]:
    page, page_size, offset = clamp_page(page, page_size)
    filtered = _filtered_contracts(q, party, date_from, date_to, account_kind)
    total = db.scalar(select(func.count()).select_from(filtered.subquery())) or 0
    rows = db.scalars(
        filtered.options(
            selectinload(Contract.invoices),
            selectinload(Contract.collections),
            selectinload(Contract.files),
        )
        .order_by(Contract.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return PageOut(
        items=[_to_out(item) for item in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=ContractSummary)
def contract_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractSummary:
    count = db.scalar(select(func.count()).select_from(Contract)) or 0
    active_count = db.scalar(select(func.count()).select_from(Contract).where(Contract.status == "active")) or 0
    total = _as_money(db.scalar(select(func.coalesce(func.sum(Contract.amount), 0))))
    collected = _as_money(db.scalar(select(func.coalesce(func.sum(Collection.amount), 0))))
    parsing_count = db.scalar(
        select(func.count(func.distinct(ContractFile.contract_id))).where(
            ContractFile.contract_id.is_not(None),
            ContractFile.parse_status.in_(("pending", "processing")),
        )
    ) or 0
    receivable_amount = _sum_contract_amount(db, "receivable")
    receivable_collected = _sum_settled_amount(db, "receivable")
    payable_amount = _sum_contract_amount(db, "payable")
    payable_paid = _sum_settled_amount(db, "payable")
    receivable_outstanding = _outstanding(receivable_amount, receivable_collected)
    payable_outstanding = _outstanding(payable_amount, payable_paid)
    return ContractSummary(
        count=count,
        active_count=active_count,
        total_amount=total,
        collected_amount=collected,
        outstanding_amount=receivable_outstanding,
        parsing_count=parsing_count,
        receivable_amount=receivable_amount,
        receivable_collected=receivable_collected,
        receivable_outstanding=receivable_outstanding,
        payable_amount=payable_amount,
        payable_paid=payable_paid,
        payable_outstanding=payable_outstanding,
    )


@router.get("/payments", response_model=CollectionPageOut)
def list_all_payments(
    q: str | None = None,
    kind: str | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CollectionPageOut:
    page, page_size, offset = clamp_page(page, page_size)
    listed = _collections_stmt(q, kind)
    receivable = _collections_stmt(q, "receivable")
    payable = _collections_stmt(q, "payable")
    total = _collection_count(db, listed)
    total_amount = _collection_sum(db, listed)
    rows = db.scalars(
        listed.options(selectinload(Collection.contract), selectinload(Collection.schedule))
        .order_by(Collection.received_at.desc(), Collection.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return CollectionPageOut(
        items=[_collection_row(item) for item in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_amount=total_amount,
        receivable_count=_collection_count(db, receivable),
        receivable_amount=_collection_sum(db, receivable),
        payable_count=_collection_count(db, payable),
        payable_amount=_collection_sum(db, payable),
    )


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
