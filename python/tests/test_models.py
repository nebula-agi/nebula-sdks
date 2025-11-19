"""
Tests for the data models
"""

from datetime import datetime

import pytest

from nebula import (
    AgentResponse,
    Collection,
    Memory,
    MemoryResponse,
    RetrievalType,
    SearchResult,
)


class TestMemory:
    """Test cases for Memory model (write-only model)"""

    def test_memory_creation(self):
        """Test creating a Memory instance for writing"""
        memory = Memory(
            collection_id="collection-123",
            content="Test memory content",
            metadata={"test": "value"},
        )

        assert memory.collection_id == "collection-123"
        assert memory.content == "Test memory content"
        assert memory.metadata == {"test": "value"}
        assert memory.role is None
        assert memory.memory_id is None
        assert memory.authority is None

    def test_memory_creation_with_role(self):
        """Test creating a conversation Memory instance"""
        memory = Memory(
            collection_id="collection-123",
            content="Hello!",
            role="user",
            metadata={"session": "abc"},
        )

        assert memory.collection_id == "collection-123"
        assert memory.content == "Hello!"
        assert memory.role == "user"
        assert memory.metadata == {"session": "abc"}

    def test_memory_creation_with_memory_id(self):
        """Test creating a Memory for appending to existing memory"""
        memory = Memory(
            collection_id="collection-123",
            content="Additional content",
            memory_id="existing-memory-123",
        )

        assert memory.collection_id == "collection-123"
        assert memory.content == "Additional content"
        assert memory.memory_id == "existing-memory-123"


class TestMemoryResponse:
    """Test cases for MemoryResponse model (read-only model)"""

    def test_memory_response_from_dict(self):
        """Test creating MemoryResponse from dictionary"""
        data = {
            "id": "memory-123",
            "content": "Test memory content",
            "metadata": {"test": "value"},
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
            "collection_ids": ["collection-1", "collection-2"],
        }

        memory = MemoryResponse.from_dict(data)

        assert memory.id == "memory-123"
        assert memory.content == "Test memory content"
        assert memory.metadata == {"test": "value"}
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
        assert memory.collection_ids == ["collection-1", "collection-2"]

    def test_memory_response_from_dict_with_datetime_objects(self):
        """Test creating MemoryResponse from dictionary with datetime objects"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)

        data = {
            "id": "memory-123",
            "content": "Test memory content",
            "metadata": {"test": "value"},
            "created_at": created_at,
            "updated_at": updated_at,
        }

        memory = MemoryResponse.from_dict(data)

        assert memory.created_at == created_at
        assert memory.updated_at == updated_at

    def test_memory_response_from_dict_without_optional_fields(self):
        """Test creating MemoryResponse from dictionary without optional fields"""
        data = {
            "id": "memory-123",
            "content": "Test memory content",
        }

        memory = MemoryResponse.from_dict(data)

        assert memory.id == "memory-123"
        assert memory.content == "Test memory content"
        assert memory.metadata == {}
        assert memory.created_at is None
        assert memory.updated_at is None

    def test_memory_response_to_dict(self):
        """Test converting MemoryResponse to dictionary"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)

        memory = MemoryResponse(
            id="memory-123",
            content="Test memory content",
            metadata={"test": "value"},
            created_at=created_at,
            updated_at=updated_at,
            collection_ids=["collection-1"],
        )

        data = memory.to_dict()

        assert data["id"] == "memory-123"
        assert data["content"] == "Test memory content"
        assert data["metadata"] == {"test": "value"}
        assert data["created_at"] == "2024-01-01T12:00:00"
        assert data["updated_at"] == "2024-01-02T12:00:00"
        assert data["collection_ids"] == ["collection-1"]

    def test_memory_response_to_dict_with_none_dates(self):
        """Test converting MemoryResponse to dictionary with None dates"""
        memory = MemoryResponse(
            id="memory-123",
            content="Test memory content",
        )

        data = memory.to_dict()

        assert data["created_at"] is None
        assert data["updated_at"] is None


class TestCollection:
    """Test cases for Collection model"""

    def test_collection_creation(self):
        """Test creating a Collection instance"""
        collection = Collection(
            id="cluster-123",
            name="Test Cluster",
            description="Test Description",
            metadata={"test": "value"},
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            memory_count=5,
            owner_id="owner-123",
        )

        assert collection.id == "cluster-123"
        assert collection.name == "Test Cluster"
        assert collection.description == "Test Description"
        assert collection.metadata == {"test": "value"}
        assert collection.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert collection.memory_count == 5
        assert collection.owner_id == "owner-123"

    def test_collection_from_dict(self):
        """Test creating Collection from dictionary"""
        data = {
            "id": "cluster-123",
            "name": "Test Cluster",
            "description": "Test Description",
            "engram_count": 5,
            "owner_id": "owner-123",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
        }

        collection = Collection.from_dict(data)

        assert collection.id == "cluster-123"
        assert collection.name == "Test Cluster"
        assert collection.description == "Test Description"
        assert isinstance(collection.created_at, datetime)
        assert isinstance(collection.updated_at, datetime)
        assert collection.memory_count == 5
        assert collection.owner_id == "owner-123"

    def test_collection_from_dict_without_optional_fields(self):
        """Test creating Collection from dictionary without optional fields"""
        data = {
            "id": "cluster-123",
            "name": "Test Cluster",
        }

        collection = Collection.from_dict(data)

        assert collection.id == "cluster-123"
        assert collection.name == "Test Cluster"
        assert collection.description is None
        assert collection.created_at is None
        assert collection.updated_at is None
        assert collection.memory_count == 0
        assert collection.owner_id is None

    def test_collection_to_dict(self):
        """Test converting Collection to dictionary"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)

        collection = Collection(
            id="cluster-123",
            name="Test Cluster",
            description="Test Description",
            metadata={"test": "value"},
            created_at=created_at,
            updated_at=updated_at,
            memory_count=5,
            owner_id="owner-123",
        )

        data = collection.to_dict()

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
            memory_id="memory-123",
        )

        assert result.id == "result-123"
        assert result.content == "Search result content"
        assert result.score == 0.95
        assert result.metadata == {"test": "value"}
        assert result.memory_id == "memory-123"

    def test_search_result_from_dict(self):
        """Test creating SearchResult from dictionary"""
        data = {
            "id": "result-123",
            "content": "Search result content",
            "score": 0.95,
            "metadata": {"test": "value"},
            "memory_id": "memory-123",
        }

        result = SearchResult.from_dict(data)

        assert result.id == "result-123"
        assert result.content == "Search result content"
        assert result.score == 0.95
        assert result.metadata == {"test": "value"}
        assert result.memory_id == "memory-123"

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
        assert result.memory_id is None


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
        assert RetrievalType.ADVANCED == "advanced"

    def test_retrieval_type_creation(self):
        """Test creating RetrievalType instances"""
        simple = RetrievalType("simple")
        advanced = RetrievalType("advanced")

        assert simple == RetrievalType.SIMPLE
        assert advanced == RetrievalType.ADVANCED

    def test_retrieval_type_invalid_value(self):
        """Test creating RetrievalType with invalid value raises error"""
        with pytest.raises(ValueError):
            RetrievalType("invalid_type")
