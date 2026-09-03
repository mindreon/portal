from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import TokenError, parse_session_token
from app.db.session import get_db
from app.models.user import User

# FastAPI 的 Cookie(alias=...) 必须在定义依赖时就确定名字
COOKIE_NAME = get_settings().cookie_name


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User:
    """从登录 Cookie 里解析出当前用户。没登录就返回 401。"""
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        user_id = parse_session_token(session_token)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不可用")
    return user
