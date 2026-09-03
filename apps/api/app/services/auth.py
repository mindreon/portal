"""登录之后怎么落库：按飞书 open_id 找到已有用户，没有就创建。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.feishu import FeishuProfile


def upsert_feishu_user(db: Session, profile: FeishuProfile) -> User:
    user = db.scalar(select(User).where(User.feishu_open_id == profile.open_id))
    if user is None:
        user = User(
            feishu_open_id=profile.open_id,
            feishu_union_id=profile.union_id,
            name=profile.name,
            email=profile.email,
            avatar_url=profile.avatar_url,
            role="member",
        )
        db.add(user)
    else:
        user.name = profile.name
        user.email = profile.email or user.email
        user.avatar_url = profile.avatar_url or user.avatar_url
        if profile.union_id:
            user.feishu_union_id = profile.union_id
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
