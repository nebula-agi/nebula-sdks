"""
Tests for the Nebula class
"""

from unittest.mock import Mock, patch

import pytest

from nebula import (
    Collection,
    Nebula,
    NebulaAuthenticationException,
    NebulaClientException,
    NebulaException,
    NebulaRateLimitException,
    NebulaValidationException,
    SearchResult,
)


class TestNebula:
    """Test cases for Nebula"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = Nebula(api_key="test-api-key")
        self.mock_response = Mock()

    def test_init_with_api_key(self):
        """Test client initialization with API key"""
        client = Nebula(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.nebulacloud.app"
        assert client.timeout == 30.0

    def test_init_with_env_var(self, monkeypatch):
        """Test client initialization with environment variable"""
        monkeypatch.setenv("NEBULA_API_KEY", "env-api-key")
        client = Nebula()
        assert client.api_key == "env-api-key"

    def test_init_without_api_key(self):
        """Test client initialization without API key raises exception"""
        with pytest.raises(NebulaClientException, match="API key is required"):
            Nebula()

    def test_init_with_custom_base_url(self):
        """Test client initialization with custom base URL"""
        client = Nebula(api_key="test-key", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"

    def test_init_with_custom_timeout(self):
        """Test client initialization with custom timeout"""
        client = Nebula(api_key="test-key", timeout=60.0)
        assert client.timeout == 60.0

    # New tests for header behavior
    def test_is_nebula_api_key_detection(self):
        client = Nebula(api_key="key_abc.def")
        assert client._is_nebula_api_key() is True
        client2 = Nebula(api_key="not-a-jwt-or-nebula")
        assert client2._is_nebula_api_key() is False
        client3 = Nebula(api_key="key_only_without_dot")
        assert client3._is_nebula_api_key() is False
        client4 = Nebula(api_key="key_ab.c.d")
        assert client4._is_nebula_api_key() is False

    def test_build_auth_headers_for_nebula_key(self):
        client = Nebula(api_key="key_pub.VERY_SECRET_RAW")
        headers = client._build_auth_headers()
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "key_pub.VERY_SECRET_RAW"
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_build_auth_headers_for_bearer(self):
        client = Nebula(api_key="a.b.c.jwt-looking-token")
        headers = client._build_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {client.api_key}"
        assert "X-API-Key" not in headers
        assert headers["Content-Type"] == "application/json"

    @patch("httpx.Client.request")
    def test_create_collection(self, mock_request):
        """Test creating a collection"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cluster-123",
            "name": "Test Collection",
            "description": "Test Description",
            "engram_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_request.return_value = mock_response

        collection = self.client.create_collection(
            name="Test Collection",
            description="Test Description",
            metadata={"test": "value"},
        )

        assert isinstance(collection, Collection)
        assert collection.id == "cluster-123"
        assert collection.name == "Test Collection"
        assert collection.description == "Test Description"

    @patch("httpx.Client.request")
    def test_get_collection(self, mock_request):
        """Test getting a collection"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cluster-123",
            "name": "Test Collection",
            "description": "Test Description",
            "engram_count": 5,
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_request.return_value = mock_response

        collection = self.client.get_collection("cluster-123")

        assert isinstance(collection, Collection)
        assert collection.id == "cluster-123"
        assert collection.memory_count == 5

    @patch("httpx.Client.request")
    def test_list_collections(self, mock_request):
        """Test listing collections"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "cluster-1",
                "name": "Collection 1",
                "description": "First cluster",
                "engram_count": 2,
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "cluster-2",
                "name": "Collection 2",
                "description": "Second cluster",
                "engram_count": 3,
                "created_at": "2024-01-02T00:00:00Z",
            },
        ]
        mock_request.return_value = mock_response

        collections = self.client.list_collections(limit=10, offset=0)

        assert len(collections) == 2
        assert all(isinstance(collection, Collection) for collection in collections)
        assert collections[0].name == "Collection 1"
        assert collections[1].name == "Collection 2"

    @patch("httpx.Client.request")
    def test_store_memory(self, mock_request):
        """Test storing a memory"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "engram_id": "memory-123",
                "id": "memory-123",
            }
        }
        mock_request.return_value = mock_response

        memory_id = self.client.store_memory(
            collection_id="cluster-123",
            content="Test memory content",
            metadata={"test": "value"},
        )

        assert isinstance(memory_id, str)
        assert memory_id == "memory-123"

    @patch("httpx.Client.request")
    def test_search_memories(self, mock_request):
        """Test searching memories"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "chunk_search_results": [
                    {
                        "id": "chunk-1",
                        "content": "First memory content",
                        "score": 0.95,
                        "metadata": {},
                        "memory_id": "memory-1",
                    },
                    {
                        "id": "chunk-2",
                        "content": "Second memory content",
                        "score": 0.87,
                        "metadata": {},
                        "memory_id": "memory-2",
                    },
                ],
                "graph_search_results": [],
            }
        }
        mock_request.return_value = mock_response

        results = self.client.search(
            query="test query",
            collection_ids=["cluster-123"],
            limit=5,
            filters={"test": "filter"},
        )

        assert len(results) == 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert results[0].score == 0.95
        assert results[1].score == 0.87

    @patch("httpx.Client.request")
    def test_health_check(self, mock_request):
        """Test health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
        }
        mock_request.return_value = mock_response

        health = self.client.health_check()

        assert health["status"] == "healthy"
        assert health["version"] == "1.0.0"

    @patch("httpx.Client.request")
    def test_authentication_error(self, mock_request):
        """Test authentication error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.content = b'{"message": "Invalid API key"}'
        mock_request.return_value = mock_response

        with pytest.raises(NebulaAuthenticationException, match="Invalid API key"):
            self.client.health_check()

    @patch("httpx.Client.request")
    def test_rate_limit_error(self, mock_request):
        """Test rate limit error handling"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.content = b'{"message": "Rate limit exceeded"}'
        mock_request.return_value = mock_response

        with pytest.raises(NebulaRateLimitException, match="Rate limit exceeded"):
            self.client.health_check()

    @patch("httpx.Client.request")
    def test_validation_error(self, mock_request):
        """Test validation error handling"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = (
            b'{"message": "Validation error", "details": {"field": "required"}}'
        )
        mock_response.json.return_value = {
            "message": "Validation error",
            "details": {"field": "required"},
        }
        mock_request.return_value = mock_response

        with pytest.raises(NebulaValidationException) as exc_info:
            self.client.health_check()

        assert "Validation error" in str(exc_info.value)
        assert exc_info.value.details == {"field": "required"}

    @patch("httpx.Client.request")
    def test_generic_api_error(self, mock_request):
        """Test generic API error handling"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b'{"message": "Internal server error"}'
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_request.return_value = mock_response

        with pytest.raises(NebulaException) as exc_info:
            self.client.health_check()

        assert "Internal server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @patch("httpx.Client.request")
    def test_get_collection_by_name(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cluster-xyz",
            "name": "longmemeval_local",
            "description": None,
            "engram_count": 0,
        }
        mock_request.return_value = mock_response

        collection = self.client.get_collection_by_name("longmemeval_local")
        assert isinstance(collection, Collection)
        assert collection.id == "cluster-xyz"
        assert collection.name == "longmemeval_local"

    @patch("httpx.Client.request")
    def test_get_collection_by_name_not_found(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b'{"message": "Not found"}'
        mock_response.json.return_value = {"message": "Not found"}
        mock_request.return_value = mock_response

        with pytest.raises(NebulaException):
            self.client.get_collection_by_name("does-not-exist")

    def test_context_manager(self):
        """Test client as context manager"""
        with Nebula(api_key="test-key") as client:
            assert isinstance(client, Nebula)
            assert client.api_key == "test-key"

    def test_close_method(self):
        """Test client close method"""
        self.client.close()
        # Should not raise any exception
