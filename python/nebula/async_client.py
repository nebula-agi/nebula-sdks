"""
Async client for the Nebula Client SDK
"""

import os
from typing import Any, cast
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
    ContentPart,
    Memory,
    MemoryResponse,
    TextContent,
)


class AsyncNebula:
    """
    Async client for interacting with Nebula API

    Mirrors the public API of `Nebula`, implemented using httpx.AsyncClient.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.trynebula.ai",
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
        return (
            public_part.startswith("key_") or public_part.startswith("neb_")
        ) and len(raw_part) > 0

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

    @staticmethod
    def _is_multimodal_content(content: Any) -> bool:
        """Check if content is a list of multimodal content parts (images, audio, documents)."""
        if not isinstance(content, list) or len(content) == 0:
            return False
        # Detect any typed part in the list (strings are allowed and will be wrapped as text).
        for part in content:
            if isinstance(part, dict) and "type" in part:
                return True
            if hasattr(part, "__dataclass_fields__"):
                return True
        return False

    @staticmethod
    def _normalize_content_parts(content: Any) -> list[ContentPart]:
        """Normalize arbitrary content into a list of ContentPart items.

        - If content is a list, strings are wrapped as TextContent, other items are passed through.
        - If content is not a list, it is wrapped as a single TextContent block.
        """
        if isinstance(content, list):
            normalized: list[ContentPart] = []
            for part in content:
                if isinstance(part, str):
                    normalized.append(TextContent(text=part))
                else:
                    normalized.append(cast(ContentPart, part))
            return normalized

        return [TextContent(text=str(content))]

    @staticmethod
    def _convert_content_parts(content: list[ContentPart]) -> list[dict[str, Any]]:
        """Convert a list of content parts (dataclasses or dicts) to API format."""
        parts = []
        for part in content:
            if hasattr(part, "__dataclass_fields__"):
                # Dataclass - convert to dict
                parts.append(
                    {k: getattr(part, k) for k in part.__dataclass_fields__.keys()}
                )
            elif isinstance(part, dict):
                parts.append(part)
            else:
                # Plain string - wrap as text
                parts.append({"type": "text", "text": str(part)})
        return parts

    async def _make_request_async(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | list[str] | str | None = None,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make an async HTTP request to the Nebula API

        Returns response JSON on 200, maps error codes to SDK exceptions.
        """
        url = urljoin(self.base_url, endpoint)
        headers = self._build_auth_headers(include_content_type=True)
        if extra_headers:
            headers.update(extra_headers)

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
        - Automatically handles multimodal content (images, audio, documents)

        Accepts either a `Memory` object or equivalent keyword arguments:
        - collection_id: str (required)
        - content: str | List[ContentPart] (required) - can include ImageContent, AudioContent, DocumentContent
        - memory_id: Optional[str] (if provided, appends to existing memory)
        - name: str (optional, used for conversation names)
        - role: Optional[str] (if provided, creates a conversation; otherwise creates a document)
        - metadata: Optional[dict]

        Returns: memory_id (for both conversations and documents)

        Raises:
            NebulaNotFoundException: If memory_id is provided but doesn't exist
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

        # If memory_id is present, append to existing memory
        if memory.memory_id:
            return await self._append_to_memory(memory.memory_id, memory)

        # Automatically infer memory type from role presence
        memory_type = "conversation" if memory.role else "document"

        # Handle conversation creation
        if memory_type == "conversation":
            doc_metadata = dict(memory.metadata or {})
            is_multimodal = self._is_multimodal_content(memory.content)

            # Build messages array if content and role are provided
            messages = []
            if memory.content and memory.role:
                msg_content: Any
                if is_multimodal:
                    msg_content = self._convert_content_parts(
                        self._normalize_content_parts(memory.content)
                    )
                else:
                    msg_content = str(memory.content)
                msg: dict[str, Any] = {
                    "role": memory.role,
                    "content": msg_content,
                    "metadata": memory.metadata or {},
                }
                if memory.authority is not None:
                    msg["authority"] = float(memory.authority)
                messages.append(msg)

            if not messages:
                raise NebulaClientException(
                    "Cannot create conversation without messages. Provide content and role."
                )

            # Backend infers engram_type from payload shape; omit engram_type.
            conv_payload: dict[str, Any] = {
                "collection_id": memory.collection_id,
                "messages": messages,
                "metadata": doc_metadata,
                "name": name or "Conversation",
            }

            response = await self._make_request_async(
                "POST", "/v1/memories", json_data=conv_payload
            )

            if isinstance(response, dict) and "results" in response:
                conv_id = response["results"].get("id") or response["results"].get(
                    "engram_id"
                )
                if not conv_id:
                    raise NebulaClientException(
                        "Failed to create conversation: no id returned"
                    )
                return str(conv_id)
            raise NebulaClientException(
                "Failed to create conversation: invalid response format"
            )

        # Handle document/text memory
        doc_metadata = dict(memory.metadata or {})
        doc_metadata["memory_type"] = "memory"

        # If authority provided for document, persist in metadata for chunk ranking
        if memory.authority is not None:
            try:
                auth_val = float(memory.authority)
                if 0.0 <= auth_val <= 1.0:
                    doc_metadata["authority"] = auth_val
            except Exception:
                pass
        # Backend infers engram_type from payload shape; omit engram_type.
        doc_payload: dict[str, Any] = {
            "collection_id": memory.collection_id,
            "metadata": doc_metadata,
            "ingestion_mode": "fast",
        }

        # Use the caller-supplied name, or infer from file content if available.
        doc_name = name
        if not doc_name and isinstance(memory.content, list):
            for part in memory.content:
                fn = getattr(part, "filename", None) or (
                    part.get("filename") if isinstance(part, dict) else None
                )
                if fn:
                    doc_name = fn
                    break
        if doc_name:
            doc_payload["name"] = doc_name

        # Handle multimodal vs plain text content.
        if self._is_multimodal_content(memory.content):
            doc_payload["content_parts"] = self._convert_content_parts(
                self._normalize_content_parts(memory.content)
            )
        else:
            content_text = str(memory.content or "")
            if not content_text:
                raise NebulaClientException("Content is required for document memories")
            doc_payload["raw_text"] = content_text

        response = await self._make_request_async(
            "POST", "/v1/memories", json_data=doc_payload
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
            NebulaNotFoundException: If memory_id doesn't exist
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

    async def store_memories(
        self,
        memories: list[Memory],
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Store multiple memories using the unified memory API.

        All items are processed identically to `store_memory`:
        - Conversations are grouped by conversation memory_id and sent in batches
        - Text/JSON/multimodal memories are stored individually
        - Multimodal content (images, audio, documents) is automatically processed

        Args:
            memories: List of Memory objects to store.
            metadata: Optional memory-level metadata for conversation groups.
                Each Memory's own metadata is used as per-message metadata.

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
                text: Any
                if self._is_multimodal_content(m.content):
                    text = self._convert_content_parts(
                        self._normalize_content_parts(m.content)
                    )
                else:
                    text = str(m.content or "")
                msg_meta = dict(m.metadata or {})
                # Skip empty messages
                if isinstance(text, str):
                    if not text.strip():
                        continue
                elif not text:
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
                    "metadata": dict(metadata or {}),
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
                    metadata=dict(metadata or {}),
                )
                await self._append_to_memory(conv_id, append_mem)
                results.extend([str(conv_id)] * len(group))

        # Process others (text/json/multimodal) individually - store_memory handles multimodal
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
                response = await self._make_request_async(
                    "POST",
                    "/v1/memories/delete",
                    json_data=memory_ids,  # type: ignore[arg-type]
                )
                result: bool | dict[str, Any] = (
                    response.get("success", False)
                    if isinstance(response, dict)
                    else True
                )
                return result
        else:
            # Batch deletion
            response = await self._make_request_async(
                "POST",
                "/v1/memories/delete",
                json_data=memory_ids,  # type: ignore[arg-type]
            )
            batch_result: bool | dict[str, Any] = response
            return batch_result

    async def delete_source(self, source_id: str) -> bool:
        """
        Delete a specific source within a memory.

        Args:
            source_id: The ID of the source to delete

        Returns:
            True if successful

        Raises:
            NebulaNotFoundException: If source_id doesn't exist
        """
        try:
            await self._make_request_async("DELETE", f"/v1/sources/{source_id}")
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(source_id, "Source") from e
            raise

    async def update_source(
        self, source_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Update a specific source within a memory.

        Args:
            source_id: The ID of the source to update
            content: New content for the source
            metadata: Optional metadata to update

        Returns:
            True if successful

        Raises:
            NebulaNotFoundException: If source_id doesn't exist
        """
        payload: dict[str, Any] = {"content": content}
        if metadata is not None:
            payload["metadata"] = metadata

        try:
            await self._make_request_async(
                "PATCH", f"/v1/sources/{source_id}", json_data=payload
            )
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(source_id, "Source") from e
            raise

    async def list_memories(
        self,
        *,
        collection_ids: list[str],
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
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
        memories: list[Memory] = []
        for doc in documents:
            # Let the model map fields appropriately
            memories.append(Memory.from_dict(doc))
        return memories

    async def get_memory(self, memory_id: str) -> Memory:
        """
        Get a specific memory by memory ID

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            Memory object
        """
        response = await self._make_request_async("GET", f"/v1/memories/{memory_id}")

        # Unwrap {"results": {...}} envelope if present
        data = (
            response.get("results", response)
            if isinstance(response, dict)
            else response
        )
        return Memory.from_dict(data)

    async def search(
        self,
        query: str,
        *,
        collection_ids: list[str] | None = None,
        effort: str | None = None,
        filters: dict[str, Any] | None = None,
        search_settings: dict[str, Any] | None = None,
    ) -> MemoryResponse:
        """
        Search your memory collections with optional metadata filtering (async version).

        Args:
            query: Search query string
            collection_ids: Optional list of collection IDs or names to search within.
                        Can be UUIDs or collection names.
                        If not provided, searches across all your accessible collections.
            effort: Compute effort budget (auto/low/medium/high). Controls traversal compute, not MemoryResponse size.
            filters: Optional filters to apply to the search. Supports comprehensive metadata filtering
                    with MongoDB-like operators for both vector/chunk search and graph search.
            search_settings: Optional advanced search settings including:
                - semantic_weight: Weight for semantic search (0-1, default: 0.8)
                - fulltext_weight: Weight for fulltext search (0-1, default: 0.2)
                - verbose: Include full metadata, UUIDs, and confidence fields (default: False)
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
            MemoryResponse object containing hierarchical memory structure with entities, semantics,
            and sources
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

        # Collection affinity: send header for consistent-hash routing.
        # Single-collection: send the ID directly. Multi-collection: send a stable
        # synthetic key so requests for the same set land on the same pod.
        extra_headers: dict[str, str] | None = None
        cids = data.get("collection_ids")
        if isinstance(cids, list) and len(cids) == 1:
            extra_headers = {"X-Nebula-Collection-Id": str(cids[0])}
        elif isinstance(cids, list) and len(cids) > 1:
            extra_headers = {
                "X-Nebula-Collection-Id": ",".join(sorted(str(c) for c in cids))
            }

        response = await self._make_request_async(
            "POST", "/v1/memories/search", json_data=data, extra_headers=extra_headers
        )

        # Backend returns MemoryResponse wrapped in { results: MemoryResponse }
        # The @base_endpoint decorator always wraps successful responses as {"results": MemoryResponse}
        return MemoryResponse.from_dict(response["results"], query)

    # Connector Methods

    @staticmethod
    def _unwrap(response: dict[str, Any]) -> Any:
        """Extract ``results`` from the API response envelope."""
        return response.get("results", response)

    async def list_providers(self) -> list[str]:
        """List available connector providers."""
        return cast(
            list[str],
            self._unwrap(
                await self._make_request_async("GET", "/v1/connectors/providers")
            ),
        )

    async def connect_provider(
        self,
        provider: str,
        collection_id: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start an OAuth connection flow for a provider.

        Returns dict with ``auth_url`` and ``state``.
        """
        body: dict[str, Any] = {"collection_id": collection_id}
        if config is not None:
            body["config"] = config
        return cast(
            dict[str, Any],
            self._unwrap(
                await self._make_request_async(
                    "POST", f"/v1/connectors/{provider}/connect", json_data=body
                )
            ),
        )

    async def list_connections(self, collection_id: str) -> list[dict[str, Any]]:
        """List active connections for a collection."""
        return cast(
            list[dict[str, Any]],
            self._unwrap(
                await self._make_request_async(
                    "GET", "/v1/connectors", params={"collection_id": collection_id}
                )
            ),
        )

    async def list_folders(
        self,
        connection_id: str,
        parent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Browse Google Drive folders for a connection."""
        params: dict[str, Any] = {}
        if parent_id is not None:
            params["parent_id"] = parent_id
        return cast(
            list[dict[str, Any]],
            self._unwrap(
                await self._make_request_async(
                    "GET",
                    f"/v1/connectors/{connection_id}/folders",
                    params=params or None,
                )
            ),
        )

    async def list_channels(self, connection_id: str) -> list[dict[str, Any]]:
        """List Slack channels for a connection."""
        return cast(
            list[dict[str, Any]],
            self._unwrap(
                await self._make_request_async(
                    "GET", f"/v1/connectors/{connection_id}/channels"
                )
            ),
        )

    async def get_connection(self, connection_id: str) -> dict[str, Any]:
        """Get a single connection by ID."""
        return cast(
            dict[str, Any],
            self._unwrap(
                await self._make_request_async("GET", f"/v1/connectors/{connection_id}")
            ),
        )

    async def trigger_sync(self, connection_id: str) -> dict[str, Any]:
        """Manually trigger a sync for a connection."""
        return cast(
            dict[str, Any],
            self._unwrap(
                await self._make_request_async(
                    "POST", f"/v1/connectors/{connection_id}/sync"
                )
            ),
        )

    async def update_connection_config(
        self,
        connection_id: str,
        config: dict[str, Any],
        apply: str = "full_resync",
    ) -> dict[str, Any]:
        """Update connection config (e.g., folder/channel selection)."""
        return cast(
            dict[str, Any],
            self._unwrap(
                await self._make_request_async(
                    "PATCH",
                    f"/v1/connectors/{connection_id}/config",
                    json_data={"config": config, "apply": apply},
                )
            ),
        )

    async def disconnect(
        self,
        connection_id: str,
        delete_memories: bool = False,
    ) -> dict[str, Any]:
        """Disconnect an external data source."""
        params: dict[str, Any] = {}
        if delete_memories:
            params["delete_memories"] = "true"
        return cast(
            dict[str, Any],
            self._unwrap(
                await self._make_request_async(
                    "DELETE",
                    f"/v1/connectors/{connection_id}",
                    params=params or None,
                )
            ),
        )

    async def health_check(self) -> dict[str, Any]:
        return await self._make_request_async("GET", "/v1/health")

    # ------------------------------------------------------------------
    # Device Memory
    # ------------------------------------------------------------------

    async def export_snapshot(self, collection_id: str) -> dict[str, Any]:
        """Export a collection's full graph state as a portable snapshot."""
        response = await self._make_request_async(
            "POST",
            "/v1/device-memory/snapshot/export",
            json_data={"collection_id": collection_id},
        )
        return cast(dict[str, Any], self._unwrap(response))

    async def import_snapshot(self, snapshot: dict[str, Any]) -> str:
        """Import a snapshot into an ephemeral server-side collection.

        Returns the ephemeral collection ID.
        """
        response = await self._make_request_async(
            "POST",
            "/v1/device-memory/snapshot/import",
            json_data={"snapshot": snapshot},
        )
        result = self._unwrap(response)
        return str(result.get("ephemeral_collection_id", ""))  # type: ignore[union-attr]

    async def compute(self, request: dict[str, Any]) -> dict[str, Any]:
        """Run extraction and consolidation over new events.

        Returns a PatchEnvelope dict with put/delete ops and the next root hash.
        """
        response = await self._make_request_async(
            "POST",
            "/v1/device-memory/compute",
            json_data={"request": request},
        )
        return cast(dict[str, Any], self._unwrap(response))

    async def query_snapshot(
        self,
        snapshot: dict[str, Any],
        query: str,
        *,
        query_embedding: list[float] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Run stateless traversal over a client-provided snapshot.

        Returns dict with ``entities`` and ``relationships`` lists.
        """
        data: dict[str, Any] = {
            "snapshot": snapshot,
            "query": query,
            "limit": limit,
        }
        if query_embedding:
            data["query_embedding"] = query_embedding
        response = await self._make_request_async(
            "POST",
            "/v1/device-memory/query",
            json_data=data,
        )
        return cast(dict[str, Any], self._unwrap(response))
