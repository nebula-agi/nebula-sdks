declare enum GraphSearchResultType {
    ENTITY = "entity",
    RELATIONSHIP = "relationship",
    COMMUNITY = "community"
}
interface Chunk {
    id: string;
    content: string;
    metadata: Record<string, unknown>;
    role?: string;
}
/**
 * Structured chunk format returned by backend for conversation messages.
 * Contains message text and role metadata inline.
 */
interface StructuredChunk {
    text: string;
    role: 'user' | 'assistant' | 'system';
}
interface TextContentPart {
    type: 'text';
    text: string;
}
interface FileContentPart {
    type?: 'image' | 'audio' | 'document' | 'file';
    data: string;
    media_type: string;
    filename?: string;
    duration_seconds?: number;
}
interface S3FileReferencePart {
    type: 's3_ref';
    s3_key: string;
    bucket?: string;
    media_type: string;
    filename?: string;
    size_bytes?: number;
}
type MultimodalContentPart = TextContentPart | FileContentPart | S3FileReferencePart;
interface Memory$1 {
    collection_id?: string;
    content?: string | string[] | MultimodalContentPart[] | Array<{
        content: string | MultimodalContentPart[];
        role: string;
        metadata?: Record<string, unknown>;
        authority?: number;
    }>;
    role?: string;
    id?: string;
    memory_id?: string;
    metadata: Record<string, unknown>;
    authority?: number;
    chunks?: Chunk[];
    collection_ids?: string[];
    created_at?: string;
    updated_at?: string;
}
interface Collection {
    id: string;
    name: string;
    description?: string;
    metadata: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
    memory_count: number;
    owner_id?: string;
}
interface SearchResult {
    id: string;
    score: number;
    metadata: Record<string, unknown>;
    source?: string;
    timestamp?: string;
    display_name?: string;
    source_role?: string;
    memory_id?: string;
    owner_id?: string;
    engram_id?: string;
    content?: string;
    graph_result_type?: GraphSearchResultType;
    graph_entity?: GraphEntityResult;
    graph_relationship?: GraphRelationshipResult;
    graph_community?: GraphCommunityResult;
    chunk_ids?: string[];
}
interface GraphEntityResult {
    id?: string;
    name: string;
    description: string;
    metadata: Record<string, unknown>;
}
interface GraphRelationshipResult {
    id?: string;
    subject: string;
    predicate: string;
    object: string;
    subject_id?: string;
    object_id?: string;
    description?: string;
    metadata: Record<string, unknown>;
}
interface GraphCommunityResult {
    id?: string;
    name: string;
    summary: string;
    metadata: Record<string, unknown>;
}
interface SearchOptions {
    limit: number;
    filters?: Record<string, unknown>;
    search_mode?: 'fast' | 'super';
}
interface RecallFocus {
    schema_weight: number;
    fact_weight: number;
    episodic_weight: number;
}
interface ActivatedEntity {
    entity_id: string;
    entity_name: string;
    entity_category?: string;
    activation_score: number;
    activation_reason?: string;
    profile?: any;
    facets?: ActivatedFacet[];
}
interface ActivatedFacet {
    facet_id: string;
    facet_name: string;
    relevance_score: number;
    facts: ActivatedFact[];
    coherence_score?: number;
    is_noise: boolean;
}
interface ActivatedFact {
    fact_id: string;
    entity_id?: string;
    entity_name?: string;
    facet_name?: string;
    subject: string;
    predicate: string;
    object_value: string;
    activation_score: number;
    extraction_confidence: number;
    corroboration_count: number;
    source_chunk_ids: string[];
}
interface GroundedUtterance {
    chunk_id: string;
    text: string;
    activation_score: number;
    timestamp?: string;
    source_role?: string;
    speaker_name?: string;
    display_name?: string;
    engram_id?: string;
    owner_id?: string;
    supporting_fact_ids: string[];
    metadata?: Record<string, unknown>;
}
interface InferenceHint {
    term: string;
    predicate: string;
    object: string;
    inferred?: boolean;
    confidence?: number;
    ledger_p_use?: number;
    ledger_p_true?: number;
    ledger_p_stable?: number;
    usable_for_rewrite?: boolean;
    used_for_rewrite?: boolean;
    relationship_id?: string;
    subject_id?: string;
    object_id?: string;
    metadata?: Record<string, unknown>;
    inference_metadata?: Record<string, unknown>;
}
interface MemoryResponse {
    query: string;
    entities: ActivatedEntity[];
    facts: ActivatedFact[];
    utterances: GroundedUtterance[];
    inference_hints?: InferenceHint[];
    focus?: RecallFocus;
    fact_to_chunks: Record<string, string[]>;
    entity_to_facts: Record<string, string[]>;
    retrieved_at: string;
    total_traversal_time_ms?: number;
    query_intent?: string;
}
interface NebulaClientConfig {
    apiKey: string;
    baseUrl?: string;
    timeout?: number;
}
declare class NebulaException extends Error {
    statusCode?: number | undefined;
    details?: unknown | undefined;
    constructor(message: string, statusCode?: number | undefined, details?: unknown | undefined);
}
declare class NebulaClientException extends NebulaException {
    cause?: Error | undefined;
    constructor(message: string, cause?: Error | undefined);
}
declare class NebulaAuthenticationException extends NebulaException {
    constructor(message?: string);
}
declare class NebulaRateLimitException extends NebulaException {
    constructor(message?: string);
}
declare class NebulaValidationException extends NebulaException {
    details?: unknown | undefined;
    constructor(message?: string, details?: unknown | undefined);
}
declare class NebulaCollectionNotFoundException extends NebulaException {
    constructor(message?: string);
}
declare class NebulaNotFoundException extends NebulaException {
    constructor(resourceId: string, resourceType?: string);
}

