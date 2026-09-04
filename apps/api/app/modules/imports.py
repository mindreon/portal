from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import ContractFile, ImportBatch
from app.models.user import User
from app.modules.contracts import _to_out
from app.schemas.contract import ContractOut, FileOut
from app.services.file_serve import original_file_response
from app.services.imports import run_import

router = APIRouter(prefix="/contracts/imports", tags=["contract-imports"])


class ImportOut(BaseModel):
    id: int
    status: str
    warning_text: str | None = None
    contracts: list[ContractOut]
    files: list[FileOut]


@router.post("", response_model=ImportOut, status_code=201)
def create_import(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ImportOut:
    uploads: list[tuple[str, bytes]] = []
    for item in files:
        uploads.append((item.filename or "upload.pdf", item.file.read()))
    try:
        batch = run_import(db, user, uploads)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _batch_out(db, batch.id)


@router.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    return _file_response(db, file_id, inline=False)


@router.get("/files/{file_id}/preview")
def preview_file(
    file_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    return _file_response(db, file_id, inline=True)


@router.get("/{batch_id}", response_model=ImportOut)
def get_import(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImportOut:
    return _batch_out(db, batch_id)


@router.post("/{batch_id}/confirm", response_model=ImportOut)
def confirm_import(
    batch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImportOut:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="导入批次不存在")
    batch.status = "confirmed"
    db.commit()
    return _batch_out(db, batch_id)


def _file_response(db: Session, file_id: int, *, inline: bool) -> FileResponse:
    row = db.get(ContractFile, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="附件不存在")
    return original_file_response(row.stored_path, row.original_name, inline=inline)


def _parse_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out


def _batch_out(db: Session, batch_id: int) -> ImportOut:
    from app.models.contract import Contract

    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="导入批次不存在")
    affected = _parse_ids(batch.affected_contract_ids)
    query = select(Contract).options(selectinload(Contract.invoices), selectinload(Contract.collections)).order_by(Contract.id)
    if affected:
        contracts = db.scalars(query.where(Contract.id.in_(affected))).all()
    else:
        contracts = db.scalars(query.where(Contract.import_batch_id == batch_id)).all()
    files = list(db.scalars(select(ContractFile).where(ContractFile.batch_id == batch_id)))
    return ImportOut(
        id=batch.id,
        status=batch.status,
        warning_text=batch.warning_text,
        contracts=[_to_out(item) for item in contracts],
        files=[FileOut.model_validate(item) for item in files],
    )
