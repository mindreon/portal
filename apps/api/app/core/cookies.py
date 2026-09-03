from fastapi import Response

from app.core.config import get_settings
from app.core.security import create_session_token


def set_session_cookie(response: Response, user_id: int) -> None:
    settings = get_settings()
    token = create_session_token(user_id)
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_hours * 3600,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.cookie_name, path="/")
