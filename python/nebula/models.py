"""
Data models for the Nebula Client SDK
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class Chunk:
    """A chunk or message within a memory"""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    role: str | None = None  # For conversation messages


@dataclass
class MemoryResponse:
    """Read model returned by list/get operations.

    Notes:
    - Exactly one of `content` or `chunks` is typically present for text memories
    - `chunks` contains individual chunks with their IDs for granular operations
    - `collection_ids` reflects collections the memory belongs to
    - Not used for writes; use `Memory` for store_memory/store_memories
    """

    id: str
    content: str | None = None
    chunks: list[Chunk] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    collection_ids: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryResponse":
        """Create a Memory from a dictionary"""
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]

        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(
                    data["updated_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["updated_at"], datetime):
                updated_at = data["updated_at"]

        # Handle chunk response format (API returns chunks, not memories)
        memory_id = str(data.get("id", ""))

        # Prefer explicit chunks if present; otherwise map 'text'/'content' → content
        content: str | None = data.get("content") or data.get("text")
        chunks: list[Chunk] | None = None
        if "chunks" in data and isinstance(data["chunks"], list):
            chunk_list: list[Chunk] = []
            for item in data["chunks"]:
                if isinstance(item, dict):
                    # Parse chunk object with id, content/text, metadata, role
                    chunk_id = str(item.get("id", ""))
                    chunk_content = item.get("content") or item.get("text", "")
                    chunk_metadata = item.get("metadata", {})
                    chunk_role = item.get("role")
                    chunk_list.append(
                        Chunk(
                            id=chunk_id,
                            content=chunk_content,
                            metadata=chunk_metadata,
                            role=chunk_role,
                        )
                    )
                elif isinstance(item, str):
                    # Legacy: plain string chunks without IDs
                    chunk_list.append(Chunk(id="", content=item))
            chunks = chunk_list if chunk_list else None

        # API returns 'collection_ids'
        metadata = data.get("metadata", {})
        collection_ids = data.get("collection_ids", [])
        if data.get("engram_id"):
            metadata["engram_id"] = data["engram_id"]

        # Handle engram-based approach - if this is a engram response
        if data.get("engram_id") and not memory_id:
            memory_id = data["engram_id"]

        # If we have engram metadata, merge it
        if data.get("engram_metadata"):
            metadata.update(data["engram_metadata"])

        return cls(
            id=memory_id,
            content=content,
            chunks=chunks,
            metadata=metadata,
            collection_ids=collection_ids,
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Memory to dictionary"""
        result = {
            "id": self.id,
            "content": self.content,
            "chunks": self.chunks,
            "metadata": self.metadata,
            "collection_ids": self.collection_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return result


@dataclass
class Memory:
    """Unified input model for writing memories via store_memory/store_memories.

    Behavior:
    - memory_id absent → creates new memory
      - role present → conversation message (returns conversation_id)
      - role absent → text/json memory (returns memory_id)
    - memory_id present → appends to existing memory
      - For conversations: appends to conversation
      - For documents: appends content to document
      - Returns the same memory_id
    """

    collection_id: str
    content: str
    role: str | None = None  # user, assistant, or custom
    memory_id: str | None = None  # ID of existing memory to append to
    metadata: dict[str, Any] = field(default_factory=dict)
    authority: float | None = None  # Optional authority score (0.0 - 1.0)


@dataclass
class Collection:
    """A collection of memories in Nebula"""

    id: str
    name: str
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    memory_count: int = 0
    owner_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Collection":
        """Create a Collection from a dictionary"""
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]

        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(
                    data["updated_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["updated_at"], datetime):
                updated_at = data["updated_at"]

        # Handle different field mappings from API response
        collection_id = str(data.get("id", ""))  # Convert UUID to string
        collection_name = data.get("name", "")
        collection_description = data.get("description")
        collection_owner_id = (
            str(data.get("owner_id", "")) if data.get("owner_id") else None
        )

        # Map API fields to SDK fields
        # API has engram_count, SDK expects memory_count
        memory_count = data.get("engram_count", 0)

        # Create metadata from API-specific fields
        metadata = {
            "graph_collection_status": data.get("graph_collection_status", ""),
            "graph_sync_status": data.get("graph_sync_status", ""),
            "user_count": data.get("user_count", 0),
            "engram_count": data.get("engram_count", 0),
        }

        return cls(
            id=collection_id,
            name=collection_name,
            description=collection_description,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
            memory_count=memory_count,
            owner_id=collection_owner_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Collection to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "memory_count": self.memory_count,
            "owner_id": self.owner_id,
        }


class GraphSearchResultType(str, Enum):
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    COMMUNITY = "community"


@dataclass
class GraphEntityResult:
    id: str | None
    name: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphRelationshipResult:
    id: str | None
    subject: str
    predicate: str
    object: str
    subject_id: str | None = None
    object_id: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphCommunityResult:
    id: str | None
    name: str
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Unified search result from Nebula (chunk or graph).

    - For chunk results, `content` is populated and graph_* fields are None.
    - For graph results, one of graph_entity/graph_relationship/graph_community is populated,
      and `graph_result_type` indicates which. `content` may include a human-readable fallback.

    Note: `id` is the chunk_id (individual chunk), `memory_id` is the container.
    """

    id: str  # chunk_id
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    # Document/source information
    memory_id: str | None = None  # Parent memory/conversation container
    owner_id: str | None = None  # Owner UUID

    # Chunk fields
    content: str | None = None

    # Graph variant discriminator and payload
    graph_result_type: GraphSearchResultType | None = None
    graph_entity: GraphEntityResult | None = None
    graph_relationship: GraphRelationshipResult | None = None
    graph_community: GraphCommunityResult | None = None
    chunk_ids: list[str] | None = None

    # Utterance-specific fields
    source_role: str | None = (
        None  # Speaker role for conversations: "user", "assistant", etc.
    )
    timestamp: datetime | None = None
    display_name: str | None = None  # Human-readable: "user on 2025-01-15"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult":
        """Create a chunk-style SearchResult from a dictionary."""
        content = data.get("content") or data.get("text")
        result_id = data.get("id") or data.get("chunk_id", "")
        # API returns engram_id, map to memory_id for SDK
        memory_id = data.get("memory_id") or data.get("engram_id")
        return cls(
            id=str(result_id),
            content=str(content) if content else None,
            score=float(data.get("score", 0.0)),
            metadata=data.get("metadata", {}) or {},
            memory_id=str(memory_id) if memory_id else None,
            owner_id=str(data["owner_id"]) if data.get("owner_id") else None,
        )

    @classmethod
    def from_graph_dict(cls, data: dict[str, Any]) -> "SearchResult":
        """Create a graph-style SearchResult (entity/relationship/community).

        Assumes server returns a valid result_type and well-formed content.
        """
        rid = str(data["id"]) if "id" in data else ""
        rtype = GraphSearchResultType(data["result_type"])  # strict
        content = data.get("content", {}) or {}
        score = float(data.get("score", 0.0)) if data.get("score") is not None else 0.0
        metadata = data.get("metadata", {}) or {}
        chunk_ids = (
            data.get("chunk_ids") if isinstance(data.get("chunk_ids"), list) else None
        )

        # Parse temporal and source fields (for utterance entities)
        timestamp = None
        if data.get("timestamp"):
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(
                    data["timestamp"].replace("Z", "+00:00")
                )
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]

        display_name = data.get("display_name")
        source_role = data.get("source_role")
        # API returns engram_id, map to memory_id for SDK
        memory_id_val = data.get("memory_id") or data.get("engram_id")
        memory_id = str(memory_id_val) if memory_id_val else None
        owner_id = str(data["owner_id"]) if data.get("owner_id") else None

        # Build typed content only (no text fallbacks for production cleanliness)
        entity: GraphEntityResult | None = None
        rel: GraphRelationshipResult | None = None
        comm: GraphCommunityResult | None = None

        if rtype == GraphSearchResultType.ENTITY:
            entity = GraphEntityResult(
                id=str(content.get("id")) if content.get("id") else None,
                name=content.get("name", ""),
                description=content.get("description", ""),
                metadata=content.get("metadata", {}) or {},
            )
        elif rtype == GraphSearchResultType.RELATIONSHIP:
            rel = GraphRelationshipResult(
                id=str(content.get("id")) if content.get("id") else None,
                subject=content.get("subject", ""),
                predicate=content.get("predicate", ""),
                object=content.get("object", ""),
                subject_id=str(content.get("subject_id"))
                if content.get("subject_id")
                else None,
                object_id=str(content.get("object_id"))
                if content.get("object_id")
                else None,
                description=content.get("description"),
                metadata=content.get("metadata", {}) or {},
            )
        else:
            comm = GraphCommunityResult(
                id=str(content.get("id")) if content.get("id") else None,
                name=content.get("name", ""),
                summary=content.get("summary", ""),
                metadata=content.get("metadata", {}) or {},
            )

        return cls(
            id=rid,
            score=score,
            metadata=metadata,
            memory_id=memory_id,
            owner_id=owner_id,
            content=None,
            graph_result_type=rtype,
            graph_entity=entity,
            graph_relationship=rel,
            graph_community=comm,
            chunk_ids=chunk_ids,
            source_role=source_role,
            timestamp=timestamp,
            display_name=display_name,
        )


@dataclass
class AgentResponse:
    """A response from an agent"""

    content: str
    agent_id: str
    conversation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentResponse":
        """Create an AgentResponse from a dictionary"""
        return cls(
            content=data["content"],
            agent_id=data["agent_id"],
            conversation_id=data.get("conversation_id"),
            metadata=data.get("metadata", {}),
            citations=data.get("citations", []),
        )


@dataclass
class SearchOptions:
    """Options for search operations"""

    limit: int = 10
    filters: dict[str, Any] | None = None
    search_mode: str = "super"  # "fast" or "super"


class RetrievalType(str, Enum):
    """Compatibility enum for legacy imports from client modules.

    Note: The current SDK does not actively use this in public APIs; it remains
    to preserve import compatibility for modules/tests that import it.
    """

    SIMPLE = "simple"
    ADVANCED = "advanced"


# @dataclass
# class AgentOptions:
#     """Options for agent operations"""
#
#     model: str = "gpt-4"
#     temperature: float = 0.7
#     max_tokens: Optional[int] = None
#     retrieval_type: RetrievalType = RetrievalType.SIMPLE
