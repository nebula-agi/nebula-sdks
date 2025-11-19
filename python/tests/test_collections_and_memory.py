import os
import time
import uuid

import pytest

from nebula import Nebula

API_KEY = os.environ.get("NEBULA_API_KEY")


@pytest.fixture(scope="module")
def client():
    assert API_KEY, "NEBULA_API_KEY must be set"
    return Nebula(api_key=API_KEY)


@pytest.fixture(scope="module")
def test_collection(client):
    # Use a unique name for the test collection
    name = f"test_sdk_collection_{uuid.uuid4()}"
    description = "SDK test collection for memory isolation"
    collection = client.create_cluster(name=name, description=description)
    yield collection
    # Cleanup: delete the collection
    try:
        client.delete_cluster(collection.id)
    except Exception:
        pass


@pytest.fixture(scope="module")
def other_collection(client):
    name = f"test_sdk_other_collection_{uuid.uuid4()}"
    description = "SDK test other collection for memory isolation"
    collection = client.create_cluster(name=name, description=description)
    yield collection
    try:
        client.delete_cluster(collection.id)
    except Exception:
        pass


def test_collection_creation_and_listing(client, test_collection):
    # List collections and verify the test collection exists
    collections = client.list_clusters()
    ids = [c.id for c in collections]
    assert test_collection.id in ids
    found = [c for c in collections if c.id == test_collection.id][0]
    assert found.name == test_collection.name


def test_memory_isolation(client, test_collection, other_collection):
    # Store a memory in test_collection
    agent_id = f"test-agent-{uuid.uuid4()}"
    content = f"This is a test memory for {test_collection.id}"
    memory = client.store(
        agent_id=agent_id,
        content=content,
        collection_id=test_collection.id,
        metadata={"purpose": "isolation-test"},
    )
    # Wait for ingestion (if async)
    time.sleep(2)
    # Retrieve memories for test_collection
    memories = client.get_cluster_memories(collection_id=test_collection.id, limit=10)
    assert any(content in m.content for m in memories), (
        "Memory not found in correct collection"
    )
    # Retrieve memories for other_collection (should NOT find the above)
    other_memories = client.get_cluster_memories(
        collection_id=other_collection.id, limit=10
    )
    assert all(content not in m.content for m in other_memories), (
        "Memory leaked to other collection!"
    )


def test_memory_search(client, test_collection):
    # Store a unique memory
    agent_id = f"search-agent-{uuid.uuid4()}"
    unique_phrase = f"searchable-phrase-{uuid.uuid4()}"
    client.store(
        agent_id=agent_id,
        content=f"This memory contains {unique_phrase}",
        collection_id=test_collection.id,
        metadata={"purpose": "search-test"},
    )
    time.sleep(2)
    # Search for the unique phrase
    results = client.retrieve(
        agent_id=agent_id,  # Add the required agent_id parameter
        query=unique_phrase,
        collection_id=test_collection.id,
        limit=5,
    )
    assert any(unique_phrase in r.content for r in results), (
        "Search did not return expected memory"
    )


def test_cleanup(client, test_collection, other_collection):
    # Delete collections and verify they're gone
    client.delete_cluster(test_collection.id)
    client.delete_cluster(other_collection.id)
    collections = client.list_clusters()
    assert test_collection.id not in [c.id for c in collections]
    assert other_collection.id not in [c.id for c in collections]
