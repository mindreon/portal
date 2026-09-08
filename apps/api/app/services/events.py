"""
进程内消息总线。

后台识别在线程里跑，浏览器用 SSE 听着。识别每提交一次进度，就往这里塞一条消息。
没有 Redis、没有 WebSocket：这个体量和现有的线程队列是同一套假设——单进程够用。
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

Payload = dict[str, Any]
Subscriber = tuple[asyncio.AbstractEventLoop, asyncio.Queue[Payload]]


def _put(queue: asyncio.Queue[Payload], payload: Payload) -> None:
    """队列满了就丢掉最旧的一条，保证最新进度还能送出去。"""
    try:
        queue.put_nowait(payload)
        return
    except asyncio.QueueFull:
        pass
    try:
        queue.get_nowait()
    except asyncio.QueueEmpty:
        pass
    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        pass


class EventHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: dict[int, list[Subscriber]] = {}

    def subscribe(self, user_id: int) -> asyncio.Queue[Payload]:
        queue: asyncio.Queue[Payload] = asyncio.Queue(maxsize=32)
        loop = asyncio.get_running_loop()
        with self._lock:
            self._subs.setdefault(user_id, []).append((loop, queue))
        return queue

    def unsubscribe(self, user_id: int, queue: asyncio.Queue[Payload]) -> None:
        with self._lock:
            rows = self._subs.get(user_id, [])
            leftover = [item for item in rows if item[1] is not queue]
            if leftover:
                self._subs[user_id] = leftover
            else:
                self._subs.pop(user_id, None)

    def publish(self, user_id: int, payload: Payload) -> None:
        with self._lock:
            rows = list(self._subs.get(user_id, []))
        for loop, queue in rows:
            try:
                loop.call_soon_threadsafe(_put, queue, payload)
            except RuntimeError:
                logger.debug("SSE 订阅已关闭，丢掉一条事件")


hub = EventHub()


def publish(user_id: int, payload: Payload) -> None:
    hub.publish(user_id, payload)


def notify_import(owner_id: int, *, batch_id: int, contract_id: int | None = None) -> None:
    """合同导入进度变了：浏览器收到后自己再拉一次列表/详情。"""
    publish(
        owner_id,
        {
            "type": "import_updated",
            "batch_id": batch_id,
            "contract_id": contract_id,
        },
    )
