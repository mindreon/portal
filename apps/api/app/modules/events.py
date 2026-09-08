"""
SSE 长连接：浏览器打开后一直听着，后台有进度就推一条 JSON。

鉴权在进流之前完成，数据库连接立刻关掉，避免每人占一条连接直到关页。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.access import can_access_module
from app.core.deps import COOKIE_NAME, load_user_from_token
from app.db.session import SessionLocal
from app.services.events import hub

router = APIRouter(prefix="/events", tags=["events"])

HEARTBEAT_SECONDS = 15


def _event_user_id(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> int:
    """鉴权后立刻归还数据库连接。SSE 可能挂几分钟，不能一直占着会话。"""
    db = SessionLocal()
    try:
        user = load_user_from_token(db, session_token)
        if not can_access_module(user, "contracts"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有访问该模块的权限",
            )
        return user.id
    finally:
        db.close()


async def _stream(user_id: int, request: Request) -> AsyncIterator[str]:
    queue = hub.subscribe(user_id)
    try:
        yield ": connected\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
            except TimeoutError:
                # 注释行：代理不会当成业务消息，但能阻止中间层把连接当死掉。
                yield ": ping\n\n"
                continue
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    finally:
        hub.unsubscribe(user_id, queue)


@router.get("")
@router.get("/")
async def stream_events(
    request: Request,
    user_id: int = Depends(_event_user_id),
) -> StreamingResponse:
    return StreamingResponse(
        _stream(user_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
