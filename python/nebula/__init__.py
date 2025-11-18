"""
Nebula Client SDK - A clean, intuitive SDK for Nebula API

This SDK provides a simplified interface to Nebula's memory and retrieval capabilities,
focusing on chunks and hiding the complexity of the underlying Nebula system.
"""

from .client import NebulaClient
from .async_client import AsyncNebulaClient
from .exceptions import (
    NebulaException,
    NebulaClientException,
    NebulaAuthenticationException,
    NebulaRateLimitException,
    NebulaValidationException,
    NebulaNotFoundException,
)
from .models import Memory, MemoryResponse, Collection, SearchResult, AgentResponse, Chunk

__version__ = "0.1.8"
__all__ = [
    "NebulaClient",
    "AsyncNebulaClient",
    "NebulaException",
    "NebulaClientException",
    "NebulaAuthenticationException",
    "NebulaRateLimitException",
    "NebulaValidationException",
    "NebulaNotFoundException",
    "Memory",
    "MemoryResponse",
    "Collection",
    "SearchResult",
    "AgentResponse",
    "Chunk",
] 