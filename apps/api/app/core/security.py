"""
会话令牌：用 JWT 把「谁登录了」写进 HttpOnly Cookie。

为什么不用把飞书的 user_access_token 直接当登录凭证？
- 飞书 token 会过期，而且权限范围是飞书 OpenAPI，不是我们自己的业务。
- 我们自己签发短期 JWT，业务接口只认自己的用户 id。
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings


class TokenError(Exception):
    """令牌无效或过期。"""


def create_session_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.session_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def parse_session_token(token: str) -> int:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise TokenError("登录已失效，请重新登录") from exc
