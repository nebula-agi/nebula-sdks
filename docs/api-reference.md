# Nebula SDK API Reference

Complete API reference for both JavaScript and Python SDKs.

## Table of Contents

- [Client Initialization](#client-initialization)
- [Collections](#collections)
- [Memories](#memories)
- [Search](#search)
- [Graph Queries](#graph-queries)
- [Error Handling](#error-handling)

---

## Client Initialization

### JavaScript/TypeScript

```typescript
import Nebula from '@nebula-ai/sdk';

const client = new Nebula({
  apiKey: 'your-api-key',        // Required
  baseUrl: 'https://api.nebulacloud.app',  // Optional
  timeout: 30000                  // Optional, in milliseconds
});
```

### Python

```python
from nebula import Nebula

client = Nebula(
    api_key='your-api-key',        # Required
    base_url='https://api.nebulacloud.app',  # Optional
    timeout=30.0                    # Optional, in seconds
)
```

**Parameters:**
- `apiKey` / `api_key` (string, required): Your Nebula API key
- `baseUrl` / `base_url` (string, optional): API base URL, defaults to production
- `timeout` (number, optional): Request timeout

---

## Collections

Collections are containers for organizing related memories.

### Create Collection

**JavaScript:**
```typescript
const collection = await client.createCollection({
  name: string,
  description?: string,
  metadata?: Record<string, any>
});
```

**Python:**
```python
collection = client.create_collection(
    name: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Returns:** `Collection` object with `id`, `name`, `description`, `metadata`

### Get Collection

**JavaScript:**
```typescript
const collection = await client.getCollection(collectionId: string);
```

**Python:**
```python
collection = client.get_collection(collection_id: str)
```

### List Collections

**JavaScript:**
```typescript
const collections = await client.listCollections({
  limit?: number,
  offset?: number
});
```

**Python:**
```python
collections = client.list_collections(
    limit: Optional[int] = None,
    offset: Optional[int] = None
)
```

### Update Collection

**JavaScript:**
```typescript
const collection = await client.updateCollection({
  collectionId: string,
  name?: string,
  description?: string,
  metadata?: Record<string, any>
});
```

**Python:**
```python
collection = client.update_collection(
    collection_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

### Delete Collection

**JavaScript:**
```typescript
await client.deleteCollection(collectionId: string);
```

**Python:**
```python
client.delete_collection(collection_id: str)
```

---

## Memories

Memories are individual pieces of content stored within collections.

### Add Memory

**JavaScript:**
```typescript
const memory = await client.addMemory({
  collectionId: string,
  content: string,
  metadata?: Record<string, any>
});
```

**Python:**
```python
memory = client.add_memory(
    collection_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
)
```

### Get Memory

**JavaScript:**
```typescript
const memory = await client.getMemory(memoryId: string);
```

**Python:**
```python
memory = client.get_memory(memory_id: str)
```

### List Memories

**JavaScript:**
```typescript
const memories = await client.listMemories({
  collectionId: string,
  limit?: number,
  offset?: number
});
```

**Python:**
```python
memories = client.list_memories(
    collection_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
)
```

### Update Memory

**JavaScript:**
```typescript
const memory = await client.updateMemory({
  memoryId: string,
  content?: string,
  metadata?: Record<string, any>
});
```

**Python:**
```python
memory = client.update_memory(
    memory_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

### Delete Memory

**JavaScript:**
```typescript
await client.deleteMemory(memoryId: string);
```

**Python:**
```python
client.delete_memory(memory_id: str)
```

---

## Search

Perform semantic search across your memories.

### Basic Search

**JavaScript:**
```typescript
const results = await client.search({
  collectionId: string,
  query: string,
  limit?: number,
  offset?: number,
  filters?: Record<string, any>
});
```

**Python:**
```python
results = client.search(
    collection_id: str,
    query: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None
)
```

**Returns:** `SearchResult` object with:
- `results`: Array of matching memories with scores
- `total`: Total number of results
- `offset`: Current offset
- `limit`: Current limit

---

## Graph Queries

Query the knowledge graph built from your memories.

### Entity Search

**JavaScript:**
```typescript
const entities = await client.graphEntitySearch({
  collectionId: string,
  query: string,
  limit?: number
});
```

**Python:**
```python
entities = client.graph_entity_search(
    collection_id: str,
    query: str,
    limit: Optional[int] = None
)
```

### Relationship Search

**JavaScript:**
```typescript
const relationships = await client.graphRelationshipSearch({
  collectionId: string,
  query: string,
  limit?: number
});
```

**Python:**
```python
relationships = client.graph_relationship_search(
    collection_id: str,
    query: str,
    limit: Optional[int] = None
)
```

---

## Error Handling

Both SDKs provide typed exceptions for different error scenarios.

### Exception Types

- `NebulaException`: Base exception class
- `NebulaClientException`: Client-side errors (invalid input, etc.)
- `NebulaAuthenticationException`: Authentication failures (HTTP 401)
- `NebulaRateLimitException`: Rate limit exceeded (HTTP 429)
- `NebulaValidationException`: Validation errors (HTTP 400)
- `NebulaNotFoundException`: Resource not found (HTTP 404)

### JavaScript Error Handling

```typescript
import Nebula, { NebulaAuthenticationException, NebulaNotFoundException } from '@nebula-ai/sdk';

try {
  const collection = await client.getCollection('non-existent-id');
} catch (error) {
  if (error instanceof NebulaAuthenticationException) {
    console.error('Invalid API key');
  } else if (error instanceof NebulaNotFoundException) {
    console.error('Collection not found');
  } else {
    console.error('Unknown error:', error);
  }
}
```

### Python Error Handling

```python
from nebula.exceptions import (
    NebulaAuthenticationException,
    NebulaNotFoundException
)

try:
    collection = client.get_collection('non-existent-id')
except NebulaAuthenticationException:
    print('Invalid API key')
except NebulaNotFoundException:
    print('Collection not found')
except Exception as e:
    print(f'Unknown error: {e}')
```

---

## Async Support

### JavaScript

All methods are async by default and return Promises.

### Python Async Client

```python
from nebula import AsyncNebula
import asyncio

async def main():
    async with AsyncNebula(api_key='your-key') as client:
        collection = await client.create_collection(name='Async Collection')
        memories = await client.list_memories(collection_id=collection.id)

asyncio.run(main())
```

---

## Rate Limits

Nebula API enforces rate limits based on your plan:

- **Free Tier**: 100 requests/minute
- **Pro Tier**: 1,000 requests/minute
- **Enterprise**: Custom limits

When rate limited, you'll receive a `NebulaRateLimitException` with a `retry-after` header.

---

## Support

- [Full Documentation](https://docs.nebulacloud.app)
- [GitHub Issues](https://github.com/nebula-agi/nebula-sdks/issues)
- [Discord Community](https://discord.gg/nebula)
- Email: support@trynebula.ai
