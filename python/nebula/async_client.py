"""
Async client for the Nebula Client SDK
"""

import hashlib
import json
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
    MemoryResponse,
    SearchResult,
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
    ) -> list[Collection]:
        params = {"limit": limit, "offset": offset}
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
    async def create_conversation(
        self,
        collection_ref: str,
        messages: list[dict[str, Any]],
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a new conversation with messages.

        Args:
            collection_ref: Collection UUID or name
            messages: List of message dicts with 'role' and 'content' keys
            name: Optional name for the conversation
            metadata: Optional conversation-level metadata

        Returns:
            Conversation ID (UUID string)

        Example:
            >>> conv_id = await client.create_conversation(
            ...     collection_ref="my-collection",
            ...     messages=[
            ...         {"role": "user", "content": "Hello!"},
            ...         {"role": "assistant", "content": "Hi there!"}
            ...     ]
            ... )
        """
        payload = {
            "collection_ref": collection_ref,
            "engram_type": "conversation",
            "messages": messages,
            "metadata": metadata or {},
        }
        if name:
            payload["name"] = name

        response = await self._make_request_async(
            "POST", "/v1/memories", json_data=payload
        )

        if isinstance(response, dict) and "results" in response:
            return str(
                response["results"].get("id") or response["results"].get("engram_id")
            )
        raise NebulaClientException("Failed to create conversation: invalid response")

    async def create_document_text(
        self,
        collection_ref: str,
        raw_text: str,
        metadata: dict[str, Any] | None = None,
        ingestion_mode: str = "fast",
    ) -> str:
        """
        Create a new document from raw text.

        Args:
            collection_ref: Collection UUID or name
            raw_text: Text content of the document
            metadata: Optional document metadata
            ingestion_mode: Ingestion mode ("fast", "hi-res", or "custom")

        Returns:
            Document ID (UUID string)

        Example:
            >>> doc_id = await client.create_document_text(
            ...     collection_ref="my-collection",
            ...     raw_text="This is my document content."
            ... )
        """
        payload = {
            "collection_ref": collection_ref,
            "engram_type": "document",
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
        collection_ref: str,
        chunks: list[str],
        metadata: dict[str, Any] | None = None,
        ingestion_mode: str = "fast",
    ) -> str:
        """
        Create a new document from pre-chunked text.

        Args:
            collection_ref: Collection UUID or name
            chunks: List of text chunks
            metadata: Optional document metadata
            ingestion_mode: Ingestion mode ("fast", "hi-res", or "custom")

        Returns:
            Document ID (UUID string)
        """
        payload = {
            "collection_ref": collection_ref,
            "engram_type": "document",
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
            doc_metadata = dict(memory.metadata or {})
            # Use files= to send as multipart/form-data (FastAPI expects this with Form(...))
            # Note: Parse UUID from string if needed
            try:
                from uuid import UUID

                collection_uuid: UUID | str = UUID(memory.collection_id)
            except (ValueError, TypeError):
                collection_uuid = memory.collection_id

            files = {
                "engram_type": (None, "conversation"),
                "name": (None, name or "Conversation"),
                "metadata": (None, json.dumps(doc_metadata)),
                "collection_ids": (None, json.dumps([str(collection_uuid)])),
            }

            url = f"{self.base_url}/v1/memories"
            headers = self._build_auth_headers(include_content_type=False)
            # Debug logging
            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"Creating conversation with files: {files}")
            response = await self._client.post(url, files=files, headers=headers)
            logger.info(
                f"Response status: {response.status_code}, content: {response.text if response.content else 'empty'}"
            )
            if response.status_code not in (200, 202):
                error_data = response.json() if response.content else {}
                logger.error(f"Failed to create conversation. Error data: {error_data}")
                raise NebulaException(
                    error_data.get(
                        "message",
                        f"Failed to create conversation: {response.status_code}",
                    ),
                    response.status_code,
                    error_data,
                )
            resp_data = response.json()
            if isinstance(resp_data, dict) and "results" in resp_data:
                conv_id = resp_data["results"].get("engram_id") or resp_data[
                    "results"
                ].get("id")
                if not conv_id:
                    raise NebulaClientException(
                        "Failed to create conversation: no id returned"
                    )

                # If content and role provided, append initial message
                if memory.content and memory.role:
                    append_memory = Memory(
                        collection_id=memory.collection_id,
                        content=[  # type: ignore[arg-type]
                            {
                                "content": str(memory.content),
                                "role": memory.role,
                                "metadata": memory.metadata,
                                **(
                                    {"authority": float(memory.authority)}
                                    if memory.authority is not None
                                    else {}
                                ),
                            }
                        ],
                        memory_id=conv_id,
                        metadata={},
                    )
                    await self._append_to_memory(conv_id, append_memory)

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
        # Use files= to send as multipart/form-data (FastAPI expects this with Form(...))
        files = {
            "metadata": (None, json.dumps(doc_metadata)),
            "ingestion_mode": (None, "fast"),
            "collection_ids": (None, json.dumps([memory.collection_id])),
            "raw_text": (None, content_text),
        }

        url = f"{self.base_url}/v1/memories"
        headers = self._build_auth_headers(include_content_type=False)
        response = await self._client.post(url, files=files, headers=headers)
        if response.status_code not in (200, 202):
            error_data = response.json() if response.content else {}
            raise NebulaException(
                error_data.get(
                    "message", f"Failed to create engram: {response.status_code}"
                ),
                response.status_code,
                error_data,
            )
        response_data = response.json()
        if isinstance(response_data, dict) and "results" in response_data:
            if "engram_id" in response_data["results"]:
                return str(response_data["results"]["engram_id"])
            if "id" in response_data["results"]:
                return str(response_data["results"]["id"])
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

            # Create conversation if needed
            if key.startswith("__new__::"):
                # Pass a placeholder role to trigger conversation creation
                conv_id = await self.store_memory(
                    collection_id=collection_id,
                    content="",
                    role="assistant",  # Placeholder role to infer conversation type
                    name="Conversation",
                )
            else:
                conv_id = key

            # Append messages using new unified API
            messages = []
            for m in group:
                text = str(m.content or "")
                msg_meta = dict(m.metadata or {})
                messages.append({"content": text, "role": m.role, "metadata": msg_meta})

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
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        search_mode: str = "super",
        search_settings: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Search your memory collections with optional metadata filtering (async version).

        Args:
            query: Search query string
            collection_ids: Optional list of collection IDs or names to search within.
                        Can be UUIDs or collection names.
                        If not provided, searches across all your accessible collections.
            limit: Maximum number of results to return
            filters: Optional filters to apply to the search. Supports comprehensive metadata filtering
                    with MongoDB-like operators for both vector/chunk search and graph search.
            search_settings: Optional search configuration including search_mode ('basic'|'advanced')

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
            List of SearchResult objects containing both vector/chunk and graph search results
        """
        # Build effective search settings with simplified structure
        effective_settings: dict[str, Any] = dict(search_settings or {})
        effective_settings["limit"] = limit
        # Retrieval type is now handled internally by the backend
        user_filters: dict[str, Any] = dict(effective_settings.get("filters", {}))
        if filters:
            user_filters.update(filters)
        # Add cluster filter if collection_ids provided (supports both UUIDs and names)
        if collection_ids:
            # Filter out empty/invalid collection IDs
            valid_collection_ids = [
                cid for cid in collection_ids if cid and str(cid).strip()
            ]
            if valid_collection_ids:
                user_filters["collection_ids"] = {"$overlap": valid_collection_ids}
        effective_settings["filters"] = user_filters

        data = {
            "query": query,
            "search_mode": search_mode,
            "search_settings": effective_settings,
        }
        response = await self._make_request_async(
            "POST", "/v1/retrieval/search", json_data=data
        )
        if isinstance(response, dict) and "results" in response:
            agg = response["results"]
            chunk_results = agg.get("chunk_search_results", [])
            graph_results = agg.get("graph_search_results", [])
        else:
            chunk_results = []
            graph_results = []
        out: list[SearchResult] = []
        out.extend(SearchResult.from_dict(result) for result in chunk_results)
        for g in graph_results:
            out.append(SearchResult.from_graph_dict(g))
        return out

    async def list_conversations(
        self,
        limit: int = 100,
        offset: int = 0,
        collection_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        List conversations for the authenticated user (async version)

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            collection_ids: Optional list of collection IDs to filter conversations by

        Returns:
            List of conversation dictionaries
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        # Convert collection_ids to collection_ids for the API
        if collection_ids and len(collection_ids) > 0:
            params["collection_ids"] = collection_ids

        response = await self._make_request_async(
            "GET", "/v1/conversations", params=params
        )

        conversations: list[dict[str, Any]]
        if isinstance(response, dict) and "results" in response:
            conversations = response["results"]
        elif isinstance(response, list):
            conversations = response
        else:
            conversations = [response] if response else []

        return conversations

    async def get_conversation_messages(
        self, conversation_id: str
    ) -> list[MemoryResponse]:
        """
        Get conversation messages directly from the conversations API (async version)

        This method retrieves messages from a specific conversation using the dedicated
        conversations API endpoint, which provides accurate chronological ordering
        and preserves conversation context.

        Args:
            conversation_id: ID of the conversation to retrieve messages from

        Returns:
            List of MemoryResponse objects containing the conversation messages

        Raises:
            NebulaClientException: If conversation_id is empty
            NebulaException: For API errors
        """
        if not conversation_id:
            raise NebulaClientException("conversation_id must be provided")

        response = await self._make_request_async(
            "GET", f"/v1/conversations/{conversation_id}"
        )

        # Extract results from response
        if isinstance(response, dict) and "results" in response:
            messages_data = response["results"]
        elif isinstance(response, list):
            messages_data = response
        else:
            messages_data = []

        # Convert to MemoryResponse objects
        messages: list[MemoryResponse] = []

        for msg_resp in messages_data:
            if not isinstance(msg_resp, dict):
                continue

            # Extract message ID
            msg_id = str(msg_resp.get("id", ""))

            # Extract nested message content (API returns MessageResponse with nested message object)
            nested_msg = msg_resp.get("message", {})

            # Handle content - could be string or structured object
            raw_content = nested_msg.get("content")
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, dict):
                # Handle structured content
                content = (
                    raw_content.get("content")
                    or raw_content.get("text")
                    or str(raw_content)
                )
            else:
                content = str(raw_content) if raw_content is not None else ""

            # Extract role from nested message
            role = (
                nested_msg.get("role")
                or msg_resp.get("metadata", {}).get("role")
                or "user"
            )

            # Merge metadata from both response and nested message
            resp_metadata = msg_resp.get("metadata", {})
            msg_metadata = nested_msg.get("metadata", {})

            # Combine metadata with role information
            combined_metadata = {
                **resp_metadata,
                **msg_metadata,
                "source_role": role,  # Preserve original role from message
                "role": role,  # Ensure role is in metadata for UI compatibility
            }

            # Create MemoryResponse object
            memory_data = {
                "id": msg_id,
                "content": content,
                "metadata": combined_metadata,
                "created_at": msg_resp.get("created_at"),
                "collection_ids": msg_resp.get("collection_ids", []),
            }

            messages.append(MemoryResponse.from_dict(memory_data))

        return messages

    async def health_check(self) -> dict[str, Any]:
        return await self._make_request_async("GET", "/health")
