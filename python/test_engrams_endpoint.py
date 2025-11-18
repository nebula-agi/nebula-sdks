#!/usr/bin/env python3
"""
Test script for the updated Nebula Client SDK using documents endpoint
"""
import os
import sys
from typing import List

# Add the current directory to the path so we can import the client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nebula import Nebula

# Set the API key for testing
os.environ["NEBULA_API_KEY"] = "key_L2bhhSmBCKX-wh-c_QcI8g==.mouoseeWHgXvrMcc7pYDYAKMhtXljXfwMYXblotgI84="

def test_collection_management():
    """Test collection creation and management"""
    print("🧪 Testing collection management...")
    
    client = Nebula()
    
    # Create a test collection
    collection = client.create_collection(
        name="test_conversation_collection",
        description="Test collection for conversational memories"
    )
    print(f"✅ Created collection: {collection.name} (ID: {collection.id})")
    
    # List collections
    collections = client.list_collections()
    print(f"✅ Found {len(collections)} collections")
    
    return collection.id

def test_memory_storage():
    """Test storing individual memories"""
    print("\n🧪 Testing individual memory storage...")
    
    client = Nebula()
    
    # Create a collection for testing with unique name
    import time
    unique_name = f"test_memory_collection_{int(time.time())}"
    collection = client.create_collection(
        name=unique_name,
        description="Test collection for individual memories"
    )
    
    # Store a simple memory
    memory = client.store(
        agent_id="test_agent_1",
        content="This is a test memory about machine learning concepts.",
        metadata={"topic": "machine_learning", "importance": "high"},
        collection_id=collection.id,
        conversation_id="conv_123",
        timestamp="2024-01-15T10:30:00Z",
        speaker="user"
    )
    print(f"✅ Stored memory: {memory.id}")
    print(f"   Content: {memory.content[:50]}...")
    print(f"   Metadata: {memory.metadata}")
    
    return collection.id, memory.id

def test_conversation_storage():
    """Test storing conversation memories"""
    print("\n🧪 Testing conversation storage...")
    
    client = Nebula()
    
    # Create a collection for testing with unique name
    import time
    unique_name = f"test_conversation_collection_2_{int(time.time())}"
    collection = client.create_collection(
        name=unique_name,
        description="Test collection for conversation memories"
    )
    
    # Sample conversation data
    conversation = [
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "speaker": "user",
            "text": "What is machine learning?"
        },
        {
            "timestamp": "2024-01-15T10:30:05Z",
            "speaker": "assistant",
            "text": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed."
        },
        {
            "timestamp": "2024-01-15T10:30:10Z",
            "speaker": "user",
            "text": "Can you give me an example?"
        },
        {
            "timestamp": "2024-01-15T10:30:15Z",
            "speaker": "assistant",
            "text": "Sure! A common example is email spam detection. The system learns from labeled examples of spam and non-spam emails to classify new emails automatically."
        }
    ]
    
    # Store conversation
    memories = client.store_conversation(
        agent_id="test_agent_2",
        conversation=conversation,
        metadata={"topic": "machine_learning", "conversation_type": "qa"},
        collection_id=collection.id,
        batch_size=2  # Store 2 messages per document
    )
    print(f"✅ Stored {len(memories)} conversation memories")
    for i, memory in enumerate(memories):
        print(f"   Memory {i+1}: {memory.id}")
        print(f"   Content preview: {memory.content[:100]}...")
    
    return collection.id

def test_retrieval():
    """Test memory retrieval"""
    print("\n🧪 Testing memory retrieval...")
    
    client = Nebula()
    
    # Create a collection and store some test data with unique name
    import time
    unique_name = f"test_retrieval_collection_{int(time.time())}"
    collection = client.create_collection(
        name=unique_name,
        description="Test collection for retrieval"
    )
    
    # Store multiple memories
    test_memories = [
        "Machine learning algorithms can be supervised or unsupervised.",
        "Deep learning uses neural networks with multiple layers.",
        "Natural language processing helps computers understand human language.",
        "Computer vision enables machines to interpret visual information."
    ]
    
    for i, content in enumerate(test_memories):
        memory = client.store(
            agent_id="test_agent_3",
            content=content,
            metadata={"topic": "ai", "index": i},
            collection_id=collection.id
        )
        print(f"   Stored memory {i+1}: {memory.id}")
    
    # Test retrieval
    results = client.retrieve(
        agent_id="test_agent_3",
        query="What is deep learning?",
        limit=3,
        collection_id=collection.id
    )
    
    print(f"✅ Retrieved {len(results)} results")
    for i, result in enumerate(results):
        print(f"   Result {i+1}: {result.content[:80]}... (score: {result.score:.3f})")
    
    return collection.id

