import asyncio
import json
import os
import sys
from typing import Any

# Ensure the package root (sdk/nebula_client) is importable when running from py/
_THIS_DIR = os.path.dirname(__file__)
_PKG_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from nebula.async_client import AsyncNebula  # noqa: E402
from nebula.models import FileContent, Memory  # noqa: E402


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload
        import json as _json

        self.content = _json.dumps(payload).encode("utf-8")
        self.text = _json.dumps(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


class _DummyHttpClient:
    def __init__(self):
        self.posts: list[dict[str, Any]] = []

    async def post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
    ):
        self.posts.append(
            {"url": url, "data": data, "headers": headers, "files": files}
        )
        # Default successful create with document id
        return _DummyResponse(
            200, {"results": {"engram_id": "doc_123", "id": "doc_123"}}
        )

    async def aclose(self) -> None:
        return None


def run(coro):
    return asyncio.run(coro)


def test_store_memory_conversation_creates_and_posts(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")

    # Track calls to _make_request_async (conversation creation)
    calls: list[dict[str, Any]] = []

    async def _fake_request(
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "json": json_data,
                "params": params,
            }
        )
        # Conversation creation uses JSON POST /v1/memories.
        if endpoint == "/v1/memories":
            return {"results": {"engram_id": "conv_123", "id": "conv_123"}}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    mem = Memory(
        collection_id="cluster_1", content="hello", role="user", metadata={"x": 1}
    )
    conv_id = run(client.store_memory(mem))

    assert conv_id == "conv_123"
    assert any(c["endpoint"] == "/v1/memories" for c in calls)


def test_is_multimodal_content_detects_mixed_list():
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    assert (
        client._is_multimodal_content(["hello", {"type": "image", "data": "Zg=="}])
        is True
    )
    assert client._is_multimodal_content(["hello", FileContent(data="Zg==")]) is True


def test_normalize_content_parts_wraps_scalar_as_text():
    parts = AsyncNebula._normalize_content_parts("hello")
    assert len(parts) == 1
    assert parts[0].type == "text"
    assert parts[0].text == "hello"


def test_normalize_content_parts_wraps_string_items_in_list():
    parts = AsyncNebula._normalize_content_parts(
        ["hello", {"type": "image", "data": "Zg==", "media_type": "image/png"}]
    )
    assert len(parts) == 2
    assert parts[0].type == "text"
    assert parts[0].text == "hello"
    assert isinstance(parts[1], dict)
    assert parts[1]["type"] == "image"


def test_store_memory_text_engram_posts(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    dummy = _DummyHttpClient()
    client._client = dummy  # type: ignore[attr-defined]

    # Patch _make_request_async to return a stable doc ID for JSON create.
    async def _fake_request(
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ):
        if endpoint == "/v1/memories":
            return {"results": {"engram_id": "doc_123", "id": "doc_123"}}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    mem = Memory(
        collection_id="cluster_1", content="some text", metadata={"foo": "bar"}
    )
    doc_id = run(client.store_memory(mem))

    assert doc_id == "doc_123"
    # Verify it used the JSON /v1/memories call (not multipart POST)
    assert dummy.posts == []


def test_store_memories_mixed_batch(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []

    async def _fake_request(
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "json": json_data,
                "params": params,
            }
        )
        # Handle create conversation/doc
        if endpoint == "/v1/memories":
            if json_data and json_data.get("messages"):
                return {"results": {"engram_id": "conv_123", "id": "conv_123"}}
            return {"results": {"engram_id": "doc_123", "id": "doc_123"}}
        # Handle append operations
        if endpoint.startswith("/v1/memories/") and endpoint.endswith("/append"):
            return {"ok": True}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    memories = [
        Memory(collection_id="c1", content="hi", role="user"),  # conversation (new)
        Memory(collection_id="c1", content="there"),  # document
        Memory(
            collection_id="c1",
            content="again",
            role="assistant",
            memory_id="conv_existing",
        ),  # conversation (existing - append)
    ]

    results = run(client.store_memories(memories))

    # We expect 3 ids back: new conversation, document, and existing conversation
    assert len(results) == 3
    assert "conv_123" in results  # New conversation created via HTTP POST
    assert "conv_existing" in results  # Existing conversation (appended)
    assert "doc_123" in results  # Document created via HTTP POST
    # Append endpoint should be called once: for existing conversation only
    append_calls = [c for c in calls if c["endpoint"].endswith("/append")]
    assert len(append_calls) == 1


def test_store_memory_conversation_includes_authority(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")

    calls: list[dict[str, Any]] = []

    async def _fake_request(
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "json": json_data,
                "params": params,
            }
        )
        if endpoint == "/v1/memories":
            return {"results": {"engram_id": "conv_123", "id": "conv_123"}}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    mem = Memory(
        collection_id="c1",
        content="hi",
        role="assistant",
        metadata={"foo": 1},
        authority=0.9,
    )
    conv_id = run(client.store_memory(mem))

    assert conv_id == "conv_123"
    create_calls = [c for c in calls if c["endpoint"] == "/v1/memories"]
    assert create_calls, "No create call made"
    msg_payload = create_calls[0]["json"] or {}
    assert (
        "messages" in msg_payload
        and isinstance(msg_payload["messages"], list)
        and msg_payload["messages"]
    )
    first_msg = msg_payload["messages"][0]
    assert first_msg.get("authority") == 0.9


def test_store_memory_document_metadata_includes_authority(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []

    async def _fake_request(
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "json": json_data,
                "params": params,
            }
        )
        if endpoint == "/v1/memories":
            return {"results": {"engram_id": "doc_123", "id": "doc_123"}}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    mem = Memory(
        collection_id="cluster_docs",
        content="some text",
        metadata={"bar": True},
        authority=0.8,
    )
    doc_id = run(client.store_memory(mem))

    assert doc_id == "doc_123"
    create_calls = [c for c in calls if c["endpoint"] == "/v1/memories"]
    assert create_calls, "No create call made"
    payload = create_calls[0]["json"] or {}
    md = payload.get("metadata") or {}
    assert md.get("authority") == 0.8


def test_store_memory_multimodal_document_serializes_raw_text(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []

    async def _fake_request(
        method: str,
        endpoint: str,
        json_data: Any | None = None,
        params: dict[str, Any] | None = None,
    ):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "json": json_data,
                "params": params,
            }
        )
        if endpoint == "/v1/memories":
            return {"results": {"engram_id": "doc_123", "id": "doc_123"}}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    mem = Memory(
        collection_id="cluster_docs",
        content=[
            "A caption",
            FileContent(data="Zg==", media_type="image/jpeg", filename="x.jpg"),
        ],
        metadata={"k": "v"},
    )
    doc_id = run(client.store_memory(mem))
    assert doc_id == "doc_123"

    create_calls = [c for c in calls if c["endpoint"] == "/v1/memories"]
    assert create_calls
    payload = create_calls[0]["json"] or {}
    assert "content_parts" not in payload
    assert isinstance(payload.get("raw_text"), str)
    decoded = json.loads(payload["raw_text"])
    assert isinstance(decoded, list)
    assert any(isinstance(p, dict) and p.get("type") == "file" for p in decoded)
