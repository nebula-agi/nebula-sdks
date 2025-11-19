import asyncio
import os
import sys
from typing import Any

# Ensure the package root (sdk/nebula_client) is importable when running from py/
_THIS_DIR = os.path.dirname(__file__)
_PKG_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from nebula.async_client import AsyncNebula  # noqa: E402
from nebula.models import Memory  # noqa: E402


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
        # Check if this is a conversation creation (has engram_type in files)
        if files and files.get("engram_type"):
            engram_type_val = (
                files["engram_type"][1]
                if isinstance(files["engram_type"], tuple)
                else files["engram_type"]
            )
            if engram_type_val == "conversation":
                return _DummyResponse(
                    200, {"results": {"engram_id": "conv_123", "id": "conv_123"}}
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

    # Inject dummy HTTP client
    dummy = _DummyHttpClient()
    client._client = dummy  # type: ignore[attr-defined]

    # Track calls to _make_request_async for append operations
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
        # Handle append operations
        if endpoint.startswith("/v1/memories/") and endpoint.endswith("/append"):
            return {"ok": True}
        raise AssertionError(f"Unexpected call: {method} {endpoint}")

    client._make_request_async = _fake_request  # type: ignore[assignment]

    mem = Memory(
        collection_id="cluster_1", content="hello", role="user", metadata={"x": 1}
    )
    conv_id = run(client.store_memory(mem))

    assert conv_id == "conv_123"
    # Ensure conversation was created via direct HTTP POST
    assert any(p["url"].endswith("/v1/memories") for p in dummy.posts)
    # Ensure append was called for initial message
    assert any(c["endpoint"].endswith("/append") for c in calls)


def test_store_memory_text_engram_posts(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    dummy = _DummyHttpClient()
    client._client = dummy  # type: ignore[attr-defined]

    # No _make_request_async used in engram path
    mem = Memory(
        collection_id="cluster_1", content="some text", metadata={"foo": "bar"}
    )
    doc_id = run(client.store_memory(mem))

    assert doc_id == "doc_123"
    # Verify it posted to memories endpoint
    assert any(p["url"].endswith("/v1/memories") for p in dummy.posts)


def test_store_memories_mixed_batch(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")
    dummy = _DummyHttpClient()
    client._client = dummy  # type: ignore[attr-defined]

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
    # Append endpoint should be called twice: once for new conversation initial message, once for existing
    append_calls = [c for c in calls if c["endpoint"].endswith("/append")]
    assert len(append_calls) == 2


def test_store_memory_conversation_includes_authority(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")

    dummy = _DummyHttpClient()
    client._client = dummy  # type: ignore[attr-defined]

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
        # Handle append operations
        if endpoint.startswith("/v1/memories/") and endpoint.endswith("/append"):
            return {"ok": True}
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
    # Find append calls and verify authority in messages
    append_calls = [c for c in calls if c["endpoint"].endswith("/append")]
    assert append_calls, "No append call made"
    msg_payload = append_calls[0]["json"]
    assert "messages" in msg_payload and isinstance(msg_payload["messages"], list)
    first_msg = msg_payload["messages"][0]
    assert first_msg.get("authority") == 0.9


def test_store_memory_document_metadata_includes_authority(monkeypatch):
    client = AsyncNebula(api_key="key_public.raw", base_url="https://example.com")

    dummy = _DummyHttpClient()
    client._client = dummy  # type: ignore[attr-defined]

    mem = Memory(
        collection_id="cluster_docs",
        content="some text",
        metadata={"bar": True},
        authority=0.8,
    )
    doc_id = run(client.store_memory(mem))

    assert doc_id == "doc_123"
    # Inspect form-data sent via files parameter; metadata field should include authority
    posted = next((p for p in dummy.posts if p["url"].endswith("/v1/memories")), None)
    assert posted is not None
    # Documents use files parameter for multipart form-data
    files_data = posted.get("files")
    assert files_data is not None
    metadata_tuple = files_data.get("metadata")
    assert metadata_tuple is not None
    # The tuple is (None, json_string)
    metadata_json = metadata_tuple[1]
    import json as _json

    md = _json.loads(metadata_json)
    assert md.get("authority") == 0.8
