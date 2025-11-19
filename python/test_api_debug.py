#!/usr/bin/env python3
"""
Comprehensive API Debug Test
Tests each Nebula API endpoint individually to identify what works and what doesn't.
"""

import json
import os
import time
import uuid

from nebula import Nebula


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"🔍 {title}")
    print(f"{'=' * 60}")


def print_result(success, message, details=None):
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    if details:
        print(f"   Details: {details}")


def test_api_connection():
    """Test basic API connection"""
    print_section("API Connection Test")

    api_key = os.environ.get("NEBULA_API_KEY")
    if not api_key:
        print_result(False, "NEBULA_API_KEY not set")
        return None

    try:
        client = Nebula(api_key=api_key)
        print_result(True, "Connected to Nebula API")
        return client
    except Exception as e:
        print_result(False, f"Failed to connect: {e}")
        return None


def test_collections(client):
    """Test collection management"""
    print_section("Collection Management Tests")

    # Test 1: List collections
    try:
        collections = client.list_clusters(limit=10)
        print_result(True, f"List collections: Found {len(collections)} collections")
        for i, col in enumerate(collections[:3]):
            print(f"   {i + 1}. {col.name} (ID: {col.id})")
    except Exception as e:
        print_result(False, f"List collections failed: {e}")

    # Test 2: Create collection
    test_name = f"debug-test-{uuid.uuid4()}"
    try:
        cluster = client.create_cluster(
            name=test_name, description="Debug test collection"
        )
        print_result(True, f"Create collection: {cluster.name} (ID: {cluster.id})")
        test_collection_id = cluster.id
    except Exception as e:
        print_result(False, f"Create collection failed: {e}")
        test_collection_id = None

    # Test 3: Get specific collection
    if test_collection_id:
        try:
            cluster = client.get_cluster(test_collection_id)
            print_result(True, f"Get collection: {cluster.name}")
        except Exception as e:
            print_result(False, f"Get collection failed: {e}")

    return test_collection_id


def test_document_ingestion(client, collection_id):
    """Test document ingestion and status checking"""
    print_section("Document Ingestion Tests")

    # Test 1: Upload document
    test_content = f"Debug test content {uuid.uuid4()}"
    try:
        # Test direct API call first
        import httpx

        url = f"{client.base_url}/v1/memories"
        headers = {"Authorization": f"Bearer {client.api_key}"}
        files = {
            "raw_text": (None, test_content),
            "metadata": (None, json.dumps({"test": True, "debug": True})),
        }
        if collection_id:
            files["collection_ids"] = (None, f'["{collection_id}"]')

        resp = httpx.post(url, files=files, headers=headers)
        print(f"   Direct API Response: {resp.status_code}")
        print(f"   Response Body: {resp.text[:200]}...")

        if resp.status_code in (200, 202):
            data = resp.json()
            print_result(True, f"Document upload: Status {resp.status_code}")

            # Test 2: Check ingestion status
            if "ingestion_id" in data:
                ingestion_id = data["ingestion_id"]
            elif "results" in data and "task_id" in data["results"]:
                ingestion_id = data["results"]["task_id"]
            else:
                print_result(False, "No ingestion_id or task_id found in response")
                return

            print(f"   Ingestion ID: {ingestion_id}")

            # Test 3: Poll for completion
            for i in range(10):
                try:
                    status_resp = httpx.get(
                        f"{client.base_url}/v1/ingestions/{ingestion_id}",
                        headers=headers,
                    )
                    print(f"   Poll {i + 1}: Status {status_resp.status_code}")
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        print(f"   Status Data: {json.dumps(status_data, indent=2)}")
                        if status_data.get("status") == "completed":
                            print_result(True, "Ingestion completed successfully")
                            break
                        elif status_data.get("status") == "failed":
                            print_result(False, f"Ingestion failed: {status_data}")
                            break
                    elif status_resp.status_code == 404:
                        print_result(False, "Ingestion status endpoint not found (404)")
                        break
                    else:
                        print(f"   Unexpected status: {status_resp.status_code}")
                except Exception as e:
                    print_result(False, f"Status check failed: {e}")
                    break
                time.sleep(1)
            else:
                print_result(False, "Ingestion polling timed out")
        else:
            print_result(False, f"Document upload failed: {resp.status_code}")

    except Exception as e:
        print_result(False, f"Document ingestion test failed: {e}")


