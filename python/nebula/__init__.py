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
    Chunk,
    Collection,
    Memory,
    MemoryRecall,
    MemoryResponse,
    SearchResult,
)

__version__ = "2.1.4"
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
]
