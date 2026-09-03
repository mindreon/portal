"""
飞书网页 OAuth 登录。

完整链路（官方文档）：
1. 浏览器跳到授权页，拿到一次性 code（5 分钟有效）
2. 服务端用 code 换 user_access_token
3. 再用 token 拉取用户姓名、open_id、头像

参考：
- 获取授权码 https://open.feishu.cn/document/authentication-management/access-token/obtain-oauth-code
- 换 token https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token
- 用户信息 https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/authen-v1/user_info/get
"""

from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


class FeishuError(Exception):
    """调用飞书开放接口失败。"""


@dataclass
class FeishuProfile:
    open_id: str
    union_id: str | None
    name: str
    email: str | None
    avatar_url: str | None


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.feishu_app_id,
        "response_type": "code",
        "redirect_uri": settings.feishu_redirect_uri,
        "state": state,
    }
    if settings.feishu_scopes.strip():
        params["scope"] = settings.feishu_scopes.strip()
    return f"{settings.feishu_authorize_url}?{urlencode(params)}"


def exchange_code(code: str) -> str:
    """用授权码换 user_access_token。code 只能用一次。"""
    settings = get_settings()
    try:
        response = httpx.post(
            settings.feishu_token_url,
            json={
                "grant_type": "authorization_code",
                "client_id": settings.feishu_app_id,
                "client_secret": settings.feishu_app_secret,
                "code": code,
                "redirect_uri": settings.feishu_redirect_uri,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise FeishuError("无法连接飞书开放平台，请检查网络") from exc

    token = payload.get("access_token")
    if payload.get("code") not in (0, None) or not token:
        message = payload.get("error_description") or payload.get("msg") or "换取飞书令牌失败"
        raise FeishuError(str(message))
    return token


def fetch_user_info(user_access_token: str) -> FeishuProfile:
    settings = get_settings()
    try:
        response = httpx.get(
            settings.feishu_user_info_url,
            headers={"Authorization": f"Bearer {user_access_token}"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise FeishuError("拉取飞书用户信息失败") from exc

    if payload.get("code") != 0:
        raise FeishuError(payload.get("msg") or "飞书返回了错误的用户信息")

    data = payload.get("data") or {}
    open_id = data.get("open_id")
    name = data.get("name") or data.get("en_name")
    if not open_id or not name:
        raise FeishuError("飞书用户信息不完整，缺少 open_id 或姓名")

    return FeishuProfile(
        open_id=open_id,
        union_id=data.get("union_id"),
        name=name,
        email=data.get("enterprise_email") or data.get("email"),
        avatar_url=data.get("avatar_middle") or data.get("avatar_url"),
    )
