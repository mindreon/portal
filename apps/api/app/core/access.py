"""
模块权限：登录只证明「你是公司的人」，权限证明「你能进哪一间房间」。

飞书开放平台只能控制「谁能打开这个应用」。它不会按页面发菜单。
合同、发票各自要不要给某人看，必须由我们自己的系统决定。

当前规则故意做得很小：
- 管理员：合同 + 发票
- 普通成员：只有发票（以及以后默认对全员开放的模块）

以后若要按部门、按人勾选，再做成独立的权限管理页；现在用角色就够用。
"""

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.user import User

# 系统里所有业务模块的 id，必须和前端 apps/web/src/lib/modules.ts 里的 id 对齐。
ALL_MODULES = ("contracts", "invoices")

# 每个角色能进哪些模块。新模块默认先给管理员，确认全员可用后再加进 member。
ROLE_MODULES: dict[str, tuple[str, ...]] = {
    "admin": ALL_MODULES,
    "member": ("invoices",),
}


def modules_for_role(role: str) -> list[str]:
    """根据角色算出菜单。未知角色按最严的「普通成员」处理。"""
    return list(ROLE_MODULES.get(role, ROLE_MODULES["member"]))


def can_access_module(user: User, module_id: str) -> bool:
    return module_id in modules_for_role(user.role)


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
