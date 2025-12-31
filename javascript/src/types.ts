// Data models matching the actual Nebula Python SDK exactly

// Extension to media type mappings for common types
const IMAGE_EXTENSIONS: Record<string, string> = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.bmp': 'image/bmp',
  '.svg': 'image/svg+xml',
};

const AUDIO_EXTENSIONS: Record<string, string> = {
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
  '.m4a': 'audio/mp4',
  '.ogg': 'audio/ogg',
  '.flac': 'audio/flac',
  '.aac': 'audio/aac',
  '.webm': 'audio/webm',
};

const DOCUMENT_EXTENSIONS: Record<string, string> = {
  '.pdf': 'application/pdf',
  '.doc': 'application/msword',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.txt': 'text/plain',
  '.csv': 'text/csv',
  '.rtf': 'application/rtf',
  '.md': 'text/markdown',
  '.json': 'application/json',
};

/**
 * Detect content type (image, audio, document) from filename.
 */
function detectContentType(filename: string): 'image' | 'audio' | 'document' | 'unknown' {
  const ext = filename.toLowerCase().match(/\.[^.]+$/)?.[0] || '';
  
  if (ext in IMAGE_EXTENSIONS) return 'image';
  if (ext in AUDIO_EXTENSIONS) return 'audio';
  if (ext in DOCUMENT_EXTENSIONS) return 'document';
  
  return 'unknown';
}

/**
 * Get the file extension from a filename.
 */
function getExtension(filename: string): string {
  return filename.toLowerCase().match(/\.[^.]+$/)?.[0] || '';
}

/**
 * Load a file and automatically detect its type (image, audio, or document).
 * 
 * Works in both Node.js and browser environments:
 * - Node.js: Pass a file path string
 * - Browser: Pass a File object from input/drag-drop
 * 
 * @param source - File path (Node.js) or File object (browser)
 * @returns Promise resolving to ImageContentPart, AudioContentPart, or DocumentContentPart
 * 
 * @example
 * // Node.js
 * import { loadFile, Memory } from '@nebula-ai/sdk';
 * 
 * const memory = {
 *   collection_id: "my-collection",
 *   content: [
 *     await loadFile("photo.jpg"),      // Auto-detected as image
 *     await loadFile("recording.mp3"),  // Auto-detected as audio
 *     await loadFile("report.pdf"),     // Auto-detected as document
 *   ]
 * };
 * 
 * @example
 * // Browser
 * const fileInput = document.querySelector('input[type="file"]');
 * const file = fileInput.files[0];
 * const content = await loadFile(file);
 */
export async function loadFile(
  source: string | File
): Promise<ImageContentPart | AudioContentPart | DocumentContentPart> {
  let data: string;
  let filename: string;
  
  if (typeof source === 'string') {
    // Node.js: Read file from path
    // Dynamic import to avoid bundling fs in browser builds
    const fs = await import('fs').catch(() => null);
    const path = await import('path').catch(() => null);
    
    if (!fs || !path) {
      throw new Error('loadFile with file path is only supported in Node.js. In browser, pass a File object.');
    }
    
    const buffer = fs.readFileSync(source);
    data = buffer.toString('base64');
    filename = path.basename(source);
  } else {
    // Browser: Read File object
    filename = source.name;
    const buffer = await source.arrayBuffer();
    data = btoa(String.fromCharCode(...new Uint8Array(buffer)));
  }
  
  const contentType = detectContentType(filename);
  const ext = getExtension(filename);
  
  if (contentType === 'image') {
    const mediaType = IMAGE_EXTENSIONS[ext] || 'image/jpeg';
    return {
      type: 'image',
      data,
      media_type: mediaType,
      filename,
    };
  }
  
  if (contentType === 'audio') {
    const mediaType = AUDIO_EXTENSIONS[ext] || 'audio/mpeg';
    return {
      type: 'audio',
      data,
      media_type: mediaType,
      filename,
    };
  }
  
  if (contentType === 'document') {
    const mediaType = DOCUMENT_EXTENSIONS[ext] || 'application/pdf';
    return {
      type: 'document',
      data,
      media_type: mediaType,
      filename,
    };
  }
  
  const supported = [
    ...Object.keys(IMAGE_EXTENSIONS),
    ...Object.keys(AUDIO_EXTENSIONS),
    ...Object.keys(DOCUMENT_EXTENSIONS),
  ].join(', ');
  
  throw new Error(
    `Cannot detect file type for '${filename}'. Supported extensions: ${supported}`
  );
}

