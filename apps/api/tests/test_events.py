import asyncio
import json
import threading
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient

from app.modules.events import _stream
from app.services.events import hub, notify_import
from app.services.extract import ExtractedFields
from app.services.pdf_parse import ParsedPdf


def test_hub_delivers_from_worker_thread() -> None:
    async def body() -> None:
        queue = hub.subscribe(42)
        threading.Thread(
            target=lambda: notify_import(42, batch_id=3, contract_id=8),
            daemon=True,
        ).start()
        payload = await asyncio.wait_for(queue.get(), timeout=2)
        hub.unsubscribe(42, queue)
        assert payload == {"type": "import_updated", "batch_id": 3, "contract_id": 8}

    asyncio.run(body())


def test_events_require_login(client: TestClient) -> None:
    response = client.get("/api/v1/events")
    assert response.status_code == 401


def test_events_forbid_member(member_client: TestClient) -> None:
    response = member_client.get("/api/v1/events")
    assert response.status_code == 403


def test_stream_sends_connected_then_payload() -> None:
    async def body() -> None:
        request = Mock()
        request.is_disconnected = AsyncMock(return_value=False)
        gen = _stream(1, request)
        first = await asyncio.wait_for(gen.__anext__(), timeout=2)
        assert first == ": connected\n\n"
        notify_import(1, batch_id=9, contract_id=4)
        second = await asyncio.wait_for(gen.__anext__(), timeout=2)
        assert second.startswith("data: ")
        payload = json.loads(second.removeprefix("data: ").strip())
        assert payload == {"type": "import_updated", "batch_id": 9, "contract_id": 4}
        await gen.aclose()

    asyncio.run(body())


def test_import_progress_is_pushed(logged_in: TestClient, monkeypatch) -> None:
    started = threading.Event()
    release = threading.Event()
    subscribed = threading.Event()
    user_id = logged_in.get("/api/v1/auth/me").json()["id"]
    received: list[dict] = []

    def slow_parse(data: bytes) -> ParsedPdf:
        started.set()
        assert release.wait(timeout=5)
        return ParsedPdf(
            text=data.decode("utf-8"),
            source="electronic",
            fields=ExtractedFields(
                doc_type="contract", contract_no="HT-SSE-1", party_a="甲", party_b="乙"
            ),
        )

    monkeypatch.setattr("app.services.imports.parse_pdf_bytes", slow_parse)

    async def subscribe() -> None:
        queue = hub.subscribe(user_id)
        subscribed.set()
        try:
            while True:
                payload = await asyncio.wait_for(queue.get(), timeout=8)
                received.append(payload)
                if payload.get("type") == "import_updated" and len(received) >= 2:
                    return
        finally:
            hub.unsubscribe(user_id, queue)

    listener = threading.Thread(target=lambda: asyncio.run(subscribe()), daemon=True)
    listener.start()
    assert subscribed.wait(timeout=5)

    try:
        response = logged_in.post(
            "/api/v1/contracts/imports",
            files=[("files", ("采购合同.pdf", b"sse-contract-bytes", "application/pdf"))],
        )
        assert response.status_code == 201, response.text
        assert started.wait(timeout=5)
    finally:
        release.set()
    listener.join(timeout=8)
    assert any(item.get("type") == "import_updated" for item in received)
    assert any(item.get("batch_id") == response.json()["id"] for item in received)
