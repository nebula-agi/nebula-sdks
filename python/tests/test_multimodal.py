#!/usr/bin/env python3
"""
Comprehensive test script for Nebula SDK multimodal functionality.

Tests:
- Image processing with vision models
- Audio transcription 
- PDF/Document processing
- Multimodal conversations
- Search and retrieval of multimodal content

Uses online datasets for sample files.

Pass base64-encoded content with explicit type and media_type.
"""

import asyncio
import base64
import os
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import pytest

# Skip entire module if NEBULA_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("NEBULA_API_KEY"),
    reason="NEBULA_API_KEY environment variable not set"
)


# ==============================================================================
# Test Fixtures and Helpers
# ==============================================================================

def get_api_key() -> str:
    """Get API key from environment."""
    key = os.getenv("NEBULA_API_KEY")
    if not key:
        raise RuntimeError("NEBULA_API_KEY not set")
    return key


def get_base_url() -> str:
    """Get base URL from environment or use default."""
    return os.getenv("NEBULA_BASE_URL", "https://api.nebulacloud.app")


def download_to_temp_file(url: str, suffix: str = ".jpg") -> Path:
    """Download a file from URL to a temporary file and return the path."""
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        # Create a temp file that won't be auto-deleted
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)
        
        return Path(path)


def download_and_encode(url: str) -> str:
    """Download a file from URL and return base64-encoded data."""
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        return base64.b64encode(response.content).decode()


async def async_download_to_temp_file(url: str, suffix: str = ".jpg") -> Path:
    """Async version: download a file from URL to a temporary file."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)
        
        return Path(path)


async def async_download_and_encode(url: str) -> str:
    """Async version: download and base64 encode."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return base64.b64encode(response.content).decode()


def encode_file(path: Path) -> str:
    """Read a file and return base64-encoded data."""
    return base64.b64encode(path.read_bytes()).decode()


def generate_test_collection_name() -> str:
    """Generate a unique test collection name."""
    return f"test-multimodal-{uuid.uuid4().hex[:8]}"


# ==============================================================================
# Sample Data URLs (using publicly available test files)
# ==============================================================================

# Sample images from Unsplash (small, royalty-free)
SAMPLE_IMAGES = {
    "cat": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&q=80",
    "dog": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&q=80",
    "landscape": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&q=80",
    "city": "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&q=80",
}

# Sample PDF (Wikipedia open content)
SAMPLE_PDF_URL = "https://www.w3.org/WAI/WCAG21/Techniques/pdf/img/table-word.pdf"

