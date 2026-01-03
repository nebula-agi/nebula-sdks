# Multimodal Content

Nebula supports images, audio, and documents. Just pass base64-encoded content to `store_memory()` — processing (OCR, transcription, text extraction) happens automatically.

## Quick Example

```python
import base64
from nebula import Nebula, Memory, ImageContent, AudioContent, DocumentContent

client = Nebula(api_key='your-api-key')

# Read and encode
with open("photo.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Store - processing happens automatically
client.store_memory(Memory(
    collection_id='my-collection',
    content=[
        "Describe this photo",
        ImageContent(data=image_data, media_type='image/jpeg', filename='photo.jpg')
    ]
))
```

```typescript
import Nebula from '@nebula-ai/sdk';
import fs from 'fs';

const client = new Nebula({ apiKey: 'your-api-key' });

const imageData = fs.readFileSync('photo.jpg').toString('base64');

await client.storeMemory({
  collection_id: 'my-collection',
  content: [
    { type: 'text', text: 'Describe this photo' },
    { type: 'image', data: imageData, media_type: 'image/jpeg', filename: 'photo.jpg' }
  ]
});
```

## Content Types

| Type | Formats | Processing |
|------|---------|------------|
| `image` | JPEG, PNG, GIF, WebP | Vision model description |
| `audio` | MP3, WAV, M4A, OGG, FLAC | Whisper transcription |
| `document` | PDF, DOC, DOCX, TXT | OCR / text extraction |

## Large Files (>5MB)

Upload to S3 first, then reference:

```python
# 1. Get upload URL
upload_info = client.get_upload_url(filename='large.pdf', content_type='application/pdf', file_size=50_000_000)

# 2. Upload to S3
requests.put(upload_info['upload_url'], data=open('large.pdf', 'rb'), headers={'Content-Type': 'application/pdf'})

# 3. Store with S3 reference
client.store_memory(Memory(
    collection_id='my-collection',
    content=[S3FileRef(s3_key=upload_info['s3_key'], media_type='application/pdf', filename='large.pdf')]
))
```
