// src/types.ts
var GraphSearchResultType = /* @__PURE__ */ ((GraphSearchResultType2) => {
  GraphSearchResultType2["ENTITY"] = "entity";
  GraphSearchResultType2["RELATIONSHIP"] = "relationship";
  GraphSearchResultType2["COMMUNITY"] = "community";
  return GraphSearchResultType2;
})(GraphSearchResultType || {});
var NebulaException = class extends Error {
  constructor(message, statusCode, details) {
    super(message);
    this.statusCode = statusCode;
    this.details = details;
    this.name = "NebulaException";
  }
};
var NebulaClientException = class extends NebulaException {
  constructor(message, cause) {
    super(message);
    this.cause = cause;
    this.name = "NebulaClientException";
  }
};
var NebulaAuthenticationException = class extends NebulaException {
  constructor(message = "Invalid API key") {
    super(message, 401);
    this.name = "NebulaAuthenticationException";
  }
};
var NebulaRateLimitException = class extends NebulaException {
  constructor(message = "Rate limit exceeded") {
    super(message, 429);
    this.name = "NebulaRateLimitException";
  }
};
var NebulaValidationException = class extends NebulaException {
  constructor(message = "Validation error", details) {
    super(message, 400);
    this.details = details;
    this.name = "NebulaValidationException";
  }
};
var NebulaCollectionNotFoundException = class extends NebulaException {
  constructor(message = "Collection not found") {
    super(message, 404);
    this.name = "NebulaCollectionNotFoundException";
  }
};
var NebulaNotFoundException = class extends NebulaException {
  constructor(resourceId, resourceType = "Resource") {
    super(`${resourceType} not found: ${resourceId}`, 404);
    this.name = "NebulaNotFoundException";
  }
};