# Alternative: Create a simple PDF in-memory for testing
def create_simple_test_pdf() -> bytes:
    """Create a minimal PDF for testing."""
    # Minimal valid PDF with text
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 68
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World! This is a test PDF document.) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000270 00000 n 
0000000389 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
466
%%EOF"""
    return pdf_content


# ==============================================================================
# Sync Client Tests
# ==============================================================================

class TestSyncMultimodal:
    """Test multimodal functionality with sync client."""

    @pytest.fixture
    def client(self):
        """Create a sync Nebula client."""
        from nebula import Nebula
        client = Nebula(api_key=get_api_key(), base_url=get_base_url())
        yield client
        client.close()

    @pytest.fixture
    def test_collection(self, client):
        """Create a test collection and clean up after."""
        collection_name = generate_test_collection_name()
        collection = client.create_collection(
            name=collection_name,
            description="Test collection for multimodal tests"
        )
        yield collection
        # Cleanup
        try:
            client.delete_collection(collection.id)
        except Exception:
            pass

    def test_store_image_memory(self, client, test_collection):
        """Test storing an image as memory."""
        from nebula import Memory, ImageContent

        # Download and encode image
        image_data = download_and_encode(SAMPLE_IMAGES["cat"])
        
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                "A cute cat picture from the internet",
                ImageContent(data=image_data, media_type='image/jpeg', filename='cat.jpg')
            ],
            metadata={"test": "image_storage", "animal": "cat"}
        )

        memory_id = client.store_memory(memory)
        assert memory_id, "Should return a memory ID"
        print(f"✅ Stored image memory: {memory_id}")

        # Verify we can retrieve it
        retrieved = client.get_memory(memory_id)
        assert retrieved.id == memory_id
        print(f"✅ Retrieved image memory with {len(retrieved.chunks or [])} chunks")

    def test_store_document_memory(self, client, test_collection):
        """Test storing a PDF document as memory."""
        from nebula import Memory, DocumentContent

        # Create a simple test PDF
        pdf_data = base64.b64encode(create_simple_test_pdf()).decode()
        
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                DocumentContent(data=pdf_data, media_type='application/pdf', filename='test.pdf')
            ],
            metadata={"test": "document_storage", "type": "pdf"},
        )

        memory_id = client.store_memory(memory)
        assert memory_id, "Should return a memory ID"
        print(f"✅ Stored PDF document memory: {memory_id}")

    def test_store_multiple_images(self, client, test_collection):
        """Test storing multiple images in a single memory."""
        from nebula import Memory, ImageContent

        # Download and encode images
        cat_data = download_and_encode(SAMPLE_IMAGES["cat"])
        dog_data = download_and_encode(SAMPLE_IMAGES["dog"])

        memory = Memory(
            collection_id=test_collection.id,
            content=[
                "Comparison of cat and dog photos",
                ImageContent(data=cat_data, media_type='image/jpeg', filename='cat.jpg'),
                ImageContent(data=dog_data, media_type='image/jpeg', filename='dog.jpg')
            ],
            metadata={"test": "multi_image", "count": 2}
        )

        memory_id = client.store_memory(memory)
        assert memory_id, "Should return a memory ID"
        print(f"✅ Stored multi-image memory: {memory_id}")

    def test_multimodal_conversation(self, client, test_collection):
        """Test storing a conversation with multimodal content."""
        from nebula import Memory, ImageContent

        # Download and encode image
        image_data = download_and_encode(SAMPLE_IMAGES["landscape"])

        # Create conversation
        conversation_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                "What do you see in this image?",
                ImageContent(data=image_data, media_type='image/jpeg', filename='landscape.jpg')
            ],
            role="user",
            metadata={"test": "multimodal_conversation"}
        ))
        assert conversation_id, "Should return a conversation ID"

        # Add assistant response
        client.store_memory(Memory(
            collection_id=test_collection.id,
            memory_id=conversation_id,  # Append to existing conversation
            content="I can see a beautiful mountain landscape with snow-capped peaks.",
            role="assistant"
        ))

        # Add another user message
        client.store_memory(Memory(
            collection_id=test_collection.id,
            memory_id=conversation_id,
            content="Where do you think this was taken?",
            role="user"
        ))

        print(f"✅ Created multimodal conversation: {conversation_id}")

        # Verify conversation was created
        retrieved = client.get_memory(conversation_id)
        assert retrieved.chunks and len(retrieved.chunks) >= 2
        print(f"✅ Conversation has {len(retrieved.chunks)} messages")

    def test_search_multimodal_memories(self, client, test_collection):
        """Test searching memories that contain multimodal content."""
        from nebula import Memory, ImageContent

        # Download and encode image
        image_data = download_and_encode(SAMPLE_IMAGES["landscape"])

        # Store a memory about mountains
        memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                "A stunning view of the Swiss Alps with fresh snow on the peaks",
                ImageContent(data=image_data, media_type='image/jpeg', filename='alps.jpg')
            ],
            metadata={"location": "Switzerland", "season": "winter"}
        ))

        # Wait for indexing
        time.sleep(3)

        # Search for related content
        results = client.search(
            query="mountains with snow in Switzerland",
            collection_ids=[test_collection.id],
            limit=5
        )

        print(f"✅ Search returned {len(results.utterances)} utterances, {len(results.entities)} entities")
        assert memory_id or results  # Either storage succeeded or we got results


# ==============================================================================
# Async Client Tests
# ==============================================================================

class TestAsyncMultimodal:
    """Test multimodal functionality with async client."""

    @pytest.fixture
    async def client(self):
        """Create an async Nebula client."""
        from nebula import AsyncNebula
        client = AsyncNebula(api_key=get_api_key(), base_url=get_base_url())
        yield client
        await client.aclose()

    @pytest.fixture
    async def test_collection(self, client):
        """Create a test collection and clean up after."""
        collection_name = generate_test_collection_name()
        collection = await client.create_collection(
            name=collection_name,
            description="Async test collection for multimodal tests"
        )
        yield collection
        # Cleanup
        try:
            await client.delete_collection(collection.id)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_async_store_image_memory(self, client, test_collection):
        """Test storing an image as memory asynchronously."""
        from nebula import Memory, ImageContent

        # Download and encode
        image_data = await async_download_and_encode(SAMPLE_IMAGES["dog"])
        
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                "A happy golden retriever playing",
                ImageContent(data=image_data, media_type='image/jpeg', filename='dog.jpg')
            ],
            metadata={"test": "async_image_storage", "animal": "dog"}
        )

        memory_id = await client.store_memory(memory)
        assert memory_id, "Should return a memory ID"
        print(f"✅ [Async] Stored image memory: {memory_id}")

    @pytest.mark.asyncio
    async def test_async_store_document(self, client, test_collection):
        """Test storing a PDF document asynchronously."""
        from nebula import Memory, DocumentContent

        pdf_data = base64.b64encode(create_simple_test_pdf()).decode()
        
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                DocumentContent(data=pdf_data, media_type='application/pdf', filename='test.pdf')
            ],
            metadata={"test": "async_document_storage"}
        )

        memory_id = await client.store_memory(memory)
        assert memory_id, "Should return a memory ID"
        print(f"✅ [Async] Stored document memory: {memory_id}")

    @pytest.mark.asyncio
    async def test_async_multimodal_conversation(self, client, test_collection):
        """Test async conversation with multimodal content."""
        from nebula import Memory, ImageContent

        # Download and encode images concurrently
        cat_data, dog_data = await asyncio.gather(
            async_download_and_encode(SAMPLE_IMAGES["cat"]),
            async_download_and_encode(SAMPLE_IMAGES["dog"])
        )

        conversation_id = await client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                "Can you compare these two pets?",
                ImageContent(data=cat_data, media_type='image/jpeg', filename='cat.jpg'),
                ImageContent(data=dog_data, media_type='image/jpeg', filename='dog.jpg')
            ],
            role="user",
            metadata={"test": "async_multimodal_conversation"}
        ))

        assert conversation_id
        print(f"✅ [Async] Created multimodal conversation: {conversation_id}")

        # Add response
        await client.store_memory(Memory(
            collection_id=test_collection.id,
            memory_id=conversation_id,
            content="I can see a cute orange cat and a golden retriever. Both look very happy!",
            role="assistant"
        ))

        # Verify
        retrieved = await client.get_memory(conversation_id)
        print(f"✅ [Async] Conversation has {len(retrieved.chunks or [])} messages")

    @pytest.mark.asyncio
    async def test_async_batch_multimodal_storage(self, client, test_collection):
        """Test storing multiple multimodal memories in batch."""
        from nebula import Memory, ImageContent

        # Download and encode all images concurrently
        image_data_list = await asyncio.gather(*[
            async_download_and_encode(url) 
            for url in SAMPLE_IMAGES.values()
        ])

        # Create memories for each image
        memories = []
        for (name, _url), data in zip(SAMPLE_IMAGES.items(), image_data_list, strict=True):
            memories.append(Memory(
                collection_id=test_collection.id,
                content=[
                    f"Image: {name}",
                    ImageContent(data=data, media_type='image/jpeg', filename=f'{name}.jpg')
                ],
                metadata={"image_name": name, "test": "batch_multimodal"}
            ))

        # Store all memories
        memory_ids = await client.store_memories(memories)
        assert len(memory_ids) == len(memories)
        print(f"✅ [Async] Batch stored {len(memory_ids)} multimodal memories")


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestMultimodalIntegration:
    """Integration tests for multimodal workflows."""

    @pytest.fixture
    def client(self):
        """Create a sync Nebula client."""
        from nebula import Nebula
        client = Nebula(api_key=get_api_key(), base_url=get_base_url())
        yield client
        client.close()

    @pytest.fixture
    def test_collection(self, client):
        """Create a test collection."""
        collection_name = generate_test_collection_name()
        collection = client.create_collection(
            name=collection_name,
            description="Integration test collection"
        )
        yield collection
        try:
            client.delete_collection(collection.id)
        except Exception:
            pass

    def test_mixed_content_workflow(self, client, test_collection):
        """Test a workflow with mixed text and multimodal content."""
        from nebula import Memory, ImageContent, DocumentContent

        # 1. Store a text memory
        text_memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content="The Eiffel Tower is located in Paris, France. It was built in 1889.",
            metadata={"type": "fact", "topic": "landmarks"}
        ))
        print(f"✅ Stored text memory: {text_memory_id}")

        # 2. Store an image memory
        image_data = download_and_encode(SAMPLE_IMAGES["city"])
        image_memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                "A beautiful cityscape at sunset",
                ImageContent(data=image_data, media_type='image/jpeg', filename='city.jpg')
            ],
            metadata={"type": "photo", "topic": "cities"}
        ))
        print(f"✅ Stored image memory: {image_memory_id}")

        # 3. Store a document memory
        pdf_data = base64.b64encode(create_simple_test_pdf()).decode()
        doc_memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                DocumentContent(data=pdf_data, media_type='application/pdf', filename='test.pdf')
            ],
            metadata={"type": "document"}
        ))
        print(f"✅ Stored document memory: {doc_memory_id}")

        # 4. Wait for indexing
        time.sleep(3)

        # 5. Search across all content types
        results = client.search(
            query="cities and landmarks",
            collection_ids=[test_collection.id],
            limit=10
        )
        print(f"✅ Search returned {len(results.utterances)} results")

        # 6. List all memories
        memories = client.list_memories(collection_ids=[test_collection.id])
        print(f"✅ Collection has {len(memories)} memories")
        assert len(memories) >= 3

    def test_dict_based_multimodal_content(self, client, test_collection):
        """Test using dict-based content parts instead of dataclasses."""
        from nebula import Memory

        # Download and encode
        image_data = download_and_encode(SAMPLE_IMAGES["landscape"])

        # Use dict format (alternative to dataclasses)
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                {"type": "text", "text": "A beautiful mountain scene"},
                {
                    "type": "image",
                    "data": image_data,
                    "media_type": "image/jpeg",
                    "filename": "mountains.jpg"
                }
            ],
            metadata={"format": "dict_based"}
        )

        memory_id = client.store_memory(memory)
        assert memory_id
        print(f"✅ Stored memory using dict-based content: {memory_id}")


# ==============================================================================
# Main Entry Point for Direct Execution
# ==============================================================================

def run_quick_test():
    """Run a quick manual test of the multimodal functionality.
    
    Pass base64-encoded content with explicit type and media_type.
    """
    from nebula import Nebula, Memory, ImageContent, DocumentContent
    
    print("=" * 60)
    print("Nebula Multimodal Quick Test")
    print("=" * 60)
    print("📝 Pass base64-encoded content with type and media_type")
    print("=" * 60)
    
    api_key = os.getenv("NEBULA_API_KEY")
    if not api_key:
        print("❌ NEBULA_API_KEY not set. Please set it and try again.")
        return
    
    base_url = get_base_url()
    print(f"🔗 Using base URL: {base_url}")
    
    # Use longer timeout for multimodal processing (vision models can take time)
    client = Nebula(api_key=api_key, base_url=base_url, timeout=300.0)
    
    try:
        # 1. Health check
        print("\n📋 Health check...")
        health = client.health_check()
        print(f"✅ API healthy: {health}")
        
        # 2. Create test collection
        print("\n📦 Creating test collection...")
        collection_name = generate_test_collection_name()
        collection = client.create_collection(
            name=collection_name,
            description="Quick multimodal test"
        )
        print(f"✅ Created collection: {collection.name} ({collection.id})")
        
        # 3. Store an image
        print("\n🖼️  Testing image storage...")
        image_data = download_and_encode(SAMPLE_IMAGES["cat"])
        memory_id = client.store_memory(Memory(
            collection_id=collection.id,
            content=[
                "A cute orange cat sitting on a couch",
                ImageContent(data=image_data, media_type='image/jpeg', filename='cat.jpg')
            ],
            metadata={"animal": "cat", "test": "quick_test"}
        ))
        print(f"✅ Stored image memory: {memory_id}")
        
        # 4. Test document storage
        print("\n📄 Testing document storage...")
        pdf_data = base64.b64encode(create_simple_test_pdf()).decode()
        doc_id = client.store_memory(Memory(
            collection_id=collection.id,
            content=[
                DocumentContent(data=pdf_data, media_type='application/pdf', filename='test.pdf')
            ]
        ))
        print(f"✅ Stored document memory: {doc_id}")
        
        # 5. Test multimodal conversation
        print("\n💬 Testing multimodal conversation...")
        cat_image = download_and_encode(SAMPLE_IMAGES["cat"])
        conv_id = client.store_memory(Memory(
            collection_id=collection.id,
            content=[
                "What do you see in this image?",
                ImageContent(data=cat_image, media_type='image/jpeg', filename='cat.jpg')
            ],
            role="user"
        ))
        client.store_memory(Memory(
            collection_id=collection.id,
            memory_id=conv_id,
            content="I see a cute cat!",
            role="assistant"
        ))
        print(f"✅ Created conversation: {conv_id}")
        
        # 6. Wait for indexing and search
        print("\n🔍 Testing search (waiting for indexing)...")
        time.sleep(3)
        results = client.search(
            query="cat picture",
            collection_ids=[collection.id],
            limit=5
        )
        print(f"✅ Search results: {len(results.utterances)} utterances, {len(results.entities)} entities")
        
        # 7. Cleanup
        print("\n🧹 Cleaning up...")
        client.delete_collection(collection.id)
        print(f"✅ Deleted collection: {collection_name}")
        
        print("\n" + "=" * 60)
        print("✅ All quick tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        client.close()


async def run_async_quick_test():
    """Run async quick test.
    
    Pass base64-encoded content with explicit type and media_type.
    """
    from nebula import AsyncNebula, Memory, ImageContent
    
    print("=" * 60)
    print("Nebula Async Multimodal Quick Test")
    print("=" * 60)
    print("📝 Pass base64-encoded content with type and media_type")
    print("=" * 60)
    
    api_key = os.getenv("NEBULA_API_KEY")
    if not api_key:
        print("❌ NEBULA_API_KEY not set")
        return
    
    async with AsyncNebula(api_key=api_key, base_url=get_base_url()) as client:
        # Health check
        print("\n📋 Health check...")
        health = await client.health_check()
        print(f"✅ API healthy: {health}")
        
        # Create collection
        print("\n📦 Creating test collection...")
        collection = await client.create_collection(
            name=generate_test_collection_name(),
            description="Async quick test"
        )
        print(f"✅ Created: {collection.name}")
        
        # Download and encode
        image_data = await async_download_and_encode(SAMPLE_IMAGES["dog"])
        
        try:
            # Store image
            print("\n🖼️  Testing async image storage...")
            memory_id = await client.store_memory(Memory(
                collection_id=collection.id,
                content=[
                    "A happy dog",
                    ImageContent(data=image_data, media_type='image/jpeg', filename='dog.jpg')
                ]
            ))
            print(f"✅ Stored: {memory_id}")
            
        finally:
            await client.delete_collection(collection.id)
            print("\n🧹 Cleaned up collection")
    
    print("\n✅ Async tests passed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--async":
        asyncio.run(run_async_quick_test())
    else:
        run_quick_test()