/**
 * Official Nebula JavaScript/TypeScript SDK
 * Mirrors the exact Nebula Python SDK client.py implementation
 */
declare class Nebula {
    private apiKey;
    private baseUrl;
    private timeout;
    private static readonly MAX_INLINE_SIZE;
    constructor(config?: NebulaClientConfig);
    setApiKey(next: string): void;
    setBaseUrl(next: string): void;
    setCorsProxy(_next: string): void;
    /** Check if API key is set */
    isApiKeySet(): boolean;
    /** Detect if a token looks like a Nebula API key (public.raw) */
    private _isNebulaApiKey;
    /** Build authentication headers */
    private _buildAuthHeaders;
    private _isRecord;
    private _unwrapResults;
    private _unwrapResultsArray;
    private _looksLikeMultimodalContent;
    private _normalizeContentParts;
    private _serializeContentAsText;
    private _serializeContentAsParts;
    /** Make an HTTP request to the Nebula API */
    private _makeRequest;
    /** Create a new collection */
    createCollection(options: {
        name: string;
        description?: string;
        metadata?: Record<string, unknown>;
    }): Promise<Collection>;
    /** Get a specific collection by ID */
    getCollection(collectionId: string): Promise<Collection>;
    /** Get a specific collection by name */
    getCollectionByName(name: string): Promise<Collection>;
    /** Get all collections */
    listCollections(options?: {
        limit?: number;
        offset?: number;
        name?: string;
    }): Promise<Collection[]>;
    /** Update a collection */
    updateCollection(options: {
        collectionId: string;
        name?: string;
        description?: string;
        metadata?: Record<string, unknown>;
    }): Promise<Collection>;
    /** Delete a collection */
    deleteCollection(collectionId: string): Promise<boolean>;
    /**
     * Legacy convenience: store raw text content into a collection as a document
     */
    store(content: string, collectionId: string, metadata?: Record<string, unknown>): Promise<Memory$1>;
    /**
     * Store a single memory using the unified engrams API.
     *
     * Automatically infers memory type:
     * - If role is present, creates a conversation
     * - Otherwise, creates a document
     */
    storeMemory(memory: Memory$1 | Record<string, unknown>, name?: string): Promise<string>;
    /**
     * Internal method to append content to an existing memory
     *
     * @throws NebulaNotFoundException if memory_id doesn't exist
     */
    private _appendToMemory;
    /** Store multiple memories using the unified engrams API */
    storeMemories(memories: Memory$1[]): Promise<string[]>;
    /** Delete one or more memories */
    delete(memoryIds: string | string[]): Promise<boolean | {
        message: string;
        results: {
            successful: string[];
            failed: Array<{
                id: string;
                error: string;
            }>;
            summary: {
                total: number;
                succeeded: number;
                failed: number;
            };
        };
    }>;
    /** Delete a specific chunk or message within a memory */
    deleteChunk(chunkId: string): Promise<boolean>;
    /** Update a specific chunk or message within a memory */
    updateChunk(chunkId: string, content: string, metadata?: Record<string, unknown>): Promise<boolean>;
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
    updateMemory(options: {
        memoryId: string;
        name?: string;
        metadata?: Record<string, unknown>;
        collectionIds?: string[];
        mergeMetadata?: boolean;
    }): Promise<boolean>;
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
    listMemories(options: {
        collection_ids: string | string[];
        limit?: number;
        offset?: number;
        metadata_filters?: Record<string, unknown>;
    }): Promise<Memory$1[]>;
    /** Get a specific memory by engram ID */
    getMemory(memoryId: string): Promise<Memory$1>;
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
    search(options: {
        query: string;
        collection_ids?: string | string[];
        effort?: 'auto' | 'low' | 'medium' | 'high';
        filters?: Record<string, unknown>;
        searchSettings?: Record<string, unknown>;
    }): Promise<MemoryResponse>;
    healthCheck(): Promise<Record<string, unknown>>;
    private _collectionFromDict;
    private _memoryResponseFromDict;
    private _searchResultFromDict;
    private _searchResultFromGraphDict;
    private _sha256;
    private _formDataFromObject;
    /**
     * Convert and process multimodal content parts, auto-uploading large base64 files to S3.
     *
     * - Binary parts (`image`/`audio`/`document` with `data`) larger than 5MB are uploaded to S3 and converted to `s3_ref`.
     */
    private _processContentParts;
    /**
     * Get a presigned URL for uploading large files to S3.
     */
    getUploadUrl(options: {
        filename: string;
        content_type: string;
        file_size: number;
    }): Promise<{
        upload_url: string;
        s3_key: string;
        bucket: string;
        expires_in: number;
    }>;
}

