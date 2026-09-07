"""登录之后怎么落库：按飞书 open_id 找到已有用户，没有就创建。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.access import modules_for_role
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import CurrentUserOut
from app.services.feishu import FeishuProfile


def to_current_user(user: User) -> CurrentUserOut:
    """User 表没有 modules 列，返回给前端时按角色现算。"""
    return CurrentUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        role=user.role,
        modules=modules_for_role(user.role),
    )


def is_feishu_admin(profile: FeishuProfile) -> bool:
    """
    飞书只告诉我们「这人是谁」，管不了菜单。
    管理员名单写在自己的 .env 里：企业邮箱或 open_id。
    """
    settings = get_settings()
    if profile.open_id and profile.open_id in settings.admin_open_ids:
        return True
    email = (profile.email or "").strip().lower()
    return bool(email and email in settings.admin_emails)


def upsert_feishu_user(db: Session, profile: FeishuProfile) -> User:
    role = "admin" if is_feishu_admin(profile) else "member"
    user = db.scalar(select(User).where(User.feishu_open_id == profile.open_id))
    if user is None:
        user = User(
            feishu_open_id=profile.open_id,
            feishu_union_id=profile.union_id,
            name=profile.name,
            email=profile.email,
            avatar_url=profile.avatar_url,
            role=role,
        )
        db.add(user)
    else:
        user.name = profile.name
        user.email = profile.email or user.email
        user.avatar_url = profile.avatar_url or user.avatar_url
        if profile.union_id:
            user.feishu_union_id = profile.union_id
        # 每次登录按白名单同步，名单里去掉的人下次进来就变回普通成员。
        user.role = role
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
