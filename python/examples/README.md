# Nebula Client SDK

A simple, intuitive Python SDK for interacting with Nebula's memory and retrieval capabilities.

## Overview

The Nebula Client SDK provides a clean interface to Nebula's memory and retrieval capabilities, focusing on the core functionality without the complexity of the underlying Nebula system. The SDK uses a **universal memory approach** where all content (text, documents, conversations) is stored and managed through unified functions.

## Key Features

- **Universal Memory Storage**: Store any type of memory (text, documents, conversations) with automatic chunking
- **Collection Management**: Organize memories into collections for access control
- **Conversational Memory**: Store multi-turn conversations with message-level granularity
- **Semantic Search**: Search across all stored memories with relevance scoring
- **RAG-powered Chat**: Chat with agents using their memories for context
- **Deterministic Deduplication**: Prevent duplicate storage using content-based IDs

## Quick Start

```python
from nebula import Nebula

# Initialize the client
client = Nebula(api_key="your_api_key")

# Store a memory
memory = client.store(
    agent_id="my_agent",
    content="Machine learning is a subset of AI that enables computers to learn from data.",
    metadata={"topic": "ai", "importance": "high"}
)

# Retrieve relevant memories
results = client.retrieve(
    agent_id="my_agent",
    query="What is machine learning?",
    limit=5
)

# Chat with the agent
response = client.chat(
    agent_id="my_agent",
    message="Explain the relationship between AI and machine learning."
)
```

## Collection Management

Collections help organize memories and provide access control:

```python
# Create a collection
collection = client.create_collection(
    name="research_notes",
    description="Collection for research-related memories"
)

# Store memories in a collection
memory = client.store_memory(
    collection_id=collection.id,
    content="Important research finding...",
    metadata={"topic": "research"}
)

# Get all memories in a collection
memories = client.list_memories(collection_ids=[collection.id])

# List all collections
collections = client.list_clusters()
```

## Conversation Messages

Store and manage conversations using the universal `store_memory` function:

```python
# Create a conversation memory
conversation = client.store_memory(
    memory_type="conversation",
    name="Customer Support Chat",
    collection_id="your-cluster-id",
    metadata={"conversation_type": "support"}
)

# Add messages to the conversation
client.append_memory(
    memory_id=conversation.id,
    messages=[
        {
            "content": "Hello! How can I help you?",
            "role": "assistant",
            "metadata": {"sentiment": "positive"}
        },
        {
            "content": "I need help with my account",
            "role": "user",
            "parent_id": None  # Optional: link to parent message
        }
    ],
    collection_id="your-cluster-id"
)

# Retrieve conversation messages
messages = client.get_conversation_messages(conversation.id)

for msg in messages:
    role = msg.metadata.get("source_role", msg.metadata.get("role"))
    print(f"[{role.upper()}] {msg.content}")
    print(f"Created: {msg.created_at}")
```

### Async Support

The SDK also supports async operations:

```python
import asyncio
from nebula import AsyncNebula

async def main():
    client = AsyncNebula(api_key="your_api_key")

    # Create conversation memory
    conversation = await client.store_memory(
        memory_type="conversation",
        name="Async Chat",
        collection_id="your-cluster-id"
    )

    # Append messages
    await client.append_memory(
        memory_id=conversation.id,
        messages=[{"content": "Hello!", "role": "user"}],
        collection_id="your-cluster-id"
    )

    # Retrieve messages
    messages = await client.get_conversation_messages(conversation.id)
    print(f"Retrieved {len(messages)} messages")

asyncio.run(main())
```

## Storing Memories

The universal `store_memory` function handles all types of memories:

### Text/Document Memories

```python
# Store a single text memory (default type is "document")
memory = client.store_memory(
    content="User prefers email communication over phone calls",
    collection_id="user_preferences",
    metadata={
        "user_id": "user_123",
        "preference_type": "communication"
    }
)

# Explicitly specify document type
document = client.store_memory(
    memory_type="document",
    content="Research findings on neural networks...",
    collection_id="research_notes",
    metadata={"topic": "ai_research"}
)
```

### Conversation Memories

Store conversations by creating a conversation memory and appending messages:

```python
# Create a conversation memory
conversation = client.store_memory(
    memory_type="conversation",
    name="AI Discussion",
    collection_id="conversations",
    metadata={"topic": "ai_education"}
)

# Add messages to the conversation
client.append_memory(
    memory_id=conversation.id,
    messages=[
        {
            "content": "What is machine learning?",
            "role": "user"
        },
        {
            "content": "Machine learning is a subset of AI that enables computers to learn from data.",
            "role": "assistant"
        }
    ],
    collection_id="conversations"
)
```

