import {
  Memory,
  MemoryResponse,
  Collection,
  SearchResult,
  MemoryRecall,
  GraphSearchResultType,
  GraphEntityResult,
  GraphRelationshipResult,
  GraphCommunityResult,
  NebulaClientConfig,
  NebulaException,
  NebulaClientException,
  NebulaAuthenticationException,
  NebulaRateLimitException,
  NebulaValidationException,
  NebulaNotFoundException,
} from './types';

/**
 * Official Nebula JavaScript/TypeScript SDK
 * Mirrors the exact Nebula Python SDK client.py implementation
 */
export class Nebula {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  // Files larger than 5MB are automatically uploaded to S3
  private static readonly MAX_INLINE_SIZE = 5 * 1024 * 1024; // 5MB

  constructor(config: NebulaClientConfig) {
    this.apiKey = config.apiKey;
    if (!this.apiKey) {
      throw new NebulaClientException(
        'API key is required. Pass it to the constructor or set NEBULA_API_KEY environment variable.'
      );
    }

    this.baseUrl = (config.baseUrl || 'https://api.nebulacloud.app').replace(/\/$/, '');
    this.timeout = config.timeout || 30000;
  }

  // Public mutators used by tests
  setApiKey(next: string) {
    this.apiKey = next;
  }
  setBaseUrl(next: string) {
    this.baseUrl = (next || this.baseUrl).replace(/\/$/, '');
  }
  // Kept for backwards-compat tests; no-op in current implementation
  setCorsProxy(_next: string) {
    // no-op
  }

  /** Check if API key is set */
  isApiKeySet(): boolean {
    return !!(this.apiKey && this.apiKey.trim() !== '');
  }

  /** Detect if a token looks like a Nebula API key (public.raw) */
  private _isNebulaApiKey(token?: string): boolean {
    const candidate = token || this.apiKey;
    if (!candidate) return false;
    const parts = candidate.split('.');
    if (parts.length !== 2) return false;
    const [publicPart, rawPart] = parts;
    return (publicPart.startsWith('key_') || publicPart.startsWith('neb_')) && !!rawPart && rawPart.length > 0;
  }

  /** Build authentication headers */
  private _buildAuthHeaders(includeContentType: boolean = true): Record<string, string> {
    const headers: Record<string, string> = {};

    if (this._isNebulaApiKey()) {
      headers['X-API-Key'] = this.apiKey;
    } else {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    if (includeContentType) {
      headers['Content-Type'] = 'application/json';
    }

    return headers;
  }

  /** Make an HTTP request to the Nebula API */
  private async _makeRequest(
    method: string,
    endpoint: string,
    jsonData?: unknown,  // Can be object, array, or primitive for JSON body
    params?: Record<string, unknown>
  ): Promise<unknown> {
    const url = new URL(endpoint, this.baseUrl);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          // Handle array parameters (e.g., collection_ids)
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
        body: jsonData ? JSON.stringify(jsonData) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.status === 200 || response.status === 202) {
        return await response.json();
      } else if (response.status === 401) {
        throw new NebulaAuthenticationException('Invalid API key');
      } else if (response.status === 429) {
        throw new NebulaRateLimitException('Rate limit exceeded');
      } else if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new NebulaValidationException(errorData.message || 'Validation error', errorData.details);
      } else if (response.status === 422) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[SDK] 422 Validation error - Full details:');
        console.error('  Status:', response.status);
        console.error('  Error data:', JSON.stringify(errorData, null, 2));
        console.error('  Message:', errorData.message);
        console.error('  Detail:', errorData.detail);
        throw new NebulaValidationException(
          errorData.message || (typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)) || 'Validation error',
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

