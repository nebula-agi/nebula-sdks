import os
import time
import uuid

import pytest

from nebula import Nebula

API_KEY = os.environ.get("NEBULA_API_KEY")

# Skip all tests in this module if NEBULA_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not API_KEY, reason="NEBULA_API_KEY environment variable not set"
)


@pytest.fixture(scope="module")
def client():
    return Nebula(api_key=API_KEY)


@pytest.fixture(scope="module")
def test_collection(client):
    # Use a unique name for the test collection
    name = f"test_sdk_collection_{uuid.uuid4()}"
    description = "SDK test collection for memory isolation"
    collection = client.create_collection(name=name, description=description)
    yield collection
    # Cleanup: delete the collection
    try:
        client.delete_collection(collection.id)
    except Exception:
        pass


@pytest.fixture(scope="module")
def other_collection(client):
    name = f"test_sdk_other_collection_{uuid.uuid4()}"
    description = "SDK test other collection for memory isolation"
    collection = client.create_collection(name=name, description=description)
    yield collection
    try:
        client.delete_collection(collection.id)
    except Exception:
        pass


def test_collection_creation_and_listing(client, test_collection):
    # List collections and verify the test collection exists
    collections = client.list_collections()
    ids = [c.id for c in collections]
    assert test_collection.id in ids
    found = [c for c in collections if c.id == test_collection.id][0]
    assert found.name == test_collection.name


def test_memory_isolation(client, test_collection, other_collection):
    # Store a memory in test_collection
    content = f"This is a test memory for {test_collection.id}"
    memory_id = client.store_memory(
        collection_id=test_collection.id,
        content=content,
        metadata={"purpose": "isolation-test"},
    )
    # Wait for ingestion (if async)
    time.sleep(2)
    # Retrieve memories for test_collection
    memories = client.list_memories(collection_ids=[test_collection.id], limit=10)
    assert any(content in (m.content or "") for m in memories), (
        "Memory not found in correct collection"
    )
    # Retrieve memories for other_collection (should NOT find the above)
    other_memories = client.list_memories(
        collection_ids=[other_collection.id], limit=10
    )
    assert all(content not in (m.content or "") for m in other_memories), (
        "Memory leaked to other collection!"
    )


def test_memory_search(client, test_collection):
    # Store a unique memory
    unique_phrase = f"searchable-phrase-{uuid.uuid4()}"
    client.store_memory(
        collection_id=test_collection.id,
        content=f"This memory contains {unique_phrase}",
        metadata={"purpose": "search-test"},
    )
    time.sleep(2)
    # Search for the unique phrase
    results = client.search(
        query=unique_phrase,
        collection_ids=[test_collection.id],
        limit=5,
    )
    assert any(unique_phrase in (r.content or "") for r in results), (
        "Search did not return expected memory"
    )


def test_cleanup(client, test_collection, other_collection):
    # Delete collections and verify they're gone
    client.delete_collection(test_collection.id)
    client.delete_collection(other_collection.id)
    collections = client.list_collections()
    assert test_collection.id not in [c.id for c in collections]
    assert other_collection.id not in [c.id for c in collections]
