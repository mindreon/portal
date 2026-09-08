"""
模块权限：登录只证明「你是公司的人」，权限证明「你能进哪一间房间」。

飞书开放平台只能控制「谁能打开这个应用」。它不会按页面发菜单。
合同、发票各自要不要给某人看，记在 users.modules 里，管理员在网页上勾选。

「管理员」是另一件事：只有管理员能打开权限页，给别人勾模块。
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.models.user import User

# 系统里所有业务模块的 id，必须和前端 apps/web/src/lib/modules.ts 里的 id 对齐。
ALL_MODULES = ("contracts", "invoices")

# 新建账号时的默认套餐。勾选之后以数据库为准，不再走这张表。
ROLE_MODULES: dict[str, tuple[str, ...]] = {
    "admin": ALL_MODULES,
    "member": ("invoices",),
}


def parse_modules(raw: str | None) -> list[str]:
    """把库里的逗号分隔字符串变成模块 id 列表，丢掉不认识的名字。"""
    if not raw:
        return []
    wanted = {part.strip() for part in raw.split(",") if part.strip()}
    return [item for item in ALL_MODULES if item in wanted]


def dump_modules(modules: list[str]) -> str:
    """保存时按固定顺序写，避免每次勾选顺序不一样。"""
    wanted = set(modules)
    unknown = wanted - set(ALL_MODULES)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不认识的模块：{', '.join(sorted(unknown))}",
        )
    return ",".join(item for item in ALL_MODULES if item in wanted)


def default_modules_for_role(role: str) -> list[str]:
    return list(ROLE_MODULES.get(role, ROLE_MODULES["member"]))


def modules_for_role(role: str) -> list[str]:
    """兼容旧测试和还没写 modules 列的行。"""
    return default_modules_for_role(role)


def modules_for_user(user: User) -> list[str]:
    """当前这个人菜单上有哪些房间。空字符串表示一个都不给。"""
    if user.modules is None:
        return default_modules_for_role(user.role)
    return parse_modules(user.modules)


def can_access_module(user: User, module_id: str) -> bool:
    return module_id in modules_for_user(user)


def require_module(module_id: str):
    """
    FastAPI 依赖工厂。写成 Depends(require_module("contracts"))，
    没权限时直接 403，前端即使藏了菜单，接口也进不去。
    """

    def _checker(user: User = Depends(get_current_user)) -> User:
        if not can_access_module(user, module_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有访问该模块的权限",
            )
        return user

    return _checker


def require_admin(user: User = Depends(get_current_user)) -> User:
    """只有管理员能打开权限页、改别人的模块。"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理权限",
        )
    return user


def count_admins(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User).where(User.role == "admin")) or 0)