def test_memory_operations(client, collection_id):
    """Test memory operations"""
    print_section("Memory Operations Tests")

    # Test 1: Store memory using SDK
    test_agent = f"debug-agent-{uuid.uuid4()}"
    test_content = f"Debug memory content {uuid.uuid4()}"

    try:
        memory = client.store(
            agent_id=test_agent,
            content=test_content,
            metadata={"test": True, "debug": True},
            collection_id=collection_id,
        )
        print_result(True, f"Store memory: {memory.content[:50]}...")
        print(f"   Memory ID: {memory.id}")
    except Exception as e:
        print_result(False, f"Store memory failed: {e}")

    # Test 2: List agent memories
    try:
        memories = client.list_agent_memories(agent_id=test_agent, limit=10)
        print_result(True, f"List agent memories: Found {len(memories)} memories")
        for i, mem in enumerate(memories[:3]):
            print(f"   {i + 1}. {mem.content[:50]}...")
    except Exception as e:
        print_result(False, f"List agent memories failed: {e}")

    # Test 3: Get cluster memories
    if collection_id:
        try:
            memories = client.get_cluster_memories(
                collection_id=collection_id, limit=10
            )
            print_result(True, f"Get cluster memories: Found {len(memories)} memories")
        except Exception as e:
            print_result(False, f"Get cluster memories failed: {e}")


def test_search_operations(client, collection_id):
    """Test search operations"""
    print_section("Search Operations Tests")

    # Test 1: Search without filters
    try:
        results = client.search(query="debug", limit=5)
        print_result(True, f"Search: Found {len(results)} results")
        for i, result in enumerate(results[:3]):
            print(
                f"   {i + 1}. Score: {result.score}, Content: {result.content[:50]}..."
            )
    except Exception as e:
        print_result(False, f"Search failed: {e}")

    # Test 2: Retrieve with agent_id
    test_agent = f"debug-agent-{uuid.uuid4()}"
    try:
        results = client.retrieve(agent_id=test_agent, query="debug", limit=5)
        print_result(True, f"Retrieve: Found {len(results)} results")
    except Exception as e:
        print_result(False, f"Retrieve failed: {e}")


def test_chat_operations(client, collection_id):
    """Test chat operations"""
    print_section("Chat Operations Tests")

    test_agent = f"debug-chat-agent-{uuid.uuid4()}"

    # Test 1: Basic chat
    try:
        response = client.chat(
            agent_id=test_agent,
            message="Hello, this is a debug test",
            model="gpt-4",
            temperature=0.7,
        )
        print_result(True, f"Basic chat: {response.content[:50]}...")
    except Exception as e:
        print_result(False, f"Basic chat failed: {e}")

    # Test 2: Chat with cluster filtering
    if collection_id:
        try:
            response = client.chat(
                agent_id=test_agent,
                message="Hello with cluster filtering",
                collection_id=collection_id,
                model="gpt-4",
                temperature=0.7,
            )
            print_result(True, f"Chat with cluster: {response.content[:50]}...")
        except Exception as e:
            print_result(False, f"Chat with cluster failed: {e}")


def test_cleanup(client, collection_id):
    """Clean up test resources"""
    print_section("Cleanup")

    if collection_id:
        try:
            client.delete_cluster(collection_id)
            print_result(True, f"Deleted test cluster: {collection_id}")
        except Exception as e:
            print_result(False, f"Failed to delete cluster: {e}")


def main():
    print("🚀 Nebula API Debug Test")
    print("This will test each API endpoint individually to identify issues.")

    # Test 1: Connection
    client = test_api_connection()
    if not client:
        return

    # Test 2: Collections
    collection_id = test_collections(client)

    # Test 3: Document ingestion
    test_document_ingestion(client, collection_id)

    # Test 4: Memory operations
    test_memory_operations(client, collection_id)

    # Test 5: Search operations
    test_search_operations(client, collection_id)

    # Test 6: Chat operations
    test_chat_operations(client, collection_id)

    # Test 7: Cleanup
    test_cleanup(client, collection_id)

    print_section("Test Summary")
    print("Check the results above to see what's working and what's not.")
    print("Look for ❌ marks to identify problematic endpoints.")


if __name__ == "__main__":
    main()
