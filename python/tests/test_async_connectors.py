"""
Tests for AsyncNebula connector methods
"""

import asyncio
import os
import sys
from typing import Any

import pytest

_THIS_DIR = os.path.dirname(__file__)
_PKG_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from nebula.async_client import AsyncNebula  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def _make_fake_request(calls: list[dict[str, Any]], default_result: Any = None):
    """Return a fake _make_request_async that records calls and returns a configurable result."""

    async def _fake(
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
        if default_result is not None:
            return default_result
        return {"results": {}}

    return _fake


def test_list_providers():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": ["gmail", "google_drive"]}
    )

    result = run(client.list_providers())

    assert result == ["gmail", "google_drive"]
    assert calls[0]["method"] == "GET"
    assert calls[0]["endpoint"] == "/v1/connectors/providers"


def test_connect_provider():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls,
        {"results": {"auth_url": "https://accounts.google.com/...", "state": "abc"}},
    )

    result = run(client.connect_provider("google_drive", "col-1"))

    assert result["auth_url"] == "https://accounts.google.com/..."
    assert calls[0]["method"] == "POST"
    assert calls[0]["endpoint"] == "/v1/connectors/google_drive/connect"
    assert calls[0]["json"]["collection_id"] == "col-1"
    assert "config" not in calls[0]["json"]


def test_connect_provider_with_config():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"auth_url": "https://example.com", "state": "xyz"}}
    )

    result = run(
        client.connect_provider("google_drive", "col-1", config={"folder_ids": ["f1"]})
    )

    assert result["state"] == "xyz"
    assert calls[0]["json"]["config"] == {"folder_ids": ["f1"]}


def test_list_connections():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": [{"id": "conn-1", "provider": "google_drive"}]}
    )

    result = run(client.list_connections("col-1"))

    assert len(result) == 1
    assert result[0]["id"] == "conn-1"
    assert calls[0]["method"] == "GET"
    assert calls[0]["endpoint"] == "/v1/connectors"
    assert calls[0]["params"]["collection_id"] == "col-1"


def test_list_folders():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": [{"id": "folder-1", "name": "Docs"}]}
    )

    result = run(client.list_folders("conn-1"))

    assert len(result) == 1
    assert result[0]["name"] == "Docs"
    assert calls[0]["endpoint"] == "/v1/connectors/conn-1/folders"


def test_list_folders_with_parent():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": [{"id": "sub-1", "name": "Subfolder"}]}
    )

    result = run(client.list_folders("conn-1", parent_id="folder-1"))

    assert len(result) == 1
    assert calls[0]["params"]["parent_id"] == "folder-1"


def test_list_channels():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": [{"id": "C01234ABC", "name": "general"}]}
    )

    result = run(client.list_channels("conn-1"))

    assert len(result) == 1
    assert result[0]["name"] == "general"
    assert calls[0]["endpoint"] == "/v1/connectors/conn-1/channels"


def test_update_connection_config():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"status": "active"}}
    )

    result = run(
        client.update_connection_config("conn-1", {"folder_ids": ["f1", "f2"]})
    )

    assert result["status"] == "active"
    assert calls[0]["method"] == "PATCH"
    assert calls[0]["endpoint"] == "/v1/connectors/conn-1/config"
    assert calls[0]["json"] == {"config": {"folder_ids": ["f1", "f2"]}, "apply": "full_resync"}


def test_disconnect():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"status": "revoked"}}
    )

    result = run(client.disconnect("conn-1"))

    assert result["status"] == "revoked"
    assert calls[0]["method"] == "DELETE"
    assert calls[0]["endpoint"] == "/v1/connectors/conn-1"


def test_get_connection():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"id": "conn-1"}}
    )

    result = run(client.get_connection("conn-1"))

    assert result["id"] == "conn-1"
    assert calls[0]["endpoint"] == "/v1/connectors/conn-1"
    assert calls[0]["method"] == "GET"


def test_trigger_sync():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"message": "Sync triggered"}}
    )

    result = run(client.trigger_sync("conn-1"))

    assert result["message"] == "Sync triggered"
    assert calls[0]["endpoint"] == "/v1/connectors/conn-1/sync"
    assert calls[0]["method"] == "POST"


def test_trigger_sync_409():
    from nebula.exceptions import NebulaException

    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")

    async def _fake_409(method, endpoint, json_data=None, params=None):
        raise NebulaException("Sync already in progress", 409, {})

    client._make_request_async = _fake_409  # type: ignore[assignment]
    with pytest.raises(NebulaException):
        run(client.trigger_sync("conn-1"))


def test_disconnect_with_delete_memories():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"message": "disconnected", "warnings": []}}
    )

    result = run(client.disconnect("conn-1", delete_memories=True))

    assert calls[0]["params"]["delete_memories"] == "true"
    assert "warnings" in result


def test_update_connection_config_with_apply():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls, {"results": {"status": "active"}}
    )

    result = run(
        client.update_connection_config("conn-1", {"folder_ids": ["f1"]}, apply="full_resync")
    )

    assert result["status"] == "active"
    assert calls[0]["json"]["apply"] == "full_resync"


def test_disconnect_warnings_shape():
    client = AsyncNebula(api_key="key_pub.raw", base_url="https://example.com")
    calls: list[dict[str, Any]] = []
    client._make_request_async = _make_fake_request(  # type: ignore[assignment]
        calls,
        {
            "results": {
                "message": "disconnected",
                "warnings": [
                    {"code": "cleanup_partial", "message": "Some memories could not be deleted."}
                ],
            }
        },
    )

    result = run(client.disconnect("conn-1", delete_memories=True))

    assert len(result["warnings"]) == 1
    w = result["warnings"][0]
    assert isinstance(w["code"], str)
    assert isinstance(w["message"], str)
    assert w["code"] == "cleanup_partial"
