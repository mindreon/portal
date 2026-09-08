"""
人员权限：管理员在网页上给每个人勾选能进的模块。

同事必须先用飞书（或开发登录）进来一次，才会出现在这张表里。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access import count_admins, dump_modules, modules_for_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserPatchIn

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


def _to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        modules=modules_for_user(user),
    )


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    rows = db.scalars(select(User).order_by(User.id.asc())).all()
    return [_to_out(item) for item in rows]


@router.patch("/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    payload: UserPatchIn,
    db: Session = Depends(get_db),
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if payload.role is not None:
        if payload.role not in {"admin", "member"}:
            raise HTTPException(status_code=400, detail="角色不合法")
        # 至少留一个管理员，否则谁都进不了权限页。
        if user.role == "admin" and payload.role != "admin" and count_admins(db) <= 1:
            raise HTTPException(status_code=400, detail="至少需要保留一名管理员")
        user.role = payload.role

    if payload.modules is not None:
        user.modules = dump_modules(payload.modules)

    db.commit()
    db.refresh(user)
    return _to_out(user)
