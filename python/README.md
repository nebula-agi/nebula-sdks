# Nebula Python SDK

Persistent memory layer for AI applications. Store, search, and retrieve information with semantic understanding.

## Installation

```bash
pip install nebula-client
```

## Quick Start

```python
from nebula import Nebula

# Initialize client
client = Nebula(api_key="your-api-key")

# Create a collection
collection = client.create_cluster(name="my_notes")

# Store a memory
memory_id = client.store_memory({
    "collection_id": collection.id,
    "content": "Machine learning is transforming healthcare",
    "metadata": {"topic": "AI", "importance": "high"}
})

# Search memories
results = client.search(
    query="machine learning healthcare",
    collection_ids=[collection.id],
    limit=5
)

for result in results:
    print(f"Score: {result.score:.2f}")
    print(f"Content: {result.content}")
```

## Core Operations

### Collections

```python
# Create
collection = client.create_cluster(name="my_collection", description="Optional description")

# List
collections = client.list_clusters()

# Get by ID or name
collection = client.get_cluster(collection_id)
collection = client.get_cluster_by_name("my_collection")

# Update
client.update_cluster(collection_id, name="new_name")

# Delete
client.delete_cluster(collection_id)
```

### Store Memories

```python
# Single memory
from nebula import Memory

memory = Memory(
    collection_id=collection.id,
    content="Your content here",
    metadata={"category": "example"}
)
memory_id = client.store_memory(memory)

# Batch storage
memories = [
    Memory(collection_id=collection.id, content="First memory"),
    Memory(collection_id=collection.id, content="Second memory")
]
ids = client.store_memories(memories)
```

### Retrieve Memories

```python
# List memories
memories = client.list_memories(collection_ids=[collection.id], limit=10)

# Filter with metadata
memories = client.list_memories(
    collection_ids=[collection.id],
    metadata_filters={"metadata.category": {"$eq": "example"}}
)

# Get specific memory
memory = client.get_memory("memory_id")
```

### Search

```python
# Semantic search
results = client.search(
    query="your search query",
    collection_ids=[collection.id],
    limit=10
)
```

### Delete

```python
# Single deletion
deleted = client.delete("memory_id")  # Returns True

# Batch deletion
result = client.delete(["id1", "id2", "id3"])  # Returns detailed results
```

## Conversations

```python
# Store conversation messages
user_msg = Memory(
    collection_id=collection.id,
    content="What is machine learning?",
    role="user"
)
conv_id = client.store_memory(user_msg)

assistant_msg = Memory(
    collection_id=collection.id,
    content="Machine learning is a subset of AI...",
    role="assistant",
    parent_id=conv_id
)
client.store_memory(assistant_msg)

# List conversations
conversations = client.list_conversations(collection_ids=[collection.id])

# Get messages
messages = client.get_conversation_messages(conv_id)
```

## Async Client

```python
from nebula import AsyncNebula, Memory

async with AsyncNebula(api_key="your-api-key") as client:
    # All methods available with await
    collection = await client.create_cluster(name="async_collection")
    memory_id = await client.store_memory(Memory(
        collection_id=collection.id,
        content="Async memory"
    ))
    results = await client.search("query", collection_ids=[collection.id])
```

## Documentation

- [Full Documentation](https://docs.trynebula.ai)
- [API Reference](https://docs.trynebula.ai/clients/python)
- [Examples](./examples/)

## Support

Email [support@trynebula.ai](mailto:support@trynebula.ai)
