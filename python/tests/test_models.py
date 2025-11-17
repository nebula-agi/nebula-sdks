"""
Tests for the data models
"""

import pytest
from datetime import datetime
from nebula_client import (
    Memory,
    Cluster,
    SearchResult,
    AgentResponse,
    RetrievalType,
)


class TestMemory:
    """Test cases for Memory model"""

    def test_memory_creation(self):
        """Test creating a Memory instance"""
        memory = Memory(
            id="memory-123",
            agent_id="test-agent",
            content="Test memory content",
            metadata={"test": "value"},
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        assert memory.id == "memory-123"
        assert memory.agent_id == "test-agent"
        assert memory.content == "Test memory content"
        assert memory.metadata == {"test": "value"}
        assert memory.created_at == datetime(2024, 1, 1, 12, 0, 0)

    def test_memory_from_dict(self):
        """Test creating Memory from dictionary"""
        data = {
            "id": "memory-123",
            "agent_id": "test-agent",
            "content": "Test memory content",
            "metadata": {"test": "value"},
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
        }

        memory = Memory.from_dict(data)

        assert memory.id == "memory-123"
        assert memory.agent_id == "test-agent"
        assert memory.content == "Test memory content"
        assert memory.metadata == {"test": "value"}
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)

    def test_memory_from_dict_with_datetime_objects(self):
        """Test creating Memory from dictionary with datetime objects"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)
        
        data = {
            "id": "memory-123",
            "agent_id": "test-agent",
            "content": "Test memory content",
            "metadata": {"test": "value"},
            "created_at": created_at,
            "updated_at": updated_at,
        }

        memory = Memory.from_dict(data)

        assert memory.created_at == created_at
        assert memory.updated_at == updated_at

    def test_memory_from_dict_without_optional_fields(self):
        """Test creating Memory from dictionary without optional fields"""
        data = {
            "id": "memory-123",
            "agent_id": "test-agent",
            "content": "Test memory content",
        }

        memory = Memory.from_dict(data)

        assert memory.id == "memory-123"
        assert memory.agent_id == "test-agent"
        assert memory.content == "Test memory content"
        assert memory.metadata == {}
        assert memory.created_at is None
        assert memory.updated_at is None

    def test_memory_to_dict(self):
        """Test converting Memory to dictionary"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)
        
        memory = Memory(
            id="memory-123",
            agent_id="test-agent",
            content="Test memory content",
            metadata={"test": "value"},
            created_at=created_at,
            updated_at=updated_at,
        )

        data = memory.to_dict()

        assert data["id"] == "memory-123"
        assert data["agent_id"] == "test-agent"
        assert data["content"] == "Test memory content"
        assert data["metadata"] == {"test": "value"}
        assert data["created_at"] == "2024-01-01T12:00:00"
        assert data["updated_at"] == "2024-01-02T12:00:00"

    def test_memory_to_dict_with_none_dates(self):
        """Test converting Memory to dictionary with None dates"""
        memory = Memory(
            id="memory-123",
            agent_id="test-agent",
            content="Test memory content",
        )

        data = memory.to_dict()

        assert data["created_at"] is None
        assert data["updated_at"] is None


