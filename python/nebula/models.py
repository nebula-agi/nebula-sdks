"""
Data models for the Nebula Client SDK
"""

import base64
import mimetypes
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import IO, Any, BinaryIO


def _read_and_encode(source: str | Path | bytes | BinaryIO) -> tuple[str, str | None]:
    """
    Read file content and encode to base64.
    
    Args:
        source: File path, bytes, or file-like object
        
    Returns:
        Tuple of (base64_data, filename or None)
    """
    filename: str | None = None
    
    if isinstance(source, (str, Path)):
        path = Path(source)
        filename = path.name
        with open(path, "rb") as f:
            data = f.read()
    elif isinstance(source, bytes):
        data = source
    else:
        # File-like object
        data = source.read()
        if hasattr(source, "name"):
            filename = os.path.basename(source.name)
    
    encoded = base64.b64encode(data).decode("utf-8")
    return encoded, filename


def _guess_media_type(filename: str | None, default: str) -> str:
    """Guess media type from filename, or return default."""
    if not filename:
        return default
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or default


# Extension to media type mappings for common types
IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
}

AUDIO_EXTENSIONS = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".webm": "audio/webm",
}

DOCUMENT_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".rtf": "application/rtf",
    ".md": "text/markdown",
    ".json": "application/json",
}


def _detect_content_type(filename: str | None, media_type: str | None = None) -> str:
    """
    Detect content type (image, audio, document) from filename or media type.
    
    Returns: 'image', 'audio', 'document', or 'unknown'
    """
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            return "image"
        if ext in AUDIO_EXTENSIONS:
            return "audio"
        if ext in DOCUMENT_EXTENSIONS:
            return "document"
    
    if media_type:
        if media_type.startswith("image/"):
            return "image"
        if media_type.startswith("audio/"):
            return "audio"
        if media_type.startswith("application/") or media_type.startswith("text/"):
            return "document"
    
    return "unknown"


def load_file(source: str | Path | BinaryIO) -> "ImageContent | AudioContent | DocumentContent":
    """
    Load a file and automatically detect its type (image, audio, or document).
    
    This is the simplest way to add files to Nebula - just pass a file path
    and the SDK handles everything: reading, encoding, and type detection.
    
    Args:
        source: File path string, Path object, or opened file (binary mode)
        
    Returns:
        ImageContent, AudioContent, or DocumentContent based on file extension
        
    Raises:
        ValueError: If file type cannot be detected
        
    Example:
        from nebula import Nebula, Memory, load_file
        
        client = Nebula()
        
        # Just use load_file() - type is auto-detected!
        memory = Memory(
            collection_id="my-collection",
            content=[
                load_file("photo.jpg"),      # Auto-detected as image
                load_file("recording.mp3"),  # Auto-detected as audio
                load_file("report.pdf"),     # Auto-detected as document
                "What's in these files?"     # Plain text (no load_file needed)
            ]
        )
        
        client.store_memory(memory)
    """
    data, filename = _read_and_encode(source)
    
    if not filename and isinstance(source, (str, Path)):
        filename = Path(source).name
    
    content_type = _detect_content_type(filename)
    
    if content_type == "image":
        ext = os.path.splitext(filename or "")[1].lower()
        media_type = IMAGE_EXTENSIONS.get(ext, _guess_media_type(filename, "image/jpeg"))
        return ImageContent(data=data, media_type=media_type, filename=filename)
    
    elif content_type == "audio":
        ext = os.path.splitext(filename or "")[1].lower()
        media_type = AUDIO_EXTENSIONS.get(ext, _guess_media_type(filename, "audio/mpeg"))
        return AudioContent(data=data, media_type=media_type, filename=filename)
    
    elif content_type == "document":
        ext = os.path.splitext(filename or "")[1].lower()
        media_type = DOCUMENT_EXTENSIONS.get(ext, _guess_media_type(filename, "application/pdf"))
        return DocumentContent(data=data, media_type=media_type, filename=filename)
    
    else:
        raise ValueError(
            f"Cannot detect file type for '{filename}'. "
            f"Supported extensions: {', '.join(list(IMAGE_EXTENSIONS) + list(AUDIO_EXTENSIONS) + list(DOCUMENT_EXTENSIONS))}"
        )