      if (error instanceof Error && error.name === 'AbortError') {
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
  async createCollection(options: {
    name: string;
    description?: string;
    metadata?: Record<string, unknown>;
  }): Promise<Collection> {
    const data: Record<string, unknown> = { name: options.name };
    if (options.description) data.description = options.description;
    if (options.metadata) data.metadata = options.metadata;

    const response = await this._makeRequest('POST', '/v1/collections', data);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }

  /** Get a specific collection by ID */
  async getCollection(collectionId: string): Promise<Collection> {
    const response = await this._makeRequest('GET', `/v1/collections/${collectionId}`);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }

  /** Get a specific collection by name */
  async getCollectionByName(name: string): Promise<Collection> {
    const response = await this._makeRequest('GET', `/v1/collections/name/${name}`);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }

  /** Get all collections */
  async listCollections(options?: {
    limit?: number;
    offset?: number;
    name?: string;
  }): Promise<Collection[]> {
    const params: Record<string, unknown> = {
      limit: options?.limit ?? 100,
      offset: options?.offset ?? 0
    };
    if (options?.name !== undefined) {
      params.name = options.name;
    }
    const response = await this._makeRequest('GET', '/v1/collections', undefined, params) as { results?: unknown[] } | unknown[] | unknown;

    let collections: unknown[];
    if (response.results) {
      collections = response.results;
    } else if (Array.isArray(response)) {
      collections = response;
    } else {
      collections = [response];
    }

    return collections.map((collection) => this._collectionFromDict(collection));
  }

  /** Update a collection */
  async updateCollection(options: {
    collectionId: string;
    name?: string;
    description?: string;
    metadata?: Record<string, unknown>;
  }): Promise<Collection> {
    const data: Record<string, unknown> = {};
    if (options.name !== undefined) data.name = options.name;
    if (options.description !== undefined) data.description = options.description;
    if (options.metadata !== undefined) data.metadata = options.metadata;

    const response = await this._makeRequest('POST', `/v1/collections/${options.collectionId}`, data);
    const result = response.results || response;
    return this._collectionFromDict(result);
  }

  /** Delete a collection */
  async deleteCollection(collectionId: string): Promise<boolean> {
    await this._makeRequest('DELETE', `/v1/collections/${collectionId}`);
    return true;
  }

  // Memory Management Methods

  /**
   * Legacy convenience: store raw text content into a collection as a document
   */
  async store(content: string, collectionId: string, metadata: Record<string, unknown> = {}): Promise<MemoryResponse> {
    const docMetadata = {
      ...metadata,
      memory_type: 'memory',
      timestamp: new Date().toISOString(),
    } as Record<string, unknown>;

    const payload = {
      collection_id: collectionId,
      raw_text: String(content || ''),
      metadata: docMetadata,
      ingestion_mode: 'fast',
    } as const;

    const response = await this._makeRequest('POST', '/v1/memories', payload);
    const id = response?.results?.engram_id || response?.results?.id || response?.id || '';

    const result: MemoryResponse = {
      id: String(id),
      content: String(content || ''),
      metadata: docMetadata,
      collection_ids: [collectionId],
      created_at: docMetadata.timestamp,
      updated_at: docMetadata.timestamp,
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
  async storeMemory(
    memory: Memory | Record<string, unknown>,
    name?: string
  ): Promise<string> {
    let mem: Memory;

    if ('collection_id' in memory) {
      mem = memory as Memory;
    } else {
      // Support both camelCase (collectionId) and snake_case (collection_id)
      const memRecord = memory as Record<string, unknown>;
      mem = {
        collection_id: (memRecord.collection_id as string) || (memRecord.collectionId as string) || '',
        content: (memRecord.content as Memory['content']) || '',
        role: memRecord.role as string | undefined,
        memory_id: (memRecord.memory_id as string) || (memRecord.memoryId as string) || undefined,
        metadata: (memRecord.metadata as Record<string, unknown>) || {},
      };
    }

    // If memory_id is present, append to existing memory
    if (mem.memory_id) {
      return await this._appendToMemory(mem.memory_id, mem);
    }

    // Automatically infer memory type from role presence
    const memoryType = mem.role ? 'conversation' : 'document';

    // Handle conversation creation
    if (memoryType === 'conversation') {
      // Use new unified POST /v1/memories endpoint with JSON body
      const messages = [];

      // If content and role provided, include as initial message
      if (mem.content && mem.role) {
        // Check if content is multimodal (array of content parts)
        const isMultimodal =
          Array.isArray(mem.content) &&
          mem.content.some((part) => part && typeof part === 'object' && 'type' in (part as Record<string, unknown>));

        const msgContent = isMultimodal
          ? JSON.stringify(await this._processContentParts(mem.content as unknown[]))
          : String(mem.content);
        
        const memRecord = mem as Memory & { authority?: number };
        messages.push({
          content: msgContent,
          role: mem.role,
          metadata: mem.metadata || {},
          ...(typeof memRecord.authority === 'number' ? { authority: Number(memRecord.authority) } : {})
        });
      }

      // Backend requires at least one message for conversation creation
      if (messages.length === 0) {
        throw new NebulaClientException('Cannot create conversation without messages. Provide content and role.');
      }

      const data = {
        collection_id: mem.collection_id,
        name: name || 'Conversation',
        messages: messages,
        metadata: mem.metadata || {},
      };

      const response = await this._makeRequest('POST', '/v1/memories', data) as { results?: { memory_id?: string; id?: string } };

      if (response.results) {
        const convId = response.results.memory_id || response.results.id;
        if (!convId) {
          throw new NebulaClientException('Failed to create conversation: no id returned');
        }
        return String(convId);
      }
      throw new NebulaClientException('Failed to create conversation: invalid response format');
    }

    // Handle document/text memory
    // Check if content is multimodal (array of content parts)
    const isMultimodal =
      Array.isArray(mem.content) &&
      mem.content.some((part) => part && typeof part === 'object' && 'type' in (part as Record<string, unknown>));
    
    const docMetadata = { ...mem.metadata } as Record<string, unknown>;
    docMetadata.memory_type = 'memory';
    
    // If authority provided for document, persist in metadata for ranking
    const memRecord = mem as Memory & { authority?: number };
    if (typeof memRecord.authority === 'number') {
      const v = Number(memRecord.authority);
      if (!Number.isNaN(v) && v >= 0 && v <= 1) {
        docMetadata.authority = v;
      }
    }

    if (isMultimodal) {
      // Process content parts, auto-uploading large files to S3 when needed
      const processedParts = await this._processContentParts(mem.content as unknown[]);

      // Backend JSON create_memory expects a string `raw_text` (or `chunks`),
      // so we serialize multimodal parts as JSON text.
      const payload: Record<string, unknown> = {
        collection_id: mem.collection_id,
        raw_text: JSON.stringify(processedParts),
        metadata: docMetadata,
        ingestion_mode: 'fast',
      };

      const response = await this._makeRequest('POST', '/v1/memories', payload) as { results?: { engram_id?: string; id?: string }; id?: string };
      const id = response?.results?.engram_id || response?.results?.id || response?.id || '';
      return String(id || '');
    }

    // Plain text content
    const contentText = String(mem.content || '');
    if (!contentText) {
      throw new NebulaClientException('Content is required for document memories');
    }

    const payload = {
      collection_id: mem.collection_id,
      raw_text: contentText,
      metadata: docMetadata,
      ingestion_mode: 'fast',
    } as const;

    const response = await this._makeRequest('POST', '/v1/memories', payload) as { results?: { engram_id?: string; id?: string }; id?: string };
    const id = response?.results?.engram_id || response?.results?.id || response?.id || '';
    return String(id || '');
  }

  /**
   * Internal method to append content to an existing memory
   *
   * @throws NebulaNotFoundException if memory_id doesn't exist
   */
  private async _appendToMemory(memoryId: string, memory: Memory): Promise<string> {
    const collectionId = memory.collection_id;
    const content = memory.content;
    const metadata = memory.metadata;

    if (!collectionId) {
      throw new NebulaClientException('collection_id is required');
    }

    const payload: Record<string, unknown> = {
      collection_id: collectionId,
    };

    // Determine content type and set appropriate field
    if (Array.isArray(content)) {
      if (content.length > 0 && typeof content[0] === 'object' && 'content' in content[0]) {
        // Array of message objects (conversation)
        payload.messages = content;
      } else {
        // Array of strings (chunks)
        payload.chunks = content;
      }
    } else if (typeof content === 'string') {
      // Raw text string
      payload.raw_text = content;
    } else {
      throw new NebulaClientException(
        'content must be a string, array of strings, or array of message objects'
      );
    }

    if (metadata) {
      payload.metadata = metadata;
    }

    try {
      await this._makeRequest('POST', `/v1/memories/${memoryId}/append`, payload);
      return memoryId;
    } catch (error) {
      // Convert 404 errors to NebulaNotFoundException
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(memoryId, 'Memory');
      }
      throw error;
    }
  }

  /** Store multiple memories using the unified engrams API */
  async storeMemories(memories: Memory[]): Promise<string[]> {
    const results: string[] = [];
    const convGroups: Record<string, Memory[]> = {};
    const others: Memory[] = [];

    for (const m of memories) {
      if (m.role) {
        const key = m.memory_id || `__new__::${m.collection_id}`;
        if (!convGroups[key]) convGroups[key] = [];
        convGroups[key].push(m);
      } else {
        others.push(m);
      }
    }

    // Process conversation groups using new unified API
    for (const [key, group] of Object.entries(convGroups)) {
      const collectionId = group[0].collection_id;
      let convId: string;

      // Prepare messages for the conversation
      const messages: Array<{ content: string; role: string; metadata?: Record<string, unknown>; authority?: number }> = [];
      for (const m of group) {
        const isMultimodal =
          Array.isArray(m.content) &&
          (m.content as unknown[]).some((part) => part && typeof part === 'object' && 'type' in (part as Record<string, unknown>));

        const text = isMultimodal
          ? JSON.stringify(await this._processContentParts(m.content as unknown[]))
          : String(m.content || '');

        if (!text.trim()) continue;

        const mRecord = m as Memory & { authority?: number };
        messages.push({
          content: text,
          role: m.role!,
          metadata: m.metadata || {},
          ...(typeof mRecord.authority === 'number' ? { authority: Number(mRecord.authority) } : {}),
        });
      }

      if (!messages.length) {
        throw new NebulaClientException(
          'Cannot create/append conversation without messages. Provide non-empty content.'
        );
      }

      // Create conversation if needed
      if (key.startsWith('__new__::')) {
        // Create conversation with initial messages using JSON body
        const data = {
          collection_id: collectionId,
          name: 'Conversation',
          messages: messages,
          metadata: {},
        };

        const response = await this._makeRequest('POST', '/v1/memories', data) as { results?: { memory_id?: string; id?: string } };

        if (response.results) {
          convId = response.results.memory_id || response.results.id;
          if (!convId) {
            throw new NebulaClientException('Failed to create conversation: no id returned');
          }
        } else {
          throw new NebulaClientException('Failed to create conversation: invalid response format');
        }
      } else {
        // Append to existing conversation
        convId = key;

        const appendMem: Memory = {
          collection_id: collectionId,
          content: messages as Memory['content'],
          memory_id: convId,
          metadata: {},
        };
        await this._appendToMemory(convId, appendMem);
      }

      results.push(...Array(group.length).fill(String(convId)));
    }

    // Process others (text/json) individually
    for (const m of others) {
      results.push(await this.storeMemory(m));
    }

    return results;
  }

  /** Delete one or more memories */
  async delete(memoryIds: string | string[]): Promise<boolean | {
    message: string;
    results: {
      successful: string[];
      failed: Array<{ id: string; error: string }>;
      summary: {
        total: number;
        succeeded: number;
        failed: number;
      };
    };
  }> {
    try {
      console.log('[SDK] delete() called with:', { memoryIds, type: typeof memoryIds, isArray: Array.isArray(memoryIds) });

      // Handle single ID vs array
      if (typeof memoryIds === 'string') {
        console.log('[SDK] Single deletion path for ID:', memoryIds);
        // Single deletion - try existing endpoint first for backward compatibility
        try {
          await this._makeRequest('DELETE', `/v1/memories/${memoryIds}`);
          return true;
        } catch {
          // Fall back to new unified endpoint
          console.log('[SDK] Falling back to POST /v1/memories/delete with single ID');
          // Send the UUID string directly as body (not wrapped in {ids: ...})
          const response = await this._makeRequest('POST', '/v1/memories/delete', memoryIds) as { success?: boolean } | boolean;
          return typeof response === 'object' && response.success !== undefined
            ? response.success
            : true;
        }
      } else {
        console.log('[SDK] Batch deletion path for IDs:', memoryIds);
        console.log('[SDK] Sending POST request with body:', memoryIds);
        // Batch deletion - send array directly as body (not wrapped in {ids: ...})
        // FastAPI Body() without embed=True expects the value directly
        const response = await this._makeRequest('POST', '/v1/memories/delete', memoryIds);
        console.log('[SDK] Batch deletion response:', response);
        return response;
      }
    } catch (error) {
      console.error('[SDK] Delete error:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new NebulaClientException(`Unknown error: ${String(error)}`);
    }
  }

  /** Delete a specific chunk or message within a memory */
  async deleteChunk(chunkId: string): Promise<boolean> {
    try {
      await this._makeRequest('DELETE', `/v1/chunks/${chunkId}`);
      return true;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(chunkId, 'Chunk');
      }
      throw error;
    }
  }

  /** Update a specific chunk or message within a memory */
  async updateChunk(
    chunkId: string,
    content: string,
    metadata?: Record<string, unknown>
  ): Promise<boolean> {
    const payload: Record<string, unknown> = { content };
    if (metadata !== undefined) {
      payload.metadata = metadata;
    }

    try {
      await this._makeRequest('PATCH', `/v1/chunks/${chunkId}`, payload);
      return true;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(chunkId, 'Chunk');
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
  async updateMemory(options: {
    memoryId: string;
    name?: string;
    metadata?: Record<string, unknown>;
    collectionIds?: string[];
    mergeMetadata?: boolean;
  }): Promise<boolean> {
    const payload: Record<string, unknown> = {};

    if (options.name !== undefined) {
      payload.name = options.name;
    }
    if (options.metadata !== undefined) {
      payload.metadata = options.metadata;
      payload.merge_metadata = options.mergeMetadata ?? false;
    }
    if (options.collectionIds !== undefined) {
      payload.collection_ids = options.collectionIds;
    }

    if (Object.keys(payload).length === 0) {
      throw new NebulaValidationException(
        'At least one field (name, metadata, or collectionIds) must be provided to update'
      );
    }

    try {
      await this._makeRequest('PATCH', `/v1/memories/${options.memoryId}`, payload);
      return true;
    } catch (error) {
      if (error instanceof NebulaException && error.statusCode === 404) {
        throw new NebulaNotFoundException(options.memoryId, 'Memory');
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
  async listMemories(options: {
    collection_ids: string | string[];
    limit?: number;
    offset?: number;
    metadata_filters?: Record<string, unknown>;
  }): Promise<MemoryResponse[]> {
    const ids = Array.isArray(options.collection_ids) ? options.collection_ids : [options.collection_ids];
    if (!ids.length) {
      throw new NebulaClientException('collection_ids must be provided to list_memories().');
    }

    const params: Record<string, unknown> = {
      limit: options.limit ?? 100,
      offset: options.offset ?? 0,
      collection_ids: ids
    };

    // Add metadata_filters if provided (serialize to JSON string for query parameter)
    if (options.metadata_filters) {
      params.metadata_filters = JSON.stringify(options.metadata_filters);
    }

    const response = await this._makeRequest('GET', '/v1/memories', undefined, params) as { results?: unknown[] } | unknown[] | unknown;

    let documents: unknown[];
    if (response.results) {
      documents = response.results;
    } else if (Array.isArray(response)) {
      documents = response;
    } else {
      documents = [response];
    }

    return documents.map((doc) => this._memoryResponseFromDict(doc, ids));
  }

  /** Get a specific memory by engram ID */
  async getMemory(memoryId: string): Promise<MemoryResponse> {
    const response = await this._makeRequest('GET', `/v1/memories/${memoryId}`) as { text?: string; content?: string; chunks?: unknown[]; id?: string; metadata?: Record<string, unknown>; collection_ids?: string[] };

    const content = response.text || response.content;
    const chunks = Array.isArray(response.chunks) ? response.chunks : undefined;

    const memoryData = {
      id: response.id,
      content,
      chunks,
      metadata: response.metadata || {},
      collection_ids: response.collection_ids || [],
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
   * @param options.effort - Compute effort budget (auto/low/medium/high). Controls traversal compute, not MemoryRecall size.
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
  async search(options: {
    query: string;
    collection_ids?: string | string[];
    effort?: 'auto' | 'low' | 'medium' | 'high';
    filters?: Record<string, unknown>;
    searchSettings?: Record<string, unknown>;
  }): Promise<MemoryRecall> {
    // Build request data - pass params directly to API (no wrapping needed)
    const data: Record<string, unknown> = {
      query: options.query,
    };

    if (options.effort) {
      data.effort = options.effort;
    }

    // Add collection_ids if provided
    if (options.collection_ids) {
      const collectionIds = Array.isArray(options.collection_ids) ? options.collection_ids : [options.collection_ids];
      const validCollectionIds = collectionIds.filter(id => id && id.trim() !== '');
      if (validCollectionIds.length) {
        data.collection_ids = validCollectionIds;
      }
    }

    // Add filters if provided
    if (options.filters) {
      data.filters = options.filters;
    }

    // Add advanced search settings if provided
    if (options.searchSettings) {
      data.search_settings = options.searchSettings;
    }

    const response = await this._makeRequest('POST', '/v1/memories/search', data) as { results?: MemoryRecall };

    // Backend returns MemoryRecall wrapped in { results: MemoryRecall }
    // The @base_endpoint decorator always wraps successful responses as {"results": MemoryRecall}
    const memoryRecallData = response.results as MemoryRecall;

    // Ensure we have a proper MemoryRecall structure with all fields
    const memoryRecall: MemoryRecall = {
      query: memoryRecallData.query || options.query,
      entities: memoryRecallData.entities || [],
      facts: memoryRecallData.facts || [],
      utterances: memoryRecallData.utterances || [],
      fact_to_chunks: memoryRecallData.fact_to_chunks || {},
      entity_to_facts: memoryRecallData.entity_to_facts || {},
      retrieved_at: memoryRecallData.retrieved_at || new Date().toISOString(),
      focus: memoryRecallData.focus,
      total_traversal_time_ms: memoryRecallData.total_traversal_time_ms,
      query_intent: memoryRecallData.query_intent,
    };

    return memoryRecall;
  }

  // Health Check
  async healthCheck(): Promise<Record<string, unknown>> {
    return this._makeRequest('GET', '/v1/health') as Promise<Record<string, unknown>>;
  }

  // Helpers

  private _collectionFromDict(data: Record<string, unknown>): Collection {
    let createdAt: string | undefined;
    if (data.created_at) {
      createdAt = typeof data.created_at === 'string' ? data.created_at : data.created_at.toISOString();
    }

    let updatedAt: string | undefined;
    if (data.updated_at) {
      updatedAt = typeof data.updated_at === 'string' ? data.updated_at : data.updated_at.toISOString();
    }

    const collectionId = String(data.id || '');
    const collectionName = data.name || '';
    const collectionDescription = data.description;
    const collectionOwnerId = data.owner_id ? String(data.owner_id) : undefined;
    const memoryCount = data.document_count || 0;

    const metadata = {
      graph_collection_status: data.graph_collection_status || '',
      graph_sync_status: data.graph_sync_status || '',
      user_count: data.user_count || 0,
      document_count: data.document_count || 0,
    };

    return {
      id: collectionId,
      name: collectionName,
      description: collectionDescription,
      metadata,
      created_at: createdAt,
      updated_at: updatedAt,
      memory_count: memoryCount,
      owner_id: collectionOwnerId,
    } as Collection;
  }

  private _memoryResponseFromDict(data: Record<string, unknown>, collectionIds: string[]): MemoryResponse {
    let createdAt: string | undefined;
    if (data.created_at) {
      createdAt = typeof data.created_at === 'string' ? data.created_at : data.created_at.toISOString();
    }

    let updatedAt: string | undefined;
    if (data.updated_at) {
      updatedAt = typeof data.updated_at === 'string' ? data.updated_at : data.updated_at.toISOString();
    }

    const engramId = String(data.id || '');
    const content = data.content || data.text;
    let chunks: string[] | undefined;

    if (data.chunks && Array.isArray(data.chunks)) {
      if (data.chunks.every((x: unknown) => typeof x === 'string')) {
        chunks = data.chunks as string[];
      } else {
        chunks = (data.chunks as Array<Record<string, unknown>>)
          .filter((item: Record<string, unknown>) => item && typeof item === 'object' && 'text' in item)
          .map((item: Record<string, unknown>) => item.text as string);
      }
    }

    const metadata = { ...(data.metadata as Record<string, unknown> || {}) };
    if (data.engram_id) {
      metadata.engram_id = data.engram_id;
    }

    let finalId = engramId;
    if (data.engram_id && !engramId) {
      finalId = data.engram_id;
    }

    if (data.document_metadata) {
      Object.assign(metadata, data.document_metadata);
    }

    return {
      id: finalId,
      content,
      chunks,
      metadata,
      collection_ids: data.collection_ids || collectionIds,
      created_at: createdAt,
      updated_at: updatedAt,
    } as MemoryResponse;
  }

  private _searchResultFromDict(data: Record<string, unknown>): SearchResult {
    const content = data.content || data.text || '';
    const resultId = data.id || data.chunk_id || '';

    return {
      id: String(resultId),
      content: String(content),
      score: Number(data.score || 0.0),
      metadata: data.metadata || {},
      source: data.source,
    };
  }

  private _searchResultFromGraphDict(data: Record<string, unknown>): SearchResult {
    const rid = data.id ? String(data.id) : '';
    const rtype =
      GraphSearchResultType[(data.result_type || 'entity').toUpperCase() as keyof typeof GraphSearchResultType] ||
      GraphSearchResultType.ENTITY;
    const content = (data.content || {}) as Record<string, unknown>;
    const score = data.score !== undefined ? Number(data.score) : 0.0;
    const metadata = data.metadata || {};
    const chunkIds = Array.isArray(data.chunk_ids) ? data.chunk_ids : undefined;
    let timestamp: string | undefined;
    if (data.timestamp) {
      if (typeof data.timestamp === 'string') {
        timestamp = data.timestamp;
      } else if (data.timestamp instanceof Date) {
        timestamp = data.timestamp.toISOString();
      } else {
        const parsed = new Date(data.timestamp);
        if (!Number.isNaN(parsed.valueOf())) {
          timestamp = parsed.toISOString();
        }
      }
    }

    const displayName = typeof data.display_name === 'string' ? data.display_name : undefined;
    const sourceRole = typeof data.source_role === 'string' ? data.source_role : undefined;
    const engramId = data.engram_id ? String(data.engram_id) : undefined;
    const ownerId = data.owner_id ? String(data.owner_id) : undefined;

    let entity: GraphEntityResult | undefined;
    let rel: GraphRelationshipResult | undefined;
    let comm: GraphCommunityResult | undefined;

    if (rtype === GraphSearchResultType.ENTITY) {
      entity = {
        id: content.id ? String(content.id) : undefined,
        name: content.name || '',
        description: content.description || '',
        metadata: content.metadata || {},
      };
    } else if (rtype === GraphSearchResultType.RELATIONSHIP) {
      rel = {
        id: content.id ? String(content.id) : undefined,
        subject: content.subject || '',
        predicate: content.predicate || '',
        object: content.object || '',
        subject_id: content.subject_id ? String(content.subject_id) : undefined,
        object_id: content.object_id ? String(content.object_id) : undefined,
        description: content.description,
        metadata: content.metadata || {},
      };
    } else {
      comm = {
        id: content.id ? String(content.id) : undefined,
        name: content.name || '',
        summary: content.summary || '',
        metadata: content.metadata || {},
      };
    }

    return {
      id: rid,
      score,
      metadata,
      source: 'graph',
      content: undefined,
      graph_result_type: rtype,
      graph_entity: entity,
      graph_relationship: rel,
      graph_community: comm,
      chunk_ids: chunkIds,
      timestamp,
      display_name: displayName,
      source_role: sourceRole,
      engram_id: engramId,
      owner_id: ownerId,
    } as SearchResult;
  }

  private async _sha256(message: string): Promise<string> {
    const msgBuffer = new TextEncoder().encode(message);
    // Use Web Crypto API: prefer globalThis.crypto (browser/Node 18+), fallback to Node's crypto.webcrypto
    let crypto: Crypto;
    if (typeof globalThis.crypto !== 'undefined' && globalThis.crypto.subtle) {
      crypto = globalThis.crypto;
    } else {
      // Node.js environment: use built-in crypto module's webcrypto
      const nodeCrypto = await import('crypto');
      crypto = nodeCrypto.webcrypto as Crypto;
    }
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  }

  private _formDataFromObject(obj: Record<string, unknown>): FormData {
    const formData = new FormData();
    Object.entries(obj).forEach(([key, value]) => {
      formData.append(key, value as string | Blob);
    });
    return formData;
  }

  /**
   * Convert and process multimodal content parts, auto-uploading large base64 files to S3.
   *
   * - Strings/unknown values are wrapped as `{ type: 'text', text: '...' }`
   * - Binary parts (`image`/`audio`/`document` with `data`) larger than 5MB are uploaded to S3 and converted to `s3_ref`.
   */
  private async _processContentParts(contentParts: unknown[]): Promise<unknown[]> {
    const processed: unknown[] = [];

    for (const part of contentParts) {
      // Wrap primitive parts as text blocks
      if (!part || typeof part !== 'object' || !('type' in (part as Record<string, unknown>))) {
        processed.push({ type: 'text', text: String(part) });
        continue;
      }

      const partRecord = part as Record<string, unknown>;
      const partType = partRecord.type as string;

      // Check if this is a binary content part with base64 data
      if (['image', 'audio', 'document'].includes(partType) && partRecord.data) {
        // Calculate decoded size (base64 is ~4/3 of original)
        const dataSize = Math.floor(String(partRecord.data).length * 3 / 4);

        if (dataSize > Nebula.MAX_INLINE_SIZE) {
          const filename = (partRecord.filename as string) || `file.${partType}`;
          const mediaType = (partRecord.media_type as string) || 'application/octet-stream';

          const uploadInfo = await this.getUploadUrl({
            filename,
            content_type: mediaType,
            file_size: dataSize,
          });

          // Decode base64 and upload to S3
          let bytes: Uint8Array;
          const globalThisRecord = globalThis as Record<string, unknown>;
          if (typeof globalThisRecord.atob === 'function') {
            const binaryString = (globalThisRecord.atob as (data: string) => string)(String(partRecord.data));
            bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
          } else {
            // Node.js fallback
            const { Buffer } = await import('buffer');
            bytes = Uint8Array.from(Buffer.from(String(partRecord.data), 'base64'));
          }

          await fetch(uploadInfo.upload_url, {
            method: 'PUT',
            body: bytes,
            headers: { 'Content-Type': mediaType },
          });

          processed.push({
            type: 's3_ref',
            s3_key: uploadInfo.s3_key,
            media_type: mediaType,
            filename,
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
  async getUploadUrl(options: {
    filename: string;
    content_type: string;
    file_size: number;
  }): Promise<{ upload_url: string; s3_key: string; bucket: string; expires_in: number }> {
    const response = await this._makeRequest('POST', '/v1/memories/upload', undefined, {
      filename: options.filename,
      content_type: options.content_type,
      file_size: options.file_size,
    }) as { results?: { upload_url: string; s3_key: string; bucket: string; expires_in: number }; upload_url?: string; s3_key?: string; bucket?: string; expires_in?: number };

    if (response.results) {
      return response.results;
    }
    return response as { upload_url: string; s3_key: string; bucket: string; expires_in: number };
  }
}
