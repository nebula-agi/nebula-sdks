"""
Data models for the Nebula Client SDK
"""

import base64
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Common MIME types for auto-detection
# We define these explicitly to avoid system dependencies and ensure consistency
MIME_TYPES = {
    # Images
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    # Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/m4a",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".webm": "audio/webm",
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".rtf": "application/rtf",
    ".epub": "application/epub+zip",
}


@dataclass
class Chunk:
    """A chunk or message within a memory"""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    role: str | None = None  # For conversation messages


@dataclass
class FileContent:
    """Unified container for all multimodal file content (images, audio, documents).

    Internal use. Access via Memory.File or Memory.from_file.
    """

    data: str  # Base64 encoded data
    type: str = "file"
    media_type: str = "application/octet-stream"
    filename: str | None = None
    duration_seconds: float | None = None  # Specific to audio

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        media_type: str | None = None,
        duration_seconds: float | None = None,
    ) -> "FileContent":
        """Create content from a file path."""
        file_path = Path(path)
        if not media_type:
            suffix = file_path.suffix.lower()
            media_type = MIME_TYPES.get(suffix, "application/octet-stream")

        with open(file_path, "rb") as f:
            file_data = f.read()
            encoded_data = base64.b64encode(file_data).decode("utf-8")

        return cls(
            data=encoded_data,
            media_type=media_type,
            filename=file_path.name,
            duration_seconds=duration_seconds,
        )


@dataclass
class S3FileRef:
    """Reference to a file uploaded to S3 (for large files >5MB)."""

    s3_key: str  # S3 object key
    bucket: str | None = None  # Uses default bucket if not specified
    media_type: str = "application/octet-stream"
    filename: str | None = None
    size_bytes: int | None = None
    type: str = "s3_ref"


@dataclass
class TextContent:
    """Text content block for multimodal messages."""

    text: str
    type: str = "text"


# Union type for content parts
ContentPart = FileContent | S3FileRef | TextContent | dict[str, Any]


@dataclass(init=False)
class Memory:
    """Unified model for Nebula memories (documents or conversations).

    Can be used both as an input for creating/appending memories and as
     a return type for get/list operations.
    """

    collection_id: str | None = None  # Primary collection for creation
    content: str | list[ContentPart] | None = None
    role: str | None = None  # user, assistant, or custom
    id: str | None = None  # Memory/Engram UUID
    metadata: dict[str, Any] = field(default_factory=dict)
    authority: float | None = None  # Optional authority score (0.0 - 1.0)

    # Read-only fields (populated from server response)
    chunks: list[Chunk] | None = None
    collection_ids: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __init__(
        self,
        collection_id: str | None = None,
        content: str | list[ContentPart] | None = None,
        role: str | None = None,
        id: str | None = None,
        metadata: dict[str, Any] | None = None,
        authority: float | None = None,
        memory_id: str | None = None,
        chunks: list[Chunk] | None = None,
        collection_ids: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.collection_id = collection_id
        self.content = content
        self.role = role
        self.id = id or memory_id
        self.metadata = metadata if metadata is not None else {}
        self.authority = authority
        self.chunks = chunks
        self.collection_ids = collection_ids if collection_ids is not None else []
        self.created_at = created_at
        self.updated_at = updated_at

    # Alias for cleaner access to file content helper
    File = FileContent.from_path

    @property
    def memory_id(self) -> str | None:
        """Alias for id, for backward compatibility."""
        return self.id

    @memory_id.setter
    def memory_id(self, value: str | None):
        self.id = value

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        collection_id: str,
        metadata: dict[str, Any] | None = None,
        role: str | None = None,
    ) -> "Memory":
        """Create a memory from a single file."""
        return cls(
            collection_id=collection_id,
            content=[FileContent.from_path(path)],
            metadata=metadata or {},
            role=role,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Memory":
        """Create a Memory from a dictionary (API response)."""
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                try:
                    created_at = datetime.fromisoformat(
                        data["created_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]

        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                try:
                    updated_at = datetime.fromisoformat(
                        data["updated_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            elif isinstance(data["updated_at"], datetime):
                updated_at = data["updated_at"]

        # Handle various ID fields from API (id, engram_id)
        memory_id = str(
            data.get("id") or data.get("engram_id") or data.get("memory_id") or ""
        )

        # Map 'text' to 'content' for documents
        content = data.get("content") or data.get("text")

        # Parse chunks if present
        chunks: list[Chunk] | None = None
        if "chunks" in data and isinstance(data["chunks"], list):
            chunk_list: list[Chunk] = []
            for item in data["chunks"]:
                if isinstance(item, dict):
                    chunk_list.append(
                        Chunk(
                            id=str(item.get("id", "")),
                            content=item.get("content") or item.get("text", ""),
                            metadata=item.get("metadata", {}),
                            role=item.get("role"),
                        )
                    )
                elif isinstance(item, str):
                    chunk_list.append(Chunk(id="", content=item))
            chunks = chunk_list if chunk_list else None

        collection_ids = data.get("collection_ids", [])
        # If input was a single collection_id, put it in the list if not there
        if data.get("collection_id") and data["collection_id"] not in collection_ids:
            collection_ids.append(data["collection_id"])

        metadata = data.get("metadata", {})
        if data.get("engram_metadata"):
            metadata.update(data["engram_metadata"])

        return cls(
            memory_id=memory_id,
            collection_id=data.get("collection_id"),
            content=content,
            role=data.get("role"),
            metadata=metadata,
            chunks=chunks,
            collection_ids=collection_ids,
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Memory to dictionary."""
        return {
            "id": self.memory_id,
            "memory_id": self.memory_id,
            "collection_id": self.collection_id,
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata,
            "collection_ids": self.collection_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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
class SearchOptions:
    """Options for search operations"""

    limit: int = 10
    filters: dict[str, Any] | None = None
    search_mode: str = "super"  # "fast" or "super"


# Hierarchical Memory Response types (matches backend MemoryRecall structure)


@dataclass
class MemoryResponse:
    """The result of a memory retrieval operation (search or recall).

    Contains hierarchical memory structures: entities, facts, and utterances.
    Nested data are stored as raw dicts for performance.
    """

    query: str
    entities: list[dict[str, Any]]
    facts: list[dict[str, Any]]
    utterances: list[dict[str, Any]]
    fact_to_chunks: dict[str, list[str]]
    entity_to_facts: dict[str, list[str]]
    retrieved_at: str
    focus: dict[str, Any] | None = None
    total_traversal_time_ms: float | None = None
    query_intent: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], query: str) -> "MemoryResponse":
        """Create a MemoryResponse from a dictionary response."""
        return cls(
            query=data.get("query", query),
            entities=data.get("entities", []),
            facts=data.get("facts", []),
            utterances=data.get("utterances", []),
            focus=data.get("focus"),
            fact_to_chunks=data.get("fact_to_chunks", {}),
            entity_to_facts=data.get("entity_to_facts", {}),
            retrieved_at=data.get("retrieved_at", ""),
            total_traversal_time_ms=data.get("total_traversal_time_ms"),
            query_intent=data.get("query_intent"),
        )
