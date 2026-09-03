from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.contract import Contract
from app.models.user import User
from app.schemas.contract import CONTRACT_STATUSES, ContractIn, ContractOut

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractOut])
def list_contracts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Contract]:
    return list(db.scalars(select(Contract).order_by(Contract.id.desc())))


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(
    payload: ContractIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Contract:
    if payload.status not in CONTRACT_STATUSES:
        raise HTTPException(status_code=400, detail="合同状态不合法")
    contract = Contract(**payload.model_dump(), owner_id=user.id)
    db.add(contract)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="合同编号已存在") from exc
    db.refresh(contract)
    return contract


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Contract:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.put("/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: int,
    payload: ContractIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Contract:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if payload.status not in CONTRACT_STATUSES:
        raise HTTPException(status_code=400, detail="合同状态不合法")
    for key, value in payload.model_dump().items():
        setattr(contract, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="合同编号已存在") from exc
    db.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.invoices:
        raise HTTPException(status_code=409, detail="请先处理关联发票，再删除合同")
    db.delete(contract)
    db.commit()
