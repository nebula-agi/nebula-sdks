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
  metadata: Record<string, any>;
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


export interface MemoryResponse {
  id: string;
  content?: string;
  chunks?: Chunk[];
  metadata: Record<string, any>;
  collection_ids: string[];
  created_at?: string;
  updated_at?: string;
}

// Multimodal content part types
export interface TextContentPart {
  type: 'text';
  text: string;
}

export interface ImageContentPart {
  type: 'image';
  data: string;  // Base64 encoded image data
  media_type: string;  // MIME type (e.g., 'image/jpeg', 'image/png')
  filename?: string;
}

export interface AudioContentPart {
  type: 'audio';
  data: string;  // Base64 encoded audio data
  media_type: string;  // MIME type (e.g., 'audio/mp3', 'audio/wav', 'audio/m4a')
  filename?: string;
  duration_seconds?: number;
}

export interface DocumentContentPart {
  type: 'document';
  data: string;  // Base64 encoded document data
  media_type: string;  // MIME type (e.g., 'application/pdf', 'application/msword')
  filename?: string;
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
  | ImageContentPart 
  | AudioContentPart 
  | DocumentContentPart 
  | S3FileReferencePart;

export interface Memory {
  collection_id: string;
  content: string | string[] | MultimodalContentPart[] | Array<{content: string | MultimodalContentPart[]; role: string; metadata?: Record<string, any>; authority?: number}>;
  role?: string; // user, assistant, or custom
  memory_id?: string; // ID of existing memory to append to
  metadata: Record<string, any>;
  authority?: number; // Optional authority score (0.0 - 1.0)
  vision_model?: string; // Optional vision model for multimodal processing
  audio_model?: string; // Optional audio transcription model
  fast_mode?: boolean; // Use fast text extraction for PDFs (default: false, uses VLM OCR)
}

export interface Collection {
  id: string;
  name: string;
  description?: string;
  metadata: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  memory_count: number;
  owner_id?: string;
}

export interface SearchResult {
  id: string; // chunk_id
  score: number;
  metadata: Record<string, any>;
  source?: string;
  timestamp?: string;
  display_name?: string;
  source_role?: string;
  memory_id?: string; // Parent memory/conversation container
  owner_id?: string;

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
  metadata: Record<string, any>;
}

export interface GraphRelationshipResult {
  id?: string;
  subject: string;
  predicate: string;
  object: string;
  subject_id?: string;
  object_id?: string;
  description?: string;
  metadata: Record<string, any>;
}

export interface GraphCommunityResult {
  id?: string;
  name: string;
  summary: string;
  metadata: Record<string, any>;
}

export interface AgentResponse {
  content: string;
  agent_id: string;
  conversation_id?: string;
  metadata: Record<string, any>;
  citations: Record<string, any>[];
}

export interface SearchOptions {
  limit: number;
  filters?: Record<string, any>;
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
  traversal_depth: number;
  profile?: Record<string, any>;
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
  speaker_name?: string;
  source_role?: string;
  timestamp?: string;
  display_name?: string;
  supporting_fact_ids: string[];
  metadata?: Record<string, any>;
}

export interface MemoryRecall {
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
    public details?: any
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
  constructor(message: string = 'Validation error', public details?: any) {
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