// src/client.ts
var _Nebula = class _Nebula {
  // 5MB
  constructor(config = {}) {
    this.apiKey = config.apiKey;
    if (!this.apiKey) {
      throw new NebulaClientException(
        "API key is required. Pass it to the constructor or set NEBULA_API_KEY environment variable."
      );
    }
    this.baseUrl = (config.baseUrl || "https://api.nebulacloud.app").replace(/\/$/, "");
    this.timeout = config.timeout || 3e4;
  }
  // Public mutators used by tests
  setApiKey(next) {
    this.apiKey = next;
  }
  setBaseUrl(next) {
    this.baseUrl = (next || this.baseUrl).replace(/\/$/, "");
  }
  // Kept for backwards-compat tests; no-op in current implementation
  setCorsProxy(_next) {
  }
  /** Check if API key is set */
  isApiKeySet() {
    return !!(this.apiKey && this.apiKey.trim() !== "");
  }
  /** Detect if a token looks like a Nebula API key (public.raw) */
  _isNebulaApiKey(token) {
    const candidate = token || this.apiKey;
    if (!candidate) return false;
    const parts = candidate.split(".");
    if (parts.length !== 2) return false;
    const [publicPart, rawPart] = parts;
    return (publicPart.startsWith("key_") || publicPart.startsWith("neb_")) && !!rawPart && rawPart.length > 0;
  }
  /** Build authentication headers */
  _buildAuthHeaders(includeContentType = true) {
    const headers = {};
    if (this._isNebulaApiKey()) {
      headers["X-API-Key"] = this.apiKey;
    } else {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }
    if (includeContentType) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }
  _isRecord(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }
  _unwrapResults(value) {
    if (this._isRecord(value) && "results" in value) {
      return value.results;
    }
    return value;
  }
  _unwrapResultsArray(value) {
    const unwrapped = this._unwrapResults(value);
    if (Array.isArray(unwrapped)) {
      return unwrapped;
    }
    if (unwrapped === void 0 || unwrapped === null) {
      return [];
    }
    return [unwrapped];
  }
  _looksLikeMultimodalContent(content) {
    if (!Array.isArray(content)) return false;
    return content.some((part) => {
      if (!this._isRecord(part)) return false;
      if (typeof part.type === "string") return true;
      if ("data" in part || "s3_key" in part || "url" in part) return true;
      return false;
    });
  }
  _normalizeContentParts(contentParts) {
    return contentParts.map((part) => {
      if (typeof part === "string") {
        return { type: "text", text: part };
      }
      if (!this._isRecord(part)) {
        return { type: "text", text: String(part) };
      }
      if (typeof part.type === "string") {
        return part;
      }
      if ("s3_key" in part && typeof part.s3_key === "string") {
        return {
          type: "s3_ref",
          s3_key: part.s3_key,
          bucket: typeof part.bucket === "string" ? part.bucket : void 0,
          media_type: typeof part.media_type === "string" ? part.media_type : "application/octet-stream",
          filename: typeof part.filename === "string" ? part.filename : void 0,
          size_bytes: typeof part.size_bytes === "number" ? part.size_bytes : void 0
        };
      }
      if ("data" in part && typeof part.data === "string") {
        return {
          type: "file",
          data: part.data,
          media_type: typeof part.media_type === "string" ? part.media_type : "application/octet-stream",
          filename: typeof part.filename === "string" ? part.filename : void 0,
          duration_seconds: typeof part.duration_seconds === "number" ? part.duration_seconds : void 0
        };
      }
      return { type: "text", text: String(part) };
    });
  }
  async _serializeContentAsText(content) {
    if (this._looksLikeMultimodalContent(content)) {
      const normalized = this._normalizeContentParts(content);
      const processed = await this._processContentParts(normalized);
      return JSON.stringify(processed);
    }
    if (typeof content === "object" && content !== null) {
      return JSON.stringify(content);
    }
    return String(content ?? "");
  }
  async _serializeContentAsParts(content) {
    if (!this._looksLikeMultimodalContent(content)) return null;
    const normalized = this._normalizeContentParts(content);
    return await this._processContentParts(normalized);
  }
  /** Make an HTTP request to the Nebula API */
  async _makeRequest(method, endpoint, jsonData, params) {
    const url = new URL(endpoint, this.baseUrl);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== void 0 && value !== null) {
          if (Array.isArray(value)) {
            value.forEach((item) => {
              url.searchParams.append(key, String(item));
            });
          } else {
            url.searchParams.append(key, String(value));
          }
        }
      });
    }
    const headers = this._buildAuthHeaders(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    try {
      const response = await fetch(url.toString(), {
        method,
        headers,
        body: jsonData ? JSON.stringify(jsonData) : void 0,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (response.status === 200 || response.status === 202) {
        return await response.json();
      } else if (response.status === 401) {
        throw new NebulaAuthenticationException("Invalid API key");
      } else if (response.status === 429) {
        throw new NebulaRateLimitException("Rate limit exceeded");
      } else if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new NebulaValidationException(errorData.message || "Validation error", errorData.details);
      } else if (response.status === 422) {
        const errorData = await response.json().catch(() => ({}));
        console.error("[SDK] 422 Validation error - Full details:");
        console.error("  Status:", response.status);
        console.error("  Error data:", JSON.stringify(errorData, null, 2));
        console.error("  Message:", errorData.message);
        console.error("  Detail:", errorData.detail);
        throw new NebulaValidationException(
          errorData.message || (typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail)) || "Validation error",
          errorData
        );
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new NebulaException(errorData.message || `API error: ${response.status}`, response.status, errorData);
      }
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof NebulaException) {
        throw error;
      }
      if (error instanceof Error && error.name === "AbortError") {
        throw new NebulaClientException(`Request timed out after ${this.timeout} milliseconds`);
      }
      if (error instanceof Error) {
        throw new NebulaClientException(`Request failed: ${error.message}`, error);
      }
      throw new NebulaClientException(`Request failed: ${String(error)}`);
    }
  }
  // Collection Management Methods
  /** Create a new collection */
  async createCollection(options) {
    const data = { name: options.name };
    if (options.description) data.description = options.description;
    if (options.metadata) data.metadata = options.metadata;
    const response = await this._makeRequest("POST", "/v1/collections", data);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }
  /** Get a specific collection by ID */
  async getCollection(collectionId) {
    const response = await this._makeRequest("GET", `/v1/collections/${collectionId}`);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }
  /** Get a specific collection by name */
  async getCollectionByName(name) {
    const response = await this._makeRequest("GET", `/v1/collections/name/${name}`);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }
  /** Get all collections */
  async listCollections(options) {
    const params = {
      limit: options?.limit ?? 100,
      offset: options?.offset ?? 0
    };
    if (options?.name !== void 0) {
      params.name = options.name;
    }
    const response = await this._makeRequest("GET", "/v1/collections", void 0, params);
    let collections;
    if (typeof response === "object" && response !== null && "results" in response) {
      collections = response.results;
    } else if (Array.isArray(response)) {
      collections = response;
    } else {
      collections = [response];
    }
    return collections.map((collection) => this._collectionFromDict(collection));
  }
  /** Update a collection */
  async updateCollection(options) {
    const data = {};
    if (options.name !== void 0) data.name = options.name;
    if (options.description !== void 0) data.description = options.description;
    if (options.metadata !== void 0) data.metadata = options.metadata;
    const response = await this._makeRequest("POST", `/v1/collections/${options.collectionId}`, data);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }
  /** Delete a collection */
  async deleteCollection(collectionId) {
    await this._makeRequest("DELETE", `/v1/collections/${collectionId}`);
    return true;
  }
  // Memory Management Methods
  /**
   * Legacy convenience: store raw text content into a collection as a document
   */
  async store(content, collectionId, metadata = {}) {
    const docMetadata = {
      ...metadata,
      memory_type: "memory",
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
    const payload = {
      collection_id: collectionId,
      raw_text: String(content || ""),
      metadata: docMetadata,
      ingestion_mode: "fast"
    };
    const response = await this._makeRequest("POST", "/v1/memories", payload);
    const id = response?.results?.engram_id || response?.results?.id || response?.id || "";
    const timestamp = docMetadata.timestamp;
    const result = {
      id: String(id),
      memory_id: String(id),
      content: String(content || ""),
      metadata: docMetadata,
      collection_ids: [collectionId],
      created_at: timestamp,
      updated_at: timestamp
    };
    return result;
  }
  /**
   * Store a single memory using the unified engrams API.
   *
   * Automatically infers memory type:
   * - If role is present, creates a conversation
   * - Otherwise, creates a document
   */
  async storeMemory(memory, name) {
    let mem;
    if ("collection_id" in memory) {
      mem = memory;
    } else {
      const memRecord2 = memory;
      mem = {
        collection_id: memRecord2.collection_id || memRecord2.collectionId || "",
        content: memRecord2.content || "",
        role: memRecord2.role,
        memory_id: memRecord2.memory_id || memRecord2.memoryId || void 0,
        metadata: memRecord2.metadata || {}
      };
    }
    if (mem.memory_id) {
      return await this._appendToMemory(mem.memory_id, mem);
    }
    const memoryType = mem.role ? "conversation" : "document";
    if (memoryType === "conversation") {
      const messages = [];
      if (mem.content && mem.role) {
        const multimodalParts2 = await this._serializeContentAsParts(mem.content);
        const msgContent = multimodalParts2 ?? await this._serializeContentAsText(mem.content);
        const memRecord2 = mem;
        messages.push({
          content: msgContent,
          role: mem.role,
          metadata: mem.metadata || {},
          ...typeof memRecord2.authority === "number" ? { authority: Number(memRecord2.authority) } : {}
        });
      }
      if (messages.length === 0) {
        throw new NebulaClientException("Cannot create conversation without messages. Provide content and role.");
      }
      const data = {
        collection_id: mem.collection_id,
        name: name || "Conversation",
        messages,
        metadata: mem.metadata || {}
      };
      const response2 = await this._makeRequest("POST", "/v1/memories", data);
      if (response2.results) {
        const convId = response2.results.memory_id || response2.results.id;
        if (!convId) {
          throw new NebulaClientException("Failed to create conversation: no id returned");
        }
        return String(convId);
      }
      throw new NebulaClientException("Failed to create conversation: invalid response format");
    }
    const docMetadata = { ...mem.metadata };
    docMetadata.memory_type = "memory";
    const memRecord = mem;
    if (typeof memRecord.authority === "number") {
      const v = Number(memRecord.authority);
      if (!Number.isNaN(v) && v >= 0 && v <= 1) {
        docMetadata.authority = v;
      }
    }
    let payload;
    const multimodalParts = await this._serializeContentAsParts(mem.content);
    if (multimodalParts) {
      payload = {
        collection_id: mem.collection_id,
        content_parts: multimodalParts,
        metadata: docMetadata,
        ingestion_mode: "fast"
      };
    } else if (Array.isArray(mem.content) && mem.content.every((x) => typeof x === "string")) {
      payload = {
        collection_id: mem.collection_id,
        chunks: mem.content,
        metadata: docMetadata,
        ingestion_mode: "fast"
      };
    } else {
      const contentText = await this._serializeContentAsText(mem.content);
      if (!contentText || contentText === '""' || contentText === "[]" || contentText === "{}") {
        throw new NebulaClientException("Content is required for document memories");
      }
      payload = {
        collection_id: mem.collection_id,
        raw_text: contentText,
        metadata: docMetadata,
        ingestion_mode: "fast"
      };
    }
    const response = await this._makeRequest("POST", "/v1/memories", payload);
    const id = response?.results?.engram_id || response?.results?.id || response?.id || "";
    return String(id || "");
  }
  /**
   * Internal method to append content to an existing memory
   *
   * @throws NebulaNotFoundException if memory_id doesn't exist
   */
  async _appendToMemory(memoryId, memory) {
    const collectionId = memory.collection_id;
    const content = memory.content;
    const metadata = memory.metadata;
    if (!collectionId) {
      throw new NebulaClientException("collection_id is required");
    }
    const payload = {
      collection_id: collectionId
    };
    if (Array.isArray(content)) {
      if (content.length > 0 && typeof content[0] === "object" && "content" in content[0]) {
        payload.messages = content;
      } else {
        payload.chunks = content;
      }
    } else if (typeof content === "string") {
      payload.raw_text = content;
    } else {
      throw new NebulaClientException(
        "content must be a string, array of strings, or array of message objects"
      );
    }
    if (metadata) {
      payload.metadata = metadata;
    }
    try {
      await this._makeRequest("POST", `/v1/memories/${memoryId}/append`, payload);
      return memoryId;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(memoryId, "Memory");
      }
      throw error;
    }
  }
  /** Store multiple memories using the unified engrams API */
  async storeMemories(memories) {
    const results = [];
    const convGroups = {};
    const others = [];
    for (const m of memories) {
      if (m.role) {
        const key = m.memory_id || `__new__::${m.collection_id}`;
        if (!convGroups[key]) convGroups[key] = [];
        convGroups[key].push(m);
      } else {
        others.push(m);
      }
    }
    for (const [key, group] of Object.entries(convGroups)) {
      const collectionId = group[0].collection_id;
      let convId;
      const messages = [];
      for (const m of group) {
        const multimodalParts = await this._serializeContentAsParts(m.content);
        const msgContent = multimodalParts ?? await this._serializeContentAsText(m.content);
        if (typeof msgContent === "string") {
          if (!msgContent.trim()) continue;
        } else if (msgContent.length === 0) {
          continue;
        }
        const mRecord = m;
        messages.push({
          content: msgContent,
          role: m.role,
          metadata: m.metadata || {},
          ...typeof mRecord.authority === "number" ? { authority: Number(mRecord.authority) } : {}
        });
      }
      if (!messages.length) {
        throw new NebulaClientException(
          "Cannot create/append conversation without messages. Provide non-empty content."
        );
      }
      if (key.startsWith("__new__::")) {
        const data = {
          collection_id: collectionId,
          name: "Conversation",
          messages,
          metadata: {}
        };
        const response = await this._makeRequest("POST", "/v1/memories", data);
        if (response.results) {
          convId = response.results.memory_id || response.results.id || "";
          if (!convId) {
            throw new NebulaClientException("Failed to create conversation: no id returned");
          }
        } else {
          throw new NebulaClientException("Failed to create conversation: invalid response format");
        }
      } else {
        convId = key;
        const appendMem = {
          collection_id: collectionId,
          content: messages,
          memory_id: convId,
          metadata: {}
        };
        await this._appendToMemory(convId, appendMem);
      }
      results.push(...Array(group.length).fill(String(convId)));
    }
    for (const m of others) {
      results.push(await this.storeMemory(m));
    }
    return results;
  }
  /** Delete one or more memories */
  async delete(memoryIds) {
    try {
      console.log("[SDK] delete() called with:", { memoryIds, type: typeof memoryIds, isArray: Array.isArray(memoryIds) });
      if (typeof memoryIds === "string") {
        console.log("[SDK] Single deletion path for ID:", memoryIds);
        try {
          await this._makeRequest("DELETE", `/v1/memories/${memoryIds}`);
          return true;
        } catch {
          console.log("[SDK] Falling back to POST /v1/memories/delete with single ID");
          const response = await this._makeRequest("POST", "/v1/memories/delete", memoryIds);
          return typeof response === "object" && response.success !== void 0 ? response.success : true;
        }
      } else {
        console.log("[SDK] Batch deletion path for IDs:", memoryIds);
        console.log("[SDK] Sending POST request with body:", memoryIds);
        const response = await this._makeRequest("POST", "/v1/memories/delete", memoryIds);
        console.log("[SDK] Batch deletion response:", response);
        return response;
      }
    } catch (error) {
      console.error("[SDK] Delete error:", error);
      if (error instanceof Error) {
        throw error;
      }
      throw new NebulaClientException(`Unknown error: ${String(error)}`);
    }
  }
  /** Delete a specific chunk or message within a memory */
  async deleteChunk(chunkId) {
    try {
      await this._makeRequest("DELETE", `/v1/chunks/${chunkId}`);
      return true;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(chunkId, "Chunk");
      }
      throw error;
    }
  }
  /** Update a specific chunk or message within a memory */
  async updateChunk(chunkId, content, metadata) {
    const payload = { content };
    if (metadata !== void 0) {
      payload.metadata = metadata;
    }
    try {
      await this._makeRequest("PATCH", `/v1/chunks/${chunkId}`, payload);
      return true;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(chunkId, "Chunk");
      }
      throw error;
    }
  }
  /**
   * Update memory-level properties including name, metadata, and collection associations.
   *
   * This method allows updating properties of an entire memory (document or conversation)
   * without modifying its content. For updating individual chunks or messages within a memory,
   * use updateChunk(). For updating content, use storeMemory() to append.
   *
   * @param options - Update configuration
   * @param options.memoryId - The ID of the memory to update
   * @param options.name - New name for the memory (useful for conversations and documents)
   * @param options.metadata - Metadata to set. By default, replaces existing metadata.
   *                           Set mergeMetadata=true to merge with existing metadata instead.
   * @param options.collectionIds - New collection associations. Must specify at least one valid collection.
   * @param options.mergeMetadata - If true, merges provided metadata with existing metadata.
   *                                If false (default), replaces existing metadata entirely.
   *
   * @returns Promise resolving to true if successful
   *
   * @throws NebulaNotFoundException if memory_id doesn't exist
   * @throws NebulaValidationException if validation fails (e.g., no fields provided)
   * @throws NebulaAuthenticationException if user doesn't have permission to update this memory
   */
  async updateMemory(options) {
    const payload = {};
    if (options.name !== void 0) {
      payload.name = options.name;
    }
    if (options.metadata !== void 0) {
      payload.metadata = options.metadata;
      payload.merge_metadata = options.mergeMetadata ?? false;
    }
    if (options.collectionIds !== void 0) {
      payload.collection_ids = options.collectionIds;
    }
    if (Object.keys(payload).length === 0) {
      throw new NebulaValidationException(
        "At least one field (name, metadata, or collectionIds) must be provided to update"
      );
    }
    try {
      await this._makeRequest("PATCH", `/v1/memories/${options.memoryId}`, payload);
      return true;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(options.memoryId, "Memory");
      }
      throw error;
    }
  }
  /**
   * Get all memories from specific collections with optional metadata filtering
   *
   * @param options - Configuration for listing memories
   * @param options.collection_ids - One or more collection IDs to retrieve memories from
   * @param options.limit - Maximum number of memories to return (default: 100)
   * @param options.offset - Number of memories to skip for pagination (default: 0)
   * @param options.metadata_filters - Optional metadata filters using MongoDB-like operators.
   *   Supported operators: $eq, $ne, $in, $nin, $exists, $and, $or
   *
   * @returns Promise resolving to array of MemoryResponse objects
   *
   * @example
   * // Get all playground memories excluding conversations
   * const memories = await client.listMemories({
   *   collection_ids: ['collection-id'],
   *   metadata_filters: {
   *     'metadata.content_type': { $ne: 'conversation' }
   *   }
   * });
   *
   * @example
   * // Complex filter with multiple conditions
   * const memories = await client.listMemories({
   *   collection_ids: ['collection-id'],
   *   metadata_filters: {
   *     $and: [
   *       { 'metadata.playground': { $eq: true } },
   *       { 'metadata.session_id': { $exists: true } }
   *     ]
   *   }
   * });
   */
  async listMemories(options) {
    const ids = Array.isArray(options.collection_ids) ? options.collection_ids : [options.collection_ids];
    if (!ids.length) {
      throw new NebulaClientException("collection_ids must be provided to list_memories().");
    }
    const params = {
      limit: options.limit ?? 100,
      offset: options.offset ?? 0,
      collection_ids: ids
    };
    if (options.metadata_filters) {
      params.metadata_filters = JSON.stringify(options.metadata_filters);
    }
    const response = await this._makeRequest("GET", "/v1/memories", void 0, params);
    let documents;
    if (typeof response === "object" && response !== null && "results" in response) {
      documents = response.results;
    } else if (Array.isArray(response)) {
      documents = response;
    } else {
      documents = [response];
    }
    return documents.map((doc) => this._memoryResponseFromDict(doc, ids));
  }
  /** Get a specific memory by engram ID */
  async getMemory(memoryId) {
    const response = await this._makeRequest("GET", `/v1/memories/${memoryId}`);
    const content = response.text || response.content;
    const chunks = Array.isArray(response.chunks) ? response.chunks : void 0;
    const memoryData = {
      id: response.id,
      content,
      chunks,
      metadata: response.metadata || {},
      collection_ids: response.collection_ids || []
    };
    return this._memoryResponseFromDict(memoryData, []);
  }
  // Search Methods
  /**
   * Search within specific collections with optional metadata filtering.
   *
   * @param options - Search configuration
   * @param options.query - Search query string
   * @param options.collection_ids - One or more collection IDs to search within
   * @param options.effort - Compute effort budget (auto/low/medium/high). Controls traversal compute, not MemoryResponse size.
   * @param options.filters - Optional filters to apply to the search. Supports comprehensive metadata filtering
   *                          with MongoDB-like operators for both vector/chunk search and graph search.
   * @param options.searchSettings - Optional search configuration
   *
   * @returns Promise resolving to array of SearchResult objects containing both vector/chunk and graph search results
   *
   * @example
   * // Basic equality filter
   * await client.search({
   *   query: "machine learning",
   *   collection_ids: ["research-collection"],
   *   filters: {
   *     "metadata.category": { $eq: "research" },
   *     "metadata.verified": true  // Shorthand for $eq
   *   }
   * });
   *
   * @example
   * // Numeric comparisons
   * await client.search({
   *   query: "high priority",
   *   collection_ids: ["tasks"],
   *   filters: {
   *     "metadata.priority": { $gte: 8 },
   *     "metadata.score": { $lt: 100 }
   *   }
   * });
   *
   * @example
   * // String matching
   * await client.search({
   *   query: "employees",
   *   collection_ids: ["team"],
   *   filters: {
   *     "metadata.email": { $ilike: "%@company.com" }  // Case-insensitive
   *   }
   * });
   *
   * @example
   * // Array operations
   * await client.search({
   *   query: "developers",
   *   collection_ids: ["team"],
   *   filters: {
   *     "metadata.skills": { $overlap: ["python", "typescript"] }  // Has any
   *   }
   * });
   *
   * @example
   * // Nested paths
   * await client.search({
   *   query: "users",
   *   collection_ids: ["profiles"],
   *   filters: {
   *     "metadata.user.preferences.theme": { $eq: "dark" }
   *   }
   * });
   *
   * @example
   * // Complex logical combinations
   * await client.search({
   *   query: "candidates",
   *   collection_ids: ["hiring"],
   *   filters: {
   *     $and: [
   *       { "metadata.verified": true },
   *       { "metadata.level": { $gte: 5 } },
   *       {
   *         $or: [
   *           { "metadata.skills": { $overlap: ["python", "go"] } },
   *           { "metadata.years_experience": { $gte: 8 } }
   *         ]
   *       }
   *     ]
   *   }
   * });
   *
   * @remarks
   * Supported Operators:
   * - Comparison: $eq, $ne, $lt, $lte, $gt, $gte
   * - String: $like (case-sensitive), $ilike (case-insensitive)
   * - Array: $in, $nin, $overlap, $contains
   * - JSONB: $json_contains
   * - Logical: $and, $or
   *
   * For comprehensive filtering documentation, see the Metadata Filtering Guide:
   * https://docs.nebulacloud.app/guides/metadata-filtering
   */
  async search(options) {
    const data = {
      query: options.query
    };
    if (options.effort) {
      data.effort = options.effort;
    }
    if (options.collection_ids) {
      const collectionIds = Array.isArray(options.collection_ids) ? options.collection_ids : [options.collection_ids];
      const validCollectionIds = collectionIds.filter((id) => id && id.trim() !== "");
      if (validCollectionIds.length) {
        data.collection_ids = validCollectionIds;
      }
    }
    if (options.filters) {
      data.filters = options.filters;
    }
    if (options.searchSettings) {
      data.search_settings = options.searchSettings;
    }
    const response = await this._makeRequest("POST", "/v1/memories/search", data);
    const memoryResponseData = response.results;
    const memoryResponse = {
      query: memoryResponseData.query || options.query,
      entities: memoryResponseData.entities || [],
      facts: memoryResponseData.facts || [],
      utterances: memoryResponseData.utterances || [],
      inference_hints: memoryResponseData.inference_hints || [],
      fact_to_chunks: memoryResponseData.fact_to_chunks || {},
      entity_to_facts: memoryResponseData.entity_to_facts || {},
      retrieved_at: memoryResponseData.retrieved_at || (/* @__PURE__ */ new Date()).toISOString(),
      focus: memoryResponseData.focus,
      total_traversal_time_ms: memoryResponseData.total_traversal_time_ms,
      query_intent: memoryResponseData.query_intent
    };
    return memoryResponse;
  }
  // Health Check
  async healthCheck() {
    return this._makeRequest("GET", "/v1/health");
  }
  // Helpers
  _collectionFromDict(data) {
    let createdAt;
    if (data.created_at) {
      if (typeof data.created_at === "string") {
        createdAt = data.created_at;
      } else if (data.created_at instanceof Date) {
        createdAt = data.created_at.toISOString();
      }
    }
    let updatedAt;
    if (data.updated_at) {
      if (typeof data.updated_at === "string") {
        updatedAt = data.updated_at;
      } else if (data.updated_at instanceof Date) {
        updatedAt = data.updated_at.toISOString();
      }
    }
    const collectionId = String(data.id || "");
    const collectionName = String(data.name || "");
    const collectionDescription = typeof data.description === "string" ? data.description : void 0;
    const collectionOwnerId = data.owner_id ? String(data.owner_id) : void 0;
    const memoryCount = typeof data.memory_count === "number" ? data.memory_count : 0;
    const metadata = {
      graph_collection_status: String(data.graph_collection_status || ""),
      graph_sync_status: String(data.graph_sync_status || ""),
      user_count: typeof data.user_count === "number" ? data.user_count : 0
    };
    return {
      id: collectionId,
      name: collectionName,
      description: collectionDescription,
      metadata,
      created_at: createdAt,
      updated_at: updatedAt,
      memory_count: memoryCount,
      owner_id: collectionOwnerId
    };
  }
  _memoryResponseFromDict(data, collectionIds) {
    let createdAt;
    if (data.created_at) {
      if (typeof data.created_at === "string") {
        createdAt = data.created_at;
      } else if (data.created_at instanceof Date) {
        createdAt = data.created_at.toISOString();
      }
    }
    let updatedAt;
    if (data.updated_at) {
      if (typeof data.updated_at === "string") {
        updatedAt = data.updated_at;
      } else if (data.updated_at instanceof Date) {
        updatedAt = data.updated_at.toISOString();
      }
    }
    const engramId = String(data.id || "");
    const content = typeof data.content === "string" ? data.content : typeof data.text === "string" ? data.text : void 0;
    let chunks;
    if (data.chunks && Array.isArray(data.chunks)) {
      if (data.chunks.every((x) => typeof x === "string")) {
        chunks = data.chunks.map((text) => ({
          id: "",
          content: text,
          metadata: {}
        }));
      } else {
        chunks = data.chunks.filter((item) => item && typeof item === "object" && ("text" in item || "content" in item)).map((item) => ({
          id: String(item.id || ""),
          content: String(item.text || item.content || ""),
          metadata: typeof item.metadata === "object" && item.metadata !== null ? item.metadata : {},
          role: typeof item.role === "string" ? item.role : void 0
        }));
      }
    }
    const metadata = { ...typeof data.metadata === "object" && data.metadata !== null ? data.metadata : {} };
    if (data.engram_id) {
      metadata.engram_id = data.engram_id;
    }
    let finalId = engramId;
    if (data.engram_id && !engramId) {
      finalId = String(data.engram_id);
    }
    if (data.document_metadata && typeof data.document_metadata === "object") {
      Object.assign(metadata, data.document_metadata);
    }
    return {
      id: finalId,
      memory_id: finalId,
      content,
      chunks,
      metadata,
      collection_ids: Array.isArray(data.collection_ids) ? data.collection_ids : collectionIds,
      created_at: createdAt,
      updated_at: updatedAt
    };
  }
  _searchResultFromDict(data) {
    const content = typeof data.content === "string" ? data.content : typeof data.text === "string" ? data.text : "";
    const resultId = String(data.id || data.chunk_id || "");
    return {
      id: String(resultId),
      content: String(content),
      score: typeof data.score === "number" ? data.score : Number(data.score || 0),
      metadata: typeof data.metadata === "object" && data.metadata !== null ? data.metadata : {},
      source: typeof data.source === "string" ? data.source : void 0
    };
  }
  _searchResultFromGraphDict(data) {
    const rid = data.id ? String(data.id) : "";
    const resultTypeStr = typeof data.result_type === "string" ? data.result_type : "entity";
    const rtype = GraphSearchResultType[resultTypeStr.toUpperCase()] || "entity" /* ENTITY */;
    const content = typeof data.content === "object" && data.content !== null ? data.content : {};
    const score = data.score !== void 0 ? Number(data.score) : 0;
    const metadata = typeof data.metadata === "object" && data.metadata !== null ? data.metadata : {};
    const chunkIds = Array.isArray(data.chunk_ids) ? data.chunk_ids : void 0;
    let timestamp;
    if (data.timestamp) {
      if (typeof data.timestamp === "string") {
        timestamp = data.timestamp;
      } else if (data.timestamp instanceof Date) {
        timestamp = data.timestamp.toISOString();
      } else {
        const parsed = new Date(String(data.timestamp));
        if (!Number.isNaN(parsed.valueOf())) {
          timestamp = parsed.toISOString();
        }
      }
    }
    const displayName = typeof data.display_name === "string" ? data.display_name : void 0;
    const sourceRole = typeof data.source_role === "string" ? data.source_role : void 0;
    const engramId = data.engram_id ? String(data.engram_id) : void 0;
    const ownerId = data.owner_id ? String(data.owner_id) : void 0;
    let entity;
    let rel;
    let comm;
    if (rtype === "entity" /* ENTITY */) {
      entity = {
        id: content.id ? String(content.id) : void 0,
        name: String(content.name || ""),
        description: String(content.description || ""),
        metadata: typeof content.metadata === "object" && content.metadata !== null ? content.metadata : {}
      };
    } else if (rtype === "relationship" /* RELATIONSHIP */) {
      rel = {
        id: content.id ? String(content.id) : void 0,
        subject: String(content.subject || ""),
        predicate: String(content.predicate || ""),
        object: String(content.object || ""),
        subject_id: content.subject_id ? String(content.subject_id) : void 0,
        object_id: content.object_id ? String(content.object_id) : void 0,
        description: typeof content.description === "string" ? content.description : void 0,
        metadata: typeof content.metadata === "object" && content.metadata !== null ? content.metadata : {}
      };
    } else {
      comm = {
        id: content.id ? String(content.id) : void 0,
        name: String(content.name || ""),
        summary: String(content.summary || ""),
        metadata: typeof content.metadata === "object" && content.metadata !== null ? content.metadata : {}
      };
    }
    return {
      id: rid,
      score,
      metadata,
      source: "graph",
      content: void 0,
      graph_result_type: rtype,
      graph_entity: entity,
      graph_relationship: rel,
      graph_community: comm,
      chunk_ids: chunkIds,
      timestamp,
      display_name: displayName,
      source_role: sourceRole,
      engram_id: engramId,
      owner_id: ownerId
    };
  }
  async _sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    let crypto;
    if (typeof globalThis.crypto !== "undefined" && globalThis.crypto.subtle) {
      crypto = globalThis.crypto;
    } else {
      const nodeCrypto = await import('crypto');
      crypto = nodeCrypto.webcrypto;
    }
    const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
    return hashHex;
  }
  _formDataFromObject(obj) {
    const formData = new FormData();
    Object.entries(obj).forEach(([key, value]) => {
      formData.append(key, value);
    });
    return formData;
  }
  /**
   * Convert and process multimodal content parts, auto-uploading large base64 files to S3.
   *
   * - Binary parts (`image`/`audio`/`document` with `data`) larger than 5MB are uploaded to S3 and converted to `s3_ref`.
   */
  async _processContentParts(contentParts) {
    const processed = [];
    for (const part of contentParts) {
      if (part.type !== "text" && part.type !== "s3_ref" && "data" in part && part.data) {
        const filePart = part;
        const dataSize = Math.floor(String(filePart.data).length * 3 / 4);
        if (dataSize > _Nebula.MAX_INLINE_SIZE) {
          const filename = filePart.filename || `file.bin`;
          const mediaType = filePart.media_type || "application/octet-stream";
          const uploadInfo = await this.getUploadUrl({
            filename,
            content_type: mediaType,
            file_size: dataSize
          });
          let bytes;
          const atobFn = globalThis.atob;
          if (typeof atobFn === "function") {
            const binaryString = atobFn(String(filePart.data));
            bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
          } else {
            const { Buffer } = await import('buffer');
            bytes = Uint8Array.from(Buffer.from(String(filePart.data), "base64"));
          }
          await fetch(uploadInfo.upload_url, {
            method: "PUT",
            body: bytes,
            headers: { "Content-Type": mediaType }
          });
          processed.push({
            type: "s3_ref",
            s3_key: uploadInfo.s3_key,
            media_type: mediaType,
            filename
          });
          continue;
        }
      }
      processed.push(part);
    }
    return processed;
  }
  /**
   * Get a presigned URL for uploading large files to S3.
   */
  async getUploadUrl(options) {
    const response = await this._makeRequest("POST", "/v1/memories/upload", void 0, {
      filename: options.filename,
      content_type: options.content_type,
      file_size: options.file_size
    });
    if (response.results) {
      return response.results;
    }
    return response;
  }
};
// Files larger than 5MB are automatically uploaded to S3
_Nebula.MAX_INLINE_SIZE = 5 * 1024 * 1024;
var Nebula = _Nebula;

