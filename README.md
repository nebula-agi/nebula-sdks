# Nebula SDKs

Official SDKs for the Nebula AI Memory platform. Build intelligent applications with persistent, contextual memory.

[![JavaScript CI](https://github.com/nebula-agi/nebula-sdks/actions/workflows/javascript-ci.yml/badge.svg)](https://github.com/nebula-agi/nebula-sdks/actions/workflows/javascript-ci.yml)
[![Python CI](https://github.com/nebula-agi/nebula-sdks/actions/workflows/python-ci.yml/badge.svg)](https://github.com/nebula-agi/nebula-sdks/actions/workflows/python-ci.yml)

## Available SDKs

### [JavaScript/TypeScript SDK](./javascript/)
[![npm version](https://img.shields.io/npm/v/@nebula-ai/sdk.svg)](https://www.npmjs.com/package/@nebula-ai/sdk)

```bash
npm install @nebula-ai/sdk
```

```javascript
import Nebula from '@nebula-ai/sdk';

const client = new Nebula({
  apiKey: process.env.NEBULA_API_KEY
});

// Create a collection
const collection = await client.createCollection({
  name: "My Documents",
  description: "Document memory collection"
});

// Add memory
await client.addMemory({
  collectionId: collection.id,
  content: "Important information to remember"
});

// Search memory
const results = await client.search({
  collectionId: collection.id,
  query: "information",
  limit: 10
});
```

### [Python SDK](./python/)
[![PyPI version](https://img.shields.io/pypi/v/nebula-client.svg)](https://pypi.org/project/nebula-client/)

```bash
pip install nebula-client
```

```python
from nebula import NebulaClient
import os

client = Nebula(api_key=os.getenv("NEBULA_API_KEY"))

# Create a collection
collection = client.create_collection(
    name="My Documents",
    description="Document memory collection"
)

# Add memory
client.add_memory(
    collection_id=collection.id,
    content="Important information to remember"
)

# Search memory
results = client.search(
    collection_id=collection.id,
    query="information",
    limit=10
)
```

## Features

- **Memory Management**: Store and retrieve contextual information
- **Collections**: Organize memories into logical groups
- **Vector Search**: Semantic search across your memory stores
- **Graph Queries**: Explore relationships in your knowledge base
- **Async Support**: Full async/await support in both SDKs
- **Type Safety**: Complete TypeScript types and Python type hints

## Documentation

- [JavaScript SDK Documentation](./javascript/README.md)
- [Python SDK Documentation](./python/README.md)
- [API Reference](./docs/api-reference.md)
- [Examples](./examples/)

## Getting Started

1. Sign up at [https://nebulacloud.app](https://nebulacloud.app)
2. Get your API key from the dashboard
3. Install your preferred SDK
4. Start building with persistent memory

## Examples

Check out the [examples directory](./examples/) for complete working examples:

- Basic usage and CRUD operations
- Conversation memory management
- Document search and retrieval
- Graph-based knowledge queries
- Multi-language examples

## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nebula-cloud/nebula-sdks.git
cd nebula-sdks

# JavaScript SDK
cd javascript
npm install
npm test

# Python SDK
cd python
pip install -e ".[dev]"
pytest
```

## Community & Support

- [Documentation](https://docs.nebulacloud.app)
- [Discord Community](https://discord.gg/nebula)
- [GitHub Issues](https://github.com/nebula-agi/nebula-sdks/issues)
- Email: support@trynebula.ai

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Versioning

Each SDK is versioned independently:

- JavaScript SDK: Uses `js-v*` tags (e.g., `js-v0.0.34`)
- Python SDK: Uses `py-v*` tags (e.g., `py-v0.1.9`)

See [CHANGELOG.md](./CHANGELOG.md) for release history.
