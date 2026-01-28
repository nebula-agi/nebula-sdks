# Nebula MCP Server (Node)

npx-friendly MCP server that exposes Nebula tools through the Model Context Protocol.

## Quick Installation

### One-Command Setup
```bash
# Install for Claude Desktop
npx install-mcp "@nebula-ai/mcp-server --stdio" --client claude --env NEBULA_API_KEY=your_api_key

# Install for Cursor  
npx install-mcp "@nebula-ai/mcp-server --stdio" --client cursor --env NEBULA_API_KEY=your_api_key
```

### Custom Installer
```bash
npx @nebula-ai/mcp-server-install --client claude --api-key your_api_key
```

## Manual Usage

- **Direct execution (stdio for MCP clients):**
```bash
npx -y @nebula-ai/mcp-server --stdio --api-key $NEBULA_API_KEY
```

- **WebSocket mode (for development):**
```bash
npx -y @nebula-ai/mcp-server --api-key $NEBULA_API_KEY
```

## Manual Client Configuration

For Claude Desktop, Cursor, VS Code, etc.:
```json
{
  "mcpServers": {
    "nebula": {
      "command": "npx",
      "args": ["-y", "@nebula-ai/mcp-server", "--stdio"],
      "env": {
        "NEBULA_API_KEY": "<your-api-key>",
        "NEBULA_API_URL": "https://api.trynebula.ai"
      }
    }
  }
}
```

📖 **See [INSTALLATION.md](./INSTALLATION.md) for complete setup instructions**

## Tools
- **add_memory** { content, role?, parent_id?, metadata? }
- **search_memories** { query, limit? }

*Note: With web-hosted servers, cluster scoping is automatic via URL path*
