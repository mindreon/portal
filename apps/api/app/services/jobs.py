"""
后台小任务队列。

合同识别可能要翻很多页、等通义千问，不能绑在「浏览器还开着这个请求」上。
这里用进程内线程：上传接口先返回，识别在旁边慢慢做。刷新页面不会打断它。
没有 Redis / Celery，这个体量够用；进程重启时由 resume_pending_imports 把没做完的批次再丢进来。
进度靠 SSE 推给还开着页面的人，前端不用再定时轮询。
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.document import ImportBatch

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="import")
_lock = threading.Lock()
_futures: dict[int, Future[None]] = {}


def enqueue_import(batch_id: int) -> None:
    """同一批次只排队一次，避免启动恢复和刚上传重复投递。"""
    with _lock:
        current = _futures.get(batch_id)
        if current is not None and not current.done():
            return
        _futures[batch_id] = _executor.submit(_run_import_job, batch_id)


def wait_import(batch_id: int, timeout: float = 30) -> None:
    """测试用：等到这一批识别结束（成功或失败都会返回）。"""
    with _lock:
        future = _futures.get(batch_id)
    if future is None:
        return
    future.result(timeout=timeout)


def wait_all_imports(timeout: float = 30) -> None:
    with _lock:
        futures = list(_futures.values())
    for future in futures:
        if not future.done():
            future.result(timeout=timeout)


def resume_pending_imports() -> None:
    """服务启动时，把上次没做完的 processing 批次重新排队。"""
    db = SessionLocal()
    try:
        rows = db.scalars(select(ImportBatch).where(ImportBatch.status == "processing")).all()
        ids = [item.id for item in rows]
    finally:
        db.close()
    for batch_id in ids:
        logger.info("恢复未完成的合同导入批次 %s", batch_id)
        enqueue_import(batch_id)


def _run_import_job(batch_id: int) -> None:
    from app.services.imports import process_import_batch

    try:
        process_import_batch(batch_id)
    except Exception:
        logger.exception("合同导入批次 %s 后台处理失败", batch_id)
