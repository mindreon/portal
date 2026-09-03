"""
认证相关接口。

飞书登录怎么走：
1. 前端请求 /feishu/login，后端生成随机 state（防 CSRF），返回飞书授权地址
2. 浏览器跳到飞书，用户同意后飞书带着 code 回到 /feishu/callback
3. 后端换 token、拉用户、写 Cookie，再跳回系统首页
"""

import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import clear_session_cookie, set_session_cookie
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthConfigOut, CurrentUserOut, DevLoginIn, FeishuLoginOut
from app.services.auth import get_or_create_dev_user, upsert_feishu_user
from app.services.feishu import FeishuError, build_authorize_url, exchange_code, fetch_user_info

router = APIRouter(prefix="/auth", tags=["auth"])

# 简单把 state 记在内存里。单进程够用；多副本时再换成 Redis。
_pending_states: set[str] = set()


@router.get("/config", response_model=AuthConfigOut)
def auth_config() -> AuthConfigOut:
    settings = get_settings()
    return AuthConfigOut(
        feishu_enabled=settings.feishu_enabled,
        dev_login_enabled=settings.auth_allow_dev_login,
    )


@router.get("/feishu/login", response_model=FeishuLoginOut)
def feishu_login() -> FeishuLoginOut:
    settings = get_settings()
    if not settings.feishu_enabled:
        raise HTTPException(status_code=400, detail="尚未配置飞书应用，无法使用飞书登录")
    state = secrets.token_urlsafe(24)
    _pending_states.add(state)
    return FeishuLoginOut(authorize_url=build_authorize_url(state))


@router.get("/feishu/callback")
def feishu_callback(
    db: Session = Depends(get_db),
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    settings = get_settings()
    login_url = f"{settings.public_url.rstrip('/')}/login"

    if error:
        return RedirectResponse(f"{login_url}?{urlencode({'error': '飞书授权已取消'})}")
    if not code or not state or state not in _pending_states:
        return RedirectResponse(f"{login_url}?{urlencode({'error': '登录状态无效，请重试'})}")

    _pending_states.discard(state)

    try:
        token = exchange_code(code)
        profile = fetch_user_info(token)
        user = upsert_feishu_user(db, profile)
    except FeishuError as exc:
        return RedirectResponse(f"{login_url}?{urlencode({'error': str(exc)})}")

    response = RedirectResponse(settings.public_url.rstrip("/") + "/")
    set_session_cookie(response, user.id)
    return response


@router.post("/dev-login", response_model=CurrentUserOut)
def dev_login(
    payload: DevLoginIn,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    if not settings.auth_allow_dev_login:
        raise HTTPException(status_code=403, detail="当前环境已关闭开发登录")
    user = get_or_create_dev_user(db, payload.name)
    set_session_cookie(response, user.id)
    return user


@router.get("/me", response_model=CurrentUserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    clear_session_cookie(response)
    return {"ok": True}
