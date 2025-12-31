"""
Nebula Client SDK - A clean, intuitive SDK for Nebula API

This SDK provides a simplified interface to Nebula's memory and retrieval capabilities,
focusing on chunks and hiding the complexity of the underlying Nebula system.
"""

from .async_client import AsyncNebula
from .client import Nebula
from .exceptions import (
    NebulaAuthenticationException,
    NebulaClientException,
    NebulaException,
    NebulaNotFoundException,
    NebulaRateLimitException,
    NebulaValidationException,
)
from .models import (
    AgentResponse,
    AudioContent,
    Chunk,
    Collection,
    DocumentContent,
    ImageContent,
    Memory,
    MemoryRecall,
    MemoryResponse,
    RetrievalType,
    S3FileRef,
    SearchResult,
    TextContent,
    # Helper functions for loading files
    load_file,
    load_url,
)

__version__ = "2.1.5"
__all__ = [
    "Nebula",
    "AsyncNebula",
    "NebulaException",
    "NebulaClientException",
    "NebulaAuthenticationException",
    "NebulaRateLimitException",
    "NebulaValidationException",
    "NebulaNotFoundException",
    "Memory",
    "MemoryResponse",
    "MemoryRecall",
    "Collection",
    "SearchResult",
    "AgentResponse",
    "Chunk",
    "RetrievalType",
    # Multimodal helpers (recommended - auto-detects file type)
    "load_file",
    "load_url",
    # Multimodal content types (for advanced use)
    "AudioContent",
    "DocumentContent",
    "ImageContent",
    "S3FileRef",
    "TextContent",
]
