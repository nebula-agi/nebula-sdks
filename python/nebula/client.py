"""
Main client for the Nebula Client SDK
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
from .models import Collection, Memory, MemoryRecall, MemoryResponse


class Nebula:
    """
    Simple client for interacting with Nebula API

    This client provides a clean interface to Nebula's memory and retrieval capabilities,
    focusing on the core functionality without the complexity of the underlying Nebula system.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.nebulacloud.app",
        timeout: float = 30.0,
    ):
        """
        Initialize the Nebula client

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
        self._client = httpx.Client(timeout=timeout)
        # Lazily initialized tokenizer encoder for token counting
        self._token_encoder = None  # type: ignore[var-annotated]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client"""
        self._client.close()

    def _is_nebula_api_key(self, token: str | None = None) -> bool:
        """Detect if a token looks like a Nebula API key (public.raw).

        Heuristic:
        - Exactly one dot
        - Public part starts with "key_" or "neb_"
        """
        candidate = token or self.api_key
        if not candidate:
            return False
        if candidate.count(".") != 1:
            return False
        public_part, raw_part = candidate.split(".", 1)
        return (public_part.startswith("key_") or public_part.startswith("neb_")) and len(raw_part) > 0

    def _build_auth_headers(self, include_content_type: bool = True) -> dict[str, str]:
        """Build authentication headers.

        - If the provided credential looks like an Nebula API key, send it via X-API-Key
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

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the Nebula API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/v1/memories")
            json_data: JSON data to send in request body
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            NebulaException: For API errors
            NebulaClientException: For client errors
        """
        url = urljoin(self.base_url, endpoint)
        headers = self._build_auth_headers(include_content_type=True)

        try:
            response = self._client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
            )

            # Handle different response status codes
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
                f"Request timed out after {self.timeout} seconds", e
            ) from e
        except httpx.RequestError as e:
            raise NebulaClientException(f"Request failed: {str(e)}", e) from e

    # Collection Management Methods

    def create_collection(
        self,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Collection:
        """
        Create a new collection
        """
        data: dict[str, Any] = {
            "name": name,
        }
        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        response = self._make_request("POST", "/v1/collections", json_data=data)
        # Unwrap 'results' if present
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    def get_collection(self, collection_id: str) -> Collection:
        """
        Get a specific collection by ID

        Args:
            collection_id: ID of the collection to retrieve

        Returns:
            Collection object
        """
        response = self._make_request("GET", f"/v1/collections/{collection_id}")
        # Unwrap 'results' if present
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    def get_collection_by_name(self, name: str) -> Collection:
        """
        Get a specific collection by name using the dedicated endpoint.
        """
        response = self._make_request("GET", f"/v1/collections/name/{name}")
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    def list_collections(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Collection]:
        """
        Get all collections

        Args:
            limit: Maximum number of collections to return
            offset: Number of collections to skip

        Returns:
            List of Collection objects
        """
        params = {
            "limit": limit,
            "offset": offset,
        }

        response = self._make_request("GET", "/v1/collections", params=params)

        if isinstance(response, dict) and "results" in response:
            collections = response["results"]
        elif isinstance(response, list):
            collections = response
        else:
            collections = [response]

        return [Collection.from_dict(collection) for collection in collections]

    def update_collection(
        self,
        collection_id: str,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Collection:
        """
        Update a collection

        Args:
            collection_id: ID of the collection to update
            name: New name for the collection
            description: New description for the collection
            metadata: New metadata for the collection

        Returns:
            Updated Collection object
        """
        # Existence validated server-side

        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if metadata is not None:
            data["metadata"] = metadata

        response = self._make_request(
            "POST", f"/v1/collections/{collection_id}", json_data=data
        )
        # Unwrap 'results' if present
        if isinstance(response, dict) and "results" in response:
            response = response["results"]
        return Collection.from_dict(response)

    def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a collection

        Args:
            collection_id: ID of the collection to delete

        Returns:
            True if successful
        """
        # Existence validated server-side

        self._make_request("DELETE", f"/v1/collections/{collection_id}")
        return True

    # MemoryResponse Management Methods

    # def store(
    #     self,
    #     content: str,
    #     collection_id: str,
    #     metadata: Optional[Dict[str, Any]] = None,
    #     *,
    #     chunks: Optional[List[str]] = None,
    #     memory_type: str = "text",
    #     conversation_id: Optional[str] = None,
    #     role: str = "user",
    # ) -> str:
    #     """
    #     Store a memory.

    #     Exactly one of `content` or `chunks` must be provided and each must be
    #     under the 8,192 token limit. If both or neither are provided, a
    #     validation error is raised. To signify "no content" when passing
    #     `chunks`, pass an empty string for `content`.

    #     Notes for text mode:
    #     - There is a maximum of 100 chunks allowed per engram when using this SDK.
    #       If you need to exceed this, prefer sending `raw_text` and letting the server
    #       chunk, or batch your chunks across multiple engrams.

    #     Notes for conversation mode:
    #     - collection_id is required and will be sent as collection_id so the backend assigns the conversation to the desired collection.

    #     Args:
    #         content: Raw text to store. Must be <= 8192 tokens if provided.
    #         collection_id: Collection ID to store the memory in (required)
    #         metadata: Additional metadata for the memory
    #         chunks: Pre-chunked text segments. Each must be <= 8192 tokens.

    #     Returns:
    #         MemoryResponse object
    #     """
    #     if memory_type == "conversation":
    #         conv_id = conversation_id
    #         if not conv_id:
    #             create_payload: Dict[str, Any] = {}
    #             response = self._make_request("POST", "/v1/conversations", json_data=create_payload)
    #             conv = response["results"] if isinstance(response, dict) and "results" in response else response
    #             conv_id = conv.get("id") if isinstance(conv, dict) else None
    #             if not conv_id:
    #                 raise NebulaClientException("Failed to create conversation: no id returned")

    #         add_msg_payload = {
    #             "messages": [
    #                 {
    #                     "content": content,
    #                     "role": role,
    #                     "metadata": metadata or {},
    #                 }
    #             ],
    #             "collection_id": collection_id,
    #         }
    #         _ = self._make_request("POST", f"/v1/conversations/{conv_id}/messages", json_data=add_msg_payload)
    #         return str(conv_id)

    #     # Existence validated server-side

    #     MAX_TOKENS_PER_FIELD = 8192

    #     def _get_encoder():
    #         # Lazy import to avoid hard dependency during import time
    #         if self._token_encoder is None:
    #             try:
    #                 import tiktoken  # type: ignore
    #             except Exception as e:  # pragma: no cover
    #                 raise NebulaClientException(
    #                     "tiktoken is required for token counting. Please install it with `pip install tiktoken`.",
    #                     e,
    #                 )
    #             # Use cl100k_base which matches GPT-3.5/4 family and text-embedding-3 models
    #             self._token_encoder = tiktoken.get_encoding("cl100k_base")
    #         return self._token_encoder

    #     # Validate exclusivity
    #     has_content = content is not None and content != ""
    #     has_chunks = chunks is not None and len(chunks) > 0
    #     if has_content and has_chunks:
    #         raise NebulaValidationException(
    #             "Provide either 'content' or 'chunks', not both.")
    #     if not has_content and not has_chunks:
    #         raise NebulaValidationException(
    #             "Either 'content' or 'chunks' must be provided.")

    #     # Token checks
    #     encoder = _get_encoder()
    #     if has_content:
    #         content_tokens = len(encoder.encode(content or ""))
    #         if content_tokens > MAX_TOKENS_PER_FIELD:
    #             raise NebulaValidationException(
    #                 f"Content is too long: {content_tokens} tokens. Max allowed is {MAX_TOKENS_PER_FIELD} tokens.")
    #     if has_chunks:
    #         for idx, ch in enumerate(chunks or []):
    #             ch_tokens = len(encoder.encode(ch))
    #             if ch_tokens > MAX_TOKENS_PER_FIELD:
    #                 raise NebulaValidationException(
    #                     f"Chunk {idx + 1} is too long: {ch_tokens} tokens. Max allowed is {MAX_TOKENS_PER_FIELD} tokens.")

    #     # Prepare metadata
    #     doc_metadata = metadata or {}
    #     doc_metadata["memory_type"] = "memory"

    #     # Generate deterministic engram ID for deduplication
    #     if has_content:
    #         content_text_for_hash = content or ""
    #     else:
    #         # Hash joined chunks when provided
    #         content_text_for_hash = "\n".join(chunks or [])
    #     content_hash = hashlib.sha256(content_text_for_hash.encode("utf-8")).hexdigest()
    #     deterministic_doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, content_hash))

    #     # Use form data for engram creation (like the original Nebula SDK)
    #     # Prefer sending explicit chunks when provided to avoid server-side partitioning
    #     data: Dict[str, Any] = {
    #         "metadata": json.dumps({**doc_metadata, "content_hash": content_hash}),
    #         "ingestion_mode": "fast",
    #         "collection_ids": json.dumps([collection_id]),
    #     }
    #     if has_chunks:
    #         data["chunks"] = json.dumps(chunks)
    #     else:
    #         data["raw_text"] = content or ""

    #     # Create memory using the memories endpoint with form data
    #     url = f"{self.base_url}/v1/memories"
    #     # For form-data, let httpx set the Content-Type; just add auth header
    #     headers = self._build_auth_headers(include_content_type=False)

    #     try:
    #         response = self._client.post(url, data=data, headers=headers)

    #         if response.status_code not in (200, 202):
    #             error_data = response.json() if response.content else {}
    #             raise NebulaException(
    #                 error_data.get("message", f"Failed to create engram: {response.status_code}"),
    #                 response.status_code,
    #                 error_data
    #             )

    #         response_data = response.json()

    #         # Extract engram ID from response
    #         if isinstance(response_data, dict) and "results" in response_data:
    #             # Try to get the actual engram ID from the response
    #             if "engram_id" in response_data["results"]:
    #                 doc_id = response_data["results"]["engram_id"]
    #             elif "id" in response_data["results"]:
    #                 doc_id = response_data["results"]["id"]
    #             else:
    #                 doc_id = deterministic_doc_id
    #         else:
    #             doc_id = deterministic_doc_id

    #     except Exception as e:
    #         # If duplicate (HTTP 409 or similar) just skip
    #         err_msg = str(e).lower()
    #         if any(token in err_msg for token in ["conflict", "already exists", "duplicate"]):
    #             # Return a memory object for the existing engram
    #             memory_data = {
    #                 "id": deterministic_doc_id,
    #                 "content": content if has_content else None,
    #                 "chunks": chunks if has_chunks else None,
    #                 "metadata": doc_metadata,
    #                 "collection_ids": [collection_id]
    #             }
    #             return MemoryResponse.from_dict(memory_data)
    #         # For other errors, re-raise
    #         raise

    #     # Return a memory object
    #     memory_data = {
    #         "id": doc_id,
    #         "content": content if has_content else None,
    #         "chunks": chunks if has_chunks else None,
    #         "metadata": doc_metadata,
    #         "collection_ids": [collection_id]
    #     }
    #     return str(doc_id)

    # New unified write APIs
    def create_document_text(
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
            >>> doc_id = client.create_document_text(
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

        response = self._make_request("POST", "/v1/memories", json_data=payload)

        if isinstance(response, dict) and "results" in response:
            return str(
                response["results"].get("id") or response["results"].get("engram_id")
            )
        raise NebulaClientException("Failed to create document: invalid response")

    def create_document_chunks(
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

        response = self._make_request("POST", "/v1/memories", json_data=payload)

        if isinstance(response, dict) and "results" in response:
            return str(
                response["results"].get("id") or response["results"].get("engram_id")
            )
        raise NebulaClientException("Failed to create document: invalid response")

    def store_memory(
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
            NebulaNotFoundException: If memory_id is provided but doesn't exist
        """
        # Allow either Memory object or equivalent keyword params
        if memory is None:
            # Build from kwargs
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
            return self._append_to_memory(memory.memory_id, memory)

        # Automatically infer memory type from role presence
        memory_type = "conversation" if memory.role else "document"

        # Handle conversation creation
        if memory_type == "conversation":
            # Use JSON format matching the backend CreateMemoryRequest model
            doc_metadata = dict(memory.metadata or {})

            # Check if content is multimodal (list of content parts)
            is_multimodal = (
                isinstance(memory.content, list) and
                len(memory.content) > 0 and
                isinstance(memory.content[0], dict) and
                "type" in memory.content[0]
            )

            # Build messages array if content and role are provided
            messages = []
            if memory.content and memory.role:
                msg: dict[str, Any] = {
                    "role": memory.role,
                    # Preserve multimodal content as-is, only stringify plain text
                    "content": memory.content if is_multimodal else str(memory.content),
                    "metadata": memory.metadata or {},
                }
                if memory.authority is not None:
                    msg["authority"] = float(memory.authority)
                messages.append(msg)

            payload: dict[str, Any] = {
                "collection_ref": memory.collection_id,
                "engram_type": "conversation",
                "messages": messages,
                "metadata": doc_metadata,
            }
            if name:
                payload["name"] = name
            
            # Add vision model if specified and content is multimodal
            if is_multimodal and memory.vision_model:
                payload["vision_model"] = memory.vision_model
            # Add audio model if specified
            if is_multimodal and memory.audio_model:
                payload["audio_model"] = memory.audio_model
            # Add fast_mode if specified (defaults to False on backend for VLM quality)
            if is_multimodal and memory.fast_mode is not None:
                payload["fast_mode"] = memory.fast_mode

            response = self._make_request("POST", "/v1/memories", json_data=payload)

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

        # Use JSON format matching the backend CreateMemoryRequest model
        payload: dict[str, Any] = {
            "collection_ref": memory.collection_id,
            "engram_type": "document",
            "metadata": doc_metadata,
            "ingestion_mode": "fast",
        }
        
        # Check if content is multimodal (list of content parts)
        if isinstance(memory.content, list):
            # Convert content parts to API format
            content_parts = []
            for part in memory.content:
                if hasattr(part, "__dataclass_fields__"):
                    # Dataclass - convert to dict
                    part_dict = {
                        k: getattr(part, k) 
                        for k in part.__dataclass_fields__.keys()
                    }
                    content_parts.append(part_dict)
                elif isinstance(part, dict):
                    content_parts.append(part)
                else:
                    # Assume it's text
                    content_parts.append({"type": "text", "text": str(part)})
            
            payload["content_parts"] = content_parts
            
            # Add vision model if specified
            if memory.vision_model:
                payload["vision_model"] = memory.vision_model
            # Add audio model if specified
            if memory.audio_model:
                payload["audio_model"] = memory.audio_model
            # Add fast_mode if specified (defaults to False on backend for VLM quality)
            if memory.fast_mode is not None:
                payload["fast_mode"] = memory.fast_mode
        else:
            # Plain text content
            content_text = str(memory.content or "")
            if not content_text:
                raise NebulaClientException("Content is required for document memories")
            
            content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
            doc_metadata["content_hash"] = content_hash
            payload["raw_text"] = content_text

        response = self._make_request("POST", "/v1/memories", json_data=payload)

        if isinstance(response, dict) and "results" in response:
            if "engram_id" in response["results"]:
                return str(response["results"]["engram_id"])
            if "id" in response["results"]:
                return str(response["results"]["id"])
        return ""

    def _append_to_memory(self, memory_id: str, memory: Memory) -> str:
        """Internal method to append content to an existing memory.

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
            # If role is present, wrap as a message for conversation append
            if memory.role:
                payload["messages"] = [{"content": content, "role": memory.role}]
            else:
                # Raw text string for document append
                payload["raw_text"] = content
        else:
            raise NebulaClientException(
                "content must be a string, list of strings, or list of message dicts"
            )

        if metadata is not None:
            payload["metadata"] = metadata

        # Call the unified append endpoint
        try:
            self._make_request(
                "POST", f"/v1/memories/{memory_id}/append", json_data=payload
            )
            return memory_id
        except NebulaException as e:
            # Convert 404 errors to NebulaNotFoundException
            if e.status_code == 404:
                raise NebulaNotFoundException(memory_id, "Memory") from e
            raise

    def store_memories(self, memories: list[Memory]) -> list[str]:
        """Store multiple memories using the unified memory API.

        All items are processed identically to `store_memory`:
        - Conversations are grouped by conversation memory_id and sent in batches
        - Text/JSON/multimodal memories are stored individually
        - Multimodal content (images, audio, documents) is automatically processed

        Returns: list of memory_ids in the same order as input memories
        """
        # Group by conversation memory_id for batching
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
            
            # Get multimodal options from first memory that has them
            vision_model = next((m.vision_model for m in group if m.vision_model), None)
            audio_model = next((m.audio_model for m in group if m.audio_model), None)
            fast_mode = next((m.fast_mode for m in group if m.fast_mode is not None), None)

            # Create conversation if needed
            if key.startswith("__new__::"):
                conv_id = self.store_memory(
                    collection_id=collection_id,
                    content="",
                    role="assistant",
                    name="Conversation",
                )
            else:
                conv_id = key

            # Append messages using new unified API
            messages = []
            for m in group:
                # Check if this message has multimodal content
                is_multimodal = (
                    isinstance(m.content, list) and
                    len(m.content) > 0 and
                    (
                        (isinstance(m.content[0], dict) and "type" in m.content[0]) or
                        hasattr(m.content[0], "__dataclass_fields__")
                    )
                )
                
                # Convert multimodal content to API format
                if is_multimodal:
                    content_parts = []
                    for part in m.content:
                        if hasattr(part, "__dataclass_fields__"):
                            part_dict = {k: getattr(part, k) for k in part.__dataclass_fields__.keys()}
                            content_parts.append(part_dict)
                        elif isinstance(part, dict):
                            content_parts.append(part)
                        else:
                            content_parts.append({"type": "text", "text": str(part)})
                    content = content_parts
                else:
                    content = str(m.content or "")
                
                msg_meta = dict(m.metadata or {})
                messages.append({"content": content, "role": m.role, "metadata": msg_meta})

            # Build append payload with multimodal options
            payload: dict[str, Any] = {
                "collection_id": collection_id,
                "messages": messages,
            }
            if vision_model:
                payload["vision_model"] = vision_model
            if audio_model:
                payload["audio_model"] = audio_model
            if fast_mode is not None:
                payload["fast_mode"] = fast_mode

            self._make_request("POST", f"/v1/memories/{conv_id}/append", json_data=payload)
            results.extend([str(conv_id)] * len(group))

        # Process others (text/json/multimodal) individually - store_memory handles multimodal
        for m in others:
            results.append(self.store_memory(m))
        return results

    def delete(self, memory_ids: str | list[str]) -> bool | dict[str, Any]:
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
                self._make_request("DELETE", f"/v1/memories/{memory_ids}")
                return True
            except Exception:
                # Try new unified endpoint
                try:
                    response = self._make_request(
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
            try:
                response = self._make_request(
                    "POST", "/v1/memories/delete", json_data={"ids": memory_ids}
                )
                batch_result: bool | dict[str, Any] = response
                return batch_result
            except Exception as e:
                raise

    def delete_chunk(self, chunk_id: str) -> bool:
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
            self._make_request("DELETE", f"/v1/chunks/{chunk_id}")
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(chunk_id, "Chunk") from e
            raise

    def update_chunk(
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
            self._make_request("PATCH", f"/v1/chunks/{chunk_id}", json_data=payload)
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(chunk_id, "Chunk") from e
            raise

    def update_memory(
        self,
        memory_id: str,
        *,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        collection_ids: list[str] | None = None,
        merge_metadata: bool = False,
    ) -> bool:
        """
        Update memory-level properties including name, metadata, and collection associations.

        This method allows you to update properties of an entire memory (document or conversation)
        without modifying its content. For updating individual chunks or messages within a memory,
        use update_chunk(). For updating content, use store_memory() to append.

        Args:
            memory_id: The ID of the memory to update
            name: New name for the memory (useful for conversations and documents)
            metadata: Metadata to set. By default, replaces existing metadata.
                     Set merge_metadata=True to merge with existing metadata instead.
            collection_ids: New collection associations. Must specify at least one valid collection.
            merge_metadata: If True, merges provided metadata with existing metadata.
                          If False (default), replaces existing metadata entirely.

        Returns:
            True if successful

        Raises:
            NebulaNotFoundException: If memory_id doesn't exist
            NebulaValidationException: If validation fails (e.g., no collections specified)
            NebulaAuthenticationException: If user doesn't have permission to update this memory
        """
        payload: dict[str, Any] = {}

        if name is not None:
            payload["name"] = name
        if metadata is not None:
            payload["metadata"] = metadata
            payload["merge_metadata"] = merge_metadata
        if collection_ids is not None:
            payload["collection_ids"] = collection_ids

        if not payload:
            raise NebulaValidationException(
                "At least one field (name, metadata, or collection_ids) must be provided to update"
            )

        try:
            self._make_request("PATCH", f"/v1/memories/{memory_id}", json_data=payload)
            return True
        except NebulaException as e:
            if e.status_code == 404:
                raise NebulaNotFoundException(memory_id, "Memory") from None
            raise

    def list_memories(
        self,
        *,
        collection_ids: list[str],
        limit: int = 100,
        offset: int = 0,
        metadata_filters: dict | None = None,
    ) -> list[MemoryResponse]:
        """
        Get all memories from a specific collection with optional metadata filtering.

        Args:
            collection_ids: One or more collection IDs to retrieve memories from
            limit: Maximum number of memories to return (default: 100)
            offset: Number of memories to skip for pagination (default: 0)
            metadata_filters: Optional metadata filters using MongoDB-like operators.
                Supported operators: $eq, $ne, $in, $nin, $exists, $and, $or
                Examples:
                    - Filter by single field: {"metadata.playground": {"$eq": True}}
                    - Exclude conversations: {"metadata.content_type": {"$ne": "conversation"}}
                    - Multiple conditions: {"$and": [
                        {"metadata.playground": {"$eq": True}},
                        {"metadata.session_id": {"$exists": True}}
                      ]}

        Returns:
            List of MemoryResponse objects matching the filters

        Example:
            # Get all playground memories excluding conversations
            memories = client.list_memories(
                collection_ids=["collection-id"],
                metadata_filters={"metadata.content_type": {"$ne": "conversation"}}
            )
        """
        # Collection existence is validated by the backend when filtering by collection

        if not collection_ids:
            raise NebulaClientException(
                "collection_ids must be provided to list_memories()."
            )

        params = {
            "limit": limit,
            "offset": offset,
            "collection_ids": collection_ids,
        }

        # Add metadata_filters if provided (serialize to JSON string for query parameter)
        if metadata_filters:
            import json

            params["metadata_filters"] = json.dumps(metadata_filters)

        response = self._make_request("GET", "/v1/memories", params=params)

        if isinstance(response, dict) and "results" in response:
            engrams = response["results"]
        elif isinstance(response, list):
            engrams = response
        else:
            engrams = [response]

        # Convert all engrams to memories (handle text or chunks)
        memories: list[MemoryResponse] = []
        for doc in engrams:
            content = doc.get("text") or doc.get("content")
            chunks = doc.get("chunks") if isinstance(doc.get("chunks"), list) else None
            memory_data = {
                "id": doc.get("id"),
                "content": content,
                "chunks": chunks,
                "metadata": doc.get("metadata", {}),
                # Prefer backend-provided collection_ids; fallback to the requested identifiers
                "collection_ids": doc.get("collection_ids", collection_ids),
            }
            memories.append(MemoryResponse.from_dict(memory_data))

        return memories

    def get_memory(self, memory_id: str) -> MemoryResponse:
        """
        Get a specific memory by memory ID

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            MemoryResponse object
        """
        response = self._make_request("GET", f"/v1/memories/{memory_id}")

        # Handle either a single text or chunks array from the backend
        content = response.get("text") or response.get("content")
        chunks = (
            response.get("chunks") if isinstance(response.get("chunks"), list) else None
        )
        memory_data = {
            "id": response.get("id"),
            "content": content,
            "chunks": chunks,
            "metadata": response.get("metadata", {}),
            "collection_ids": response.get("collection_ids", []),
        }
        return MemoryResponse.from_dict(memory_data)

    def search(
        self,
        query: str,
        *,
        collection_ids: list[str] | None = None,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        search_settings: dict[str, Any] | None = None,
    ) -> MemoryRecall:
        """
        Search your memory collections with optional metadata filtering.

        Args:
            query: Search query string
            collection_ids: Optional list of collection IDs or names to search within.
                        Can be UUIDs or collection names.
                        If not provided, searches across all your accessible collections.
            limit: Maximum number of results to return (default: 10, max: 1000)
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

            Logical operators:
                filters={
                    "$and": [
                        {"metadata.verified": True},
                        {"metadata.score": {"$gte": 80}}
                    ]
                }

        Supported Operators:
            Comparison: $eq, $ne, $lt, $lte, $gt, $gte
            String: $like (case-sensitive), $ilike (case-insensitive)
            Array: $in, $nin, $overlap, $contains
            Logical: $and, $or

        Returns:
            MemoryRecall object containing hierarchical memory structure with entities, facts,
            and utterances
        """
        # Build request data - pass params directly to API (no wrapping needed)
        data: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }

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

        response = self._make_request("POST", "/v1/retrieval/search", json_data=data)

        # Backend returns MemoryRecall wrapped in { results: MemoryRecall }
        if isinstance(response, dict) and "results" in response:
            return MemoryRecall.from_dict(response["results"], query)

        # Fallback to empty MemoryRecall
        return MemoryRecall(
            query=query,
            entities=[],
            facts=[],
            utterances=[],
            fact_to_chunks={},
            entity_to_facts={},
            retrieved_at="",
        )

    # def chat(
    #     self,
    #     agent_id: str,
    #     message: str,
    #     conversation_id: Optional[str] = None,
    #     model: str = "gpt-4",
    #     temperature: float = 0.7,
    #     max_tokens: Optional[int] = None,
    #     retrieval_type: Union[RetrievalType, str] = RetrievalType.SIMPLE,
    #     collection_id: Optional[str] = None,
    #     stream: bool = False,
    # ) -> AgentResponse:
    #     """
    #     Chat with an agent using its memories for context
    #
    #     Args:
    #         agent_id: Unique identifier for the agent
    #         message: User message to send to the agent
    #         conversation_id: Optional conversation ID for multi-turn conversations
    #         model: LLM model to use for generation
    #         temperature: Sampling temperature for generation
    #         max_tokens: Maximum tokens to generate
    #         retrieval_type: Type of retrieval to use for context
    #         collection_id: Optional collection ID to search within
    #         stream: Whether to enable streaming response
    #
    #     Returns:
    #         AgentResponse object with the agent's response
    #     """
    #     # Convert string to enum if needed
    #     if isinstance(retrieval_type, str):
    #         retrieval_type = RetrievalType(retrieval_type)
    #
    #     data = {
    #         "query": message,
    #         "rag_generation_config": {
    #             "model": model,
    #             "temperature": temperature,
    #             "stream": stream,
    #         }
    #     }
    #
    #     if max_tokens:
    #         data["rag_generation_config"]["max_tokens"] = max_tokens
    #
    #     if conversation_id:
    #         data["conversation_id"] = conversation_id
    #
    #     # Note: Skipping collection_id filter for now due to API issue
    #
    #     if stream:
    #         # For streaming, we need to handle the response differently
    #         return self._make_streaming_generator("POST", "/v1/retrieval/rag", json_data=data, agent_id=agent_id, conversation_id=conversation_id)
    #     else:
    #         response = self._make_request("POST", "/v1/retrieval/rag", json_data=data)
    #
    #     # Extract the response from the API format
    #     if isinstance(response, dict) and "results" in response:
    #         # The RAG endpoint returns the answer in "generated_answer" field
    #         generated_answer = response["results"].get("generated_answer", "")
    #         if generated_answer:
    #                 return AgentResponse(
    #                     content=generated_answer,
    #                     agent_id=agent_id,
    #                     conversation_id=conversation_id,
    #                     metadata={},
    #                     citations=[]
    #                 )
    #
    #         # Fallback to completion format if generated_answer is not available
    #         completion = response["results"].get("completion", {})
    #         if completion and "choices" in completion:
    #             content = completion["choices"][0].get("message", {}).get("content", "")
    #             return AgentResponse(
    #                 content=content,
    #                 agent_id=agent_id,
    #                 conversation_id=conversation_id,
    #                 metadata={},
    #                 citations=[]
    #             )
    #
    #     # Fallback
    #     return AgentResponse(
    #         content="No response received",
    #         agent_id=agent_id,
    #         conversation_id=conversation_id,
    #         metadata={},
    #         citations=[]
    #     )

    def health_check(self) -> dict[str, Any]:
        """
        Check the health of the Nebula API

        Returns:
            Health status information
        """
        return self._make_request("GET", "/v1/health")

    def process_multimodal_content(
        self,
        content_parts: list[dict[str, Any]],
        vision_model: str | None = None,
        audio_model: str | None = None,
        fast_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Process multimodal content (audio, documents, images) and return extracted text.
        
        This method processes files on-the-fly without saving to memory. Useful for:
        - Pre-processing files before sending to an LLM in chat
        - Extracting text from PDFs/documents
        - Transcribing audio files
        - Analyzing images with vision models
        
        Args:
            content_parts: List of content part dicts with keys:
                - type: 'image' | 'audio' | 'document'
                - data: Base64 encoded file data
                - media_type: MIME type (e.g., 'application/pdf', 'audio/mp3')
                - filename: Optional filename
            vision_model: Optional vision model for images/documents (default: modal/qwen3-vl-thinking)
            audio_model: Optional audio transcription model (default: whisper-1)
            fast_mode: Use fast text extraction for PDFs (pypdf) instead of VLM OCR (default: True)
                       Fast mode is much faster but less accurate for scanned/image PDFs.
            
        Returns:
            dict with:
            - extracted_text: The processed/extracted text content
            - content_parts_count: Number of parts processed
            - vision_model: Vision model used (if any)
            - audio_model: Audio model used (if any)
            - fast_mode: Whether fast mode was used
            
        Example:
            import base64
            from nebula import Nebula
            
            client = Nebula(api_key="your-key")
            
            # Process a PDF document
            with open("report.pdf", "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode()
            
            result = client.process_multimodal_content([
                {
                    "type": "document",
                    "data": pdf_data,
                    "media_type": "application/pdf",
                    "filename": "report.pdf"
                }
            ])
            print(result["extracted_text"])
            
            # Transcribe audio
            with open("recording.mp3", "rb") as f:
                audio_data = base64.b64encode(f.read()).decode()
            
            result = client.process_multimodal_content([
                {
                    "type": "audio",
                    "data": audio_data,
                    "media_type": "audio/mp3",
                    "filename": "recording.mp3"
                }
            ])
            print(result["extracted_text"])
            
            # Use VLM OCR for scanned PDFs (slower but more accurate)
            result = client.process_multimodal_content(
                content_parts=[{"type": "document", "data": pdf_data, "media_type": "application/pdf"}],
                fast_mode=False  # Use VLM OCR
            )
        """
        data: dict[str, Any] = {
            "content_parts": content_parts,
            "fast_mode": fast_mode,
        }
        
        if vision_model:
            data["vision_model"] = vision_model
        if audio_model:
            data["audio_model"] = audio_model
        
        response = self._make_request("POST", "/v1/multimodal/process", json_data=data)
        
        if isinstance(response, dict) and "results" in response:
            return response["results"]
        return response

    def get_upload_url(
        self,
        filename: str,
        content_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        """
        Get a presigned URL for uploading large files directly to S3.
        
        Use this for files larger than 5MB that cannot be sent inline as base64.
        After uploading, reference the file in memory creation using S3FileRef.
        
        Args:
            filename: Original filename (e.g., "image.jpg")
            content_type: MIME type (e.g., "image/jpeg", "application/pdf")
            file_size: File size in bytes (max 100MB)
            
        Returns:
            dict with:
            - upload_url: Presigned URL for PUT request (expires in 1 hour)
            - s3_key: The S3 key to use in S3FileRef
            - bucket: S3 bucket name
            - expires_in: Seconds until URL expires
            - max_size: Maximum allowed file size
            
        Example:
            # Get upload URL
            result = client.get_upload_url(
                filename="large_image.jpg",
                content_type="image/jpeg",
                file_size=10_000_000  # 10MB
            )
            
            # Upload file directly to S3
            import requests
            with open("large_image.jpg", "rb") as f:
                requests.put(
                    result["upload_url"],
                    data=f,
                    headers={"Content-Type": "image/jpeg"}
                )
            
            # Use s3_key in memory creation
            from nebula import Memory, S3FileRef
            client.store_memory(Memory(
                collection_id="my-collection",
                content=[S3FileRef(s3_key=result["s3_key"], media_type="image/jpeg")]
            ))
        """
        response = self._make_request(
            "POST",
            "/v1/upload-url",
            params={
                "filename": filename,
                "content_type": content_type,
                "file_size": file_size,
            }
        )
        if isinstance(response, dict) and "results" in response:
            return response["results"]
        return response
