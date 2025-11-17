# Nebula Client SDK API Documentation

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Client Initialization](#client-initialization)
3. [Authentication](#authentication)
4. [Cluster Management](#cluster-management)
5. [Memory Storage](#memory-storage)
6. [Memory Retrieval](#memory-retrieval)
7. [Search Operations](#search-operations)
8. [Memory Management](#memory-management)
9. [Async Client](#async-client)
10. [Health Check](#health-check)
11. [Error Handling](#error-handling)
12. [Data Models](#data-models)
13. [Examples](#examples)

## Installation & Setup

### Prerequisites

- Python 3.8+
- Nebula API key

### Installation

```bash
pip install nebula-client
```

### Environment Setup

```bash
export NEBULA_API_KEY="your_api_key_here"
```

## Client Initialization

### Basic Initialization

```python
from nebula_client import NebulaClient

# Using environment variable
client = NebulaClient()

# Or with explicit API key
client = NebulaClient(api_key="your_api_key_here")
```

### Advanced Configuration

```python
client = NebulaClient(
    api_key="your_api_key_here",
    base_url="https://api.nebulacloud.app",  # Default
    timeout=30.0  # Default timeout in seconds
)
```

## Authentication

- If your credential looks like a Nebula API key (e.g., starts with `key_` and contains one `.`), the SDK sends it via the `X-API-Key` header.
- Otherwise, the SDK sends the credential as a Bearer token via the `Authorization` header.

### Context Manager Usage

```python
with NebulaClient(api_key="your_api_key") as client:
    # Your operations here
    from nebula_client import Memory
    memory = Memory(collection_id="cluster_123", content="Hello world")
    doc_id = client.store_memory(memory)
```

## Cluster Management

Clusters help organize memories and provide access control.

### Create Cluster

```python
cluster = client.create_cluster(
    name="research_notes",
    description="Cluster for research-related memories",
    metadata={"category": "academic", "priority": "high"}
)
```

**Parameters:**
- `name` (str): Cluster name (required)
- `description` (str, optional): Cluster description
- `metadata` (dict, optional): Additional metadata

**Returns:** `Cluster` object with cluster details

### Get Cluster

```python
cluster = client.get_cluster("collection_id_here")
```

**Parameters:**
- `collection_id` (str): ID of the cluster to retrieve

**Returns:** `Cluster` object

### Get Cluster by Name

```python
cluster = client.get_cluster_by_name("research_notes")
```

**Parameters:**
- `name` (str): Name of the cluster to retrieve

**Returns:** `Cluster` object

### List Clusters

```python
clusters = client.list_clusters(limit=100, offset=0)
```

**Parameters:**
- `limit` (int, optional): Maximum number of clusters to return (default: 100)
- `offset` (int, optional): Number of clusters to skip (default: 0)

**Returns:** List of `Cluster` objects

### Update Cluster

```python
updated_cluster = client.update_cluster(
    collection_id="collection_id_here",
    name="new_name",
    description="Updated description",
    metadata={"updated": True}
)
```

**Parameters:**
- `collection_id` (str): ID of the cluster to update
- `name` (str, optional): New name for the cluster
- `description` (str, optional): New description for the cluster
- `metadata` (dict, optional): New metadata for the cluster

**Returns:** Updated `Cluster` object

### Delete Cluster

```python
success = client.delete_cluster("collection_id_here")
```

**Parameters:**
- `collection_id` (str): ID of the cluster to delete

**Returns:** `True` if successful

## Memory Storage

The SDK provides unified methods for storing both conversation messages and text documents.

### Store Single Memory

```python
from nebula_client import Memory

# Store a text document
memory = Memory(
    collection_id="cluster_123",
    content="This is an important memory about machine learning.",
    metadata={"topic": "machine_learning", "importance": "high"}
)

doc_id = client.store_memory(memory)
```

**Parameters:**
- `memory` (Memory or dict): Memory object or equivalent keyword arguments
- `**kwargs`: Alternative way to specify memory parameters

**Returns:** Engram ID (str) for text documents, or conversation ID (str) for conversation messages

### Store Multiple Memories

```python
memories = [
    Memory(collection_id="cluster_123", content="First memory", metadata={"type": "note"}),
    Memory(collection_id="cluster_123", content="Second memory", metadata={"type": "note"}),
    Memory(collection_id="cluster_123", content="User question", role="user"),
    Memory(collection_id="cluster_123", content="Assistant response", role="assistant", parent_id="conv_123")
]

ids = client.store_memories(memories)
```

**Parameters:**
- `memories` (List[Memory]): List of memory objects to store

**Returns:** List of IDs in the same order as input memories

### Conversation Storage

```python
# Create a new conversation
message = Memory(
    collection_id="cluster_123",
    content="What is machine learning?",
    role="user",
    metadata={"timestamp": "2024-01-15T10:30:00Z"}
)

conv_id = client.store_memory(message)

# Add to existing conversation
response = Memory(
    collection_id="cluster_123",
    content="Machine learning is a subset of AI.",
    role="assistant",
    parent_id=conv_id,  # Link to existing conversation
    metadata={"timestamp": "2024-01-15T10:30:05Z"}
)

client.store_memory(response)
```

## Memory Retrieval

### List Memories

```python
memories = client.list_memories(
    collection_ids=["cluster_123", "cluster_456"],
    limit=100,
    offset=0
)
```

**Parameters:**
- `collection_ids` (List[str]): List of cluster IDs to retrieve memories from
- `limit` (int, optional): Maximum number of memories to return (default: 100)
- `offset` (int, optional): Number of memories to skip (default: 0)

**Returns:** List of `MemoryResponse` objects

### Get Memory

```python
memory = client.get_memory("memory_id_here")
```

**Parameters:**
- `memory_id` (str): ID of the memory to retrieve

**Returns:** `MemoryResponse` object

### Delete Memory

Delete one or more memories with a single method call.

#### Single Deletion

```python
success = client.delete("memory_id_here")
print(f"Deleted: {success}")  # True
```

**Parameters:**
- `memory_ids` (str): ID of the memory to delete

**Returns:** `bool` - `True` if successful, raises exception on failure

#### Batch Deletion

```python
memory_ids = ["mem_id_1", "mem_id_2", "mem_id_3"]
result = client.delete(memory_ids)

print(f"Message: {result['message']}")
print(f"Successful: {result['results']['successful']}")  # List of deleted IDs
print(f"Failed: {result['results']['failed']}")  # List of failed deletions with errors
print(f"Summary: {result['results']['summary']}")  # Deletion statistics
```

**Parameters:**
- `memory_ids` (List[str]): List of memory IDs to delete

**Returns:** `Dict[str, Any]` with the following structure:
```python
{
    "message": "Deleted 2 of 3 documents",
    "results": {
        "successful": ["mem_id_1", "mem_id_2"],
        "failed": [{"id": "mem_id_3", "error": "Not found or no permission"}],
        "summary": {
            "total": 3,
            "succeeded": 2,
            "failed": 1
        }
    }
}
```

**Note:** The method automatically detects whether you're passing a single ID or a list and returns the appropriate response type.

## Search Operations

### Search Memories

```python
# Default (SuperBFS search)
results = client.search(
    query="machine learning",
    collection_ids=["cluster_123"],
    limit=10,
    filters={"metadata.topic": "ai"}
)

# Fast BFS search
results = client.search(
    query="quick search",
    collection_ids=["cluster_123"],
    limit=10,
    search_settings={
        "search_mode": "fast"
    }
)

# SuperBFS search with custom settings
results = client.search(
    query="complex query",
    collection_ids=["cluster_123"],
    limit=10,
    search_settings={
        "search_mode": "super",
        "use_semantic_search": True,
        "use_fulltext_search": True
    }
)
```

**Parameters:**
- `query` (str): Search query
- `collection_ids` (List[str]): List of cluster IDs to search within
- `limit` (int, optional): Maximum number of results (default: 10)
- `filters` (dict, optional): Additional filters to apply
- `search_settings` (dict, optional): Advanced search configuration
  - `search_mode` (str): "fast" for fast BFS or "super" for SuperBFS (default: "super")

**Returns:** List of `SearchResult` objects

### Search Result Types

Search results can include both chunk-based and graph-based results:

```python
for result in results:
    if result.content:
        # Chunk-based result
        print(f"Content: {result.content}")
    elif result.graph_result_type:
        # Graph-based result
        if result.graph_entity:
            print(f"Entity: {result.graph_entity.name}")
        elif result.graph_relationship:
            print(f"Relationship: {result.graph_relationship.subject} -> {result.graph_relationship.object}")
        elif result.graph_community:
            print(f"Community: {result.graph_community.name}")
```

## Async Client

The SDK provides an async client with identical functionality:

```python
from nebula_client import AsyncNebulaClient, Memory

async with AsyncNebulaClient(api_key="your_api_key") as client:
    # Store memory
    memory = Memory(collection_id="cluster_123", content="Async memory")
    doc_id = await client.store_memory(memory)
    
    # Search
    results = await client.search("query", collection_ids=["cluster_123"])
    
    # List memories
    memories = await client.list_memories(collection_ids=["cluster_123"])
```

### Async Client Methods

All methods from the sync client are available in the async client with `await`:

- `await client.create_cluster(...)`
- `await client.store_memory(...)`
- `await client.store_memories(...)`
- `await client.list_memories(...)`
- `await client.search(...)`
- etc.

## Health Check

```python
health = client.health_check()
```

**Returns:** Dictionary with health status information

## Error Handling

The SDK provides specific exception types for different error scenarios:

### Exception Types

- `NebulaClientException`: General client errors (network issues, timeouts)
- `NebulaAuthenticationException`: Authentication failures (invalid API key)
- `NebulaRateLimitException`: Rate limiting exceeded
- `NebulaValidationException`: Invalid input data
- `NebulaClusterNotFoundException`: Cluster not found
- `NebulaException`: General API errors

### Error Handling Example

```python
from nebula_client import NebulaClient, NebulaAuthenticationException, NebulaValidationException

try:
    client = NebulaClient(api_key="invalid_key")
    memory = Memory(collection_id="cluster_123", content="test")
    doc_id = client.store_memory(memory)
except NebulaAuthenticationException as e:
    print(f"Authentication failed: {e}")
except NebulaValidationException as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Data Models

### Memory (Write Model)

```python
@dataclass
class Memory:
    collection_id: str
    content: str
    role: Optional[str] = None  # user, assistant, or custom
    parent_id: Optional[str] = None  # conversation_id for messages
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Behavior:**
- `role` present → conversation message
  - `parent_id` used as conversation_id if provided; else a new conversation is created
  - Returns conversation_id
- `role` absent → text/json document
  - Content is stored as raw text
  - Returns engram_id

### MemoryResponse (Read Model)

```python
@dataclass
class MemoryResponse:
    id: str
    content: Optional[str] = None
    chunks: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    collection_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Cluster

```python
@dataclass
class Cluster:
    id: str
    name: str
    description: Optional[str]
    metadata: Dict[str, Any]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    memory_count: int
    owner_id: Optional[str]
```

### SearchResult

```python
@dataclass
class SearchResult:
    id: str
    score: float
    metadata: Dict[str, Any]
    source: Optional[str]
    content: Optional[str] = None
    # Graph fields for graph search results
    graph_result_type: Optional[GraphSearchResultType] = None
    graph_entity: Optional[GraphEntityResult] = None
    graph_relationship: Optional[GraphRelationshipResult] = None
    graph_community: Optional[GraphCommunityResult] = None
```

## Examples

### Basic Usage

```python
from nebula_client import NebulaClient, Memory

# Initialize client
client = NebulaClient(api_key="your_api_key")

# Create a cluster
cluster = client.create_cluster(
    name="my_memories",
    description="Personal memory storage"
)

# Store a memory
memory = Memory(
    collection_id=cluster.id,
    content="Remember to buy groceries tomorrow",
    metadata={"type": "reminder", "priority": "high"}
)

doc_id = client.store_memory(memory)
print(f"Stored memory with ID: {doc_id}")

# Search for memories
results = client.search(
    query="groceries",
    collection_ids=[cluster.id],
    limit=5
)

for result in results:
    print(f"Found: {result.content}")
```

### Conversation Management

```python
# Start a conversation
user_msg = Memory(
    collection_id=cluster.id,
    content="What is the weather like?",
    role="user",
    metadata={"timestamp": "2024-01-15T10:00:00Z"}
)

conv_id = client.store_memory(user_msg)

# Add assistant response
assistant_msg = Memory(
    collection_id=cluster.id,
    content="The weather is sunny and 75°F.",
    role="assistant",
    parent_id=conv_id,
    metadata={"timestamp": "2024-01-15T10:00:05Z"}
)

client.store_memory(assistant_msg)

# Continue conversation
follow_up = Memory(
    collection_id=cluster.id,
    content="Will it rain later?",
    role="user",
    parent_id=conv_id,
    metadata={"timestamp": "2024-01-15T10:00:10Z"}
)

client.store_memory(follow_up)
```

### Batch Operations

```python
# Store multiple memories efficiently
memories = [
    Memory(collection_id=cluster.id, content="Note 1", metadata={"type": "note"}),
    Memory(collection_id=cluster.id, content="Note 2", metadata={"type": "note"}),
    Memory(collection_id=cluster.id, content="User question", role="user"),
    Memory(collection_id=cluster.id, content="Assistant response", role="assistant", parent_id="conv_123")
]

ids = client.store_memories(memories)
print(f"Stored {len(ids)} memories")
```

### Advanced Search

```python
# Search with filters and custom settings
results = client.search(
    query="machine learning",
    collection_ids=[cluster.id],
    limit=10,
    filters={
        "metadata.type": "note",
        "metadata.priority": "high"
    },
    search_settings={
        "use_semantic_search": True,
        "use_fulltext_search": True,
        "num_sub_queries": 3
    }
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content}")
    print(f"Metadata: {result.metadata}")
```

### Async Usage

```python
import asyncio
from nebula_client import AsyncNebulaClient, Memory

async def main():
    async with AsyncNebulaClient(api_key="your_api_key") as client:
        # Create cluster
        cluster = await client.create_cluster(name="async_memories")
        
        # Store memory
        memory = Memory(collection_id=cluster.id, content="Async memory")
        doc_id = await client.store_memory(memory)
        
        # Search
        results = await client.search("async", collection_ids=[cluster.id])
        
        print(f"Found {len(results)} results")

# Run async function
asyncio.run(main())
``` 