def test_chat():
    """Test chat functionality"""
    print("\n🧪 Testing chat functionality...")
    
    client = Nebula()
    
    # Create a collection and store some context with unique name
    import time
    unique_name = f"test_chat_collection_{int(time.time())}"
    collection = client.create_collection(
        name=unique_name,
        description="Test collection for chat"
    )
    
    # Store some context about AI
    context_memories = [
        "Artificial Intelligence (AI) is a broad field of computer science focused on creating systems that can perform tasks requiring human intelligence.",
        "Machine learning is a subset of AI that enables computers to learn from data without explicit programming.",
        "Deep learning is a type of machine learning that uses neural networks with multiple layers to process complex patterns."
    ]
    
    for content in context_memories:
        client.store(
            agent_id="test_chat_agent",
            content=content,
            collection_id=collection.id
        )
    
    # Test chat
    response = client.chat(
        agent_id="test_chat_agent",
        message="Explain the relationship between AI, machine learning, and deep learning.",
        collection_id=collection.id,
        model="gpt-4.1-mini",
        temperature=0.7
    )
    
    print(f"✅ Chat response: {response.content[:200]}...")
    print(f"   Agent ID: {response.agent_id}")
    print(f"   Conversation ID: {response.conversation_id}")
    
    return collection.id

def test_search():
    """Test general search functionality"""
    print("\n🧪 Testing general search...")
    
    client = Nebula()
    
    # Create a collection and store diverse content with unique name
    import time
    unique_name = f"test_search_collection_{int(time.time())}"
    collection = client.create_collection(
        name=unique_name,
        description="Test collection for search"
    )
    
    # Store diverse content
    diverse_content = [
        "Python is a popular programming language for data science and machine learning.",
        "JavaScript is widely used for web development and creating interactive websites.",
        "SQL is essential for database management and data querying.",
        "Docker helps with containerization and deployment of applications."
    ]
    
    for content in diverse_content:
        client.store(
            agent_id="test_search_agent",
            content=content,
            collection_id=collection.id
        )
    
    # Test search
    results = client.search(
        query="programming languages for data science",
        limit=2,
        filters={"collection_ids": [collection.id]}
    )
    
    print(f"✅ Search returned {len(results)} results")
    for i, result in enumerate(results):
        print(f"   Result {i+1}: {result.content[:80]}... (score: {result.score:.3f})")
    
    return collection.id

def test_collection_memories():
    """Test getting memories from a collection using documents"""
    print("\n🧪 Testing collection memories retrieval...")
    
    client = Nebula()
    
    # Create a collection and add some memories with unique name
    import time
    unique_name = f"test_collection_memories_{int(time.time())}"
    collection = client.create_collection(
        name=unique_name,
        description="Test collection for memory retrieval"
    )
    
    # Add some memories to the collection
    for i in range(3):
        client.store(
            agent_id="test_collection_agent",
            content=f"Test memory {i+1} for collection testing.",
            collection_id=collection.id
        )
    
    # Get memories from the collection using documents endpoint
    memories = client.get_collection_memories(collection.id, limit=10)
    print(f"✅ Retrieved {len(memories)} memories from collection using documents endpoint")
    for i, memory in enumerate(memories):
        print(f"   Memory {i+1}: {memory.content[:50]}...")
        print(f"   Engram ID: {memory.id}")
    
    return collection.id

def cleanup_test_collections(collection_ids: List[str]):
    """Clean up test collections"""
    print("\n🧹 Cleaning up test collections...")
    
    client = Nebula()
    
    for collection_id in collection_ids:
        try:
            client.delete_collection(collection_id)
            print(f"✅ Deleted collection: {collection_id}")
        except Exception as e:
            print(f"⚠️  Failed to delete collection {collection_id}: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Nebula Client SDK Tests (Documents Endpoint)")
    print("=" * 60)
    
    collection_ids = []
    
    try:
        # Run tests
        collection_ids.append(test_collection_management())
        collection_ids.append(test_memory_storage()[0])  # Get collection ID from tuple
        collection_ids.append(test_conversation_storage())
        collection_ids.append(test_retrieval())
        collection_ids.append(test_chat())
        collection_ids.append(test_search())
        collection_ids.append(test_collection_memories())
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if collection_ids:
            cleanup_test_collections(collection_ids)
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main() 