def load_url(url: str, filename: str | None = None) -> "ImageContent":
    """
    Download a file from URL and create appropriate content.
    
    Currently only supports images. For documents/audio, download first
    and use load_file() with the local path.
    
    Args:
        url: URL to download from
        filename: Optional filename (extracted from URL if not provided)
        
    Returns:
        ImageContent with downloaded and encoded data
        
    Example:
        from nebula import Memory, load_url
        
        memory = Memory(
            collection_id="my-collection",
            content=[
                load_url("https://example.com/photo.jpg"),
                "Describe this image"
            ]
        )
    """
    import httpx
    
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        data = response.content
    
    # Extract filename from URL if not provided
    if filename is None:
        from urllib.parse import urlparse
        path = urlparse(url).path
        filename = os.path.basename(path) if path else None
    
    # Detect media type from content-type header or filename
    content_type_header = response.headers.get("content-type", "").split(";")[0].strip()
    
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            media_type = IMAGE_EXTENSIONS.get(ext, content_type_header or "image/jpeg")
            return ImageContent(
                data=base64.b64encode(data).decode("utf-8"),
                media_type=media_type,
                filename=filename
            )
    
    # Default to image for URLs
    return ImageContent(
        data=base64.b64encode(data).decode("utf-8"),
        media_type=content_type_header or "image/jpeg",
        filename=filename
    )


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
class ImageContent:
    """Image content for multimodal messages.
    
    Create from file path (easiest):
        ImageContent.from_file("photo.jpg")
        ImageContent.from_file(Path("photos/vacation.png"))
    
    Create from bytes:
        ImageContent.from_bytes(image_bytes, filename="photo.jpg")
    
    Create from file object:
        with open("photo.jpg", "rb") as f:
            ImageContent.from_file(f)
    
    Create manually with base64 (advanced):
        ImageContent(data=base64_string, media_type="image/jpeg")
    """
    data: str  # Base64 encoded image data
    media_type: str = "image/jpeg"  # MIME type (e.g., 'image/jpeg', 'image/png')
    filename: str | None = None
    type: str = "image"
    
    @classmethod
    def from_file(cls, source: str | Path | BinaryIO) -> "ImageContent":
        """
        Create ImageContent from a file path, Path object, or file-like object.
        
        Args:
            source: File path string, Path object, or opened file (binary mode)
            
        Returns:
            ImageContent with base64-encoded data and auto-detected media type
            
        Example:
            # From file path
            img = ImageContent.from_file("photo.jpg")
            
            # From Path object
            img = ImageContent.from_file(Path("photos/vacation.png"))
            
            # From file object
            with open("photo.jpg", "rb") as f:
                img = ImageContent.from_file(f)
        """
        data, filename = _read_and_encode(source)
        
        # Detect media type from extension
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            media_type = IMAGE_EXTENSIONS.get(ext, _guess_media_type(filename, "image/jpeg"))
        else:
            media_type = "image/jpeg"
        
        return cls(data=data, media_type=media_type, filename=filename)
    
    @classmethod
    def from_bytes(cls, data: bytes, filename: str | None = None, media_type: str | None = None) -> "ImageContent":
        """
        Create ImageContent from raw bytes.
        
        Args:
            data: Raw image bytes
            filename: Optional filename (used for media type detection)
            media_type: Optional explicit media type (auto-detected if not provided)
            
        Returns:
            ImageContent with base64-encoded data
        """
        encoded = base64.b64encode(data).decode("utf-8")
        
        if media_type is None:
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                media_type = IMAGE_EXTENSIONS.get(ext, _guess_media_type(filename, "image/jpeg"))
            else:
                media_type = "image/jpeg"
        
        return cls(data=encoded, media_type=media_type, filename=filename)
    
    @classmethod
    def from_url(cls, url: str, filename: str | None = None) -> "ImageContent":
        """
        Create ImageContent by downloading from a URL.
        
        Args:
            url: URL to download the image from
            filename: Optional filename (extracted from URL if not provided)
            
        Returns:
            ImageContent with base64-encoded data
            
        Note: Requires httpx to be installed (included with nebula-client)
        """
        import httpx
        
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            data = response.content
        
        # Extract filename from URL if not provided
        if filename is None:
            from urllib.parse import urlparse
            path = urlparse(url).path
            filename = os.path.basename(path) if path else None
        
        # Detect media type from content-type header or filename
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type and content_type.startswith("image/"):
            media_type = content_type
        elif filename:
            ext = os.path.splitext(filename)[1].lower()
            media_type = IMAGE_EXTENSIONS.get(ext, "image/jpeg")
        else:
            media_type = "image/jpeg"
        
        return cls(
            data=base64.b64encode(data).decode("utf-8"),
            media_type=media_type,
            filename=filename
        )


