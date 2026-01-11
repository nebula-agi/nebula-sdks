// Data models matching the actual Nebula Python SDK exactly

// Enums
export enum GraphSearchResultType {
  ENTITY = "entity",
  RELATIONSHIP = "relationship",
  COMMUNITY = "community"
}

// Core interfaces matching Python SDK exactly
export interface Chunk {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
  role?: string; // For conversation messages
}

/**
 * Structured chunk format returned by backend for conversation messages.
 * Contains message text and role metadata inline.
 */
export interface StructuredChunk {
  text: string;
  role: 'user' | 'assistant' | 'system';
}



// Multimodal content part types
export interface TextContentPart {
  type: 'text';
  text: string;
}

export interface FileContentPart {
  type?: 'image' | 'audio' | 'document' | 'file';
  data: string; // Base64 encoded data
  media_type: string; // MIME type
  filename?: string;
  duration_seconds?: number; // Specific to audio
}

export interface S3FileReferencePart {
  type: 's3_ref';
  s3_key: string;
  bucket?: string;
  media_type: string;
  filename?: string;
  size_bytes?: number;
}

export type MultimodalContentPart =
  | TextContentPart
  | FileContentPart
  | S3FileReferencePart;

export interface Memory {
  collection_id?: string;
  content?: string | string[] | MultimodalContentPart[] | Array<{ content: string | MultimodalContentPart[]; role: string; metadata?: Record<string, unknown>; authority?: number }>;
  role?: string; // user, assistant, or custom
  id?: string; // Memory/Engram UUID
  memory_id?: string; // Alias for id, for backward compatibility
  metadata: Record<string, unknown>;
  authority?: number; // Optional authority score (0.0 - 1.0)

  // Read-only fields (populated from server response)
  chunks?: Chunk[];
  collection_ids?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface Collection {
  id: string;
  name: string;
  description?: string;
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
  memory_count: number;
  owner_id?: string;
}

export interface SearchResult {
  id: string; // chunk_id
  score: number;
  metadata: Record<string, unknown>;
  source?: string;
  timestamp?: string;
  display_name?: string;
  source_role?: string;
  memory_id?: string; // Parent memory/conversation container
  owner_id?: string;
  engram_id?: string; // Engram ID for graph results

  // Chunk fields
  content?: string;

  // Graph variant discriminator and payload
  graph_result_type?: GraphSearchResultType;
  graph_entity?: GraphEntityResult;
  graph_relationship?: GraphRelationshipResult;
  graph_community?: GraphCommunityResult;
  chunk_ids?: string[];
}

export interface GraphEntityResult {
  id?: string;
  name: string;
  description: string;
  metadata: Record<string, unknown>;
}

export interface GraphRelationshipResult {
  id?: string;
  subject: string;
  predicate: string;
  object: string;
  subject_id?: string;
  object_id?: string;
  description?: string;
  metadata: Record<string, unknown>;
}

export interface GraphCommunityResult {
  id?: string;
  name: string;
  summary: string;
  metadata: Record<string, unknown>;
}

export interface SearchOptions {
  limit: number;
  filters?: Record<string, unknown>;
  search_mode?: 'fast' | 'super';
}

// Hierarchical Memory Recall types (matches backend MemoryRecall structure)
export interface RecallFocus {
  schema_weight: number;
  fact_weight: number;
  episodic_weight: number;
}

export interface ActivatedEntity {
  entity_id: string;
  entity_name: string;
  entity_category?: string;
  activation_score: number;
  activation_reason?: string;
  profile?: any;
  facets?: ActivatedFacet[];
}

export interface ActivatedFacet {
  facet_id: string;
  facet_name: string;
  relevance_score: number;
  facts: ActivatedFact[];
  coherence_score?: number;
  is_noise: boolean;
}

export interface ActivatedFact {
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

export interface GroundedUtterance {
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

export interface MemoryResponse {
  query: string;
  entities: ActivatedEntity[];
  facts: ActivatedFact[];
  utterances: GroundedUtterance[];
  focus?: RecallFocus;
  fact_to_chunks: Record<string, string[]>;
  entity_to_facts: Record<string, string[]>;
  retrieved_at: string;
  total_traversal_time_ms?: number;
  query_intent?: string;
}

// Configuration interface
export interface NebulaClientConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

// Error types matching Python SDK
export class NebulaException extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'NebulaException';
  }
}

export class NebulaClientException extends NebulaException {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'NebulaClientException';
  }
}

export class NebulaAuthenticationException extends NebulaException {
  constructor(message: string = 'Invalid API key') {
    super(message, 401);
    this.name = 'NebulaAuthenticationException';
  }
}

export class NebulaRateLimitException extends NebulaException {
  constructor(message: string = 'Rate limit exceeded') {
    super(message, 429);
    this.name = 'NebulaRateLimitException';
  }
}

export class NebulaValidationException extends NebulaException {
  constructor(message: string = 'Validation error', public details?: unknown) {
    super(message, 400);
    this.name = 'NebulaValidationException';
  }
}

export class NebulaCollectionNotFoundException extends NebulaException {
  constructor(message: string = 'Collection not found') {
    super(message, 404);
    this.name = 'NebulaCollectionNotFoundException';
  }
}

export class NebulaNotFoundException extends NebulaException {
  constructor(resourceId: string, resourceType: string = 'Resource') {
    super(`${resourceType} not found: ${resourceId}`, 404);
    this.name = 'NebulaNotFoundException';
  }
}
