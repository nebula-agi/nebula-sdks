# @nebula-ai/sdk

Persistent memory layer for AI applications. Store, search, and retrieve information with semantic understanding.

## Installation

```bash
npm install @nebula-ai/sdk
```

## Quick Start

```typescript
import Nebula from '@nebula-ai/sdk';

// Initialize client
const client = new Nebula({
  apiKey: 'your-api-key'
});

// Create a collection
const collection = await client.createCluster({
  name: 'my_notes'
});

// Store a memory
const memoryId = await client.storeMemory({
  collection_id: collection.id,
  content: 'Machine learning is transforming healthcare',
  metadata: { topic: 'AI', importance: 'high' }
});

// Search memories
const results = await client.search({
  query: 'machine learning healthcare',
  collection_ids: [collection.id],
  limit: 5
});

results.forEach(result => {
  console.log(`Score: ${result.score?.toFixed(2)}`);
  console.log(`Content: ${result.content}`);
});
```

## Core Operations

### Collections

```typescript
// Create
const collection = await client.createCluster({
  name: 'my_collection',
  description: 'Optional description'
});

// List
const collections = await client.listClusters();

// Get by ID or name
const collection = await client.getCluster(collectionId);
const collection = await client.getClusterByName('my_collection');

// Update
await client.updateCluster({
  collectionId,
  name: 'new_name'
});

// Delete
await client.deleteCluster(collectionId);
```

### Store Memories

```typescript
// Single memory
const memoryId = await client.storeMemory({
  collection_id: collection.id,
  content: 'Your content here',
  metadata: { category: 'example' }
});

// Batch storage
const memoryIds = await client.storeMemories([
  { collection_id: collection.id, content: 'First memory' },
  { collection_id: collection.id, content: 'Second memory' }
]);
```

### Retrieve Memories

```typescript
// List memories
const memories = await client.listMemories({
  collection_ids: [collection.id],
  limit: 10
});

// Filter with metadata
const memories = await client.listMemories({
  collection_ids: [collection.id],
  metadata_filters: {
    'metadata.category': { $eq: 'example' }
  }
});

// Get specific memory
const memory = await client.getMemory('memory-id');
```

### Search

```typescript
// Semantic search
const results = await client.search({
  query: 'your search query',
  collection_ids: [collection.id],
  limit: 10
});
```

### Delete

```typescript
// Single deletion
const deleted = await client.delete('memory-id'); // Returns boolean

// Batch deletion
const result = await client.delete(['id1', 'id2', 'id3']); // Returns detailed results
```

## Conversations

```typescript
// Store conversation messages
const conversationId = await client.storeMemory({
  collection_id: collection.id,
  content: 'What is machine learning?',
  role: 'user',
  metadata: { content_type: 'conversation' }
});

await client.storeMemory({
  collection_id: collection.id,
  content: 'Machine learning is a subset of AI...',
  role: 'assistant',
  parent_id: conversationId,
  metadata: { content_type: 'conversation' }
});

// List conversation memories
const conversations = await client.listMemories({
  collection_ids: [collection.id],
  metadata_filters: { 'metadata.content_type': { $eq: 'conversation' } }
});

// Get messages from a conversation memory
const conversation = await client.getMemory(conversationId);
const messages = conversation.chunks ?? [];
```

## Error Handling

```typescript
import Nebula, {
  NebulaAuthenticationException,
  NebulaRateLimitException,
  NebulaValidationException
} from '@nebula-ai/sdk';

try {
  await client.search({ query: 'query', collection_ids: [collectionId] });
} catch (error) {
  if (error instanceof NebulaAuthenticationException) {
    console.log('Invalid API key');
  } else if (error instanceof NebulaRateLimitException) {
    console.log('Rate limit exceeded');
  }
}
```

## Documentation

- [Full Documentation](https://docs.trynebula.ai)
- [API Reference](https://docs.trynebula.ai/clients/nodejs)

## Support

Email [support@trynebula.ai](mailto:support@trynebula.ai)