class TestCluster:
    """Test cases for Cluster model"""

    def test_cluster_creation(self):
        """Test creating a Cluster instance"""
        cluster = Cluster(
            id="cluster-123",
            name="Test Cluster",
            description="Test Description",
            metadata={"test": "value"},
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            memory_count=5,
            owner_id="owner-123",
        )

        assert cluster.id == "cluster-123"
        assert cluster.name == "Test Cluster"
        assert cluster.description == "Test Description"
        assert cluster.metadata == {"test": "value"}
        assert cluster.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert cluster.memory_count == 5
        assert cluster.owner_id == "owner-123"

    def test_cluster_from_dict(self):
        """Test creating Cluster from dictionary"""
        data = {
            "id": "cluster-123",
            "name": "Test Cluster",
            "description": "Test Description",
            "metadata": {"test": "value"},
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
            "memory_count": 5,
            "owner_id": "owner-123",
        }

        cluster = Cluster.from_dict(data)

        assert cluster.id == "cluster-123"
        assert cluster.name == "Test Cluster"
        assert cluster.description == "Test Description"
        assert cluster.metadata == {"test": "value"}
        assert isinstance(cluster.created_at, datetime)
        assert isinstance(cluster.updated_at, datetime)
        assert cluster.memory_count == 5
        assert cluster.owner_id == "owner-123"

    def test_cluster_from_dict_without_optional_fields(self):
        """Test creating Cluster from dictionary without optional fields"""
        data = {
            "id": "cluster-123",
            "name": "Test Cluster",
        }

        cluster = Cluster.from_dict(data)

        assert cluster.id == "cluster-123"
        assert cluster.name == "Test Cluster"
        assert cluster.description is None
        assert cluster.metadata == {}
        assert cluster.created_at is None
        assert cluster.updated_at is None
        assert cluster.memory_count == 0
        assert cluster.owner_id is None

    def test_cluster_to_dict(self):
        """Test converting Cluster to dictionary"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)
        
        cluster = Cluster(
            id="cluster-123",
            name="Test Cluster",
            description="Test Description",
            metadata={"test": "value"},
            created_at=created_at,
            updated_at=updated_at,
            memory_count=5,
            owner_id="owner-123",
        )

        data = cluster.to_dict()

        assert data["id"] == "cluster-123"
        assert data["name"] == "Test Cluster"
        assert data["description"] == "Test Description"
        assert data["metadata"] == {"test": "value"}
        assert data["created_at"] == "2024-01-01T12:00:00"
        assert data["updated_at"] == "2024-01-02T12:00:00"
        assert data["memory_count"] == 5
        assert data["owner_id"] == "owner-123"


class TestSearchResult:
    """Test cases for SearchResult model"""

    def test_search_result_creation(self):
        """Test creating a SearchResult instance"""
        result = SearchResult(
            id="result-123",
            content="Search result content",
            score=0.95,
            metadata={"test": "value"},
            source="memory-123",
        )

        assert result.id == "result-123"
        assert result.content == "Search result content"
        assert result.score == 0.95
        assert result.metadata == {"test": "value"}
        assert result.source == "memory-123"

    def test_search_result_from_dict(self):
        """Test creating SearchResult from dictionary"""
        data = {
            "id": "result-123",
            "content": "Search result content",
            "score": 0.95,
            "metadata": {"test": "value"},
            "source": "memory-123",
        }

        result = SearchResult.from_dict(data)

        assert result.id == "result-123"
        assert result.content == "Search result content"
        assert result.score == 0.95
        assert result.metadata == {"test": "value"}
        assert result.source == "memory-123"

    def test_search_result_from_dict_without_optional_fields(self):
        """Test creating SearchResult from dictionary without optional fields"""
        data = {
            "id": "result-123",
            "content": "Search result content",
        }

        result = SearchResult.from_dict(data)

        assert result.id == "result-123"
        assert result.content == "Search result content"
        assert result.score == 0.0
        assert result.metadata == {}
        assert result.source is None


class TestAgentResponse:
    """Test cases for AgentResponse model"""

    def test_agent_response_creation(self):
        """Test creating an AgentResponse instance"""
        response = AgentResponse(
            content="Hello! How can I help you?",
            agent_id="test-agent",
            conversation_id="conv-123",
            metadata={"model": "gpt-4"},
            citations=[{"id": "memory-1", "content": "Cited content"}],
        )

        assert response.content == "Hello! How can I help you?"
        assert response.agent_id == "test-agent"
        assert response.conversation_id == "conv-123"
        assert response.metadata == {"model": "gpt-4"}
        assert len(response.citations) == 1
        assert response.citations[0]["id"] == "memory-1"

    def test_agent_response_from_dict(self):
        """Test creating AgentResponse from dictionary"""
        data = {
            "content": "Hello! How can I help you?",
            "agent_id": "test-agent",
            "conversation_id": "conv-123",
            "metadata": {"model": "gpt-4"},
            "citations": [{"id": "memory-1", "content": "Cited content"}],
        }

        response = AgentResponse.from_dict(data)

        assert response.content == "Hello! How can I help you?"
        assert response.agent_id == "test-agent"
        assert response.conversation_id == "conv-123"
        assert response.metadata == {"model": "gpt-4"}
        assert len(response.citations) == 1

    def test_agent_response_from_dict_without_optional_fields(self):
        """Test creating AgentResponse from dictionary without optional fields"""
        data = {
            "content": "Hello!",
            "agent_id": "test-agent",
        }

        response = AgentResponse.from_dict(data)

        assert response.content == "Hello!"
        assert response.agent_id == "test-agent"
        assert response.conversation_id is None
        assert response.metadata == {}
        assert response.citations == []


class TestRetrievalType:
    """Test cases for RetrievalType enum"""

    def test_retrieval_type_values(self):
        """Test RetrievalType enum values"""
        assert RetrievalType.SIMPLE == "simple"
        assert RetrievalType.PLANNING == "planning"
        assert RetrievalType.REASONING == "reasoning"
        assert RetrievalType.DEEP_RESEARCH == "deep_research"

    def test_retrieval_type_creation(self):
        """Test creating RetrievalType instances"""
        simple = RetrievalType("simple")
        planning = RetrievalType("planning")
        reasoning = RetrievalType("reasoning")
        deep_research = RetrievalType("deep_research")

        assert simple == RetrievalType.SIMPLE
        assert planning == RetrievalType.PLANNING
        assert reasoning == RetrievalType.REASONING
        assert deep_research == RetrievalType.DEEP_RESEARCH

    def test_retrieval_type_invalid_value(self):
        """Test creating RetrievalType with invalid value raises error"""
        with pytest.raises(ValueError):
            RetrievalType("invalid_type") 