# Getting Started with Nebula SDKs

This guide will help you get started with Nebula's official SDKs for JavaScript/TypeScript and Python.

## Prerequisites

- A Nebula account and API key (sign up at [nebulacloud.app](https://nebulacloud.app))
- Node.js 16+ (for JavaScript SDK)
- Python 3.8+ (for Python SDK)

## Quick Start

### JavaScript/TypeScript

1. **Install the SDK**

```bash
npm install @nebula-ai/sdk
```

2. **Set your API key**

```bash
export NEBULA_API_KEY=your_api_key_here
```

3. **Create your first collection**

```javascript
import Nebula from '@nebula-ai/sdk';

const client = new Nebula({
  apiKey: process.env.NEBULA_API_KEY
});

// Create a collection
const collection = await client.createCollection({
  name: "My First Collection",
  description: "Getting started with Nebula"
});

console.log('Collection created:', collection.id);
```

### Python

1. **Install the SDK**

```bash
pip install nebula-client
```

2. **Set your API key**

```bash
export NEBULA_API_KEY=your_api_key_here
```

3. **Create your first collection**

```python
from nebula import NebulaClient
import os

client = NebulaClient(api_key=os.getenv('NEBULA_API_KEY'))

# Create a collection
collection = client.create_collection(
    name="My First Collection",
    description="Getting started with Nebula"
)

print(f'Collection created: {collection.id}')
```

## Core Concepts

### Collections

Collections are containers for organizing related memories. Think of them as databases or folders for your AI's memory.

```javascript
// Create a collection for user conversations
const userCollection = await client.createCollection({
  name: "User Conversations",
  description: "Store all user chat history",
  metadata: { type: "conversations" }
});
```

### Memories

Memories are individual pieces of content stored within collections. Each memory can have:
- **Content**: The actual text/data
- **Metadata**: Additional key-value pairs
- **Vector embedding**: Automatically generated for semantic search

```javascript
// Add a memory to the collection
const memory = await client.addMemory({
  collectionId: userCollection.id,
  content: "User prefers dark mode and compact layout",
  metadata: {
    userId: "user-123",
    category: "preferences"
  }
});
```

### Search

Search enables semantic retrieval of relevant memories based on natural language queries.

```javascript
// Search for relevant memories
const results = await client.search({
  collectionId: userCollection.id,
  query: "What are the user's UI preferences?",
  limit: 5
});

results.results.forEach(result => {
  console.log(`[${result.score}] ${result.content}`);
});
```

## Common Patterns

### 1. Conversation Memory

Store and retrieve conversation history:

```javascript
// Store a conversation turn
await client.addMemory({
  collectionId: conversationCollection.id,
  content: `User: ${userMessage}\nAssistant: ${assistantResponse}`,
  metadata: {
    timestamp: new Date().toISOString(),
    userId: userId
  }
});

// Retrieve relevant context for new message
const context = await client.search({
  collectionId: conversationCollection.id,
  query: newUserMessage,
  limit: 3
});
```

### 2. Document RAG (Retrieval Augmented Generation)

Build a RAG system with document chunks:

```javascript
// Split document into chunks and store
const chunks = splitDocument(document);
for (const chunk of chunks) {
  await client.addMemory({
    collectionId: documentCollection.id,
    content: chunk.text,
    metadata: {
      documentId: document.id,
      chunkIndex: chunk.index,
      section: chunk.section
    }
  });
}

// Query for relevant chunks
const relevantChunks = await client.search({
  collectionId: documentCollection.id,
  query: userQuestion,
  limit: 5
});
```

### 3. User Preference Tracking

Store and recall user preferences:

```javascript
// Store preference
await client.addMemory({
  collectionId: userPrefsCollection.id,
  content: `User ${userId} prefers ${preference}`,
  metadata: {
    userId: userId,
    category: "preferences",
    timestamp: Date.now()
  }
});

// Recall preferences
const prefs = await client.search({
  collectionId: userPrefsCollection.id,
  query: `preferences for user ${userId}`,
  filters: { userId: userId }
});
```

## Error Handling

Always handle errors appropriately:

**JavaScript:**
```javascript
import Nebula, { NebulaAuthenticationException, NebulaNotFoundException } from '@nebula-ai/sdk';

try {
  const memory = await client.getMemory(memoryId);
} catch (error) {
  if (error instanceof NebulaAuthenticationException) {
    console.error('Invalid API key');
  } else if (error instanceof NebulaNotFoundException) {
    console.error('Memory not found');
  } else {
    console.error('Unexpected error:', error);
  }
}
```

**Python:**
```python
from nebula.exceptions import NebulaAuthenticationException, NebulaNotFoundException

try:
    memory = client.get_memory(memory_id)
except NebulaAuthenticationException:
    print('Invalid API key')
except NebulaNotFoundException:
    print('Memory not found')
except Exception as e:
    print(f'Unexpected error: {e}')
```

## Best Practices

1. **Use descriptive collection names**: Make it easy to identify what each collection contains
2. **Add meaningful metadata**: Include searchable metadata with your memories
3. **Chunk appropriately**: For documents, use 200-500 word chunks for optimal search
4. **Handle rate limits**: Implement retry logic with exponential backoff
5. **Use collections to organize**: Separate different types of data into different collections

## Next Steps

- Explore the [API Reference](./api-reference.md)
- Check out [Examples](../examples/)
- Read about [Graph Queries](./graph-queries.md)
- Join our [Discord Community](https://discord.gg/nebula)

## Getting Help

- [Documentation](https://docs.nebulacloud.app)
- [GitHub Issues](https://github.com/nebula-agi/nebula-sdks/issues)
- [Discord](https://discord.gg/nebula)
- Email: support@trynebula.ai
