"""
Basic Memory Operations Example

Demonstrates:
- Creating a collection
- Adding memories
- Searching memories
- Retrieving specific memories
- Deleting memories
"""

import os
from nebula import NebulaClient


def main():
    # Initialize the client
    client = NebulaClient(api_key=os.getenv("NEBULA_API_KEY"))

    print("🚀 Starting Nebula SDK Basic Operations Example\n")

    # 1. Create a collection
    print("📁 Creating collection...")
    collection = client.create_collection(
        name="Product Documentation",
        description="Technical documentation for our products",
        metadata={
            "category": "docs",
            "version": "1.0"
        }
    )
    print(f"✅ Created collection: {collection.name} (ID: {collection.id})\n")

    # 2. Add memories to the collection
    print("💾 Adding memories...")
    memory1 = client.add_memory(
        collection_id=collection.id,
        content="Our API supports both REST and GraphQL interfaces for maximum flexibility.",
        metadata={
            "type": "api-info",
            "section": "overview"
        }
    )
    print(f"✅ Added memory 1: {memory1.id}")

    memory2 = client.add_memory(
        collection_id=collection.id,
        content="Authentication requires an API key passed in the Authorization header.",
        metadata={
            "type": "api-info",
            "section": "authentication"
        }
    )
    print(f"✅ Added memory 2: {memory2.id}\n")

    # 3. Search for memories
    print('🔍 Searching for "authentication"...')
    search_results = client.search(
        collection_id=collection.id,
        query="how to authenticate",
        limit=5
    )

    print(f"Found {len(search_results.results)} results:")
    for idx, result in enumerate(search_results.results, 1):
        print(f"  {idx}. [Score: {result.score:.3f}] {result.content[:80]}...")
    print()

    # 4. Retrieve a specific memory
    print("📖 Retrieving specific memory...")
    retrieved_memory = client.get_memory(memory1.id)
    print(f"✅ Retrieved: {retrieved_memory.content}\n")

    # 5. Update a memory
    print("✏️  Updating memory...")
    updated_memory = client.update_memory(
        memory_id=memory1.id,
        content="Our API supports REST, GraphQL, and WebSocket interfaces for maximum flexibility.",
        metadata={
            "type": "api-info",
            "section": "overview",
            "updated": True
        }
    )
    print(f"✅ Updated memory: {updated_memory.content}\n")

    # 6. List all memories in collection
    print("📋 Listing all memories...")
    all_memories = client.list_memories(
        collection_id=collection.id,
        limit=10
    )
    print(f"Total memories in collection: {len(all_memories.results)}\n")

    # 7. Clean up - delete memories and collection
    print("🧹 Cleaning up...")
    client.delete_memory(memory1.id)
    client.delete_memory(memory2.id)
    client.delete_collection(collection.id)
    print("✅ Cleanup complete\n")

    print("✨ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
