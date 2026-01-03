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
    AudioContent,
    Chunk,
    Collection,
    DocumentContent,
    ImageContent,
    Memory,
    MemoryRecall,
    MemoryResponse,
    S3FileRef,
    SearchResult,
    TextContent,
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
    "Chunk",
    # Multimodal content types
    "AudioContent",
    "DocumentContent",
    "ImageContent",
    "S3FileRef",
    "TextContent",
]
