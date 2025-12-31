# Multimodal Content Guide

Nebula supports storing and processing multimodal content including images, audio files, and documents (PDFs, Word docs, etc.). **All multimodal processing is handled automatically by `store_memory()`** — just pass your content and Nebula handles transcription, OCR, and text extraction behind the scenes.

## Table of Contents

- [Quick Start](#quick-start)
- [Supported Content Types](#supported-content-types)
- [Storing Multimodal Memories](#storing-multimodal-memories)
- [Processing Options](#processing-options)
- [Processing Content On-the-Fly](#processing-content-on-the-fly)
- [Large File Uploads (S3)](#large-file-uploads-s3)
- [Complete Examples](#complete-examples)

---

## Quick Start

Use `load_file()` (Python) or `loadFile()` (JavaScript) to automatically detect file types - no manual base64 encoding needed.

### Python

```python
from nebula import Nebula, Memory, load_file, load_url

client = Nebula(api_key='your-api-key')

# Just use load_file() - type is auto-detected from extension!
client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        "Describe these files",
        load_file("photo.jpg"),      # Auto-detected as image
        load_file("recording.mp3"),  # Auto-detected as audio
        load_file("report.pdf"),     # Auto-detected as document
    ]
))

# Or use load_url() for images from the web
client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        "What's in this image?",
        load_url("https://example.com/image.jpg")
    ]
))
```

### JavaScript/TypeScript

```typescript
import Nebula, { loadFile, loadUrl } from '@nebula-ai/sdk';

const client = new Nebula({ apiKey: 'your-api-key' });

// Just use loadFile() - type is auto-detected from extension!
await client.storeMemory({
  collection_id: 'my-collection',
  content: [
    { type: 'text', text: 'Describe these files' },
    await loadFile('photo.jpg'),      // Auto-detected as image
    await loadFile('recording.mp3'),  // Auto-detected as audio
    await loadFile('report.pdf'),     // Auto-detected as document
  ]
});

// Or use loadUrl() for images from the web
await client.storeMemory({
  collection_id: 'my-collection',
  content: [
    { type: 'text', text: "What's in this image?" },
    await loadUrl('https://example.com/image.jpg')
  ]
});

// Browser: Works with File objects from input/drag-drop
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];
const content = await loadFile(file);
```

### Supported File Extensions (Auto-Detected)

| Type | Extensions |
|------|------------|
| **Image** | .jpg, .jpeg, .png, .gif, .webp, .bmp, .svg |
| **Audio** | .mp3, .wav, .m4a, .ogg, .flac, .aac, .webm |
| **Document** | .pdf, .doc, .docx, .txt, .csv, .rtf, .md, .json |

---

## Supported Content Types

### Images
- **Formats**: JPEG, PNG, GIF, WebP
- **Processing**: Vision models (Qwen3-VL, GPT-4o, Claude) generate descriptions
- **Max inline size**: 5MB (use S3 for larger files)

### Audio
- **Formats**: MP3, WAV, M4A, OGG, FLAC, AAC, WebM
- **Processing**: Transcribed using Whisper via LiteLLM
- **Max inline size**: 5MB (use S3 for larger files)

### Documents
- **Formats**: PDF, DOC, DOCX, TXT, CSV, RTF, XLSX, PPTX
- **Processing**: OCR using vision models (best quality for all PDFs)
- **Max inline size**: 5MB (use S3 for larger files)

---

## Storing Multimodal Memories

### Using load_file / loadFile

Use `load_file()` / `loadFile()` for automatic type detection - no encoding needed:

**Python:**
```python
from nebula import Nebula, Memory, load_file

client = Nebula(api_key='your-api-key')

# Store an image with text
client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        'Photo from my trip to Paris',
        load_file('paris.jpg')  # Auto-detected as image
    ],
    metadata={'trip': 'paris-2024'}
))

# Store audio transcription
client.store_memory(Memory(
    collection_id='my-collection',
    content=[load_file('meeting.mp3')],  # Auto-detected as audio
    metadata={'type': 'meeting-notes'}
))

# Store a PDF document
client.store_memory(Memory(
    collection_id='my-collection',
    content=[load_file('Q4-report.pdf')],  # Auto-detected as document
    metadata={'category': 'reports'}
))
```

**JavaScript/TypeScript:**
```typescript
import Nebula, { loadFile } from '@nebula-ai/sdk';

const client = new Nebula({ apiKey: 'your-api-key' });

// Store an image with text
await client.storeMemory({
  collection_id: 'my-collection',
  content: [
    { type: 'text', text: 'Photo from my trip to Paris' },
    await loadFile('paris.jpg')  // Auto-detected as image
  ],
  metadata: { trip: 'paris-2024' }
});

// Store audio transcription
await client.storeMemory({
  collection_id: 'my-collection',
  content: [await loadFile('meeting.mp3')],  // Auto-detected as audio
  metadata: { type: 'meeting-notes' }
});

// Store a PDF document
await client.storeMemory({
  collection_id: 'my-collection',
  content: [await loadFile('Q4-report.pdf')],  // Auto-detected as document
  metadata: { category: 'reports' }
});
```

### Advanced: Manual Encoding

If you need more control, you can manually encode content:

**JavaScript/TypeScript:**
```typescript
import Nebula from '@nebula-ai/sdk';
import fs from 'fs';

const client = new Nebula({ apiKey: 'your-api-key' });

// Manual encoding (advanced)
const imageBuffer = fs.readFileSync('photo.jpg');
const imageBase64 = imageBuffer.toString('base64');

await client.storeMemory({
  collection_id: 'my-collection',
  content: [
    { type: 'text', text: 'Photo from my trip to Paris' },
    { type: 'image', data: imageBase64, media_type: 'image/jpeg', filename: 'paris.jpg' }
  ],
  metadata: { trip: 'paris-2024' }
});
```

**Python:**
```python
import base64
from nebula import Nebula, Memory, ImageContent, AudioContent, DocumentContent

client = Nebula(api_key='your-api-key')

# Manual encoding (advanced)
with open('photo.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        {'type': 'text', 'text': 'Photo from my trip to Paris'},
        ImageContent(data=image_data, media_type='image/jpeg', filename='paris.jpg')
    ],
    metadata={'trip': 'paris-2024'}
))
```

---

## Processing Options

The `store_memory()` function automatically handles all multimodal processing. You can customize the processing with these optional parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vision_model` | string | `modal/qwen3-vl-thinking` | Vision model for images and document OCR |
| `audio_model` | string | `whisper-1` | Audio transcription model |

### Example with Options

**JavaScript:**
```typescript
await client.storeMemory({
  collection_id: 'my-collection',
  content: [
    { type: 'document', data: pdfBase64, media_type: 'application/pdf' }
  ],
  metadata: {},
  vision_model: 'gpt-4o',  // Custom vision model
});
```

**Python:**
```python
client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        DocumentContent(data=pdf_data, media_type='application/pdf')
    ],
    metadata={},
    vision_model='gpt-4o',  # Custom vision model
))
```

---

## Processing Content On-the-Fly

Use `processMultimodalContent()` to extract text from files **without saving to memory**. This is useful for:
- Pre-processing files before sending to an LLM
- Quick text extraction from documents
- Audio transcription

### JavaScript/TypeScript

```typescript
import Nebula from '@nebula-ai/sdk';
import fs from 'fs';

const client = new Nebula({ apiKey: 'your-api-key' });

// Extract text from a PDF
const pdfBuffer = fs.readFileSync('document.pdf');
const pdfBase64 = pdfBuffer.toString('base64');

const result = await client.processMultimodalContent({
  contentParts: [{
    type: 'document',
    data: pdfBase64,
    media_type: 'application/pdf',
    filename: 'document.pdf'
  }]
});

console.log('Extracted text:', result.extracted_text);
console.log('Parts processed:', result.content_parts_count);

// Transcribe audio
const audioBuffer = fs.readFileSync('speech.mp3');
const audioBase64 = audioBuffer.toString('base64');

const transcription = await client.processMultimodalContent({
  contentParts: [{
    type: 'audio',
    data: audioBase64,
    media_type: 'audio/mp3',
    filename: 'speech.mp3'
  }]
});

console.log('Transcription:', transcription.extracted_text);

// Use custom vision model for PDFs
const scannedResult = await client.processMultimodalContent({
  contentParts: [{
    type: 'document',
    data: pdfBase64,
    media_type: 'application/pdf'
  }],
  visionModel: 'modal/qwen3-vl-thinking'
});
```

### Python

```python
import base64
from nebula import Nebula

client = Nebula(api_key='your-api-key')

# Extract text from a PDF
with open('document.pdf', 'rb') as f:
    pdf_data = base64.b64encode(f.read()).decode()

result = client.process_multimodal_content([
    {
        'type': 'document',
        'data': pdf_data,
        'media_type': 'application/pdf',
        'filename': 'document.pdf'
    }
])

print('Extracted text:', result['extracted_text'])
print('Parts processed:', result['content_parts_count'])

# Transcribe audio
with open('speech.mp3', 'rb') as f:
    audio_data = base64.b64encode(f.read()).decode()

transcription = client.process_multimodal_content([
    {
        'type': 'audio',
        'data': audio_data,
        'media_type': 'audio/mp3',
        'filename': 'speech.mp3'
    }
])

print('Transcription:', transcription['extracted_text'])

# Use custom vision model for PDFs
scanned_result = client.process_multimodal_content(
    content_parts=[{
        'type': 'document',
        'data': pdf_data,
        'media_type': 'application/pdf'
    }],
    vision_model='modal/qwen3-vl-thinking'
)
```

### Async Python

```python
import base64
from nebula import AsyncNebula

async with AsyncNebula(api_key='your-api-key') as client:
    with open('document.pdf', 'rb') as f:
        pdf_data = base64.b64encode(f.read()).decode()
    
    result = await client.process_multimodal_content([
        {'type': 'document', 'data': pdf_data, 'media_type': 'application/pdf'}
    ])
    print(result['extracted_text'])
```

---

## Large File Uploads (S3)

For files larger than 5MB, upload to S3 first:

### Python

```python
import requests
from nebula import Nebula, Memory, S3FileRef

client = Nebula(api_key='your-api-key')

# 1. Get presigned upload URL
upload_info = client.get_upload_url(
    filename='large_video.mp4',
    content_type='video/mp4',
    file_size=50_000_000  # 50MB
)

# 2. Upload file directly to S3
with open('large_video.mp4', 'rb') as f:
    requests.put(
        upload_info['upload_url'],
        data=f,
        headers={'Content-Type': 'video/mp4'}
    )

# 3. Create memory with S3 reference
client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        S3FileRef(
            s3_key=upload_info['s3_key'],
            media_type='video/mp4',
            filename='large_video.mp4'
        )
    ]
))
```

### JavaScript/TypeScript

```typescript
import Nebula from '@nebula-ai/sdk';
import fs from 'fs';

const client = new Nebula({ apiKey: 'your-api-key' });

// 1. Get presigned upload URL (using raw request)
const uploadInfo = await client._makeRequest('POST', '/v1/upload-url', undefined, {
  filename: 'large_video.mp4',
  content_type: 'video/mp4',
  file_size: 50_000_000
});

// 2. Upload file directly to S3
const fileBuffer = fs.readFileSync('large_video.mp4');
await fetch(uploadInfo.results.upload_url, {
  method: 'PUT',
  body: fileBuffer,
  headers: { 'Content-Type': 'video/mp4' }
});

// 3. Create memory with S3 reference
await client.storeMemory({
  collection_id: 'my-collection',
  content: [{
    type: 's3_ref',
    s3_key: uploadInfo.results.s3_key,
    media_type: 'video/mp4',
    filename: 'large_video.mp4'
  }],
  metadata: {}
});
```

---

## Complete Examples

### Build a Document Q&A System

```python
import base64
from nebula import Nebula

client = Nebula(api_key='your-api-key')

def process_and_store_document(filepath: str, collection_id: str):
    """Extract text from document and store in Nebula for search."""
    with open(filepath, 'rb') as f:
        doc_data = base64.b64encode(f.read()).decode()
    
    # Extract text
    result = client.process_multimodal_content([
        {'type': 'document', 'data': doc_data, 'media_type': 'application/pdf'}
    ])
    
    # Store extracted text as searchable memory
    memory_id = client.store_memory({
        'collection_id': collection_id,
        'content': result['extracted_text'],
        'metadata': {'source_file': filepath, 'type': 'document'}
    })
    
    return memory_id

# Process multiple documents
docs = ['report1.pdf', 'report2.pdf', 'whitepaper.pdf']
for doc in docs:
    process_and_store_document(doc, 'documents-collection')

# Search across all documents
results = client.search({
    'query': 'What are the Q4 revenue projections?',
    'collection_ids': ['documents-collection']
})

for fact in results.facts:
    print(f"Found: {fact['subject']} - {fact['predicate']} - {fact['object_value']}")
```

### Meeting Transcription Pipeline

```typescript
import Nebula from '@nebula-ai/sdk';
import fs from 'fs';

const client = new Nebula({ apiKey: 'your-api-key' });

async function processMeetingRecording(audioPath: string, collectionId: string) {
  // Read and encode audio
  const audioBuffer = fs.readFileSync(audioPath);
  const audioBase64 = audioBuffer.toString('base64');
  
  // Transcribe
  const result = await client.processMultimodalContent({
    contentParts: [{
      type: 'audio',
      data: audioBase64,
      media_type: 'audio/mp3',
      filename: audioPath
    }]
  });
  
  // Store transcription as conversation
  const memoryId = await client.storeMemory({
    collection_id: collectionId,
    content: result.extracted_text,
    role: 'user',  // Creates a conversation-type memory
    metadata: {
      type: 'meeting-transcription',
      source: audioPath,
      transcribed_at: new Date().toISOString()
    }
  });
  
  console.log(`Transcribed and stored: ${memoryId}`);
  return memoryId;
}

// Process recordings
await processMeetingRecording('meeting-2024-01-15.mp3', 'meetings');
```

---

## API Reference

### Content Part Types

```typescript
// Text content
{ type: 'text', text: 'Hello world' }

// Image content
{ 
  type: 'image', 
  data: 'base64...', 
  media_type: 'image/jpeg',
  filename: 'photo.jpg'  // optional
}

// Audio content  
{ 
  type: 'audio', 
  data: 'base64...', 
  media_type: 'audio/mp3',
  filename: 'recording.mp3',  // optional
  duration_seconds: 120.5     // optional
}

// Document content
{ 
  type: 'document', 
  data: 'base64...', 
  media_type: 'application/pdf',
  filename: 'report.pdf'  // optional
}

// S3 file reference (for large files)
{ 
  type: 's3_ref', 
  s3_key: 'multimodal/abc/file.pdf',
  bucket: 'nebula-uploads',  // optional, uses default
  media_type: 'application/pdf',
  filename: 'report.pdf',    // optional
  size_bytes: 15000000       // optional
}
```

### Supported MIME Types

**Images**: `image/jpeg`, `image/png`, `image/gif`, `image/webp`

**Audio**: `audio/mp3`, `audio/mpeg`, `audio/wav`, `audio/m4a`, `audio/ogg`, `audio/flac`, `audio/aac`, `audio/webm`

**Documents**: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`, `text/csv`

---

## Support

- [Full SDK Documentation](https://docs.nebulacloud.app)
- [GitHub Issues](https://github.com/nebula-agi/nebula-sdks/issues)
- [Discord Community](https://discord.gg/nebula)
- Email: support@trynebula.ai

