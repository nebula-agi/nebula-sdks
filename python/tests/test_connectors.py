"""
Tests for Nebula connector methods (sync client)
"""

from unittest.mock import Mock, patch

import pytest

from nebula import Nebula
from nebula.exceptions import NebulaException


class TestConnectors:
    """Test cases for connector methods on the sync Nebula client."""

    def setup_method(self):
        self.client = Nebula(api_key="test-api-key")

    @patch("httpx.Client.request")
    def test_list_providers(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": ["gmail", "google_drive"],
        }
        mock_request.return_value = mock_response

        result = self.client.list_providers()

        assert result == ["gmail", "google_drive"]

    @patch("httpx.Client.request")
    def test_connect_provider(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"auth_url": "https://accounts.google.com/...", "state": "abc"},
        }
        mock_request.return_value = mock_response

        result = self.client.connect_provider("google_drive", "col-1")

        assert result["auth_url"] == "https://accounts.google.com/..."
        assert result["state"] == "abc"
        call_args = mock_request.call_args
        body = call_args.kwargs.get("json") or {}
        assert body["collection_id"] == "col-1"
        assert "config" not in body

    @patch("httpx.Client.request")
    def test_connect_provider_with_config(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"auth_url": "https://example.com", "state": "xyz"},
        }
        mock_request.return_value = mock_response

        result = self.client.connect_provider(
            "google_drive", "col-1", config={"folder_ids": ["f1"]}
        )

        assert result["state"] == "xyz"
        call_args = mock_request.call_args
        body = call_args.kwargs.get("json") or {}
        assert body["config"] == {"folder_ids": ["f1"]}

    @patch("httpx.Client.request")
    def test_list_connections(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "conn-1", "provider": "google_drive", "status": "active"},
            ],
        }
        mock_request.return_value = mock_response

        result = self.client.list_connections("col-1")

        assert len(result) == 1
        assert result[0]["id"] == "conn-1"
        call_args = mock_request.call_args
        params = call_args.kwargs.get("params") or {}
        assert params["collection_id"] == "col-1"

    @patch("httpx.Client.request")
    def test_list_folders(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "folder-1", "name": "Docs", "has_children": True},
            ],
        }
        mock_request.return_value = mock_response

        result = self.client.list_folders("conn-1")

        assert len(result) == 1
        assert result[0]["name"] == "Docs"
        call_args = mock_request.call_args
        url = call_args.kwargs.get("url") or str(call_args)
        assert "/v1/connectors/conn-1/folders" in url

    @patch("httpx.Client.request")
    def test_list_folders_with_parent(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "sub-1", "name": "Subfolder", "has_children": False},
            ],
        }
        mock_request.return_value = mock_response

        result = self.client.list_folders("conn-1", parent_id="folder-1")

        assert len(result) == 1
        call_args = mock_request.call_args
        params = call_args.kwargs.get("params") or {}
        assert params["parent_id"] == "folder-1"

    @patch("httpx.Client.request")
    def test_list_channels(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "C01234ABC", "name": "general", "is_private": False},
            ],
        }
        mock_request.return_value = mock_response

        result = self.client.list_channels("conn-1")

        assert len(result) == 1
        assert result[0]["name"] == "general"
        call_args = mock_request.call_args
        url = call_args.kwargs.get("url") or str(call_args)
        assert "/v1/connectors/conn-1/channels" in url

    @patch("httpx.Client.request")
    def test_update_connection_config(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"status": "active"},
        }
        mock_request.return_value = mock_response

        result = self.client.update_connection_config(
            "conn-1", {"folder_ids": ["f1", "f2"]}
        )

        assert result["status"] == "active"
        call_args = mock_request.call_args
        body = call_args.kwargs.get("json") or {}
        assert body == {"config": {"folder_ids": ["f1", "f2"]}, "apply": "full_resync"}

    @patch("httpx.Client.request")
    def test_disconnect(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"status": "revoked"},
        }
        mock_request.return_value = mock_response

        result = self.client.disconnect("conn-1")

        assert result["status"] == "revoked"
        call_args = mock_request.call_args
        assert call_args.kwargs.get("method") == "DELETE"
        url = call_args.kwargs.get("url") or str(call_args)
        assert "/v1/connectors/conn-1" in url

    @patch("httpx.Client.request")
    def test_get_connection(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"id": "conn-1", "provider": "google_drive", "health": "ok"},
        }
        mock_request.return_value = mock_response

        result = self.client.get_connection("conn-1")

        assert result["id"] == "conn-1"
        call_args = mock_request.call_args
        url = call_args.kwargs.get("url") or str(call_args)
        assert "/v1/connectors/conn-1" in url
        assert call_args.kwargs.get("method") == "GET"

    @patch("httpx.Client.request")
    def test_trigger_sync(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"message": "Sync triggered"},
        }
        mock_request.return_value = mock_response

        result = self.client.trigger_sync("conn-1")

        assert "Sync triggered" in result["message"]
        call_args = mock_request.call_args
        url = call_args.kwargs.get("url") or str(call_args)
        assert "/v1/connectors/conn-1/sync" in url
        assert call_args.kwargs.get("method") == "POST"

    @patch("httpx.Client.request")
    def test_trigger_sync_409(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.content = True
        mock_response.json.return_value = {"message": "Sync already in progress"}
        mock_request.return_value = mock_response

        with pytest.raises(NebulaException):
            self.client.trigger_sync("conn-1")

    @patch("httpx.Client.request")
    def test_disconnect_with_delete_memories(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"message": "disconnected", "warnings": []},
        }
        mock_request.return_value = mock_response

        result = self.client.disconnect("conn-1", delete_memories=True)

        assert "warnings" in result
        call_args = mock_request.call_args
        params = call_args.kwargs.get("params") or {}
        assert params["delete_memories"] == "true"

    @patch("httpx.Client.request")
    def test_update_connection_config_with_apply(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {"status": "active"},
        }
        mock_request.return_value = mock_response

        result = self.client.update_connection_config(
            "conn-1", {"folder_ids": ["f1"]}, apply="full_resync"
        )

        assert result["status"] == "active"
        call_args = mock_request.call_args
        body = call_args.kwargs.get("json") or {}
        assert body["apply"] == "full_resync"

    @patch("httpx.Client.request")
    def test_disconnect_warnings_shape(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "message": "disconnected",
                "warnings": [
                    {
                        "code": "cleanup_partial",
                        "message": "Some memories could not be deleted.",
                    }
                ],
            },
        }
        mock_request.return_value = mock_response

        result = self.client.disconnect("conn-1", delete_memories=True)

        assert len(result["warnings"]) == 1
        w = result["warnings"][0]
        assert isinstance(w["code"], str)
        assert isinstance(w["message"], str)
        assert w["code"] == "cleanup_partial"
