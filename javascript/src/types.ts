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

export interface Memory {
  collection_id: string;
  content: string | string[] | Array<{content: string; role: string; metadata?: Record<string, any>; authority?: number}>;
  role?: string; // user, assistant, or custom
  memory_id?: string; // ID of existing memory to append to
  metadata: Record<string, any>;
  authority?: number; // Optional authority score (0.0 - 1.0)
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
