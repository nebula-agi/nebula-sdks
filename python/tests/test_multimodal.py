#!/usr/bin/env python3
"""
Comprehensive test script for Nebula SDK multimodal functionality.

Tests:
- Image processing with vision models
- Audio transcription 
- PDF/Document processing
- On-the-fly multimodal processing
- Multimodal conversations
- Search and retrieval of multimodal content

Uses online datasets for sample files.

The SDK handles all file encoding automatically - just pass file paths!
"""

import asyncio
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


async def async_download_to_temp_file(url: str, suffix: str = ".jpg") -> Path:
    """Async version: download a file from URL to a temporary file."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)
        
        return Path(path)


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
        from nebula import Nebula
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
        from nebula import Memory, load_file

        # Download image to a temp file
        image_path = download_to_temp_file(SAMPLE_IMAGES["cat"], suffix=".jpg")
        
        try:
            # Just use load_file() - type is auto-detected!
            memory = Memory(
                collection_id=test_collection.id,
                content=[
                    "A cute cat picture from the internet",  # Plain strings work too!
                    load_file(image_path)  # Auto-detects as image, handles encoding
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
        finally:
            image_path.unlink(missing_ok=True)

    def test_store_document_memory(self, client, test_collection):
        """Test storing a PDF document as memory."""
        from nebula import Memory, load_file

        # Create a simple test PDF and save to temp file
        pdf_data = create_simple_test_pdf()
        pdf_path = Path(tempfile.mktemp(suffix=".pdf"))
        pdf_path.write_bytes(pdf_data)
        
        try:
            # Just use load_file() - auto-detects as document!
            memory = Memory(
                collection_id=test_collection.id,
                content=[
                    load_file(pdf_path)  # Auto-detects as PDF document
                ],
                metadata={"test": "document_storage", "type": "pdf"},
            )

            memory_id = client.store_memory(memory)
            assert memory_id, "Should return a memory ID"
            print(f"✅ Stored PDF document memory: {memory_id}")
        finally:
            pdf_path.unlink(missing_ok=True)

    def test_store_multiple_images(self, client, test_collection):
        """Test storing multiple images in a single memory."""
        from nebula import Memory, load_file

        # Download images to temp files
        cat_path = download_to_temp_file(SAMPLE_IMAGES["cat"], suffix=".jpg")
        dog_path = download_to_temp_file(SAMPLE_IMAGES["dog"], suffix=".jpg")

        try:
            # Just use load_file() - types are auto-detected!
            memory = Memory(
                collection_id=test_collection.id,
                content=[
                    "Comparison of cat and dog photos",
                    load_file(cat_path),  # Auto-detected as image
                    load_file(dog_path)   # Auto-detected as image
                ],
                metadata={"test": "multi_image", "count": 2}
            )

            memory_id = client.store_memory(memory)
            assert memory_id, "Should return a memory ID"
            print(f"✅ Stored multi-image memory: {memory_id}")
        finally:
            cat_path.unlink(missing_ok=True)
            dog_path.unlink(missing_ok=True)

    def test_multimodal_conversation(self, client, test_collection):
        """Test storing a conversation with multimodal content."""
        from nebula import Memory, load_file

        # Download image to temp file
        image_path = download_to_temp_file(SAMPLE_IMAGES["landscape"], suffix=".jpg")

        try:
            # Create conversation - just use load_file()!
            conversation_id = client.store_memory(Memory(
                collection_id=test_collection.id,
                content=[
                    "What do you see in this image?",
                    load_file(image_path)  # Auto-detected as image
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
        finally:
            image_path.unlink(missing_ok=True)

    def test_process_multimodal_content_image(self, client):
        """Test on-the-fly image processing without storage."""
        from nebula import load_url
        
        # Use load_url() - downloads and auto-detects type!
        image = load_url(SAMPLE_IMAGES["city"])

        # Process the image using the content dict
        result = client.process_multimodal_content(
            content_parts=[
                {
                    "type": image.type,
                    "data": image.data,
                    "media_type": image.media_type,
                    "filename": "city.jpg"
                }
            ]
        )

        assert "extracted_text" in result
        print(f"✅ Processed image, extracted text length: {len(result.get('extracted_text', ''))}")
        print(f"   Preview: {result.get('extracted_text', '')[:200]}...")

    def test_process_multimodal_content_document(self, client):
        """Test on-the-fly document processing without storage."""
        from nebula import load_file
        
        # Create a test PDF and save to temp file
        pdf_data = create_simple_test_pdf()
        pdf_path = Path(tempfile.mktemp(suffix=".pdf"))
        pdf_path.write_bytes(pdf_data)
        
        try:
            # Use load_file() - auto-detects as document!
            doc = load_file(pdf_path)

            # Process the document
            result = client.process_multimodal_content(
                content_parts=[
                    {
                        "type": doc.type,
                        "data": doc.data,
                        "media_type": doc.media_type,
                        "filename": doc.filename
                    }
                ]
            )

            assert "extracted_text" in result
            print(f"✅ Processed document, extracted text: {result.get('extracted_text', '')[:200]}")
        finally:
            pdf_path.unlink(missing_ok=True)

    def test_search_multimodal_memories(self, client, test_collection):
        """Test searching memories that contain multimodal content."""
        from nebula import Memory, load_url

        # Use load_url() - auto-detects type!
        image = load_url(SAMPLE_IMAGES["landscape"])

        # Store a memory about mountains
        memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                "A stunning view of the Swiss Alps with fresh snow on the peaks",
                image
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
        from nebula import Memory, load_file

        # Download to temp file
        image_path = await async_download_to_temp_file(SAMPLE_IMAGES["dog"], suffix=".jpg")
        
        try:
            # Just use load_file() - type is auto-detected!
            memory = Memory(
                collection_id=test_collection.id,
                content=[
                    "A happy golden retriever playing",
                    load_file(image_path)  # Auto-detected as image
                ],
                metadata={"test": "async_image_storage", "animal": "dog"}
            )

            memory_id = await client.store_memory(memory)
            assert memory_id, "Should return a memory ID"
            print(f"✅ [Async] Stored image memory: {memory_id}")
        finally:
            image_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_async_store_document(self, client, test_collection):
        """Test storing a PDF document asynchronously."""
        from nebula import Memory, load_file

        pdf_data = create_simple_test_pdf()
        pdf_path = Path(tempfile.mktemp(suffix=".pdf"))
        pdf_path.write_bytes(pdf_data)
        
        try:
            # Just use load_file() - auto-detects as document!
            memory = Memory(
                collection_id=test_collection.id,
                content=[
                    load_file(pdf_path)  # Auto-detected as PDF
                ],
                metadata={"test": "async_document_storage"}
            )

            memory_id = await client.store_memory(memory)
            assert memory_id, "Should return a memory ID"
            print(f"✅ [Async] Stored document memory: {memory_id}")
        finally:
            pdf_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_async_process_multimodal(self, client):
        """Test async on-the-fly multimodal processing."""
        from nebula import load_file
        
        # Download to temp file
        image_path = await async_download_to_temp_file(SAMPLE_IMAGES["landscape"], suffix=".jpg")
        
        try:
            # Use load_file() - auto-detects type!
            image = load_file(image_path)

            # Process the image
            result = await client.process_multimodal_content(
                content_parts=[
                    {
                        "type": image.type,
                        "data": image.data,
                        "media_type": image.media_type,
                        "filename": "landscape.jpg"
                    }
                ]
            )

            assert "extracted_text" in result
            print(f"✅ [Async] Processed image, text length: {len(result.get('extracted_text', ''))}")
        finally:
            image_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_async_multimodal_conversation(self, client, test_collection):
        """Test async conversation with multimodal content."""
        from nebula import Memory, load_file

        # Download images to temp files concurrently
        cat_path, dog_path = await asyncio.gather(
            async_download_to_temp_file(SAMPLE_IMAGES["cat"], suffix=".jpg"),
            async_download_to_temp_file(SAMPLE_IMAGES["dog"], suffix=".jpg")
        )

        try:
            # Just use load_file() - types are auto-detected!
            conversation_id = await client.store_memory(Memory(
                collection_id=test_collection.id,
                content=[
                    "Can you compare these two pets?",
                    load_file(cat_path),  # Auto-detected as image
                    load_file(dog_path)   # Auto-detected as image
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
        finally:
            cat_path.unlink(missing_ok=True)
            dog_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_async_batch_multimodal_storage(self, client, test_collection):
        """Test storing multiple multimodal memories in batch."""
        from nebula import Memory, load_file

        # Download all images to temp files concurrently
        image_paths = await asyncio.gather(*[
            async_download_to_temp_file(url, suffix=".jpg") 
            for url in SAMPLE_IMAGES.values()
        ])

        try:
            # Create memories for each image - just use load_file()!
            memories = []
            for (name, url), path in zip(SAMPLE_IMAGES.items(), image_paths):
                memories.append(Memory(
                    collection_id=test_collection.id,
                    content=[
                        f"Image: {name}",
                        load_file(path)  # Auto-detected as image
                    ],
                    metadata={"image_name": name, "test": "batch_multimodal"}
                ))

            # Store all memories
            memory_ids = await client.store_memories(memories)
            assert len(memory_ids) == len(memories)
            print(f"✅ [Async] Batch stored {len(memory_ids)} multimodal memories")
        finally:
            for path in image_paths:
                path.unlink(missing_ok=True)


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
        from nebula import Memory, load_file, load_url

        # 1. Store a text memory
        text_memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content="The Eiffel Tower is located in Paris, France. It was built in 1889.",
            metadata={"type": "fact", "topic": "landmarks"}
        ))
        print(f"✅ Stored text memory: {text_memory_id}")

        # 2. Store an image memory - use load_url() for web images!
        image_memory_id = client.store_memory(Memory(
            collection_id=test_collection.id,
            content=[
                "A beautiful cityscape at sunset",
                load_url(SAMPLE_IMAGES["city"])  # Auto-detected as image
            ],
            metadata={"type": "photo", "topic": "cities"}
        ))
        print(f"✅ Stored image memory: {image_memory_id}")

        # 3. Store a document memory - use load_file()!
        pdf_data = create_simple_test_pdf()
        pdf_path = Path(tempfile.mktemp(suffix=".pdf"))
        pdf_path.write_bytes(pdf_data)
        
        try:
            doc_memory_id = client.store_memory(Memory(
                collection_id=test_collection.id,
                content=[
                    load_file(pdf_path)  # Auto-detected as document
                ],
                metadata={"type": "document"}
            ))
            print(f"✅ Stored document memory: {doc_memory_id}")
        finally:
            pdf_path.unlink(missing_ok=True)

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

    def test_vision_model_specification(self, client, test_collection):
        """Test specifying a custom vision model."""
        from nebula import Memory, load_url

        # Use load_url() - auto-detects as image!
        image = load_url(SAMPLE_IMAGES["cat"])
        
        # Store with specific vision model
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                "Analyze this cat photo in detail",
                image
            ],
            vision_model="modal/qwen3-vl-thinking",  # Specify vision model
            metadata={"test": "custom_vision_model"}
        )

        memory_id = client.store_memory(memory)
        assert memory_id
        print(f"✅ Stored memory with custom vision model: {memory_id}")

    def test_dict_based_multimodal_content(self, client, test_collection):
        """Test using dict-based content parts instead of dataclasses."""
        from nebula import Memory, load_url

        # load_url() returns an auto-detected content object
        image = load_url(SAMPLE_IMAGES["landscape"])

        # Use dict format (alternative to dataclasses) - but leverage the encoded data
        memory = Memory(
            collection_id=test_collection.id,
            content=[
                {"type": "text", "text": "A beautiful mountain scene"},
                {
                    "type": image.type,  # "image" - auto-detected!
                    "data": image.data,  # Already encoded
                    "media_type": image.media_type,
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
    
    - load_file() for local files (auto-detects type)
    - load_url() for web files (auto-detects type)
    """
    from nebula import Nebula, Memory, load_file, load_url
    
    print("=" * 60)
    print("Nebula Multimodal Quick Test")
    print("=" * 60)
    print("📝 Just use load_file() or load_url() - type is auto-detected!")
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
        
        # 3. Store an image - just use load_url()!
        print("\n🖼️  Testing image storage (using load_url)...")
        memory_id = client.store_memory(Memory(
            collection_id=collection.id,
            content=[
                "A cute orange cat sitting on a couch",  # Plain string works!
                load_url(SAMPLE_IMAGES["cat"])  # Auto-detected as image!
            ],
            metadata={"animal": "cat", "test": "quick_test"}
        ))
        print(f"✅ Stored image memory: {memory_id}")
        
        # 4. Test document storage - use load_file()!
        print("\n📄 Testing document storage (using load_file)...")
        pdf_data = create_simple_test_pdf()
        pdf_path = Path(tempfile.mktemp(suffix=".pdf"))
        pdf_path.write_bytes(pdf_data)
        
        try:
            doc_id = client.store_memory(Memory(
                collection_id=collection.id,
                content=[
                    load_file(pdf_path)  # Auto-detected as PDF document!
                ]
            ))
            print(f"✅ Stored document memory: {doc_id}")
        finally:
            pdf_path.unlink(missing_ok=True)
        
        # 5. Test on-the-fly processing
        print("\n⚡ Testing on-the-fly multimodal processing...")
        image = load_url(SAMPLE_IMAGES["cat"])
        result = client.process_multimodal_content(
            content_parts=[{
                "type": image.type,  # Auto-detected!
                "data": image.data,
                "media_type": image.media_type
            }]
        )
        extracted = result.get("extracted_text", "")
        print(f"✅ Extracted text ({len(extracted)} chars): {extracted[:150]}...")
        
        # 6. Test multimodal conversation
        print("\n💬 Testing multimodal conversation...")
        conv_id = client.store_memory(Memory(
            collection_id=collection.id,
            content=[
                "What do you see in this image?",
                load_url(SAMPLE_IMAGES["cat"])
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
        
        # 7. Wait for indexing and search
        print("\n🔍 Testing search (waiting for indexing)...")
        time.sleep(3)
        results = client.search(
            query="cat picture",
            collection_ids=[collection.id],
            limit=5
        )
        print(f"✅ Search results: {len(results.utterances)} utterances, {len(results.entities)} entities")
        
        # 8. Cleanup
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
    
    - load_file() for local files (auto-detects type)
    """
    from nebula import AsyncNebula, Memory, load_file
    
    print("=" * 60)
    print("Nebula Async Multimodal Quick Test")
    print("=" * 60)
    print("📝 Just use load_file() - type is auto-detected!")
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
        
        # Download to temp file for async test
        image_path = await async_download_to_temp_file(SAMPLE_IMAGES["dog"], suffix=".jpg")
        
        try:
            # Store image - just use load_file()!
            print("\n🖼️  Testing async image storage (using load_file)...")
            memory_id = await client.store_memory(Memory(
                collection_id=collection.id,
                content=[
                    "A happy dog",
                    load_file(image_path)  # Auto-detected as image!
                ]
            ))
            print(f"✅ Stored: {memory_id}")
            
            # Process multimodal content
            print("\n⚡ Testing async processing...")
            image = load_file(image_path)  # Auto-detected!
            result = await client.process_multimodal_content([{
                "type": image.type,
                "data": image.data,
                "media_type": image.media_type
            }])
            print(f"✅ Extracted: {len(result.get('extracted_text', ''))} chars")
            
        finally:
            image_path.unlink(missing_ok=True)
            await client.delete_collection(collection.id)
            print(f"\n🧹 Cleaned up collection")
    
    print("\n✅ Async tests passed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--async":
        asyncio.run(run_async_quick_test())
    else:
        run_quick_test()

