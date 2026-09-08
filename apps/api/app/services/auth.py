"""登录之后怎么落库：按飞书 open_id 找到已有用户，没有就创建。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access import (
    ALL_MODULES,
    count_admins,
    default_modules_for_role,
    dump_modules,
    modules_for_user,
)
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import CurrentUserOut
from app.services.feishu import FeishuProfile


def to_current_user(user: User) -> CurrentUserOut:
    """User 表的 modules 是逗号字符串，返回给前端时拆成数组。"""
    return CurrentUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        role=user.role,
        modules=modules_for_user(user),
    )


def is_feishu_admin(profile: FeishuProfile) -> bool:
    """
    .env 白名单只用来「第一次认出谁是管理员」。
    日常给谁看合同、给谁看发票，改网页上的权限页，不要再改 .env。
    """
    settings = get_settings()
    if profile.open_id and profile.open_id in settings.admin_open_ids:
        return True
    email = (profile.email or "").strip().lower()
    return bool(email and email in settings.admin_emails)


def upsert_feishu_user(db: Session, profile: FeishuProfile) -> User:
    user = db.scalar(select(User).where(User.feishu_open_id == profile.open_id))
    if user is None:
        # 库里还没有管理员时，第一个进来的人当管理员，这样不用先改 .env 也能打开权限页。
        role = "admin" if is_feishu_admin(profile) or count_admins(db) == 0 else "member"
        user = User(
            feishu_open_id=profile.open_id,
            feishu_union_id=profile.union_id,
            name=profile.name,
            email=profile.email,
            avatar_url=profile.avatar_url,
            role=role,
            modules=dump_modules(default_modules_for_role(role)),
        )
        db.add(user)
    else:
        user.name = profile.name
        user.email = profile.email or user.email
        user.avatar_url = profile.avatar_url or user.avatar_url
        if profile.union_id:
            user.feishu_union_id = profile.union_id
        # 已经落库的人：角色和模块以权限页为准，登录不再覆盖。
        # 白名单里的人如果还是普通成员，只升管理员，不改他已经勾好的模块。
        if is_feishu_admin(profile) and user.role != "admin":
            user.role = "admin"
    db.commit()
    db.refresh(user)
    return user


def get_or_create_dev_user(db: Session, name: str) -> User:
    """本地调试用：固定一个 open_id，避免每次登录都新建账号。"""
    open_id = "dev-local-admin"
    user = db.scalar(select(User).where(User.feishu_open_id == open_id))
    if user is None:
        user = User(
            feishu_open_id=open_id,
            name=name,
            email="dev@localhost",
            role="admin",
            modules=dump_modules(list(ALL_MODULES)),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    if user.name != name:
        user.name = name
        db.commit()
        db.refresh(user)
    return user
