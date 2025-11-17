# Nebula SDK Examples

This directory contains example code demonstrating how to use the Nebula SDKs.

## Quick Start Examples

### JavaScript/TypeScript

See [javascript/](./javascript/) for:
- Basic memory operations
- Collection management
- Search and retrieval
- Conversation memory
- Async patterns

### Python

See [python/](./python/) for:
- Basic memory operations
- Collection management
- Search and retrieval
- Conversation memory
- Sync and async clients

## Running Examples

### JavaScript Examples

```bash
cd javascript/examples
npm install
node basic-usage.js
```

### Python Examples

```bash
cd python/examples
pip install nebula-client
python basic_usage.py
```

## Environment Setup

All examples require a Nebula API key. Set it as an environment variable:

```bash
export NEBULA_API_KEY=your_api_key_here
```

Or create a `.env` file in the examples directory:

```
NEBULA_API_KEY=your_api_key_here
```

## Example Categories

### 1. Basic Operations
- Creating collections
- Adding memories
- Retrieving memories
- Updating memories
- Deleting memories

### 2. Search & Retrieval
- Vector search
- Semantic search
- Filtered search
- Pagination

### 3. Graph Queries
- Entity queries
- Relationship queries
- Community detection

### 4. Advanced Patterns
- Conversation memory management
- Batch operations
- Error handling
- Retry logic

## Contributing Examples

Have a useful example? We'd love to include it!

1. Add your example to the appropriate directory
2. Include clear comments and documentation
3. Test that it works
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.