@dataclass
class AudioContent:
    """Audio content for transcription.
    
    Supported formats: MP3, WAV, M4A, OGG, FLAC, AAC, WebM
    Transcribed using Whisper via LiteLLM.
    
    Create from file path (easiest):
        AudioContent.from_file("recording.mp3")
        AudioContent.from_file(Path("audio/meeting.wav"))
    
    Create from bytes:
        AudioContent.from_bytes(audio_bytes, filename="recording.mp3")
    
    Create manually with base64 (advanced):
        AudioContent(data=base64_string, media_type="audio/mp3")
    """
    data: str  # Base64 encoded audio data
    media_type: str = "audio/mpeg"  # MIME type (e.g., 'audio/mpeg', 'audio/wav')
    filename: str | None = None
    duration_seconds: float | None = None
    type: str = "audio"
    
    @classmethod
    def from_file(cls, source: str | Path | BinaryIO) -> "AudioContent":
        """
        Create AudioContent from a file path, Path object, or file-like object.
        
        Args:
            source: File path string, Path object, or opened file (binary mode)
            
        Returns:
            AudioContent with base64-encoded data and auto-detected media type
            
        Example:
            # From file path
            audio = AudioContent.from_file("recording.mp3")
            
            # From Path object
            audio = AudioContent.from_file(Path("audio/meeting.wav"))
        """
        data, filename = _read_and_encode(source)
        
        # Detect media type from extension
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            media_type = AUDIO_EXTENSIONS.get(ext, _guess_media_type(filename, "audio/mpeg"))
        else:
            media_type = "audio/mpeg"
        
        return cls(data=data, media_type=media_type, filename=filename)
    
    @classmethod
    def from_bytes(cls, data: bytes, filename: str | None = None, media_type: str | None = None) -> "AudioContent":
        """
        Create AudioContent from raw bytes.
        
        Args:
            data: Raw audio bytes
            filename: Optional filename (used for media type detection)
            media_type: Optional explicit media type (auto-detected if not provided)
            
        Returns:
            AudioContent with base64-encoded data
        """
        encoded = base64.b64encode(data).decode("utf-8")
        
        if media_type is None:
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                media_type = AUDIO_EXTENSIONS.get(ext, _guess_media_type(filename, "audio/mpeg"))
            else:
                media_type = "audio/mpeg"
        
        return cls(data=encoded, media_type=media_type, filename=filename)


