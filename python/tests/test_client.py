"""
Tests for the NebulaClient class
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from nebula import (
    NebulaClient,
    Memory,
    Collection,
    SearchResult,
    AgentResponse,
    RetrievalType,
    NebulaException,
    NebulaClientException,
    NebulaAuthenticationException,
    NebulaRateLimitException,
    NebulaValidationException,
)


class TestNebulaClient:
    """Test cases for NebulaClient"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = NebulaClient(api_key="test-api-key")
        self.mock_response = Mock()

    def test_init_with_api_key(self):
        """Test client initialization with API key"""
        client = NebulaClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.nebulacloud.app"
        assert client.timeout == 30.0

    def test_init_with_env_var(self, monkeypatch):
        """Test client initialization with environment variable"""
        monkeypatch.setenv("NEBULA_API_KEY", "env-api-key")
        client = NebulaClient()
        assert client.api_key == "env-api-key"

    def test_init_without_api_key(self):
        """Test client initialization without API key raises exception"""
        with pytest.raises(NebulaClientException, match="API key is required"):
            NebulaClient()

    def test_init_with_custom_base_url(self):
        """Test client initialization with custom base URL"""
        client = NebulaClient(api_key="test-key", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"

    def test_init_with_custom_timeout(self):
        """Test client initialization with custom timeout"""
        client = NebulaClient(api_key="test-key", timeout=60.0)
        assert client.timeout == 60.0

    # New tests for header behavior
    def test_is_nebula_api_key_detection(self):
        client = NebulaClient(api_key="key_abc.def")
        assert client._is_nebula_api_key() is True
        client2 = NebulaClient(api_key="not-a-jwt-or-nebula")
        assert client2._is_nebula_api_key() is False
        client3 = NebulaClient(api_key="key_only_without_dot")
        assert client3._is_nebula_api_key() is False
        client4 = NebulaClient(api_key="key_ab.c.d")
        assert client4._is_nebula_api_key() is False

    def test_build_auth_headers_for_nebula_key(self):
        client = NebulaClient(api_key="key_pub.VERY_SECRET_RAW")
        headers = client._build_auth_headers()
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "key_pub.VERY_SECRET_RAW"
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_build_auth_headers_for_bearer(self):
        client = NebulaClient(api_key="a.b.c.jwt-looking-token")
        headers = client._build_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {client.api_key}"
        assert "X-API-Key" not in headers
        assert headers["Content-Type"] == "application/json"

    @patch("httpx.Client.request")
    def test_create_cluster(self, mock_request):
        """Test creating a cluster"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cluster-123",
            "name": "Test Collection",
            "description": "Test Description",
            "metadata": {"test": "value"},
            "created_at": "2024-01-01T00:00:00Z",
            "memory_count": 0,
        }
        mock_request.return_value = mock_response

        cluster = self.client.create_cluster(
            name="Test Collection",
            description="Test Description",
            metadata={"test": "value"},
        )

        assert isinstance(cluster, Collection)
        assert cluster.id == "cluster-123"
        assert cluster.name == "Test Collection"
        assert cluster.description == "Test Description"
        assert cluster.metadata == {"test": "value"}

    @patch("httpx.Client.request")
    def test_get_cluster(self, mock_request):
        """Test getting a cluster"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cluster-123",
            "name": "Test Collection",
            "description": "Test Description",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z",
            "memory_count": 5,
        }
        mock_request.return_value = mock_response

        cluster = self.client.get_cluster("cluster-123")

        assert isinstance(cluster, Collection)
        assert cluster.id == "cluster-123"
        assert cluster.memory_count == 5

    @patch("httpx.Client.request")
    def test_list_clusters(self, mock_request):
        """Test listing clusters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "cluster-1",
                "name": "Collection 1",
                "description": "First cluster",
                "metadata": {},
                "created_at": "2024-01-01T00:00:00Z",
                "memory_count": 2,
            },
            {
                "id": "cluster-2",
                "name": "Collection 2",
                "description": "Second cluster",
                "metadata": {},
                "created_at": "2024-01-02T00:00:00Z",
                "memory_count": 3,
            },
        ]
        mock_request.return_value = mock_response

        clusters = self.client.list_clusters(limit=10, offset=0)

        assert len(clusters) == 2
        assert all(isinstance(cluster, Collection) for cluster in clusters)
        assert clusters[0].name == "Collection 1"
        assert clusters[1].name == "Collection 2"

    @patch("httpx.Client.request")
    def test_store_memory(self, mock_request):
        """Test storing a memory"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "memory-123",
            "content": "Test memory content",
            "metadata": {"test": "value"},
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_request.return_value = mock_response

        memory = self.client.store(
            content="Test memory content",
            metadata={"test": "value"},
            collection_id="cluster-123",
        )

        assert isinstance(memory, Memory)
        assert memory.id == "memory-123"
        assert memory.content == "Test memory content"
        assert memory.metadata == {"test": "value"}

    @patch("httpx.Client.request")
    def test_retrieve_memories(self, mock_request):
        """Test retrieving memories"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "memory-1",
                "content": "First memory content",
                "score": 0.95,
                "metadata": {"agent_id": "test-agent"},
            },
            {
                "id": "memory-2",
                "content": "Second memory content",
                "score": 0.87,
                "metadata": {"agent_id": "test-agent"},
            },
        ]
        mock_request.return_value = mock_response

        results = self.client.retrieve(
            agent_id="test-agent",
            query="test query",
            limit=5,
            retrieval_type=RetrievalType.SIMPLE,
            filters={"test": "filter"},
            collection_id="cluster-123",
        )

        assert len(results) == 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert results[0].score == 0.95
        assert results[1].score == 0.87

    @patch("httpx.Client.request")
    def test_retrieve_with_string_retrieval_type(self, mock_request):
        """Test retrieving memories with string retrieval type"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response

        results = self.client.retrieve(
            agent_id="test-agent",
            query="test query",
            retrieval_type="reasoning",
        )

        assert len(results) == 0

    @patch("httpx.Client.request")
    def test_chat(self, mock_request):
        """Test chatting with an agent"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Hello! How can I help you?",
            "agent_id": "test-agent",
            "conversation_id": "conv-123",
            "metadata": {"model": "gpt-4"},
            "citations": [{"id": "memory-1", "content": "Cited content"}],
        }
        mock_request.return_value = mock_response

        response = self.client.chat(
            agent_id="test-agent",
            message="Hello",
            conversation_id="conv-123",
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            retrieval_type=RetrievalType.SIMPLE,
            collection_id="cluster-123",
        )

        assert isinstance(response, AgentResponse)
        assert response.content == "Hello! How can I help you?"
        assert response.agent_id == "test-agent"
        assert response.conversation_id == "conv-123"
        assert len(response.citations) == 1

    @patch("httpx.Client.request")
    def test_chat_with_string_retrieval_type(self, mock_request):
        """Test chatting with string retrieval type"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Response",
            "agent_id": "test-agent",
            "metadata": {},
            "citations": [],
        }
        mock_request.return_value = mock_response

        response = self.client.chat(
            agent_id="test-agent",
            message="Hello",
            retrieval_type="planning",
        )

        assert isinstance(response, AgentResponse)

    @patch("httpx.Client.request")
    def test_search(self, mock_request):
        """Test searching across all memories"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "memory-1",
                "content": "Search result content",
                "score": 0.92,
                "metadata": {},
            }
        ]
        mock_request.return_value = mock_response

        results = self.client.search(
            query="search query",
            limit=10,
            filters={"test": "filter"},
            collection_id="cluster-123",
        )

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].score == 0.92

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
        mock_response.content = b'{"message": "Validation error", "details": {"field": "required"}}'
        mock_response.json.return_value = {"message": "Validation error", "details": {"field": "required"}}
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
    def test_get_cluster_by_name(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cluster-xyz",
            "name": "longmemeval_local",
            "description": None,
            "metadata": {},
        }
        mock_request.return_value = mock_response

        cluster = self.client.get_cluster_by_name("longmemeval_local")
        assert isinstance(cluster, Collection)
        assert cluster.id == "cluster-xyz"
        assert cluster.name == "longmemeval_local"

    @patch("httpx.Client.request")
    def test_get_cluster_by_name_not_found(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b'{"message": "Not found"}'
        mock_response.json.return_value = {"message": "Not found"}
        mock_request.return_value = mock_response

        with pytest.raises(NebulaException):
            self.client.get_cluster_by_name("does-not-exist")

    def test_context_manager(self):
        """Test client as context manager"""
        with NebulaClient(api_key="test-key") as client:
            assert isinstance(client, NebulaClient)
            assert client.api_key == "test-key"

    def test_close_method(self):
        """Test client close method"""
        self.client.close()
        # Should not raise any exception


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = NebulaClient(api_key="test-api-key")

    def test_chunk_aliases(self):
        """Test chunk terminology aliases"""
        # These should be the same methods
        assert self.client.store == self.client.store_chunk
        assert self.client.retrieve == self.client.retrieve_chunks
        assert self.client.delete == self.client.delete_chunk
        assert self.client.get == self.client.get_chunk
        assert self.client.list_agent_memories == self.client.list_agent_chunks
        assert self.client.search == self.client.search_chunks
        assert self.client.chat == self.client.chat_with_chunks

    def test_collection_aliases(self):
        """Test collection terminology aliases"""
        # These should be the same methods
        assert self.client.create_cluster == self.client.create_collection
        assert self.client.get_cluster == self.client.get_collection
        assert self.client.list_clusters == self.client.list_collections
        assert self.client.update_cluster == self.client.update_collection
        assert self.client.delete_cluster == self.client.delete_collection
        assert self.client.add_memory_to_cluster == self.client.add_memory_to_collection
        assert self.client.remove_memory_from_cluster == self.client.remove_memory_from_collection
        assert self.client.get_cluster_memories == self.client.get_collection_memories 