"""
Async client for the Nebula Client SDK
"""

import hashlib
import os
from typing import Any
from urllib.parse import urljoin

import httpx

from .exceptions import (
    NebulaAuthenticationException,
    NebulaClientException,
    NebulaException,
    NebulaNotFoundException,
    NebulaRateLimitException,
    NebulaValidationException,
)
from .models import (
    Collection,
    Memory,
    MemoryRecall,
    MemoryResponse,
)


class AsyncNebula:
    """
    Async client for interacting with Nebula API

    Mirrors the public API of `Nebula`, implemented using httpx.AsyncClient.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.nebulacloud.app",
        timeout: float = 120.0,  # Increased from 30s to handle bulk operations & network delays
    ):
        """
        Initialize the async Nebula client

        Args:
            api_key: Your Nebula API key. If not provided, will look for NEBULA_API_KEY env var
            base_url: Base URL for the Nebula API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("NEBULA_API_KEY")
        if not self.api_key:
            raise NebulaClientException(
                "API key is required. Pass it to the constructor or set NEBULA_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        # Lazily initialized tokenizer encoder for token counting
        self._token_encoder = None  # type: ignore[var-annotated]

    async def __aenter__(self) -> "AsyncNebula":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying async HTTP client"""
        await self._client.aclose()

    # Compatibility alias
    async def close(self) -> None:
        await self.aclose()

    def _is_nebula_api_key(self, token: str | None = None) -> bool:
        """Detect if a token looks like a Nebula API key (public.raw)."""
        candidate = token or self.api_key
        if not candidate:
            return False
        if candidate.count(".") != 1:
            return False
        public_part, raw_part = candidate.split(".", 1)
        return public_part.startswith("key_") and len(raw_part) > 0

    def _build_auth_headers(self, include_content_type: bool = True) -> dict[str, str]:
        """Build authentication headers.

        - If the provided credential looks like a Nebula API key, send it via X-API-Key
          to avoid JWT parsing on Supabase-auth deployments.
        - Otherwise, send it as a Bearer token.
        - Optionally include Content-Type: application/json for JSON requests.
        """
        headers: dict[str, str] = {}
        if self._is_nebula_api_key():
            headers["X-API-Key"] = self.api_key  # type: ignore[assignment]
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    async def _make_request_async(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an async HTTP request to the Nebula API

        Returns response JSON on 200, maps error codes to SDK exceptions.
        """
        url = urljoin(self.base_url, endpoint)
        headers = self._build_auth_headers(include_content_type=True)

        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
            )

            if response.status_code in (200, 202):
                result: dict[str, Any] = response.json()
                return result
            elif response.status_code == 401:
                raise NebulaAuthenticationException("Invalid API key")
            elif response.status_code == 429:
                raise NebulaRateLimitException("Rate limit exceeded")
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                details = error_data.get("details")
                if details is not None and not isinstance(details, dict):
                    details = None
                raise NebulaValidationException(
                    error_data.get("message", "Validation error"),
                    details,
                )
            else:
                error_data = response.json() if response.content else {}
                raise NebulaException(
                    error_data.get("message", f"API error: {response.status_code}"),
                    response.status_code,
                    error_data,
                )
        except httpx.ConnectError as e:
            raise NebulaClientException(
                f"Failed to connect to {self.base_url}. Check your internet connection.",
                e,
            ) from e
        except httpx.TimeoutException as e:
            raise NebulaClientException(
                f"Request timed out after {self.timeout} seconds",
                e,
            ) from e
        except httpx.RequestError as e:
            raise NebulaClientException(f"Request failed: {str(e)}", e) from e

    # Collection Management Methods

    async def create_collection(
        self,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Collection:
        data: dict[str, Any] = {"name": name}
        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        response = await self._make_request_async(
            "POST", "/v1/collections", json_data=data
        )
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    async def get_collection(self, collection_id: str) -> Collection:
        response = await self._make_request_async(
            "GET", f"/v1/collections/{collection_id}"
        )
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    async def get_collection_by_name(self, name: str) -> Collection:
        response = await self._make_request_async("GET", f"/v1/collections/name/{name}")
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    async def list_collections(
        self,
        limit: int = 100,
        offset: int = 0,
        name: str | None = None,
    ) -> list[Collection]:
        """
        Get all collections

        Args:
            limit: Maximum number of collections to return
            offset: Number of collections to skip
            name: Optional name filter (case-insensitive exact match). Use this to find a collection ID by name.

        Returns:
            List of Collection objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if name is not None:
            params["name"] = name
        response = await self._make_request_async(
            "GET", "/v1/collections", params=params
        )
        if isinstance(response, dict) and "results" in response:
            collections: list[dict[str, Any]] = response["results"]
        elif isinstance(response, list):
            collections = response
        else:
            collections = [response]
        return [Collection.from_dict(collection) for collection in collections]

    async def update_collection(
        self,
        collection_id: str,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Collection:
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if metadata is not None:
            data["metadata"] = metadata
        response = await self._make_request_async(
            "POST", f"/v1/collections/{collection_id}", json_data=data
        )
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    async def delete_collection(self, collection_id: str) -> bool:
        await self._make_request_async("DELETE", f"/v1/collections/{collection_id}")
        return True

    # Unified write APIs (mirror sync client)
    async def create_document_text(
        self,
        collection_id: str,
        raw_text: str,
        metadata: dict[str, Any] | None = None,
        ingestion_mode: str = "fast",
    ) -> str:
        """
        Create a new document from raw text.

        Args:
            collection_id: Collection UUID (required)
            raw_text: Text content of the document
            metadata: Optional document metadata
            ingestion_mode: Ingestion mode ("fast", "hi-res", or "custom")

        Returns:
            Document ID (UUID string)

        Example:
            >>> collection = await client.collections.create(name="my-collection")
            >>> doc_id = await client.create_document_text(
            ...     collection_id=collection.id,
            ...     raw_text="This is my document content."
            ... )
        """
        payload = {
            "collection_id": collection_id,
            "raw_text": raw_text,
            "metadata": metadata or {},
            "ingestion_mode": ingestion_mode,
        }

        response = await self._make_request_async(
            "POST", "/v1/memories", json_data=payload
        )

        if isinstance(response, dict) and "results" in response:
            return str(
                response["results"].get("id") or response["results"].get("engram_id")
            )
        raise NebulaClientException("Failed to create document: invalid response")

    async def create_document_chunks(
        self,
        collection_id: str,
        chunks: list[str],
        metadata: dict[str, Any] | None = None,
        ingestion_mode: str = "fast",
    ) -> str:
        """
        Create a new document from pre-chunked text.

        Args:
            collection_id: Collection UUID (required)
            chunks: List of text chunks
            metadata: Optional document metadata
            ingestion_mode: Ingestion mode ("fast", "hi-res", or "custom")

        Returns:
            Document ID (UUID string)
        """
        payload = {
            "collection_id": collection_id,
            "chunks": chunks,
            "metadata": metadata or {},
            "ingestion_mode": ingestion_mode,
        }

        response = await self._make_request_async(
            "POST", "/v1/memories", json_data=payload
        )

        if isinstance(response, dict) and "results" in response:
            return str(
                response["results"].get("id") or response["results"].get("engram_id")
            )
        raise NebulaClientException("Failed to create document: invalid response")

    async def store_memory(
        self,
        memory: Memory | dict[str, Any] | None = None,
        name: str | None = None,
        **kwargs,
    ) -> str:
        """Store or append memory using the unified memory API.

        Behavior:
        - If memory_id is absent → creates new memory
        - If memory_id is present → appends to existing memory

        Accepts either a `Memory` object or equivalent keyword arguments:
        - collection_id: str (required)
        - content: str | List[str] | List[Dict] (required)
        - memory_id: Optional[str] (if provided, appends to existing memory)
        - name: str (optional, used for conversation names)
        - role: Optional[str] (if provided, creates a conversation; otherwise creates a document)
        - metadata: Optional[dict]

        Returns: memory_id (for both conversations and documents)

        Raises:
            NebulaNotFoundException: If engram_id is provided but doesn't exist
        """
        if memory is None:
            memory = Memory(
                collection_id=kwargs["collection_id"],
                content=kwargs.get("content", ""),
                role=kwargs.get("role"),
                memory_id=kwargs.get("memory_id"),
                metadata=kwargs.get("metadata", {}),
                authority=kwargs.get("authority"),
            )
        elif isinstance(memory, dict):
            memory = Memory(
                collection_id=memory["collection_id"],
                content=memory.get("content", ""),
                role=memory.get("role"),
                memory_id=memory.get("memory_id"),
                metadata=memory.get("metadata", {}),
                authority=memory.get("authority"),
            )

        # If engram_id is present, append to existing engram
        if memory.memory_id:
            return await self._append_to_memory(memory.memory_id, memory)

        # Automatically infer memory type from role presence
        memory_type = "conversation" if memory.role else "document"

        # Handle conversation creation
        if memory_type == "conversation":
            # Use JSON format matching the backend CreateMemoryRequest model.
            # Backend infers type from `messages` presence; we intentionally omit `engram_type`.
            messages: list[dict[str, Any]] = []
            if memory.content and memory.role:
                msg: dict[str, Any] = {
                    "role": memory.role,
                    "content": str(memory.content),
                    "metadata": memory.metadata or {},
                }
                if memory.authority is not None:
                    msg["authority"] = float(memory.authority)
                messages.append(msg)

            if not messages:
                raise NebulaClientException(
                    "Cannot create conversation without messages. Provide content and role."
                )

            payload: dict[str, Any] = {
                "collection_id": memory.collection_id,
                "messages": messages,
                "metadata": dict(memory.metadata or {}),
            }
            payload["name"] = name or "Conversation"

            response = await self._make_request_async(
                "POST", "/v1/memories", json_data=payload
            )
            if isinstance(response, dict) and "results" in response:
                conv_id = response["results"].get("engram_id") or response[
                    "results"
                ].get("id")
                if not conv_id:
                    raise NebulaClientException(
                        "Failed to create conversation: no id returned"
                    )
                return str(conv_id)

            raise NebulaClientException(
                "Failed to create conversation: invalid response format"
            )

        # Handle document/text memory
        content_text = str(memory.content or "")
        if not content_text:
            raise NebulaClientException("Content is required for document memories")

        content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        doc_metadata = dict(memory.metadata or {})
        doc_metadata["memory_type"] = "memory"
        doc_metadata["content_hash"] = content_hash
        # If authority provided for document, persist in metadata for chunk ranking
        if memory.authority is not None:
            try:
                auth_val = float(memory.authority)
                if 0.0 <= auth_val <= 1.0:
                    doc_metadata["authority"] = auth_val
            except Exception:
                pass
        payload = {
            "collection_id": memory.collection_id,
            "raw_text": content_text,
            "metadata": doc_metadata,
            "ingestion_mode": "fast",
        }

        response = await self._make_request_async(
            "POST", "/v1/memories", json_data=payload
        )
        if isinstance(response, dict) and "results" in response:
            if "engram_id" in response["results"]:
                return str(response["results"]["engram_id"])
            if "id" in response["results"]:
                return str(response["results"]["id"])
        return ""

    async def _append_to_memory(self, memory_id: str, memory: Memory) -> str:
        """Internal method to append content to an existing engram.

        Args:
            memory_id: The ID of the memory to append to
            memory: Memory object with collection_id, content, and optional metadata

        Returns:
            The memory_id (same as input)

        Raises:
            NebulaNotFoundException: If engram_id doesn't exist
        """
        collection_id = memory.collection_id
        content = memory.content
        metadata = memory.metadata

        # Build request payload
        payload: dict[str, Any] = {
            "collection_id": collection_id,
        }

        # Determine content type and set appropriate field
        if isinstance(content, list):
            if len(content) > 0 and isinstance(content[0], dict):
                # List of message dicts (conversation)
                payload["messages"] = content
            else:
                # List of strings (chunks)
                payload["chunks"] = content
        elif isinstance(content, str):
            # Raw text string
            payload["raw_text"] = content
        else:
            raise NebulaClientException(
                "content must be a string, list of strings, or list of message dicts"
            )

        if metadata is not None:
            payload["metadata"] = metadata

        # Call the unified append endpoint
        try:
            await self._make_request_async(
                "POST", f"/v1/memories/{memory_id}/append", json_data=payload
            )
            return memory_id
        except NebulaException as e:
            # Convert 404 errors to NebulaNotFoundException
            if e.status_code == 404:
                raise NebulaNotFoundException(memory_id, "Memory") from e
            raise

    async def store_memories(self, memories: list[Memory]) -> list[str]:
        """Store multiple memories using the unified memory API.

        All items are processed identically to `store_memory`:
        - Conversations are grouped by conversation memory_id and sent in batches
        - Text/JSON memories are stored individually with consistent metadata generation

        Returns: list of memory_ids in the same order as input memories
        """
        results: list[str] = []
        conv_groups: dict[str, list[Memory]] = {}
        others: list[Memory] = []

        for m in memories:
            if m.role:
                key = m.memory_id or f"__new__::{m.collection_id}"
                conv_groups.setdefault(key, []).append(m)
            else:
                others.append(m)

        # Process conversation groups using new unified API
        for key, group in conv_groups.items():
            collection_id = group[0].collection_id

            # Prepare messages for the conversation
            messages: list[dict[str, Any]] = []
            for m in group:
                text = str(m.content or "")
                msg_meta = dict(m.metadata or {})
                # Skip empty messages
                if not text.strip():
                    continue
                msg: dict[str, Any] = {
                    "content": text,
                    "role": m.role,
                    "metadata": msg_meta,
                }
                if m.authority is not None:
                    msg["authority"] = float(m.authority)
                messages.append(msg)

            if not messages:
                raise NebulaClientException(
                    "Cannot create/append conversation without messages. Provide non-empty content."
                )

            if key.startswith("__new__::"):
                # Create conversation with initial messages using JSON body (single request).
                payload: dict[str, Any] = {
                    "collection_id": collection_id,
                    "name": "Conversation",
                    "messages": messages,
                    "metadata": {},
                }
                resp = await self._make_request_async(
                    "POST", "/v1/memories", json_data=payload
                )
                if not (isinstance(resp, dict) and "results" in resp):
                    raise NebulaClientException(
                        "Failed to create conversation: invalid response format"
                    )
                conv_id = resp["results"].get("engram_id") or resp["results"].get("id")
                if not conv_id:
                    raise NebulaClientException(
                        "Failed to create conversation: no id returned"
                    )
                results.extend([str(conv_id)] * len(group))
            else:
                conv_id = key
                # Append messages to existing conversation
                append_mem = Memory(
                    collection_id=collection_id,
                    content=messages,  # type: ignore[arg-type]
                    memory_id=conv_id,
                    metadata={},
                )
                await self._append_to_memory(conv_id, append_mem)
                results.extend([str(conv_id)] * len(group))

        # Process others (text/json) individually
        for m in others:
            results.append(await self.store_memory(m))
        return results

    async def delete(self, memory_ids: str | list[str]) -> bool | dict[str, Any]:
        """
        Delete one or more memories.

        Args:
            memory_ids: Either a single memory ID (str) or a list of memory IDs

        Returns:
            For single deletion: Returns True if successful
            For batch deletion: Returns dict with deletion results
        """
        # Handle single ID vs list
        if isinstance(memory_ids, str):
            # Single deletion - use existing endpoint for backward compatibility
            try:
                await self._make_request_async("DELETE", f"/v1/memories/{memory_ids}")
                return True
            except Exception:
                # Try new unified endpoint
                try:
                    response = await self._make_request_async(
                        "POST", "/v1/memories/delete", json_data={"ids": memory_ids}
                    )
                    result: bool | dict[str, Any] = (
                        response.get("success", False)
                        if isinstance(response, dict)
                        else True
                    )
                    return result
                except Exception as e:
                    raise
        else:
            # Batch deletion
            response = await self._make_request_async(
                "POST", "/v1/memories/delete", json_data={"ids": memory_ids}
            )
            batch_result: bool | dict[str, Any] = response
            return batch_result

    async def delete_chunk(self, chunk_id: str) -> bool:
        """
        Delete a specific chunk or message within a memory.

        Args:
            chunk_id: The ID of the chunk to delete

        Returns:
            True if successful

        Raises:
            NebulaNotFoundException: If chunk_id doesn't exist
        """
        try:
            await self._make_request_async("DELETE", f"/v1/chunks/{chunk_id}")
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(chunk_id, "Chunk") from e
            raise

    async def update_chunk(
        self, chunk_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Update a specific chunk or message within a memory.

        Args:
            chunk_id: The ID of the chunk to update
            content: New content for the chunk
            metadata: Optional metadata to update

        Returns:
            True if successful

        Raises:
            NebulaNotFoundException: If chunk_id doesn't exist
        """
        payload: dict[str, Any] = {"content": content}
        if metadata is not None:
            payload["metadata"] = metadata

        try:
            await self._make_request_async(
                "PATCH", f"/v1/chunks/{chunk_id}", json_data=payload
            )
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(chunk_id, "Chunk") from e
            raise

    async def list_memories(
        self,
        *,
        collection_ids: list[str],
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryResponse]:
        if not collection_ids:
            raise NebulaClientException(
                "collection_ids must be provided to list_memories()."
            )
        params = {"limit": limit, "offset": offset, "collection_ids": collection_ids}
        response = await self._make_request_async("GET", "/v1/memories", params=params)
        if isinstance(response, dict) and "results" in response:
            documents = response["results"]
        elif isinstance(response, list):
            documents = response
        else:
            documents = [response]
        memories: list[MemoryResponse] = []
        for doc in documents:
            # Let the model map fields appropriately
            memories.append(MemoryResponse.from_dict(doc))
        return memories

    async def get_memory(self, memory_id: str) -> MemoryResponse:
        """
        Get a specific memory by memory ID

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            MemoryResponse object
        """
        response = await self._make_request_async("GET", f"/v1/memories/{memory_id}")
        return MemoryResponse.from_dict(response)

    async def search(
        self,
        query: str,
        *,
        collection_ids: list[str] | None = None,
        effort: str | None = None,
        filters: dict[str, Any] | None = None,
        search_settings: dict[str, Any] | None = None,
    ) -> MemoryRecall:
        """
        Search your memory collections with optional metadata filtering (async version).

        Args:
            query: Search query string
            collection_ids: Optional list of collection IDs or names to search within.
                        Can be UUIDs or collection names.
                        If not provided, searches across all your accessible collections.
            effort: Compute effort budget (auto/low/medium/high). Controls traversal compute, not MemoryRecall size.
            filters: Optional filters to apply to the search. Supports comprehensive metadata filtering
                    with MongoDB-like operators for both vector/chunk search and graph search.
            search_settings: Optional advanced search settings including:
                - semantic_weight: Weight for semantic search (0-1, default: 0.8)
                - fulltext_weight: Weight for fulltext search (0-1, default: 0.2)
                - include_metadata: Whether to include metadata in results (default: False)
                - include_scores: Whether to include scores in results (default: True)

        Filter Examples:
            Basic equality:
                filters={"metadata.category": {"$eq": "research"}}
                filters={"metadata.verified": True}  # Shorthand for $eq

            Numeric comparisons:
                filters={"metadata.score": {"$gte": 80}}
                filters={"metadata.priority": {"$lt": 5}}

            String matching:
                filters={"metadata.email": {"$ilike": "%@company.com"}}  # Case-insensitive
                filters={"metadata.title": {"$like": "Important%"}}      # Case-sensitive

            Array operations:
                filters={"metadata.tags": {"$overlap": ["ai", "ml"]}}        # Has any of these
                filters={"metadata.skills": {"$contains": ["python", "go"]}} # Has all of these
                filters={"metadata.categories": {"$in": ["tech", "science"]}}

            Nested paths:
                filters={"metadata.user.preferences.theme": {"$eq": "dark"}}
                filters={"metadata.settings.notifications.email": True}

            Logical operators:
                filters={
                    "$and": [
                        {"metadata.verified": True},
                        {"metadata.score": {"$gte": 80}},
                        {"metadata.tags": {"$overlap": ["important"]}}
                    ]
                }

                filters={
                    "$or": [
                        {"metadata.priority": {"$eq": "high"}},
                        {"metadata.urgent": True}
                    ]
                }

            Complex combinations:
                filters={
                    "$and": [
                        {"metadata.department": {"$eq": "engineering"}},
                        {"metadata.level": {"$gte": 5}},
                        {
                            "$or": [
                                {"metadata.skills": {"$overlap": ["python", "go"]}},
                                {"metadata.years_experience": {"$gte": 10}}
                            ]
                        }
                    ]
                }

        Supported Operators:
            Comparison: $eq, $ne, $lt, $lte, $gt, $gte
            String: $like (case-sensitive), $ilike (case-insensitive)
            Array: $in, $nin, $overlap, $contains
            JSONB: $json_contains
            Logical: $and, $or

        Returns:
            MemoryRecall object containing hierarchical memory structure with entities, facts,
            and utterances
        """
        # Build request data - pass params directly to API (no wrapping needed)
        data: dict[str, Any] = {
            "query": query,
        }

        if effort:
            data["effort"] = effort

        # Add optional params only if provided
        if collection_ids:
            # Filter out empty/invalid collection IDs
            valid_collection_ids = [
                cid for cid in collection_ids if cid and str(cid).strip()
            ]
            if valid_collection_ids:
                data["collection_ids"] = valid_collection_ids

        if filters:
            data["filters"] = filters

        if search_settings:
            data["search_settings"] = search_settings

        response = await self._make_request_async(
            "POST", "/v1/memories/search", json_data=data
        )

        # Backend returns MemoryRecall wrapped in { results: MemoryRecall }
        # The @base_endpoint decorator always wraps successful responses as {"results": MemoryRecall}
        return MemoryRecall.from_dict(response["results"], query)

    async def health_check(self) -> dict[str, Any]:
        return await self._make_request_async("GET", "/v1/health")