@dataclass
class DocumentContent:
    """Document content for text extraction.
    
    Supported formats: PDF, DOC, DOCX, TXT, CSV, RTF
    PDFs are processed with VLM OCR or pypdf depending on fast_mode setting.
    
    Create from file path (easiest):
        DocumentContent.from_file("report.pdf")
        DocumentContent.from_file(Path("docs/contract.docx"))
    
    Create from bytes:
        DocumentContent.from_bytes(pdf_bytes, filename="report.pdf")
    
    Create manually with base64 (advanced):
        DocumentContent(data=base64_string, media_type="application/pdf")
    """
    data: str  # Base64 encoded document data
    media_type: str = "application/pdf"  # MIME type
    filename: str | None = None
    type: str = "document"
    
    @classmethod
    def from_file(cls, source: str | Path | BinaryIO) -> "DocumentContent":
        """
        Create DocumentContent from a file path, Path object, or file-like object.
        
        Args:
            source: File path string, Path object, or opened file (binary mode)
            
        Returns:
            DocumentContent with base64-encoded data and auto-detected media type
            
        Example:
            # From file path
            doc = DocumentContent.from_file("report.pdf")
            
            # From Path object
            doc = DocumentContent.from_file(Path("docs/contract.docx"))
        """
        data, filename = _read_and_encode(source)
        
        # Detect media type from extension
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            media_type = DOCUMENT_EXTENSIONS.get(ext, _guess_media_type(filename, "application/pdf"))
        else:
            media_type = "application/pdf"
        
        return cls(data=data, media_type=media_type, filename=filename)
    
    @classmethod
    def from_bytes(cls, data: bytes, filename: str | None = None, media_type: str | None = None) -> "DocumentContent":
        """
        Create DocumentContent from raw bytes.
        
        Args:
            data: Raw document bytes
            filename: Optional filename (used for media type detection)
            media_type: Optional explicit media type (auto-detected if not provided)
            
        Returns:
            DocumentContent with base64-encoded data
        """
        encoded = base64.b64encode(data).decode("utf-8")
        
        if media_type is None:
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                media_type = DOCUMENT_EXTENSIONS.get(ext, _guess_media_type(filename, "application/pdf"))
            else:
                media_type = "application/pdf"
        
        return cls(data=encoded, media_type=media_type, filename=filename)


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
ContentPart = ImageContent | AudioContent | DocumentContent | S3FileRef | TextContent | dict[str, Any]


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
    
    Multimodal Support:
    - content can be a string (text-only) or list of ContentPart objects
    - For images, use ImageContent or S3FileRef
    - Images are processed with a vision model (Qwen3-VL by default)
    - For files >5MB, upload to S3 first using client.get_upload_url()
    
    Examples:
        # Text-only memory
        Memory(collection_id="...", content="Hello world")
        
        # Multimodal with image (base64)
        Memory(
            collection_id="...",
            content=[
                TextContent(text="What's in this image?"),
                ImageContent(data="base64...", media_type="image/jpeg")
            ]
        )
        
        # Large file via S3
        Memory(
            collection_id="...",
            content=[S3FileRef(s3_key="multimodal/abc/image.jpg")]
        )
    """

    collection_id: str
    content: str | list[ContentPart]
    role: str | None = None  # user, assistant, or custom
    memory_id: str | None = None  # ID of existing memory to append to
    metadata: dict[str, Any] = field(default_factory=dict)
    authority: float | None = None  # Optional authority score (0.0 - 1.0)
    vision_model: str | None = None  # Vision model for image processing (default: modal/qwen3-vl-thinking)
    audio_model: str | None = None  # Audio transcription model (default: whisper-1)
    fast_mode: bool | None = None  # Use fast text extraction for PDFs (None = use backend default: False/VLM)


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


# Hierarchical Memory Recall types (matches backend MemoryRecall structure)


@dataclass
class MemoryRecall:
    """Hierarchical memory recall result containing entities, facts, and utterances.

    Nested data (entities, facts, utterances, focus) are stored as raw dicts
    for performance - no parsing overhead.

    Entity dict keys: entity_id, entity_name, entity_category, activation_score,
                      activation_reason, traversal_depth, profile
    Fact dict keys: fact_id, entity_id, entity_name, facet_name, subject, predicate,
                    object_value, activation_score, extraction_confidence,
                    corroboration_count, source_chunk_ids
    Utterance dict keys: chunk_id, text, activation_score, speaker_name, source_role,
                         timestamp, display_name, supporting_fact_ids, metadata
    Focus dict keys: schema_weight, fact_weight, episodic_weight
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
    def from_dict(cls, data: dict[str, Any], query: str) -> "MemoryRecall":
        """Create a MemoryRecall from a dictionary response."""
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