/**
 * Utility for creating multimodal content from files.
 * Note: These methods only work in Node.js environments.
 */
declare class NebulaContent {
    /**
     * Create a FileContentPart from a file path.
     * Automatically deduces media_type and the backend 'type' (image, audio, document).
     */
    static fromFile(filePath: string, mediaType?: string): Promise<FileContentPart>;
}

type MemoryFactory = {
    (data: Memory$1): Memory$1;
    File: typeof NebulaContent.fromFile;
    fromFile: (filePath: string, collection_id: string, metadata?: Record<string, unknown>, role?: string) => Promise<Memory$1>;
};
declare const Memory: MemoryFactory;
type Memory = Memory$1;

export { type ActivatedEntity, type ActivatedFacet, type ActivatedFact, type Chunk, type Collection, type FileContentPart, type GraphCommunityResult, type GraphEntityResult, type GraphRelationshipResult, GraphSearchResultType, type GroundedUtterance, Memory, type MemoryResponse, type MultimodalContentPart, Nebula, NebulaAuthenticationException, type NebulaClientConfig, NebulaClientException, NebulaCollectionNotFoundException, NebulaContent, NebulaException, NebulaNotFoundException, NebulaRateLimitException, NebulaValidationException, type RecallFocus, type S3FileReferencePart, type SearchOptions, type SearchResult, type StructuredChunk, type TextContentPart, Nebula as default };