## Appending to Memories

The universal append function allows you to add content to existing memories:

### Append to Conversations

```python
# Append messages to an existing conversation
client.append_memory(
    memory_id="conversation_memory_id",
    messages=[
        {"content": "What's the weather like?", "role": "user"},
        {"content": "It's sunny today!", "role": "assistant"}
    ],
    collection_id="your-cluster-id"
)
```

### Append to Documents

```python
# Append text to an existing document memory
client.append_memory(
    memory_id="document_memory_id",
    raw_text="Additional paragraph or content to add to the document.",
    collection_id="your-cluster-id"
)

# Or append multiple chunks
client.append_memory(
    memory_id="document_memory_id",
    chunks=["Chunk 1 text", "Chunk 2 text", "Chunk 3 text"],
    collection_id="your-cluster-id"
)
```

## Retrieving Memories

### Semantic Search

```python
# Search for relevant memories
results = client.retrieve(
    agent_id="assistant",
    query="machine learning algorithms",
    limit=10
)

for result in results:
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
    print(f"Memory ID: {result.id}")
```

### General Search

```python
# Search across all memories
results = client.search(
    query="artificial intelligence",
    limit=5
)
```

## Chat with Memories

Use RAG (Retrieval-Augmented Generation) to chat with agents using their memories:

```python
response = client.chat(
    agent_id="assistant",
    message="What have you learned about user preferences?",
    model="gpt-4.1-mini",
    temperature=0.7
)

print(f"Response: {response.content}")
print(f"Agent ID: {response.agent_id}")
```

## Memory Management

### Get Specific Memory

```python
memory = client.get("memory_id_here")
print(f"Content: {memory.content}")
print(f"Metadata: {memory.metadata}")
```

### List Agent Memories

```python
memories = client.list_agent_memories(
    agent_id="assistant",
    limit=50
)
```

### Delete Memory

```python
client.delete("memory_id_here")
```

## Key Changes from Previous Version

- **Unified Memory Architecture**: All content (documents, conversations, text) is managed through universal `store_memory` and `append_memory` functions
- **Universal Append**: Single `append_memory` function works for both conversations and documents
- **Memory Types**: Memories are created with `memory_type` parameter ("conversation" or "document")
- **Consistent Terminology**: SDK uses "memory" terminology throughout, abstracting away backend "engram" implementation
- **Collection Terminology**: Renamed "clusters" to "collections" for consistency
- **Deterministic IDs**: Uses SHA-256 + UUIDv5 for content-based deduplication
- **Form Data**: Uses form data (like the original Nebula SDK) for memory creation

## Architecture

The SDK follows a unified memory-centric approach:

```
Memories (Universal Storage)
├── Documents (memory_type="document")
│   ├── Files (PDF, TXT, MP3, etc.)
│   ├── Individual Text Memories (raw_text)
│   └── Multi-chunk content
│
├── Conversations (memory_type="conversation")
│   ├── Multi-turn dialogues
│   ├── Messages with roles (user/assistant/system)
│   └── Chronological message history
│
└── Metadata & Collections

Chunks (Internal)
├── Automatically created from memories
├── Used for retrieval and search
└── Managed by the Nebula backend

SDK Operations
├── Create: store_memory(memory_type=...)
├── Append: append_memory(memory_id=..., messages=... or raw_text=...)
├── Retrieve: retrieve(...) or get_conversation_messages(...)
└── Delete: delete(memory_id=...)

Backend Endpoints (abstracted by SDK)
├── POST /v1/memories (with engram_type)
├── POST /v1/memories/{id}/append
├── GET /v1/memories/{id}
└── DELETE /v1/memories/{id}
```

## Testing

Run the test suite to verify functionality:

```bash
python3 test_engrams_endpoint.py
```

The test suite covers:
- Collection management
- Individual memory storage
- Conversation storage
- Memory retrieval
- Chat functionality
- General search
- Collection memories retrieval

## Error Handling

The SDK provides comprehensive error handling:

```python
from nebula.exceptions import (
    NebulaException,
    NebulaClientException,
    NebulaAuthenticationException,
    NebulaRateLimitException,
    NebulaValidationException
)

try:
    memory = client.store(agent_id="test", content="test")
except NebulaAuthenticationException:
    print("Invalid API key")
except NebulaRateLimitException:
    print("Rate limit exceeded")
except NebulaException as e:
    print(f"API error: {e}")
```

## Backward Compatibility

The SDK maintains backward compatibility with method aliases:

```python
# Old method names still work
client.store_chunk = client.store
client.retrieve_chunks = client.retrieve
client.create_cluster = client.create_collection
client.get_cluster = client.get_collection
``` 