/**
 * Load raw bytes and create content with auto-detected type.
 * 
 * @param data - Raw bytes as Uint8Array, ArrayBuffer, or Buffer
 * @param filename - Filename used to detect the content type
 * @returns ImageContentPart, AudioContentPart, or DocumentContentPart
 * 
 * @example
 * const bytes = new Uint8Array([...]);
 * const content = loadBytes(bytes, "photo.jpg");
 */
export function loadBytes(
  data: Uint8Array | ArrayBuffer | Buffer,
  filename: string
): ImageContentPart | AudioContentPart | DocumentContentPart {
  // Convert to base64
  let bytes: Uint8Array;
  if (data instanceof ArrayBuffer) {
    bytes = new Uint8Array(data);
  } else if (Buffer && Buffer.isBuffer(data)) {
    bytes = new Uint8Array(data);
  } else {
    bytes = data as Uint8Array;
  }
  
  const base64 = typeof Buffer !== 'undefined'
    ? Buffer.from(bytes).toString('base64')
    : btoa(String.fromCharCode(...bytes));
  
  const contentType = detectContentType(filename);
  const ext = getExtension(filename);
  
  if (contentType === 'image') {
    return {
      type: 'image',
      data: base64,
      media_type: IMAGE_EXTENSIONS[ext] || 'image/jpeg',
      filename,
    };
  }
  
  if (contentType === 'audio') {
    return {
      type: 'audio',
      data: base64,
      media_type: AUDIO_EXTENSIONS[ext] || 'audio/mpeg',
      filename,
    };
  }
  
  if (contentType === 'document') {
    return {
      type: 'document',
      data: base64,
      media_type: DOCUMENT_EXTENSIONS[ext] || 'application/pdf',
      filename,
    };
  }
  
  throw new Error(`Cannot detect file type for '${filename}'.`);
}

/**
 * Download a file from URL and create content with auto-detected type.
 * 
 * @param url - URL to download from
 * @param filename - Optional filename (extracted from URL if not provided)
 * @returns Promise resolving to ImageContentPart (currently only images supported via URL)
 * 
 * @example
 * import { loadUrl, Memory } from '@nebula-ai/sdk';
 * 
 * const memory = {
 *   collection_id: "my-collection",
 *   content: [
 *     await loadUrl("https://example.com/photo.jpg"),
 *     "What's in this image?"
 *   ]
 * };
 */
export async function loadUrl(
  url: string,
  filename?: string
): Promise<ImageContentPart> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download from URL: ${response.status} ${response.statusText}`);
  }
  
  const buffer = await response.arrayBuffer();
  const data = typeof Buffer !== 'undefined'
    ? Buffer.from(buffer).toString('base64')
    : btoa(String.fromCharCode(...new Uint8Array(buffer)));
  
  // Extract filename from URL if not provided
  if (!filename) {
    try {
      const urlPath = new URL(url).pathname;
      filename = urlPath.split('/').pop() || 'downloaded_file';
    } catch {
      filename = 'downloaded_file';
    }
  }
  
  // Detect media type from content-type header or filename
  const contentTypeHeader = response.headers.get('content-type')?.split(';')[0].trim() || '';
  
  let mediaType = 'image/jpeg';
  if (contentTypeHeader.startsWith('image/')) {
    mediaType = contentTypeHeader;
  } else if (filename) {
    const ext = getExtension(filename);
    if (ext in IMAGE_EXTENSIONS) {
      mediaType = IMAGE_EXTENSIONS[ext];
    }
  }
  
  return {
    type: 'image',
    data,
    media_type: mediaType,
    filename,
  };
}

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