// src/content.ts
var MIME_TYPES = {
  // Images
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".heic": "image/heic",
  ".bmp": "image/bmp",
  ".tiff": "image/tiff",
  // Audio
  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
  ".m4a": "audio/m4a",
  ".ogg": "audio/ogg",
  ".flac": "audio/flac",
  ".aac": "audio/aac",
  ".webm": "audio/webm",
  // Documents
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
  ".epub": "application/epub+zip"
};
var NebulaContent = class {
  /**
   * Create a FileContentPart from a file path.
   * Automatically deduces media_type and the backend 'type' (image, audio, document).
   */
  static async fromFile(filePath, mediaType) {
    let fs;
    let path;
    try {
      fs = await import('fs/promises');
      path = await import('path');
    } catch (e) {
      throw new Error("File system operations are only supported in Node.js environments.");
    }
    const absolutePath = path.resolve(filePath);
    const fileName = path.basename(absolutePath);
    const ext = path.extname(absolutePath).toLowerCase();
    const detectedMime = mediaType || MIME_TYPES[ext] || "application/octet-stream";
    const buffer = await fs.readFile(absolutePath);
    const data = buffer.toString("base64");
    return {
      data,
      media_type: detectedMime,
      filename: fileName
    };
  }
};

// src/index.ts
var MemoryBase = (data) => data;
var Memory2 = Object.assign(MemoryBase, {
  /**
   * Helper to create a file content part from a file path.
   * Alias for NebulaContent.fromFile().
   */
  File: NebulaContent.fromFile,
  /**
   * Helper to create a complete Memory object from a single file.
   */
  async fromFile(filePath, collection_id, metadata, role) {
    return {
      collection_id,
      content: [await NebulaContent.fromFile(filePath)],
      metadata: metadata || {},
      role
    };
  }
});

export { GraphSearchResultType, Memory2 as Memory, Nebula, NebulaAuthenticationException, NebulaClientException, NebulaCollectionNotFoundException, NebulaContent, NebulaException, NebulaNotFoundException, NebulaRateLimitException, NebulaValidationException, Nebula as default };
//# sourceMappingURL=index.mjs.map
//# sourceMappingURL=index.mjs.map